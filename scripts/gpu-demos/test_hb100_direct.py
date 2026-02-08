#!/usr/bin/env python3
"""
Minimal HB100 detection test - NumPy only, no GPU required.

Connects directly to the Phaser hardware (bypassing radar-web) and captures
a range-Doppler frame. Saves the raw IQ data and processed range-Doppler map
for offline analysis.

Based on Jon Kraft's FMCW Range-Doppler demo, simplified for diagnosis.

Usage (on device, after stopping radar-web):
    sudo systemctl stop radar-web
    python3 test_hb100_direct.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
    python3 test_hb100_direct.py --sdr-uri usb: --phaser-uri ip:192.168.4.184
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

# matplotlib for saving plots (non-interactive)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import adi


def setup_hardware(sdr_uri, phaser_uri, sample_rate=4e6, center_freq=2.1e9,
                   signal_freq=100e3, rx_gain=30, output_freq=9.9e9,
                   chirp_bw=500e6, ramp_time_us=500, num_chirps=256):
    """Configure Phaser hardware exactly like Jon Kraft's reference script."""
    
    print(f"Connecting SDR: {sdr_uri}")
    print(f"Connecting Phaser: {phaser_uri}")
    
    my_sdr = adi.ad9361(uri=sdr_uri)
    my_phaser = adi.CN0566(uri=phaser_uri, sdr=my_sdr)
    
    # Configure Phaser
    my_phaser.configure(device_mode="rx")
    my_phaser.element_spacing = 0.014
    my_phaser.load_gain_cal()
    my_phaser.load_phase_cal()
    for i in range(8):
        my_phaser.set_chan_phase(i, 0)
        my_phaser.set_chan_gain(i, 127, apply_cal=True)
    
    # GPIOs
    my_phaser._gpios.gpio_tx_sw = 0
    my_phaser._gpios.gpio_vctrl_1 = 1
    my_phaser._gpios.gpio_vctrl_2 = 1
    
    # SDR Rx
    my_sdr.sample_rate = int(sample_rate)
    my_sdr.rx_lo = int(center_freq)
    my_sdr.rx_enabled_channels = [0, 1]
    my_sdr.gain_control_mode_chan0 = 'manual'
    my_sdr.gain_control_mode_chan1 = 'manual'
    my_sdr.rx_hardwaregain_chan0 = int(rx_gain)
    my_sdr.rx_hardwaregain_chan1 = int(rx_gain)
    
    # SDR Tx
    my_sdr.tx_lo = int(center_freq)
    my_sdr.tx_enabled_channels = [0, 1]
    my_sdr.tx_cyclic_buffer = True
    my_sdr.tx_hardwaregain_chan0 = -88
    my_sdr.tx_hardwaregain_chan1 = 0
    
    # ADF4159 ramping PLL
    vco_freq = int(output_freq + signal_freq + center_freq)
    num_steps = int(ramp_time_us)
    my_phaser.frequency = int(vco_freq / 4)
    my_phaser.freq_dev_range = int(chirp_bw / 4)
    my_phaser.freq_dev_step = int((chirp_bw / 4) / num_steps)
    my_phaser.freq_dev_time = int(ramp_time_us)
    my_phaser.delay_word = 4095
    my_phaser.delay_clk = "PFD"
    my_phaser.delay_start_en = 0
    my_phaser.ramp_delay_en = 0
    my_phaser.trig_delay_en = 0
    my_phaser.ramp_mode = "single_sawtooth_burst"
    my_phaser.sing_ful_tri = 0
    my_phaser.tx_trig_en = 1
    my_phaser.enable = 0
    
    # TDD setup (using IP-mode one_bit_adc_dac for proper gpio routing)
    sdr_pins = adi.one_bit_adc_dac(sdr_uri)
    tdd = adi.tddn(sdr_uri)
    
    sdr_pins.gpio_tdd_ext_sync = True
    sdr_pins.gpio_phaser_enable = True
    
    pri_us = ramp_time_us + 200  # PRI = ramp + guard
    pri_ms = pri_us / 1000.0
    
    tdd.enable = False
    tdd.sync_external = True
    tdd.startup_delay_ms = 0
    tdd.frame_length_ms = pri_ms
    tdd.burst_count = num_chirps
    
    for ch in range(3):
        tdd.channel[ch].enable = True
        tdd.channel[ch].polarity = False
        tdd.channel[ch].on_raw = 0
        tdd.channel[ch].off_raw = 10
    
    tdd.enable = True
    
    # Tx waveform - create a constant tone at signal_freq
    # Use fixed 2**18 samples like Jon Kraft's reference script
    N = int(2**18)
    fc = int(signal_freq)
    ts = 1 / float(sample_rate)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = 0.9 * (i + 1j * q)
    my_sdr.tx([iq, iq])
    
    # Buffer size
    total_time_ms = pri_ms * num_chirps
    buffer_size = 2 ** int(np.ceil(np.log2(total_time_ms / 1000 * sample_rate)))
    buffer_size = min(buffer_size, 2**22)
    my_sdr.rx_buffer_size = buffer_size
    
    print(f"Buffer size: {buffer_size}")
    print(f"PRI: {pri_ms:.3f} ms, Burst: {num_chirps} chirps")
    
    return my_sdr, my_phaser, tdd, sdr_pins


