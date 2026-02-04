# GPU Range-Doppler Radar TUI

A real-time terminal user interface for visualizing GPU-accelerated Range-Doppler maps from the CN0566 Phaser radar system. Designed for high frame rates over SSH connections to the Aleph/Orin NX platform.

## Architecture

The TUI uses a hybrid Rust/Python architecture:

- **Rust (TUI)**: Terminal rendering, user input, frame timing
- **Python (Backend)**: Radar data acquisition, GPU processing via CuPy

```
┌─────────────────────────────────────────────────────────────┐
│                    Rust TUI Application                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  main.rs │→ │  app.rs  │→ │ data/    │→ │   ui/    │    │
│  │  (CLI)   │  │ (state)  │  │ (PyO3)   │  │ (render) │    │
│  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘    │
└───────────────────────────────────┼─────────────────────────┘
                                    │ PyO3
┌───────────────────────────────────┼─────────────────────────┐
│              Python Radar Backend │                          │
│  ┌────────────────────────────────┴─────────────────────┐   │
│  │              radar_backend.py                         │   │
│  │  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │ HardwareMode │  │ SyntheticMode│                  │   │
│  │  │  (pyadi-iio) │  │  (NumPy/CuPy)│                  │   │
│  │  └──────┬───────┘  └──────┬───────┘                  │   │
│  │         └────────┬────────┘                          │   │
│  │                  ▼                                    │   │
│  │         GPU Processing (CuPy)                        │   │
│  │         - 2D FFT                                     │   │
│  │         - MTI Filter                                 │   │
│  │         - dB conversion                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

This architecture ensures that radar processing exactly matches Jon Kraft's `Range_Doppler_Plot_Aleph.py` script while providing a lightweight terminal interface.

## Features

- **High-Resolution Visualization**: Braille-based heatmap rendering with 24-bit true color
- **Real-Time Performance**: 30+ FPS with GPU acceleration
- **Full Dashboard**: Range-Doppler map, Range spectrum, Doppler spectrum, and performance metrics
- **Multiple Colormaps**: Inferno, Plasma, Viridis, Magma
- **Interactive Controls**: Gain adjustment, MTI filter, pause, colormap cycling
- **Dual Mode**: Works with live hardware or synthetic data for testing
- **Processing Parity**: Identical radar processing to Jon's reference script

## Requirements

### On Aleph/Orin NX (Target Platform)

- Rust toolchain (1.70+)
- Python 3.10+ with:
  - pyadi-iio
  - numpy
  - cupy (for GPU acceleration)
- CUDA toolkit (for CuPy)

### Hardware (for live mode)

- ADALM-PLUTO SDR
- CN0566 Phaser Kit
- Raspberry Pi (for Phaser control)

## Building

```bash
cd apps/tui-radar
cargo build --release
```

The build requires Python development headers for PyO3. On most systems these are available via the system package manager (e.g., `python3-dev` on Debian/Ubuntu).

## Local Development

Use the Nix devShell for a consistent development environment across macOS and Linux:

```bash
# Enter the development shell (from repo root)
nix develop

# Build and run
cd apps/tui-radar
cargo build --release
./target/release/tui-radar --synthetic
```

The devShell provides:
- Python 3.12 with numpy
- Rust toolchain
- Correctly configured `PYO3_PYTHON` environment variable

**Note**: GPU acceleration (CuPy) is only available on the target Aleph/Orin NX platform. Local development uses CPU-only processing.

## Running

### Synthetic Mode (No Hardware Required)

```bash
# Run with synthetic data for testing
./target/release/tui-radar --synthetic

# Or with cargo
cargo run --release -- --synthetic
```

### Live Hardware Mode

```bash
# Connect to Phaser system
./target/release/tui-radar \
    --sdr-uri ip:192.168.2.1 \
    --phaser-uri ip:192.168.4.184
```

### Options

```
Usage: tui-radar [OPTIONS]

Options:
      --sdr-uri <SDR_URI>        PlutoSDR URI [default: ip:192.168.2.1]
      --phaser-uri <PHASER_URI>  Phaser/Raspberry Pi URI [default: ip:192.168.4.184]
  -s, --synthetic                Use synthetic data (no hardware required)
      --fps <FPS>                Target frame rate [default: 30]
      --n-doppler <N_DOPPLER>    Number of Doppler bins/chirps [default: 512]
      --max-range <MAX_RANGE>    Maximum range to display (meters) [default: 10.0]
      --chirp-bw <CHIRP_BW>      Chirp bandwidth (Hz) [default: 500000000]
      --ramp-time-us <RAMP_TIME_US>  Ramp time (microseconds) [default: 500]
      --sample-rate <SAMPLE_RATE>    Sample rate (Hz) [default: 4000000]
      --rx-gain <RX_GAIN>        Receive gain (dB) [default: 30]
  -h, --help                     Print help
  -V, --version                  Print version
