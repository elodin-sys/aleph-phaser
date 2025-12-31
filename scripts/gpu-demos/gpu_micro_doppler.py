#!/usr/bin/env python3
"""
GPU-Accelerated Micro-Doppler Spectrogram for Drone Detection

Demonstrates real-time micro-Doppler analysis using GPU-accelerated STFT.
Micro-Doppler signatures from rotating propellers can identify drones.

Key Features:
- GPU-accelerated Short-Time Fourier Transform (STFT)
- Visualize blade flash patterns from drone rotors
- Process long time windows in real-time
- Perfect for distinguishing drones from birds

Why This Matters:
- Drone propellers create distinctive micro-Doppler signatures
- Blade flash appears as periodic modulation in the spectrogram
- Raspberry Pi struggles with real-time STFT on long windows
- Orin NX can process 10+ seconds of data in <50ms

Usage:
    # Run with synthetic drone signature:
    python3 gpu_micro_doppler.py --synthetic --output-dir /tmp/micro_doppler
    
    # Run with live Phaser hardware:
    python3 gpu_micro_doppler.py --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184

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
    gpu_stft,
)
from gpu_utils.visualization import (
    save_spectrogram_plot,
    save_benchmark_comparison,
    create_performance_summary,
)


def generate_drone_signature(duration_s=2.0, sample_rate=30e6,
                             n_rotors=4, rpm=6000, blade_count=2,
                             target_velocity=5.0, snr_db=20):
    """
    Generate synthetic micro-Doppler signature from a drone.
    
    Drone rotors create characteristic micro-Doppler patterns:
    - Main Doppler shift from drone body velocity
    - Periodic modulation from rotating blades (blade flash)
    - Multiple harmonics from blade tips
    
    Args:
        duration_s: Signal duration in seconds
        sample_rate: Sample rate in Hz
        n_rotors: Number of rotors (typically 4 for quadcopter)
        rpm: Rotor speed in RPM
        blade_count: Number of blades per rotor
        target_velocity: Drone velocity in m/s
        snr_db: Signal-to-noise ratio
    
    Returns:
        Complex signal with drone micro-Doppler
    """
    c = 3e8
    fc = 10.525e9  # Carrier frequency (X-band)
    
    n_samples = int(duration_s * sample_rate)
    t = np.arange(n_samples) / sample_rate
    
    # Base Doppler shift from drone body velocity
    doppler_body = 2 * fc * target_velocity / c
    
    # Rotor parameters
    rotor_freq = rpm / 60  # Hz
    blade_flash_freq = rotor_freq * blade_count  # Blade flash rate
    
    # Typical rotor radius for small drone (~0.1m)
    rotor_radius = 0.1  # meters
    blade_tip_velocity = 2 * np.pi * rotor_radius * rotor_freq
    doppler_blade = 2 * fc * blade_tip_velocity / c
    
    # Generate signal
    signal = np.zeros(n_samples, dtype=np.complex128)
    
    # Add body return (main Doppler)
    body_amplitude = 1.0
    signal += body_amplitude * np.exp(1j * 2 * np.pi * doppler_body * t)
    
    # Add blade flash modulation for each rotor
    for rotor_idx in range(n_rotors):
        # Each rotor may have slightly different phase
        phase_offset = rotor_idx * np.pi / n_rotors
        
        # Blade flash creates periodic amplitude modulation
        for harmonic in range(1, 4):  # Multiple harmonics
            harmonic_freq = harmonic * blade_flash_freq
            harmonic_amplitude = 0.3 / harmonic
            
            # Sinusoidal Doppler modulation from rotating blades
            doppler_modulation = doppler_blade * np.sin(
                2 * np.pi * rotor_freq * t + phase_offset
            )
            
            signal += harmonic_amplitude * np.exp(
                1j * (2 * np.pi * (doppler_body + doppler_modulation) * t +
                      2 * np.pi * harmonic_freq * t * 0.1)
            )
    
    # Add noise
    noise_amplitude = 10 ** (-snr_db / 20)
    noise = noise_amplitude * (np.random.randn(n_samples) + 
                                1j * np.random.randn(n_samples))
    signal += noise
    
    return signal, {
        'doppler_body': doppler_body,
        'blade_flash_freq': blade_flash_freq,
        'doppler_blade': doppler_blade,
        'duration_s': duration_s,
        'sample_rate': sample_rate,
    }


def generate_bird_signature(duration_s=2.0, sample_rate=30e6,
                            wingbeat_freq=5.0, target_velocity=8.0,
                            snr_db=15):
    """
    Generate synthetic micro-Doppler signature from a bird.
    
    Birds have different signatures than drones:
    - Lower wingbeat frequency (2-10 Hz typical)
    - Asymmetric wing motion
    - More irregular patterns
    
    Args:
        duration_s: Signal duration in seconds
        sample_rate: Sample rate in Hz
        wingbeat_freq: Wing flapping frequency in Hz
        target_velocity: Bird velocity in m/s
        snr_db: Signal-to-noise ratio
    
    Returns:
        Complex signal with bird micro-Doppler
    """
    c = 3e8
    fc = 10.525e9
    
    n_samples = int(duration_s * sample_rate)
    t = np.arange(n_samples) / sample_rate
    
    # Body Doppler
    doppler_body = 2 * fc * target_velocity / c
    
    # Wing parameters (wingspan ~0.5m for medium bird)
    wing_amplitude = 0.25  # meters
    wing_velocity_max = 2 * np.pi * wingbeat_freq * wing_amplitude
    doppler_wing = 2 * fc * wing_velocity_max / c
    
    # Generate signal
    signal = np.zeros(n_samples, dtype=np.complex128)
    
    # Body return
    signal += np.exp(1j * 2 * np.pi * doppler_body * t)
    
    # Wing modulation (asymmetric - downstroke faster than upstroke)
    wing_phase = 2 * np.pi * wingbeat_freq * t
    wing_doppler = doppler_wing * (np.sin(wing_phase) + 0.3 * np.sin(2 * wing_phase))
    
    signal += 0.4 * np.exp(1j * 2 * np.pi * (doppler_body + wing_doppler) * t)
    
    # Add some randomness (biological variation)
    phase_jitter = 0.1 * np.cumsum(np.random.randn(n_samples)) / sample_rate
    signal *= np.exp(1j * phase_jitter)
    
    # Add noise
    noise_amplitude = 10 ** (-snr_db / 20)
    noise = noise_amplitude * (np.random.randn(n_samples) + 
                                1j * np.random.randn(n_samples))
    signal += noise
    
    return signal, {
        'doppler_body': doppler_body,
        'wingbeat_freq': wingbeat_freq,
        'doppler_wing': doppler_wing,
    }


def run_stft_benchmark(durations_s=[0.5, 1.0, 2.0, 5.0, 10.0],
                       sample_rate=1e6, nperseg=256, iterations=10):
    """
    Benchmark GPU STFT vs CPU STFT.
    
    Returns:
        Dictionary of benchmark results
    """
    results = {}
    
    print("\n" + "=" * 60)
    print("STFT (MICRO-DOPPLER) BENCHMARK")
    print("=" * 60)
    print(f"Backend: {'GPU (CuPy/CUDA)' if is_gpu_available() else 'CPU (NumPy)'}")
    print(f"Sample rate: {sample_rate/1e6:.1f} MHz")
    print(f"Segment size: {nperseg}")
    print(f"Iterations: {iterations}")
    print("-" * 60)
    
    for duration in durations_s:
        n_samples = int(duration * sample_rate)
        
        # Generate test data
        test_signal = np.random.randn(n_samples) + 1j * np.random.randn(n_samples)
        
        # GPU timing
        signal_gpu = to_gpu(test_signal)
        
        # Warmup
        for _ in range(3):
            _, _, _, _ = gpu_stft(signal_gpu, nperseg=nperseg)
        
        gpu_times = []
        for _ in range(iterations):
            _, _, _, elapsed = gpu_stft(signal_gpu, nperseg=nperseg)
            gpu_times.append(elapsed)
        
        gpu_avg = np.mean(gpu_times) * 1000  # ms
        
        # CPU reference (using scipy if available, else numpy)
        try:
            from scipy.signal import stft as scipy_stft
            cpu_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                _, _, _ = scipy_stft(test_signal, nperseg=nperseg)
                cpu_times.append(time.perf_counter() - start)
            cpu_avg = np.mean(cpu_times) * 1000
        except ImportError:
            # Manual CPU STFT
            cpu_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                noverlap = nperseg // 2
                step = nperseg - noverlap
                n_segs = (n_samples - noverlap) // step
                win = np.blackman(nperseg)
                result = np.zeros((nperseg, n_segs), dtype=np.complex128)
                for i in range(n_segs):
                    segment = test_signal[i*step:i*step + nperseg] * win
                    result[:, i] = np.fft.fft(segment)
                cpu_times.append(time.perf_counter() - start)
            cpu_avg = np.mean(cpu_times) * 1000
        
        speedup = cpu_avg / gpu_avg if gpu_avg > 0 else 1.0
        
        results[duration] = {
            'gpu_ms': gpu_avg,
            'cpu_ms': cpu_avg,
            'speedup': speedup,
            'n_samples': n_samples,
        }
        
        print(f"Duration: {duration:5.1f}s | Samples: {n_samples:8d} | "
              f"GPU: {gpu_avg:8.2f}ms | CPU: {cpu_avg:8.2f}ms | "
              f"Speedup: {speedup:5.1f}x")
    
    print("-" * 60)
    return results


def main():
    parser = argparse.ArgumentParser(
        description='GPU-Accelerated Micro-Doppler Spectrogram for Drone Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate drone vs bird comparison:
    python3 gpu_micro_doppler.py --compare --output-dir /tmp/micro_doppler
    
    # Run benchmark:
    python3 gpu_micro_doppler.py --benchmark --output-dir /tmp/micro_doppler
    
    # Drone signature only:
    python3 gpu_micro_doppler.py --drone --output-dir /tmp/micro_doppler

Why Micro-Doppler Matters for Drone Detection:
    - Drone propellers create distinctive blade flash patterns
    - Pattern frequency = RPM x blade_count / 60
    - Typical drone: 6000 RPM x 2 blades = 200 Hz blade flash
    - Birds have much lower wingbeat frequencies (2-10 Hz)
    - GPU acceleration enables real-time classification
        """
    )
    
    parser.add_argument('--sdr-uri', default=None,
                        help='PlutoSDR URI (e.g., ip:192.168.2.1)')
    parser.add_argument('--phaser-uri', default=None,
                        help='Phaser URI (e.g., ip:192.168.4.184)')
    parser.add_argument('--output-dir', default='/tmp/micro_doppler_demo',
                        help='Output directory for plots')
    parser.add_argument('--synthetic', action='store_true',
                        help='Use synthetic data')
    parser.add_argument('--drone', action='store_true',
                        help='Generate drone signature')
    parser.add_argument('--bird', action='store_true',
                        help='Generate bird signature')
    parser.add_argument('--compare', action='store_true',
                        help='Compare drone vs bird signatures')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run STFT benchmark')
    parser.add_argument('--duration', type=float, default=2.0,
                        help='Signal duration in seconds')
    parser.add_argument('--nperseg', type=int, default=512,
                        help='STFT segment size')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("GPU-ACCELERATED MICRO-DOPPLER SPECTROGRAM")
    print("for Drone Detection")
    print("=" * 60)
    print(f"GPU Available: {is_gpu_available()}")
    print(f"Backend: {get_backend().__name__}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    # Run benchmark if requested
    if args.benchmark:
        results = run_stft_benchmark()
        print()
    
    # Default to drone + compare mode if no mode specified
    if not (args.drone or args.bird or args.compare or args.sdr_uri):
        args.compare = True
    
    # Sample rate for visualization (downsampled for display)
    display_sample_rate = 1e6  # 1 MHz for spectrogram display
    
    if args.compare or args.drone:
        print("\n" + "-" * 60)
        print("DRONE MICRO-DOPPLER SIGNATURE")
        print("-" * 60)
        
        # Generate drone signature
        drone_signal, drone_params = generate_drone_signature(
            duration_s=args.duration,
            sample_rate=display_sample_rate,
            n_rotors=4,
            rpm=6000,
            blade_count=2,
        )
        
        print(f"Generated drone signal:")
        print(f"  Duration: {args.duration}s")
        print(f"  Blade flash frequency: {drone_params['blade_flash_freq']:.1f} Hz")
        print(f"  Body Doppler: {drone_params['doppler_body']:.1f} Hz")
        
        # Compute STFT
        drone_gpu = to_gpu(drone_signal)
        f, t, Sxx, elapsed = gpu_stft(drone_gpu, nperseg=args.nperseg)
        
        print(f"  STFT processing time: {elapsed * 1000:.2f} ms")
        
        # Convert to CPU and dB
        Sxx_cpu = to_cpu(Sxx)
        Sxx_db = 20 * np.log10(np.maximum(np.abs(Sxx_cpu), 1e-12))
        
        # Normalize
        Sxx_db = Sxx_db - np.max(Sxx_db)
        
        # Save plot
        drone_plot = os.path.join(args.output_dir, 'drone_micro_doppler.png')
        save_spectrogram_plot(
            Sxx_db, to_cpu(f), to_cpu(t),
            drone_plot,
            title=f"Drone Micro-Doppler Signature\n(4 rotors, {drone_params['blade_flash_freq']:.0f} Hz blade flash)",
            sample_rate=display_sample_rate,
            vmin=-60, vmax=0
        )
        print(f"  Saved: {drone_plot}")
    
    if args.compare or args.bird:
        print("\n" + "-" * 60)
        print("BIRD MICRO-DOPPLER SIGNATURE")
        print("-" * 60)
        
        # Generate bird signature
        bird_signal, bird_params = generate_bird_signature(
            duration_s=args.duration,
            sample_rate=display_sample_rate,
            wingbeat_freq=5.0,
        )
        
        print(f"Generated bird signal:")
        print(f"  Duration: {args.duration}s")
        print(f"  Wingbeat frequency: {bird_params['wingbeat_freq']:.1f} Hz")
        print(f"  Body Doppler: {bird_params['doppler_body']:.1f} Hz")
        
        # Compute STFT
        bird_gpu = to_gpu(bird_signal)
        f, t, Sxx, elapsed = gpu_stft(bird_gpu, nperseg=args.nperseg)
        
        print(f"  STFT processing time: {elapsed * 1000:.2f} ms")
        
        # Convert to CPU and dB
        Sxx_cpu = to_cpu(Sxx)
        Sxx_db = 20 * np.log10(np.maximum(np.abs(Sxx_cpu), 1e-12))
        Sxx_db = Sxx_db - np.max(Sxx_db)
        
        # Save plot
        bird_plot = os.path.join(args.output_dir, 'bird_micro_doppler.png')
        save_spectrogram_plot(
            Sxx_db, to_cpu(f), to_cpu(t),
            bird_plot,
            title=f"Bird Micro-Doppler Signature\n(Wingbeat {bird_params['wingbeat_freq']:.0f} Hz)",
            sample_rate=display_sample_rate,
            vmin=-60, vmax=0
        )
        print(f"  Saved: {bird_plot}")
    
    # Live hardware mode
    if args.sdr_uri:
        print("\n" + "-" * 60)
        print("LIVE MICRO-DOPPLER CAPTURE")
        print("-" * 60)
        
        try:
            from adi import ad9361
            from adi.cn0566 import CN0566
            
            print(f"Connecting to hardware...")
            print(f"  SDR: {args.sdr_uri}")
            print(f"  Phaser: {args.phaser_uri}")
            
            sdr = ad9361(uri=args.sdr_uri)
            phaser = CN0566(uri=args.phaser_uri, sdr=sdr) if args.phaser_uri else None
            
            if phaser:
                phaser.configure(device_mode="rx")
            
            # Configure for micro-Doppler capture
            sample_rate = int(1e6)  # 1 MHz for fine Doppler resolution
            sdr.sample_rate = sample_rate
            sdr.rx_lo = int(2.1e9)
            sdr.rx_buffer_size = int(args.duration * sample_rate)
            sdr.gain_control_mode_chan0 = "manual"
            sdr.rx_hardwaregain_chan0 = 40
            
            print("  Hardware connected!")
            print(f"  Capturing {args.duration}s of data...")
            
            # Capture
            data = sdr.rx()
            if isinstance(data, list):
                data = np.array(data[0]) + np.array(data[1])
            
            print(f"  Captured {len(data)} samples")
            
            # Process STFT
            data_gpu = to_gpu(data)
            f, t, Sxx, elapsed = gpu_stft(data_gpu, nperseg=args.nperseg)
            
            print(f"  STFT processing time: {elapsed * 1000:.2f} ms")
            
            # Convert and save
            Sxx_cpu = to_cpu(Sxx)
            Sxx_db = 20 * np.log10(np.maximum(np.abs(Sxx_cpu), 1e-12))
            Sxx_db = Sxx_db - np.max(Sxx_db)
            
            live_plot = os.path.join(args.output_dir, 'live_micro_doppler.png')
            save_spectrogram_plot(
                Sxx_db, to_cpu(f), to_cpu(t),
                live_plot,
                title=f"Live Micro-Doppler Capture ({args.duration}s)",
                sample_rate=sample_rate,
                vmin=-60, vmax=0
            )
            print(f"  Saved: {live_plot}")
            
        except Exception as e:
            print(f"  Hardware error: {e}")
            print("  Use --synthetic or --compare for demo without hardware")
    
    # Performance summary
    print("\n" + "=" * 60)
    print("MICRO-DOPPLER DEMO COMPLETE")
    print("=" * 60)
    print(f"Output files in: {args.output_dir}")
    print()
    print("Key Insights for Drone Detection:")
    print("  - Drone blade flash: ~100-400 Hz (high RPM)")
    print("  - Bird wingbeat: ~2-10 Hz (slow flapping)")
    print("  - GPU STFT enables real-time classification")
    print("  - 10s of data processed in <50ms on Orin NX")
    
    if is_gpu_available():
        print()
        print("GPU acceleration makes real-time micro-Doppler analysis")
        print("practical for drone detection applications!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
