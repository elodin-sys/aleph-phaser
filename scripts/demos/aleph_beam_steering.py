#!/usr/bin/env python3
"""
Aleph Beam Steering Demo

Demonstrates phased array beam steering on the Aleph with CN0566 Phaser.
Sweeps the beam angle from -60° to +60° and measures signal power at each angle.
Generates beam pattern plot saved to file.

Usage:
    python3 aleph_beam_steering.py [--output-dir /path/to/output]
    
To see the beam pattern:
1. Power on HB100 and aim at array
2. Run this script
3. Slowly move HB100 around to see beam tracking
"""

import argparse
import os
from time import sleep
import numpy as np
from numpy.fft import fft, fftshift

# ADI libraries
from adi import ad9361
from adi.cn0566 import CN0566


def measure_power(sdr, num_averages=5):
    """Measure signal power with averaging."""
    powers = []
    for _ in range(num_averages):
        data = sdr.rx()
        combined = data[0] + data[1]
        
        # Apply window and compute FFT
        window = np.blackman(len(combined))
        windowed = combined * window
        spectrum = np.abs(fftshift(fft(windowed)))
        
        # Find peak power
        peak_power = 20 * np.log10(np.max(spectrum) + 1e-10)
        powers.append(peak_power)
    
    return np.mean(powers)


def calculate_phase_delta(angle_deg, freq_hz, element_spacing_m=0.014):
    """
    Calculate phase delta between elements for desired steering angle.
    
    Args:
        angle_deg: Desired steering angle in degrees (0 = boresight)
        freq_hz: Signal frequency in Hz
        element_spacing_m: Element spacing in meters (default 14mm for CN0566)
    
    Returns:
        Phase delta in degrees
    """
    c = 3e8  # Speed of light
    wavelength = c / freq_hz
    phase_delta = 360 * element_spacing_m * np.sin(np.radians(angle_deg)) / wavelength
    return phase_delta


