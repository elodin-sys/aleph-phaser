#!/usr/bin/env python3
"""
Test Pattern Validation Script

This script validates the test pattern generation in radar_backend.py.
Each test pattern is generated and checked against expected values at
known positions to verify the coordinate system and rendering pipeline.

Usage:
    python test_patterns.py [--verbose] [--export DIR]

Exit codes:
    0 = All tests passed
    1 = One or more tests failed
"""

import argparse
import sys
import os
import numpy as np
from typing import Tuple, List, Dict

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from radar_backend import RadarBackend, create_backend


class TestResult:
    """Container for test results."""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        if self.message:
            return f"[{status}] {self.name}: {self.message}"
        return f"[{status}] {self.name}"


def create_test_backend() -> RadarBackend:
    """Create a test backend with known dimensions."""
    return create_backend(
        mode='synthetic',
        sample_rate=4_000_000,
        num_chirps=64,  # Smaller for faster tests
        ramp_time_us=500,
        chirp_bw=500_000_000,
        max_range=10.0,
    )


def test_corner_dots(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test corner_dots pattern.
    
    Expected behavior:
    - rd_map[0, 0] (bottom-left) = max_scale (brightest)
    - rd_map[0, -1] (bottom-right) = 0.75 * max_scale
    - rd_map[-1, 0] (top-left) = 0.5 * max_scale
    - rd_map[-1, -1] (top-right) = 0.25 * max_scale (dimmest)
    """
    backend.set_test_pattern('corner_dots')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    min_scale = backend.min_scale
    max_scale = backend.max_scale
    
    # Check corners (with some tolerance for the Gaussian falloff)
    tolerance = (max_scale - min_scale) * 0.15
    
    # Bottom-left should be brightest
    bl_val = frame[0, 0]
    bl_expected = max_scale
    
    # Bottom-right
    br_val = frame[0, n_range-1]
    br_expected = min_scale + 0.75 * (max_scale - min_scale)
    
    # Top-left
    tl_val = frame[n_doppler-1, 0]
    tl_expected = min_scale + 0.5 * (max_scale - min_scale)
    
    # Top-right should be dimmest
    tr_val = frame[n_doppler-1, n_range-1]
    tr_expected = min_scale + 0.25 * (max_scale - min_scale)
    
    # Verify ordering (BL > BR > TL > TR in brightness)
    ordering_ok = bl_val > br_val > tl_val > tr_val
    
    # Verify approximate values
    bl_ok = abs(bl_val - bl_expected) < tolerance
    br_ok = abs(br_val - br_expected) < tolerance
    tl_ok = abs(tl_val - tl_expected) < tolerance
    tr_ok = abs(tr_val - tr_expected) < tolerance
    
    passed = ordering_ok and bl_ok and br_ok and tl_ok and tr_ok
    
    if verbose or not passed:
        msg = (f"BL={bl_val:.2f}(exp {bl_expected:.2f}), "
               f"BR={br_val:.2f}(exp {br_expected:.2f}), "
               f"TL={tl_val:.2f}(exp {tl_expected:.2f}), "
               f"TR={tr_val:.2f}(exp {tr_expected:.2f}), "
               f"ordering={'OK' if ordering_ok else 'FAIL'}")
    else:
        msg = "Corner intensities in correct order"
    
    return TestResult('corner_dots', passed, msg)


def test_gradient_h(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test horizontal gradient pattern.
    
    Expected: Values increase from left (r=0) to right (r=n_range-1)
    All rows should have identical values (constant across Doppler).
    """
    backend.set_test_pattern('gradient_h')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    min_scale = backend.min_scale
    max_scale = backend.max_scale
    
    # Check that left edge is near min, right edge is near max
    left_val = frame[n_doppler//2, 0]
    right_val = frame[n_doppler//2, n_range-1]
    
    tolerance = (max_scale - min_scale) * 0.05
    left_ok = abs(left_val - min_scale) < tolerance
    right_ok = abs(right_val - max_scale) < tolerance
    
    # Check that all rows are the same (horizontal gradient is constant in Doppler)
    row_variance = np.var(frame, axis=0).mean()  # Variance across Doppler for each Range
    rows_same = row_variance < 0.01
    
    # Check monotonic increase along Range axis
    mid_row = frame[n_doppler//2, :]
    diffs = np.diff(mid_row)
    monotonic = np.all(diffs >= -tolerance)
    
    passed = left_ok and right_ok and rows_same and monotonic
    
    if verbose or not passed:
        msg = (f"left={left_val:.2f}(exp {min_scale:.2f}), "
               f"right={right_val:.2f}(exp {max_scale:.2f}), "
               f"row_var={row_variance:.4f}, monotonic={monotonic}")
    else:
        msg = "Horizontal gradient correct (left to right increase)"
    
    return TestResult('gradient_h', passed, msg)


def test_gradient_v(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test vertical gradient pattern.
    
    Expected: Values increase from bottom (d=0) to top (d=n_doppler-1)
    All columns should have identical values (constant across Range).
    """
    backend.set_test_pattern('gradient_v')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    min_scale = backend.min_scale
    max_scale = backend.max_scale
    
    # Check that bottom edge is near min, top edge is near max
    bottom_val = frame[0, n_range//2]
    top_val = frame[n_doppler-1, n_range//2]
    
    tolerance = (max_scale - min_scale) * 0.05
    bottom_ok = abs(bottom_val - min_scale) < tolerance
    top_ok = abs(top_val - max_scale) < tolerance
    
    # Check that all columns are the same (vertical gradient is constant in Range)
    col_variance = np.var(frame, axis=1).mean()  # Variance across Range for each Doppler
    cols_same = col_variance < 0.01
    
    # Check monotonic increase along Doppler axis
    mid_col = frame[:, n_range//2]
    diffs = np.diff(mid_col)
    monotonic = np.all(diffs >= -tolerance)
    
    passed = bottom_ok and top_ok and cols_same and monotonic
    
    if verbose or not passed:
        msg = (f"bottom={bottom_val:.2f}(exp {min_scale:.2f}), "
               f"top={top_val:.2f}(exp {max_scale:.2f}), "
               f"col_var={col_variance:.4f}, monotonic={monotonic}")
    else:
        msg = "Vertical gradient correct (bottom to top increase)"
    
    return TestResult('gradient_v', passed, msg)


def test_center_target(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test center target pattern.
    
    Expected: Peak value at center, decreasing outward (Gaussian).
    """
    backend.set_test_pattern('center_target')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    max_scale = backend.max_scale
    
    # Find the maximum value position
    max_idx = np.unravel_index(np.argmax(frame), frame.shape)
    max_val = frame[max_idx]
    
    # Expected center
    expected_center = (n_doppler // 2, n_range // 2)
    
    # Check if max is near center (within 5%)
    center_tolerance_d = max(1, n_doppler // 20)
    center_tolerance_r = max(1, n_range // 20)
    
    center_ok = (abs(max_idx[0] - expected_center[0]) <= center_tolerance_d and
                 abs(max_idx[1] - expected_center[1]) <= center_tolerance_r)
    
    # Check that max value is near max_scale
    tolerance = (max_scale - backend.min_scale) * 0.1
    max_val_ok = abs(max_val - max_scale) < tolerance
    
    # Check that corners are near minimum (background)
    corners = [frame[0, 0], frame[0, -1], frame[-1, 0], frame[-1, -1]]
    corners_low = all(c < (backend.min_scale + backend.max_scale) / 2 for c in corners)
    
    passed = center_ok and max_val_ok and corners_low
    
    if verbose or not passed:
        msg = (f"max at {max_idx} (exp ~{expected_center}), "
               f"max_val={max_val:.2f}(exp {max_scale:.2f}), "
               f"corners_low={corners_low}")
    else:
        msg = "Center target at expected position with correct intensity"
    
    return TestResult('center_target', passed, msg)


def test_grid(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test grid pattern.
    
    Expected: 5 grid lines in each direction with bright intersections.
    """
    backend.set_test_pattern('grid')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    min_scale = backend.min_scale
    max_scale = backend.max_scale
    
    # Grid uses 5 lines in each direction (matching radar_backend.py)
    n_lines = 5
    grid_spacing_r = max(1, n_range // n_lines)
    grid_spacing_d = max(1, n_doppler // n_lines)
    
    # Check if the first grid line position is brighter than background
    grid_r = grid_spacing_r
    
    # Find a position that should be on a line vs off a line
    line_val = frame[n_doppler // 2, 0]  # r=0 is always on a vertical line
    
    # Find a position between lines (if possible)
    between_r = grid_spacing_r // 2
    if between_r > 0 and between_r < n_range:
        bg_val = frame[n_doppler // 4, between_r]  # Should be between horizontal lines too
        lines_visible = line_val > bg_val + 0.5  # Line should be noticeably brighter
    else:
        # With very few bins, just check that corners are bright (they're at intersections)
        lines_visible = frame[0, 0] > (min_scale + max_scale) / 2
    
    # Check if intersections (like [0,0]) are bright
    intersection_val = frame[0, 0]
    intersection_bright = intersection_val >= max_scale * 0.9
    
    passed = lines_visible and intersection_bright
    
    if verbose or not passed:
        msg = f"lines_visible={lines_visible}, intersection_bright={intersection_bright}, corner_val={intersection_val:.1f}"
    else:
        msg = "Grid lines and intersections visible"
    
    return TestResult('grid', passed, msg)


def test_diagonal(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test diagonal pattern.
    
    Expected: Bright line from bottom-left (0,0) to top-right (max,max).
    """
    backend.set_test_pattern('diagonal')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    max_scale = backend.max_scale
    
    # Sample points along the diagonal
    diag_points = []
    off_diag_points = []
    
    for i in range(min(n_doppler, n_range)):
        d = int(i * (n_doppler - 1) / max(n_doppler, n_range))
        r = int(i * (n_range - 1) / max(n_doppler, n_range))
        if d < n_doppler and r < n_range:
            diag_points.append(frame[d, r])
    
    # Sample some off-diagonal points
    if n_range > 10 and n_doppler > 10:
        off_diag_points.append(frame[n_doppler // 2, 0])  # Mid-left
        off_diag_points.append(frame[0, n_range // 2])    # Bottom-mid
    
    # Diagonal should be bright
    diag_mean = np.mean(diag_points)
    diag_bright = diag_mean > max_scale * 0.7
    
    # Off-diagonal should be darker
    if off_diag_points:
        off_diag_mean = np.mean(off_diag_points)
        off_diag_dark = off_diag_mean < diag_mean
    else:
        off_diag_dark = True
    
    passed = diag_bright and off_diag_dark
    
    if verbose or not passed:
        msg = f"diag_mean={diag_mean:.2f}, off_diag_mean={np.mean(off_diag_points) if off_diag_points else 0:.2f}"
    else:
        msg = "Diagonal line from BL to TR visible"
    
    return TestResult('diagonal', passed, msg)


def test_checkerboard(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test checkerboard pattern.
    
    Expected: Alternating bright and dark cells in 4x4 pattern.
    """
    backend.set_test_pattern('checkerboard')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    min_scale = backend.min_scale
    max_scale = backend.max_scale
    mid_scale = (min_scale + max_scale) / 2
    
    # Pattern uses 4x4 cells (matching radar_backend.py)
    cells_r = 4
    cells_d = 4
    cell_width = max(1, n_range // cells_r)
    cell_height = max(1, n_doppler // cells_d)
    
    # Sample center of a few cells
    correct_cells = 0
    total_cells = 0
    
    for cell_d in range(cells_d):
        for cell_r in range(cells_r):
            # Center of this cell
            d = cell_d * cell_height + cell_height // 2
            r = cell_r * cell_width + cell_width // 2
            
            if d < n_doppler and r < n_range:
                val = frame[d, r]
                expected_bright = (cell_r + cell_d) % 2 == 0
                
                if expected_bright:
                    if val > mid_scale:
                        correct_cells += 1
                else:
                    if val < mid_scale:
                        correct_cells += 1
                
                total_cells += 1
    
    accuracy = correct_cells / total_cells if total_cells > 0 else 0
    passed = accuracy > 0.9
    
    if verbose or not passed:
        msg = f"accuracy={accuracy:.1%} ({correct_cells}/{total_cells} cells correct)"
    else:
        msg = f"Checkerboard pattern {accuracy:.0%} accurate"
    
    return TestResult('checkerboard', passed, msg)


def test_animated(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test animated pattern.
    
    Expected: Multiple frames should show some variation (targets moving).
    """
    backend.set_test_pattern('animated')
    
    # Get two frames
    frame1 = backend.get_frame().copy()
    frame2 = backend.get_frame().copy()
    
    # Frames should be different (animation)
    diff = np.abs(frame1 - frame2).mean()
    frames_different = diff > 0.01
    
    # Should have some structure (not just noise)
    frame_std = frame1.std()
    has_structure = frame_std > 0.1
    
    passed = frames_different and has_structure
    
    if verbose or not passed:
        msg = f"frame_diff={diff:.4f}, frame_std={frame_std:.2f}"
    else:
        msg = "Animated frames show variation"
    
    return TestResult('animated', passed, msg)


def test_hb100_stationary(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test HB100 stationary pattern.
    
    Expected: Target at center Doppler (zero velocity), ~3m range.
    """
    backend.set_test_pattern('hb100_stationary')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    max_idx = np.unravel_index(frame.argmax(), frame.shape)
    max_val = frame[max_idx]
    
    # Target should be at center Doppler (zero velocity)
    center_d = n_doppler // 2
    doppler_offset = abs(max_idx[0] - center_d)
    at_zero_doppler = doppler_offset < n_doppler // 10  # Within 10% of center
    
    # Target should be around 30% of range (3m with 10m max)
    expected_r = int(0.3 * n_range)
    range_offset = abs(max_idx[1] - expected_r)
    at_expected_range = range_offset < n_range // 4  # Within 25% tolerance
    
    # Max should be near the scale max
    bright_enough = max_val > (backend.min_scale + backend.max_scale) / 2
    
    passed = at_zero_doppler and at_expected_range and bright_enough
    
    range_m = (max_idx[1] / n_range) * 10.0  # Assuming max_range=10m
    
    if verbose or not passed:
        msg = f"target at d={max_idx[0]} (center={center_d}), r={max_idx[1]} (~{range_m:.1f}m), val={max_val:.1f}"
    else:
        msg = f"HB100 stationary at {range_m:.1f}m, zero Doppler"
    
    return TestResult('hb100_stationary', passed, msg)


def test_hb100_walking(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test HB100 walking pattern.
    
    Expected: Target above center Doppler (approaching), ~4m range.
    """
    backend.set_test_pattern('hb100_walking')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    max_idx = np.unravel_index(frame.argmax(), frame.shape)
    max_val = frame[max_idx]
    
    # Target should be above center Doppler (positive = approaching)
    center_d = n_doppler // 2
    above_center = max_idx[0] > center_d
    
    # Target should be around 40% of range (4m with 10m max)
    expected_r = int(0.4 * n_range)
    range_offset = abs(max_idx[1] - expected_r)
    at_expected_range = range_offset < n_range // 3  # Within 33% tolerance
    
    # Max should be bright
    bright_enough = max_val > (backend.min_scale + backend.max_scale) / 2
    
    passed = above_center and at_expected_range and bright_enough
    
    range_m = (max_idx[1] / n_range) * 10.0
    doppler_offset = max_idx[0] - center_d
    
    if verbose or not passed:
        msg = f"target at d={max_idx[0]} (+{doppler_offset} from center), r={max_idx[1]} (~{range_m:.1f}m), val={max_val:.1f}"
    else:
        msg = f"HB100 walking at {range_m:.1f}m, +{doppler_offset} Doppler bins"
    
    return TestResult('hb100_walking', passed, msg)


def test_dc_leakage(backend: RadarBackend, verbose: bool = False) -> TestResult:
    """
    Test DC leakage pattern.
    
    Expected: Bright horizontal line at zero Doppler, max at zero range.
    """
    backend.set_test_pattern('dc_leakage')
    frame = backend.get_frame()
    
    n_doppler, n_range = frame.shape
    max_idx = np.unravel_index(frame.argmax(), frame.shape)
    max_val = frame[max_idx]
    
    # Max should be at center Doppler (DC line)
    center_d = n_doppler // 2
    at_dc = abs(max_idx[0] - center_d) < n_doppler // 20  # Within 5% of center
    
    # Max should be at or near zero range
    at_near_range = max_idx[1] < n_range // 4  # Within first 25%
    
    # Check that DC line exists (center row should be brighter than edges)
    dc_line_mean = frame[center_d, :].mean()
    edge_mean = (frame[0, :].mean() + frame[-1, :].mean()) / 2
    dc_prominent = dc_line_mean > edge_mean + 0.5
    
    passed = at_dc and at_near_range and dc_prominent
    
    if verbose or not passed:
        msg = f"max at d={max_idx[0]} (center={center_d}), r={max_idx[1]}, DC_mean={dc_line_mean:.1f}, edge_mean={edge_mean:.1f}"
    else:
        msg = f"DC leakage visible at center Doppler"
    
    return TestResult('dc_leakage', passed, msg)


def run_all_tests(verbose: bool = False, export_dir: str = None) -> List[TestResult]:
    """Run all test pattern tests."""
    print("Creating test backend...")
    backend = create_test_backend()
    
    config = backend.get_config()
    print(f"  n_doppler={config['n_doppler']}, n_range={config['n_range']}")
    print(f"  scale=[{config['min_scale']}, {config['max_scale']}]")
    print()
    
    tests = [
        ('corner_dots', test_corner_dots),
        ('gradient_h', test_gradient_h),
        ('gradient_v', test_gradient_v),
        ('center_target', test_center_target),
        ('grid', test_grid),
        ('diagonal', test_diagonal),
        ('checkerboard', test_checkerboard),
        ('animated', test_animated),
        ('hb100_stationary', test_hb100_stationary),
        ('hb100_walking', test_hb100_walking),
        ('dc_leakage', test_dc_leakage),
    ]
    
    results = []
    
    for pattern_name, test_func in tests:
        print(f"Testing '{pattern_name}'...", end=" ")
        result = test_func(backend, verbose)
        results.append(result)
        print(result)
        
        # Export frame if requested
        if export_dir:
            backend.set_test_pattern(pattern_name)
            frame = backend.get_frame()
            filepath = os.path.join(export_dir, f"{pattern_name}.npy")
            np.save(filepath, frame)
            if verbose:
                print(f"  Exported to {filepath}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Validate radar TUI test patterns"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed test output'
    )
    parser.add_argument(
        '--export',
        type=str,
        metavar='DIR',
        help='Export test pattern frames to directory as .npy files'
    )
    args = parser.parse_args()
    
    # Create export directory if needed
    if args.export:
        os.makedirs(args.export, exist_ok=True)
        print(f"Exporting frames to: {args.export}")
    
    print("=" * 60)
    print("Radar TUI Test Pattern Validation")
    print("=" * 60)
    print()
    
    results = run_all_tests(verbose=args.verbose, export_dir=args.export)
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print()
        print("Failed tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")
    
    print()
    
    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
