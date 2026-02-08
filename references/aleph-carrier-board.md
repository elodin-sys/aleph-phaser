# Aleph Carrier Board - Technical Summary

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Physical Specifications](#physical-specifications)
3. [Environmental Capabilities](#environmental-capabilities)
4. [Electrical Specifications](#electrical-specifications)
5. [Connectivity and Interfaces](#connectivity-and-interfaces)
6. [Board-to-Board Connector Pinout](#board-to-board-connector-pinout)
7. [SOM Compatibility](#som-compatibility)
8. [Software Support](#software-support)
9. [Critical Integration Points](#critical-integration-points)

---

## Executive Summary

### Product Overview
The **Aleph Carrier Board (ES02)** is a space-grade flight computer designed to house NVIDIA Jetson Orin NX/Nano SOMs for high-performance computing in extreme environments.

### Key Capabilities
- **AI Performance**: Up to 157 TOPS with Orin NX 16GB
- **Operating Range**: -45°C to +85°C
- **Form Factor**: Ultra-compact 89 × 53.5 × 19.3 mm
- **Power**: 5-20V input, 10W idle, 40W peak
- **Interfaces**: Comprehensive I/O including PCIe 4.0, USB-SS+, GigE
- **Space-Ready**: Low outgassing materials selected

### Primary Applications
- On-orbit compute and AI processing
- Real-time image processing
- Autonomous decision-making
- UAV/drone flight control
- Edge AI deployments

---

## Physical Specifications

### Mechanical Dimensions
| Dimension | Value |
|-----------|-------|
| **Length** | 89 mm |
| **Width** | 53.5 mm |
| **Height** | 19.3 mm |
| **PCB Material** | Isola 370HR |
| **Surface Finish** | ENIG |

### Form Factor Features
- Compact design optimized for space-constrained applications
- Board-to-board expansion capability
- M.2 slots for storage and wireless expansion
- Integrated mounting points

---

## Environmental Capabilities

### Operating Conditions
| Parameter | Specification |
|-----------|--------------|
| **Temperature Range** | -45°C to +85°C |
| **ROHS Compliance** | Yes |
| **Vibration Qualification** | Contact manufacturer |
| **Outgassing** | Low outgassing materials |

### Space-Grade Features
- Components selected for radiation tolerance
- Materials chosen for low outgassing
- Wide temperature operation
- Vibration and shock resistant design

---

## Electrical Specifications

### Power Requirements
| Parameter | Value |
|-----------|-------|
| **Input Voltage Range** | 5V - 20V |
| **Power Consumption (Idle)** | 10W |
| **Power Consumption (Peak)** | 40W |
| **Power Delivery** | USB-PD capable |

### Power Distribution
- Multiple power domains for efficiency
- USB Power Delivery support on select ports
- Integrated power management
- Battery backup support (PMIC_BBAT pin)

---

## Connectivity and Interfaces

### High-Speed Interfaces

#### PCIe Connectivity
- **M.2 M-Key (J7)**: PCIe 4.0 x4
- **M.2 E-Key (J6)**: PCIe 4.0 x1 + USB HS + I2C + UART
- **B2B Connector**: 2× PCIe 4.0 x1

#### USB Interfaces
| Connector | Type | Speed | Features |
|-----------|------|-------|----------|
| **J8** | USB-C | Debug | Serial Debug + PD |
| **J9** | USB-C | USB-SS+ (10 Gbps) | PD + DisplayPort Alt |
| **J10** | USB-C | USB-SS+ (10 Gbps) | Standard |
| **B2B** | Internal | USB-SS (5 Gbps) | Via J3 connector |

### Communication Interfaces

#### Serial Protocols
- **I2C**: 3 buses total
  - 2× via B2B (3.3V VDDIO)
  - 1× via M.2 E-Key
- **SPI**: 1 bus (1.8V VDDIO) with 2 chip selects
- **UART**: 2 channels
  - 1× via B2B (1.8V VDDIO)
  - 1× via M.2 E-Key
- **CAN**: TTL level (3.3V VDDIO)

#### Network
- **Gigabit Ethernet**: Full GbE with LED indicators
- **MDI Pairs**: 4 differential pairs (MDI0-MDI3)

### Camera/Display
- **CSI-2 Interfaces (J1, J2)**: 2× 22-pin MIPI
- **DisplayPort**: Via USB-C J9 Alt mode
- **Compatibility**: Similar to Raspberry Pi 5 camera interface

### Control and Debug
- **GPIO**: 6 pins (1.8V VDDIO)
- **Reset Button (SW3)**: System reset
- **Force Recovery (SW2)**: Boot mode selection
- **Serial Debug**: Via USB-C J8

---

## Board-to-Board Connector Pinout

### Samtech ERF5-050 100-Pin Connector (J3)

#### Power Pins
- **EXP-VDD**: Pins 86, 88, 90, 92, 94, 96, 98, 100
- **GND**: Multiple pins throughout
- **PMIC_BBAT**: Pin 82

#### PCIe Lanes
| Signal | Pins | Description |
|--------|------|-------------|
| **PCIe2** | 6-17 | Full x1 lane with clock |
| **PCIe3** | 3-5, 18-20 | Full x1 lane with clock |
| **Control** | 21-28 | Reset, CLKREQ, Wake |

#### High-Speed USB
| Signal | Pins | Description |
|--------|------|-------------|
| **USB-SS1** | 66, 70, 72, 91 | 5 Gbps differential |
| **EXP-USB1** | 58, 60, 64 | Additional USB |

#### Ethernet MDI
- **MDI0**: Pins 43-45
- **MDI1**: Pins 42, 44
- **MDI2**: Pins 49, 51
- **MDI3**: Pins 48, 50
- **LED Control**: Pins 54-55

#### Communication Buses
| Interface | Pins | Voltage |
|-----------|------|---------|
| **I2C0** | 71, 73 | 3.3V |
| **I2C1** | 77, 79 | 3.3V |
| **SPI0** | 59, 61, 63, 65, 67 | 1.8V |
| **UART1** | 37, 39 | 1.8V |
| **CAN** | 76, 78 | 3.3V |

#### GPIO and Control
- **GPIO Pins**: 29, 31-34, 36 (1.8V)
- **Spare Pins**: 83-84

---

## SOM Compatibility

### Supported NVIDIA Jetson Modules

| Module | AI TOPS | GPU Cores | CPU | Memory | DLA | PVA |
|--------|---------|-----------|-----|--------|-----|-----|
| **Orin NX 16GB** | 157 | 1024 @ 1173MHz | 8-core A78AE @ 2GHz | 16GB LPDDR5 | 2× | 1× |
| **Orin NX 8GB** | 117 | 1024 @ 1173MHz | 6-core A78AE @ 2GHz | 8GB LPDDR5 | 1× | 1× |
| **Orin Nano 8GB** | 67 | 1024 @ 1020MHz | 6-core A78AE @ 1.7GHz | 8GB LPDDR5 | - | - |

### Module Interface
- **Connector**: 260-position SODIMM
- **Compatibility**: Full NVIDIA design guideline compliance
- **Storage**: External NVMe support via M.2
- **Cooling**: Fan connector (J4) for active cooling

---

## Software Support

### Operating Systems
| OS | Status | Notes |
|----|--------|-------|
| **NixOS** | Pre-installed | Default Elodin configuration |
| **JetPack** | Supported | NVIDIA official SDK |
| **Yocto** | Supported | Custom embedded Linux |

### Software Stack Options
- **Elodin Flight Software**: Open-source modules available
- **Custom Mission Software**: Fully user-definable
- **AI Frameworks**: Full CUDA/TensorRT support via JetPack

---

## Critical Integration Points

### For Phaser Integration

#### Available Interfaces for CN0566
1. **USB Connection**
   - USB-SS+ ports for PlutoSDR
   - Multiple USB-C connectors available
   - Power delivery capability

2. **SPI Access Challenge**
   - Only 1 SPI bus exposed via B2B
   - 1.8V logic levels (needs level shifting for 3.3V Phaser)
   - 2 chip selects available
   - **Issue**: Phaser needs 2 SPI devices without chip select

3. **I2C Availability**
   - 3 buses total (sufficient for AD7291 monitoring)
   - 3.3V logic compatible

4. **GPIO Resources**
   - 6 GPIO pins at 1.8V
   - Sufficient for virtual array control
   - Level shifting required for 3.3V compatibility

### Power Considerations
- Can provide 5V @ 3A via USB-C (meets Phaser requirements)
- Wide input voltage range allows flexible power solutions
- 40W peak capacity sufficient for Phaser + Orin NX

### Mechanical Integration
- B2B connector enables custom expansion board
- Compact form factor compatible with drone/flight applications
- M.2 slots available for additional peripherals

### Software Requirements
- Linux IIO framework support needed
- GNU Radio compatibility required
- Python environment for pyadi-iio
- Network stack for remote operation

### Expansion Board Requirements
For full Phaser integration, custom expansion board needs:
1. **SPI Multiplexer**: Handle multiple SPI devices without chip select
2. **Level Shifters**: 1.8V ↔ 3.3V conversion
3. **Power Distribution**: 5V @ 3A to Phaser
4. **Physical Interface**: 40-pin header or equivalent

---

## Key Advantages for Phaser Project

1. **Compute Power**: 100-157 TOPS vs Raspberry Pi's limited performance
2. **Industrial Grade**: -45°C to +85°C operation
3. **Flexible I/O**: Multiple high-speed interfaces available
4. **Compact Design**: Smaller than Pi + Phaser stack
5. **Professional Platform**: Space-grade reliability

## Integration Challenges

1. **SPI Limitation**: Need custom expansion for full SPI access
2. **Level Shifting**: 1.8V GPIO vs 3.3V Phaser logic
3. **Software Port**: NixOS vs Raspberry Pi OS differences
4. **Connector Adaptation**: B2B vs 40-pin header interface

---

*Document compiled from ES02 Aleph Carrier Board Data Sheet, Rev 2.0.0, April 2025*
*Summary prepared for Aleph-Phaser integration project*
