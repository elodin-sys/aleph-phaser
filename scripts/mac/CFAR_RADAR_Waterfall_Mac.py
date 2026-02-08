#!/usr/bin/env python3
"""
CFAR Radar Waterfall Demo - Mac Edition

Runs the Qt visualization on your Mac while connecting to:
- PlutoSDR via Aleph's socat proxy (ip:192.168.4.181:30431)
- Phaser via Raspberry Pi (ip:192.168.4.184)

Prerequisites (on Mac):
    cd scripts/mac
    uv venv --python 3.12
    source .venv/bin/activate
    uv sync

Usage:
    python3 CFAR_RADAR_Waterfall_Mac.py

Configuration:
    Edit aleph_ip and phaser_ip below to match your network setup.

Based on Jon Kraft's CFAR Radar Demo, adapted for Aleph hybrid architecture.
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

from target_detection_dbfs import cfar
import adi

# ============================================================================
# CONFIGURATION - Edit these to match your network
# ============================================================================

# Aleph IP - socat proxies PlutoSDR's IIO port (30431) to the network
aleph_ip = "192.168.4.181"
sdr_ip = f"ip:{aleph_ip}"  # Port 30431 is default for IIO

# Raspberry Pi (Phaser) IP
phaser_ip = "192.168.4.184"
rpi_ip = f"ip:{phaser_ip}"

# ============================================================================

print("=" * 60)
print("CFAR Radar Waterfall - Mac Edition")
print("=" * 60)
print(f"Connecting to SDR via Aleph at {sdr_ip}")
print(f"Connecting to Phaser via Pi at {rpi_ip}")
print()

def disable_tdd(sdr):
    """Disable TDD engine on PlutoSDR if left enabled by radar-web.
    
    The radar-web/tui-radar apps use TDD burst mode with external sync.
    If they are killed without clean shutdown, the TDD engine stays enabled
    and gates the RX path, causing sdr.rx() to timeout (ETIMEDOUT).
    """
    try:
        ctx = sdr._ctx
        for dev in ctx.devices:
            if hasattr(dev, 'name') and dev.name and 'tdd' in dev.name:
                for attr in dev.attrs:
                    if attr == 'enable':
                        if dev.attrs['enable'].value.strip() == '1':
                            dev.attrs['enable'].value = '0'
                            print("  ✓ Disabled leftover TDD engine (was blocking RX)")
                        return
    except Exception:
        pass  # Best effort -- not all SDR firmware versions have TDD

# Connect to hardware
try:
    print("Connecting to PlutoSDR (via Aleph iio-proxy)...")
    my_sdr = adi.ad9361(uri=sdr_ip)
    print("  ✓ PlutoSDR connected")
    disable_tdd(my_sdr)
except Exception as e:
    print(f"  ✗ Failed to connect to SDR: {e}")
    print()
    print("Make sure:")
    print(f"  1. Aleph is reachable at {aleph_ip}")
    print(f"  2. iio-proxy is running: ssh aleph-phaser@{aleph_ip} 'systemctl status iio-proxy'")
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
    my_phaser._gpios.gpio_tx_sw = 0  # 0 = TX_OUT_2, 1 = TX_OUT_1
    my_phaser._gpios.gpio_vctrl_1 = 1  # 1=Use onboard PLL/LO source
    my_phaser._gpios.gpio_vctrl_2 = 1  # 1=Send LO to transmit circuitry
except:
    try:
        my_phaser.gpios.gpio_tx_sw = 0
        my_phaser.gpios.gpio_vctrl_1 = 1
        my_phaser.gpios.gpio_vctrl_2 = 1
    except:
        print("  ⚠ Could not configure GPIOs")

sample_rate = 0.6e6
center_freq = 2.1e9
signal_freq = 100e3
num_slices = 50     # this sets how much time will be displayed on the waterfall plot
fft_size = 1024 * 8
plot_freq = 100e3    # x-axis freq range to plot
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
output_freq = 12.145e9
BW = 500e6
num_steps = 500
ramp_time = 0.5e3  # us
my_phaser.frequency = int(output_freq / 4)
my_phaser.freq_dev_range = int(BW / 4)
my_phaser.freq_dev_step = int((BW/4) / num_steps)
my_phaser.freq_dev_time = int(ramp_time)
print(f"  Requested freq dev time = {ramp_time} us")
ramp_time = my_phaser.freq_dev_time
ramp_time_s = ramp_time / 1e6
print(f"  Actual freq dev time = {ramp_time} us")
my_phaser.delay_word = 4095
my_phaser.delay_clk = "PFD"
my_phaser.delay_start_en = 0
my_phaser.ramp_delay_en = 0
my_phaser.trig_delay_en = 0
my_phaser.ramp_mode = "continuous_triangular"
my_phaser.sing_ful_tri = 0
my_phaser.tx_trig_en = 0
my_phaser.enable = 0

# Print config
print(f"""
CONFIG:
  Sample rate: {sample_rate / 1e6} MHz
  Num samples: 2^{int(np.log2(fft_size))}
  Bandwidth: {BW / 1e6} MHz
  Ramp time: {ramp_time / 1e3} ms
  Output frequency: {output_freq / 1e6} MHz
  IF: {signal_freq / 1e3} kHz
