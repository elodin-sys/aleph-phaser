# radar-core

A shared Rust library providing the radar backend for the CN0566 Phaser radar system. This library handles all Python interop (via PyO3), radar data types, wire protocol, and test pattern generation.

## Overview

`radar-core` provides:

- **PyO3 Bridge**: Seamless Rust-Python interop for radar data acquisition
- **Type System**: Strongly-typed radar configuration, frames, and dimensions
- **Wire Protocol**: Binary frame encoding/decoding for streaming applications
- **Test Patterns**: 11 synthetic patterns for validation and testing
- **Validation Tools**: Python scripts for pattern verification and hardware validation

## Architecture

The library uses a hybrid Rust/Python architecture where Rust provides type safety and performance-critical code, while Python handles hardware communication and GPU-accelerated signal processing.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Rust Application                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    radar-core                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │ RadarConfig│  │ RadarFrame │  │   RadarSource      │  │   │
│  │  │ RadarMode  │  │ FrameData  │  │   (PyO3 bridge)    │  │   │
│  │  │ TestPattern│  │ FrameDims  │  │                    │  │   │
│  │  └────────────┘  └────────────┘  └─────────┬──────────┘  │   │
│  │                                            │ PyO3        │   │
│  └────────────────────────────────────────────┼─────────────┘   │
└───────────────────────────────────────────────┼─────────────────┘
                                                │
┌───────────────────────────────────────────────┼─────────────────┐
│              Python Radar Backend             │                 │
│  ┌────────────────────────────────────────────┴───────────────┐ │
│  │                    radar_backend.py                        │ │
│  │  ┌──────────────┐  ┌──────────────┐                        │ │
│  │  │ HardwareMode │  │ SyntheticMode│                        │ │
│  │  │  (pyadi-iio) │  │  (NumPy/CuPy)│                        │ │
│  │  └──────┬───────┘  └──────┬───────┘                        │ │
│  │         └────────┬────────┘                                │ │
│  │                  ▼                                         │ │
│  │         GPU Processing (CuPy)                              │ │
│  │         - 2D FFT                                           │ │
│  │         - MTI Filter                                       │ │
│  │         - dB conversion                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Guide

### Adding to Your Project

Add `radar-core` as a dependency in your `Cargo.toml`:

```toml
[dependencies]
radar-core = { path = "../../libs/radar-core" }
```

If using a Cargo workspace, add it to your workspace members:

```toml
[workspace]
members = [
    "libs/radar-core",
    "apps/your-app",
]
```

### Basic Usage

```rust
use radar_core::{RadarConfig, RadarMode, RadarSource, TestPattern};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Configure the radar
    let config = RadarConfig {
        mode: RadarMode::Synthetic,  // or RadarMode::Hardware
        test_pattern: TestPattern::Animated,
        n_doppler: 512,
        sample_rate: 4_000_000.0,
        ..Default::default()
    };

    // Create the radar source
    let mut source = RadarSource::new(config)?;

    // Capture frames
    loop {
        let frame = source.capture()?;
        
        // frame.data is Array2<f32> with shape (n_doppler, n_range)
        // Values are in log10 scale [0, 8]
        println!("Frame shape: {:?}", frame.data.dim());
        
        // Access frame metadata
        println!("Doppler bins: {}", source.n_doppler());
        println!("Range bins: {}", source.n_range());
    }
}
```

### Hardware Mode

For live radar data from CN0566 Phaser:

```rust
let config = RadarConfig {
    mode: RadarMode::Hardware,
    sdr_uri: "ip:192.168.2.1".to_string(),
    phaser_uri: "ip:192.168.4.184".to_string(),
    ..Default::default()
};

let mut source = RadarSource::new(config)?;
```

### Working with Frames

```rust
use radar_core::{RadarFrame, FrameData, FrameDimensions};

// Capture returns a RadarFrame
let frame = source.capture()?;

// Access raw float data
let data: &Array2<f32> = frame.data();

// Get dimensions
let dims = frame.dimensions();
println!("{}x{} (Doppler x Range)", dims.n_doppler, dims.n_range);

// Convert to bytes for transmission
let bytes: Vec<u8> = frame.to_u8();
```

### Wire Protocol

For streaming radar data over network:

```rust
use radar_core::{EncodedFrame, FrameHeader};

// Encode a frame for transmission
let frame = source.capture()?;
let encoded = EncodedFrame::from_frame(&frame, source.min_scale(), source.max_scale());

// Get bytes for network transmission
let header_bytes = encoded.header_bytes();
let data_bytes = encoded.data_bytes();

// Decode received frame
let decoded = EncodedFrame::from_bytes(&received_bytes)?;
let frame = decoded.to_frame();
```

## Test Patterns

Synthetic test patterns for validation and development. Use `--synthetic` mode with any application built on radar-core.

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

### Using Test Patterns in Code

```rust
use radar_core::TestPattern;

// Get pattern by name
let pattern = TestPattern::from_name("corner_dots").unwrap_or_default();

// Cycle through patterns
let next = pattern.next();
let prev = pattern.prev();

// Get pattern description
println!("{}: {}", pattern.name(), pattern.description());

// All patterns implement Display
println!("Current pattern: {}", pattern);
```

## Validation Tools

