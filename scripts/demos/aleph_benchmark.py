#!/usr/bin/env python3
"""
Aleph Phaser Performance Benchmarks

Measures key performance metrics for the Aleph-Phaser integration:
- FFT computation time
- Data capture throughput
- Beam sweep timing
- CPU and memory usage

Usage:
    python3 aleph_benchmark.py [--output-dir /path/to/output]
"""

import argparse
import os
import time
import numpy as np
from numpy.fft import fft, fftshift

from adi import ad9361
from adi.cn0566 import CN0566


def benchmark_fft(sizes=[256, 512, 1024, 2048, 4096, 8192], iterations=1000):
    """Benchmark FFT computation time for various sizes."""
    print("FFT Benchmark")
    print("-" * 50)
    
    results = {}
    for size in sizes:
        data = np.random.randn(size) + 1j * np.random.randn(size)
        
        # Warm up
        for _ in range(10):
            _ = fft(data)
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            _ = fft(data)
        elapsed = time.perf_counter() - start
        
        avg_time = elapsed / iterations * 1000  # ms
        results[size] = avg_time
        print(f"  {size:5d} samples: {avg_time:.4f} ms ({iterations} iterations)")
    
    return results


def benchmark_capture(sdr, buffer_sizes=[256, 512, 1024, 2048, 4096, 8192], 
                      iterations=50):
    """Benchmark data capture from PlutoSDR."""
    print()
    print("Data Capture Benchmark")
    print("-" * 50)
    
    results = {}
    for size in buffer_sizes:
        sdr.rx_buffer_size = size
        
        # Warm up
        for _ in range(5):
            _ = sdr.rx()
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            _ = sdr.rx()
        elapsed = time.perf_counter() - start
        
        avg_time = elapsed / iterations * 1000  # ms
        throughput = size * iterations / elapsed  # samples/sec
        results[size] = {'time_ms': avg_time, 'throughput_sps': throughput}
        
        print(f"  {size:5d} samples: {avg_time:.2f} ms ({throughput/1e6:.2f} MSPS effective)")
    
    return results


def benchmark_beam_sweep(sdr, phaser, signal_freq, angles_count=25, iterations=10):
    """Benchmark beam sweep operation."""
    print()
    print("Beam Sweep Benchmark")
    print("-" * 50)
    
    angles = np.linspace(-60, 60, angles_count)
    c = 3e8
    wavelength = c / signal_freq
    d = 0.014
    
    sdr.rx_buffer_size = 1024
    
    # Warm up
    for angle in angles:
        phase_delta = 360 * d * np.sin(np.radians(angle)) / wavelength
        for i in range(8):
            phaser.set_chan_phase(i, i * phase_delta, apply_cal=False)
        _ = sdr.rx()
    
    # Benchmark
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for angle in angles:
            phase_delta = 360 * d * np.sin(np.radians(angle)) / wavelength
            for i in range(8):
                phaser.set_chan_phase(i, i * phase_delta, apply_cal=False)
            _ = sdr.rx()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)
    
    print(f"  {angles_count} angles sweep:")
    print(f"    Average: {avg_time*1000:.1f} ms")
    print(f"    Min:     {min_time*1000:.1f} ms")
    print(f"    Max:     {max_time*1000:.1f} ms")
    print(f"    Per angle: {avg_time/angles_count*1000:.2f} ms")
    
    return {
        'angles_count': angles_count,
        'avg_time_s': avg_time,
        'min_time_s': min_time,
        'max_time_s': max_time
    }


