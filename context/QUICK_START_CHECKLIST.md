# Aleph-Phaser Quick Start Checklist

## Current Status (Dec 4, 2024)
- [x] **Phase 1 COMPLETE**: PlutoSDR working on Aleph
- [x] **Phase 2 COMPLETE**: Phaser/Pi accessible at 192.168.4.184
- [x] **Phase 3 COMPLETE**: Minimal example running
- [x] **Phase 4 COMPLETE**: Beam steering demo working
- [x] **Phase 5 COMPLETE**: Lab exercises (3 & 4) ported
- [x] **Phase 6 COMPLETE**: Benchmarks run (FFT: 0.036ms, sweep: 3.2s)
- [x] **Phase 7 COMPLETE**: Documentation updated

## Connection Details
| Device | Address | User |
|--------|---------|------|
| Aleph | 192.168.4.181 | aleph-phaser |
| PlutoSDR | 192.168.2.1 | (via USB-Ethernet) |
| Phaser/Pi | phaser.local | analog (password: analog) |

## Pre-Flight Checklist

### Hardware Setup
- [x] Aleph Carrier Board (ES02) powered and accessible
- [x] Orin NX module properly seated
- [x] WiFi connected (192.168.4.181)
- [x] PlutoSDR connected to Aleph USB-C
- [ ] Phaser + Raspberry Pi powered and on network ⚠️ NEEDED
- [ ] HB100 signal source with fresh battery

### Software Prerequisites
- [x] MacBook Pro development environment ready
- [x] SSH access to Aleph verified: `ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.181`
- [ ] SSH access to Pi verified: `ssh analog@phaser.local`, password "analog" ⚠️ NEEDED
- [x] Git repository cloned and up to date
- [x] `deploy.sh` script tested and working

---

## Phase 1 Quick Tests

### After NixOS Deployment
```bash
# On Aleph:
groups  # Should show: plugdev dialout
lsusb | grep -E "0456|2fa2"  # Should show PlutoSDR
iio_info -s  # Should list PlutoSDR context
python3 -c "import adi; print('Success!')"
```

### PlutoSDR Connection Test
```python
# save as test_pluto.py
import adi
sdr = adi.ad9361(uri="ip:192.168.2.1")
print(f"Sample rate: {sdr.sample_rate}")
print(f"RX LO: {sdr.rx_lo}")
print("PlutoSDR connection successful!")
```

---

## Phase 2 Quick Tests

### Phaser Connection Test
```python
# save as test_phaser.py
import adi
sdr = adi.ad9361(uri="ip:192.168.2.1")
phaser = adi.CN0566(uri="ip:phaser.local", sdr=sdr)
print("Phaser object created successfully!")
phaser.configure(device_mode="rx")
print("Phaser configured for RX mode!")
```

---

## Phase 3 Quick Tests

### Single Angle Beam Test
```python
# save as test_single_beam.py
import adi
import numpy as np

sdr = adi.ad9361(uri="ip:192.168.2.1")
phaser = adi.CN0566(uri="ip:phaser.local", sdr=sdr)
phaser.configure(device_mode="rx")

# Set all elements to 0 phase
for i in range(8):
    phaser.set_chan_phase(i, 0)
    
print("Beam set to broadside (0°)")

# Capture data
sdr.rx_buffer_size = 1024
data = sdr.rx()
print(f"Captured {len(data[0])} samples")
```

---

## Common Issues & Quick Fixes

### PlutoSDR Not Found
```bash
# Check USB connection
lsusb
# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
# Try network mode instead
iio_info -u ip:192.168.2.1
```

### Permission Denied
```bash
# Add user to groups (requires logout/login)
sudo usermod -a -G plugdev,dialout $USER
```

### Network Connection to Pi Failed
```bash
# From Aleph:
ping phaser.local
# If fails, find Pi IP:
nmap -sn 192.168.1.0/24  # Adjust subnet as needed
```

### Python Import Errors
```bash
# Reinstall pyadi-iio
pip install --upgrade pyadi-iio
# Check Python path
python3 -c "import sys; print(sys.path)"
```

---

## Performance Quick Tests

### FFT Benchmark
```python
import time
import numpy as np

data = np.random.randn(1024) + 1j*np.random.randn(1024)
start = time.time()
for _ in range(1000):
    fft = np.fft.fft(data)
elapsed = time.time() - start
print(f"1000 FFTs in {elapsed:.3f} seconds")
print(f"Average: {elapsed/1000*1000:.3f} ms per FFT")
```

### Memory Check
```bash
free -h  # Check available memory
htop    # Monitor CPU and memory usage
```

---

## Data Validation Checks

### Beam Pattern Validation
Expected values for 8-element array at 10.3 GHz:
- HPBW: ~13° (half-power beamwidth)
- First sidelobe: ~-13 dB
- Steering range: ±60° typical

### Phase Delta Calculation
```python
import numpy as np

freq = 10.3e9  # Hz
c = 3e8  # m/s
d = 0.014  # 14mm element spacing
angle = 30  # degrees

wavelength = c / freq
phase_delta = 360 * d * np.sin(np.radians(angle)) / wavelength
print(f"Phase delta for {angle}°: {phase_delta:.1f}°")
# Expected: ~87.4° for 30°
```

---

## Daily Progress Tracker

### Day 1 (Dec 4, 2024) - ALL PHASES COMPLETE
- [x] Phase 1.1 Complete (NixOS setup) - Fixed pylibiio for nixpkgs 25.05
- [x] Phase 1.2 Complete (PlutoSDR hardware) - USB detected, network mode working
- [x] Phase 1.3 Complete (IIO verification) - Python imports working
- [x] Phase 2 Complete - Phaser/Pi at 192.168.4.184
- [x] Phase 3 Complete - aleph_minimal_example.py working
- [x] Phase 4 Complete - aleph_beam_steering.py working
- [x] Phase 5 Complete - aleph_lab_exercises.py (Lab 3 & 4)
- [x] Phase 6 Complete - Benchmarks: FFT 0.036ms, sweep 3.2s
- [x] Phase 7 Complete - README and docs updated

### Hardware Notes
- Pi IP: 192.168.4.184 (use this instead of phaser.local on Aleph)
- PlutoSDR: ip:192.168.2.1 (direct USB connection)
- HB100: Turn on and aim at array to see signal

### Day 4-5
- [ ] Phase 3.1 Complete (Port beamforming)
- [ ] Phase 3.2 Complete (Single angle test)
- [ ] Phase 3.3 Complete (Beam sweep)

### Day 6-8
- [ ] Phase 4 Complete (Lab exercises)

### Day 9-10
- [ ] Phase 5 Complete (Benchmarking)
- [ ] Phase 6 Complete (Documentation)

---

## Emergency Recovery

### Aleph Recovery
```bash
# If Aleph won't boot, use serial console
screen /dev/tty.usbserial 115200

# Rollback NixOS generation
nixos-rebuild switch --rollback
```

### Repository Recovery
```bash
# Revert to last known good
git log --oneline
git checkout <good-commit-hash>
```

### Hardware Reset
1. Power cycle Aleph (wait 10 seconds)
2. Power cycle PlutoSDR
3. Power cycle Phaser/Pi
4. Reconnect in order: Pi → Phaser → PlutoSDR → Aleph

---

## Contact for Help

### Documentation References
- PlutoSDR: `context/pluto-sdr-integration.md`
- Beamforming: `context/beamforming-example.md`
- Hardware: `context/cn0566-circuit-note.md`

### Online Resources
- Analog Devices EngineerZone
- NixOS Discourse
- pyadi-iio GitHub Issues

---

*Keep this checklist handy during development!*
