#!/usr/bin/env python3
"""
GPU-Accelerated CFAR Target Detection Demo

Demonstrates GPU-accelerated Constant False Alarm Rate (CFAR) detection
for radar target identification. Shows massive speedup over CPU implementation.

Key Features:
- GPU-parallel CFAR processing
- Processes entire spectrum in single kernel
- Handles large FFT sizes (64K+ samples)
- Side-by-side comparison with CPU implementation

Usage:
    # Run benchmark with synthetic data:
    python3 gpu_cfar.py --benchmark --output-dir /tmp/cfar_demo
    
    # Run with live Phaser hardware:
    python3 gpu_cfar.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184

The CFAR algorithm:
- Slides a window across the spectrum
- Estimates local noise floor from reference cells
- Sets detection threshold based on noise + bias
- Detects targets that exceed threshold

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
    gpu_fft,
    gpu_cfar,
)
from gpu_utils.visualization import (
    save_cfar_plot,
    save_benchmark_comparison,
    create_performance_summary,
)


def cpu_cfar_reference(spectrum_db, num_guard_cells, num_ref_cells, bias_db):
    """
    Reference CPU implementation of CFAR (from target_detection_dbfs.py).
    This is the original loop-based implementation for comparison.
    """
    N = len(spectrum_db)
    threshold = np.full_like(spectrum_db, np.min(spectrum_db))
    
    for center_idx in range(num_guard_cells + num_ref_cells, 
                            N - (num_guard_cells + num_ref_cells)):
        min_idx = center_idx - (num_guard_cells + num_ref_cells)
        min_guard = center_idx - num_guard_cells
        max_idx = center_idx + (num_guard_cells + num_ref_cells) + 1
        max_guard = center_idx + num_guard_cells + 1
        
        lower_nearby = spectrum_db[min_idx:min_guard]
        upper_nearby = spectrum_db[max_guard:max_idx]
        
        mean_val = np.mean(np.concatenate([lower_nearby, upper_nearby]))
        threshold[center_idx] = mean_val + bias_db
    
    targets = np.where(spectrum_db > threshold, spectrum_db, np.nan)
    return threshold, targets


def generate_synthetic_spectrum(n_samples=8192, n_targets=5, snr_range=(10, 30)):
    """
    Generate synthetic radar spectrum with targets.
    
    Args:
        n_samples: Number of frequency bins
        n_targets: Number of targets to simulate
        snr_range: Range of target SNR values in dB
    
    Returns:
        spectrum_db: Spectrum in dB
        target_positions: Indices of true targets
    """
    # Generate noise floor (complex Gaussian noise)
    noise = np.random.randn(n_samples) + 1j * np.random.randn(n_samples)
    spectrum = np.abs(noise)
    
    # Add targets at random positions
    target_positions = np.random.choice(
        range(n_samples // 10, 9 * n_samples // 10), 
        size=n_targets, 
        replace=False
    )
    
    for pos in target_positions:
        snr = np.random.uniform(snr_range[0], snr_range[1])
        amplitude = 10 ** (snr / 20)
        # Add target with some width
        width = np.random.randint(2, 6)
        for w in range(-width, width + 1):
            if 0 <= pos + w < n_samples:
                spectrum[pos + w] += amplitude * np.exp(-0.5 * (w / (width/2)) ** 2)
    
    # Convert to dB
    spectrum_db = 20 * np.log10(np.maximum(spectrum, 1e-12))
    
    # Normalize to typical radar range
    spectrum_db = spectrum_db - np.median(spectrum_db) - 30
    
    return spectrum_db, target_positions


def run_cfar_benchmark(sizes=[1024, 2048, 4096, 8192, 16384, 32768, 65536],
                       num_guard_cells=10, num_ref_cells=20, bias_db=10,
                       iterations=20):
    """
    Benchmark GPU CFAR vs CPU CFAR.
    
    Returns:
        Dictionary of benchmark results
    """
    results = {}
    
    print("\n" + "=" * 60)
    print("CFAR TARGET DETECTION BENCHMARK")
    print("=" * 60)
    print(f"Backend: {'GPU (CuPy/CUDA)' if is_gpu_available() else 'CPU (NumPy)'}")
    print(f"Guard cells: {num_guard_cells}, Ref cells: {num_ref_cells}")
    print(f"Bias: {bias_db} dB")
    print(f"Iterations: {iterations}")
    print("-" * 60)
    
    for n_samples in sizes:
        # Generate test spectrum
        spectrum_db, _ = generate_synthetic_spectrum(n_samples)
        
        # GPU/accelerated CFAR
        spectrum_gpu = to_gpu(spectrum_db)
        
        # Warmup
        for _ in range(3):
            _, _, _ = gpu_cfar(spectrum_gpu, num_guard_cells, num_ref_cells, bias_db)
        
        # Benchmark GPU
        gpu_times = []
        for _ in range(iterations):
            _, _, elapsed = gpu_cfar(spectrum_gpu, num_guard_cells, num_ref_cells, bias_db)
            gpu_times.append(elapsed)
        
        gpu_avg = np.mean(gpu_times) * 1000  # ms
        
        # CPU reference
        cpu_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            _, _ = cpu_cfar_reference(spectrum_db, num_guard_cells, num_ref_cells, bias_db)
            cpu_times.append(time.perf_counter() - start)
        
        cpu_avg = np.mean(cpu_times) * 1000  # ms
        
        speedup = cpu_avg / gpu_avg if gpu_avg > 0 else 1.0
        
        results[n_samples] = {
            'gpu_ms': gpu_avg,
            'cpu_ms': cpu_avg,
            'speedup': speedup,
        }
        
        print(f"Samples: {n_samples:6d} | GPU: {gpu_avg:8.3f}ms | "
              f"CPU: {cpu_avg:8.3f}ms | Speedup: {speedup:6.1f}x")
    
    print("-" * 60)
    return results


def main():
    parser = argparse.ArgumentParser(
        description='GPU-Accelerated CFAR Target Detection Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run benchmark with synthetic data:
    python3 gpu_cfar.py --benchmark --output-dir /tmp/cfar_demo
    
    # Run single detection demo:
    python3 gpu_cfar.py --synthetic --output-dir /tmp/cfar_demo
    
    # Run with live Phaser hardware:
    python3 gpu_cfar.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
        """
    )
    
    parser.add_argument('--sdr-uri', default=None,
                        help='PlutoSDR URI (e.g., ip:192.168.2.1)')
    parser.add_argument('--phaser-uri', default=None,
                        help='Phaser URI (e.g., ip:192.168.4.184)')
    parser.add_argument('--output-dir', default='/tmp/cfar_demo',
                        help='Output directory for plots and results')
    parser.add_argument('--synthetic', action='store_true',
                        help='Use synthetic data (no hardware required)')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run full benchmark across sizes')
    parser.add_argument('--n-samples', type=int, default=8192,
                        help='Number of FFT samples')
    parser.add_argument('--guard-cells', type=int, default=10,
                        help='Number of CFAR guard cells')
    parser.add_argument('--ref-cells', type=int, default=20,
                        help='Number of CFAR reference cells')
    parser.add_argument('--bias', type=float, default=10,
                        help='CFAR detection bias in dB')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("GPU-ACCELERATED CFAR TARGET DETECTION DEMO")
    print("=" * 60)
    print(f"GPU Available: {is_gpu_available()}")
    print(f"Backend: {get_backend().__name__}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    # Run benchmark if requested
    if args.benchmark:
        results = run_cfar_benchmark(
            num_guard_cells=args.guard_cells,
            num_ref_cells=args.ref_cells,
            bias_db=args.bias
        )
        
        # Save benchmark plot
        benchmark_path = os.path.join(args.output_dir, 'cfar_benchmark.png')
        save_benchmark_comparison(results, benchmark_path,
                                  title="CFAR Target Detection: GPU vs CPU")
        print(f"\nBenchmark plot saved to: {benchmark_path}")
    
    # Run detection demo
    print("\n" + "-" * 60)
    print("CFAR DETECTION DEMO")
    print("-" * 60)
    
    # Get data
    if args.synthetic or args.sdr_uri is None:
        print(f"Using synthetic spectrum ({args.n_samples} samples)...")
        spectrum_db, true_targets = generate_synthetic_spectrum(
            args.n_samples, n_targets=5)
        use_hardware = False
        
        # Create frequency axis for plotting
        sample_rate = 30e6
        freq_axis = np.linspace(-sample_rate/2, sample_rate/2, args.n_samples)
    else:
        print(f"Connecting to hardware...")
        use_hardware = True
        
        try:
            from adi import ad9361
            from adi.cn0566 import CN0566
            
            # Connect
            sdr = ad9361(uri=args.sdr_uri)
            phaser = CN0566(uri=args.phaser_uri, sdr=sdr)
            
            # Configure
            phaser.configure(device_mode="rx")
            sdr.sample_rate = int(30e6)
            sdr.rx_lo = int(2.1e9)
            sdr.rx_buffer_size = args.n_samples
            sdr.gain_control_mode_chan0 = "manual"
            sdr.rx_hardwaregain_chan0 = 30
            
            # Capture
            data = sdr.rx()
            if isinstance(data, list):
                data = np.array(data[0]) + np.array(data[1])
            
            # FFT
            window = np.blackman(len(data))
            spectrum = np.fft.fftshift(np.fft.fft(data * window))
            spectrum_db = 20 * np.log10(np.maximum(np.abs(spectrum), 1e-12))
            
            sample_rate = sdr.sample_rate
            freq_axis = np.linspace(-sample_rate/2, sample_rate/2, len(spectrum))
            true_targets = []
            
            print("  Hardware connected!")
            
        except Exception as e:
            print(f"  Hardware connection failed: {e}")
            print("  Falling back to synthetic data...")
            use_hardware = False
            spectrum_db, true_targets = generate_synthetic_spectrum(args.n_samples)
            sample_rate = 30e6
            freq_axis = np.linspace(-sample_rate/2, sample_rate/2, args.n_samples)
    
    print(f"\nCFAR Parameters:")
    print(f"  Guard cells: {args.guard_cells}")
    print(f"  Reference cells: {args.ref_cells}")
    print(f"  Detection bias: {args.bias} dB")
    
    # GPU-accelerated CFAR
    print(f"\nRunning GPU-accelerated CFAR...")
    spectrum_gpu = to_gpu(spectrum_db)
    threshold, targets, gpu_time = gpu_cfar(
        spectrum_gpu, args.guard_cells, args.ref_cells, args.bias
    )
    
    # CPU reference timing
    print(f"Running CPU reference CFAR...")
    cpu_start = time.perf_counter()
    _, _ = cpu_cfar_reference(spectrum_db, args.guard_cells, args.ref_cells, args.bias)
    cpu_time = time.perf_counter() - cpu_start
    
    # Count detections
    threshold_cpu = to_cpu(threshold)
    targets_cpu = to_cpu(targets)
    n_detections = np.sum(~np.isnan(targets_cpu))
    
    speedup = cpu_time / gpu_time if gpu_time > 0 else 1.0
    
    print(f"\nResults:")
    print(f"  GPU processing time: {gpu_time * 1000:.3f} ms")
    print(f"  CPU processing time: {cpu_time * 1000:.3f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    print(f"  Detections: {n_detections}")
    
    if len(true_targets) > 0:
        print(f"  True targets: {len(true_targets)}")
    
    # Save plot
    plot_path = os.path.join(args.output_dir, 'cfar_detection.png')
    save_cfar_plot(
        spectrum_db, threshold_cpu, targets_cpu, freq_axis,
        plot_path,
        title=f"GPU CFAR Detection ({args.n_samples} samples)",
        processing_time=gpu_time
    )
    print(f"\nCFAR plot saved to: {plot_path}")
    
    # Create performance summary
    metrics = {
        'gpu_available': is_gpu_available(),
        f'cfar_{args.n_samples}_time_ms': gpu_time * 1000,
        'cfar_cpu_time_ms': cpu_time * 1000,
        'cfar_speedup': speedup,
        'n_samples': args.n_samples,
        'n_detections': n_detections,
    }
    
    # Add FFT benchmarks
    for size in [1024, 8192, 65536]:
        if size <= args.n_samples * 4:
            test_data = np.random.randn(size) + 1j * np.random.randn(size)
            test_gpu = to_gpu(test_data)
            
            times = []
            for _ in range(20):
                _, elapsed = gpu_fft(test_gpu, window='blackman')
                times.append(elapsed)
            
            metrics[f'fft_{size}_time_ms'] = np.mean(times) * 1000
    
    summary_path = os.path.join(args.output_dir, 'cfar_performance_summary.txt')
    create_performance_summary(metrics, summary_path)
    
    # Final summary
    print("\n" + "=" * 60)
    print("CFAR DEMO COMPLETE")
    print("=" * 60)
    print(f"Output files in: {args.output_dir}")
    print()
    print("Key Results:")
    print(f"  - CFAR processing ({args.n_samples} samples): {gpu_time * 1000:.3f} ms")
    print(f"  - Speedup vs CPU: {speedup:.1f}x")
    print(f"  - Targets detected: {n_detections}")
    
    if is_gpu_available():
        print()
        print("GPU acceleration dramatically reduces CFAR processing time,")
        print("enabling real-time target detection at high sample rates.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
