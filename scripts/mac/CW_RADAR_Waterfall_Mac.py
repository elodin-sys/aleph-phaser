#!/usr/bin/env python3
"""
CW Radar Waterfall Demo - Mac Edition

Runs the Qt visualization on your Mac while connecting to:
- PlutoSDR via Aleph's socat proxy (ip:192.168.4.181:30431)
- Phaser via Raspberry Pi (ip:192.168.4.184)

Prerequisites (on Mac):
    cd scripts/mac
    uv venv --python 3.12
    source .venv/bin/activate
    uv sync

Usage:
    python3 CW_RADAR_Waterfall_Mac.py

Configuration:
    Edit aleph_ip and phaser_ip below to match your network setup.

Based on Jon Kraft's CW Radar Demo, adapted for Aleph hybrid architecture.
"""

# Copyright (C) 2022 Analog Devices, Inc.
# Adapted for Aleph by Elodin, Dec 2024

import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from pyqtgraph.Qt import QtCore, QtGui

import adi

# ============================================================================
# CONFIGURATION - Edit these to match your network
# ============================================================================

# Aleph IP - socat proxies PlutoSDR's IIO port (30431) to the network
aleph_ip = "192.168.4.186"
sdr_ip = f"ip:{aleph_ip}"  # Port 30431 is default for IIO

# Raspberry Pi (Phaser) IP
phaser_ip = "192.168.4.184"
rpi_ip = f"ip:{phaser_ip}"

# ============================================================================

print("=" * 60)
print("CW Radar Waterfall - Mac Edition")
print("=" * 60)
print(f"Connecting to SDR via Aleph at {sdr_ip}")
print(f"Connecting to Phaser via Pi at {rpi_ip}")
print()

# Connect to hardware
try:
    print("Connecting to PlutoSDR (via Aleph iiod)...")
    my_sdr = adi.ad9361(uri=sdr_ip)
    print("  ✓ PlutoSDR connected")
except Exception as e:
    print(f"  ✗ Failed to connect to SDR: {e}")
    print()
    print("Make sure:")
    print(f"  1. Aleph is reachable at {aleph_ip}")
    print("  2. iiod service is running: ssh aleph-phaser@{aleph_ip} 'systemctl status iiod'")
    print("  3. PlutoSDR is connected to Aleph USB")
    sys.exit(1)

try:
    print("Connecting to Phaser (via Pi)...")
    my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)
    print("  ✓ Phaser connected")
except Exception as e:
    print(f"  ✗ Failed to connect to Phaser: {e}")
    print()
    print("Make sure:")
    print(f"  1. Raspberry Pi is reachable at {phaser_ip}")
    print("  2. iiod is running on the Pi")
    sys.exit(1)

print()
print("Configuring hardware...")

# Initialize both ADAR1000s, set gains to max, and all phases to 0
my_phaser.configure(device_mode="rx")

# Note: Calibration files are stored on the Pi, not the Aleph
# If you see "file not found" messages, run calibration on the Pi first:
#   ssh analog@192.168.4.184
#   cd ~/pyadi-iio/examples/phaser
#   python3 phaser_prod_tst.py
try:
    my_phaser.load_gain_cal()
    my_phaser.load_phase_cal()
except:
    pass  # pyadi-iio prints its own "file not found" messages
print("  ✓ Phaser configured (using Pi's calibration if available)")

for i in range(0, 8):
    my_phaser.set_chan_phase(i, 0)

gain_list = [8, 34, 84, 127, 127, 84, 34, 8]  # Blackman taper
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

# Setup Raspberry Pi GPIO states
try:
    my_phaser._gpios.gpio_tx_sw = 0
    my_phaser._gpios.gpio_vctrl_1 = 1
    my_phaser._gpios.gpio_vctrl_2 = 1
except:
    try:
        my_phaser.gpios.gpio_tx_sw = 0
        my_phaser.gpios.gpio_vctrl_1 = 1
        my_phaser.gpios.gpio_vctrl_2 = 1
    except:
        print("  ⚠ Could not configure GPIOs")

