# Phaser Beamforming Example - Code Analysis

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Code Structure](#code-structure)
3. [Key Parameters](#key-parameters)
4. [Hardware Configuration](#hardware-configuration)
5. [Beamforming Algorithm](#beamforming-algorithm)
6. [SDR Configuration](#sdr-configuration)
7. [Data Processing](#data-processing)
8. [Integration Considerations](#integration-considerations)
9. [Aleph Porting Requirements](#aleph-porting-requirements)

---

## Executive Summary

### Overview
This Python script (`simple-beamforming-example.py`) demonstrates real-time phased array beamforming using the CN0566 Phaser platform. Written by Jon Kraft from Analog Devices (Jan 2025), it provides a working reference implementation for beam steering from -90° to +90°.

### Key Features
- Multi-angle beam steering with real-time updates
- Automatic calibration file loading
- HB100 signal source integration (10.525 GHz)
- FFT visualization in dBFS
- Phase calculation for 8-element array

### Dependencies
- `adi` library (pyadi-iio)
- `numpy` for calculations
- `matplotlib` for visualization
- `phaser_functions` for calibration loading

---

## Code Structure

### Main Components

```python
# Key Sections:
1. Imports and Setup (lines 42-48)
2. System Parameters (lines 50-56)
3. User Configuration (lines 59-62)
4. Phaser Object Creation (lines 65-67)
5. Hardware Initialization (lines 70-87)
6. SDR Configuration (lines 89-103)
7. GPIO and PLL Setup (lines 106-114)
8. FFT Processing Function (lines 117-125)
9. Main Steering Loop (lines 128-162)
```

### Execution Flow
1. Initialize Phaser and SDR hardware
2. Load calibration files
3. Configure RF paths and frequencies
4. Loop through steering angles
5. Calculate phase deltas
6. Apply phases to elements
7. Capture and display FFT

---

## Key Parameters

### System Constants

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **sample_rate** | 3 MHz | PlutoSDR sampling rate |
| **rx_lo** | 2.2 GHz | Intermediate frequency |
| **rx_gain** | 0 dB | Receive gain (-3 to 70 dB range) |
| **rx_buffer_size** | 1024 | Samples per capture |
| **SignalFreq** | 10.525 GHz | HB100 source frequency |

### Network Configuration
```python
rpi_ip = "ip:phaser.local"        # Raspberry Pi hosting Phaser
sdr_ip = "ip:phaser.local:50901"  # PlutoSDR via IIO port forwarding
# Alternative: "ip:192.168.2.1"   # Direct USB connection
```

### Steering Angles
```python
# Examples provided:
steer_angles = [0]                      # Single angle
steer_angles = [-30, 0, 30]            # Three discrete angles
steer_angles = np.arange(-90, 90, 10)  # Full sweep in 10° steps
```

---

## Hardware Configuration

### Phaser Initialization
```python
my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)
my_phaser.configure(device_mode="rx")
```

### Calibration Loading
```python
my_phaser.load_channel_cal()  # Channel mismatch correction
my_phaser.load_gain_cal()     # Gain calibration
my_phaser.load_phase_cal()    # Phase calibration
```

### GPIO Control for RF Paths
```python
gpio_tx_sw = 0    # TX_OUT_2 selected (HB100 mode)
gpio_vctrl_1 = 1  # Use onboard PLL/LO
gpio_vctrl_2 = 0  # Disable TX, route LO to LO_OUT
```

### ADF4159 PLL Configuration
```python
vco_freq = SignalFreq + rx_lo  # 10.525 + 2.2 = 12.725 GHz
my_phaser.frequency = vco_freq / 4  # Divided by 4
my_phaser.ramp_mode = "disabled"    # No FMCW
```

---

## Beamforming Algorithm

### Phase Calculation
The core beamforming equation implemented:

```python
# Convert steering angle to phase delta between elements
steer_rad = np.radians(steer_angles[i])
PhDelta = 2*np.pi*element_spacing*np.sin(steer_rad) / (c/SignalFreq)
PhDelta = np.degrees(PhDelta)
```

### Physical Constants
- **Element spacing**: 14mm (0.48λ at 10.525 GHz)
- **Speed of light (c)**: 3×10⁸ m/s
- **Wavelength (λ)**: ~28.5mm at 10.525 GHz

### Phase Application
```python
for element in range(8):
    my_phaser.set_chan_phase(element, element*PhDelta, apply_cal=True)
```
- Linear phase progression across array
- Calibration corrections applied
- Phase wraps at 360°

---

## SDR Configuration

### PlutoSDR Receive Setup
```python
my_sdr.sample_rate = 3e6
my_sdr.rx_lo = 2.2e9
my_sdr.rx_enabled_channels = [0, 1]  # Dual channel
my_sdr.gain_control_mode = 'manual'
my_sdr.rx_hardwaregain = 0
```

### Transmit Disabled
```python
my_sdr.tx_hardwaregain_chan0 = -88  # Minimum power
my_sdr.tx_hardwaregain_chan1 = -88  # Effectively off
```

### Buffer Management
```python
my_sdr._rxadc.set_kernel_buffers_count(1)  # No stale buffers
```

---

## Data Processing

### FFT Calculation Function
```python
def dbfs(raw_data):
    NumSamples = len(raw_data)
    win = np.hamming(NumSamples)        # Window function
    y = raw_data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    s_dbfs = 20*np.log10(np.abs(s_shift)/(2**11))  # 12-bit ADC
    return s_dbfs
```

### Key Processing Steps
1. Apply Hamming window (reduces spectral leakage)
2. Compute FFT normalized by window sum
3. Shift zero frequency to center
4. Convert to dBFS (12-bit ADC reference)

### Data Acquisition
```python
data = my_sdr.rx()           # Capture from both channels
data_sum = data[0] + data[1]  # Coherent combining
sum_dbfs = dbfs(data_sum)     # Process to frequency domain
```

---

## Integration Considerations

### Current Dependencies on Raspberry Pi
1. **Network Access**: Uses `phaser.local` hostname
2. **GPIO Control**: Direct GPIO manipulation
3. **Calibration Files**: Stored on Pi filesystem
4. **IIO Context**: Port forwarding at 50901

### Critical Functions for Aleph
```python
# Essential operations to replicate:
1. my_phaser.configure(device_mode="rx")
2. my_phaser.set_chan_phase(element, phase, apply_cal=True)
3. my_phaser.set_chan_gain(element, gain, apply_cal=True)
4. my_sdr.rx()  # Data capture
```

### Performance Metrics
- **Update Rate**: ~0.5 Hz (2-second pause per angle)
- **Processing**: Real-time FFT of 1024 samples
- **Visualization**: Live matplotlib updates

---

## Aleph Porting Requirements

### Software Dependencies
```bash
# Required Python packages
pip install pyadi-iio
pip install numpy
pip install matplotlib
```

### NixOS Package Requirements
```nix
pythonPackages = with pkgs.python3Packages; [
  pyadi-iio      # ADI hardware interface
  numpy          # Numerical computation
  matplotlib     # Plotting (headless mode)
  scipy          # Signal processing (optional)
];
```

### Network Configuration Changes
```python
# Current (Raspberry Pi):
rpi_ip = "ip:phaser.local"
sdr_ip = "ip:phaser.local:50901"

# Aleph adaptation needed:
aleph_ip = "ip:localhost"  # Local execution
sdr_ip = "ip:192.168.2.1"  # Direct USB to PlutoSDR
```

### Calibration File Management
```python
# Current implementation:
from phaser_functions import load_hb100_cal
my_phaser.SignalFreq = load_hb100_cal()

# Aleph needs:
# - Port phaser_functions module
# - Store calibration in /etc/nixos/phaser/
# - Or embed calibration in configuration
```

### Headless Operation Adaptations
1. **Remove GUI Elements**:
   ```python
   # Replace matplotlib display with file output
   plt.savefig(f'beam_pattern_{angle}.png')
   ```

2. **Add Network API**:
   ```python
   # Expose results via HTTP/JSON
   results = {'angle': angle, 'fft': sum_dbfs.tolist()}
   ```

3. **Logging Instead of Display**:
   ```python
   import logging
   logging.info(f'Steering: {angle}°, Peak: {np.max(sum_dbfs)} dBFS')
   ```

---

## Key Algorithm Insights

### Phase Steering Mathematics
For an 8-element linear array:
- **Phase increment**: ΔΦ = (2π × d × sin(θ)) / λ
- **Element phases**: [0, ΔΦ, 2ΔΦ, 3ΔΦ, 4ΔΦ, 5ΔΦ, 6ΔΦ, 7ΔΦ]
- **Wrap at 360°**: Phases modulo 360

### Example Calculations
| Steering Angle | Phase Delta | Element 7 Phase |
|---------------|-------------|-----------------|
| 0° | 0° | 0° |
| 30° | 87.4° | 611.8° → 251.8° |
| 45° | 123.6° | 865.2° → 145.2° |
| 60° | 151.3° | 1059.1° → 339.1° |

### Calibration Impact
- **Without calibration**: Up to 11 dB element mismatch
- **With calibration**: <0.5 dB mismatch
- **Phase accuracy**: ±2.8° (ADAR1000 limitation)

---

## Testing and Validation

### Expected Results
1. **Peak Signal**: Should track HB100 physical position
2. **Beamwidth**: ~13° at broadside (8 elements)
3. **Sidelobe Level**: -13 dB (uniform weighting)
4. **Dynamic Range**: >40 dB typical

### Troubleshooting Guide
| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| No signal | HB100 off/misaligned | Check power, aim at array |
| Wrong frequency | Calibration missing | Run frequency finder |
| Poor steering | Phase cal missing | Load calibration files |
| Low SNR | Gain too low | Increase rx_gain |

---

## Conclusions

This beamforming example provides:
1. **Complete working implementation** of phased array control
2. **Reference for phase calculations** and array mathematics
3. **Template for SDR integration** with Phaser hardware
4. **Baseline for performance validation**

For Aleph integration, key challenges are:
- Replacing Raspberry Pi network context
- Managing calibration files in NixOS
- Adapting for headless operation
- Handling SPI communication directly

---

*Code analysis based on simple-beamforming-example.py*
*Author: Jon Kraft, Analog Devices, January 2025*
*Analysis prepared for Aleph-Phaser integration project*