```

**Note:** The number of range bins (`n_range`) is automatically calculated by the Python backend to match Jon's script:
```
n_range = int(0.9 * ramp_time_us * sample_rate / 1e6)
```
With default parameters (500us ramp, 4MHz sample rate), this gives 1800 range bins.

## Controls

| Key | Action |
|-----|--------|
| `Q` or `Esc` | Quit |
| `P` | Pause/Resume |
| `+` / `-` | Increase/Decrease display gain |
| `C` | Cycle colormap |
| `M` | Toggle MTI filter |
| `R` | Reset to defaults |
| `T` | Cycle test pattern (synthetic mode only) |
| `D` | Toggle debug overlay |
| `E` | Export current frame to file |

## Validation & Testing

The TUI includes comprehensive validation tools to verify correct visual rendering and compare synthetic patterns against real hardware data.

### Test Patterns

Run with a specific test pattern:

```bash
./target/release/tui-radar --synthetic --pattern <pattern_name>
```

Available patterns:

| Pattern | Purpose | Expected Appearance |
|---------|---------|---------------------|
| `animated` | Default moving targets | Multiple bright spots moving over time |
| `corner_dots` | Coordinate verification | 4 bright dots at corners (BL=brightest, TR=dimmest) |
| `gradient_h` | Range axis verification | Horizontal gradient (dark left → bright right) |
| `gradient_v` | Doppler axis verification | Vertical gradient (dark bottom → bright top) |
| `center_target` | Basic target rendering | Single bright blob at center |
| `grid` | Scaling/spacing verification | 5×5 grid lines with bright intersections |
| `diagonal` | Axis orientation check | Diagonal line from bottom-left to top-right |
| `checkerboard` | Axis inversion detection | 4×4 checkerboard pattern |
| `hb100_stationary` | **HB100 reference** | Target at center Doppler, ~3m range |
| `hb100_walking` | **Moving target reference** | Target above center Doppler, ~4m range |
| `dc_leakage` | **DC interference reference** | Bright horizontal line at zero Doppler |

### Validation Workflow

#### Step 1: Verify Synthetic Patterns Pass

Run the automated test suite:

```bash
cd apps/tui-radar
nix develop --command python python/test_patterns.py --verbose
```

All 11 tests should pass. This validates:
- Coordinate system is correct (`rd_map[d, r]` where d=row/Doppler, r=column/Range)
- Value scaling is correct ([0, 8] log10 scale)
- Pattern geometry matches expectations

#### Step 2: Visual Verification with Debug Overlay

```bash
./target/release/tui-radar --synthetic --pattern corner_dots
```

1. Press `D` to enable debug overlay
2. Verify corner labels match expectations:
   - **BL (Bottom-Left)**: `[0, 0]` - brightest (value ~8.0)
   - **BR (Bottom-Right)**: `[0, max_r]` - second brightest (~6.0)
   - **TL (Top-Left)**: `[max_d, 0]` - third (~4.0)
   - **TR (Top-Right)**: `[max_d, max_r]` - dimmest (~2.8)
3. Press `T` to cycle through other patterns and verify each

#### Step 3: Export Synthetic Reference Frames

```bash
# Export HB100 stationary reference (what a real target should look like)
./target/release/tui-radar --synthetic --pattern hb100_stationary
# Press E to export, note the filename

# Export DC leakage reference (for understanding interference patterns)
./target/release/tui-radar --synthetic --pattern dc_leakage
# Press E to export
```

Exports are saved to `apps/tui-radar/exports/` with metadata.

#### Step 4: Validate Exported Frames

```bash
nix develop --command python python/validate_hardware.py --analyze-export ./exports/
```

This generates:
- Statistical analysis (value range, variation, aspect ratio)
- Coordinate mapping verification
- Target detection analysis
- Reference matplotlib plot (if matplotlib available)

### Hardware Validation Workflow

Once you have access to the physical hardware:

#### Step 1: Basic Hardware Connection Test

```bash
./target/release/tui-radar --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
```

If connection fails, verify:
- PlutoSDR is accessible (`ping 192.168.2.1`)
- Phaser/RPi is accessible (`ping 192.168.4.184`)
- Correct IP addresses for your network configuration

#### Step 2: Capture Without Target (Noise Floor)

1. Remove any targets from the radar's field of view
2. Run in hardware mode and export a frame (press `E`)
3. Validate the export:

```bash
nix develop --command python python/validate_hardware.py --validate ./exports/<noise_frame>.npy
```

Expected results:
- No strong peaks
- Relatively flat Range and Doppler profiles
- Possible DC component at center Doppler (this is normal)

#### Step 3: Capture with Stationary HB100

1. Place HB100 on a tripod at a known distance (e.g., 3 meters)
2. Point HB100 at the Phaser array
3. Run TUI and verify you see a bright spot:
   - **Doppler**: Should be at center (zero velocity)
   - **Range**: Should correspond to the actual distance
4. Export the frame (press `E`)

Compare to synthetic reference:

```bash
# Validate hardware capture
nix develop --command python python/validate_hardware.py --validate ./exports/<hb100_frame>.npy

