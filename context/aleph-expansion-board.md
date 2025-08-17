# Aleph Drone Expansion Board - Technical Summary

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Core Architecture](#core-architecture)
3. [Sensor Suite](#sensor-suite)
4. [Electrical Specifications](#electrical-specifications)
5. [Connectivity and Interfaces](#connectivity-and-interfaces)
6. [Microcontroller Details](#microcontroller-details)
7. [Software Support](#software-support)
8. [Integration Potential for Phaser](#integration-potential-for-phaser)

---

## Executive Summary

### Product Overview
The **Aleph Drone Expansion Board (ES03)** is a versatile flight controller featuring dual microcontrollers (STM32H7 + RP2040) designed for drone and robotics applications with direct integration capability to the Aleph Carrier Board.

### Key Capabilities
- **Dual MCU Architecture**: STM32H7 (main) + RP2040 (debug/flash)
- **Flight Sensors**: Dual IMU with redundancy, barometer, magnetometer
- **I/O Rich**: 16× PWM, 8× GPIO, 3× UART, 2× CAN, I2C
- **Power Management**: 5-28V input with monitoring and protection
- **Development Friendly**: Built-in debugger/flasher via USB-C

### Primary Applications
- Drone flight control
- Robotics control systems
- Sensor data fusion
- Real-time control with high-level compute integration
- **Potential SPI bridge for Phaser integration**

---

## Core Architecture

### Dual Microcontroller Design
```
┌─────────────────────────────────────┐
│         STM32H7 (Main MCU)          │
│  • Cortex-M7 @ 480MHz               │
│  • Cortex-M4 @ 240MHz               │
│  • 2MB Flash, 1MB RAM               │
│  • Flight Control & Sensor Fusion   │
└─────────────┬───────────────────────┘
              │ UART/SWD
┌─────────────▼───────────────────────┐
│         RP2040 (Debug MCU)          │
│  • CMSIS-DAP Probe                  │
│  • USB-to-UART Bridge               │
│  • Watchdog Capability              │
│  • Pre-flashed with debugprobe     │
└─────────────────────────────────────┘
```

### Key Advantages
- **In-system Programming**: No external debugger needed
- **Real-time Monitoring**: RP2040 can monitor STM32 health
- **Development Efficiency**: Single USB-C for power, debug, and data

---

## Sensor Suite

### Flight Sensors

| Sensor Type | Model Options | Purpose |
|-------------|--------------|---------|
| **IMU** | BMI323 or BMI270 | 2× units for redundancy |
| **Barometer** | BMP581 | Altitude measurement |
| **Magnetometer** | BMM350 | Heading reference |

### Sensor Features
- **Redundant IMUs**: Communication redundancy for safety
- **High-Performance**: Latest generation MEMS sensors
- **Integrated Processing**: Sensor fusion on STM32H7

---

## Electrical Specifications

### Power System

| Parameter | Specification |
|-----------|--------------|
| **Input Voltage Range** | 5V - 28V |
| **Standard Power Consumption** | 3W |
| **Max Peripheral Power** | 15W |
| **Peripheral VDD** | 5V |
| **Logic Level** | 3.3V |

### Protection Features
- ✅ Reverse current protection
- ✅ Over-current protection
- ✅ ESD protection
- ✅ Voltage monitoring (VBAT-IN and regulated)
- ✅ Current monitoring on peripheral rail
- ✅ Switchable peripheral power rail

### Environmental
| Parameter | Value |
|-----------|-------|
| **Operating Temperature** | -25°C to +80°C |
| **ROHS Compliant** | Yes |
| **Vibration Qualification** | Contact manufacturer |

---

## Connectivity and Interfaces

### Communication Peripherals

| Interface | Quantity | Notes |
|-----------|----------|-------|
| **PWM** | 16 | Motor/servo control |
| **GPIO** | 8 | General purpose I/O |
| **UART** | 3 | Serial communication |
| **CAN** | 2 | Vehicle bus |
| **I2C** | 1 | Sensor bus |
| **SPI** | Not specified | **Likely available on STM32H7** |
| **USB** | FS (12 Mbps) | With Power Delivery |
| **MicroSD** | 1 | Data logging |

### Board-to-Board Interface
- Designed for direct connection to Aleph Carrier Board
- Enables tight coupling between:
  - Low-level control (STM32H7)
  - High-level autonomy (Jetson Orin NX)

### Status Indicators
- **7× LEDs**: Visual status feedback
- Useful for debugging and operational monitoring

---

## Microcontroller Details

### STM32H7 (Main Processor)

| Feature | Specification |
|---------|--------------|
| **Core 1** | ARM Cortex-M7 @ 480MHz |
| **Core 2** | ARM Cortex-M4 @ 240MHz |
| **Flash Memory** | 2MB |
| **RAM** | 1MB |
| **FRAM** | 16 Kbit |

### RP2040 (Debug Processor)
- **Function**: Debug probe and USB bridge
- **Firmware**: Pre-loaded debugprobe
- **Capabilities**:
  - CMSIS-DAP debugging
  - USB-to-UART conversion
  - STM32 watchdog monitoring
  - nRST control

### Programming Options
- **OpenOCD**: Via RP2040 debug probe
- **probe-rs**: Rust-based flashing tool
- **USB DFU**: Direct firmware update
- **SWD**: Serial Wire Debug interface

---

## Software Support

### Autopilot Firmware

| Platform | Status | Notes |
|----------|--------|-------|
| **Betaflight** | Pre-installed | Default firmware |
| **PX4** | Supported | Professional autopilot |
| **Roci** | Available | Elodin's control stack |
| **Custom** | Supported | Full development access |

### Development Environment
- Standard ARM toolchain support
- STM32CubeIDE compatible
- Arduino framework possible
- Real-time OS options (FreeRTOS, etc.)

---

## Integration Potential for Phaser

### As SPI Bridge Solution

The Aleph Drone Expansion Board could serve as the **critical SPI multiplexer** needed for full Phaser integration:

#### Available Resources
1. **STM32H7 SPI Capabilities**
   - Multiple SPI peripherals available
   - DMA support for high-speed transfers
   - Flexible pin mapping
   - Can implement custom chip select logic

2. **Processing Power**
   - 480MHz Cortex-M7 can handle SPI protocol translation
   - Dual-core allows dedicated SPI management
   - Real-time guarantees for timing-critical operations

3. **Communication to Carrier**
   - Board-to-board connector to Aleph Carrier
   - Multiple UART/CAN channels for data transfer
   - Could tunnel SPI over higher-level protocol

### Proposed Integration Architecture

```
Phaser (CN0566)
    │
    ├── ADF4159 (SPI) ──┐
    ├── ADAR1000 (SPI) ─┼──► Expansion Board (SPI Mux)
    └── AD7291 (I2C) ───┘         │
                                  │ B2B Connector
                           Aleph Carrier Board
                                  │
                           Jetson Orin NX SOM
```

### Implementation Strategy

#### Phase 1: SPI Bridge Mode
- Configure STM32H7 as SPI master for Phaser devices
- Implement protocol translation to Carrier Board
- Handle chip select emulation for devices without CS pins

#### Phase 2: Enhanced Integration
- Add real-time signal processing on STM32H7
- Implement data pre-processing before sending to Orin NX
- Utilize FRAM for configuration storage

#### Phase 3: Full System Integration
- Coordinate with flight control if used in drone applications
- Sensor fusion between Phaser radar and flight sensors
- Real-time obstacle avoidance using radar data

### Advantages of This Approach

1. **Solves SPI Challenge**: Provides multiple SPI interfaces with custom CS logic
2. **Level Shifting**: Can handle 3.3V Phaser to 1.8V Carrier translation
3. **Real-time Processing**: Offload time-critical tasks from Orin NX
4. **Development Flexibility**: Fully programmable solution
5. **Additional I/O**: Extra GPIO, UART, and PWM available

### Considerations

1. **Software Development**: Need custom firmware for SPI bridge
2. **Latency**: Additional hop in communication path
3. **Power**: Adds 3W to system power budget
4. **Mechanical**: Need to accommodate additional board

---

## Summary

The Aleph Drone Expansion Board presents a **viable solution** to the SPI interface challenge identified in the Phaser-Aleph integration project. Its powerful STM32H7 microcontroller, combined with flexible I/O and direct Carrier Board integration, makes it an ideal candidate for implementing the custom SPI multiplexer needed for full CN0566 control.

### Key Benefits for Phaser Project
- ✅ Multiple SPI interfaces available
- ✅ Real-time processing capability
- ✅ Already designed for Aleph ecosystem
- ✅ Level shifting capability
- ✅ Additional sensor fusion potential

### Next Steps
1. Verify STM32H7 SPI peripheral availability
2. Design SPI multiplexing firmware
3. Test communication latency
4. Develop protocol for Carrier-Expansion communication

---

*Document compiled from ES03 Aleph Drone Expansion Board Data Sheet, Rev 2.0.0, April 2025*
*Summary prepared for Aleph-Phaser integration project*