def get_system_info():
    """Get system information."""
    print()
    print("System Information")
    print("-" * 50)
    
    import platform
    import subprocess
    
    info = {
        'platform': platform.platform(),
        'processor': platform.processor(),
        'python': platform.python_version()
    }
    
    # Try to get more detailed CPU info
    try:
        result = subprocess.run(['cat', '/proc/cpuinfo'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'model name' in line:
                info['cpu_model'] = line.split(':')[1].strip()
                break
            if 'Model' in line:
                info['cpu_model'] = line.split(':')[1].strip()
                break
    except:
        pass
    
    # Memory info
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Mem:' in line:
                parts = line.split()
                info['memory_total'] = parts[1]
                info['memory_available'] = parts[6] if len(parts) > 6 else parts[3]
                break
    except:
        pass
    
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    return info


def main():
    parser = argparse.ArgumentParser(description='Aleph Performance Benchmarks')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184')
    parser.add_argument('--signal-freq', type=float, default=10.525e9)
    parser.add_argument('--output-dir', default='/tmp')
    args = parser.parse_args()

    print("=" * 60)
    print("Aleph Phaser Performance Benchmarks")
    print("=" * 60)
    print()

    os.makedirs(args.output_dir, exist_ok=True)
    
    # System info
    sys_info = get_system_info()
    
    # Connect to hardware
    print()
    print("Connecting to hardware...")
    phaser = CN0566(uri=args.phaser_uri)
    sdr = ad9361(uri=args.sdr_uri)
    phaser.sdr = sdr
    
    phaser.configure(device_mode="rx")
    phaser.SignalFreq = args.signal_freq
    
    for i in range(8):
        phaser.set_chan_gain(i, 64, apply_cal=False)
    
    sdr.sample_rate = int(30e6)
    sdr.rx_buffer_size = 1024
    sdr.rx_rf_bandwidth = int(10e6)
    sdr.rx_lo = int(2.2e9)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.gain_control_mode_chan1 = "manual"
    sdr.rx_hardwaregain_chan0 = 0
    sdr.rx_hardwaregain_chan1 = 0
    sdr.tx_hardwaregain_chan0 = int(-80)
    sdr.tx_hardwaregain_chan1 = int(-80)
    
    offset = 1_000_000
    phaser.frequency = int(args.signal_freq + sdr.rx_lo - offset) // 4
    print("  Connected!")
    
    # Run benchmarks
    print()
    fft_results = benchmark_fft()
    capture_results = benchmark_capture(sdr)
    sweep_results = benchmark_beam_sweep(sdr, phaser, args.signal_freq)
    
    # Summary
    print()
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print()
    print("FFT Performance (1024 samples):")
    print(f"  Time: {fft_results[1024]:.4f} ms")
    print(f"  Target: <1 ms  {'✓ PASS' if fft_results[1024] < 1 else '✗ FAIL'}")
    print()
    print("Data Capture (1024 samples):")
    print(f"  Time: {capture_results[1024]['time_ms']:.2f} ms")
    print(f"  Throughput: {capture_results[1024]['throughput_sps']/1e6:.2f} MSPS")
    print(f"  Target: >30 MSPS  {'✓ PASS' if capture_results[1024]['throughput_sps'] > 30e6 else '(Limited by USB/network)'}")
    print()
    print(f"Beam Sweep ({sweep_results['angles_count']} angles):")
    print(f"  Time: {sweep_results['avg_time_s']*1000:.1f} ms")
    print(f"  Target: <5000 ms  {'✓ PASS' if sweep_results['avg_time_s'] < 5 else '✗ FAIL'}")
    print()
    
    # Save results
    results = {
        'system': sys_info,
        'fft': fft_results,
        'capture': capture_results,
        'sweep': sweep_results
    }
    
    output_path = os.path.join(args.output_dir, "benchmark_results.npz")
    np.savez(output_path, **{k: str(v) for k, v in results.items()})
    print(f"Results saved to: {output_path}")
    
    # Text report
    report_path = os.path.join(args.output_dir, "benchmark_report.txt")
    with open(report_path, 'w') as f:
        f.write("Aleph Phaser Benchmark Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Platform: {sys_info.get('platform', 'N/A')}\n")
        f.write(f"CPU: {sys_info.get('cpu_model', 'N/A')}\n")
        f.write(f"Memory: {sys_info.get('memory_total', 'N/A')}\n\n")
        f.write("FFT Results (ms):\n")
        for size, time_ms in fft_results.items():
            f.write(f"  {size}: {time_ms:.4f}\n")
        f.write("\nCapture Results:\n")
        for size, data in capture_results.items():
            f.write(f"  {size}: {data['time_ms']:.2f} ms, {data['throughput_sps']/1e6:.2f} MSPS\n")
        f.write(f"\nBeam Sweep: {sweep_results['avg_time_s']*1000:.1f} ms\n")
    print(f"Report saved to: {report_path}")
    
    # Clean up
    del sdr
    del phaser
    
    print()
    print("Benchmarks complete!")


if __name__ == '__main__':
    main()