# Compare visually - hardware frame should match hb100_stationary pattern:
# - Bright spot at center Doppler
# - Range bin corresponding to actual distance
```

#### Step 4: Capture with Moving Target

1. Walk toward the radar at a steady pace (~1.5 m/s) while holding HB100
2. Observe the target moving:
   - **Doppler**: Should be above center (approaching = positive Doppler)
   - **Range**: Should decrease as you approach
3. Export frames during movement

Compare to `hb100_walking` synthetic pattern.

#### Step 5: Verify MTI Filter

1. Place a stationary HB100 at ~3m
2. Without MTI: Should see DC line at zero Doppler AND the target
3. Enable MTI (press `M`): DC line should be suppressed, target may also be suppressed if truly stationary
4. With slight target movement, only the target should remain visible

### Troubleshooting

#### Frame Shape Mismatch

If validation reports "AXIS SWAP DETECTED":
- The captured data has axes transposed
- This indicates a bug in the capture code or an old capture format
- Hardware captures should be `(n_doppler, n_range)` = `(512, 30)` with default settings

#### Value Range Mismatch

If values are not in `[0, 8]` range:
- Old captures may use different normalization (e.g., `[-7, 0]` dB scale)
- Current code uses log10 scale with min=0, max=8

#### No Visible Target

If hardware mode shows no target when HB100 is present:
1. Check HB100 frequency matches Phaser configuration (~10.5 GHz)
2. Ensure HB100 is powered and pointing at the array
3. Try adjusting rx_gain (`--rx-gain 40`)
4. Check for obstructions between HB100 and Phaser

#### Excessive DC Leakage

If zero-Doppler line dominates the display:
1. Enable MTI filter (press `M`)
2. Check for reflections from nearby objects
3. Ensure Phaser antennas are unobstructed

### Batch Capture from CLI

For automated testing, use the Python backend directly:

```bash
# Capture 10 frames from hardware
nix develop --command python python/radar_backend.py \
    --mode hardware \
    --sdr-uri ip:192.168.2.1 \
    --phaser-uri ip:192.168.4.184 \
    --frames 10 \
    --export ./captures/

# Analyze the captures
nix develop --command python python/validate_hardware.py --analyze-export ./captures/
```

## Performance

Target performance on Aleph/Orin NX:

| Metric | Value |
|--------|-------|
| Frame Rate | 30-60 FPS |
| Processing Time | <35ms (GPU) |
| Matrix Size | 512 x 1800 (~922K samples) |
| Display Resolution | 400×400 effective pixels |
| Color Depth | 24-bit (16M colors) |

## Code Structure

```
apps/tui-radar/
├── Cargo.toml              # Rust dependencies (PyO3 required)
├── pyproject.toml          # Python dependencies (for uv sync)
├── README.md               # This file
├── analyze_capture.py      # Batch capture analysis tool
├── python/
│   ├── radar_backend.py    # Python radar backend (CuPy/pyadi-iio)
│   ├── phaser_wrapper.py   # Legacy hardware wrapper (unused)
│   ├── test_patterns.py    # Automated test pattern validation
│   └── validate_hardware.py # Hardware capture validation
├── exports/                # Exported frames (created on first export)
├── captures/               # Batch capture output (created on demand)
└── src/
    ├── main.rs             # Entry point and CLI
    ├── app.rs              # Application state machine
    ├── config.rs           # Radar configuration
    ├── data/
    │   └── mod.rs          # PyO3 bridge to Python backend
    ├── processing/
    │   └── mod.rs          # Placeholder (all processing in Python)
    └── ui/
        ├── mod.rs          # UI module
        ├── colormap.rs     # Color mapping
        ├── dashboard.rs    # Dashboard layout
        ├── heatmap.rs      # Braille heatmap renderer
        └── spectrum.rs     # 1D spectrum plots
```

## Comparison with Jon's Script

This TUI is designed to produce identical radar processing results to Jon Kraft's `Range_Doppler_Plot_Aleph.py`:

| Parameter | Jon's Script | TUI Radar |
|-----------|--------------|-----------|
| Sample Rate | 4 MHz | 4 MHz |
| num_chirps / n_doppler | 512 | 512 |
| ramp_time | 500 us | 500 us |
| chirp_BW | 500 MHz | 500 MHz |
| n_range (good_ramp_samples) | 1800 | 1800 (calculated) |
| GPU Processing | CuPy | CuPy (via Python) |
| MTI Filter | Phase-corrected | Phase-corrected |

The key difference is the display: matplotlib GUI vs terminal TUI.

## License

Copyright (C) 2024 Analog Devices, Inc. / Aleph-Phaser Team