def capture_and_process(my_sdr, my_phaser, sample_rate=4e6, chirp_bw=500e6,
                        ramp_time_us=500, signal_freq=100e3, num_chirps=256):
    """Capture IQ data and produce a range-Doppler map."""
    
    c = 3e8
    ramp_time_s = ramp_time_us / 1e6
    slope = chirp_bw / ramp_time_s
    
    # Discard first few frames (transients)
    for _ in range(5):
        # Toggle gpio_burst to trigger TDD burst (required!)
        my_phaser._gpios.gpio_burst = 0
        my_phaser._gpios.gpio_burst = 1
        my_phaser._gpios.gpio_burst = 0
        my_sdr.rx()
    
    # Capture
    my_phaser._gpios.gpio_burst = 0
    my_phaser._gpios.gpio_burst = 1
    my_phaser._gpios.gpio_burst = 0
    raw = my_sdr.rx()
    
    # Use channel 0
    if isinstance(raw, list):
        data = raw[0]
    else:
        data = raw
    
    print(f"Raw IQ: len={len(data)}, dtype={data.dtype}, "
          f"mean_abs={np.mean(np.abs(data)):.1f}")
    
    # Extract chirps from the buffer
    begin_offset_time = 0.1 * ramp_time_s
    good_ramp_samples = int((ramp_time_s - begin_offset_time) * sample_rate)
    begin_offset_samples = int(begin_offset_time * sample_rate)
    
    pri_samples = int((ramp_time_us + 200) / 1e6 * sample_rate)
    
    n_chirps_actual = min(num_chirps, (len(data) - begin_offset_samples) // pri_samples)
    print(f"Extracting {n_chirps_actual} chirps, {good_ramp_samples} good samples each")
    
    # Build chirp matrix
    chirp_matrix = np.zeros((n_chirps_actual, good_ramp_samples), dtype=complex)
    for i in range(n_chirps_actual):
        start = i * pri_samples + begin_offset_samples
        end = start + good_ramp_samples
        if end <= len(data):
            chirp_matrix[i, :] = data[start:end]
    
    # Apply window
    window = np.blackman(good_ramp_samples)
    chirp_matrix = chirp_matrix * window[np.newaxis, :]
    
    # Range FFT (along fast-time axis)
    range_fft = np.fft.fftshift(np.fft.fft(chirp_matrix, axis=1), axes=1)
    
    # Doppler FFT (along slow-time axis)
    doppler_window = np.blackman(n_chirps_actual)
    range_fft = range_fft * doppler_window[:, np.newaxis]
    rd_map = np.fft.fftshift(np.fft.fft(range_fft, axis=0), axes=0)
    
    # Magnitude in dB
    rd_mag = 20 * np.log10(np.abs(rd_map) + 1e-10)
    
    # Range axis
    freq_axis = np.fft.fftshift(np.fft.fftfreq(good_ramp_samples, 1 / sample_rate))
    range_axis = (freq_axis - signal_freq) * c / (2 * slope)
    
    # Doppler axis
    doppler_axis = np.fft.fftshift(np.fft.fftfreq(n_chirps_actual, (ramp_time_us + 200) / 1e6))
    
    return rd_mag, range_axis, doppler_axis, data, chirp_matrix


def save_results(output_dir, rd_mag, range_axis, doppler_axis, raw_iq,
                 chirp_matrix, sdr_uri, phaser_uri):
    """Save range-Doppler map, raw IQ, and diagnostic plots."""
    
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw data
    np.save(os.path.join(output_dir, f"rd_map_{ts}.npy"), rd_mag)
    np.save(os.path.join(output_dir, f"raw_iq_{ts}.npy"), raw_iq)
    np.save(os.path.join(output_dir, f"chirp_matrix_{ts}.npy"), chirp_matrix)
    
    # Save metadata
    meta = {
        "timestamp": ts,
        "sdr_uri": sdr_uri,
        "phaser_uri": phaser_uri,
        "rd_shape": list(rd_mag.shape),
        "rd_min": float(rd_mag.min()),
        "rd_max": float(rd_mag.max()),
        "rd_mean": float(rd_mag.mean()),
        "raw_iq_len": len(raw_iq),
        "range_axis_m": [float(range_axis[0]), float(range_axis[-1])],
        "doppler_axis_hz": [float(doppler_axis[0]), float(doppler_axis[-1])],
    }
    with open(os.path.join(output_dir, f"meta_{ts}.json"), 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata: {json.dumps(meta, indent=2)}")
    
    # --- Plot 1: Full range-Doppler map ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"HB100 Direct Test - {sdr_uri} - {ts}", fontsize=14)
    
    # Full RD map
    ax = axes[0, 0]
    extent = [range_axis[0], range_axis[-1], doppler_axis[0], doppler_axis[-1]]
    im = ax.imshow(rd_mag, aspect='auto', origin='lower', extent=extent,
                   cmap='viridis', vmin=rd_mag.max() - 60, vmax=rd_mag.max())
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Doppler (Hz)")
    ax.set_title("Full Range-Doppler Map")
    plt.colorbar(im, ax=ax, label="dB")
    
    # Zoomed RD map (0-5m range)
    ax = axes[0, 1]
    mask = (range_axis >= 0) & (range_axis <= 5)
    if np.any(mask):
        zoomed = rd_mag[:, mask]
        extent_zoom = [0, 5, doppler_axis[0], doppler_axis[-1]]
        im = ax.imshow(zoomed, aspect='auto', origin='lower', extent=extent_zoom,
                       cmap='viridis', vmin=rd_mag.max() - 60, vmax=rd_mag.max())
        ax.set_xlabel("Range (m)")
        ax.set_ylabel("Doppler (Hz)")
        ax.set_title("Zoomed: 0-5 m range")
        plt.colorbar(im, ax=ax, label="dB")
    
    # Range profile (sum across Doppler)
    ax = axes[1, 0]
    range_profile = np.max(rd_mag, axis=0)
    ax.plot(range_axis, range_profile)
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Peak power (dB)")
    ax.set_title("Range Profile (max across Doppler)")
    ax.set_xlim(-2, 10)
    ax.axvline(x=1.0, color='r', linestyle='--', alpha=0.7, label='HB100 @ 1m')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Doppler profile at zero range and at 1m
    ax = axes[1, 1]
    zero_range_idx = np.argmin(np.abs(range_axis - 0))
    one_m_idx = np.argmin(np.abs(range_axis - 1.0))
    ax.plot(doppler_axis, rd_mag[:, zero_range_idx], label=f"Range=0m (bin {zero_range_idx})", alpha=0.7)
    ax.plot(doppler_axis, rd_mag[:, one_m_idx], label=f"Range=1m (bin {one_m_idx})", alpha=0.7)
    ax.set_xlabel("Doppler (Hz)")
    ax.set_ylabel("Power (dB)")
    ax.set_title("Doppler Profiles")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"hb100_test_{ts}.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Plot saved: {plot_path}")
    
    # --- Plot 2: Raw IQ diagnostics ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle(f"Raw IQ Diagnostics - {ts}", fontsize=14)
    
    # First 10000 samples of raw IQ
    n_show = min(10000, len(raw_iq))
    ax = axes[0]
    ax.plot(np.real(raw_iq[:n_show]), label='I', alpha=0.7)
    ax.plot(np.imag(raw_iq[:n_show]), label='Q', alpha=0.7)
    ax.set_xlabel("Sample")
    ax.set_ylabel("Amplitude")
    ax.set_title(f"Raw IQ (first {n_show} samples)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Spectrum of raw IQ
    ax = axes[1]
    spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(raw_iq[:65536]))) + 1e-10)
    freqs = np.fft.fftshift(np.fft.fftfreq(65536, 1 / 4e6))
    ax.plot(freqs / 1e3, spectrum, alpha=0.7)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Power (dB)")
    ax.set_title("Raw IQ Spectrum")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    iq_plot_path = os.path.join(output_dir, f"iq_diag_{ts}.png")
    plt.savefig(iq_plot_path, dpi=150)
    plt.close()
    print(f"IQ diagnostic plot saved: {iq_plot_path}")


