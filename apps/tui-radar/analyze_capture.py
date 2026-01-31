#!/usr/bin/env python3
"""Analyze captured radar frames to diagnose issues."""

import numpy as np
import json
import os
import sys

def analyze_capture(capture_dir):
    """Analyze a capture directory."""
    
    # Load config
    with open(os.path.join(capture_dir, "config.json")) as f:
        config = json.load(f)
    
    print("=" * 60)
    print(f"Capture Analysis: {os.path.basename(capture_dir)}")
    print("=" * 60)
    print(f"\nConfig:")
    for k, v in config.items():
        print(f"  {k}: {v}")
    
    # Load all frames
    frame_files = sorted([f for f in os.listdir(capture_dir) if f.startswith("frame_") and f.endswith(".npy")])
    print(f"\nFound {len(frame_files)} frames")
    
    frames = []
    for ff in frame_files:
        frame = np.load(os.path.join(capture_dir, ff))
        frames.append(frame)
    
    frames = np.array(frames)
    print(f"Frames shape: {frames.shape} (n_frames, n_doppler, n_range)")
    
    # Overall statistics
    print(f"\n--- Overall Statistics ---")
    print(f"Global min: {frames.min():.2f} dB")
    print(f"Global max: {frames.max():.2f} dB")
    print(f"Global mean: {frames.mean():.2f} dB")
    print(f"Global std: {frames.std():.4f} dB")
    print(f"Dynamic range: {frames.max() - frames.min():.2f} dB")
    
    # Check for variation
    print(f"\n--- Frame-to-Frame Variation ---")
    frame_means = frames.mean(axis=(1, 2))
    print(f"Mean across frames varies from {frame_means.min():.3f} to {frame_means.max():.3f} dB")
    print(f"Std of frame means: {frame_means.std():.4f} dB")
    
    # Check if frames are identical
    if len(frames) > 1:
        diff_01 = np.abs(frames[0] - frames[1]).max()
        diff_first_last = np.abs(frames[0] - frames[-1]).max()
        print(f"Max diff between frame 0 and 1: {diff_01:.4f} dB")
        print(f"Max diff between first and last frame: {diff_first_last:.4f} dB")
    
    # Analyze spatial structure
    print(f"\n--- Spatial Structure (Frame 0) ---")
    f0 = frames[0]
    
    # Range profile (average across Doppler)
    range_profile = f0.mean(axis=0)
    print(f"Range profile: min={range_profile.min():.2f}, max={range_profile.max():.2f}, std={range_profile.std():.4f}")
    
    # Doppler profile (average across Range)  
    doppler_profile = f0.mean(axis=1)
    print(f"Doppler profile: min={doppler_profile.min():.2f}, max={doppler_profile.max():.2f}, std={doppler_profile.std():.4f}")
    
    # Check for DC component (center Doppler bin)
    center_doppler = config["n_doppler"] // 2
    dc_level = f0[center_doppler, :].mean()
    off_dc_level = np.concatenate([f0[:center_doppler-10, :], f0[center_doppler+10:, :]]).mean()
    print(f"DC bin (center) mean: {dc_level:.2f} dB")
    print(f"Off-DC mean: {off_dc_level:.2f} dB")
    print(f"DC prominence: {dc_level - off_dc_level:.2f} dB")
    
    # Check for any peaks
    print(f"\n--- Peak Detection ---")
    threshold = f0.mean() + 3 * f0.std()
    peaks = f0 > threshold
    n_peaks = peaks.sum()
    print(f"Threshold (mean + 3*std): {threshold:.2f} dB")
    print(f"Pixels above threshold: {n_peaks} ({100*n_peaks/f0.size:.2f}%)")
    
    if n_peaks > 0 and n_peaks < 1000:
        peak_locations = np.argwhere(peaks)
        print(f"Peak locations (doppler, range):")
        for loc in peak_locations[:10]:
            print(f"  ({loc[0]}, {loc[1]}): {f0[loc[0], loc[1]]:.2f} dB")
    
    # Diagnosis
    print(f"\n--- DIAGNOSIS ---")
    issues = []
    
    if (frames.max() - frames.min()) < 20:
        issues.append("CRITICAL: Dynamic range < 20 dB - data may not be processed correctly or signal is saturated/clipped")
    
    if frames.max() == 0.0:
        issues.append("WARNING: Max is exactly 0.0 dB - suggests normalization to max, which is losing absolute power info")
    
    if frame_means.std() < 0.5:
        issues.append("WARNING: Frames are nearly identical - no temporal variation detected")
    
    if range_profile.std() < 1.0:
        issues.append("WARNING: Range profile is flat - no range structure visible")
    
    if doppler_profile.std() < 1.0:
        issues.append("WARNING: Doppler profile is flat - no Doppler structure visible")
    
    if abs(dc_level - off_dc_level) < 3:
        issues.append("INFO: No prominent DC component - MTI filtering may be active or signal is very weak")
    
    if issues:
        for issue in issues:
            print(f"  * {issue}")
    else:
        print("  Data looks reasonable!")
    
    # Try to create visualization if matplotlib available
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Frame 0 heatmap
        im = axes[0, 0].imshow(f0, aspect='auto', cmap='inferno', origin='lower')
        axes[0, 0].set_title('Frame 0 - Range-Doppler Map')
        axes[0, 0].set_xlabel('Range Bin')
        axes[0, 0].set_ylabel('Doppler Bin')
        plt.colorbar(im, ax=axes[0, 0], label='dB')
        
        # Last frame heatmap
        im = axes[0, 1].imshow(frames[-1], aspect='auto', cmap='inferno', origin='lower')
        axes[0, 1].set_title(f'Frame {len(frames)-1} - Range-Doppler Map')
        axes[0, 1].set_xlabel('Range Bin')
        axes[0, 1].set_ylabel('Doppler Bin')
        plt.colorbar(im, ax=axes[0, 1], label='dB')
        
        # Difference
        diff = frames[-1] - frames[0]
        im = axes[0, 2].imshow(diff, aspect='auto', cmap='RdBu', origin='lower', 
                               vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
        axes[0, 2].set_title('Difference (Last - First)')
        axes[0, 2].set_xlabel('Range Bin')
        axes[0, 2].set_ylabel('Doppler Bin')
        plt.colorbar(im, ax=axes[0, 2], label='dB diff')
        
        # Range profile
        axes[1, 0].plot(range_profile)
        axes[1, 0].set_title('Range Profile (avg across Doppler)')
        axes[1, 0].set_xlabel('Range Bin')
        axes[1, 0].set_ylabel('Power (dB)')
        axes[1, 0].grid(True)
        
        # Doppler profile
        axes[1, 1].plot(doppler_profile)
        axes[1, 1].set_title('Doppler Profile (avg across Range)')
        axes[1, 1].set_xlabel('Doppler Bin')
        axes[1, 1].set_ylabel('Power (dB)')
        axes[1, 1].axvline(center_doppler, color='r', linestyle='--', label='DC')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        # Frame means over time
        axes[1, 2].plot(frame_means, 'o-')
        axes[1, 2].set_title('Frame Mean Over Time')
        axes[1, 2].set_xlabel('Frame Index')
        axes[1, 2].set_ylabel('Mean Power (dB)')
        axes[1, 2].grid(True)
        
        plt.tight_layout()
        output_path = os.path.join(capture_dir, "analysis.png")
        plt.savefig(output_path, dpi=150)
        print(f"\nVisualization saved to: {output_path}")
        
    except ImportError:
        print("\nMatplotlib not available - skipping visualization")
    
    return frames, config

if __name__ == "__main__":
    if len(sys.argv) > 1:
        capture_dir = sys.argv[1]
    else:
        # Find most recent capture
        captures_dir = os.path.dirname(os.path.abspath(__file__)) + "/captures"
        if os.path.exists(captures_dir):
            subdirs = [d for d in os.listdir(captures_dir) if d.startswith("capture_")]
            if subdirs:
                capture_dir = os.path.join(captures_dir, sorted(subdirs)[-1])
            else:
                print("No captures found")
                sys.exit(1)
        else:
            print(f"Captures directory not found: {captures_dir}")
            sys.exit(1)
    
    analyze_capture(capture_dir)
