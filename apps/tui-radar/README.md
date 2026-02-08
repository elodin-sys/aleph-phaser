# TUI Radar

A real-time terminal user interface for visualizing Range-Doppler maps from the CN0566 Phaser radar system. Designed for high frame rates over SSH connections to the Aleph/Orin NX platform.

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
- Python 3.10+ with pyadi-iio, numpy, cupy
- CUDA toolkit (for CuPy)

### Hardware (for live mode)

- ADALM-PLUTO SDR
- CN0566 Phaser Kit

## Building

From the repository root:

```bash
nix develop
cargo build --release -p tui-radar
```

Or directly from the app directory:

```bash
cd apps/tui-radar
cargo build --release
```

## Running

### Synthetic Mode (No Hardware Required)

```bash
./target/release/tui-radar --synthetic
```

### Live Hardware Mode

```bash
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

## Test Patterns & Validation

The TUI supports 11 synthetic test patterns for validating the visualization pipeline. Run with `--synthetic` and press `T` to cycle through patterns.

For detailed documentation on test patterns, validation tools, and hardware validation workflows, see the [radar-core library documentation](../../libs/radar-core/README.md).

Quick validation:

```bash
# Run automated pattern tests
nix develop --command python libs/radar-core/python/test_patterns.py --verbose

# Validate an exported frame
nix develop --command python libs/radar-core/python/validate_hardware.py --validate ./exports/<frame>.npy
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
├── Cargo.toml              # Rust dependencies
├── README.md               # This file
└── src/
    ├── main.rs             # Entry point and CLI
    ├── app.rs              # Application state machine
    ├── config.rs           # TUI configuration
    ├── data/
    │   └── mod.rs          # Data source wrapper (uses radar-core)
    ├── processing/
    │   └── mod.rs          # Placeholder (processing in radar-core)
    └── ui/
        ├── mod.rs          # UI module
        ├── colormap.rs     # Color mapping
        ├── dashboard.rs    # Dashboard layout
        ├── heatmap.rs      # Braille heatmap renderer
        └── spectrum.rs     # 1D spectrum plots
```

## Backend

This TUI is built on the `radar-core` library which handles:
- Python interop via PyO3
- Radar data acquisition and GPU processing
- Test pattern generation
- Wire protocol for streaming

See [libs/radar-core/README.md](../../libs/radar-core/README.md) for library documentation, integration guide, and validation tools.

## License

Copyright (C) 2024 Analog Devices, Inc. / Aleph-Phaser Team
