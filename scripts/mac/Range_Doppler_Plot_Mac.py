#!/usr/bin/env python3
"""
FMCW Range-Doppler Plot - Mac Edition

Real-time Range-Doppler map using the Phaser's TDD burst mode.
Runs the matplotlib visualization on your Mac while connecting to:
- PlutoSDR via Aleph's iiod proxy (ip:192.168.4.181:30431)
- Phaser via Raspberry Pi (ip:192.168.4.184)

This is the reference implementation for validating radar-web and tui-radar output.
Uses the same processing pipeline as ADI's original Range_Doppler_Plot.py.

Prerequisites:
    nix develop   # enters shell with all Python deps (pyadi-iio, matplotlib, etc.)

    # Stop radar-web first (exclusive SDR access):
    ssh aleph-phaser@192.168.4.181 'sudo systemctl stop radar-web'
    # Wait ~20s for Pluto to reboot after radar-web shutdown

Usage:
    cd scripts/mac
    python3 Range_Doppler_Plot_Mac.py

Based on Jon Kraft's Range_Doppler_Plot.py (Sept 25 2024), adapted for Aleph hybrid architecture.
"""

# Copyright (C) 2024 Analog Devices, Inc.
# Adapted for Aleph by Elodin, Feb 2026

import sys
import time
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
plt.close('all')

import adi
print(f"pyadi-iio version: {adi.__version__}")

# ============================================================================
# CONFIGURATION - Edit these to match your network
# ============================================================================

# Aleph IP - iiod proxies the PlutoSDR's IIO context on port 30431
aleph_ip = "192.168.4.181"
sdr_ip = f"ip:{aleph_ip}"  # Port 30431 is default for IIO

# Raspberry Pi (Phaser) IP
phaser_ip = "192.168.4.184"
rpi_ip = f"ip:{phaser_ip}"

# Key Radar Parameters (matching ADI's original defaults for comparison)
sample_rate = 4e6
center_freq = 2.1e9
signal_freq = 100e3
rx_gain = 60        # must be between -3 and 70
tx_gain = 0         # must be between 0 and -88
output_freq = 9.9e9
chirp_BW = 500e6
ramp_time = 300     # us (ADI default; our radar-web uses 100-500)
num_chirps = 256    # Doppler bins (ADI default; our radar-web uses 128-512)
max_range = 100     # display limit in meters
min_scale = 0
max_scale = 100
mti_filter = True

# ============================================================================

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
            # Also check label (PlutoSDR TDD device is named 'adi-iio-fakedev' with label 'iio-axi-tdd-0')
            label = getattr(dev, 'label', None) or ''
            if 'tdd' in label:
                for attr in dev.attrs:
                    if attr == 'enable':
                        if dev.attrs['enable'].value.strip() == '1':
                            dev.attrs['enable'].value = '0'
                            print("  ✓ Disabled leftover TDD engine (was blocking RX)")
                        return
    except Exception:
        pass  # Best effort

def reboot_pluto():
    """Reboot the PlutoSDR via the Aleph to reset the FPGA DMA engine.

    TDD burst mode leaves the Zynq FPGA's DMA controller in a triggered-only
    state. Only a full reboot restores free-running mode for CW demos.
    
    The Pluto is at 192.168.2.1 on the Aleph's USB-RNDIS network, which is
    not reachable from the Mac. So we SSH into the Aleph first, then from
    there SSH into the Pluto to reboot it, and finally restart iiod.
    """
    try:
        import paramiko
        # SSH to the Aleph
        aleph = paramiko.SSHClient()
        aleph.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        aleph.connect(aleph_ip, username='aleph-phaser', timeout=5)
        
        # From the Aleph, reboot the Pluto via its RNDIS address
        cmd = (
            "python3 -c \""
            "import paramiko; "
            "c=paramiko.SSHClient(); "
            "c.set_missing_host_key_policy(paramiko.AutoAddPolicy()); "
            "c.connect('192.168.2.1',username='root',password='analog',timeout=3); "
            "c.exec_command('reboot'); "
            "c.close(); "
            "print('Pluto reboot sent')"
            "\""
        )
        stdin, stdout, stderr = aleph.exec_command(cmd, timeout=10)
        result = stdout.read().decode().strip()
        print(f"  {result}")
        
        # Wait for Pluto to come back, then restart iiod
        import time
        print("  Waiting for Pluto to reboot (~20s)...")
        time.sleep(20)
        stdin, stdout, stderr = aleph.exec_command(
            "sudo systemctl restart iio-proxy", timeout=10
        )
        stdout.read()  # wait for completion
        print("  iiod proxy restarted")
        
        aleph.close()
        print("  PlutoSDR rebooted and iiod restarted. Ready for next demo.")
    except Exception as e:
        print(f"  Could not reboot PlutoSDR: {e}")
        print("  Run manually: ssh aleph-phaser@{} 'sudo systemctl restart iio-proxy'".format(aleph_ip))


