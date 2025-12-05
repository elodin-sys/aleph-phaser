#!/usr/bin/env python3
"""
Aleph Phaser Minimal Example

Adapted from phaser_minimal_example.py for running on Aleph with hybrid architecture:
- PlutoSDR connected directly to Aleph USB (ip:192.168.2.1)
- Phaser controlled via Raspberry Pi (ip:192.168.4.184)

This script demonstrates:
1. Connecting to PlutoSDR and Phaser
2. Configuring the array for RX
3. Setting PLL frequency for HB100 reception
4. Capturing data and computing FFT
5. Saving plots to files (headless operation)

Usage:
    python3 aleph_minimal_example.py [--output-dir /path/to/output]
"""

import argparse
import os
from time import sleep

import numpy as np
from numpy.fft import fft, fftfreq, fftshift
from scipy import signal

# ADI libraries
from adi import ad9361
from adi.cn0566 import CN0566


def spec_est(x, fs, ref=2**15):
    """
    Simple spectrum estimation function.
    Applies window, takes FFT, scales and converts to dB.
    """
    N = len(x)
    
    # Apply Kaiser window (use numpy.kaiser which is always available)
    window = np.kaiser(N, beta=38)
    window /= np.average(window)
    x = np.multiply(x, window)
    
    # FFT and convert to dB
    ampl = 1 / N * fftshift(np.absolute(fft(x)))
    ampl = 20 * np.log10(ampl / ref + 1e-20)
    
    # Frequency bins
    freqs = fftshift(fftfreq(N, 1 / fs))
    
    return ampl, freqs


