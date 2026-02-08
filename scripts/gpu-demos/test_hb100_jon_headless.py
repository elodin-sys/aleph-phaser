#!/usr/bin/env python3
"""
HB100 test using Jon Kraft's exact processing pipeline, headless (saves to file).
Uses GPU (CuPy) when available, both Rx channels summed, and MTI filter.

Based on gpu_range_doppler_jon.py with correct IPs and non-interactive output.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# GPU setup (same as Jon's script)
try:
    import cupy as cp
    _test = cp.array([1, 2, 3])
    del _test
    xp = cp
    HAS_GPU = True
    print("GPU acceleration: ENABLED (CuPy/CUDA)")
except Exception:
    xp = np
    HAS_GPU = False
    print("GPU acceleration: DISABLED (using NumPy)")

def to_gpu(data):
    if HAS_GPU and isinstance(data, np.ndarray):
        return cp.asarray(data)
    return data

def to_cpu(data):
    if hasattr(data, 'get'):
        return data.get()
    return data

import adi

def main():
    parser = argparse.ArgumentParser(description="HB100 test - Jon Kraft pipeline, headless")
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184')
    parser.add_argument('--output-dir', default='/tmp/hb100_jon_test')
    parser.add_argument('--num-frames', type=int, default=5, help='Number of frames to capture and average')
    parser.add_argument('--mti', action='store_true', default=True, help='Also run MTI filter')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---- Jon Kraft's exact parameters ----
    sample_rate = 4e6
    center_freq = 2.1e9
    signal_freq = 100e3
    rx_gain = 30
    tx_gain = 0
    output_freq = 9.9e9
    chirp_BW = 500e6
    ramp_time = 500  # us
    num_chirps = 512  # Jon uses 512
    max_range = 10
    min_scale = 0
    max_scale = 50

    sdr_ip = args.sdr_uri
    rpi_ip = args.phaser_uri

    print(f"SDR: {sdr_ip}, Phaser: {rpi_ip}")
    print(f"Chirps: {num_chirps}, Ramp: {ramp_time} us, BW: {chirp_BW/1e6:.0f} MHz")

    # ---- Hardware setup (identical to Jon's script) ----
    my_sdr = adi.ad9361(uri=sdr_ip)
    my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)

    my_phaser.configure(device_mode="rx")
    my_phaser.element_spacing = 0.014
    my_phaser.load_gain_cal()
    my_phaser.load_phase_cal()
    for i in range(0, 8):
        my_phaser.set_chan_phase(i, 0)
    gain_list = [127] * 8
    for i in range(0, len(gain_list)):
        my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

    my_phaser._gpios.gpio_tx_sw = 0
    my_phaser._gpios.gpio_vctrl_1 = 1
    my_phaser._gpios.gpio_vctrl_2 = 1

    my_sdr.sample_rate = int(sample_rate)
    my_sdr.rx_lo = int(center_freq)
    my_sdr.rx_enabled_channels = [0, 1]
    my_sdr.gain_control_mode_chan0 = 'manual'
    my_sdr.gain_control_mode_chan1 = 'manual'
    my_sdr.rx_hardwaregain_chan0 = int(rx_gain)
    my_sdr.rx_hardwaregain_chan1 = int(rx_gain)

    my_sdr.tx_lo = int(center_freq)
    my_sdr.tx_enabled_channels = [0, 1]
    my_sdr.tx_cyclic_buffer = True
    my_sdr.tx_hardwaregain_chan0 = -88
    my_sdr.tx_hardwaregain_chan1 = int(tx_gain)

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

    # TDD (identical to Jon's)
    sdr_pins = adi.one_bit_adc_dac(sdr_ip)
    sdr_pins.gpio_tdd_ext_sync = True
    tdd = adi.tddn(sdr_ip)
    sdr_pins.gpio_phaser_enable = True
    tdd.enable = False
    tdd.sync_external = True
    tdd.startup_delay_ms = 0
    PRI_ms = ramp_time/1e3 + 0.2
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

    # Ramp parameters (identical to Jon's)
    ramp_time = int(my_phaser.freq_dev_time)
    ramp_time_s = ramp_time / 1e6
    begin_offset_time = 0.1 * ramp_time_s
    good_ramp_samples = int((ramp_time_s - begin_offset_time) * sample_rate)
    start_offset_time = tdd.channel[0].on_ms/1e3 + begin_offset_time
    start_offset_samples = int(start_offset_time * sample_rate)

    # Buffer size (identical to Jon's)
    num_samples_frame = int(tdd.frame_length_ms/1000*sample_rate)
    power = 8
    fft_size = int(2**power)
    while num_samples_frame > fft_size:
        power += 1
        fft_size = int(2**power)
        if power == 18:
            break

    total_time = tdd.frame_length_ms * num_chirps
    buffer_time = 0
    power = 12
    while total_time > buffer_time:
        power += 1
        buffer_size = int(2**power)
        buffer_time = buffer_size/sample_rate*1000
        if power == 23:
            break
    my_sdr.rx_buffer_size = buffer_size
    print(f"Buffer size: {buffer_size}, buffer time: {buffer_time:.1f} ms")
    print(f"Good ramp samples: {good_ramp_samples}, start offset: {start_offset_samples}")

    # Range/velocity axes (identical to Jon's)
    c = 3e8
    wavelength = c / output_freq
    slope = BW / ramp_time_s
    PRI_s = PRI_ms / 1e3
    PRF = 1 / PRI_s
    num_bursts = tdd.burst_count
    N_frame = int(PRI_s * float(sample_rate))
    freq = np.linspace(-sample_rate / 2, sample_rate / 2, N_frame)
    dist = (freq - signal_freq) * c / (2 * slope)
    R_res = c / (2 * BW)
    v_res = wavelength / (2 * num_bursts * PRI_s)
    max_doppler_freq = PRF / 2
    max_doppler_vel = max_doppler_freq * wavelength / 2

    print(f"Range res: {R_res:.3f} m, Velocity res: {v_res:.4f} m/s")
    print(f"Max range: {dist.max():.1f} m, Max velocity: {max_doppler_vel:.2f} m/s")

    # Tx waveform (identical to Jon's)
    N = int(2**18)
    fc = int(signal_freq)
    ts_val = 1 / float(sample_rate)
    t = np.arange(0, N * ts_val, ts_val)
    i_sig = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q_sig = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = 0.9 * (i_sig + 1j * q_sig)
    my_sdr.tx([iq, iq])

    # ---- Jon's data collection function ----
    def get_radar_data():
        my_phaser._gpios.gpio_burst = 0
        my_phaser._gpios.gpio_burst = 1
        my_phaser._gpios.gpio_burst = 0
        data = my_sdr.rx()
        chan1 = data[0]
        chan2 = data[1]
        sum_data = chan1 + chan2  # coherent sum of both channels

        rx_bursts = np.zeros((num_bursts, good_ramp_samples), dtype=complex)
        for burst in range(num_bursts):
            start_index = start_offset_samples + burst * N_frame
            stop_index = start_index + good_ramp_samples
            rx_bursts[burst] = sum_data[start_index:stop_index]
        # DC leakage suppression: subtract mean chirp (kills TX-RX coupling)
        rx_bursts = rx_bursts - np.mean(rx_bursts, axis=0, keepdims=True)
        return rx_bursts, sum_data

    # ---- Jon's standard processing ----
    def freq_process(data):
        data_gpu = to_gpu(data)
        rx_bursts_fft = xp.fft.fftshift(xp.abs(xp.fft.fft2(data_gpu)))
        range_doppler_data = xp.log10(rx_bursts_fft).T
        range_doppler_data = xp.clip(range_doppler_data, min_scale, max_scale)
        return to_cpu(range_doppler_data)

    # ---- Jon's MTI filter (vectorized) ----
    def mti_filter_process(rx_bursts):
        rx_chirps = to_gpu(rx_bursts)
        corr = xp.sum(rx_chirps[:-1] * xp.conj(rx_chirps[1:]), axis=1)
        angles = xp.angle(corr)
        phase_correction = xp.exp(-1j * angles[:, None])
        result = xp.zeros_like(rx_chirps)
        result[:-1] = rx_chirps[1:] - rx_chirps[:-1] * phase_correction
        if HAS_GPU:
            cp.cuda.Stream.null.synchronize()
        return to_cpu(result)

    # ---- Discard transients ----
    print("Discarding 10 transient frames...")
    for _ in range(10):
        my_phaser._gpios.gpio_burst = 0
        my_phaser._gpios.gpio_burst = 1
        my_phaser._gpios.gpio_burst = 0
        my_sdr.rx()

    # ---- Capture frames ----
    print(f"Capturing {args.num_frames} frames...")
    all_bursts = []
    all_raw = []
    all_std = []
    all_mti = []

    for frame_idx in range(args.num_frames):
        t0 = time.perf_counter()
        rx_bursts, raw_iq = get_radar_data()
        rd_std = freq_process(rx_bursts)
        rd_mti = freq_process(mti_filter_process(rx_bursts)) if args.mti else None
        elapsed = time.perf_counter() - t0
        print(f"  Frame {frame_idx}: {elapsed*1000:.1f} ms, std range [{rd_std.min():.1f}, {rd_std.max():.1f}]")
        all_bursts.append(rx_bursts)
        all_raw.append(raw_iq)
        all_std.append(rd_std)
        if rd_mti is not None:
            all_mti.append(rd_mti)

    # Average the standard RD maps
    avg_std = np.mean(all_std, axis=0)
    avg_mti = np.mean(all_mti, axis=0) if all_mti else None

    # Save raw data
    np.save(os.path.join(args.output_dir, f"chirps_{ts}.npy"), all_bursts[0])
    np.save(os.path.join(args.output_dir, f"raw_iq_{ts}.npy"), all_raw[0])
    np.save(os.path.join(args.output_dir, f"rd_std_{ts}.npy"), avg_std)
    if avg_mti is not None:
        np.save(os.path.join(args.output_dir, f"rd_mti_{ts}.npy"), avg_mti)

    # ---- Plots ----
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"Jon Kraft Pipeline - HB100 @ 48in (1.22m) - {ts}\n"
                 f"GPU={'ON' if HAS_GPU else 'OFF'}, {num_chirps} chirps, {args.num_frames} frames avg",
                 fontsize=14)

    extent = [-max_doppler_vel, max_doppler_vel, dist.min(), dist.max()]
    extent_zoom = [-max_doppler_vel, max_doppler_vel, 0, max_range]

    # Standard RD map (full)
    ax = axes[0, 0]
    im = ax.imshow(avg_std, aspect='auto', extent=extent, origin='lower', cmap='inferno')
    ax.set_title('Standard (Jon log10 scale)')
    ax.set_xlabel('Velocity (m/s)')
    ax.set_ylabel('Range (m)')
    ax.set_xlim([-5, 5])
    ax.set_ylim([0, max_range])
    ax.axhline(y=1.22, color='cyan', linestyle='--', alpha=0.7, label='HB100 @ 1.22m')
    ax.legend(fontsize=8)
    plt.colorbar(im, ax=ax)

    # Standard - range profile
    ax = axes[0, 1]
    # Jon's dist axis is for N_frame points; the RD map has good_ramp_samples columns
    # The RD map is transposed (freq_process returns .T), so rows=range, cols=doppler
    range_profile_std = np.max(avg_std, axis=1)  # max across doppler (columns)
    # Reconstruct range axis for good_ramp_samples
    freq_ramp = np.linspace(-sample_rate/2, sample_rate/2, good_ramp_samples)
    dist_ramp = (freq_ramp - signal_freq) * c / (2 * slope)
    ax.plot(dist_ramp, range_profile_std)
    ax.set_xlim([0, max_range])
    ax.axvline(x=1.22, color='r', linestyle='--', alpha=0.7, label='HB100 @ 1.22m')
    ax.set_xlabel('Range (m)')
    ax.set_ylabel('Peak Power (log10)')
    ax.set_title('Standard Range Profile')
    ax.legend()
    ax.grid(True, alpha=0.3)

    if avg_mti is not None:
        # MTI RD map
        ax = axes[1, 0]
        im = ax.imshow(avg_mti, aspect='auto', extent=extent, origin='lower', cmap='inferno')
        ax.set_title('MTI Filtered (Jon pipeline)')
        ax.set_xlabel('Velocity (m/s)')
        ax.set_ylabel('Range (m)')
        ax.set_xlim([-5, 5])
        ax.set_ylim([0, max_range])
        ax.axhline(y=1.22, color='cyan', linestyle='--', alpha=0.7, label='HB100 @ 1.22m')
        ax.legend(fontsize=8)
        plt.colorbar(im, ax=ax)

        # MTI range profile
        ax = axes[1, 1]
        range_profile_mti = np.max(avg_mti, axis=1)
        ax.plot(dist_ramp, range_profile_mti)
        ax.set_xlim([0, max_range])
        ax.axvline(x=1.22, color='r', linestyle='--', alpha=0.7, label='HB100 @ 1.22m')
        ax.set_xlabel('Range (m)')
        ax.set_ylabel('Peak Power (log10)')
        ax.set_title('MTI Range Profile')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(args.output_dir, f"jon_pipeline_{ts}.png")
    plt.savefig(plot_path, dpi=150)
    print(f"Saved: {plot_path}")

    # ---- Quick analysis ----
    print("\n=== QUICK ANALYSIS ===")
    # Find 1.22m in the range axis
    one_m_idx = np.argmin(np.abs(dist_ramp - 1.22))
    print(f"1.22m -> range bin {one_m_idx} (actual: {dist_ramp[one_m_idx]:.2f}m)")

    # Standard
    peak_region = range_profile_std[max(0, one_m_idx-5):one_m_idx+6]
    noise_region = range_profile_std[one_m_idx+20:one_m_idx+50]
    print(f"Standard: peak near 1.22m = {peak_region.max():.2f}, noise floor = {np.median(noise_region):.2f}")

    if avg_mti is not None:
        peak_region_mti = range_profile_mti[max(0, one_m_idx-5):one_m_idx+6]
        noise_region_mti = range_profile_mti[one_m_idx+20:one_m_idx+50]
        print(f"MTI: peak near 1.22m = {peak_region_mti.max():.2f}, noise floor = {np.median(noise_region_mti):.2f}")

    # Save meta
    meta = {
        "timestamp": ts,
        "sdr_uri": args.sdr_uri,
        "phaser_uri": args.phaser_uri,
        "num_chirps": num_chirps,
        "num_frames_averaged": args.num_frames,
        "gpu": HAS_GPU,
        "target_distance_m": 1.22,
        "target_distance_in": 48,
        "range_res_m": R_res,
        "max_range_m": float(dist.max()),
        "max_velocity_ms": max_doppler_vel,
    }
    with open(os.path.join(args.output_dir, f"meta_{ts}.json"), 'w') as f:
        json.dump(meta, f, indent=2)

    # Cleanup
    tdd.enable = False
    my_sdr.tx_destroy_buffer()
    print("\nDone. Pluto buffer cleared.")


if __name__ == '__main__':
    main()
