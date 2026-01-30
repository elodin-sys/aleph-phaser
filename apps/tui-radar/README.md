# GPU Range-Doppler Radar TUI

A real-time terminal user interface for visualizing GPU-accelerated Range-Doppler maps from the CN0566 Phaser radar system. Designed for high frame rates over SSH connections to the Aleph/Orin NX platform.

## Features

- **High-Resolution Visualization**: Braille-based heatmap rendering with 24-bit true color
- **Real-Time Performance**: 30+ FPS with GPU acceleration
- **Full Dashboard**: Range-Doppler map, Range spectrum, Doppler spectrum, and performance metrics
- **Multiple Colormaps**: Inferno, Plasma, Viridis, Magma
- **Interactive Controls**: Gain adjustment, MTI filter, pause, colormap cycling
- **Dual Mode**: Works with live hardware or synthetic data for testing

## Requirements

### On Aleph/Orin NX (Target Platform)

- Rust toolchain (1.70+)
- Python 3.10+ with pyadi-iio installed
- libiio development libraries
- CUDA toolkit (optional, for GPU acceleration)

### Hardware (for live mode)

- ADALM-PLUTO SDR
- CN0566 Phaser Kit
- Raspberry Pi (for Phaser control)

## Building

```bash
cd scripts/tui-radar

# Basic build (synthetic mode only, no hardware dependencies)
cargo build --release

# With Python support for Phaser control (requires Python + pyadi-iio)
cargo build --release --features python

# With GPU acceleration (requires CUDA)
cargo build --release --features gpu

# Full build with all features (for Aleph deployment)
cargo build --release --features full
```

### Feature Flags

| Feature | Description |
|---------|-------------|
| (default) | Basic TUI with synthetic data support |
| `python` | Enables PyO3 bindings to pyadi-iio for Phaser control |
| `gpu` | Enables CUDA/cuFFT for GPU-accelerated processing (requires CUDA toolkit) |
| `full` | All features enabled |

**Note:** The `gpu` feature requires the CUDA toolkit to be installed on the build system. It will auto-detect the CUDA version at compile time. This feature is intended for use on the Aleph/Orin NX platform which has CUDA pre-installed.

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
      --n-range <N_RANGE>        Number of range bins [default: 512]
      --n-doppler <N_DOPPLER>    Number of Doppler bins [default: 512]
      --max-range <MAX_RANGE>    Maximum range to display (meters) [default: 150.0]
      --chirp-bw <CHIRP_BW>      Chirp bandwidth (Hz) [default: 500000000]
      --ramp-time-us <RAMP_TIME_US>  Ramp time (microseconds) [default: 500]
  -h, --help                     Print help
  -V, --version                  Print version
```

## Controls

| Key | Action |
|-----|--------|
| `Q` or `Esc` | Quit |
| `P` | Pause/Resume |
| `+` / `-` | Increase/Decrease display gain |
| `C` | Cycle colormap |
| `M` | Toggle MTI filter |
| `R` | Reset to defaults |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Rust TUI Application                   │
├──────────────┬──────────────┬──────────────┬────────────┤
│  Data Acq    │  Processing  │  Rendering   │  Control   │
│  (IIO)       │  (FFT)       │  (Ratatui)   │  (PyO3)    │
└──────────────┴──────────────┴──────────────┴────────────┘
       ↓               ↓               ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────┐
│  PlutoSDR    │ │   GPU/CPU    │ │ Terminal │ │   Pi   │
└──────────────┘ └──────────────┘ └──────────┘ └────────┘
```

## Performance

Target performance on Aleph/Orin NX:

| Metric | Value |
|--------|-------|
| Frame Rate | 30-60 FPS |
| Processing Time | <5ms |
| Display Resolution | 400×400 effective pixels |
| Color Depth | 24-bit (16M colors) |

## Development

### Running Tests

```bash
cargo test
```

### Code Structure

- `src/main.rs` - Entry point and CLI
- `src/app.rs` - Application state machine
- `src/config.rs` - Radar configuration
- `src/data/` - Data acquisition (synthetic, IIO, Phaser control)
- `src/processing/` - Signal processing (FFT, windowing)
- `src/ui/` - TUI components (heatmap, spectrum, dashboard)

## License

Copyright (C) 2024 Analog Devices, Inc. / Aleph-Phaser Team
