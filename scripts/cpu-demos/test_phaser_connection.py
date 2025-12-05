#!/usr/bin/env python3
"""
Phaser Connection Test for Aleph-Phaser Integration

This script tests connectivity to the CN0566 Phaser via the Raspberry Pi.
The hybrid architecture requires:
  - PlutoSDR connected directly to Aleph (ip:192.168.2.1)
  - Phaser controlled via Raspberry Pi's IIO server (ip:phaser.local)

Usage:
    python3 test_phaser_connection.py [--phaser-uri ip:phaser.local] [--sdr-uri ip:192.168.2.1]
"""

import argparse
import sys

def test_sdr_connection(uri):
    """Test PlutoSDR connection"""
    print(f"Testing PlutoSDR at {uri}...")
    try:
        import adi
        sdr = adi.ad9361(uri=uri)
        print(f"  ✓ Connected to PlutoSDR")
        print(f"    Sample rate: {sdr.sample_rate / 1e6:.1f} MSPS")
        print(f"    RX LO: {sdr.rx_lo / 1e9:.3f} GHz")
        return sdr
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None

def test_phaser_connection(uri, sdr=None):
    """Test Phaser connection via Raspberry Pi"""
    print(f"Testing Phaser at {uri}...")
    try:
        from adi.cn0566 import CN0566
        phaser = CN0566(uri=uri)
        if sdr:
            phaser.sdr = sdr
        print(f"  ✓ Connected to Phaser")
        
        # Try to configure
        phaser.configure(device_mode="rx")
        print(f"  ✓ Phaser configured for RX mode")
        
        return phaser
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None

def test_element_control(phaser):
    """Test Phaser element control"""
    print("Testing element control...")
    try:
        # Set all elements to half gain
        for i in range(8):
            phaser.set_chan_gain(i, 64, apply_cal=False)
        print(f"  ✓ Set gain on all 8 elements")
        
        # Set beam to boresight
        phaser.set_beam_phase_diff(0.0)
        print(f"  ✓ Set beam to boresight (0°)")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def scan_for_phaser(subnet="192.168.4"):
    """Scan network for Phaser IIO service"""
    print(f"Scanning {subnet}.0/24 for IIO services...")
    import subprocess
    import concurrent.futures
    
    def check_host(ip):
        try:
            result = subprocess.run(
                ['iio_info', '-u', f'ip:{ip}'],
                capture_output=True, timeout=2
            )
            if b'CN0566' in result.stdout or b'adar1000' in result.stdout.lower():
                return ip
        except:
            pass
        return None
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_host, f"{subnet}.{i}"): i for i in range(1, 255)}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                print(f"  Found Phaser at {result}!")
                return result
    
    print("  No Phaser found on network")
    return None

def main():
    parser = argparse.ArgumentParser(description='Test Phaser Connection')
    parser.add_argument('--phaser-uri', default='ip:phaser.local',
                        help='Phaser URI (default: ip:phaser.local)')
    parser.add_argument('--sdr-uri', default='ip:192.168.2.1',
                        help='PlutoSDR URI (default: ip:192.168.2.1)')
    parser.add_argument('--scan', action='store_true',
                        help='Scan network for Phaser')
    parser.add_argument('--subnet', default='192.168.4',
                        help='Subnet to scan (default: 192.168.4)')
    args = parser.parse_args()

    print("=== Aleph-Phaser Connection Test ===")
    print()
    
    results = {
        'sdr': False,
        'phaser': False,
        'elements': False
    }
    
    # Test SDR
    sdr = test_sdr_connection(args.sdr_uri)
    results['sdr'] = sdr is not None
    print()
    
    # Optionally scan for Phaser
    if args.scan:
        found_ip = scan_for_phaser(args.subnet)
        if found_ip:
            args.phaser_uri = f"ip:{found_ip}"
        print()
    
    # Test Phaser
    phaser = test_phaser_connection(args.phaser_uri, sdr)
    results['phaser'] = phaser is not None
    print()
    
    # Test element control if Phaser connected
    if phaser:
        results['elements'] = test_element_control(phaser)
        print()
    
    # Summary
    print("=== Summary ===")
    print(f"  PlutoSDR:       {'✓ Working' if results['sdr'] else '✗ Failed'}")
    print(f"  Phaser:         {'✓ Working' if results['phaser'] else '✗ Failed'}")
    print(f"  Element Control: {'✓ Working' if results['elements'] else '✗ Not tested'}")
    print()
    
    if all(results.values()):
        print("SUCCESS: Full Phaser system operational!")
        return 0
    elif results['sdr']:
        print("PARTIAL: PlutoSDR working, but Phaser not accessible.")
        print("         Ensure Raspberry Pi is on the network with iiod running.")
        print("         Try: ssh analog@phaser.local (password: analog)")
        return 1
    else:
        print("FAILED: Cannot connect to SDR or Phaser.")
        return 2

if __name__ == '__main__':
    sys.exit(main())
