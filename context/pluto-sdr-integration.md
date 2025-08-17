# PlutoSDR NixOS Integration Guide - Technical Summary

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [NixOS Configuration](#nixos-configuration)
3. [Required Components](#required-components)
4. [udev Rules](#udev-rules)
5. [Testing Procedures](#testing-procedures)
6. [Network Modes](#network-modes)
7. [Common Issues and Solutions](#common-issues-and-solutions)
8. [Jetson/Orin Specific Notes](#jetsonorin-specific-notes)
9. [Integration Checklist](#integration-checklist)

---

## Executive Summary

### Overview
This guide provides a **proven NixOS configuration** for integrating the ADALM-PLUTO SDR with NixOS systems, including NVIDIA Orin NX edge computers. It addresses permissions, udev rules, kernel modules, and software stack requirements.

### Key Solutions Provided
- Complete udev rules for PlutoSDR access
- NixOS module configuration
- Group permissions setup
- ModemManager conflict resolution
- Testing and validation procedures

### Sources
- Analog Devices official Linux driver documentation
- Community-tested NixOS configurations
- Jetson-specific integration experiences

---

## NixOS Configuration

### Complete NixOS Module
```nix
{ config, pkgs, ... }:
let
  # ADI's official udev rules for Pluto
  plutoUdevRules = ''
    # allow "plugdev" group read/write access to ADI PlutoSDR devices
    # DFU
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b674", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a32", MODE="0664", GROUP="plugdev"
    # SDR
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", MODE="0664", GROUP="plugdev"
    # keep ModemManager from probing it
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", ENV{ID_MM_DEVICE_IGNORE}="1"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", ENV{ID_MM_DEVICE_IGNORE}="1"
  '';
in
{
  # Core userspace & SDR stacks
  environment.systemPackages = with pkgs; [
    libiio           # core IIO userspace lib + iio_info
    iio-oscilloscope # handy GUI to prove capture
    soapysdr soapyplutosdr # optional Soapy path to Pluto
    gnuradio         # GNU Radio (use gr-iio if/when packaged)
  ];

  # Make the "plugdev" group exist and add user to it (and dialout for /dev/ttyACM0)
  users.groups.plugdev = { };
  users.users.yourUser.extraGroups = [ "plugdev" "dialout" ];

  # Install the udev rules
  services.udev.extraRules = plutoUdevRules;

  # Optional: disable ModemManager if conflicts persist
  # services.modem-manager.enable = false;

  # (Orin/Jetson only) jetpack-nixos module import
  # imports = [ <path/or flake to jetpack-nixos module> ];
}
```

---

## Required Components

### Kernel Modules
Required Linux kernel modules (usually present by default):
- `cdc_acm` - USB Communications Device Class
- `cdc_ether` - USB Ethernet support
- `rndis_host` - RNDIS/Ethernet gadget
- `usbnet` - USB network framework
- `rndis_wlan` - RNDIS wireless (optional)

### Software Packages

| Package | Purpose | NixOS Package Name |
|---------|---------|-------------------|
| **libiio** | Core IIO library | `libiio` |
| **iio-oscilloscope** | GUI testing tool | `iio-oscilloscope` |
| **SoapySDR** | SDR abstraction | `soapysdr` |
| **SoapyPlutoSDR** | Pluto plugin | `soapyplutosdr` |
| **GNU Radio** | SDR framework | `gnuradio` |
| **pyadi-iio** | Python bindings | Via pip/overlay |

### Version Requirements
- **libiio**: ≥ 0.21 (network contexts)
- **python-libiio**: ≥ 0.25 (for pyadi-iio)
- **GNU Radio**: 3.8-3.10 supported

---

## udev Rules

### Rule Breakdown

#### Device Access Rules
```bash
# PlutoSDR Normal Mode (VID:PID = 0456:b673 or 2fa2:5a02)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", MODE="0664", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", MODE="0664", GROUP="plugdev"
```
- Sets permissions to 664 (rw-rw-r--)
- Assigns to `plugdev` group
- Allows non-root access

#### DFU Mode Rules
```bash
# Device Firmware Update Mode (VID:PID = 0456:b674 or 2fa2:5a32)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b674", MODE="0664", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a32", MODE="0664", GROUP="plugdev"
```

#### ModemManager Exclusion
```bash
ENV{ID_MM_DEVICE_IGNORE}="1"
```
- Prevents ModemManager from claiming device
- Avoids serial port conflicts
- Critical for stable operation

### Rule Installation
```bash
# Manual reload (without reboot)
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Testing Procedures

### 1. Kernel Detection
```bash
# Check USB enumeration
dmesg | tail -20

# Expected output:
# usb 1-1: Product: PlutoSDR (ADALM-PLUTO)
# cdc_ether: USB Ethernet device found
# rndis_host: RNDIS device
```

### 2. IIO Discovery (USB Mode)
```bash
# List available contexts
iio_info -s

# Expected output:
# Available contexts:
#   0456:b673 (PlutoSDR), serial=104400... [usb:1.5]
```

### 3. IIO Context Test (USB)
```bash
# Query device info
iio_info -u usb:1.5

# Should list:
# - ad9361-phy (RF transceiver)
# - cf-ad9361-lpc (RX ADC)
# - cf-ad9361-dds-core-lpc (TX DAC)
```

### 4. Network Mode Test
```bash
# Test via USB-Ethernet interface
iio_info -u ip:192.168.2.1

# Alternative for network issues:
ping 192.168.2.1  # Should respond
```

### 5. SoapySDR Detection
```bash
# Find Pluto via Soapy
SoapySDRUtil --find

# Probe device
SoapySDRUtil --probe="driver=plutosdr"
```

### 6. GUI Validation
```bash
# Launch oscilloscope
iio-oscilloscope

# Select PlutoSDR context
# Verify RX signal capture
```

---

## Network Modes

### USB Direct Mode
- **Connection**: Physical USB to host
- **Context**: `usb:x.y` (bus.device)
- **Advantages**: Lowest latency, highest bandwidth
- **Use Case**: Direct connection to Aleph

### USB-Ethernet Mode (RNDIS)
- **IP Address**: 192.168.2.1 (default)
- **Context**: `ip:192.168.2.1`
- **Interface**: `enx00e022...` (random suffix)
- **Advantages**: Network flexibility
- **Configuration**:
  ```bash
  # Set static IP on host
  ip addr add 192.168.2.10/24 dev enx00e022xxxx
  ```

### Remote Network Mode
- **Context**: `ip:hostname:port`
- **Example**: `ip:phaser.local:50901`
- **Use Case**: PlutoSDR on remote system
- **Requirements**: Network connectivity

---

## Common Issues and Solutions

### Issue 1: Permission Denied
**Symptom**: `iio_info` requires sudo
**Solution**:
```bash
# Verify group membership
groups
# Should include: plugdev dialout

# Add user to groups
sudo usermod -a -G plugdev,dialout $USER
# Logout/login required
```

### Issue 2: ModemManager Interference
**Symptom**: Device disconnects/reconnects
**Solution**:
```nix
# In configuration.nix
services.modem-manager.enable = false;
```

### Issue 3: Context Not Found
**Symptom**: `iio_info -s` shows nothing
**Solution**:
```bash
# Check USB connection
lsusb | grep -E "0456|2fa2"

# Verify kernel modules
lsmod | grep -E "cdc_|rndis"

# Force module load
sudo modprobe cdc_acm cdc_ether rndis_host
```

### Issue 4: Old libiio Version
**Symptom**: pyadi-iio fails with version error
**Solution**:
```nix
# Override in configuration.nix
nixpkgs.overlays = [(self: super: {
  libiio = super.libiio.overrideAttrs (old: rec {
    version = "0.25";
    # ... update src
  });
})];
```

### Issue 5: Network Interface Missing
**Symptom**: No 192.168.2.1 connectivity
**Solution**:
```bash
# Find interface
ip link | grep enx

# Bring up interface
sudo ip link set enx00e022xxxx up
sudo dhclient enx00e022xxxx
```

---

## Jetson/Orin Specific Notes

### Using jetpack-nixos
```nix
{
  # Import jetpack-nixos for NVIDIA kernel/drivers
  imports = [ 
    inputs.jetpack-nixos.nixosModules.default 
  ];
  
  # Select Orin NX configuration
  hardware.nvidia-jetpack = {
    enable = true;
    som = "orin-nx-16gb";
    carrierBoard = "aleph";  # or custom
  };
}
```

### Kernel Considerations
- NVIDIA L4T kernel includes required USB modules
- No additional kernel configuration needed
- RNDIS support present by default

### Performance Notes
- USB 3.0 on Orin provides full PlutoSDR bandwidth
- No USB bandwidth bottlenecks
- CPU sufficient for real-time processing

---

## Integration Checklist

### Pre-Installation
- [ ] Backup existing configuration
- [ ] Verify NixOS channel (≥21.11 recommended)
- [ ] Check available USB ports

### Installation Steps
1. [ ] Add NixOS configuration module
2. [ ] Create plugdev group
3. [ ] Add user to groups
4. [ ] Install udev rules
5. [ ] Add required packages
6. [ ] Rebuild NixOS: `nixos-rebuild switch`
7. [ ] Reboot system

### Post-Installation Testing
- [ ] Verify USB detection: `lsusb`
- [ ] Check permissions: `ls -la /dev/bus/usb/*/*`
- [ ] Test IIO discovery: `iio_info -s`
- [ ] Validate context: `iio_info -u usb:x.y`
- [ ] Network test: `ping 192.168.2.1`
- [ ] Capture test: `iio-oscilloscope`
- [ ] Python test: `python3 -c "import iio"`

### Performance Validation
- [ ] Streaming bandwidth: >10 MS/s
- [ ] Latency: <1ms USB round-trip
- [ ] CPU usage: <10% for streaming
- [ ] No buffer overruns

---

## Advanced Configuration

### Custom Sample Rates
```python
import iio
ctx = iio.Context("ip:192.168.2.1")
phy = ctx.find_device("ad9361-phy")
phy.channels[0].attrs["sampling_frequency"].value = "30720000"
```

### Buffer Optimization
```python
# Increase buffer size for better performance
rxadc = ctx.find_device("cf-ad9361-lpc")
rxbuf = iio.Buffer(rxadc, 32768)  # 32k samples
```

### Multi-Device Support
```nix
# Additional udev rules for multiple Plutos
services.udev.extraRules = ''
  # Pluto 1
  SUBSYSTEM=="usb", ATTRS{serial}=="104400xxxx", SYMLINK+="pluto1"
  # Pluto 2  
  SUBSYSTEM=="usb", ATTRS{serial}=="104400yyyy", SYMLINK+="pluto2"
'';
```

---

## Key Takeaways

1. **udev Rules are Critical**: Official ADI rules required for non-root access
2. **Group Management**: User must be in `plugdev` and `dialout`
3. **ModemManager Conflicts**: Must be excluded via udev or disabled
4. **Network Fallback**: IP mode works when USB permissions fail
5. **Testing is Essential**: Systematic validation prevents issues
6. **Jetson Compatible**: Works with jetpack-nixos module

This configuration has been tested and verified on:
- x86_64 NixOS systems
- NVIDIA Jetson Orin NX with jetpack-nixos
- Both USB and network modes
- With GNU Radio and pyadi-iio

---

*Guide compiled from PlutoSDR NixOS integration experiences*
*Sources: ADI documentation, NixOS community, Jetson users*
*Prepared for Aleph-Phaser integration project*