# ============================================================================
# Connect to hardware
# ============================================================================
print("=" * 60)
print("Range-Doppler Plot - Mac Edition")
print("=" * 60)
print(f"Connecting to SDR via Aleph at {sdr_ip}")
print(f"Connecting to Phaser via Pi at {rpi_ip}")
print()

try:
    print("Connecting to PlutoSDR (via Aleph iiod)...")
    my_sdr = adi.ad9361(uri=sdr_ip)
    print("  ✓ PlutoSDR connected")
    disable_tdd(my_sdr)
except Exception as e:
    print(f"  ✗ Failed to connect to SDR: {e}")
    print()
    print("Make sure:")
    print(f"  1. Aleph is reachable at {aleph_ip}")
    print(f"  2. iio-proxy is running: ssh aleph-phaser@{aleph_ip} 'systemctl status iio-proxy'")
    print(f"  3. radar-web is stopped: ssh aleph-phaser@{aleph_ip} 'sudo systemctl stop radar-web'")
    print("  4. PlutoSDR is connected to Aleph USB")
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
try:
    my_phaser.load_gain_cal()
    my_phaser.load_phase_cal()
except:
    pass  # pyadi-iio prints its own "file not found" messages

for i in range(0, 8):
    my_phaser.set_chan_phase(i, 0)

gain_list = [127] * 8
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

# Configure SDR Rx
my_sdr.sample_rate = int(sample_rate)
my_sdr.rx_lo = int(center_freq)
my_sdr.rx_enabled_channels = [0, 1]
my_sdr.gain_control_mode_chan0 = 'manual'
my_sdr.gain_control_mode_chan1 = 'manual'
my_sdr.rx_hardwaregain_chan0 = int(rx_gain)
my_sdr.rx_hardwaregain_chan1 = int(rx_gain)

# Configure SDR Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True
my_sdr.tx_hardwaregain_chan0 = -88
my_sdr.tx_hardwaregain_chan1 = int(tx_gain)

# Configure the ADF4159 Ramping PLL
vco_freq = int(output_freq + signal_freq + center_freq)
BW = chirp_BW
num_steps = int(ramp_time)
my_phaser.frequency = int(vco_freq / 4)
my_phaser.freq_dev_range = int(BW / 4)
my_phaser.freq_dev_step = int((BW / 4) / num_steps)
my_phaser.freq_dev_time = int(ramp_time)
my_phaser.delay_word = 4095
my_phaser.delay_clk = "PFD"
my_phaser.delay_start_en = 0
my_phaser.ramp_delay_en = 0
my_phaser.trig_delay_en = 0
my_phaser.ramp_mode = "single_sawtooth_burst"
my_phaser.sing_ful_tri = 0
my_phaser.tx_trig_en = 1
my_phaser.enable = 0

print(f"  ✓ ADF4159 configured (ramp_time={ramp_time}us, BW={BW/1e6:.0f}MHz)")

# ============================================================================
# Configure TDD controller
# ============================================================================
sdr_pins = adi.one_bit_adc_dac(sdr_ip)
sdr_pins.gpio_tdd_ext_sync = True
tdd = adi.tddn(sdr_ip)
sdr_pins.gpio_phaser_enable = True
tdd.enable = False
tdd.sync_external = True
tdd.startup_delay_ms = 0
PRI_ms = ramp_time / 1e3 + 0.2
tdd.frame_length_ms = PRI_ms
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

print(f"  ✓ TDD configured (PRI={PRI_ms:.2f}ms, burst_count={num_chirps})")

# ============================================================================
# Calculate ramp parameters
# ============================================================================
ramp_time = int(my_phaser.freq_dev_time)
ramp_time_s = ramp_time / 1e6
begin_offset_time = 0.1 * ramp_time_s
good_ramp_samples = int((ramp_time_s - begin_offset_time) * sample_rate)
start_offset_time = tdd.channel[0].on_ms / 1e3 + begin_offset_time
start_offset_samples = int(start_offset_time * sample_rate)

