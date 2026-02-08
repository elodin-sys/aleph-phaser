#!/usr/bin/env python3
"""
FMCW Radar Waterfall with ChirpSync Demo - Mac Edition

Uses the Pluto TDD engine for synchronized chirp FFT data collection.
Requires PlutoSDR firmware v0.39 or later.

Prerequisites (on Mac):
    cd scripts/mac
    uv venv --python 3.12
    source .venv/bin/activate
    uv sync

Usage:
    python3 FMCW_RADAR_Waterfall_ChirpSync_Mac.py

Based on Jon Kraft's FMCW ChirpSync Demo.
"""

# Copyright (C) 2024 Analog Devices, Inc.
# Adapted for Aleph by Elodin, Dec 2024

import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from pyqtgraph.Qt import QtCore, QtGui

import adi
print(f"pyadi-iio version: {adi.__version__}")

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

# Key Parameters
sample_rate = 5e6
center_freq = 2.1e9
signal_freq = 100e3
rx_gain = 20   # must be between -3 and 70
output_freq = 10e9
default_chirp_bw = 500e6
ramp_time = 500      # ramp time in us
num_slices = 400     # this sets how much time will be displayed on the waterfall plot
plot_freq = 100e3    # x-axis freq range to plot

print("=" * 60)
print("FMCW Radar Waterfall (ChirpSync) - Mac Edition")
print("=" * 60)
print(f"Connecting to SDR via Aleph at {sdr_ip}")
print(f"Connecting to Phaser via Pi at {rpi_ip}")
print("NOTE: This demo requires PlutoSDR firmware v0.39 or later")
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
my_phaser.element_spacing = 0.014

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

# Configure SDR Rx
my_sdr.sample_rate = int(sample_rate)
sample_rate = int(my_sdr.sample_rate)
my_sdr.rx_lo = int(center_freq)
my_sdr.rx_enabled_channels = [0, 1]
my_sdr.gain_control_mode_chan0 = "manual"
my_sdr.gain_control_mode_chan1 = "manual"
my_sdr.rx_hardwaregain_chan0 = int(rx_gain)
my_sdr.rx_hardwaregain_chan1 = int(rx_gain)

# Configure SDR Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True
my_sdr.tx_hardwaregain_chan0 = -88
my_sdr.tx_hardwaregain_chan1 = -0

# Configure the ADF4159 Ramping PLL
vco_freq = int(output_freq + signal_freq + center_freq)
BW = default_chirp_bw
num_steps = int(ramp_time)    # in general it works best if there is 1 step per us
my_phaser.frequency = int(vco_freq / 4)
my_phaser.freq_dev_range = int(BW / 4)
my_phaser.freq_dev_step = int((BW / 4) / num_steps)
my_phaser.freq_dev_time = int(ramp_time)
print(f"  Requested freq dev time = {ramp_time} us")
my_phaser.delay_word = 4095
my_phaser.delay_clk = "PFD"
my_phaser.delay_start_en = 0
my_phaser.ramp_delay_en = 0
my_phaser.trig_delay_en = 0
my_phaser.ramp_mode = "single_sawtooth_burst"
my_phaser.sing_ful_tri = 0
my_phaser.tx_trig_en = 1  # start a ramp with TXdata
my_phaser.enable = 0

# Configure TDD controller
print("  Configuring TDD controller...")
sdr_pins = adi.one_bit_adc_dac(sdr_ip)
sdr_pins.gpio_tdd_ext_sync = True
tdd = adi.tddn(sdr_ip)
sdr_pins.gpio_phaser_enable = True
tdd.enable = False
tdd.sync_external = True
tdd.startup_delay_ms = 0
PRI_ms = ramp_time/1e3 + 1.0
tdd.frame_length_ms = PRI_ms
num_chirps = 1
tdd.burst_count = num_chirps

tdd.channel[0].enable = True
tdd.channel[0].polarity = False
tdd.channel[0].on_raw = 0
tdd.channel[0].off_raw = 10
tdd.channel[1].enable = True
tdd.channel[1].polarity = False
tdd.channel[1].on_raw = 0
tdd.channel[1].off_raw = 10
tdd.channel[2].enable = True
tdd.channel[2].polarity = False
tdd.channel[2].on_raw = 0
tdd.channel[2].off_raw = 10
tdd.enable = True

# From start of each ramp, how many "good" points do we want?
ramp_time = int(my_phaser.freq_dev_time)
ramp_time_s = ramp_time / 1e6
begin_offset_time = 0.10 * ramp_time_s
print(f"  Actual freq dev time = {ramp_time} us")
good_ramp_samples = int((ramp_time_s - begin_offset_time) * sample_rate)
start_offset_time = tdd.channel[0].on_ms/1e3 + begin_offset_time
start_offset_samples = int(start_offset_time * sample_rate)

# size the fft for the number of ramp data points
power = 8
fft_size = int(2**power)
num_samples_frame = int(tdd.frame_length_ms/1000*sample_rate)
while num_samples_frame > fft_size:
    power = power + 1
    fft_size = int(2**power)
    if power == 18:
        break
print(f"  FFT size = {fft_size}")

