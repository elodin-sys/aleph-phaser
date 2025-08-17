# Aleph-Phaser Integration Implementation Plan

## Project Overview

**Goal**: Demonstrate the CN0566 Phaser phased array platform running on the Aleph Flight Computer with NVIDIA Orin NX, showcasing significant compute advantages over Raspberry Pi while maintaining core beamforming functionality.

**Timeline**: 2-3 weeks  
**Approach**: Hybrid model (Phase A) - Raspberry Pi handles SPI/calibration, Aleph handles processing  
**Priority**: Speed of implementation over completeness

---

## Phase 1: Foundation and PlutoSDR Integration
**Duration**: 2-3 days  
**Objective**: Establish basic communication between Aleph and PlutoSDR

### Implementation Steps

#### 1.1 NixOS Environment Setup
- [ ] Review current `flake.nix` and `deploy.sh` structure
- [ ] Add PlutoSDR support packages to configuration:
  ```nix
  # Add to system packages
  - libiio
  - python3Packages.pyadi-iio
  - python3Packages.numpy
  - python3Packages.matplotlib
  ```
- [ ] Implement udev rules for PlutoSDR (from `pluto-sdr-integration-claude.md`)
- [ ] Create `plugdev` group and add user
- [ ] Deploy initial configuration to Aleph

#### 1.2 PlutoSDR Hardware Connection
- [ ] Connect PlutoSDR directly to Aleph USB-C port
- [ ] Verify USB enumeration: `lsusb | grep -E "0456|2fa2"`
- [ ] Check kernel module loading: `lsmod | grep -E "cdc_|rndis"`
- [ ] Verify network interface: `ip addr | grep 192.168.2`

#### 1.3 IIO Context Verification
- [ ] Test USB mode: `iio_info -s`
- [ ] Test network mode: `iio_info -u ip:192.168.2.1`
- [ ] Verify device attributes: `iio_info -u ip:192.168.2.1 | grep ad9361`
- [ ] Create simple Python test script:
  ```python
  import adi
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  print(f"Sample rate: {sdr.sample_rate}")
  ```

### Acceptance Criteria
- [x] PlutoSDR detected by Aleph without sudo
- [x] IIO context accessible via USB and network modes
- [x] Python can import adi and connect to PlutoSDR
- [x] Basic SDR parameters readable (sample rate, gain, etc.)

### References
- `context/pluto-sdr-integration-claude.md`
- `sources/pluto-sdr-aleph-integration.md`

---

## Phase 2: Phaser Control Interface
**Duration**: 2-3 days  
**Objective**: Establish control of Phaser hardware through hybrid approach

### Implementation Steps

#### 2.1 Network Configuration
- [ ] Ensure Aleph and Raspberry Pi are on same network
- [ ] Configure static IPs if needed:
  - Raspberry Pi: `phaser.local` or static IP
  - Aleph: Known IP for SSH access
- [ ] Test connectivity: `ping phaser.local` from Aleph
- [ ] Verify SSH access between systems if needed

#### 2.2 Port pyadi-iio CN0566 Support
- [ ] Install pyadi-iio with CN0566 support:
  ```bash
  pip install pyadi-iio
  ```
- [ ] Port `phaser_functions` module for calibration file loading
- [ ] Create test script for Phaser object creation:
  ```python
  import adi
  # Connect to Pi for Phaser control, PlutoSDR direct
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  phaser = adi.CN0566(uri="ip:phaser.local", sdr=sdr)
  phaser.configure(device_mode="rx")
  ```

#### 2.3 Calibration Integration
- [ ] Copy calibration files from Pi to Aleph (or access remotely)
- [ ] Test calibration loading:
  ```python
  phaser.load_channel_cal()
  phaser.load_gain_cal()
  phaser.load_phase_cal()
  ```
- [ ] Verify phase/gain control of individual elements

### Acceptance Criteria
- [x] Phaser object creation successful
- [x] Can set phase and gain for all 8 elements
- [x] Calibration files load without errors
- [x] No errors in `phaser.configure(device_mode="rx")`

### References
- `context/beamforming-example-claude.md`
- `sources/simple-beamforming-example.py`

---

## Phase 3: Basic Beamforming Demonstration
**Duration**: 2-3 days  
**Objective**: Demonstrate beam steering from -90° to +90°

### Implementation Steps