# Size the FFT for the number of ramp data points
power = 8
fft_size = int(2**power)
num_samples_frame = int(tdd.frame_length_ms / 1000 * sample_rate)
while num_samples_frame > fft_size:
    power = power + 1
    fft_size = int(2**power)
    if power == 18:
        break

# Buffer size (power of 2, large enough for all chirps)
total_time = tdd.frame_length_ms * num_chirps
buffer_time = 0
power = 12
while total_time > buffer_time:
    power = power + 1
    buffer_size = int(2**power)
    buffer_time = buffer_size / sample_rate * 1000
    if power == 23:
        break
my_sdr.rx_buffer_size = buffer_size

PRI_s = PRI_ms / 1e3
PRF = 1 / PRI_s
num_bursts = tdd.burst_count
N_frame = int(PRI_s * float(sample_rate))

# Range axis
c = 3e8
wavelength = c / output_freq
slope = BW / ramp_time_s
freq = np.linspace(-sample_rate / 2, sample_rate / 2, N_frame)
dist = (freq - signal_freq) * c / (2 * slope)

# Resolutions
R_res = c / (2 * BW)
v_res = wavelength / (2 * num_bursts * PRI_s)
max_doppler_freq = PRF / 2
max_doppler_vel = max_doppler_freq * wavelength / 2

print(f"  ✓ Radar parameters:")
print(f"    good_ramp_samples={good_ramp_samples}, buffer_size={buffer_size}")
print(f"    Range resolution: {R_res:.2f}m, Velocity resolution: {v_res:.3f}m/s")
print(f"    Max Doppler velocity: {max_doppler_vel:.1f}m/s")

# ============================================================================
# Create and transmit waveform
# ============================================================================
N = int(2**18)
fc = int(signal_freq)
ts = 1 / float(sample_rate)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 0.9 * (i + 1j * q)
my_sdr.tx([iq, iq])

print(f"  ✓ TX waveform started")
print()

# ============================================================================
# Data collection and processing functions
# ============================================================================
def get_radar_data():
    """Trigger a TDD burst and capture the radar data."""
    # Trigger burst via Phaser GPIO (goes to Pi at 192.168.4.184)
    my_phaser._gpios.gpio_burst = 0
    my_phaser._gpios.gpio_burst = 1
    my_phaser._gpios.gpio_burst = 0
    data = my_sdr.rx()
    chan1 = data[0]
    chan2 = data[1]
    sum_data = chan1 + chan2

    # Reshape into chirps
    rx_bursts = np.zeros((num_bursts, good_ramp_samples), dtype=complex)
    for burst in range(num_bursts):
        start_index = start_offset_samples + burst * N_frame
        stop_index = start_index + good_ramp_samples
        rx_bursts[burst] = sum_data[start_index:stop_index]

    return rx_bursts


def freq_process(data):
    """2D FFT processing: Range-Doppler map."""
    rx_bursts_fft = np.fft.fftshift(abs(np.fft.fft2(data)))
    range_doppler_data = np.log10(rx_bursts_fft).T
    range_doppler_data = np.clip(range_doppler_data, min_scale, max_scale)
    return range_doppler_data


# ============================================================================
# Export function
# ============================================================================
import json
import os
from datetime import datetime

export_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'exports', 'mac_rd')

