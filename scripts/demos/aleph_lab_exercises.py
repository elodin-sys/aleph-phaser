#!/usr/bin/env python3
"""
Aleph Phaser Lab Exercises

Implements Lab 3 (Array Factor/Beamwidth) and Lab 4 (Sidelobes/Tapering)
from the CN0566 Phaser workshop.

Lab 3: Array Factor and Beamwidth
- Observe array factor vs steering angle
- Measure half-power beamwidth (HPBW)
- Compare measured vs theoretical patterns

Lab 4: Sidelobes and Tapering
- Uniform weighting (no taper)
- Blackman window tapering
- Compare sidelobe levels

Usage:
    python3 aleph_lab_exercises.py [--lab 3|4|both] [--output-dir /path/to/output]
"""

import argparse
import os
from time import sleep
import numpy as np
from numpy.fft import fft, fftshift

from adi import ad9361
from adi.cn0566 import CN0566


def measure_power(sdr, num_averages=3):
    """Measure peak signal power with averaging."""
    powers = []
    for _ in range(num_averages):
        data = sdr.rx()
        combined = data[0] + data[1]
        window = np.blackman(len(combined))
        spectrum = np.abs(fftshift(fft(combined * window)))
        peak_power = 20 * np.log10(np.max(spectrum) + 1e-10)
        powers.append(peak_power)
    return np.mean(powers)


def calculate_phase_delta(angle_deg, freq_hz, element_spacing_m=0.014):
    """Calculate phase delta for steering angle."""
    c = 3e8
    wavelength = c / freq_hz
    return 360 * element_spacing_m * np.sin(np.radians(angle_deg)) / wavelength


def theoretical_array_factor(angles, num_elements=8, element_spacing=0.014, 
                              freq=10.525e9, steer_angle=0, taper=None):
    """
    Calculate theoretical array factor.
    
    Args:
        angles: Array of angles in degrees
        num_elements: Number of array elements
        element_spacing: Element spacing in meters
        freq: Signal frequency in Hz
        steer_angle: Steering angle in degrees
        taper: Optional amplitude taper (array of weights)
    """
    c = 3e8
    wavelength = c / freq
    k = 2 * np.pi / wavelength
    d = element_spacing
    
    if taper is None:
        taper = np.ones(num_elements)
    
    af = np.zeros(len(angles), dtype=complex)
    
    for idx, theta in enumerate(angles):
        phase_prog = k * d * (np.sin(np.radians(theta)) - np.sin(np.radians(steer_angle)))
        for n in range(num_elements):
            af[idx] += taper[n] * np.exp(1j * n * phase_prog)
    
    # Normalize to max
    af_mag = np.abs(af)
    af_db = 20 * np.log10(af_mag / np.max(af_mag) + 1e-10)
    
    return af_db


def setup_hardware(sdr_uri, phaser_uri, signal_freq):
    """Initialize and configure hardware."""
    print("Connecting to hardware...")
    phaser = CN0566(uri=phaser_uri)
    sdr = ad9361(uri=sdr_uri)
    phaser.sdr = sdr
    sleep(0.5)
    
    print("Configuring Phaser...")
    phaser.configure(device_mode="rx")
    phaser.SignalFreq = signal_freq
    
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
    
    offset = 1_000_000
    phaser.frequency = int(signal_freq + sdr.rx_lo - offset) // 4
    
    # Warm up
    for _ in range(5):
        sdr.rx()
    
    return sdr, phaser