#### 3.1 Port Beamforming Example
- [ ] Adapt `simple-beamforming-example.py` for Aleph environment
- [ ] Modify network configurations:
  ```python
  rpi_ip = "ip:phaser.local"      # Pi for Phaser control
  sdr_ip = "ip:192.168.2.1"       # Direct USB to PlutoSDR
  ```
- [ ] Implement headless operation (save plots instead of display)
- [ ] Add logging for debugging

#### 3.2 Single Angle Test
- [ ] Set up HB100 signal source at known angle (e.g., 0°)
- [ ] Run single angle steering test
- [ ] Verify signal peak in FFT
- [ ] Save FFT plot: `plt.savefig('beam_0deg.png')`

#### 3.3 Beam Sweep Implementation
- [ ] Implement sweep from -90° to +90° in 10° steps
- [ ] Calculate phase deltas for each angle
- [ ] Apply phases to elements
- [ ] Record peak amplitude at each angle
- [ ] Generate beam pattern plot

### Acceptance Criteria
- [x] Single angle steering shows clear signal peak
- [x] Beam sweep completes without errors
- [x] Peak follows physical HB100 position
- [x] Beam pattern plot shows expected main lobe
- [x] Data saved for analysis (FFT plots, amplitude vs angle)

### Test Script
```python
# test_beamforming.py
import numpy as np
import adi
import matplotlib.pyplot as plt

# Initialize hardware
sdr = adi.ad9361(uri="ip:192.168.2.1")
phaser = adi.CN0566(uri="ip:phaser.local", sdr=sdr)
phaser.configure(device_mode="rx")
phaser.load_gain_cal()
phaser.load_phase_cal()

# Test single angle
angle = 30  # degrees
phase_delta = calculate_phase_delta(angle)
for i in range(8):
    phaser.set_chan_phase(i, i * phase_delta, apply_cal=True)

# Capture and plot
data = sdr.rx()
# ... FFT processing ...
plt.savefig(f'beam_{angle}deg.png')
print(f"Test complete: Angle {angle}°")
```

### References
- Lab exercises 1-3 from `context/phaser_lab_info.md`

---

## Phase 4: Lab Exercise Validation
**Duration**: 3-4 days  
**Objective**: Run multiple lab exercises to validate functionality

### Implementation Steps

#### 4.1 Lab Selection
Priority labs to implement:
1. [ ] Lab 1: SDR and Software Control
2. [ ] Lab 2: Steering Angle
3. [ ] Lab 3: Array Factor and Beamwidth
4. [ ] Lab 4: Sidelobes and Tapering
5. [ ] Lab 5: Grating Lobes (if time permits)

#### 4.2 Lab Adaptation
For each lab:
- [ ] Port Python code to headless operation
- [ ] Replace GUI elements with file output
- [ ] Create automated test sequences
- [ ] Document expected vs actual results

#### 4.3 Test Suite Creation
- [ ] Create `lab_tests/` directory
- [ ] Implement test script for each lab
- [ ] Create master test runner
- [ ] Generate results summary

### Acceptance Criteria
- [x] At least 3 labs running successfully
- [x] Results match expected values within tolerance
- [x] Automated test suite completes without intervention
- [x] Results documented with plots and data files

### References
- `context/phaser_lab_info.md`
- `sources/phaser_lab_instructions_june14_2022_no_title.docx`

---

## Phase 5: Performance Benchmarking
**Duration**: 2 days  
**Objective**: Demonstrate compute advantages of Aleph over Raspberry Pi

### Implementation Steps

#### 5.1 Baseline Measurements (on Pi)
- [ ] Time for single FFT computation
- [ ] Time for full beam sweep
- [ ] CPU utilization during processing
- [ ] Memory usage

#### 5.2 Aleph Performance Tests
- [ ] Same measurements on Aleph
- [ ] Test with larger buffer sizes
- [ ] Test with higher sample rates
- [ ] Parallel processing tests (if applicable)

#### 5.3 Advanced Processing Demo
- [ ] Implement real-time beam tracking
- [ ] Add signal processing enhancements:
  - Digital filtering
  - Averaging/integration
  - Peak detection algorithms
- [ ] Document processing that's infeasible on Pi

### Acceptance Criteria
- [x] Performance metrics documented in table
- [x] >5x speed improvement demonstrated
- [x] At least one advanced feature working
- [x] Clear documentation of advantages