def export_frame(rx_bursts_raw, radar_data_processed):
    """Export current frame data for comparison with radar-web.

    Saves:
    - rx_bursts_raw.npy: pre-FFT complex IQ chirps, shape (num_chirps, good_ramp_samples)
    - radar_data_processed.npy: post-FFT, transposed, log10 clipped, shape (n_range, n_doppler)
    - metadata.json: all radar parameters for reproducibility
    - screenshot.png: current matplotlib display
    """
    os.makedirs(export_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    prefix = os.path.join(export_dir, ts)

    np.save(f'{prefix}_rx_bursts.npy', rx_bursts_raw)
    np.save(f'{prefix}_rd_map.npy', radar_data_processed)

    metadata = {
        'timestamp': ts,
        'source': 'Range_Doppler_Plot_Mac.py (ADI reference)',
        'sample_rate': sample_rate,
        'center_freq': center_freq,
        'signal_freq': signal_freq,
        'output_freq': output_freq,
        'chirp_BW': chirp_BW,
        'ramp_time_us': ramp_time,
        'num_chirps': num_chirps,
        'good_ramp_samples': good_ramp_samples,
        'rx_gain': rx_gain,
        'tx_gain': tx_gain,
        'mti_filter': mti_filter,
        'min_scale': min_scale,
        'max_scale': max_scale,
        'max_range': max_range,
        'PRI_ms': PRI_ms,
        'PRF': PRF,
        'R_res_m': R_res,
        'v_res_mps': v_res,
        'max_doppler_vel_mps': max_doppler_vel,
        'buffer_size': buffer_size,
        'rx_bursts_shape': list(rx_bursts_raw.shape),
        'rd_map_shape': list(radar_data_processed.shape),
        'rd_map_dtype': str(radar_data_processed.dtype),
        'axes': 'rd_map is (n_range_bins, n_doppler_bins) after .T; imshow rows=Y=Range, cols=X=Velocity',
    }
    with open(f'{prefix}_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    range_doppler_fig.savefig(f'{prefix}_screenshot.png', dpi=150, bbox_inches='tight')
    print(f"  Exported to {export_dir}/{ts}_*")


# ============================================================================
# Main display loop
# ============================================================================
print("Capturing first frame...")
rx_bursts = get_radar_data()
radar_data = freq_process(rx_bursts)

range_doppler_fig, ax = plt.subplots(figsize=(14, 7))
extent = [-max_doppler_vel, max_doppler_vel, dist.min(), dist.max()]
cmn = 'inferno'
try:
    range_doppler = ax.imshow(radar_data, aspect='auto',
        extent=extent, origin='lower', cmap=matplotlib.colormaps.get_cmap(cmn))
except:
    from matplotlib.cm import get_cmap
    range_doppler = ax.imshow(radar_data, aspect='auto', vmin=0, vmax=8,
        extent=extent, origin='lower', cmap=get_cmap(cmn))
ax.set_title('Range Doppler Spectrum (Aleph + Phaser)', fontsize=24)
ax.set_xlabel('Velocity [m/s]', fontsize=22)
ax.set_ylabel('Range [m]', fontsize=22)
ax.set_xlim([-10, 10])
ax.set_ylim([0, max_range])
ax.set_yticks(np.arange(0, max_range, max_range / 20))
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

# Key press handler for export
def on_key(event):
    if event.key == 's':
        print("  Exporting frame...")
        export_frame(last_rx_bursts, last_radar_data)

range_doppler_fig.canvas.mpl_connect('key_press_event', on_key)

print(f"sample_rate = {sample_rate/1e6:.1f} MHz, ramp_time = {ramp_time} us, num_chirps = {num_chirps}")
print(f"MTI filter: {'ON' if mti_filter else 'OFF'}")
print("Press 's' to export current frame | CTRL+C to stop")
print()

last_rx_bursts = rx_bursts
last_radar_data = radar_data

try:
    while True:
        rx_bursts = get_radar_data()
        last_rx_bursts = rx_bursts  # Save for export
        if mti_filter:
            rx_chirps = rx_bursts
            num_samples = len(rx_chirps[0])
            Chirp2P = np.ones([num_chirps, num_samples]) * 1j
            for chirp in range(num_chirps - 1):
                chirpI = rx_chirps[chirp, :]
                chirpI1 = rx_chirps[chirp + 1, :]
                chirp_correlation = np.correlate(chirpI, chirpI1, 'valid')
                angle_diff = np.angle(chirp_correlation, deg=False)
                Chirp2P[chirp:] = chirpI1 - chirpI * np.exp(-1j * angle_diff[0])
            rx_bursts = Chirp2P

        radar_data = freq_process(rx_bursts)
        last_radar_data = radar_data  # Save for export
        range_doppler.set_data(radar_data)
        plt.show(block=False)
        plt.pause(.1)
except KeyboardInterrupt:
    print()
    print("Stopping...")

# ============================================================================
# Cleanup
# ============================================================================
print("Cleaning up...")
try:
    tdd.enable = False
    sdr_pins.gpio_tdd_ext_sync = False
    my_sdr.tx_destroy_buffer()
    print("  ✓ TDD disabled, TX buffer cleared")
except Exception as e:
    print(f"  ⚠ Cleanup error: {e}")

# Reboot the PlutoSDR to reset the FPGA DMA engine.
# This is necessary so that CW demos work afterward.
print("  Rebooting PlutoSDR to restore clean DMA state...")
reboot_pluto()
print("Done.")