Python scripts are included in `libs/radar-core/python/` for comprehensive validation.

### Automated Pattern Validation

Run the test suite to verify all synthetic patterns generate correct data:

```bash
# From repository root
nix develop --command python libs/radar-core/python/test_patterns.py --verbose
```

All 11 tests validate:
- Coordinate system is correct (`rd_map[d, r]` where d=row/Doppler, r=column/Range)
- Value scaling is correct ([0, 8] log10 scale)
- Pattern geometry matches expectations

### Hardware Capture Validation

Analyze exported radar frames:

```bash
# Validate a single capture
nix develop --command python libs/radar-core/python/validate_hardware.py --validate ./exports/<frame>.npy

# Analyze a directory of captures
nix develop --command python libs/radar-core/python/validate_hardware.py --analyze-export ./exports/
```

This generates:
- Statistical analysis (value range, variation, aspect ratio)
- Coordinate mapping verification
- Target detection analysis
- Reference matplotlib plot (if matplotlib available)

### Batch Capture from CLI

Use the Python backend directly for automated testing:

```bash
# Capture 10 frames from hardware
nix develop --command python libs/radar-core/python/radar_backend.py \
    --mode hardware \
    --sdr-uri ip:192.168.2.1 \
    --phaser-uri ip:192.168.4.184 \
    --frames 10 \
    --export ./captures/

# Analyze the captures
nix develop --command python libs/radar-core/python/validate_hardware.py --analyze-export ./captures/
```

## Hardware Validation Workflow

Complete workflow for validating radar-core with physical hardware.

### Step 1: Verify Synthetic Patterns Pass

```bash
nix develop --command python libs/radar-core/python/test_patterns.py --verbose
```

All 11 tests should pass before proceeding to hardware.

### Step 2: Basic Hardware Connection Test

```bash
# Using tui-radar or your own application
./target/release/tui-radar --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
```

If connection fails, verify:
- PlutoSDR is accessible (`ping 192.168.2.1`)
- Phaser/RPi is accessible (`ping 192.168.4.184`)
- Correct IP addresses for your network configuration

### Step 3: Capture Without Target (Noise Floor)

1. Remove any targets from the radar's field of view
2. Export a frame and validate:

```bash
nix develop --command python libs/radar-core/python/validate_hardware.py --validate ./exports/<noise_frame>.npy
```

Expected results:
- No strong peaks
- Relatively flat Range and Doppler profiles
- Possible DC component at center Doppler (this is normal)

### Step 4: Capture with Stationary HB100

1. Place HB100 on a tripod at a known distance (e.g., 3 meters)
2. Point HB100 at the Phaser array
3. Verify you see a bright spot:
   - **Doppler**: Should be at center (zero velocity)
   - **Range**: Should correspond to the actual distance
4. Export and compare to synthetic reference:

```bash
nix develop --command python libs/radar-core/python/validate_hardware.py --validate ./exports/<hb100_frame>.npy
```

### Step 5: Capture with Moving Target

1. Walk toward the radar at a steady pace (~1.5 m/s) while holding HB100
2. Observe the target moving:
   - **Doppler**: Should be above center (approaching = positive Doppler)
   - **Range**: Should decrease as you approach
3. Compare to `hb100_walking` synthetic pattern

### Step 6: Verify MTI Filter

1. Place a stationary HB100 at ~3m
2. Without MTI: Should see DC line at zero Doppler AND the target
3. Enable MTI: DC line should be suppressed
4. With slight target movement, only the target should remain visible

## Troubleshooting

### Frame Shape Mismatch

If validation reports "AXIS SWAP DETECTED":
- The captured data has axes transposed
- Hardware captures should be `(n_doppler, n_range)` = `(512, 30)` with default settings

### Value Range Mismatch

If values are not in `[0, 8]` range:
- Old captures may use different normalization
- Current code uses log10 scale with min=0, max=8

### No Visible Target

If hardware mode shows no target when HB100 is present:
1. Check HB100 frequency matches Phaser configuration (~10.5 GHz)
2. Ensure HB100 is powered and pointing at the array
3. Try adjusting rx_gain
4. Check for obstructions between HB100 and Phaser

### Excessive DC Leakage

If zero-Doppler line dominates the display:
1. Enable MTI filter
2. Check for reflections from nearby objects
3. Ensure Phaser antennas are unobstructed

## Module Structure

```
libs/radar-core/
├── Cargo.toml              # Crate manifest
├── README.md               # This file
├── build.rs                # PyO3 build configuration
├── python/
│   ├── radar_backend.py    # Python radar backend (CuPy/pyadi-iio)
│   ├── test_patterns.py    # Automated test pattern validation
│   └── validate_hardware.py # Hardware capture validation
└── src/
    ├── lib.rs              # Public API exports
    ├── backend.rs          # PyO3 bridge to Python
    ├── config.rs           # RadarConfig, RadarMode
    ├── error.rs            # RadarError types
    ├── frame.rs            # RadarFrame, FrameData, FrameDimensions
    ├── patterns.rs         # TestPattern enum and methods
    └── protocol.rs         # FrameHeader, EncodedFrame (wire protocol)
```

## License

Copyright (C) 2024 Analog Devices, Inc. / Aleph-Phaser Team
