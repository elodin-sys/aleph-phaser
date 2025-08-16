# CN0566 Phaser + Aleph Integration: Email Discussion Summary

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Participants](#key-participants)
3. [Timeline Summary](#timeline-summary)
4. [Technical Architecture](#technical-architecture)
5. [Integration Challenges](#integration-challenges)
6. [Proposed Solutions](#proposed-solutions)
7. [Resources and References](#resources-and-references)
8. [Action Items](#action-items)

---

## Project Overview

### Initial Vision
Partnership between Elodin (Aleph flight computer manufacturer) and Analog Devices to integrate the CN0566 Phaser development kit with the NVIDIA Jetson Orin NX-based Aleph flight computer, creating a powerful AI-capable radar platform.

### Core Objectives
- Replace Raspberry Pi with Aleph/Jetson Orin NX as the primary compute platform
- Leverage Orin NX's 100 TOPS AI performance for enhanced radar processing
- Enable both GUI and headless operation modes
- Maintain full Phaser functionality including calibration and beamforming

---

## Key Participants

| Name | Role | Organization | Key Contributions |
|------|------|--------------|-------------------|
| **Dan Driscoll** | CEO & Co-founder | Elodin | Project initiator, business lead |
| **Jon Kraft** | Technical Lead | Analog Devices | Phaser expert, ADI liaison |
| **Dave LoCascio** | Director of System Platforms | Analog Devices | Strategic ADI partnership |
| **Akhil Velagapudi** | Engineer | Elodin | Technical architecture, SPI interface expert |
| **Sascha Wise** | Engineer | Elodin | Implementation phases planning |
| **Krackson** | Developer | Elodin | NixOS image development |

---

## Timeline Summary

### April 9, 2025: Initial Contact
- Dan Driscoll reaches out to Jon Kraft expressing interest in Phaser
- Mentions educational value and potential for AI-enhanced radar applications
- Proposes partnership between Elodin's Aleph platform and ADI's Phaser

### April 9, 2025: Positive Response
- Jon Kraft expresses interest
- Teams call scheduled

### May 22, 2025: Kickoff Meeting
- Formal introduction with Dave LoCascio (ADI Director)
- Vision expanded to potentially include higher-performance ADI radar systems
- Phaser selected as initial proof of concept

### May 31, 2025: Technical Deep Dive
- Dan completes Phaser quickstart guide
- Identifies GUI requirements as primary challenge
- Aleph OS currently headless (optimized for professional use)
- Questions about SSH/headless operation capabilities
- Range inquiry: ~100m demonstrated for small drone targets

### June 2, 2025: Headless Operation Confirmed
- Jon confirms headless operation possible via PlutoSDR USB connection
- References GitHub examples: https://github.com/jonkraft/PhaserBeamforming
- Shares drone detection demo: https://youtu.be/M1eXeqN1c-I?t=445

### May 31, 2025 (Internal Discussion): Architecture Debate
- **Critical Technical Discovery**: SPI interface limitations
  - Two SPI devices need connection: ADF4159 and ADAR1000
  - Aleph doesn't expose Jetson SPI peripherals through connectors
  - Custom expansion board with SPI mux required for full integration
- **Phased Approach Proposed**:
  - Phase 1-2: Keep Pi for SPI/calibration, Aleph for GNU Radio/PlutoSDR
  - Phase 3: Full Pi replacement with custom expansion board
- Headless operation confirmed viable via pyadi-iio library

### June 30, 2025: Hardware Order
- Jon Kraft orders Aleph Flight Computer (variant 50127470690602)
- Developer begins integration work

---

## Technical Architecture

### Current Phaser Stack (with Raspberry Pi)
```
┌─────────────────┐
│   Phaser Board  │
│  ┌───────────┐  │
│  │  ADF4159  │◄─┼──SPI──┐
│  │   (PLL)   │  │       │
│  └───────────┘  │       │
│  ┌───────────┐  │       │
│  │ ADAR1000  │◄─┼──SPI──┤
│  │(Beamform) │  │       │
│  └───────────┘  │       │
└─────────────────┘       │
                          │
┌─────────────────┐       │
│   PlutoSDR      │       │
│  (ADALM-PLUTO)  │◄──USB─┤
└─────────────────┘   +   │
                  Ethernet│
                          │
                   ┌──────▼──────┐
                   │ Raspberry Pi│
                   │   - GUI     │
                   │   - Control │
                   └─────────────┘
```

### Proposed Aleph Integration Phases

#### Phase 1-2: Hybrid Approach
```
Phaser Board ◄──SPI──► Raspberry Pi (calibration only)
     │
     └──USB/Ethernet──► PlutoSDR ◄──USB──► Aleph (GNU Radio, processing)
```

#### Phase 3: Full Integration (requires custom expansion board)
```
Phaser Board ◄──SPI Mux──► Custom Expansion ◄──B2B──► Aleph
     │
     └──USB/Ethernet──► PlutoSDR ◄──USB──► Aleph
```

---

## Integration Challenges

### 1. SPI Interface Access
- **Problem**: Phaser requires SPI control of ADF4159 (PLL) and ADAR1000 (beamformer)
- **Root Cause**: 
  - Aleph doesn't expose Jetson SPI peripherals through external connectors
  - ADI chips lack standard SPI chip select pins
  - Multiple SPI buses need multiplexing to single interface
- **Impact**: Cannot achieve full Pi replacement without hardware modification

### 2. Operating System Differences
- **Problem**: Aleph runs headless NixOS, Phaser designed for Raspberry Pi OS with GUI
- **Considerations**:
  - GUI packages (GNOME, VNC) need to be added to Aleph image
  - Matplotlib and Thonny IDE support needed for labs
  - Trade-off between professional headless use and educational GUI needs

### 3. Software Stack Port
- **Components to Port**:
  - GNU Radio integration
  - pyadi-iio library
  - CN0566 Python control libraries
  - Calibration routines

---

## Proposed Solutions

### Immediate Path (Phases 1-2)
1. **Headless Operation Focus**
   - Utilize existing pyadi-iio minimal example
   - Reference: `https://github.com/analogdevicesinc/pyadi-iio/blob/cn0566_dev/examples/cn0566/cn0566_minimal_example.py`
   - SSH + matplotlib for remote visualization

2. **Hybrid Configuration**
   - Keep Pi for SPI control and calibration
   - Connect PlutoSDR directly to Aleph for signal processing
   - Leverage Orin NX compute for AI/ML applications

### Long-term Solution (Phase 3)
1. **Custom Expansion Board Development**
   - Design SPI multiplexer board
   - Utilize B2B connector on Aleph
   - Enable full Pi replacement

2. **Complete Software Stack**
   - Full NixOS package for Phaser support
   - Optional GUI overlay for educational use
   - Maintain headless operation for professional applications

---

## Resources and References

### GitHub Repositories
- **Phaser Beamforming Examples**: https://github.com/jonkraft/PhaserBeamforming
- **pyadi-iio Library**: https://github.com/analogdevicesinc/pyadi-iio
  - Specific CN0566 branch: `/blob/cn0566_dev/examples/cn0566/`

### Documentation
- **CN0566 Circuit Note**: Available in sources
- **Phaser Lab Instructions**: June 14, 2022 version available
- **Video Demos**: 
  - Drone detection at 100m: https://youtu.be/M1eXeqN1c-I?t=445

### Hardware Links
- **Aleph Flight Computer**: https://shop.elodin.systems/products/aleph-flight-computer
  - Specific variant ordered: 50127470690602

---

## Action Items

### Completed
- [x] Initial partnership discussions (Dan, Jon)
- [x] Quickstart guide evaluation (Dan)
- [x] Hardware order placed (Jon - June 30, 2025)
- [x] Developer assigned to integration (mentioned June 30)

### In Progress
- [ ] NixOS image development for Phaser support
- [ ] PlutoSDR to Aleph direct connection testing
- [ ] Headless operation workflow documentation

### Future Work
- [ ] Custom expansion board design for SPI mux
- [ ] Full calibration routine port to Aleph
- [ ] GUI overlay package for educational use
- [ ] Performance benchmarking vs Raspberry Pi
- [ ] AI/ML demo applications leveraging Orin NX

---

## Key Technical Insights

1. **Calibration is not continuously required** - SPI interface primarily needed during setup
2. **Headless operation is viable** - pyadi-iio supports full functionality without GUI
3. **Computational upgrade significant** - Orin NX offers ~100 TOPS vs Pi's limited compute
4. **Phased approach practical** - Can deliver value in stages while working toward full integration
5. **Educational vs Professional trade-offs** - Need to balance GUI requirements with embedded optimization

---

## Next Steps for Engineering Team

1. **Immediate Priority**: Get PlutoSDR communicating with Aleph via USB
2. **Secondary**: Port pyadi-iio and dependencies to NixOS
3. **Testing**: Validate GNU Radio pipeline on Aleph
4. **Documentation**: Create migration guide from Pi to Aleph
5. **Long-term**: Spec out custom expansion board requirements

---

*Document compiled from email chain dated April 9 - June 30, 2025*
*Last updated: Analysis of original project emails*