def run_lab3(sdr, phaser, signal_freq, output_dir):
    """
    Lab 3: Array Factor and Beamwidth
    
    Measures the array pattern at different steering angles and compares
    with theoretical predictions.
    """
    print()
    print("=" * 60)
    print("Lab 3: Array Factor and Beamwidth")
    print("=" * 60)
    
    angles = np.arange(-60, 61, 2)
    steer_angles = [0, 20, 40]  # Different steering angles to test
    
    results = {}
    
    for steer in steer_angles:
        print(f"\nSteering beam to {steer}°...")
        powers = []
        
        for angle in angles:
            phase_delta = calculate_phase_delta(steer, signal_freq)
            for i in range(8):
                phaser.set_chan_phase(i, i * phase_delta, apply_cal=True)
            
            # For each measurement angle, we adjust steering
            meas_phase_delta = calculate_phase_delta(angle, signal_freq)
            for i in range(8):
                phaser.set_chan_phase(i, i * meas_phase_delta, apply_cal=True)
            
            sleep(0.01)
            power = measure_power(sdr, num_averages=2)
            powers.append(power)
            
            print(f"\r  Measuring at {angle:+3d}°... ", end="", flush=True)
        
        # Normalize to peak
        powers = np.array(powers)
        powers_norm = powers - np.max(powers)
        results[steer] = powers_norm
        
        # Calculate HPBW
        half_power = -3
        above_half = powers_norm >= half_power
        if np.sum(above_half) > 1:
            above_indices = np.where(above_half)[0]
            hpbw = angles[above_indices[-1]] - angles[above_indices[0]]
        else:
            hpbw = 0
        
        print(f"\n  HPBW at {steer}° steering: {hpbw}°")
        
        # Theoretical HPBW for 8-element array at boresight is ~13°
        # It increases with steering angle
    
    # Generate plot
    print("\nGenerating Lab 3 plot...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Measured patterns
    ax1 = axes[0]
    for steer in steer_angles:
        ax1.plot(angles, results[steer], label=f'Steer {steer}°', linewidth=2)
    ax1.axhline(y=-3, color='gray', linestyle='--', alpha=0.5, label='-3dB')
    ax1.set_xlabel('Angle [degrees]')
    ax1.set_ylabel('Normalized Power [dB]')
    ax1.set_title('Measured Array Patterns')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([-60, 60])
    ax1.set_ylim([-30, 5])
    
    # Theoretical patterns
    ax2 = axes[1]
    for steer in steer_angles:
        theoretical = theoretical_array_factor(angles, steer_angle=steer, freq=signal_freq)
        ax2.plot(angles, theoretical, label=f'Steer {steer}°', linewidth=2)
    ax2.axhline(y=-3, color='gray', linestyle='--', alpha=0.5, label='-3dB')
    ax2.set_xlabel('Angle [degrees]')
    ax2.set_ylabel('Normalized Power [dB]')
    ax2.set_title('Theoretical Array Patterns (8 elements)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([-60, 60])
    ax2.set_ylim([-30, 5])
    
    plt.suptitle('Lab 3: Array Factor and Beamwidth', fontsize=14)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, "lab3_array_factor.png")
    plt.savefig(output_path, dpi=150)
    print(f"  Plot saved to: {output_path}")
    plt.close()
    
    return results


def run_lab4(sdr, phaser, signal_freq, output_dir):
    """
    Lab 4: Sidelobes and Tapering
    
    Compares uniform weighting vs Blackman window tapering
    to demonstrate sidelobe reduction.
    """
    print()
    print("=" * 60)
    print("Lab 4: Sidelobes and Tapering")
    print("=" * 60)
    
    angles = np.arange(-60, 61, 2)
    
    # Define tapers
    uniform_taper = np.ones(8) * 64  # Half scale, uniform
    blackman_taper = np.blackman(8)
    blackman_taper = (blackman_taper / np.max(blackman_taper) * 127).astype(int)  # Scale to 0-127
    
    tapers = {
        'Uniform': uniform_taper,
        'Blackman': blackman_taper
    }
    
    results = {}
    
    for taper_name, gains in tapers.items():
        print(f"\nApplying {taper_name} taper: {gains}")
        powers = []
        
        # Apply taper gains
        for i in range(8):
            phaser.set_chan_gain(i, int(gains[i]), apply_cal=False)
        
        for angle in angles:
            phase_delta = calculate_phase_delta(angle, signal_freq)
            for i in range(8):
                phaser.set_chan_phase(i, i * phase_delta, apply_cal=True)
            
            sleep(0.01)
            power = measure_power(sdr, num_averages=2)
            powers.append(power)
            
            print(f"\r  Measuring at {angle:+3d}°... ", end="", flush=True)
        
        # Normalize
        powers = np.array(powers)
        powers_norm = powers - np.max(powers)
        results[taper_name] = powers_norm
        
        # Find first sidelobe level
        main_lobe_idx = np.argmax(powers_norm)
        # Look for sidelobes (local maxima away from main lobe)
        sidelobe_mask = np.abs(np.arange(len(powers_norm)) - main_lobe_idx) > 5
        if np.any(sidelobe_mask):
            sidelobe_level = np.max(powers_norm[sidelobe_mask])
        else:
            sidelobe_level = -30
        
        print(f"\n  First sidelobe level: {sidelobe_level:.1f} dB")
    
    # Reset to uniform
    for i in range(8):
        phaser.set_chan_gain(i, 64, apply_cal=False)
    
    # Generate plot
    print("\nGenerating Lab 4 plot...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Measured patterns
    ax1 = axes[0]
    for taper_name in ['Uniform', 'Blackman']:
        ax1.plot(angles, results[taper_name], label=taper_name, linewidth=2)
    ax1.axhline(y=-13.2, color='gray', linestyle='--', alpha=0.5, label='Uniform theory (-13.2dB)')
    ax1.set_xlabel('Angle [degrees]')
    ax1.set_ylabel('Normalized Power [dB]')
    ax1.set_title('Measured Patterns with Tapering')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([-60, 60])
    ax1.set_ylim([-40, 5])
    
    # Theoretical patterns
    ax2 = axes[1]
    theoretical_uniform = theoretical_array_factor(angles, freq=signal_freq)
    theoretical_blackman = theoretical_array_factor(angles, freq=signal_freq, 
                                                     taper=np.blackman(8))
    ax2.plot(angles, theoretical_uniform, label='Uniform', linewidth=2)
    ax2.plot(angles, theoretical_blackman, label='Blackman', linewidth=2)
    ax2.axhline(y=-13.2, color='gray', linestyle='--', alpha=0.5, label='Uniform sidelobe (-13.2dB)')
    ax2.set_xlabel('Angle [degrees]')
    ax2.set_ylabel('Normalized Power [dB]')
    ax2.set_title('Theoretical Patterns')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([-60, 60])
    ax2.set_ylim([-80, 5])
    
    plt.suptitle('Lab 4: Sidelobes and Tapering', fontsize=14)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, "lab4_tapering.png")
    plt.savefig(output_path, dpi=150)
    print(f"  Plot saved to: {output_path}")
    plt.close()
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Aleph Phaser Lab Exercises')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184')
    parser.add_argument('--signal-freq', type=float, default=10.525e9)
    parser.add_argument('--lab', choices=['3', '4', 'both'], default='both',
                        help='Which lab to run')
    parser.add_argument('--output-dir', default='/tmp')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup hardware
    sdr, phaser = setup_hardware(args.sdr_uri, args.phaser_uri, args.signal_freq)
    
    try:
        if args.lab in ['3', 'both']:
            run_lab3(sdr, phaser, args.signal_freq, args.output_dir)
        
        if args.lab in ['4', 'both']:
            run_lab4(sdr, phaser, args.signal_freq, args.output_dir)
        
        print()
        print("=" * 60)
        print("Lab exercises complete!")
        print("=" * 60)
        
    finally:
        # Reset to defaults
        phaser.set_beam_phase_diff(0.0)
        for i in range(8):
            phaser.set_chan_gain(i, 64, apply_cal=False)
        del sdr
        del phaser


if __name__ == '__main__':
    main()