sample_rate = 0.6e6
center_freq = 2.2e9
signal_freq = 100e3
num_slices = 50
fft_size = 1024 * 64
img_array = np.ones((num_slices, fft_size)) * (-100)

# Configure SDR Rx
my_sdr.sample_rate = int(sample_rate)
my_sdr.rx_lo = int(center_freq)
my_sdr.rx_enabled_channels = [0, 1]
my_sdr.rx_buffer_size = int(fft_size)
my_sdr.gain_control_mode_chan0 = "manual"
my_sdr.gain_control_mode_chan1 = "manual"
my_sdr.rx_hardwaregain_chan0 = int(30)
my_sdr.rx_hardwaregain_chan1 = int(30)

# Configure SDR Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True
my_sdr.tx_hardwaregain_chan0 = -88
my_sdr.tx_hardwaregain_chan1 = -0

# Configure the ADF4159 Rampling PLL
output_freq = 12.2e9
my_phaser.frequency = int(output_freq / 4)
my_phaser.ramp_mode = "disabled"
my_phaser.enable = 0

print(f"  Sample rate: {sample_rate/1e6:.1f} MSPS")
print(f"  Center freq: {center_freq/1e9:.1f} GHz")
print(f"  PLL output: {output_freq/1e9:.1f} GHz")

# Create a sinewave waveform
fs = int(my_sdr.sample_rate)
N = int(my_sdr.rx_buffer_size)
fc = int(signal_freq / (fs / N)) * (fs / N)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 1 * (i + 1j * q)

# Send data
print("  Starting Tx...")
my_sdr._ctx.set_timeout(5000)  # 5 second timeout (0 = infinite, can cause hangs)
my_sdr.tx([iq * 0.5, iq])

c = 3e8
N_frame = fft_size
freq = np.linspace(-fs / 2, fs / 2, int(N_frame))

