# Aleph-Phaser Integration

Demonstrate the Analog Devices CN0566 Phaser development kit running on the Elodin Aleph (NVIDIA Orin NX 16GB) using a hybrid architecture.

## Status: ✅ COMPLETE (Dec 5, 2024)

All phases successfully implemented:
- Phase 1: PlutoSDR integration ✅
- Phase 2: Phaser network control ✅
- Phase 3: Minimal example demo ✅
- Phase 4: Beam steering demo ✅
- Phase 5: Lab exercises ✅
- Phase 6: Performance benchmarks ✅
- Phase 7: Documentation ✅
- **Phase 8: GPU-Accelerated Demos ✅** (NEW)
  - Range-Doppler processing at 30+ FPS
  - GPU CFAR detection (10-100x speedup)
  - Micro-Doppler for drone detection

## Architecture

```
┌─────────────────────┐     USB-C      ┌─────────────────┐
│  Aleph Orin NX      │◄──────────────►│    PlutoSDR     │
│  (192.168.4.181)    │                │  (192.168.2.1)  │
│                     │                └─────────────────┘
│  - Data processing  │
│  - FFT/beamforming  │     WiFi       ┌─────────────────┐
│  - Python/pyadi-iio │◄──────────────►│  Raspberry Pi   │
└─────────────────────┘  (192.168.4.184)                 │
                                       │  - SPI control  │
                                       │  - ADAR1000 x2  │
                                       │  - ADF4159 PLL  │
                                       └─────────────────┘
```

## Performance Results

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| FFT (1024 samples) | 0.036 ms | <1 ms | ✅ |
| FFT (8192 samples) | 0.235 ms | <5 ms | ✅ |
| Beam sweep (25 angles) | 3.2 s | <5 s | ✅ |
| Memory available | 14 GB | - | ✅ |

**Platform**: NVIDIA Orin NX 16GB @ Linux 5.10.216

## Quick Start

### 1. Deploy to Aleph

```bash
# Add SSH key
ssh-add ssh/aleph-phaser

# Deploy NixOS configuration
./deploy.sh -h 192.168.4.181 -u aleph-phaser
```

### 2. Verify Hardware

```bash
# SSH to Aleph
ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.181

# Test PlutoSDR
iio_info -u ip:192.168.2.1

# Test Phaser (Pi must be on network)
iio_info -u ip:192.168.4.184

# Python test
python3 -c "import adi; print(adi.ad9361(uri='ip:192.168.2.1').sample_rate)"
```

### 3. Run Demos

Demo scripts are automatically deployed to `/opt/phaser/scripts/` on the Aleph:

```bash
# SSH to Aleph
ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.181

# CPU Demos (work immediately after deploy)
python3 /opt/phaser/scripts/cpu-demos/aleph_minimal_example.py --output-dir /tmp/output
python3 /opt/phaser/scripts/cpu-demos/aleph_beam_steering.py --output-dir /tmp/output
python3 /opt/phaser/scripts/cpu-demos/aleph_benchmark.py --output-dir /tmp/output

# GPU Demos (require CuPy for full acceleration)
python3 /opt/phaser/scripts/gpu-demos/run_gpu_demo.py --output-dir /tmp/gpu_results
```

## Hardware Requirements

- **Aleph Carrier Board** (ES02) with NVIDIA Orin NX 16GB
- **PlutoSDR** (ADALM-PLUTO) - connected to Aleph USB-C
- **CN0566 Phaser Kit** - includes Raspberry Pi, Phaser board, HB100
- **Network** - Aleph and Pi on same WiFi network

## Connection Details

| Device | Address | Connection |
|--------|---------|------------|
| Aleph | 192.168.4.181 | WiFi (wlan0) |
| PlutoSDR | 192.168.2.1 | USB-Ethernet (enu1) |
| Phaser/Pi | 192.168.4.184 | WiFi |
| Pi SSH | analog@192.168.4.184 | Password: analog |

## Demo Scripts

### GPU-Accelerated Demos (Orin NX Showcase)

These demos showcase radar processing capabilities **impractical on Raspberry Pi**:

| Script | Description | Key Feature |
|--------|-------------|-------------|
| `gpu-demos/gpu_benchmark.py` | Full performance comparison | 10-100x speedup vs Pi4 |
| `gpu-demos/gpu_range_doppler.py` | Range-Doppler maps | 30+ FPS @ 256K samples |
| `gpu-demos/gpu_cfar.py` | GPU CFAR detection | <1ms for 64K samples |
| `gpu-demos/gpu_micro_doppler.py` | Drone detection | Micro-Doppler spectrograms |
| `gpu-demos/run_gpu_demo.py` | Complete demo suite | All demos + report |

**Run GPU demos on Aleph:**
```bash
ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.181
cd /opt/phaser/scripts/gpu-demos

# Full demo suite with synthetic data
python3 run_gpu_demo.py --output-dir /tmp/gpu_results

# Individual demos
python3 gpu_benchmark.py --output-dir /tmp/results
python3 gpu_range_doppler.py --output-dir /tmp/results
python3 gpu_micro_doppler.py --output-dir /tmp/results
```

