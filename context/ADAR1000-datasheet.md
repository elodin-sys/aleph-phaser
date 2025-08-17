# ADAR1000 Datasheet - Technical Summary

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Key Specifications](#key-specifications)
3. [Functional Architecture](#functional-architecture)
4. [RF Signal Path](#rf-signal-path)
5. [Phase and Gain Control](#phase-and-gain-control)
6. [Digital Interface](#digital-interface)
7. [Power and Bias Control](#power-and-bias-control)
8. [Monitoring and Diagnostics](#monitoring-and-diagnostics)
9. [Operating Modes](#operating-modes)
10. [Integration Considerations](#integration-considerations)
11. [Phaser System Context](#phaser-system-context)

---

## Executive Summary

### Product Overview
The **ADAR1000** is a 4-channel, X-band and Ku-band beamforming core chip designed for phased array applications. It operates from 8 GHz to 16 GHz in half-duplex mode, providing both transmit and receive functionality with integrated phase and amplitude control.

### Key Capabilities
- **Frequency Range**: 8-16 GHz (X and Ku bands)
- **Channels**: 4 independent T/R channels
- **Phase Control**: 360° range with 2.8° resolution (7-bit)
- **Gain Control**: ≥31 dB range with ≤0.5 dB resolution (6-bit)
- **Operating Modes**: Half-duplex transmit/receive
- **Memory**: 121 beam position states
- **Package**: 88-terminal, 7mm × 7mm LGA

### Primary Applications
- Phased array radar systems
- Satellite communications
- 5G mmWave infrastructure
- Electronic warfare systems
- Beamforming antennas

---

## Key Specifications

### RF Performance

| Parameter | Specification | Notes |
|-----------|--------------|-------|
| **Frequency Range** | 8-16 GHz | X and Ku bands |
| **Gain Control Range** | ≥31 dB | Per channel |
| **Gain Resolution** | ≤0.5 dB | 6-bit control |
| **Phase Range** | 360° | Full rotation |
| **Phase Resolution** | 2.8° | 7-bit control (128 states) |
| **Noise Figure (RX)** | ~5 dB @ 10 GHz | Typical |
| **Input P1dB (RX)** | -15 dBm | Per channel |
| **Output P1dB (TX)** | +15 dBm | At RF_IO |

### Power Specifications

| Supply | Voltage | Current (Typ) | Notes |
|--------|---------|---------------|-------|
| **AVDD** | 3.3V | 240 mA (RX) / 280 mA (TX) | Analog supply |
| **DVDD** | 1.8V | 20 mA | Digital supply |
| **Operating Temp** | -40°C to +85°C | | Industrial range |

### Timing Specifications

| Parameter | Min | Typ | Max | Units |
|-----------|-----|-----|-----|-------|
| **SPI Clock** | - | - | 25 | MHz |
| **T/R Switch Time** | - | 1 | - | μs |
| **Memory Load Time** | - | 2 | - | μs |
| **Power-Up Time** | - | 100 | - | μs |

---

## Functional Architecture

### Block Diagram Structure
```
        RF_IO (Common Port)
              │
        ┌─────┴─────┐
        │  T/R Switch│
        └─────┬─────┘
              │
    ┌─────────┴─────────┐
    │                   │
  TX Path            RX Path
    │                   │
  4-Way              4-Way
  Splitter          Combiner
    │                   │
┌───┴───┬───┬───┐   ┌───┴───┬───┬───┐
CH1   CH2  CH3  CH4  CH1   CH2  CH3  CH4
 │     │    │    │    │     │    │    │
Phase/Gain Control   Phase/Gain Control
```

### Core Components per Channel
1. **Vector Modulator**: 360° phase control
2. **Variable Gain Amplifier**: 31 dB range
3. **T/R Switch**: Channel routing
4. **Power Detector**: -20 to +10 dBm range
5. **Bias Control**: External PA/LNA support

---

## RF Signal Path

### Receive Mode Operation
1. **Input**: Signals enter through CH1_RX to CH4_RX pins
2. **Amplification**: Variable gain amplifier per channel
3. **Phase Shift**: Vector modulator applies programmed phase
4. **Combining**: 4-way Wilkinson combiner
5. **Output**: Combined signal exits at RF_IO port

### Transmit Mode Operation
1. **Input**: Signal enters at RF_IO port
2. **Splitting**: 4-way Wilkinson splitter
3. **Phase Shift**: Vector modulator per channel
4. **Amplification**: Variable gain control
5. **Output**: Signals exit through CH1_TX to CH4_TX pins

### Key Path Characteristics
- **Insertion Loss**: ~8 dB typical (RX or TX)
- **Channel Isolation**: >25 dB
- **Amplitude Balance**: ±0.5 dB between channels
- **Phase Balance**: ±5° between channels

---

## Phase and Gain Control

### Phase Control Implementation
- **Technology**: I/Q vector modulator
- **Resolution**: 7-bit (128 states)
- **Step Size**: 2.8125° (360°/128)
- **Accuracy**: ±2° typical
- **Register**: Dedicated 7-bit register per channel

### Gain Control Implementation
- **Technology**: Digitally controlled attenuator + VGA
- **Resolution**: 6-bit (64 states)
- **Range**: ≥31 dB
- **Step Size**: ~0.5 dB
- **Accuracy**: ±0.25 dB typical

### Control Registers
```
Channel Control (per channel):
├── RX_GAIN[5:0]: 6-bit receive gain
├── RX_PHASE[6:0]: 7-bit receive phase
├── TX_GAIN[5:0]: 6-bit transmit gain
└── TX_PHASE[6:0]: 7-bit transmit phase
```

---

## Digital Interface

### SPI Configuration
- **Type**: 4-wire SPI (SCLK, SDI, SDO, CS)
- **Maximum Clock**: 25 MHz
- **Word Size**: 24-bit (8-bit address + 16-bit data)
- **Modes**: Single R/W, Streaming, Memory operations

### Addressing Scheme
- **Device Address**: 2 pins (ADDR0, ADDR1) for 4-device addressing
- **Register Space**: 8-bit addresses (0x00 to 0x3F)
- **Memory Space**: 121 beam positions (0x00 to 0x78)

### Control Pins
| Pin | Function | Description |
|-----|----------|-------------|
| **TR** | T/R Control | High=TX, Low=RX |
| **RX_LOAD** | RX Settings Load | Rising edge loads RX registers |
| **TX_LOAD** | TX Settings Load | Rising edge loads TX registers |
| **TR_SPI** | T/R via SPI | Enables SPI control of T/R |

### Multi-Chip Synchronization
- Common TR pin for array-wide T/R switching
- Shared LOAD pins for synchronized updates
- SPI daisy-chain capability
- Common LO distribution

---

## Power and Bias Control

### External Amplifier Support

#### PA Bias Control (4 channels)
- **Output Current**: Up to 100 mA per channel
- **Voltage**: Programmable 0-2V
- **DAC Resolution**: 6-bit
- **Protection**: Current limiting

#### LNA Bias Control (4 channels)  
- **Output Current**: Up to 8 mA per channel
- **Voltage**: Programmable 0-2V
- **DAC Resolution**: 4-bit
- **Enable/Disable**: Per channel control

### Power Management Modes
1. **Full Power**: All circuits active
2. **Standby**: Digital active, RF powered down
3. **Power Down**: Minimal current (<1 mA)
4. **Channel Disable**: Individual channel power-down

### Sequencing Requirements
1. Apply DVDD (1.8V)
2. Apply AVDD (3.3V)
3. Configure via SPI
4. Enable RF paths
5. Load beam settings

---

## Monitoring and Diagnostics

### Power Detectors
- **Quantity**: 4 (one per channel)
- **Range**: -20 to +10 dBm
- **Accuracy**: ±1 dB typical
- **Response Time**: <10 μs
- **Output**: Via internal 8-bit ADC

### Temperature Sensor
- **Range**: -40°C to +125°C
- **Resolution**: 1°C
- **Accuracy**: ±3°C
- **Output**: 8-bit ADC reading

### Internal ADC
- **Resolution**: 8-bit
- **Channels**: 5 (4 power detectors + temperature)
- **Conversion Time**: 2 μs
- **Interface**: SPI readback

### Diagnostic Features
- Lock detect for PLL monitoring
- Power-good indicators
- SPI readback verification
- Channel status monitoring

---

## Operating Modes

### Standard Beam Steering
- Manual phase/gain control via SPI
- Independent channel control
- Real-time updates via LOAD pins

### Memory Mode Operation
- 121 prestored beam positions
- 7-bit addressing
- Fast beam switching (<2 μs)
- Separate TX and RX states

### Fast Switching Mode
- Hardware TR pin control
- Sub-microsecond T/R switching
- Synchronized multi-chip operation
- Minimal SPI overhead

### Calibration Support
- Individual channel enable/disable
- Power detector readback
- Phase/gain sweep capability
- Temperature compensation data

---

## Integration Considerations

### For CN0566 Phaser System

#### Dual ADAR1000 Configuration
- **ADAR1000 #1**: Controls elements 1-4
- **ADAR1000 #2**: Controls elements 5-8
- **Synchronization**: Common TR and LOAD signals
- **Addressing**: Different ADDR pins for SPI

#### Interface Requirements
1. **SPI Bus**: Shared between both chips
2. **Control Signals**: TR, RX_LOAD, TX_LOAD
3. **Power**: 3.3V analog, 1.8V digital
4. **RF Connections**: To LNAs and antenna elements

#### Critical Design Points
- Phase matching between chips
- Amplitude balance across 8 channels
- Common LO distribution
- Thermal management

### Software Control via SPI

#### Basic Operation Sequence
```python
# 1. Initialize ADAR1000
write_register(INTERFACE_CONFIG, 0x18)  # Soft reset
write_register(CLOCK_CONFIG, 0x82)      # Enable clock

# 2. Configure channels
for channel in range(4):
    write_register(RX_GAIN[channel], gain_value)
    write_register(RX_PHASE[channel], phase_value)

# 3. Load settings
pulse_pin(RX_LOAD)  # Transfer to active registers

# 4. Enable receive mode
set_pin(TR, LOW)    # Set to receive mode
```

---

## Phaser System Context

### Role in CN0566
The ADAR1000 is the **core beamforming engine** in the Phaser system:
- Two chips provide 8-channel control
- Enables ±60° beam steering
- Provides 31 dB dynamic range
- Supports fast T/R switching for radar

### Integration Challenges
1. **SPI Access**: Requires dedicated SPI bus (no chip select)
2. **Timing**: Synchronization across dual chips
3. **Calibration**: Channel-to-channel matching
4. **Power**: Significant current draw (>500 mA total)

### Performance Impact
- **Beam Accuracy**: Limited by 2.8° phase resolution
- **Sidelobe Levels**: Affected by amplitude matching
- **Switching Speed**: 1 μs limits pulse repetition frequency
- **Dynamic Range**: 31 dB gain control enables AGC

### Aleph Integration Notes
- SPI control requires level shifting (3.3V to 1.8V)
- Memory mode could reduce SPI traffic
- Power detectors useful for calibration
- Temperature monitoring for drift compensation

---

## Key Takeaways

1. **Versatile Beamformer**: Complete 4-channel solution for phased arrays
2. **High Resolution**: 7-bit phase, 6-bit amplitude control
3. **Integrated Features**: Power detectors, temperature sensor, memory
4. **Fast Switching**: Sub-microsecond T/R transitions
5. **SPI Complexity**: No chip select requires dedicated bus
6. **Power Hungry**: ~1W per chip in operation
7. **Critical Component**: Essential for Phaser beamforming capability

---

*Document compiled from ADAR1000 Datasheet, Rev. B*
*Summary prepared for Aleph-Phaser integration project*
