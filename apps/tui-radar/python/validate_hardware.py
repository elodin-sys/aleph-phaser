#!/usr/bin/env python3
"""
Hardware Data Validation Script

This script helps validate that the TUI correctly displays radar data by:
1. Capturing frames from hardware (or loading from exports)
2. Analyzing the data structure and expected appearance
3. Generating reference matplotlib plots for visual comparison
4. Providing quantitative validation checks

Usage:
    # Analyze existing exports
    python validate_hardware.py --analyze-export ./exports/frame_*.npy
    
    # Capture new frames and analyze (requires hardware)
    python validate_hardware.py --capture --frames 5 --export ./validation_capture
    
    # Compare TUI export to expectations
    python validate_hardware.py --validate ./exports/frame_20260203_102044_877262.npy
"""

import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

# Add parent directory to path for radar_backend import
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None


def load_frame_with_meta(npy_path: str) -> Tuple[np.ndarray, Dict]:
    """Load a frame and its metadata."""
    frame = np.load(npy_path)
    
    meta = {
        'shape': list(frame.shape),
        'dtype': str(frame.dtype),
        'min': float(frame.min()),
        'max': float(frame.max()),
    }
    
    # Try to load metadata from _meta.json (new format)
    meta_path = npy_path.replace('.npy', '_meta.json')
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            loaded_meta = json.load(f)
            meta.update(loaded_meta)
    
    # Also try to load config.json from parent directory (old capture format)
    parent_dir = os.path.dirname(npy_path)
    config_path = os.path.join(parent_dir, 'config.json')
    if os.path.exists(config_path) and 'config' not in meta:
        with open(config_path) as f:
            meta['config'] = json.load(f)
    
    return frame, meta


def analyze_frame_structure(frame: np.ndarray, meta: Dict) -> List[ValidationResult]:
    """Analyze the structure of a radar frame."""
    results = []
    dim0, dim1 = frame.shape
    
    # Check 1: Dimensions match config and detect axis swap
    if 'config' in meta:
        expected_d = meta['config'].get('n_doppler', dim0)
        expected_r = meta['config'].get('n_range', dim1)
        
        # Check for normal orientation (n_doppler, n_range)
        matches_normal = (dim0 == expected_d) and (dim1 == expected_r)
        # Check for swapped orientation (n_range, n_doppler)
        matches_swapped = (dim0 == expected_r) and (dim1 == expected_d)
        
        if matches_normal:
            results.append(ValidationResult(
                'dimensions',
                True,
                f"Shape {frame.shape} matches config (n_doppler={expected_d}, n_range={expected_r})"
            ))
            n_doppler, n_range = dim0, dim1
        elif matches_swapped:
            results.append(ValidationResult(
                'dimensions',
                False,
                f"AXIS SWAP DETECTED! Shape {frame.shape} is (n_range, n_doppler) but expected (n_doppler, n_range). "
                f"Config has n_doppler={expected_d}, n_range={expected_r}. "
                f"This frame needs to be transposed for correct TUI display!"
            ))
            # For subsequent analysis, use the swapped interpretation
            n_doppler, n_range = dim1, dim0
        else:
            results.append(ValidationResult(
                'dimensions',
                False,
                f"Shape {frame.shape} does NOT match config (n_doppler={expected_d}, n_range={expected_r})"
            ))
            n_doppler, n_range = dim0, dim1
    else:
        n_doppler, n_range = dim0, dim1
    
    # Check 2: Value range is reasonable
    min_val, max_val = frame.min(), frame.max()
    if 'config' in meta:
        expected_min = meta['config'].get('min_scale', 0)
        expected_max = meta['config'].get('max_scale', 8)
    else:
        expected_min, expected_max = 0, 8
    
    range_ok = (min_val >= expected_min - 0.1) and (max_val <= expected_max + 0.1)
    results.append(ValidationResult(
        'value_range',
        range_ok,
        f"Values [{min_val:.2f}, {max_val:.2f}] vs expected [{expected_min}, {expected_max}]",
        {'actual_min': min_val, 'actual_max': max_val}
    ))
    
    # Check 3: Not all zeros or constant
    is_constant = frame.std() < 0.01
    results.append(ValidationResult(
        'has_variation',
        not is_constant,
        f"Frame std={frame.std():.4f} - {'CONSTANT (bad)' if is_constant else 'has variation (good)'}",
        {'std': float(frame.std())}
    ))
    
    # Check 4: Check for extreme aspect ratio issues
    aspect = n_doppler / n_range
    aspect_ok = aspect < 50  # Very extreme would be problematic
    results.append(ValidationResult(
        'aspect_ratio',
        aspect_ok,
        f"Aspect ratio {aspect:.1f}:1 (Doppler:Range) - {'OK' if aspect_ok else 'EXTREME'}",
        {'aspect_ratio': aspect}
    ))
    
    return results