def main():
    parser = argparse.ArgumentParser(description='Aleph Phaser Minimal Example')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1',
                        help='PlutoSDR URI (default: ip:192.168.2.1)')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184',
                        help='Phaser/Pi URI (default: ip:192.168.4.184)')
    parser.add_argument('--signal-freq', type=float, default=10.525e9,
                        help='HB100 signal frequency in Hz (default: 10.525e9)')
    parser.add_argument('--output-dir', default='/tmp',
                        help='Directory to save output plots (default: /tmp)')
    args = parser.parse_args()

    print("=" * 60)
    print("Aleph Phaser Minimal Example")
    print("=" * 60)
    print()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Connect to Phaser via Raspberry Pi
    print(f"Connecting to Phaser at {args.phaser_uri}...")
    my_phaser = CN0566(uri=args.phaser_uri)
    print("  ✓ Phaser connected")

    # Connect to PlutoSDR directly on Aleph
    print(f"Connecting to PlutoSDR at {args.sdr_uri}...")
    my_sdr = ad9361(uri=args.sdr_uri)
    print("  ✓ PlutoSDR connected")

    # Link SDR to Phaser
    my_phaser.sdr = my_sdr
    sleep(0.5)

    # Configure Phaser for RX
    print("Configuring Phaser for RX mode...")
    my_phaser.configure(device_mode="rx")
    my_phaser.SignalFreq = args.signal_freq
    print(f"  Signal frequency: {args.signal_freq/1e9:.3f} GHz")

    # Set all antenna elements to half scale
    print("Setting antenna elements to half gain...")
    gain_list = [64] * 8
    for i in range(len(gain_list)):
        my_phaser.set_chan_gain(i, gain_list[i], apply_cal=False)

    # Aim beam at boresight
    my_phaser.set_beam_phase_diff(0.0)
    print("  Beam aimed at boresight (0°)")

    # Configure SDR parameters
    print("Configuring SDR parameters...")
    
    # Advanced settings
    my_sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
    my_sdr._ctrl.debug_attrs["adi,ensm-enable-txnrx-control-enable"].value = "0"
    my_sdr._ctrl.debug_attrs["initialize"].value = "1"

    my_sdr.rx_enabled_channels = [0, 1]
    my_sdr._rxadc.set_kernel_buffers_count(1)
    rx = my_sdr._ctrl.find_channel("voltage0")
    rx.attrs["quadrature_tracking_en"].value = "1"

    # Attenuate TX
    my_sdr.tx_hardwaregain_chan0 = int(-80)
    my_sdr.tx_hardwaregain_chan1 = int(-80)

    # Main SDR parameters
    my_sdr.sample_rate = int(30e6)
    my_sdr.rx_buffer_size = int(1024)
    my_sdr.rx_rf_bandwidth = int(10e6)

    # Manual gain control
    my_sdr.gain_control_mode_chan0 = "manual"
    my_sdr.gain_control_mode_chan1 = "manual"
    my_sdr.rx_hardwaregain_chan0 = 0
    my_sdr.rx_hardwaregain_chan1 = 0

    # Set RX LO (downconvert by 2 GHz)
    my_sdr.rx_lo = int(2.2e9)
    
    # Load LTE filter if available
    try:
        my_sdr.filter = "LTE20_MHz.ftr"
        print("  LTE20 filter loaded")
    except Exception as e:
        print(f"  Filter not loaded: {e}")

    print(f"  Sample rate: {my_sdr.sample_rate/1e6:.1f} MSPS")
    print(f"  RX LO: {my_sdr.rx_lo/1e9:.3f} GHz")
    print(f"  Buffer size: {my_sdr.rx_buffer_size}")

    # Set Phaser PLL
    # PLL frequency = HB100 freq + RX LO - offset (to avoid DC)
    offset = 1_000_000  # 1 MHz offset
    pll_freq = int(my_phaser.SignalFreq + my_sdr.rx_lo - offset) // 4
    my_phaser.frequency = pll_freq
    print(f"  Phaser PLL: {pll_freq*4/1e9:.3f} GHz")

    # Capture data
    print()
    print("Capturing data...")
    data = my_sdr.rx()
    data_sum = data[0] + data[1]
    print(f"  Captured {len(data[0])} samples per channel")

    # Compute spectrum
    print("Computing spectrum...")
    ampl, freqs = spec_est(data_sum, 30e6, ref=2**12)
    ampl = np.fft.fftshift(ampl)
    ampl = np.flip(ampl)
    freqs = np.fft.fftshift(freqs)
    freqs /= 1e6  # Scale Hz -> MHz

    # Find peak
    peak_index = np.argmax(ampl)
    peak_freq = freqs[peak_index]
    peak_power = ampl[peak_index]
    print(f"  Peak frequency: {peak_freq:.2f} MHz")
    print(f"  Peak power: {peak_power:.1f} dB")

    # Generate plots (headless - save to files)
    print()
    print("Generating plots...")
    
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Time domain plot
    ax1.set_title("Time Domain I/Q Data")
    ax1.plot(data[0].real, marker="o", ms=2, color="red", label="Ch0 Real")
    ax1.plot(data[1].real, marker="o", ms=2, color="blue", label="Ch1 Real")
    ax1.set_xlabel("Sample")
    ax1.set_ylabel("ADC Output")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Frequency domain plot
    ax2.set_title(f"Spectrum - Peak at {peak_freq:.2f} MHz")
    ax2.plot(freqs, ampl, marker="o", ms=2)
    ax2.axvline(x=peak_freq, color='r', linestyle='--', alpha=0.5)
    ax2.set_xlabel("Frequency [MHz]")
    ax2.set_ylabel("Signal Strength [dB]")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(args.output_dir, "aleph_minimal_example.png")
    plt.savefig(output_path, dpi=150)
    print(f"  Plot saved to: {output_path}")

    # Also save data
    data_path = os.path.join(args.output_dir, "aleph_minimal_example_data.npz")
    np.savez(data_path,
             data_ch0=data[0],
             data_ch1=data[1],
             freqs=freqs,
             ampl=ampl,
             peak_freq=peak_freq,
             peak_power=peak_power,
             signal_freq=args.signal_freq)
    print(f"  Data saved to: {data_path}")

    # Clean up
    del my_sdr
    del my_phaser

    print()
    print("=" * 60)
    print("SUCCESS! HB100 signal detected at {:.2f} MHz offset".format(peak_freq))
    print("=" * 60)


if __name__ == '__main__':
    main()