def main():
    parser = argparse.ArgumentParser(description='Aleph Beam Steering Demo')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1',
                        help='PlutoSDR URI')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184',
                        help='Phaser/Pi URI')
    parser.add_argument('--signal-freq', type=float, default=10.525e9,
                        help='HB100 signal frequency in Hz')
    parser.add_argument('--angle-start', type=float, default=-60,
                        help='Start angle in degrees')
    parser.add_argument('--angle-end', type=float, default=60,
                        help='End angle in degrees')
    parser.add_argument('--angle-step', type=float, default=5,
                        help='Angle step in degrees')
    parser.add_argument('--output-dir', default='/tmp',
                        help='Output directory for plots')
    args = parser.parse_args()

    print("=" * 60)
    print("Aleph Beam Steering Demo")
    print("=" * 60)
    print()

    os.makedirs(args.output_dir, exist_ok=True)

    # Connect to hardware
    print("Connecting to hardware...")
    phaser = CN0566(uri=args.phaser_uri)
    print(f"  ✓ Phaser connected at {args.phaser_uri}")
    
    sdr = ad9361(uri=args.sdr_uri)
    print(f"  ✓ PlutoSDR connected at {args.sdr_uri}")
    
    phaser.sdr = sdr
    sleep(0.5)

    # Configure Phaser
    print("Configuring Phaser...")
    phaser.configure(device_mode="rx")
    phaser.SignalFreq = args.signal_freq
    
    # Set gains
    for i in range(8):
        phaser.set_chan_gain(i, 64, apply_cal=False)

    # Configure SDR
    print("Configuring SDR...")
    sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
    sdr._ctrl.debug_attrs["adi,ensm-enable-txnrx-control-enable"].value = "0"
    sdr._ctrl.debug_attrs["initialize"].value = "1"

    sdr.rx_enabled_channels = [0, 1]
    sdr._rxadc.set_kernel_buffers_count(1)
    
    sdr.sample_rate = int(30e6)
    sdr.rx_buffer_size = int(1024)
    sdr.rx_rf_bandwidth = int(10e6)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.gain_control_mode_chan1 = "manual"
    sdr.rx_hardwaregain_chan0 = 0
    sdr.rx_hardwaregain_chan1 = 0
    sdr.rx_lo = int(2.2e9)
    
    sdr.tx_hardwaregain_chan0 = int(-80)
    sdr.tx_hardwaregain_chan1 = int(-80)

    # Set Phaser PLL
    offset = 1_000_000
    phaser.frequency = int(phaser.SignalFreq + sdr.rx_lo - offset) // 4
    print(f"  Phaser PLL: {phaser.frequency*4/1e9:.3f} GHz")

    # Warm up
    print()
    print("Warming up (flushing buffers)...")
    for _ in range(5):
        sdr.rx()
    sleep(0.5)

    # Beam sweep
    angles = np.arange(args.angle_start, args.angle_end + 0.1, args.angle_step)
    powers = []
    
    print()
    print(f"Sweeping beam from {args.angle_start}° to {args.angle_end}°...")
    print("-" * 50)
    
    for angle in angles:
        # Calculate and apply phase delta
        phase_delta = calculate_phase_delta(angle, args.signal_freq)
        
        # Apply phases to each element
        for i in range(8):
            phaser.set_chan_phase(i, i * phase_delta, apply_cal=True)
        
        sleep(0.02)  # Let phases settle
        
        # Measure power
        power = measure_power(sdr, num_averages=3)
        powers.append(power)
        
        # Progress indicator
        bar_len = int((angle - args.angle_start) / (args.angle_end - args.angle_start) * 30)
        print(f"\r  Angle: {angle:+6.1f}° | Power: {power:6.1f} dB | [{'='*bar_len}{' '*(30-bar_len)}]", end="", flush=True)
    
    print()
    print("-" * 50)
    
    # Find peak
    peak_idx = np.argmax(powers)
    peak_angle = angles[peak_idx]
    peak_power = powers[peak_idx]
    
    print(f"  Peak at: {peak_angle:+.1f}° with {peak_power:.1f} dB")
    
    # Calculate half-power beamwidth
    powers_array = np.array(powers)
    half_power = peak_power - 3
    above_half = powers_array >= half_power
    if np.sum(above_half) > 1:
        above_indices = np.where(above_half)[0]
        hpbw = angles[above_indices[-1]] - angles[above_indices[0]]
        print(f"  Half-power beamwidth: ~{hpbw:.1f}°")

    # Generate plots
    print()
    print("Generating plots...")
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Cartesian plot
    ax1.plot(angles, powers, 'b-', linewidth=2, marker='o', markersize=4)
    ax1.axvline(x=peak_angle, color='r', linestyle='--', alpha=0.5, label=f'Peak: {peak_angle:+.1f}°')
    ax1.axhline(y=half_power, color='g', linestyle=':', alpha=0.5, label='-3dB level')
    ax1.set_xlabel("Steering Angle [degrees]")
    ax1.set_ylabel("Signal Power [dB]")
    ax1.set_title("Beam Pattern (Cartesian)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([args.angle_start, args.angle_end])

    # Polar plot
    # Normalize powers to 0-1 range for polar plot
    powers_norm = powers_array - np.min(powers_array)
    powers_norm = powers_norm / np.max(powers_norm) if np.max(powers_norm) > 0 else powers_norm
    
    theta = np.radians(angles)
    ax2 = plt.subplot(122, projection='polar')
    ax2.plot(theta, powers_norm, 'b-', linewidth=2)
    ax2.set_theta_zero_location('N')  # 0 degrees at top
    ax2.set_theta_direction(-1)  # Clockwise
    ax2.set_thetamin(-90)
    ax2.set_thetamax(90)
    ax2.set_title("Beam Pattern (Polar)")
    ax2.grid(True, alpha=0.3)

    plt.suptitle(f"CN0566 Phaser Beam Pattern @ {args.signal_freq/1e9:.3f} GHz", fontsize=14)
    plt.tight_layout()

    # Save plot
    output_path = os.path.join(args.output_dir, "aleph_beam_pattern.png")
    plt.savefig(output_path, dpi=150)
    print(f"  Plot saved to: {output_path}")

    # Save data
    data_path = os.path.join(args.output_dir, "aleph_beam_pattern_data.npz")
    np.savez(data_path,
             angles=angles,
             powers=powers,
             peak_angle=peak_angle,
             peak_power=peak_power,
             signal_freq=args.signal_freq)
    print(f"  Data saved to: {data_path}")

    # Reset to boresight
    print()
    print("Resetting beam to boresight...")
    phaser.set_beam_phase_diff(0.0)

    # Clean up
    del sdr
    del phaser

    print()
    print("=" * 60)
    print("Beam steering demo complete!")
    print(f"Peak detected at {peak_angle:+.1f}° with {peak_power:.1f} dB")
    print("=" * 60)


if __name__ == '__main__':
    main()
