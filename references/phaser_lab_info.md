# CN0566 Phaser Lab Instructions - Technical Summary

## Table of Contents
1. [Workshop Overview](#workshop-overview)
2. [Hardware Setup](#hardware-setup)
3. [Lab Modules](#lab-modules)
   - [Lab 1: SDR and Software Control](#lab-1-sdr-and-software-control)
   - [Lab 2: Steering Angle](#lab-2-steering-angle)
   - [Lab 3: Array Factor and Beamwidth](#lab-3-array-factor-and-beamwidth)
   - [Lab 4: Sidelobes and Tapering](#lab-4-sidelobes-and-tapering)
   - [Lab 5: Grating Lobes](#lab-5-grating-lobes)
   - [Lab 6: Beam Squint](#lab-6-beam-squint)
   - [Lab 7: Quantization Sidelobes](#lab-7-quantization-sidelobes)
   - [Lab 8: Hybrid Beamforming](#lab-8-hybrid-beamforming)
   - [Lab 9: Monopulse Tracking](#lab-9-monopulse-tracking)
   - [Lab 10: FMCW Radar](#lab-10-fmcw-radar)
4. [Technical Specifications](#technical-specifications)
5. [Software Architecture](#software-architecture)
6. [Key Learning Objectives](#key-learning-objectives)
7. [Resources and References](#resources-and-references)

---

## Workshop Overview

### Purpose
**Phased Array Exploration Workshop** using Analog Devices' ADALM-PHASER platform
- **Date**: June 20, 2022 (document version June 14, 2022)
- **Goal**: Demystify phased array terminology and provide hands-on understanding of electronically steered arrays (ESA)
- **Application Areas**: 5G communications, automotive radar, satellite communications, military applications

### Core Concepts Covered
- Software-defined radio (SDR) control
- Beamforming fundamentals
- Antenna pattern measurements
- Array impairments and mitigation
- Radar signal processing

---

## Hardware Setup

### Primary Components

#### 1. ADALM-PHASER Board
- 8-element linear phased array
- Operating frequency: ~10.5 GHz
- Element spacing: 14mm
- Integrated with Raspberry Pi and PlutoSDR

#### 2. Connections Required
```
┌─────────────────────────────────┐
│         ADALM-PHASER            │
│  ┌──────────────────────────┐   │
│  │  USB-C Power (5V, 3A)    │◄──┼── Power Supply
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │    Raspberry Pi 4        │   │
│  │  • HDMI Monitor          │◄──┼── Display
│  │  • USB Keyboard/Mouse    │◄──┼── Input Devices
│  │  • PlutoSDR (integrated) │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

#### 3. RF Source: HB100 Module
- **Model**: SEN0192 from DF Robot
- **Frequency**: 10.1-10.7 GHz (nominal 10.525 GHz)
- **Purpose**: Battery-powered, moveable RF source for antenna pattern measurements
- **Use Case**: Freedom of movement for tracking and pattern measurement labs

### Important Setup Notes
- Power applied to Phaser board USB-C, NOT Raspberry Pi USB-C
- All peripherals connect to Raspberry Pi
- PlutoSDR directly attached to Phaser board

---

## Lab Modules

### Lab 1: SDR and Software Control

#### Objectives
- Control PlutoSDR through Python
- Understand signal flow: 10.5 GHz → 2.2 GHz IF → Digital
- Visualize time and frequency domain signals

#### Technical Process
1. **Signal Reception**: 10.525 GHz from HB100
2. **Downconversion**: Mixed to 2.2 GHz IF
3. **SDR Processing**:
   - Pluto PLL: 2.2 GHz - offset
   - ADC Sample Rate: 30 MSPS
   - Digital Filter: 20 MHz bandwidth
   - Buffer Size: 1024 samples
4. **Visualization**: FFT and time domain plots

#### Key Script: `cn0566_minimal_example.py`
- Sets antenna to zero phase
- Equal gain on all elements
- Configures PlutoSDR parameters
- Plots data buffers

#### Lab Exercise
- Modify line 176: Change frequency offset (-10e6 to +10e6)
- Observe impact on received signal

---

### Lab 2: Steering Angle

#### Objectives
- Understand phase shift → steering angle relationship
- Find optimal phase delta for maximum signal reception

#### Key Concepts
- Element-to-element phase shift controls beam direction
- GUI provides real-time steering control
- Peak amplitude indicates beam alignment with source

#### Practical Exercise
1. Position HB100 at 30° using protractor
2. Adjust steering angle slider
3. Find phase delta for maximum FFT amplitude
4. Verify predictable amplitude response in rectangular plot

---

### Lab 3: Array Factor and Beamwidth

#### Theoretical Foundation
**Array Factor Equation** for uniform linear array:
```
AF = sin(N·π·d·sin(θ)/λ) / sin(π·d·sin(θ)/λ)
```

#### Key Measurements

| Elements (N) | HPBW (calc) | FNBW (calc) |
|-------------|-------------|-------------|
| 8           | 13°         | 30°         |
| 4           | 27°         | 62°         |
| 2           | 62°         | 180°        |

**Where**:
- **HPBW**: Half-Power Beam Width (3dB down)
- **FNBW**: First Null Beam Width
- **Frequency**: 10.3 GHz
- **Element spacing (d)**: 14mm

#### Lab Procedures
1. Measure actual HPBW and FNBW for N=8
2. Disable elements to create N=4 array
3. Compare measured vs calculated values
4. Observe beamwidth changes with steering

---

### Lab 4: Sidelobes and Tapering

#### Objectives
- Observe sidelobe reduction through amplitude tapering
- Compare different windowing functions

#### Tapering Options
- Uniform (no taper)
- Blackman window
- Custom symmetric taper

#### Measurements
- Sidelobe level reduction
- Main lobe broadening
- Peak gain reduction

#### Trade-offs
| Taper Type | Sidelobe Level | Beamwidth | Peak Gain |
|------------|----------------|-----------|-----------|
| Uniform    | -13 dB         | Narrow    | Maximum   |
| Blackman   | -58 dB         | Wide      | Reduced   |

---

### Lab 5: Grating Lobes

#### Theory
Grating lobes occur when: `d/λ > 1/(1 + |sin(θ₀)|)`

#### Experimental Configurations

| Config | Element Spacing | Active Elements | Expected Grating Lobes |
|--------|----------------|-----------------|------------------------|
| 1      | 42mm (3×14mm)  | 1,4,7           | ±44°                  |
| 2      | 56mm (4×14mm)  | 1,5             | ±31°, ±90°            |

#### Procedure
1. Set d=42mm by disabling intermediate elements
2. Observe grating lobes at calculated angles
3. Repeat for d=56mm
4. Verify lobe positions match theory

---

### Lab 6: Beam Squint

#### Concept
Beam deviation vs frequency: `Δθ = arcsin(f/f₀ × sin(θ₀)) - θ₀`

#### Example Calculation
- Carrier: 10.5 GHz
- Reference: 10.0 GHz
- Steering: ±45°
- **Result**: 3° beam shift

#### Lab Exercise
1. Set HB100 to 50° angle
2. Adjust signal bandwidth (0-500 MHz)
3. Measure peak angle shift
4. Verify matches calculated squint

---

### Lab 7: Quantization Sidelobes

#### Objective
Observe impact of phase shifter bit resolution on sidelobe levels

#### Configuration
- Apply Blackman taper (suppress natural sidelobes)
- Steering angle: 15°
- Vary phase shift bits: 8 → 2 bits

#### Expected Results
| Phase Bits | Quantization Step | Sidelobe Impact |
|------------|------------------|-----------------|
| 8          | 1.4°             | Negligible      |
| 4          | 22.5°            | Visible         |
| 2          | 90°              | Significant     |

---

### Lab 8: Hybrid Beamforming

#### Architecture
```
Digital Domain                    Analog Domain
┌──────────────┐                 ┌──────────────┐
│ Beam0 (Rx5-8)│────────────────►│ ADAR1000 #1  │
│ Beam1 (Rx1-4)│────────────────►│ ADAR1000 #2  │
└──────────────┘                 └──────────────┘
   Phase/Gain                        Phase/Gain
```

#### Experiments
1. **Digital vs Analog Control**:
   - Compare Beam0=0 vs disabling Rx5-8
   - Test phase shifts at digital vs analog level

2. **Phase Alignment**:
   - Apply random digital phase to Beam0
   - Compensate with analog phase on Rx1-4
   - Verify alignment restoration

---

### Lab 9: Monopulse Tracking

#### Concept
Simultaneous sum and difference patterns for angle tracking

#### Key Signals
- **Sum (Σ)**: Maximum on boresight
- **Difference (Δ)**: Zero on boresight, slope indicates direction
- **Error Function**: Δ/Σ ratio for tracking

#### Implementation
1. Apply Blackman taper
2. Enable Delta and Error displays
3. Activate tracking mode
4. Observe real-time target following

---

### Lab 10: FMCW Radar

#### Radar Parameters
- **Waveform**: Linear frequency ramp (FMCW)
- **Ramp Time (Ts)**: 0.5 ms
- **Bandwidth (B)**: 500 MHz (adjustable)
- **Beat Frequency**: 6.7 kHz/meter

#### Range Equation
```
Range = (c × fb × Ts) / (2 × B)
```

#### Setup Changes
- **Transmit**: Vivaldi antenna with frequency ramp
- **Receive**: 8-element array
- **Target**: Corner reflector (not HB100)
- **Mixer**: LTC5548 on-board

#### Measurements
1. Calibrate "0m frequency" (~100 kHz)
2. Verify 6.7 kHz/m beat frequency
3. Test range resolution
4. Observe waterfall plot for moving targets
5. Test beam steering impact on return signal

---

## Technical Specifications

### Frequency Plan
- **RF Input**: 10.1-10.7 GHz (HB100 source)
- **IF Frequency**: 2.2 GHz (after first downconversion)
- **PlutoSDR Input**: 2.2 GHz ± offset
- **Digital Processing**: 30 MSPS, 20 MHz bandwidth

### Array Specifications
- **Elements**: 8 linear
- **Spacing**: 14mm (0.48λ at 10.3 GHz)
- **Steering Range**: ±60° typical
- **Phase Control**: 8-bit resolution (1.4° steps)
- **Gain Control**: Per-element on/off, tapering profiles

### Software Stack
- **OS**: Raspberry Pi OS
- **IDE**: Thonny Python IDE
- **SDR Framework**: GNU Radio
- **Hardware Control**: pyadi-iio library
- **Visualization**: Matplotlib

---

## Key Learning Objectives

### Fundamental Concepts
1. **Beamforming Basics**
   - Phase steering principles
   - Array factor mathematics
   - Beamwidth vs array size

2. **Array Impairments**
   - Sidelobe formation and suppression
   - Grating lobe conditions
   - Beam squint with frequency
   - Quantization effects

3. **Advanced Techniques**
   - Amplitude tapering strategies
   - Hybrid analog/digital beamforming
   - Monopulse tracking
   - FMCW radar processing

### Practical Skills
- Python-based SDR control
- Real-time signal visualization
- Antenna pattern measurement
- Radar range detection

---

## Resources and References

### Documentation
- **Hardware Wiki**: https://wiki.analog.com/phaser
- **PlutoSDR Resources**: https://wiki.analog.com/sdrseminars
- **Article Series**: https://www.analog.com/en/analog-dialogue/articles/phased-array-antenna-patterns-part1.html

### GitHub Repositories
- **Phaser Examples**: https://github.com/jonkraft/PhaserBeamforming
- **pyadi-iio**: https://github.com/analogdevicesinc/pyadi-iio

### Key Scripts
1. `cn0566_minimal_example.py` - Basic SDR control
2. `cn0566_gui.py` - Interactive beamforming GUI
3. `RADAR_FFT_Waterfall.py` - FMCW radar implementation

### Hardware Datasheets
- **HB100 Sensor**: https://www.limpkin.fr/public/HB100/HB100_Microwave_Sensor_Module_Datasheet.pdf
- **ADAR1000**: 4-channel X/Ku band beamformer
- **ADF4159**: 13 GHz fractional-N PLL
- **LTC5548**: Microwave mixer

---

## Implementation Notes for Aleph Integration

### Current Dependencies on Raspberry Pi
1. **Display Output**: HDMI for GUI visualization
2. **USB Peripherals**: Keyboard/mouse for interaction
3. **Python Environment**: Thonny IDE, matplotlib
4. **OS Services**: Desktop environment for labs

### Headless Operation Potential
- All core functionality accessible via pyadi-iio
- Remote plotting possible via SSH + X11 forwarding
- Command-line control scripts available
- Web-based GUI could replace desktop requirement

### Critical Path Items
1. PlutoSDR USB communication
2. Python 3.x with numpy, matplotlib
3. GNU Radio framework (optional for advanced features)
4. pyadi-iio library installation
5. Network configuration for remote access

---

*Document compiled from Phaser Lab Instructions, June 14, 2022*
*Summary prepared for Aleph-Phaser integration project*
