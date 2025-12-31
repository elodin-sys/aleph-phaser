#!/usr/bin/env python3
"""
CPU Demos Runner - Phaser Integration Tests

Runs all CPU-based demos for the Aleph-Phaser integration.
These demos require live hardware (PlutoSDR and Phaser).

Demos included:
1. SDR Basic Capture - PlutoSDR only, no Phaser required
2. Phaser Connection Test - Tests connectivity to both devices
3. Minimal Example - Basic spectrum capture with HB100
4. Beam Steering - Beam pattern measurement
5. Lab Exercises - Lab 3 (Array Factor) and Lab 4 (Tapering)
6. Benchmark - Performance measurements

Usage:
    # Run all demos
    python3 run_cpu_demos.py --output-dir /tmp/cpu_results
    
    # Run quick test (SDR capture + connection test only)
    python3 run_cpu_demos.py --quick --output-dir /tmp/cpu_results
    
    # Run specific demo
    python3 run_cpu_demos.py --demo minimal --output-dir /tmp/cpu_results

Author: Elodin (for Analog Devices Phaser Demo)
Date: December 2024
"""

import argparse
import os
import sys
import time
import subprocess
from datetime import datetime

# Set matplotlib backend before any imports
import matplotlib
matplotlib.use('Agg')


def print_header(text):
    """Print a formatted header."""
    width = 70
    print()
    print("=" * width)
    print(text.center(width))
    print("=" * width)
    print()


def print_section(text):
    """Print a section divider."""
    print()
    print("-" * 70)
    print(text)
    print("-" * 70)


def check_hardware_connectivity(sdr_uri, phaser_uri):
    """Quick check if hardware is reachable."""
    print_section("Checking Hardware Connectivity")
    
    results = {'sdr': False, 'phaser': False}
    
    # Check PlutoSDR
    print(f"Checking PlutoSDR at {sdr_uri}...")
    try:
        import adi
        sdr = adi.ad9361(uri=sdr_uri)
        print(f"  ✓ PlutoSDR connected (sample rate: {sdr.sample_rate/1e6:.1f} MSPS)")
        results['sdr'] = True
        del sdr
    except Exception as e:
        print(f"  ✗ PlutoSDR not accessible: {e}")
    
    # Check Phaser
    print(f"Checking Phaser at {phaser_uri}...")
    try:
        from adi.cn0566 import CN0566
        phaser = CN0566(uri=phaser_uri)
        print(f"  ✓ Phaser connected")
        results['phaser'] = True
        del phaser
    except Exception as e:
        print(f"  ✗ Phaser not accessible: {e}")
    
    return results


