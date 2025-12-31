#!/usr/bin/env python3
"""
PlutoSDR Connection Test Script

Tests connectivity for the Aleph + Phaser system:
- PlutoSDR via direct USB (through USB hub)
- Phaser board via Raspberry Pi over WiFi
- GPU (CuPy) availability

Usage:
    python3 test_plutosdr.py
"""

import sys
import subprocess


def test_usb_detection():
    """Check if PlutoSDR is detected via USB"""
    print("=" * 60)
    print("TEST 1: USB Device Detection")
    print("-" * 60)
    
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        
        pluto_found = False
        for line in lines:
            if '0456' in line or '2fa2' in line:
                print(f"✓ Found PlutoSDR: {line}")
                pluto_found = True
                
        if not pluto_found:
            print("✗ PlutoSDR not detected via USB")
            print("  Check USB connection (use a USB hub if needed)")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_network_interface():
    """Check if PlutoSDR network interface is up"""
    print("\n" + "=" * 60)
    print("TEST 2: Network Interface (USB-Ethernet)")
    print("-" * 60)
    
    try:
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
        interfaces = result.stdout
        
        if '192.168.2' in interfaces:
            print("✓ PlutoSDR network interface found")
            
            ping_result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '192.168.2.1'],
                capture_output=True
            )
            if ping_result.returncode == 0:
                print("✓ PlutoSDR is reachable at 192.168.2.1")
                return True
            else:
                print("⚠ Interface exists but PlutoSDR not responding to ping")
                return False
        else:
            print("✗ No PlutoSDR network interface found")
            print("  The USB-Ethernet gadget may not be enabled")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_iio_context():
    """Test IIO context access"""
    print("\n" + "=" * 60)
    print("TEST 3: IIO Context (ip:192.168.2.1)")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            ['iio_info', '-u', 'ip:192.168.2.1'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and 'ad9361' in result.stdout.lower():
            for line in result.stdout.splitlines():
                if 'hw_model' in line:
                    print(f"✓ {line.strip()}")
                    break
            return True
        else:
            print(f"✗ IIO context failed")
            if result.stderr:
                print(f"  {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ IIO context timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_python_adi():
    """Test pyadi-iio connection"""
    print("\n" + "=" * 60)
    print("TEST 4: Python pyadi-iio Connection")
    print("-" * 60)
    
    try:
        import adi
        sdr = adi.ad9361(uri='ip:192.168.2.1')
        print(f"✓ Connected to PlutoSDR")
        print(f"  Sample rate: {sdr.sample_rate/1e6:.1f} MHz")
        print(f"  RX LO: {sdr.rx_lo/1e9:.3f} GHz")
        return True
    except ImportError:
        print("✗ pyadi-iio not installed")
        return False
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False


def test_data_acquisition():
    """Test actual data capture"""
    print("\n" + "=" * 60)
    print("TEST 5: Data Acquisition")
    print("-" * 60)
    
    try:
        import adi
        import numpy as np
        
        sdr = adi.ad9361(uri='ip:192.168.2.1')
        sdr.rx_buffer_size = 4096
        sdr.rx_enabled_channels = [0]
        
        data = sdr.rx()
        if isinstance(data, list):
            data = data[0]
        
        print(f"✓ Captured {len(data)} samples")
        print(f"  Data type: {data.dtype}")
        print(f"  Mean amplitude: {np.abs(data).mean():.2f}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_phaser_connection():
    """Test Phaser board on Raspberry Pi"""
    print("\n" + "=" * 60)
    print("TEST 6: Phaser Board (via Pi at 192.168.4.184)")
    print("-" * 60)
    
    try:
        # First check Pi is reachable
        ping_result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', '192.168.4.184'],
            capture_output=True
        )
        if ping_result.returncode != 0:
            print("✗ Raspberry Pi not reachable at 192.168.4.184")
            return False
        
        result = subprocess.run(
            ['iio_info', '-u', 'ip:192.168.4.184'],
            capture_output=True, text=True, timeout=10
        )
        
        found_adf = 'adf4159' in result.stdout.lower()
        found_adar = 'adar1000' in result.stdout.lower()
        
        if found_adf:
            print("✓ ADF4159 PLL found")
        if found_adar:
            print("✓ ADAR1000 Beamformer found")
        
        if found_adf and found_adar:
            return True
        elif result.returncode == 0:
            print("⚠ Connected to Pi but Phaser devices not detected")
            return False
        else:
            print(f"✗ Failed to connect to Pi iiod")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Connection to Pi timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_gpu():
    """Test GPU/CuPy availability"""
    print("\n" + "=" * 60)
    print("TEST 7: GPU (CuPy) Availability")
    print("-" * 60)
    
    try:
        import cupy as cp
        dev = cp.cuda.Device(0)
        mem = dev.mem_info
        print(f"✓ CuPy available")
        print(f"  GPU memory: {mem[1]/1e9:.1f} GB total, {mem[0]/1e9:.1f} GB free")
        return True
    except ImportError:
        print("⚠ CuPy not installed (GPU acceleration unavailable)")
        return False
    except Exception as e:
        print(f"⚠ CuPy error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "█" * 60)
    print(" PlutoSDR Integration Test Suite for Aleph ".center(60))
    print("█" * 60)
    
    tests = [
        ("USB Detection", test_usb_detection),
        ("Network Interface", test_network_interface),
        ("IIO Context", test_iio_context),
        ("Python pyadi-iio", test_python_adi),
        ("Data Acquisition", test_data_acquisition),
        ("Phaser Board", test_phaser_connection),
        ("GPU (CuPy)", test_gpu),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "█" * 60)
    print(" TEST SUMMARY ".center(60))
    print("█" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS ✓" if result else "FAIL ✗"
        print(f"  {name:.<40} {status}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    # Core tests are 1-5 (USB, network, IIO, pyadi, data)
    core_passed = sum(1 for name, result in results[:5] if result)
    
    if core_passed == 5:
        print("\n🎉 PlutoSDR is ready for use!")
        print("\nURIs for scripts:")
        print("  PlutoSDR: ip:192.168.2.1")
        print("  Phaser:   ip:192.168.4.184")
        return 0
    elif core_passed >= 3:
        print("\n⚠ Some tests failed but basic functionality may work.")
        return 1
    else:
        print("\n❌ PlutoSDR integration needs attention.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
