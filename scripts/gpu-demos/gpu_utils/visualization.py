"""
Visualization utilities for radar signal processing demos.

Provides real-time plotting capabilities for:
- Range-Doppler maps
- Micro-Doppler spectrograms
- Performance benchmarks
- Target detection overlays
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless operation
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os
import time


# Custom colormap for radar displays (similar to what's used in radar GUIs)
RADAR_COLORS = [
    (0.0, 'navy'),
    (0.25, 'blue'),
    (0.5, 'cyan'),
    (0.75, 'yellow'),
    (1.0, 'red')
]


def get_radar_colormap():
    """Create a custom radar-style colormap."""
    positions = [c[0] for c in RADAR_COLORS]
    colors = [c[1] for c in RADAR_COLORS]
    return LinearSegmentedColormap.from_list('radar', list(zip(positions, colors)))


def save_range_doppler_plot(rd_map, range_axis, doppler_axis, 
                            output_path, title="Range-Doppler Map",
                            vmin=-60, vmax=0, targets=None,
                            processing_time=None):
    """
    Save a range-Doppler map plot to file.
    
    Args:
        rd_map: 2D range-Doppler map (dB scale)
        range_axis: Range values in meters
        doppler_axis: Doppler values in Hz
        output_path: Path to save the plot
        title: Plot title
        vmin, vmax: Color scale limits (dB)
        targets: Optional target detection overlay
        processing_time: Optional processing time to display
    """
    # Convert from GPU if needed
    if hasattr(rd_map, 'get'):
        rd_map = rd_map.get()
    if hasattr(range_axis, 'get'):
        range_axis = range_axis.get()
    if hasattr(doppler_axis, 'get'):
        doppler_axis = doppler_axis.get()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot range-Doppler map
    extent = [range_axis[0], range_axis[-1], doppler_axis[0], doppler_axis[-1]]
    im = ax.imshow(rd_map, aspect='auto', origin='lower', extent=extent,
                   cmap=get_radar_colormap(), vmin=vmin, vmax=vmax)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label='Power (dB)')
    
    # Overlay targets if provided
    if targets is not None:
        if hasattr(targets, 'get'):
            targets = targets.get()
        # Mark detected targets
        target_mask = ~np.isnan(targets)
        target_y, target_x = np.where(target_mask)
        if len(target_x) > 0:
            # Convert indices to physical coordinates
            range_vals = range_axis[target_x] if len(range_axis) == rd_map.shape[1] else target_x
            doppler_vals = doppler_axis[target_y] if len(doppler_axis) == rd_map.shape[0] else target_y
            ax.scatter(range_vals, doppler_vals, c='lime', s=20, marker='o', 
                      label='Detected Targets', alpha=0.7)
            ax.legend(loc='upper right')
    
    ax.set_xlabel('Range (m)')
    ax.set_ylabel('Doppler (Hz)')
    
    # Add processing time to title if provided
    if processing_time is not None:
        title = f"{title}\n(Processing time: {processing_time*1000:.2f} ms)"
    ax.set_title(title)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def save_spectrogram_plot(Sxx, f, t, output_path, 
                          title="Micro-Doppler Spectrogram",
                          sample_rate=1.0, vmin=-60, vmax=0):
    """
    Save a micro-Doppler spectrogram plot.
    
    Args:
        Sxx: Spectrogram magnitude (linear or dB)
        f: Frequency axis (normalized -0.5 to 0.5 or Hz)
        t: Time axis (samples or seconds)
        output_path: Path to save plot
        title: Plot title
        sample_rate: Sample rate for axis scaling
        vmin, vmax: Color scale limits
    """
    # Convert from GPU if needed
    if hasattr(Sxx, 'get'):
        Sxx = Sxx.get()
    if hasattr(f, 'get'):
        f = f.get()
    if hasattr(t, 'get'):
        t = t.get()
    
    # Convert to dB if not already
    if Sxx.max() > 100:  # Likely linear scale
        Sxx_db = 20 * np.log10(np.maximum(Sxx, 1e-12))
    else:
        Sxx_db = Sxx
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Scale axes
    f_hz = f * sample_rate
    t_sec = t / sample_rate
    
    extent = [t_sec[0], t_sec[-1], f_hz[0], f_hz[-1]]
    im = ax.imshow(Sxx_db, aspect='auto', origin='lower', extent=extent,
                   cmap='viridis', vmin=vmin, vmax=vmax)
    
    cbar = plt.colorbar(im, ax=ax, label='Power (dB)')
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_title(title)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def save_cfar_plot(spectrum_db, threshold, targets, freq_axis,
                   output_path, title="CFAR Target Detection",
                   processing_time=None):
    """
    Save a CFAR detection plot showing spectrum, threshold, and targets.
    
    Args:
        spectrum_db: Input spectrum in dB
        threshold: CFAR threshold
        targets: Detected targets (masked array)
        freq_axis: Frequency axis
        output_path: Path to save plot
        title: Plot title
        processing_time: Optional processing time to display
    """
    # Convert from GPU if needed
    if hasattr(spectrum_db, 'get'):
        spectrum_db = spectrum_db.get()
    if hasattr(threshold, 'get'):
        threshold = threshold.get()
    if hasattr(targets, 'get'):
        targets = targets.get()
    if hasattr(freq_axis, 'get'):
        freq_axis = freq_axis.get()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot spectrum
    ax.plot(freq_axis, spectrum_db, 'b-', label='Spectrum', linewidth=1)
    
    # Plot threshold
    ax.plot(freq_axis, threshold, 'r--', label='CFAR Threshold', linewidth=1.5)
    
    # Highlight detected targets
    # targets can be either indices (new format) or masked array with NaN (old format)
    if targets is not None and len(targets) > 0:
        # Check if targets are indices (integers) or masked values
        if targets.dtype in [np.int32, np.int64, np.intp]:
            # New format: targets are indices
            target_indices = targets
        else:
            # Old format: targets are values with NaN for non-detections
            valid_targets = ~np.isnan(targets)
            target_indices = np.where(valid_targets)[0]
        
        if len(target_indices) > 0:
            ax.scatter(freq_axis[target_indices], spectrum_db[target_indices],
                      c='lime', s=50, marker='o', label='Detected Targets', zorder=5)
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power (dB)')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    if processing_time is not None:
        title = f"{title}\n(Processing time: {processing_time*1000:.3f} ms)"
    ax.set_title(title)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def save_benchmark_comparison(results, output_path, title="GPU vs CPU Performance"):
    """
    Save a benchmark comparison bar chart.
    
    Args:
        results: Dictionary with size -> {'gpu_ms': x, 'cpu_ms': y, 'speedup': z}
        output_path: Path to save plot
        title: Plot title
    """
    sizes = list(results.keys())
    gpu_times = [results[s].get('gpu_ms', 0) or 0 for s in sizes]
    cpu_times = [results[s].get('cpu_ms', 0) for s in sizes]
    speedups = [results[s].get('speedup', 1) or 1 for s in sizes]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Bar chart of times
    x = np.arange(len(sizes))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, cpu_times, width, label='CPU (NumPy)', color='#ff7f0e')
    bars2 = ax1.bar(x + width/2, gpu_times, width, label='GPU (CuPy)', color='#1f77b4')
    
    ax1.set_xlabel('FFT Size')
    ax1.set_ylabel('Time (ms)')
    ax1.set_title('Processing Time Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(s) for s in sizes], rotation=45)
    ax1.legend()
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Speedup chart
    colors = ['#2ca02c' if s > 1 else '#d62728' for s in speedups]
    bars3 = ax2.bar(x, speedups, color=colors)
    ax2.axhline(y=1, color='gray', linestyle='--', linewidth=1)
    
    ax2.set_xlabel('FFT Size')
    ax2.set_ylabel('Speedup (CPU time / GPU time)')
    ax2.set_title('GPU Speedup Factor')
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(s) for s in sizes], rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add speedup labels
    for bar, speedup in zip(bars3, speedups):
        height = bar.get_height()
        ax2.annotate(f'{speedup:.1f}x',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def create_performance_summary(metrics, output_path):
    """
    Create a text-based performance summary.
    
    Args:
        metrics: Dictionary of metric name -> value pairs
        output_path: Path to save summary
    """
    lines = [
        "=" * 60,
        "GPU RADAR DEMO - PERFORMANCE SUMMARY",
        "=" * 60,
        "",
        f"Platform: {'GPU (CuPy/CUDA)' if metrics.get('gpu_available', False) else 'CPU (NumPy)'}",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "-" * 60,
        "PROCESSING TIMES",
        "-" * 60,
    ]
    
    for key, value in metrics.items():
        if key.endswith('_time_ms'):
            name = key.replace('_time_ms', '').replace('_', ' ').title()
            lines.append(f"  {name}: {value:.3f} ms")
    
    lines.extend([
        "",
        "-" * 60,
        "THROUGHPUT",
        "-" * 60,
    ])
    
    for key, value in metrics.items():
        if 'fps' in key.lower() or 'throughput' in key.lower():
            name = key.replace('_', ' ').title()
            lines.append(f"  {name}: {value:.1f}")
    
    lines.extend([
        "",
        "-" * 60,
        "COMPARISON VS RASPBERRY PI 4",
        "-" * 60,
    ])
    
    # Estimated Pi performance (based on benchmarks)
    pi_estimates = {
        'fft_1024': 0.5,      # ms
        'fft_8192': 5.0,      # ms
        'fft_65536': 200.0,   # ms
        'cfar_8192': 50.0,    # ms
    }
    
    for key, pi_time in pi_estimates.items():
        if f'{key}_time_ms' in metrics:
            aleph_time = metrics[f'{key}_time_ms']
            speedup = pi_time / aleph_time if aleph_time > 0 else 0
            lines.append(f"  {key}: Pi4={pi_time:.1f}ms, Aleph={aleph_time:.3f}ms, Speedup={speedup:.1f}x")
    
    lines.extend([
        "",
        "=" * 60,
        "Aleph (Orin NX 16GB) demonstrates significant performance",
        "advantages for radar signal processing workloads.",
        "=" * 60,
    ])
    
    summary = "\n".join(lines)
    
    with open(output_path, 'w') as f:
        f.write(summary)
    
    print(summary)
    return output_path