# Pluto receive buffer size needs to be greater than total time for all chirps
total_time = tdd.frame_length_ms * num_chirps
print(f"  Total time for all chirps: {total_time} ms")
buffer_time = 0
power = 12
while total_time > buffer_time:
    power = power + 1
    buffer_size = int(2**power)
    buffer_time = buffer_size/my_sdr.sample_rate*1000
    if power == 23:
        break
print(f"  Buffer size: {buffer_size}")
my_sdr.rx_buffer_size = buffer_size
print(f"  Buffer time: {buffer_time} ms")

# Calculate ramp parameters
c = 3e8
wavelength = c / output_freq
freq = np.linspace(-sample_rate / 2, sample_rate / 2, int(fft_size))
slope = BW / ramp_time_s
dist = (freq - signal_freq) * c / (2 * slope)
plot_dist = False

print(f"""
CONFIG:
  Sample rate: {sample_rate / 1e6} MHz
  Num samples: 2^{int(np.log2(my_sdr.rx_buffer_size))}
  Bandwidth: {BW / 1e6} MHz
  Ramp time: {ramp_time / 1e3} ms
  Output frequency: {output_freq / 1e6} MHz
  IF: {signal_freq / 1e3} kHz
""")

# Create a sinewave waveform
N = int(2**18)
fc = int(signal_freq)
ts = 1 / float(sample_rate)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 1 * (i + 1j * q)

# transmit data from Pluto
print("  Starting Tx...")
my_sdr._ctx.set_timeout(30000)
my_sdr._rx_init_channels()
my_sdr.tx([iq, iq])

