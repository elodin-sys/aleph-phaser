#!/usr/bin/env python3
"""
GPU-Accelerated Range-Doppler Map Demo

Demonstrates real-time FMCW radar range-Doppler processing using GPU acceleration.
This showcases a capability that would be impractical on a Raspberry Pi.

Key Features:
- GPU-accelerated 2D FFT using CuPy
- Process large buffers (64K+ samples) at high frame rates
- Real-time range vs velocity visualization
- Side-by-side CPU vs GPU timing comparison

Usage:
    # On Aleph (with GPU):
    python3 gpu_range_doppler.py --output-dir /tmp/gpu_demo
    
    # With live Phaser hardware:
    python3 gpu_range_doppler.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184

Requirements:
    - CuPy installed (run /etc/gpu-radar/setup-cupy.sh first)
    - For live mode: PlutoSDR and Phaser connected

Author: Elodin (for Analog Devices Phaser Demo)
Date: December 2024
"""

import argparse
import os
import sys
import time
import numpy as np

# Set matplotlib backend before any imports
import matplotlib
matplotlib.use('Agg')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpu_utils import (
    is_gpu_available,
    get_backend,
    to_gpu,
    to_cpu,
    gpu_range_doppler,
    gpu_fft2,
)
from gpu_utils.visualization import (
    save_range_doppler_plot,
    save_benchmark_comparison,
    create_performance_summary,
)


# Physical constants
C = 3e8  # Speed of light (m/s)