def analyze_coordinate_mapping(frame: np.ndarray, meta: Dict) -> List[ValidationResult]:
    """Verify coordinate mapping matches expectations.
    
    For radar data:
    - frame[d, r] where d=Doppler index, r=Range index
    - d=0 should be bottom (negative max Doppler)
    - d=max should be top (positive max Doppler)
    - r=0 should be left (0 meters / near range)
    - r=max should be right (max_range meters)
    """
    results = []
    n_doppler, n_range = frame.shape
    
    # Get corner values
    corners = {
        'BL': frame[0, 0],
        'BR': frame[0, n_range-1],
        'TL': frame[n_doppler-1, 0],
        'TR': frame[n_doppler-1, n_range-1],
    }
    
    results.append(ValidationResult(
        'corner_values',
        True,  # Always pass, this is informational
        f"BL={corners['BL']:.2f}, BR={corners['BR']:.2f}, TL={corners['TL']:.2f}, TR={corners['TR']:.2f}",
        corners
    ))
    
    # Check DC component location (should be at center Doppler)
    center_d = n_doppler // 2
    dc_line = frame[center_d, :]
    dc_mean = dc_line.mean()
    
    # Compare to rows away from DC
    off_dc_mean = np.mean([frame[0, :].mean(), frame[-1, :].mean()])
    
    dc_prominent = dc_mean > off_dc_mean + 1.0  # DC should be at least 1 unit brighter
    results.append(ValidationResult(
        'dc_at_center',
        dc_prominent,
        f"DC line (d={center_d}) mean={dc_mean:.2f}, edges mean={off_dc_mean:.2f} - "
        f"{'DC prominent at center (expected)' if dc_prominent else 'No clear DC (MTI active or weak signal)'}",
        {'dc_mean': float(dc_mean), 'edge_mean': float(off_dc_mean)}
    ))
    
    return results


def analyze_for_targets(frame: np.ndarray, meta: Dict) -> List[ValidationResult]:
    """Look for target signatures in the frame."""
    results = []
    n_doppler, n_range = frame.shape
    
    # Find peaks above noise floor
    noise_floor = np.percentile(frame, 25)
    threshold = noise_floor + 2 * frame.std()
    
    peaks_mask = frame > threshold
    n_peaks = peaks_mask.sum()
    
    results.append(ValidationResult(
        'peak_detection',
        n_peaks > 0,
        f"Found {n_peaks} pixels above threshold ({threshold:.2f})",
        {'n_peaks': n_peaks, 'threshold': float(threshold), 'noise_floor': float(noise_floor)}
    ))
    
    if n_peaks > 0 and n_peaks < 500:
        # Find the brightest peak
        max_idx = np.unravel_index(frame.argmax(), frame.shape)
        max_val = frame[max_idx]
        
        # Convert to physical units if config available
        if 'config' in meta:
            config = meta['config']
            
            # Range calculation
            sample_rate = config.get('sample_rate', 4_000_000)
            chirp_bw = config.get('chirp_bw', 500_000_000)
            c = 3e8
            range_res = c / (2 * chirp_bw)
            
            # The range bins are sliced, so we need to account for that
            # Assuming frame starts at 0m
            peak_range_m = max_idx[1] * range_res * (sample_rate / chirp_bw) / 2
            
            # Doppler calculation
            ramp_time = config.get('ramp_time_us', 500) * 1e-6
            doppler_res = 1 / (config.get('num_chirps', 512) * ramp_time)
            peak_doppler_idx = max_idx[0] - n_doppler // 2  # Center at 0
            peak_doppler_hz = peak_doppler_idx * doppler_res
            
            results.append(ValidationResult(
                'brightest_peak',
                True,
                f"Brightest at [d={max_idx[0]}, r={max_idx[1]}] = {max_val:.2f} "
                f"(~{peak_range_m:.1f}m, ~{peak_doppler_hz:.1f}Hz Doppler)",
                {'doppler_idx': int(max_idx[0]), 'range_idx': int(max_idx[1]), 
                 'value': float(max_val), 'range_m': float(peak_range_m), 
                 'doppler_hz': float(peak_doppler_hz)}
            ))
        else:
            results.append(ValidationResult(
                'brightest_peak',
                True,
                f"Brightest at [d={max_idx[0]}, r={max_idx[1]}] = {max_val:.2f}",
                {'doppler_idx': int(max_idx[0]), 'range_idx': int(max_idx[1]), 'value': float(max_val)}
            ))
    
    return results


