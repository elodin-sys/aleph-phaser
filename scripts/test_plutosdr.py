#!/usr/bin/env python3
"""
PlutoSDR Connection Test Script
Tests basic connectivity and IIO context access
"""

import sys
import subprocess
import time

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
            print("  Check USB connection and power")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error running lsusb: {e}")
        return False

def test_kernel_modules():
    """Check if required kernel modules are loaded"""
    print("\n" + "=" * 60)
    print("TEST 2: Kernel Module Check")
    print("-" * 60)
    
    required_modules = ['cdc_acm', 'cdc_ether', 'rndis_host', 'usbnet']
    all_loaded = True
    
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        loaded_modules = result.stdout
        
        for module in required_modules:
            module_base = module.replace('_', '[-_]')  # Handle underscore/dash
            if module in loaded_modules or module.replace('_', '-') in loaded_modules:
                print(f"✓ Module {module} is loaded")
            else:
                print(f"✗ Module {module} is NOT loaded")
                print(f"  Try: sudo modprobe {module}")
                all_loaded = False
                
        return all_loaded
        
    except Exception as e:
        print(f"✗ Error checking modules: {e}")
        return False

def test_iio_context():
    """Test IIO context discovery"""
    print("\n" + "=" * 60)
    print("TEST 3: IIO Context Discovery")
    print("-" * 60)
    
    try:
        # Check for iio_info command
        result = subprocess.run(['which', 'iio_info'], capture_output=True)
        if result.returncode != 0:
            print("✗ iio_info not found. libiio may not be installed")
            return False
            
        # Try to scan for IIO contexts
        print("Scanning for IIO contexts...")
        result = subprocess.run(['iio_info', '-s'], capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout
            if 'PlutoSDR' in output or '0456:b673' in output:
                print(f"✓ PlutoSDR IIO context found:")
                print(f"  {output.strip()}")
                return True
            else:
                print("✗ No PlutoSDR context found")
                print(f"  Output: {output.strip()}")
        else:
            print(f"✗ Error running iio_info: {result.stderr}")
            
        return False
        
    except Exception as e:
        print(f"✗ Error testing IIO: {e}")
        return False

def test_network_interface():
    """Check if PlutoSDR network interface is up"""
    print("\n" + "=" * 60)
    print("TEST 4: Network Interface (USB-Ethernet)")
    print("-" * 60)
    
    try:
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
        interfaces = result.stdout
        
        # Look for the typical PlutoSDR interface
        if 'enx' in interfaces or '192.168.2' in interfaces:
            print("✓ PlutoSDR network interface found")
            
            # Try to ping PlutoSDR
            ping_result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '192.168.2.1'],
                capture_output=True
            )
            if ping_result.returncode == 0:
                print("✓ PlutoSDR is reachable at 192.168.2.1")
                return True
            else:
                print("⚠ Interface exists but PlutoSDR not responding to ping")
                print("  This might be normal depending on configuration")
                return True
        else:
            print("✗ No PlutoSDR network interface found")
            print("  The device may not be in network mode")
            return False
            
    except Exception as e:
        print(f"✗ Error checking network: {e}")
        return False

def test_python_import():
    """Test Python library imports"""
    print("\n" + "=" * 60)
    print("TEST 5: Python Library Imports")
    print("-" * 60)
    
    libraries = [
        ('numpy', 'NumPy'),
        ('matplotlib', 'Matplotlib'),
        ('iio', 'Python libiio bindings'),
    ]
    
    all_imported = True
    for lib, name in libraries:
        try:
            __import__(lib)
            print(f"✓ {name} ({lib}) imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {name} ({lib}): {e}")
            all_imported = False
            
    # Special test for pyadi-iio (might need pip install)
    try:
        import adi
        print("✓ pyadi-iio imported successfully")
    except ImportError:
        print("⚠ pyadi-iio not installed yet")
        print("  Install with: pip install pyadi-iio")
        
    return all_imported

def test_permissions():
    """Check user permissions"""
    print("\n" + "=" * 60)
    print("TEST 6: User Permissions")
    print("-" * 60)
    
    try:
        import os
        import grp
        
        username = os.environ.get('USER', 'unknown')
        print(f"Current user: {username}")
        
        # Get user's groups
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        gid = os.getgid()
        groups.append(grp.getgrgid(gid).gr_name)
        
        required_groups = ['plugdev', 'dialout']
        all_present = True
        
        for group in required_groups:
            if group in groups:
                print(f"✓ User is in '{group}' group")
            else:
                print(f"✗ User is NOT in '{group}' group")
                print(f"  Add with: sudo usermod -a -G {group} {username}")
                all_present = False
                
        return all_present
        
    except Exception as e:
        print(f"✗ Error checking permissions: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "█" * 60)
    print(" PlutoSDR Integration Test Suite for Aleph ".center(60))
    print("█" * 60)
    
    tests = [
        ("USB Detection", test_usb_detection),
        ("Kernel Modules", test_kernel_modules),
        ("IIO Context", test_iio_context),
        ("Network Interface", test_network_interface),
        ("Python Libraries", test_python_import),
        ("User Permissions", test_permissions),
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
    
    if passed == total:
        print("\n🎉 All tests passed! PlutoSDR is ready for use.")
        return 0
    elif passed >= 3:
        print("\n⚠ Some tests failed. Basic functionality should work.")
        print("Review the failed tests above for troubleshooting.")
        return 1
    else:
        print("\n❌ Multiple tests failed. PlutoSDR integration needs attention.")
        print("Check hardware connections and review errors above.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