def generate_synthetic_fmcw_data(n_range=1024, n_doppler=256, 
                                  targets=None, noise_level=-40):
    """
    Generate synthetic FMCW radar data with simulated targets.
    
    Args:
        n_range: Number of range bins (samples per chirp)
        n_doppler: Number of Doppler bins (number of chirps)
        targets: List of (range_bin, doppler_bin, amplitude_db) tuples
        noise_level: Noise floor in dB
    
    Returns:
        Complex IQ data array
    """
    xp = get_backend()
    
    # Default targets: one stationary, one moving
    if targets is None:
        targets = [
            (n_range // 4, n_doppler // 2, -10),       # Target at 1/4 range, stationary
            (n_range // 2, n_doppler // 2 + 20, -15),  # Target at 1/2 range, moving
            (3 * n_range // 4, n_doppler // 2 - 30, -20),  # Target at 3/4 range, moving opposite
        ]
    
    # Generate noise floor
    noise_amplitude = 10 ** (noise_level / 20)
    data = noise_amplitude * (xp.random.randn(n_doppler, n_range) + 
                               1j * xp.random.randn(n_doppler, n_range))
    
    # Create coordinate grids for vectorized target generation
    r_idx = xp.arange(n_range)
    d_idx = xp.arange(n_doppler)
    R, D = xp.meshgrid(r_idx, d_idx)  # R is range, D is Doppler
    
    # Add targets as sinusoids in the beat frequency domain (vectorized)
    for range_bin, doppler_bin, amplitude_db in targets:
        amplitude = 10 ** (amplitude_db / 20)
        
        # Create target signal - fully vectorized
        range_phase = 2 * xp.pi * range_bin / n_range
        doppler_phase = 2 * xp.pi * doppler_bin / n_doppler
        
        # Compute phase for all (range, doppler) pairs at once
        phase = range_phase * R + doppler_phase * D
        data += amplitude * xp.exp(1j * phase)
    
    return data.flatten()


def capture_live_data(sdr, n_samples):
    """
    Capture live data from PlutoSDR.
    
    Args:
        sdr: AD9361 SDR object
        n_samples: Number of samples to capture
    
    Returns:
        Complex IQ data
    """
    sdr.rx_buffer_size = n_samples
    data = sdr.rx()
    
    # Combine channels if both available
    if isinstance(data, list) and len(data) >= 2:
        return np.array(data[0]) + np.array(data[1])
    elif isinstance(data, list):
        return np.array(data[0])
    return np.array(data)


def run_benchmark(n_range_sizes=[1024, 2048, 4096, 8192], 
                  n_doppler=256, iterations=20):
    """
    Run benchmark comparing GPU vs CPU range-Doppler processing.
    
    Returns:
        Dictionary of benchmark results
    """
    xp = get_backend()
    results = {}
    
    print("\n" + "=" * 60)
    print("RANGE-DOPPLER PROCESSING BENCHMARK")
    print("=" * 60)
    print(f"Backend: {'GPU (CuPy/CUDA)' if is_gpu_available() else 'CPU (NumPy)'}")
    print(f"Doppler bins: {n_doppler}")
    print(f"Iterations per size: {iterations}")
    print("-" * 60)
    
    for n_range in n_range_sizes:
        total_samples = n_range * n_doppler
        
        # Generate test data
        data = generate_synthetic_fmcw_data(n_range, n_doppler)
        
        # Warmup
        for _ in range(5):
            _, _, _, _ = gpu_range_doppler(data, n_range, n_doppler)
        
        # Benchmark GPU/accelerated path
        times = []
        for _ in range(iterations):
            _, _, _, elapsed = gpu_range_doppler(data, n_range, n_doppler)
            times.append(elapsed)
        
        gpu_avg = np.mean(times) * 1000  # ms
        gpu_std = np.std(times) * 1000
        
        # CPU reference (force NumPy)
        data_np = to_cpu(data).copy()
        cpu_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            matrix = data_np[:n_range * n_doppler].reshape(n_doppler, n_range)
            window_2d = np.outer(np.blackman(n_doppler), np.blackman(n_range))
            rd = np.fft.fftshift(np.fft.fft2(matrix * window_2d))
            rd_db = 20 * np.log10(np.maximum(np.abs(rd), 1e-12))
            cpu_times.append(time.perf_counter() - start)
        
        cpu_avg = np.mean(cpu_times) * 1000  # ms
        
        speedup = cpu_avg / gpu_avg if gpu_avg > 0 else 1.0
        fps = 1000 / gpu_avg if gpu_avg > 0 else 0
        
        results[n_range] = {
            'gpu_ms': gpu_avg,
            'cpu_ms': cpu_avg,
            'speedup': speedup,
            'fps': fps,
            'samples': total_samples,
        }
        
        print(f"Range bins: {n_range:5d} | Samples: {total_samples:7d} | "
              f"GPU: {gpu_avg:7.3f}ms | CPU: {cpu_avg:7.3f}ms | "
              f"Speedup: {speedup:5.1f}x | FPS: {fps:6.1f}")
    
    print("-" * 60)
    return results


def main():
    parser = argparse.ArgumentParser(
        description='GPU-Accelerated Range-Doppler Map Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with synthetic data (no hardware needed):
    python3 gpu_range_doppler.py --synthetic --output-dir /tmp/gpu_demo

    # Run with live Phaser hardware:
    python3 gpu_range_doppler.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
        """
    )
    
    parser.add_argument('--sdr-uri', default=None,
                        help='PlutoSDR URI (e.g., ip:192.168.2.1)')
    parser.add_argument('--phaser-uri', default=None,
                        help='Phaser URI (e.g., ip:192.168.4.184)')
    parser.add_argument('--output-dir', default='/tmp/gpu_radar_demo',
                        help='Output directory for plots and results')
    parser.add_argument('--synthetic', action='store_true',
                        help='Use synthetic data (no hardware required)')
    parser.add_argument('--n-range', type=int, default=1024,
                        help='Number of range bins')
    parser.add_argument('--n-doppler', type=int, default=256,
                        help='Number of Doppler bins')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run performance benchmark')
    parser.add_argument('--chirp-bw', type=float, default=500e6,
                        help='Chirp bandwidth in Hz')
    parser.add_argument('--chirp-time', type=float, default=0.5e-3,
                        help='Chirp duration in seconds')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("GPU-ACCELERATED RANGE-DOPPLER MAP DEMO")
    print("=" * 60)
    print(f"GPU Available: {is_gpu_available()}")
    print(f"Backend: {get_backend().__name__}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    # Run benchmark if requested
    if args.benchmark:
        results = run_benchmark()
        
        # Save benchmark plot
        benchmark_path = os.path.join(args.output_dir, 'benchmark_results.png')
        save_benchmark_comparison(results, benchmark_path, 
                                  title="Range-Doppler Processing: GPU vs CPU")
        print(f"\nBenchmark plot saved to: {benchmark_path}")
    
    # Determine data source
    if args.synthetic or (args.sdr_uri is None):
        print("\nUsing synthetic FMCW radar data...")
        use_hardware = False
        
        # Generate synthetic data with realistic targets
        targets = [
            (args.n_range // 4, args.n_doppler // 2, -10),        # Near, stationary
            (args.n_range // 2, args.n_doppler // 2 + 30, -15),   # Mid, approaching
            (3 * args.n_range // 4, args.n_doppler // 2 - 20, -12),  # Far, receding
            (args.n_range // 3, args.n_doppler // 2 + 50, -18),   # Drone (high Doppler)
        ]
        data = generate_synthetic_fmcw_data(args.n_range, args.n_doppler, 
                                             targets=targets, noise_level=-50)
    else:
        print(f"\nConnecting to hardware...")
        print(f"  SDR: {args.sdr_uri}")
        print(f"  Phaser: {args.phaser_uri}")
        use_hardware = True
        
        try:
            from adi import ad9361
            from adi.cn0566 import CN0566
            
            # Connect to hardware
            sdr = ad9361(uri=args.sdr_uri)
            phaser = CN0566(uri=args.phaser_uri, sdr=sdr)
            
            # Configure for FMCW
            phaser.configure(device_mode="rx")
            
            # Configure SDR
            sdr.sample_rate = int(30e6)
            sdr.rx_lo = int(2.1e9)
            sdr.rx_buffer_size = args.n_range * args.n_doppler
            sdr.gain_control_mode_chan0 = "manual"
            sdr.gain_control_mode_chan1 = "manual"
            sdr.rx_hardwaregain_chan0 = 30
            sdr.rx_hardwaregain_chan1 = 30
            
            # Configure Phaser PLL for FMCW
            output_freq = 12.1e9
            phaser.frequency = int(output_freq / 4)
            phaser.freq_dev_range = int(args.chirp_bw / 4)
            phaser.freq_dev_step = int((args.chirp_bw / 4) / 500)
            phaser.freq_dev_time = int(args.chirp_time * 1e6)
            phaser.ramp_mode = "continuous_triangular"
            phaser.enable = 0
            
            print("  Hardware connected!")
            
            # Capture data
            data = capture_live_data(sdr, args.n_range * args.n_doppler)
            
        except Exception as e:
            print(f"  Hardware connection failed: {e}")
            print("  Falling back to synthetic data...")
            use_hardware = False
            data = generate_synthetic_fmcw_data(args.n_range, args.n_doppler)
    
    # Process range-Doppler map
    print(f"\nProcessing Range-Doppler Map...")
    print(f"  Range bins: {args.n_range}")
    print(f"  Doppler bins: {args.n_doppler}")
    print(f"  Total samples: {args.n_range * args.n_doppler}")
    
    # GPU-accelerated processing
    rd_map, range_axis, doppler_axis, elapsed = gpu_range_doppler(
        data,
        n_range=args.n_range,
        n_doppler=args.n_doppler,
        chirp_bw=args.chirp_bw,
        chirp_time=args.chirp_time
    )
    
    print(f"  Processing time: {elapsed * 1000:.3f} ms")
    print(f"  Frame rate: {1/elapsed:.1f} FPS")
    
    # Convert to CPU for visualization
    rd_map_cpu = to_cpu(rd_map)
    range_axis_cpu = to_cpu(range_axis)
    doppler_axis_cpu = to_cpu(doppler_axis)
    
    # Save plot
    plot_path = os.path.join(args.output_dir, 'range_doppler_map.png')
    save_range_doppler_plot(
        rd_map_cpu, range_axis_cpu, doppler_axis_cpu,
        plot_path,
        title=f"Range-Doppler Map ({'Live' if use_hardware else 'Synthetic'} Data)",
        processing_time=elapsed
    )
    print(f"\nRange-Doppler plot saved to: {plot_path}")
    
    # Create performance summary
    metrics = {
        'gpu_available': is_gpu_available(),
        'range_doppler_time_ms': elapsed * 1000,
        'range_doppler_fps': 1 / elapsed if elapsed > 0 else 0,
        'n_range': args.n_range,
        'n_doppler': args.n_doppler,
        'total_samples': args.n_range * args.n_doppler,
    }
    
    # Run quick benchmarks for the summary
    print("\nRunning quick benchmark for summary...")
    for size in [1024, 8192, 65536]:
        test_data = np.random.randn(size) + 1j * np.random.randn(size)
        test_data_gpu = to_gpu(test_data)
        
        # Warmup
        for _ in range(5):
            if is_gpu_available():
                import cupy as cp
                _ = cp.fft.fft(test_data_gpu)
                cp.cuda.Stream.null.synchronize()
            else:
                _ = np.fft.fft(test_data)
        
        # Time it
        times = []
        for _ in range(20):
            start = time.perf_counter()
            if is_gpu_available():
                import cupy as cp
                _ = cp.fft.fft(test_data_gpu)
                cp.cuda.Stream.null.synchronize()
            else:
                _ = np.fft.fft(test_data)
            times.append(time.perf_counter() - start)
        
        metrics[f'fft_{size}_time_ms'] = np.mean(times) * 1000
    
    summary_path = os.path.join(args.output_dir, 'performance_summary.txt')
    create_performance_summary(metrics, summary_path)
    print(f"\nPerformance summary saved to: {summary_path}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"Output files in: {args.output_dir}")
    print()
    print("Key Results:")
    print(f"  - Range-Doppler processing: {elapsed * 1000:.3f} ms")
    print(f"  - Achievable frame rate: {1/elapsed:.1f} FPS")
    print(f"  - Buffer size processed: {args.n_range * args.n_doppler} samples")
    
    if is_gpu_available():
        print()
        print("GPU acceleration enabled - this demo showcases capabilities")
        print("that would be impractical on a Raspberry Pi!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
