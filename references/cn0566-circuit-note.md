# CN0566 Circuit Note - Technical Summary

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Key Components](#key-components)
4. [RF Signal Path](#rf-signal-path)
5. [Beamforming Fundamentals](#beamforming-fundamentals)
6. [Hardware Specifications](#hardware-specifications)
7. [Power Architecture](#power-architecture)
8. [System Calibration](#system-calibration)
9. [Performance Metrics](#performance-metrics)
10. [Common Variations](#common-variations)
11. [Integration Considerations](#integration-considerations)

---

## Executive Summary

The **CN0566** is a complete phased array development platform designed as an educational and prototyping tool for X-band (10.0-10.5 GHz) beamforming applications. It combines:
- 8-element linear antenna array
- Dual ADAR1000 beamformers
- Integrated frequency synthesizer
- PlutoSDR for signal digitization
- Direct Raspberry Pi mounting
- Single 5V USB-C power source

**Primary Applications**:
- Phased array education
- Radar development (FMCW, Doppler)
- Beamforming research
- 5G/communications prototyping
- Synthetic aperture imaging

---

## System Architecture

### High-Level Block Diagram
```
Antenna Array (8 elements, 10-10.5 GHz)
       ↓
   ADL8107 LNAs (24 dB gain each)
       ↓
   ADAR1000 Beamformers (2×4 channels)
       ↓
   LTC5548 Mixers → 2.2 GHz IF
       ↓
   PlutoSDR (ADC/Digital Processing)
       ↓
   Raspberry Pi 4 (Control/Software)
```

### Key Interfaces
- **RF Input**: 8 patch antennas or external SMP connectors
- **IF Output**: 2.2 GHz to PlutoSDR
- **LO Generation**: ADF4159 PLL + HMC735 VCO (10.5-12.7 GHz)
- **Digital Control**: SPI, I2C via Raspberry Pi
- **Power**: 5V, 3A USB-C

---

## Key Components

### Core ICs and Their Functions

| Component | Function | Key Specifications |
|-----------|----------|-------------------|
| **ADAR1000** (×2) | 4-channel beamformer | 8-16 GHz, 360° phase @ 2.8° resolution, 31 dB gain @ 0.5 dB steps |
| **ADF4159** | Fractional-N PLL | 13 GHz, FMCW capable, sawtooth/triangular/parabolic ramps |
| **HMC735** | VCO | 10.5-12.2 GHz with ÷4 output |
| **LTC5548** (×2) | Microwave mixer | 2-14 GHz RF, DC-6 GHz IF |
| **ADL8107** (×9) | Low noise amplifier | 6-18 GHz, 24 dB gain, 2.5 dB NF |
| **AD7291** | System monitor ADC | 8-channel, 12-bit, I2C interface |

### Support Components
- **LTC4217**: Hot swap controller with current monitoring
- **LT8609S**: Step-down regulator (5V → 3.3V)
- **Multiple LDOs**: ADP7158, ADM7150, ADM7170, ADP7118
- **ADRF5019**: SPDT switch for transmit path selection

---

## RF Signal Path

### Receive Path (Primary)
1. **Antenna Input**: 10.0-10.5 GHz signal
2. **LNA Stage**: ADL8107 provides 24 dB gain per element
3. **Beamforming**: ADAR1000 applies phase/amplitude weights
4. **Combining**: 4 channels summed to RFIO output
5. **Filtering**: 10.6 GHz LPF removes high-side image
6. **Downconversion**: LTC5548 mixes to 2.2 GHz IF
7. **IF Filtering**: 2.5 GHz LPF
8. **Digitization**: PlutoSDR samples at 30 MSPS

**Measured Performance**:
- SFDR: ~56 dBc
- Noise Figure: ~2.5 dB (ADL8107 contribution)

### Transmit Path (Auxiliary)
1. **Input**: 2.2 GHz from SDR
2. **Filtering**: 2.5 GHz LPF (removes harmonics)
3. **Upconversion**: LTC5548 to 10-10.3 GHz
4. **Amplification**: ADL8107 (+24 dB)
5. **Output Filtering**: 9.7-11.95 GHz BPF
6. **Outputs**: TX1/TX2 SMA connectors

### Virtual Array Mode
- Alternates between TX1 and TX2 outputs
- Triggered by PLL chirp counter (2, 4, 8...128 chirps)
- Effectively doubles array aperture
- Trade-off: 2× data collection time

---

## Beamforming Fundamentals

### Key Equations

**Element Phase Shift for Beam Steering**:
```
ΔΦ = (2π × d × sin(θ)) / λ
```
Where:
- ΔΦ = phase shift between elements
- d = element spacing (14mm)
- θ = steering angle
- λ = wavelength (~29mm at 10.3 GHz)

**Example**: 30° steering requires 87.4° phase shift

### Array Factor (Normalized)
```
AF(θ) = sin(N×π×d×sin(θ)/λ) / (N×sin(π×d×sin(θ)/λ))
```
Where N = number of elements (8)

### Beam Characteristics (8-element, λ/2 spacing)
- **HPBW**: 13° (half-power beamwidth)
- **FNBW**: 30° (first null beamwidth)
- **First Sidelobe**: -13.2 dB
- **Steering Range**: ±60° typical

---

## Hardware Specifications

### Antenna Array
- **Type**: Patch antenna with 4 sub-elements per element
- **Frequency Range**: 9.9-10.8 GHz (-3 dB bandwidth)
- **Element Spacing**: 14mm (0.48λ at 10.3 GHz)
- **Polarization**: Linear
- **ESD Protection**: Quarter-wave shorting stubs

### Frequency Synthesizer
- **LO Range**: 10.5-12.7 GHz
- **Reference**: External or on-board crystal
- **FMCW Capability**: 
  - Ramp time: 0.5 ms typical
  - Bandwidth: 500 MHz adjustable
  - Beat frequency: 6.7 kHz/meter

### System Interfaces
- **Digital Control**: 
  - SPI: ADAR1000, ADF4159
  - I2C: AD7291 monitor
  - GPIO: 3 lines for virtual array control
- **RF Connectors**:
  - SMP: Optional external antenna inputs
  - SMA: LO in/out, TX in/out

---

## Power Architecture

### Power Tree
```
USB-C (5V, 3A)
    ├── Raspberry Pi (via 40-pin header)
    └── CN0566 Power Management
        ├── LTC4217 (Hot swap controller)
        ├── LT8609S → 3.3V (Digital/RF)
        ├── ADP7158 → 3.3V (Beamformers/LNAs)
        ├── ADM7150 → 1.8V (Digital level shifters)
        ├── ADM7170 → VCO supply
        └── LT3460 + ADP7118 → 14V (AD8065)
```

### Power Consumption
- **Typical**: 12-15W total system
- **Peak**: 15W (3A @ 5V max)
- **Current Monitoring**: Via LTC4217 IMON output

---

## System Calibration

### Calibration Requirements
Compensates for multiple error sources:
- Element-to-element mismatch
- ADAR1000 gain/phase errors
- Dual ADAR1000 mismatch
- Receive path variations
- PlutoSDR channel mismatch

### Calibration Process

#### 1. Channel Calibration
- Measures ADAR1000-0 vs ADAR1000-1 mismatch
- Adjusts receive channel gains
- Stores compensation values

#### 2. Gain Calibration
- Measures individual element strengths
- Normalizes to weakest element
- Creates gain correction table
- **Result**: <0.5 dB element mismatch

#### 3. Phase Calibration
- Measures adjacent element phase differences
- Finds null positions (180° out-of-phase)
- Calculates compensation offsets
- **Result**: <2.8° phase accuracy

### Calibration Performance
- **Before**: 11.2 dB gain mismatch
- **After**: <0.51 dB gain mismatch
- **Phase Accuracy**: Limited by ADAR1000 resolution (2.8°)

---

## Performance Metrics

### Measured Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Frequency Range** | 10.0-10.5 GHz | X-band operation |
| **IF Frequency** | 2.2 GHz | To PlutoSDR |
| **Beam Steering** | ±60° | Typical range |
| **Phase Resolution** | 2.8° | ADAR1000 limitation |
| **Gain Control** | 31 dB range | 0.5 dB steps |
| **SFDR** | 56 dBc | System level |
| **Sample Rate** | 30 MSPS | PlutoSDR ADC |
| **Array Gain** | ~9 dB | 8-element theoretical |

### Beam Pattern Characteristics
- **Beamwidth Scaling**: HPBW ∝ λ/(N×d)
- **Sidelobe Suppression**: -13 dB (uniform), -58 dB (Blackman)
- **Grating Lobe Free Range**: d < λ/(1 + |sin(θ₀)|)

---

## Common Variations

### Horizontal Array Extension
- Stack multiple CN0566 boards side-by-side
- Requires common LO distribution
- Needs multi-channel synchronized SDR
- Achieves narrower azimuth beamwidth

### Single Channel Operation
- Combine multiple ADAR1000 outputs
- Use single ADC channel
- Loses monopulse/hybrid capabilities
- Simplifies system architecture

### External Antenna Support
- Connect via SMP connectors
- Frequency range: 8-14 GHz feasible
- Requires filter modifications
- Enables custom array geometries

### Alternative Frequency Plans
- Change LO frequency
- Modify filters accordingly
- Maintain 2.2 GHz IF for PlutoSDR compatibility

---

## Integration Considerations

### For Aleph Platform Integration

#### Critical Interfaces
1. **PlutoSDR Connection**
   - USB connection mandatory
   - 2.2 GHz IF input requirement
   - IIO framework support needed

2. **Digital Control**
   - SPI: 2 devices (ADAR1000s, ADF4159)
   - I2C: System monitoring (AD7291)
   - GPIO: 3 lines minimum
   - Level shifting: 3.3V/1.8V

3. **Power Requirements**
   - 5V @ 3A supply
   - Clean power for VCO/PLL
   - Hot-swap capability beneficial

#### Software Dependencies
- **Linux IIO Framework**: Core requirement
- **pyadi-iio**: Python control library
- **GNU Radio**: Optional but recommended
- **Python Libraries**: numpy, matplotlib
- **MATLAB Support**: Via IIO bindings

#### Mechanical Considerations
- Direct Raspberry Pi mounting design
- 40-pin header interconnect
- USB-C power entry
- Tripod mount included

### Migration Path from Raspberry Pi

#### Phase 1: Minimal Port
- PlutoSDR USB connection only
- Remote control via network
- Headless operation

#### Phase 2: Full Integration
- Direct SPI/I2C control
- Power management integration
- Custom software stack

#### Phase 3: Hardware Optimization
- Custom expansion board for SPI
- Integrated power solution
- Performance enhancements

---

## Key Takeaways

1. **Complete System**: Fully integrated phased array platform requiring only power and RF source
2. **Educational Focus**: Designed for learning and experimentation, not production
3. **Flexible Architecture**: Supports radar, communications, and imaging applications
4. **Calibration Critical**: Software calibration essential for beam accuracy
5. **Expansion Ready**: Can be scaled horizontally or modified for different frequencies
6. **Well Documented**: Extensive application notes, examples, and community support

---

*Document compiled from Analog Devices Circuit Note CN-0566, Rev. 0*
*Summary prepared for Aleph-Phaser integration project*
