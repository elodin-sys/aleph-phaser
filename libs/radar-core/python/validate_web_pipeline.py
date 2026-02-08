#!/usr/bin/env python3
"""
Web pipeline diagnostic: analyze exported full-resolution radar frames.

Exported frames from radar-web are already positive-range-only (0 m at left edge,
~27 m at right edge). This script:
  1. Loads the frame and metadata
  2. Reconstructs the physical range axis from radar config
  3. Shows range/Doppler profiles with expected target positions
  4. Simulates u8 quantization to check if the target survives
  5. Generates comparison plots (hardware frame vs synthetic patterns)

Usage:
    python validate_web_pipeline.py exports/frame_20260208_001707.npy
    python validate_web_pipeline.py exports/frame_20260208_001707.npy -o exports/pipeline_diag
    python validate_web_pipeline.py exports/frame_20260208_001707.npy --target-range 1.0
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

# Add parent for radar_backend and validate_hardware
sys.path.insert(0, str(Path(__file__).parent))


def compute_positive_range_axis(config: dict, n_range_positive: int) -> np.ndarray:
    """Compute the physical range axis (meters) for a positive-range-only frame.

    The frame starts at 0 m (range_start_idx in the original fftshift'd FFT)
    and extends to ~max_unambiguous_range.  We reconstruct the axis from the
    radar config the same way radar_backend.py does, then return only the
    positive portion matching the frame width.
    """
    sample_rate = config.get("sample_rate", 4_000_000)
    chirp_bw = config.get("chirp_bw", 500_000_000)
    ramp_time_us = config.get("ramp_time_us", 500)
    signal_freq = config.get("signal_freq", 100_000)

    ramp_time_s = ramp_time_us / 1e6
    begin_offset_time = 0.1 * ramp_time_s
    good_ramp_samples = int((ramp_time_s - begin_offset_time) * sample_rate)

    c = 3e8
    slope = chirp_bw / ramp_time_s
    freq_axis = np.fft.fftshift(np.fft.fftfreq(good_ramp_samples, 1 / sample_rate))
    full_range_axis = (freq_axis - signal_freq) * c / (2 * slope)

    range_start_idx = int(np.argmin(np.abs(full_range_axis - 0)))
    positive_range_axis = full_range_axis[range_start_idx:]

    # The frame may have fewer bins than the computed axis (e.g. num_chirps
    # changed but range bins stayed the same).  Truncate or pad to match.
    if len(positive_range_axis) >= n_range_positive:
        positive_range_axis = positive_range_axis[:n_range_positive]
    else:
        # Extend with linear extrapolation
        dr = positive_range_axis[-1] - positive_range_axis[-2] if len(positive_range_axis) > 1 else 1.0
        extra = np.arange(1, n_range_positive - len(positive_range_axis) + 1) * dr + positive_range_axis[-1]
        positive_range_axis = np.concatenate([positive_range_axis, extra])

    return positive_range_axis


def load_frame_with_meta(npy_path: str) -> tuple:
    """Load frame and metadata."""
    frame = np.load(npy_path)
    meta = {
        "shape": list(frame.shape),
        "dtype": str(frame.dtype),
        "min": float(frame.min()),
        "max": float(frame.max()),
    }
    meta_path = npy_path.replace(".npy", "_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta.update(json.load(f))
    parent_dir = os.path.dirname(npy_path)
    config_path = os.path.join(parent_dir, "config.json")
    if os.path.exists(config_path) and "config" not in meta:
        with open(config_path) as f:
            meta["config"] = json.load(f)
    return frame, meta


def simulate_u8_quantization(frame: np.ndarray, scale_min: float = 0.0, scale_max: float = 8.0) -> np.ndarray:
    """Quantize float log10 frame to u8 (matches radar-core frame.rs to_u8())."""
    scale = 255.0 / (scale_max - scale_min)
    return ((frame - scale_min) * scale).clip(0, 255).astype(np.uint8)


def bin_for_meters(range_axis: np.ndarray, meters: float) -> int:
    """Return bin index closest to a given range in meters."""
    return int(np.argmin(np.abs(range_axis - meters)))


def run_diagnostic(
    npy_path: str,
    output_dir: str | None = None,
    skip_plots: bool = False,
    target_range_m: float = 1.0,
) -> dict:
    """Run full pipeline diagnostic on an exported positive-range-only frame."""
    frame, meta = load_frame_with_meta(npy_path)
    n_doppler, n_range = frame.shape
    config = meta.get("config", {})
    scale_min = config.get("min_scale", 0.0)
    scale_max = config.get("max_scale", 8.0)

    # Reconstruct physical range axis (0 m at bin 0)
    range_axis = compute_positive_range_axis(config, n_range)
    max_range_m = float(range_axis[-1]) if len(range_axis) > 0 else 0.0

    # Range profile (mean across Doppler)
    range_profile = frame.mean(axis=0)
    peak_bin = int(np.argmax(range_profile))
    peak_range_m = float(range_axis[peak_bin]) if peak_bin < len(range_axis) else float("nan")

    # Doppler profile (mean across Range)
    doppler_profile = frame.mean(axis=1)
    dc_bin = n_doppler // 2
    dc_power = float(doppler_profile[dc_bin])

    # Expected bins for target and a reference distance
    bin_target = bin_for_meters(range_axis, target_range_m)
    bin_3m = bin_for_meters(range_axis, 3.0)

    # Simulate u8 quantization
    u8_frame = simulate_u8_quantization(frame, scale_min, scale_max)
    margin = max(5, n_range // 100)
    region_target = u8_frame[:, max(0, bin_target - margin) : min(n_range, bin_target + margin)]
    target_region_max_u8 = int(region_target.max()) if region_target.size else 0
    global_max_u8 = int(u8_frame.max())

    # Value at the expected target bin (raw float)
    target_col = frame[:, bin_target] if bin_target < n_range else np.zeros(n_doppler)
    target_peak_val = float(target_col.max())
    target_peak_doppler = int(np.argmax(target_col))

    out = {
        "npy_path": npy_path,
        "shape": (n_doppler, n_range),
        "max_range_m": max_range_m,
        "peak_bin": peak_bin,
        "peak_range_m": peak_range_m,
        "target_range_m": target_range_m,
        "bin_for_target": bin_target,
        "bin_for_3m": bin_3m,
        "target_peak_val": target_peak_val,
        "target_peak_doppler_bin": target_peak_doppler,
        "target_region_max_u8": target_region_max_u8,
        "global_max_u8": global_max_u8,
        "dc_power": dc_power,
        "value_range": [float(frame.min()), float(frame.max())],
    }

    sep = "=" * 60
    print(sep)
    print("Web pipeline diagnostic:", npy_path)
    print(sep)
    print(f"Frame shape:        {frame.shape} (n_doppler x n_range)")
    print(f"Range axis:         0 m at left, {max_range_m:.1f} m at right")
    print(f"Value range:        [{frame.min():.2f}, {frame.max():.2f}]  (log10 scale, expected [0, 8])")
    print(f"Range profile peak: bin {peak_bin} = {peak_range_m:.2f} m  (mean across Doppler)")
    print(f"DC Doppler power:   {dc_power:.2f} at bin {dc_bin}")
    print()
    print(f"Target expected at: {target_range_m:.1f} m -> bin {bin_target}")
    print(f"  Peak value at target column: {target_peak_val:.2f} (Doppler bin {target_peak_doppler})")
    print(f"  U8 in target region (+/-{margin} bins): max {target_region_max_u8}  (global max {global_max_u8})")
    print(f"Reference 3.0 m -> bin {bin_3m}")
    print(sep)

    if skip_plots or output_dir is None:
        return out

    try:
        import matplotlib
        matplotlib.use("Agg")  # headless
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available - skipping plots")
        return out

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.basename(npy_path).replace(".npy", "")

    # --- Plot 1: Range-Doppler heatmap with target annotation ---
    fig1, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(
        frame,
        aspect="auto",
        cmap="inferno",
        origin="lower",
        vmin=scale_min,
        vmax=scale_max,
        extent=[0, max_range_m, 0, n_doppler],
    )
    ax.axvline(target_range_m, color="cyan", linewidth=1, linestyle="--", label=f"Target ({target_range_m:.1f} m)")
    ax.axhline(dc_bin, color="lime", linewidth=0.5, linestyle=":", alpha=0.5, label="Zero Doppler")
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Doppler Bin")
    ax.set_title("Exported frame (positive-range-only, 0 m at left)")
    ax.legend(loc="upper right", fontsize=8)
    plt.colorbar(im, ax=ax, label="log10(magnitude)")
    plt.tight_layout()
    fig1.savefig(os.path.join(output_dir, f"{base}_heatmap.png"), dpi=150, bbox_inches="tight")
    plt.close(fig1)
    print(f"Saved {output_dir}/{base}_heatmap.png")

    # --- Plot 2: Range and Doppler profiles ---
    fig2, axes = plt.subplots(2, 1, figsize=(10, 6))
    ax = axes[0]
    ax.plot(range_axis, range_profile, "b-")
    ax.axvline(target_range_m, color="orange", linestyle="--", label=f"Target ({target_range_m:.1f} m)")
    ax.axvline(3.0, color="red", linestyle="--", alpha=0.5, label="3 m ref")
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Mean power (log10)")
    ax.set_title("Range profile (averaged across Doppler)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(np.arange(n_doppler), doppler_profile, "g-")
    ax.axvline(dc_bin, color="red", linestyle="--", alpha=0.5, label="Zero Doppler")
    ax.set_xlabel("Doppler Bin")
    ax.set_ylabel("Mean power (log10)")
    ax.set_title("Doppler profile (averaged across Range)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig2.savefig(os.path.join(output_dir, f"{base}_profiles.png"), dpi=150, bbox_inches="tight")
    plt.close(fig2)
    print(f"Saved {output_dir}/{base}_profiles.png")

    # --- Plot 3: Synthetic hb100_stationary for comparison ---
    try:
        from radar_backend import create_backend

        backend = create_backend(mode="synthetic")
        backend.set_test_pattern("hb100_stationary")
        syn = backend.get_frame_full_resolution()

        fig3, axes = plt.subplots(1, 2, figsize=(14, 5))
        for ax_i, (data, title) in enumerate([
            (frame, "Hardware (exported)"),
            (syn, "Synthetic hb100_stationary"),
        ]):
            ax = axes[ax_i]
            im = ax.imshow(
                data, aspect="auto", cmap="inferno", origin="lower",
                vmin=scale_min, vmax=scale_max,
            )
            ax.set_xlabel("Range Bin")
            ax.set_ylabel("Doppler Bin")
            ax.set_title(title)
            plt.colorbar(im, ax=ax, label="log10")
        plt.tight_layout()
        fig3.savefig(os.path.join(output_dir, f"{base}_hw_vs_syn.png"), dpi=150, bbox_inches="tight")
        plt.close(fig3)
        print(f"Saved {output_dir}/{base}_hw_vs_syn.png")
    except Exception as e:
        print(f"Skipping synthetic comparison plot: {e}")

    return out


def main():
    parser = argparse.ArgumentParser(description="Validate web pipeline on exported radar frame")
    parser.add_argument("npy_path", help="Path to exported .npy frame")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory for diagnostic plots")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating plots")
    parser.add_argument(
        "--target-range", type=float, default=1.0,
        help="Expected target distance in meters (default: 1.0 for HB100 at 1 m)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.npy_path):
        print(f"File not found: {args.npy_path}")
        sys.exit(1)

    run_diagnostic(
        args.npy_path,
        output_dir=args.output_dir or os.path.dirname(args.npy_path) or ".",
        skip_plots=args.no_plot,
        target_range_m=args.target_range,
    )


if __name__ == "__main__":
    main()