print()
print("Starting Qt display...")
print("Close the window to exit.")
print()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FMCW Radar ChirpSync - Aleph/Mac")
        self.setGeometry(0, 0, 400, 400)
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.num_rows = 12
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        widget = QWidget()

        global layout, signal_freq, fft_size, plot_freq
        layout = QGridLayout()

        # Control Panel
        control_label = QLabel("PHASER FMCW ChirpSync (Aleph/Mac)")
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
        self.x_axis_check = QCheckBox("Convert to Distance")
        font = self.x_axis_check.font()
        font.setPointSize(10)
        self.x_axis_check.setFont(font)
        self.x_axis_check.stateChanged.connect(self.change_x_axis)
        layout.addWidget(self.x_axis_check, 2, 0)

        # Range resolution
        self.range_res_label = QLabel(
            "B: %0.2f MHz - R<sub>res</sub>: %0.2f m"
            % (default_chirp_bw / 1e6, c / (2 * default_chirp_bw))
        )
        font = self.range_res_label.font()
        font.setPointSize(10)
        self.range_res_label.setFont(font)
        self.range_res_label.setAlignment(Qt.AlignLeft)
        self.range_res_label.setMaximumWidth(200)
        self.range_res_label.setMinimumWidth(100)
        layout.addWidget(self.range_res_label, 4, 1)

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

        # waterfall level slider
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setMinimum(-100)
        self.low_slider.setMaximum(20)
        self.low_slider.setValue(-30)
        self.low_slider.setTickInterval(20)
        self.low_slider.setMaximumWidth(200)
        self.low_slider.setTickPosition(QSlider.TicksBelow)
        self.low_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.low_slider, 8, 0)

        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setMinimum(-100)
        self.high_slider.setMaximum(20)
        self.high_slider.setValue(5)
        self.high_slider.setTickInterval(20)
        self.high_slider.setMaximumWidth(200)
        self.high_slider.setTickPosition(QSlider.TicksBelow)
        self.high_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.high_slider, 10, 0)

        self.water_label = QLabel("Waterfall Intensity Levels")
        self.water_label.setFont(font)
        self.water_label.setAlignment(Qt.AlignCenter)
        self.water_label.setMinimumWidth(100)
        self.water_label.setMaximumWidth(200)
        layout.addWidget(self.water_label, 7, 0, 1, 1)
        self.low_label = QLabel("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.low_label.setFont(font)
        self.low_label.setAlignment(Qt.AlignLeft)
        self.low_label.setMinimumWidth(100)
        self.low_label.setMaximumWidth(200)
        layout.addWidget(self.low_label, 8, 1)
        self.high_label = QLabel("HIGH LEVEL: %0.0f" % (self.high_slider.value()))
        self.high_label.setFont(font)
        self.high_label.setAlignment(Qt.AlignLeft)
        self.high_label.setMinimumWidth(100)
        self.high_label.setMaximumWidth(200)
        layout.addWidget(self.high_label, 10, 1)

        self.steer_slider = QSlider(Qt.Horizontal)
        self.steer_slider.setMinimum(-80)
        self.steer_slider.setMaximum(80)
        self.steer_slider.setValue(0)
        self.steer_slider.setTickInterval(20)
        self.steer_slider.setMaximumWidth(200)
        self.steer_slider.setTickPosition(QSlider.TicksBelow)
        self.steer_slider.valueChanged.connect(self.get_steer_angle)
        layout.addWidget(self.steer_slider, 14, 0)
        self.steer_title = QLabel("Receive Steering Angle")
        self.steer_title.setFont(font)
        self.steer_title.setAlignment(Qt.AlignCenter)
        self.steer_title.setMinimumWidth(100)
        self.steer_title.setMaximumWidth(200)
        layout.addWidget(self.steer_title, 13, 0)
        self.steer_label = QLabel("%0.0f DEG" % (self.steer_slider.value()))
        self.steer_label.setFont(font)
        self.steer_label.setAlignment(Qt.AlignLeft)
        self.steer_label.setMinimumWidth(100)
        self.steer_label.setMaximumWidth(200)
        layout.addWidget(self.steer_label, 14, 1, 1, 2)

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
        self.fft_plot.setXRange(signal_freq, signal_freq + plot_freq)

        # Waterfall plot
        self.waterfall = pg.PlotWidget()
        self.imageitem = pg.ImageItem()
        self.waterfall.addItem(self.imageitem)
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([[68, 1, 84, 255], [59, 82, 139, 255], [33, 145, 140, 255],
                          [94, 201, 98, 255], [253, 231, 37, 255]], dtype=np.ubyte)
        lut = pg.ColorMap(pos, color).getLookupTable(0.0, 1.0, 256)
        self.imageitem.setLookupTable(lut)
        self.imageitem.setLevels([0, 1])
        tr = QtGui.QTransform()
        tr.translate(0, -sample_rate / 2)
        tr.scale(0.35, sample_rate / fft_size)
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
        """Updates the slider bar label with RF bandwidth and range resolution"""
        bw = self.bw_slider.value() * 1e6
        range_res = c / (2 * bw)
        self.range_res_label.setText(
            "B: %0.2f MHz - R<sub>res</sub>: %0.2f m"
            % (bw / 1e6, c / (2 * bw))
        )

    def get_water_levels(self):
        """Updates the waterfall intensity levels"""
        if self.low_slider.value() > self.high_slider.value():
            self.low_slider.setValue(self.high_slider.value())
        self.low_label.setText("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.high_label.setText("HIGH LEVEL: %0.0f" % (self.high_slider.value()))

    def get_steer_angle(self):
        """Updates the steering angle readout"""
        self.steer_label.setText("%0.0f DEG" % (self.steer_slider.value()))
        phase_delta = (2 * 3.14159 * output_freq * my_phaser.element_spacing
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
        if self.x_axis_check.isChecked() == True:
            plot_dist = True
            range_x = (plot_freq) * c / (2 * slope)
            self.fft_plot.setXRange(0, range_x)
        else:
            plot_dist = False
            self.fft_plot.setXRange(signal_freq, signal_freq + plot_freq)
        my_phaser.freq_dev_range = int(bw / 4)
        my_phaser.enable = 0

    def end_program(self):
        """Gracefully shuts down the program and Pluto"""
        my_sdr.tx_destroy_buffer()
        print("Program finished and Pluto Tx Buffer Cleared")
        # disable TDD and revert to non-TDD (standard) mode
        tdd.enable = False
        sdr_pins.gpio_phaser_enable = False
        tdd.channel[1].polarity = not(sdr_pins.gpio_phaser_enable)
        tdd.channel[2].polarity = sdr_pins.gpio_phaser_enable
        tdd.enable = True
        tdd.enable = False
        self.close()

    def change_x_axis(self, state):
        """Toggles between showing frequency and range for the x-axis"""
        global plot_dist, slope, signal_freq, plot_freq
        plot_state = win.fft_plot.getViewBox().state
        if state == QtCore.Qt.Checked:
            plot_dist = True
            range_x = (plot_freq) * c / (2 * slope)
            self.fft_plot.setXRange(0, range_x)
        else:
            plot_dist = False
            self.fft_plot.setXRange(signal_freq, signal_freq + plot_freq)


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
win = Window()
index = 0


def update():
    """Updates the FFT in the window"""
    global index, plot_dist, freq, dist, ramp_time_s, sample_rate
    label_style = {"color": "#FFF", "font-size": "14pt"}
    my_phaser._gpios.gpio_burst = 0
    my_phaser._gpios.gpio_burst = 1
    my_phaser._gpios.gpio_burst = 0
    data = my_sdr.rx()
    chan1 = data[0]
    chan2 = data[1]
    sum_data = chan1 + chan2

    # select just the linear portion of the last chirp
    rx_bursts = np.zeros((num_chirps, good_ramp_samples), dtype=complex)
    for burst in range(num_chirps):
        start_index = start_offset_samples + burst * num_samples_frame
        stop_index = start_index + good_ramp_samples
        rx_bursts[burst] = sum_data[start_index:stop_index]
        burst_data = np.ones(fft_size, dtype=complex) * 1e-10
        win_funct = np.ones(len(rx_bursts[burst]))
        burst_data[start_offset_samples:(start_offset_samples + good_ramp_samples)] = rx_bursts[burst] * win_funct

    sp = np.absolute(np.fft.fft(burst_data))
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))

    if plot_dist:
        win.fft_curve.setData(dist, s_dbfs)
        win.fft_plot.setLabel("bottom", text="Distance", units="m", **label_style)
    else:
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
sys.exit(App.exec())