def run_demo_script(script_path, args_list, description, timeout=120):
    """Run a demo script and capture output."""
    print_section(f"Running: {description}")
    print(f"  Script: {script_path}")
    print(f"  Args: {' '.join(args_list)}")
    print()
    
    start_time = time.perf_counter()
    
    try:
        cmd = [sys.executable, script_path] + args_list
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            timeout=timeout
        )
        
        elapsed = time.perf_counter() - start_time
        
        if result.returncode == 0:
            print(f"\n  ✓ {description} completed in {elapsed:.1f}s")
            return True
        else:
            print(f"\n  ✗ {description} failed (exit code {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n  ✗ {description} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"\n  ✗ {description} error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run CPU-based Phaser demos')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1',
                        help='PlutoSDR URI (default: ip:192.168.2.1)')
    parser.add_argument('--phaser-uri', default='ip:192.168.4.184',
                        help='Phaser URI (default: ip:192.168.4.184)')
    parser.add_argument('--output-dir', default='/tmp/cpu_results',
                        help='Output directory for results')
    parser.add_argument('--quick', action='store_true',
                        help='Quick test (SDR capture only)')
    parser.add_argument('--demo', choices=['sdr', 'connection', 'minimal', 'beam', 'labs', 'benchmark', 'all'],
                        default='all', help='Which demo to run')
    parser.add_argument('--skip-hardware-check', action='store_true',
                        help='Skip initial hardware connectivity check')
    args = parser.parse_args()
    
    print_header("CPU DEMOS - ALEPH PHASER INTEGRATION")
    print(f"Output directory: {args.output_dir}")
    print(f"SDR URI: {args.sdr_uri}")
    print(f"Phaser URI: {args.phaser_uri}")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    start_time = time.perf_counter()
    results = {}
    
    # Check hardware connectivity first
    if not args.skip_hardware_check:
        hw_status = check_hardware_connectivity(args.sdr_uri, args.phaser_uri)
        
        if not hw_status['sdr']:
            print("\n✗ Cannot proceed without PlutoSDR connection.")
            print("  Make sure PlutoSDR is connected via USB and accessible at", args.sdr_uri)
            return 1
        
        if not hw_status['phaser'] and args.demo not in ['sdr', 'quick']:
            print("\n⚠ Phaser not accessible - some demos will be skipped.")
            print("  Make sure Raspberry Pi is running iiod at", args.phaser_uri)
    
    # Define demos
    demos = [
        {
            'id': 'sdr',
            'name': 'SDR Basic Capture',
            'script': 'sdr_basic_capture.py',
            'args': ['--uri', args.sdr_uri],
            'requires_phaser': False,
            'quick': True,
        },
        {
            'id': 'connection',
            'name': 'Phaser Connection Test',
            'script': 'test_phaser_connection.py',
            'args': ['--sdr-uri', args.sdr_uri, '--phaser-uri', args.phaser_uri],
            'requires_phaser': True,
            'quick': True,
        },
        {
            'id': 'minimal',
            'name': 'Minimal Example',
            'script': 'aleph_minimal_example.py',
            'args': ['--sdr-uri', args.sdr_uri, '--phaser-uri', args.phaser_uri, 
                     '--output-dir', args.output_dir],
            'requires_phaser': True,
            'quick': False,
        },
        {
            'id': 'beam',
            'name': 'Beam Steering Demo',
            'script': 'aleph_beam_steering.py',
            'args': ['--sdr-uri', args.sdr_uri, '--phaser-uri', args.phaser_uri,
                     '--output-dir', args.output_dir],
            'requires_phaser': True,
            'quick': False,
        },
        {
            'id': 'labs',
            'name': 'Lab Exercises (3 & 4)',
            'script': 'aleph_lab_exercises.py',
            'args': ['--sdr-uri', args.sdr_uri, '--phaser-uri', args.phaser_uri,
                     '--output-dir', args.output_dir, '--lab', 'both'],
            'requires_phaser': True,
            'quick': False,
        },
        {
            'id': 'benchmark',
            'name': 'Performance Benchmark',
            'script': 'aleph_benchmark.py',
            'args': ['--sdr-uri', args.sdr_uri, '--phaser-uri', args.phaser_uri,
                     '--output-dir', args.output_dir],
            'requires_phaser': True,
            'quick': False,
        },
    ]
    
    # Filter demos based on arguments
    demos_to_run = []
    for demo in demos:
        if args.demo == 'all':
            if args.quick and not demo['quick']:
                continue
            demos_to_run.append(demo)
        elif args.demo == demo['id']:
            demos_to_run.append(demo)
    
    # Run demos
    for demo in demos_to_run:
        script_path = os.path.join(script_dir, demo['script'])
        
        if not os.path.exists(script_path):
            print(f"\n⚠ Script not found: {script_path}")
            results[demo['id']] = False
            continue
        
        success = run_demo_script(
            script_path,
            demo['args'],
            demo['name'],
            timeout=180
        )
        results[demo['id']] = success
    
    # Summary
    total_time = time.perf_counter() - start_time
    
    print_header("DEMO RESULTS SUMMARY")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for demo_id, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        demo_name = next((d['name'] for d in demos if d['id'] == demo_id), demo_id)
        print(f"  {demo_name:.<45} {status}")
    
    print("-" * 60)
    print(f"  Results: {passed}/{total} passed")
    print(f"  Total time: {total_time:.1f}s")
    print()
    
    # List output files
    if os.path.exists(args.output_dir):
        files = os.listdir(args.output_dir)
        if files:
            print("Output files:")
            for f in sorted(files):
                fpath = os.path.join(args.output_dir, f)
                size = os.path.getsize(fpath) / 1024
                print(f"  - {f} ({size:.1f} KB)")
    
    # Write summary
    summary_path = os.path.join(args.output_dir, "cpu_demo_summary.txt")
    with open(summary_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("CPU DEMO RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Total time: {total_time:.1f}s\n\n")
        f.write("Results:\n")
        for demo_id, success in results.items():
            status = "PASS" if success else "FAIL"
            f.write(f"  {demo_id}: {status}\n")
        f.write(f"\nPassed: {passed}/{total}\n")
    
    print(f"\nSummary saved to: {summary_path}")
    
    if passed == total:
        print("\n🎉 All CPU demos passed!")
        return 0
    elif passed > 0:
        print("\n⚠ Some demos failed. Check output above for details.")
        return 1
    else:
        print("\n❌ All demos failed. Check hardware connectivity.")
        return 2


if __name__ == '__main__':
    sys.exit(main())