""")

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
default_chirp_bw = 500e6
N_frame = fft_size
freq = np.linspace(-fs / 2, fs / 2, int(N_frame))
slope = BW / ramp_time_s
dist = (freq - signal_freq) * c / (2 * slope)

plot_threshold = False
cfar_toggle = False

print()
print("Starting Qt display...")
print("Close the window to exit.")
print()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CFAR Radar Waterfall - Aleph/Mac")
        self.setGeometry(0, 0, 400, 400)
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.num_rows = 12
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        widget = QWidget()

        global layout, signal_freq, plot_freq
        layout = QGridLayout()

        # Control Panel
        control_label = QLabel("PHASER CFAR Targeting (Aleph/Mac)")
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

        # Check boxes
        self.thresh_check = QCheckBox("Plot CFAR Threshold")
        font = self.thresh_check.font()
        font.setPointSize(10)
        self.thresh_check.setFont(font)
        self.thresh_check.stateChanged.connect(self.change_thresh)
        layout.addWidget(self.thresh_check, 2, 0)
        
        self.cfar_check = QCheckBox("Apply CFAR Threshold")
        font = self.cfar_check.font()
        self.cfar_check.setFont(font)
        self.cfar_check.stateChanged.connect(self.change_cfar)
        layout.addWidget(self.cfar_check, 2, 1)

        # Chirp bandwidth slider
        self.bw_slider = QSlider(Qt.Horizontal)
        self.bw_slider.setMinimum(100)
        self.bw_slider.setMaximum(500)
        self.bw_slider.setValue(int(default_chirp_bw / 1e6))
        self.bw_slider.setTickInterval(50)
        self.bw_slider.setMaximumWidth(200)
        self.bw_slider.setTickPosition(QSlider.TicksBelow)
        self.bw_slider.valueChanged.connect(self.get_range_res)
        layout.addWidget(self.bw_slider, 4, 0)

        self.set_bw = QPushButton("Set Chirp Bandwidth")
        self.set_bw.setMaximumWidth(200)
        self.set_bw.pressed.connect(self.set_range_res)
        layout.addWidget(self.set_bw, 5, 0, 1, 1)
        
        self.quit_button = QPushButton("Quit")
        self.quit_button.pressed.connect(self.end_program)
        layout.addWidget(self.quit_button, 30, 0, 4, 4)
        
        # CFAR Sliders
        self.cfar_bias = QSlider(Qt.Horizontal)
        self.cfar_bias.setMinimum(0)
        self.cfar_bias.setMaximum(100)
        self.cfar_bias.setValue(40)
        self.cfar_bias.setTickInterval(5)
        self.cfar_bias.setMaximumWidth(200)
        self.cfar_bias.setTickPosition(QSlider.TicksBelow)
        self.cfar_bias.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_bias, 8, 0)
        self.cfar_bias_label = QLabel("CFAR Bias (dB): %0.0f" % (self.cfar_bias.value()))
        self.cfar_bias_label.setFont(font)
        self.cfar_bias_label.setAlignment(Qt.AlignLeft)
        self.cfar_bias_label.setMinimumWidth(100)
        self.cfar_bias_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_bias_label, 8, 1)
        
        self.cfar_guard = QSlider(Qt.Horizontal)
        self.cfar_guard.setMinimum(1)
        self.cfar_guard.setMaximum(40)
        self.cfar_guard.setValue(27)
        self.cfar_guard.setTickInterval(4)
        self.cfar_guard.setMaximumWidth(200)
        self.cfar_guard.setTickPosition(QSlider.TicksBelow)
        self.cfar_guard.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_guard, 10, 0)
        self.cfar_guard_label = QLabel("Num Guard Cells: %0.0f" % (self.cfar_guard.value()))
        self.cfar_guard_label.setFont(font)
        self.cfar_guard_label.setAlignment(Qt.AlignLeft)
        self.cfar_guard_label.setMinimumWidth(100)
        self.cfar_guard_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_guard_label, 10, 1)
        
        self.cfar_ref = QSlider(Qt.Horizontal)
        self.cfar_ref.setMinimum(1)
        self.cfar_ref.setMaximum(100)
        self.cfar_ref.setValue(16)
        self.cfar_ref.setTickInterval(10)
        self.cfar_ref.setMaximumWidth(200)
        self.cfar_ref.setTickPosition(QSlider.TicksBelow)
        self.cfar_ref.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_ref, 12, 0)
        self.cfar_ref_label = QLabel("Num Ref Cells: %0.0f" % (self.cfar_ref.value()))
        self.cfar_ref_label.setFont(font)
        self.cfar_ref_label.setAlignment(Qt.AlignLeft)
        self.cfar_ref_label.setMinimumWidth(100)
        self.cfar_ref_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_ref_label, 12, 1)

        # waterfall level slider
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setMinimum(-100)
        self.low_slider.setMaximum(0)
        self.low_slider.setValue(-100)
        self.low_slider.setTickInterval(20)
        self.low_slider.setMaximumWidth(200)
        self.low_slider.setTickPosition(QSlider.TicksBelow)
        self.low_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.low_slider, 16, 0)

        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setMinimum(-100)
        self.high_slider.setMaximum(0)
        self.high_slider.setValue(0)
        self.high_slider.setTickInterval(20)
        self.high_slider.setMaximumWidth(200)
        self.high_slider.setTickPosition(QSlider.TicksBelow)
        self.high_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.high_slider, 18, 0)

        self.water_label = QLabel("Waterfall Intensity Levels")
        self.water_label.setFont(font)
        self.water_label.setAlignment(Qt.AlignCenter)
        self.water_label.setMinimumWidth(100)
        self.water_label.setMaximumWidth(200)
        layout.addWidget(self.water_label, 15, 0, 1, 1)
        self.low_label = QLabel("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.low_label.setFont(font)
        self.low_label.setAlignment(Qt.AlignLeft)
        self.low_label.setMinimumWidth(100)
        self.low_label.setMaximumWidth(200)
        layout.addWidget(self.low_label, 16, 1)
        self.high_label = QLabel("HIGH LEVEL: %0.0f" % (self.high_slider.value()))
        self.high_label.setFont(font)
        self.high_label.setAlignment(Qt.AlignLeft)
        self.high_label.setMinimumWidth(100)
        self.high_label.setMaximumWidth(200)
        layout.addWidget(self.high_label, 18, 1)

        self.steer_slider = QSlider(Qt.Horizontal)
        self.steer_slider.setMinimum(-80)
        self.steer_slider.setMaximum(80)
        self.steer_slider.setValue(0)
        self.steer_slider.setTickInterval(20)
        self.steer_slider.setMaximumWidth(200)
        self.steer_slider.setTickPosition(QSlider.TicksBelow)
        self.steer_slider.valueChanged.connect(self.get_steer_angle)
        layout.addWidget(self.steer_slider, 22, 0)
        self.steer_title = QLabel("Receive Steering Angle")
        self.steer_title.setFont(font)
        self.steer_title.setAlignment(Qt.AlignCenter)
        self.steer_title.setMinimumWidth(100)
        self.steer_title.setMaximumWidth(200)
        layout.addWidget(self.steer_title, 21, 0)
        self.steer_label = QLabel("%0.0f DEG" % (self.steer_slider.value()))
        self.steer_label.setFont(font)
        self.steer_label.setAlignment(Qt.AlignLeft)
        self.steer_label.setMinimumWidth(100)
        self.steer_label.setMaximumWidth(200)
        layout.addWidget(self.steer_label, 22, 1, 1, 2)

        # FFT plot
        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq, pen={'color': 'y', 'width': 2})
        self.fft_threshold = self.fft_plot.plot(freq, pen={'color': 'r', 'width': 2})
        title_style = {"size": "20pt"}
        label_style = {"color": "#FFF", "font-size": "14pt"}
        self.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)
        self.fft_plot.setLabel("left", text="Magnitude", units="dB", **label_style)
        self.fft_plot.setTitle("Received Signal - Frequency Spectrum", **title_style)
        layout.addWidget(self.fft_plot, 0, 2, self.num_rows, 1)
        self.fft_plot.setYRange(-60, 0)
        self.fft_plot.setXRange(signal_freq, signal_freq + plot_freq)

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
        zoom_freq = 35e3
        self.waterfall.setRange(yRange=(signal_freq, signal_freq + zoom_freq))
        self.waterfall.setTitle("Waterfall Spectrum", **title_style)
        self.waterfall.setLabel("left", "Frequency", units="Hz", **label_style)
        self.waterfall.setLabel("bottom", "Time", units="sec", **label_style)
        layout.addWidget(self.waterfall, 0 + self.num_rows + 1, 2, self.num_rows, 1)
        self.img_array = np.ones((num_slices, fft_size)) * (-100)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def get_range_res(self):
        """Updates the slider bar label with Chirp bandwidth and range resolution"""
        bw = self.bw_slider.value() * 1e6
        range_res = c / (2 * bw)

    def get_cfar_values(self):
        """Updates the cfar values"""
        self.cfar_bias_label.setText("CFAR Bias (dB): %0.0f" % (self.cfar_bias.value()))
        self.cfar_guard_label.setText("Num Guard Cells: %0.0f" % (self.cfar_guard.value()))
        self.cfar_ref_label.setText("Num Ref Cells: %0.0f" % (self.cfar_ref.value()))

    def get_water_levels(self):
        """Updates the waterfall intensity levels"""
        if self.low_slider.value() > self.high_slider.value():
            self.low_slider.setValue(self.high_slider.value())
        self.low_label.setText("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.high_label.setText("HIGH LEVEL: %0.0f" % (self.high_slider.value()))

    def get_steer_angle(self):
        """Updates the steering angle readout"""
        self.steer_label.setText("%0.0f DEG" % (self.steer_slider.value()))
        phase_delta = (
            2
            * 3.14159
            * 10.25e9
            * 0.014
            * np.sin(np.radians(self.steer_slider.value()))
            / (3e8)
        )
        my_phaser.set_beam_phase_diff(np.degrees(phase_delta))

    def set_range_res(self):
        """Sets the Chirp bandwidth"""
        global dist, slope, signal_freq, plot_freq
        bw = self.bw_slider.value() * 1e6
        slope = bw / ramp_time_s
        dist = (freq - signal_freq) * c / (2 * slope)
        my_phaser.freq_dev_range = int(bw / 4)
        my_phaser.enable = 0

    def end_program(self):
        """Gracefully shuts down the program and Pluto"""
        my_sdr.tx_destroy_buffer()
        self.close()

    def change_thresh(self, state):
        """Toggles between showing cfar threshold values"""
        global plot_threshold
        plot_state = win.fft_plot.getViewBox().state
        if state == QtCore.Qt.Checked:
            plot_threshold = True
        else:
            plot_threshold = False

    def change_cfar(self, state):
        """Toggles between enabling/disabling CFAR"""
        global cfar_toggle
        if state == QtCore.Qt.Checked:
            cfar_toggle = True
        else:
            cfar_toggle = False


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
win = Window()
index = 0


rx_error_count = 0

def update():
    """Updates the FFT in the window"""
    global index, plot_threshold, freq, dist, rx_error_count
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
    data_fft = np.fft.fft(y, n=fft_size)
    sp = np.absolute(data_fft)
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))

    bias = win.cfar_bias.value()
    num_guard_cells = win.cfar_guard.value()
    num_ref_cells = win.cfar_ref.value()
    cfar_method = 'average'
    if (True):
        threshold, targets = cfar(s_dbfs, num_guard_cells, num_ref_cells, bias, cfar_method)
        s_dbfs_cfar = targets.filled(-200)
        s_dbfs_threshold = threshold

    win.fft_threshold.setData(freq, s_dbfs_threshold)
    if plot_threshold:
        win.fft_threshold.setVisible(True)
    else:
        win.fft_threshold.setVisible(False)

    win.img_array = np.roll(win.img_array, 1, axis=0)
    if cfar_toggle:
        win.fft_curve.setData(freq, s_dbfs_cfar)
        win.img_array[0] = s_dbfs_cfar
    else:
        win.fft_curve.setData(freq, s_dbfs)
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