def generate_reference_plot(frame: np.ndarray, meta: Dict, output_path: str):
    """Generate a matplotlib reference plot for visual comparison."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
    except ImportError:
        print("Matplotlib not available - skipping reference plot generation")
        return
    
    n_doppler, n_range = frame.shape
    
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig)
    
    # Main heatmap (matches TUI layout)
    ax_main = fig.add_subplot(gs[0:2, 0:2])
    
    # Use same colormap as TUI (inferno-like)
    im = ax_main.imshow(frame, aspect='auto', cmap='inferno', origin='lower',
                        vmin=meta.get('min', 0), vmax=meta.get('max', 8))
    
    ax_main.set_xlabel('Range Bin (r) →')
    ax_main.set_ylabel('Doppler Bin (d) →')
    ax_main.set_title('Range-Doppler Map (Origin=Bottom-Left)\nrd_map[d, r]: d=row, r=column')
    
    # Add corner labels
    ax_main.text(0, 0, 'BL\n[0,0]', ha='left', va='bottom', color='white', fontsize=8, 
                 bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    ax_main.text(n_range-1, 0, 'BR\n[0,max_r]', ha='right', va='bottom', color='white', fontsize=8,
                 bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    ax_main.text(0, n_doppler-1, 'TL\n[max_d,0]', ha='left', va='top', color='white', fontsize=8,
                 bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    ax_main.text(n_range-1, n_doppler-1, 'TR\n[max_d,max_r]', ha='right', va='top', color='white', fontsize=8,
                 bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    
    plt.colorbar(im, ax=ax_main, label='log10(magnitude)')
    
    # Range profile (top)
    ax_range = fig.add_subplot(gs[0:2, 2])
    range_profile = frame.mean(axis=0)
    ax_range.plot(range_profile, range(n_range), 'b-')
    ax_range.set_xlabel('Power')
    ax_range.set_ylabel('Range Bin')
    ax_range.set_title('Range Profile\n(avg across Doppler)')
    ax_range.grid(True, alpha=0.3)
    ax_range.set_ylim(0, n_range-1)
    
    # Doppler profile (bottom)
    ax_doppler = fig.add_subplot(gs[2, 0:2])
    doppler_profile = frame.mean(axis=1)
    ax_doppler.plot(range(n_doppler), doppler_profile, 'g-')
    ax_doppler.axvline(n_doppler//2, color='r', linestyle='--', alpha=0.5, label='DC')
    ax_doppler.set_xlabel('Doppler Bin')
    ax_doppler.set_ylabel('Power')
    ax_doppler.set_title('Doppler Profile (avg across Range)')
    ax_doppler.legend()
    ax_doppler.grid(True, alpha=0.3)
    
    # Info panel
    ax_info = fig.add_subplot(gs[2, 2])
    ax_info.axis('off')
    
    info_text = [
        f"Frame Shape: {frame.shape}",
        f"Aspect Ratio: {n_doppler/n_range:.1f}:1",
        f"Value Range: [{frame.min():.2f}, {frame.max():.2f}]",
        f"Mean: {frame.mean():.2f}",
        f"Std: {frame.std():.4f}",
    ]
    
    if 'config' in meta:
        config = meta['config']
        info_text.extend([
            "",
            f"Mode: {config.get('mode', 'unknown')}",
            f"Sample Rate: {config.get('sample_rate', 0)/1e6:.1f} MHz",
            f"Num Chirps: {config.get('num_chirps', 0)}",
            f"Chirp BW: {config.get('chirp_bw', 0)/1e6:.0f} MHz",
        ])
        if config.get('test_pattern'):
            info_text.append(f"Test Pattern: {config.get('test_pattern')}")
    
    ax_info.text(0.1, 0.9, '\n'.join(info_text), transform=ax_info.transAxes,
                 fontsize=9, verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Reference plot saved to: {output_path}")


def validate_frame(npy_path: str, generate_plot: bool = True) -> Dict:
    """Run full validation on a frame."""
    print("=" * 60)
    print(f"Validating: {npy_path}")
    print("=" * 60)
    
    frame, meta = load_frame_with_meta(npy_path)
    
    print(f"\nFrame shape: {frame.shape} (n_doppler x n_range)")
    print(f"Value range: [{frame.min():.2f}, {frame.max():.2f}]")
    
    all_results = []
    
    # Structure checks
    print("\n--- Structure Validation ---")
    structure_results = analyze_frame_structure(frame, meta)
    all_results.extend(structure_results)
    for r in structure_results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {status}: {r.name}: {r.message}")
    
    # Coordinate mapping
    print("\n--- Coordinate Mapping ---")
    coord_results = analyze_coordinate_mapping(frame, meta)
    all_results.extend(coord_results)
    for r in coord_results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {status}: {r.name}: {r.message}")
    
    # Target analysis
    print("\n--- Target Analysis ---")
    target_results = analyze_for_targets(frame, meta)
    all_results.extend(target_results)
    for r in target_results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {status}: {r.name}: {r.message}")
    
    # Summary
    passed = sum(1 for r in all_results if r.passed)
    total = len(all_results)
    print(f"\n--- Summary: {passed}/{total} checks passed ---")
    
    # Generate reference plot
    if generate_plot:
        plot_path = npy_path.replace('.npy', '_reference.png')
        generate_reference_plot(frame, meta, plot_path)
    
    return {
        'file': npy_path,
        'shape': frame.shape,
        'results': [{'name': r.name, 'passed': r.passed, 'message': r.message, 'details': r.details} 
                    for r in all_results],
        'passed': passed,
        'total': total,
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate radar frame data")
    parser.add_argument('--validate', type=str, help="Path to .npy frame file to validate")
    parser.add_argument('--analyze-export', type=str, help="Analyze export directory")
    parser.add_argument('--no-plot', action='store_true', help="Skip generating matplotlib plots")
    parser.add_argument('--capture', action='store_true', help="Capture new frames from hardware")
    parser.add_argument('--frames', type=int, default=5, help="Number of frames to capture")
    parser.add_argument('--export', type=str, default='./validation_capture', help="Export directory")
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1', help="SDR URI")
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184', help="Phaser URI")
    
    args = parser.parse_args()
    
    if args.validate:
        validate_frame(args.validate, generate_plot=not args.no_plot)
    
    elif args.analyze_export:
        # Find all .npy files in directory
        export_dir = args.analyze_export
        if os.path.isfile(export_dir) and export_dir.endswith('.npy'):
            # Single file
            validate_frame(export_dir, generate_plot=not args.no_plot)
        elif os.path.isdir(export_dir):
            npy_files = sorted([f for f in os.listdir(export_dir) if f.endswith('.npy') and not f.endswith('_raw.npy')])
            print(f"Found {len(npy_files)} frames in {export_dir}")
            for npy_file in npy_files[:3]:  # Validate first 3
                validate_frame(os.path.join(export_dir, npy_file), generate_plot=not args.no_plot)
        else:
            print(f"Invalid path: {export_dir}")
            sys.exit(1)
    
    elif args.capture:
        from radar_backend import create_backend
        
        print(f"Capturing {args.frames} frames from hardware...")
        print(f"SDR URI: {args.sdr_uri}")
        print(f"Phaser URI: {args.phaser_uri}")
        
        os.makedirs(args.export, exist_ok=True)
        
        backend = create_backend(
            mode='hardware',
            sdr_uri=args.sdr_uri,
            phaser_uri=args.phaser_uri,
        )
        
        for i in range(args.frames):
            frame = backend.get_frame()
            export_path = backend.export_frame(args.export)
            print(f"  Frame {i+1}/{args.frames}: {export_path}")
        
        print(f"\nFrames saved to: {args.export}")
        print("Run validation with: python validate_hardware.py --analyze-export " + args.export)
    
    else:
        # Default: check exports directory
        export_dir = Path(__file__).parent.parent / 'exports'
        if export_dir.exists():
            npy_files = sorted(export_dir.glob('*.npy'))
            if npy_files:
                print(f"Found {len(npy_files)} exported frames in {export_dir}")
                print("Validating most recent...")
                validate_frame(str(npy_files[-1]), generate_plot=not args.no_plot)
            else:
                print(f"No .npy files found in {export_dir}")
                print("Use --validate <file.npy> to validate a specific file")
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
