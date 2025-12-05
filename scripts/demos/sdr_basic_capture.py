#!/usr/bin/env python3
"""
Basic SDR Capture Demo for Aleph-Phaser Integration

This script demonstrates basic PlutoSDR data capture on the Aleph.
It works without the Phaser/Raspberry Pi - just requires PlutoSDR 
connected directly to Aleph USB.

Usage:
    python3 sdr_basic_capture.py [--uri ip:192.168.2.1]
"""

import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='Basic SDR Capture Demo')
    parser.add_argument('--uri', default='ip:192.168.2.1', 
                        help='PlutoSDR URI (default: ip:192.168.2.1)')
    parser.add_argument('--samples', type=int, default=1024,
                        help='Number of samples to capture (default: 1024)')
    parser.add_argument('--rx-lo', type=float, default=2.4e9,
                        help='RX LO frequency in Hz (default: 2.4e9)')
    parser.add_argument('--sample-rate', type=float, default=30e6,
                        help='Sample rate in Hz (default: 30e6)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for captured data (optional)')
    args = parser.parse_args()

    print("=== Aleph PlutoSDR Basic Capture Demo ===")
    print()
    
    # Import here to fail fast if not available
    import adi
    
    print(f"Connecting to PlutoSDR at {args.uri}...")
    sdr = adi.ad9361(uri=args.uri)
    
    # Configure SDR
    sdr.sample_rate = int(args.sample_rate)
    sdr.rx_lo = int(args.rx_lo)
    sdr.rx_buffer_size = args.samples
    sdr.rx_rf_bandwidth = int(20e6)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.gain_control_mode_chan1 = "manual"
    sdr.rx_hardwaregain_chan0 = 30
    sdr.rx_hardwaregain_chan1 = 30
    
    print(f"Configuration:")
    print(f"  Sample Rate: {sdr.sample_rate / 1e6:.2f} MSPS")
    print(f"  RX LO: {sdr.rx_lo / 1e9:.3f} GHz")
    print(f"  RX RF Bandwidth: {sdr.rx_rf_bandwidth / 1e6:.1f} MHz")
    print(f"  Buffer Size: {sdr.rx_buffer_size} samples")
    print()
    
    # Capture data
    print("Capturing data...")
    data = sdr.rx()
    
    # Analyze
    print(f"Captured {len(data)} channels")
    for i, ch in enumerate(data):
        print(f"  Channel {i}:")
        print(f"    Samples: {len(ch)}")
        print(f"    Dtype: {ch.dtype}")
        print(f"    Mean amplitude: {np.mean(np.abs(ch)):.2f}")
        print(f"    Max amplitude: {np.max(np.abs(ch)):.2f}")
    
    # Combined channels (for beamforming, sum both)
    combined = data[0] + data[1]
    
    # Compute FFT
    fft_data = np.fft.fftshift(np.fft.fft(combined))
    fft_mag = 20 * np.log10(np.abs(fft_data) + 1e-10)
    freqs = np.fft.fftshift(np.fft.fftfreq(len(combined), 1/sdr.sample_rate))
    
    peak_idx = np.argmax(fft_mag)
    peak_freq = freqs[peak_idx]
    peak_power = fft_mag[peak_idx]
    
    print()
    print(f"FFT Analysis:")
    print(f"  Peak frequency offset: {peak_freq/1e3:.1f} kHz")
    print(f"  Peak power: {peak_power:.1f} dB")
    
    # Save if requested
    if args.output:
        np.savez(args.output, 
                 data_ch0=data[0], 
                 data_ch1=data[1],
                 sample_rate=sdr.sample_rate,
                 rx_lo=sdr.rx_lo)
        print(f"Data saved to {args.output}")
    
    print()
    print("SUCCESS: Basic SDR capture working on Aleph!")

if __name__ == '__main__':
    main()