Note: Demos automatically use GPU (CuPy) when available, otherwise fall back to CPU (NumPy).

### CPU Demos (run on Aleph)

| Script | Description | Requirements |
|--------|-------------|--------------|
| `cpu-demos/sdr_basic_capture.py` | Basic PlutoSDR capture | PlutoSDR only |
| `cpu-demos/test_phaser_connection.py` | System connectivity test | Full system |
| `cpu-demos/aleph_minimal_example.py` | HB100 signal detection | Full system + HB100 |
| `cpu-demos/aleph_beam_steering.py` | Beam sweep and pattern | Full system |
| `cpu-demos/aleph_lab_exercises.py` | Lab 3 & 4 exercises | Full system |
| `cpu-demos/aleph_benchmark.py` | Performance benchmarks | Full system |

### Qt GUI (run on Mac)

| Script | Radar Type | Description |
|--------|------------|-------------|
| `scripts/mac/CW_RADAR_Waterfall_Mac.py` | CW | Real-time CW radar waterfall |
| `scripts/mac/FMCW_RADAR_Waterfall_Mac.py` | FMCW | FMCW with range display |
| `scripts/mac/CFAR_RADAR_Waterfall_Mac.py` | CFAR | Target detection radar |
| `scripts/mac/FMCW_RADAR_Waterfall_ChirpSync_Mac.py` | FMCW | TDD-synced (requires Pluto v0.39+) |
| `scripts/mac/CFAR_RADAR_Waterfall_ChirpSync_Mac.py` | CFAR | TDD-synced CFAR (requires Pluto v0.39+) |

**Mac setup (using uv):**
```bash
cd scripts/mac
uv venv --python 3.12
source .venv/bin/activate
uv sync
python3 CW_RADAR_Waterfall_Mac.py
```

See `scripts/mac/README.md` for full details.

## Project Structure

```
aleph-phaser/
├── flake.nix                    # NixOS configuration
├── deploy.sh                    # Deployment script
├── nix/
│   ├── modules/
│   │   └── plutosdr.nix        # PlutoSDR + GPU demo support
│   └── pkgs/                    # Custom packages
│       ├── pylibiio.nix        # Python IIO bindings
│       ├── pyadi-iio.nix       # ADI hardware control
│       ├── cupy.nix            # GPU-accelerated NumPy (CuPy)
│       ├── phaser-data.nix     # Data files + scripts deployment
│       └── test-plutosdr.nix   # Validation tool
├── scripts/
│   ├── cpu-demos/               # CPU-based demos for Aleph
│   │   ├── aleph_minimal_example.py
│   │   ├── aleph_beam_steering.py
│   │   └── aleph_benchmark.py
│   ├── gpu-demos/               # GPU-accelerated demos
│   │   ├── gpu_benchmark.py    # Performance comparison
│   │   ├── gpu_range_doppler.py
│   │   ├── gpu_cfar.py
│   │   ├── gpu_micro_doppler.py
│   │   ├── run_gpu_demo.py     # Complete demo suite
│   │   └── gpu_utils/          # GPU signal processing library
│   └── mac/                     # Qt GUI demos for Mac
│       └── ...
├── data/                        # Filter files, calibration data
├── results/                     # Benchmark results and plots
├── context/                     # Project documentation
└── ssh/                         # SSH keys

# On Aleph after deploy:
/opt/phaser/
├── filters/                     # LTE filter files
├── scripts/                     # All demo scripts
│   ├── cpu-demos/
│   └── gpu-demos/
└── calibration/                 # Calibration data (if any)
```

## Troubleshooting

### PlutoSDR not detected
```bash
lsusb | grep -E "0456|2fa2"   # Check USB
ip addr | grep 192.168.2      # Check network interface
```

### Phaser/Pi not accessible
```bash
# Find Pi on network
ping 192.168.4.184
# Or scan network
nmap -sn 192.168.4.0/24
```

### Python import errors
Redeploy to rebuild pylibiio package:
```bash
./deploy.sh -h 192.168.4.181 -u aleph-phaser
```

### No HB100 signal
1. Check HB100 battery
2. Aim HB100 directly at array (~1m distance)
3. Expected peak: ~1 MHz offset from DC

## Technical Details

### pylibiio Fix (nixpkgs 25.05)
The `pylibiio` package required modification for nixpkgs 25.05 split outputs:
- Uses `lib.getLib libiio` to find library output
- Dynamic library path detection in postInstall
- Proper Nix store references to prevent GC

### Hybrid Architecture Benefits
- **Aleph handles**: High-performance FFT, DSP, data processing
- **Pi handles**: Low-level SPI communication, calibration
- **Result**: Best of both worlds - compute power + hardware control

## References

- [CN0566 Wiki](https://wiki.analog.com/resources/eval/user-guides/circuits-from-the-lab/cn0566)
- [pyadi-iio Docs](https://analogdevicesinc.github.io/pyadi-iio/)