def main():
    parser = argparse.ArgumentParser(description="Minimal HB100 detection test")
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1', help='PlutoSDR URI')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184', help='Phaser/CN0566 URI')
    parser.add_argument('--output-dir', default='/tmp/hb100_test', help='Output directory')
    parser.add_argument('--num-chirps', type=int, default=256, help='Number of chirps')
    args = parser.parse_args()
    
    print("=" * 60)
    print("HB100 Direct Hardware Test (NumPy, no GPU)")
    print("=" * 60)
    print(f"SDR URI:    {args.sdr_uri}")
    print(f"Phaser URI: {args.phaser_uri}")
    print(f"Chirps:     {args.num_chirps}")
    print()
    
    try:
        my_sdr, my_phaser, tdd, sdr_pins = setup_hardware(
            args.sdr_uri, args.phaser_uri, num_chirps=args.num_chirps
        )
        
        print("\nCapturing frame...")
        rd_mag, range_axis, doppler_axis, raw_iq, chirp_matrix = capture_and_process(
            my_sdr, my_phaser, num_chirps=args.num_chirps
        )
        
        print(f"\nRange-Doppler map: shape={rd_mag.shape}")
        print(f"  Dynamic range: {rd_mag.min():.1f} to {rd_mag.max():.1f} dB")
        
        # Quick check: is there a peak near 1m?
        one_m_idx = np.argmin(np.abs(range_axis - 1.0))
        peak_at_1m = np.max(rd_mag[:, max(0, one_m_idx-3):one_m_idx+4])
        noise_floor = np.median(rd_mag)
        dc_peak = np.max(rd_mag[:, np.argmin(np.abs(range_axis))])
        
        print(f"\n--- Quick Analysis ---")
        print(f"  Noise floor (median): {noise_floor:.1f} dB")
        print(f"  DC peak (0m):         {dc_peak:.1f} dB")
        print(f"  Peak near 1m:         {peak_at_1m:.1f} dB")
        print(f"  SNR at 1m:            {peak_at_1m - noise_floor:.1f} dB")
        
        if peak_at_1m - noise_floor > 10:
            print(f"  >>> HB100 LIKELY DETECTED at ~1m (SNR > 10 dB)")
        else:
            print(f"  >>> No clear target at 1m (SNR < 10 dB)")
        
        save_results(args.output_dir, rd_mag, range_axis, doppler_axis,
                     raw_iq, chirp_matrix, args.sdr_uri, args.phaser_uri)
        
        # Cleanup
        tdd.enable = False
        my_sdr.tx_destroy_buffer()
        
        print(f"\nAll results saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