### Benchmark Table Template
| Metric | Raspberry Pi 4 | Aleph Orin NX | Improvement |
|--------|---------------|---------------|-------------|
| FFT (1024 samples) | X ms | Y ms | Z× |
| Beam sweep (19 angles) | X s | Y s | Z× |
| Max sample rate | 30 MSPS | ?? MSPS | Z× |
| CPU usage @ 3 MSPS | X% | Y% | - |

---

## Phase 6: Documentation and Demo Package
**Duration**: 2 days  
**Objective**: Create comprehensive documentation and demo materials

### Implementation Steps

#### 6.1 README Creation
- [ ] Project overview and capabilities
- [ ] Hardware setup instructions
- [ ] Software installation guide
- [ ] Quick start examples
- [ ] Troubleshooting section

#### 6.2 Demo Scripts
- [ ] Create `demos/` directory with:
  - `demo_basic_steering.py`
  - `demo_beam_pattern.py`
  - `demo_performance.py`
- [ ] Add configuration files
- [ ] Include sample output/plots

#### 6.3 Video/Screenshot Documentation
- [ ] Record terminal session of demos
- [ ] Capture performance comparisons
- [ ] Generate beam pattern animations
- [ ] Create system architecture diagram

### Acceptance Criteria
- [x] README covers all essential topics
- [x] Demo scripts run without modification
- [x] New user can replicate setup in <1 hour
- [x] Clear evidence of success for stakeholders

---

## Stretch Goals (If Time Permits)

### GPU Acceleration Proof of Concept
- [ ] Investigate CUDA FFT implementation
- [ ] Port FFT processing to GPU
- [ ] Benchmark GPU vs CPU performance
- [ ] Document potential for ML integration

### FMCW Radar Demo
- [ ] Port Lab 10 FMCW radar code
- [ ] Implement range detection
- [ ] Create range vs time plot
- [ ] Demo object tracking

### Additional Labs
- [ ] Lab 6: Beam Squint
- [ ] Lab 7: Quantization Sidelobes
- [ ] Lab 8: Hybrid Beamforming
- [ ] Lab 9: Monopulse Tracking

---

## Risk Mitigation & Fallback Plans

### Risk 1: PlutoSDR Connection Issues
**Mitigation**: Use network mode (ip:192.168.2.1) if USB fails  
**Fallback**: Keep PlutoSDR connected to Pi, use network forwarding

### Risk 2: Phaser Control Failures
**Mitigation**: Extensive logging and debug output  
**Fallback**: Pre-configure Phaser settings on Pi, run static configs

### Risk 3: Performance Not Better Than Pi
**Mitigation**: Focus on capabilities Pi can't do (larger buffers, parallel processing)  
**Fallback**: Demonstrate potential with GPU acceleration path

### Risk 4: Time Constraints
**Mitigation**: Prioritize Phase 1-3 for minimum viable demo  
**Fallback**: Document path forward for remaining work

---

## Daily Checklist

### Day Start
- [ ] Check hardware connections
- [ ] Verify network connectivity
- [ ] Pull latest code changes
- [ ] Review previous day's notes

### During Development
- [ ] Commit code frequently
- [ ] Document issues/solutions
- [ ] Save test outputs/plots
- [ ] Update acceptance criteria

### Day End
- [ ] Push code to repository
- [ ] Update this plan with progress
- [ ] Note blockers for next day
- [ ] Backup any calibration files

---

## Success Metrics Summary

### Minimum Success (Week 1)
- PlutoSDR working with Aleph
- Basic beamforming demonstrated
- One complete beam sweep

### Target Success (Week 2)
- 3+ labs running
- Clear performance advantage shown
- Automated test suite

### Stretch Success (Week 3)
- GPU acceleration demo
- FMCW radar working
- 5+ labs complete

---

## Quick Reference Commands

```bash
# Deploy to Aleph
./deploy.sh

# Test PlutoSDR
iio_info -u ip:192.168.2.1

# SSH to Aleph
ssh user@aleph-ip

# SSH to Pi
ssh pi@phaser.local

# Monitor system
htop  # CPU usage
journalctl -f  # System logs

# Python test
python3 test_beamforming.py
```

---

## Notes Section
*Use this space to track daily progress, issues, and solutions*

### Day 1 Notes:
- 

### Day 2 Notes:
- 

### Day 3 Notes:
- 

---

*Document Version: 1.0*  
*Created: [Current Date]*  
*Last Updated: [Current Date]*