print()
print("Starting Qt display...")
print("Close the window to exit.")
print()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CW Radar Waterfall - Aleph/Mac")
        self.setGeometry(100, 100, 800, 800)
        self.setFixedWidth(1600)
        self.num_rows = 12
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        widget = QWidget()

        global layout
        layout = QGridLayout()

        # Control Panel
        control_label = QLabel("PHASER CW Radar (Aleph/Mac)")
        font = control_label.font()
        font.setPointSize(24)
        control_label.setFont(font)
        font.setPointSize(12)
        control_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(control_label, 0, 0, 1, 2)

        # Connection info
        conn_label = QLabel(f"SDR: {sdr_ip}\nPhaser: {rpi_ip}")
        conn_label.setFont(font)
        layout.addWidget(conn_label, 1, 0, 1, 2)

        # Buttons
        self.quit_button = QPushButton("Quit")
        self.quit_button.pressed.connect(self.end_program)
        layout.addWidget(self.quit_button, 30, 0, 4, 4)

        # waterfall level slider
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setMinimum(-100)
        self.low_slider.setMaximum(0)
        self.low_slider.setValue(-66)
        self.low_slider.setTickInterval(20)
        self.low_slider.setMaximumWidth(200)
        self.low_slider.setTickPosition(QSlider.TicksBelow)
        self.low_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.low_slider, 8, 0)

        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setMinimum(-100)
        self.high_slider.setMaximum(0)
        self.high_slider.setValue(-42)
        self.high_slider.setTickInterval(20)
        self.high_slider.setMaximumWidth(200)
        self.high_slider.setTickPosition(QSlider.TicksBelow)
        self.high_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.high_slider, 10, 0)

        self.water_label = QLabel("Waterfall Intensity Levels")
        self.water_label.setFont(font)
        self.water_label.setAlignment(Qt.AlignCenter)
        self.water_label.setMinimumWidth(300)
        layout.addWidget(self.water_label, 7, 0)
        self.low_label = QLabel("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.low_label.setFont(font)
        self.low_label.setAlignment(Qt.AlignLeft)
        self.low_label.setMinimumWidth(100)
        layout.addWidget(self.low_label, 8, 1)
        self.high_label = QLabel("HIGH LEVEL: %0.0f" % (self.high_slider.value()))
        self.high_label.setFont(font)
        self.high_label.setAlignment(Qt.AlignLeft)
        self.high_label.setMinimumWidth(100)
        layout.addWidget(self.high_label, 10, 1)

        # FFT plot
        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq, pen={'color': 'y', 'width': 2})
        title_style = {"size": "20pt"}
        label_style = {"color": "#FFF", "font-size": "14pt"}
        self.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)
        self.fft_plot.setLabel("left", text="Magnitude", units="dB", **label_style)
        self.fft_plot.setTitle("Received Signal - Frequency Spectrum", **title_style)
        layout.addWidget(self.fft_plot, 0, 2, self.num_rows, 1)
        self.fft_plot.setYRange(-60, 0)
        self.fft_plot.setXRange(99e3, 101e3)

        # Waterfall plot
        self.waterfall = pg.PlotWidget()
        self.imageitem = pg.ImageItem()
        self.waterfall.addItem(self.imageitem)
        # Use a viridis colormap
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([[68, 1, 84, 255], [59, 82, 139, 255], [33, 145, 140, 255], 
                          [94, 201, 98, 255], [253, 231, 37, 255]], dtype=np.ubyte)
        lut = pg.ColorMap(pos, color).getLookupTable(0.0, 1.0, 256)
        self.imageitem.setLookupTable(lut)
        self.imageitem.setLevels([0, 1])
        tr = QtGui.QTransform()
        tr.translate(0, -sample_rate / 2)
        tr.scale(0.35, sample_rate / (N))
        self.imageitem.setTransform(tr)
        zoom_freq = 0.3e3
        self.waterfall.setRange(yRange=(signal_freq - zoom_freq, signal_freq + zoom_freq))
        self.waterfall.setTitle("Waterfall Spectrum", **title_style)
        self.waterfall.setLabel("left", "Frequency", units="Hz", **label_style)
        self.waterfall.setLabel("bottom", "Time", units="sec", **label_style)
        layout.addWidget(self.waterfall, 0 + self.num_rows + 1, 2, self.num_rows, 1)
        self.img_array = np.ones((num_slices, fft_size)) * (-100)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def get_water_levels(self):
        if self.low_slider.value() > self.high_slider.value():
            self.low_slider.setValue(self.high_slider.value())
        self.low_label.setText("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.high_label.setText("HIGH LEVEL: %0.0f" % (self.high_slider.value()))

    def end_program(self):
        my_sdr.tx_destroy_buffer()
        self.close()


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
win = Window()
win.setWindowState(QtCore.Qt.WindowMaximized)
index = 0


rx_error_count = 0

def update():
    global index, freq, rx_error_count
    label_style = {"color": "#FFF", "font-size": "14pt"}

    try:
        data = my_sdr.rx()
        rx_error_count = 0  # Reset on success
    except OSError as e:
        rx_error_count += 1
        if rx_error_count <= 3:
            print(f"Rx error ({rx_error_count}/3): {e}")
        elif rx_error_count == 4:
            print("Too many Rx errors - SDR may need restart. Use Quit button or restart iio-proxy.")
        return  # Skip this update

    data = data[0] + data[1]
    win_funct = np.blackman(len(data))
    y = data * win_funct
    sp = np.absolute(np.fft.fft(y))
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))

    win.fft_curve.setData(freq, s_dbfs)
    win.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)

    win.img_array = np.roll(win.img_array, 1, axis=0)
    win.img_array[0] = s_dbfs
    win.imageitem.setLevels([win.low_slider.value(), win.high_slider.value()])
    win.imageitem.setImage(win.img_array, autoLevels=False)

    if index == 1:
        win.fft_plot.enableAutoRange("xy", False)
    index = index + 1


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# start the app
try:
    App.exec()
except KeyboardInterrupt:
    print("\nInterrupted by user")
finally:
    # Always clean up Tx buffer to prevent SDR from getting stuck
    try:
        my_sdr.tx_destroy_buffer()
        print("Tx buffer cleaned up")
    except:
        pass
sys.exit(0)
