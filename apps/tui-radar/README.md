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
├── Cargo.toml           # Rust dependencies (PyO3 required)
├── pyproject.toml       # Python dependencies (for uv sync)
├── README.md            # This file
├── python/
│   ├── radar_backend.py # Python radar backend (CuPy/pyadi-iio)
│   └── phaser_wrapper.py # Legacy hardware wrapper (unused)
└── src/
    ├── main.rs          # Entry point and CLI
    ├── app.rs           # Application state machine
    ├── config.rs        # Radar configuration
    ├── data/
    │   └── mod.rs       # PyO3 bridge to Python backend
    ├── processing/
    │   └── mod.rs       # Placeholder (all processing in Python)
    └── ui/
        ├── mod.rs       # UI module
        ├── colormap.rs  # Color mapping
        ├── dashboard.rs # Dashboard layout
        ├── heatmap.rs   # Braille heatmap renderer
        └── spectrum.rs  # 1D spectrum plots
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
