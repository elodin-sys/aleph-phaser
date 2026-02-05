# Radar Web

WebGPU-based radar visualization web application. Provides real-time range-Doppler map visualization in a browser with full interactivity including zoom, pan, colormap selection, and all test patterns.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  WASM Client                             │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │   │
│  │  │ WebSocket │  │ Protocol  │  │  WebGPU Renderer  │   │   │
│  │  │  Client   │──│  Decoder  │──│  (wgpu + shaders) │   │   │
│  │  └───────────┘  └───────────┘  └───────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              │ (binary frames + JSON commands)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Axum Server                                │
│  ┌───────────┐  ┌───────────────┐  ┌─────────────────────────┐ │
│  │   REST    │  │   WebSocket   │  │    Frame Acquisition    │ │
│  │   API     │  │   Handler     │──│    Loop (tokio)         │ │
│  └───────────┘  └───────────────┘  └─────────────────────────┘ │
│                                              │                   │
│                                              ▼                   │
│                                    ┌─────────────────────────┐  │
│                                    │      radar-core         │  │
│                                    │   (Python backend)      │  │
│                                    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Nix with flakes enabled
- A WebGPU-capable browser (Chrome 113+, Edge 113+, or Firefox Nightly with `dom.webgpu.enabled`)

## Quick Start

All commands are run from the **repository root** inside a nix develop shell.

```bash
# 1. Enter the development shell
nix develop

# 2. Build the WASM client
cd apps/radar-web/client && wasm-pack build --target web --dev && cd ../../..

# 3. Copy WASM artifacts to static directory
cp -r apps/radar-web/client/pkg/* apps/radar-web/static/

# 4. Run the server in synthetic mode
cargo run -p radar-web -- --synthetic
```

Then open http://localhost:8080 in a WebGPU-capable browser.

## Build Options

### Development Build (faster, larger WASM)

```bash
cd apps/radar-web/client && wasm-pack build --target web --dev && cd ../../..
cp -r apps/radar-web/client/pkg/* apps/radar-web/static/
```

### Release Build (optimized, smaller WASM)

```bash
cd apps/radar-web/client && wasm-pack build --target web --release && cd ../../..
cp -r apps/radar-web/client/pkg/* apps/radar-web/static/
```

## Running the Server

### Synthetic Mode (no hardware required)

```bash
cargo run -p radar-web -- --synthetic
```

### Hardware Mode (requires PlutoSDR + Phaser)

```bash
cargo run -p radar-web -- --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.2.1
```

### Server Options

```
Options:
  -s, --synthetic              Run in synthetic data mode (no hardware)
      --sdr-uri <URI>          PlutoSDR URI (e.g., ip:192.168.2.1)
      --phaser-uri <URI>       Phaser board URI (e.g., ip:192.168.2.1)
  -h, --host <HOST>            Server host address [default: 0.0.0.0]
  -p, --port <PORT>            Server port [default: 8080]
  -f, --fps <FPS>              Target frame rate [default: 30]
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `T` | Cycle test pattern (synthetic mode) |
| `M` | Toggle MTI filter |
| `E` | Export frame to `./exports/` |
| `C` | Cycle colormap |
| `+` / `=` | Increase gain |
| `-` | Decrease gain |
| `P` | Pause/resume |
| `R` | Reset to defaults |
| `D` | Toggle debug overlay |

## Mouse Controls

| Action | Effect |
|--------|--------|
| Scroll wheel | Zoom in/out |
| Click + drag | Pan |

## Test Patterns

Available in synthetic mode (cycle with `T`):

- `animated` - Moving target simulation
- `corner_dots` - Corner markers for calibration
- `grid` - Grid pattern
- `gradient_h` - Horizontal gradient
- `gradient_v` - Vertical gradient
- `diagonal` - Diagonal stripes
- `checkerboard` - Checkerboard pattern
- `center_cross` - Cross at center
- `concentric` - Concentric circles
- `noise` - Random noise
- `single_target` - Single bright point

## Colormaps

Cycle through with `C`:

- Inferno (default)
- Plasma
- Viridis
- Hot
- Grayscale

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Server status and version |
| `/api/config` | GET | Current radar configuration |
| `/ws/frames` | WebSocket | Bidirectional frame streaming and commands |

## WebSocket Protocol

The `/ws/frames` endpoint supports bidirectional communication:

### Server → Client (Binary)
Binary messages contain encoded radar frames with a 32-byte header + f32 payload.

### Server → Client (JSON)
```json
{"event":"state_update","mode":"synthetic","pattern":"animated","mti_enabled":false,"paused":false,...}
{"event":"toast","message":"Pattern: grid","level":"info"}
{"event":"export_result","success":true,"path":"exports/frame_20260205_123456.npy"}
```

### Client → Server (JSON)
```json
{"cmd":"cycle_pattern"}
{"cmd":"toggle_mti"}
{"cmd":"export"}
{"cmd":"pause"}
{"cmd":"resume"}
{"cmd":"reset"}
{"cmd":"get_state"}
```

## Project Structure

```
apps/radar-web/
├── Cargo.toml           # Server crate
├── src/
│   ├── main.rs          # Server entry point
│   ├── config.rs        # Server configuration
│   └── server/
│       ├── mod.rs       # Server setup
│       ├── broadcast.rs # Frame acquisition & command handling
│       ├── routes.rs    # REST API routes
│       └── websocket.rs # WebSocket handler
├── client/
│   ├── Cargo.toml       # WASM client crate
│   └── src/
│       ├── lib.rs       # WASM entry point
│       ├── app.rs       # Application state & event handlers
│       ├── protocol.rs  # Frame protocol decoder
│       ├── websocket.rs # WebSocket client
│       └── renderer/
│           ├── mod.rs       # WebGPU renderer
│           ├── pipeline.rs  # Render pipeline
│           ├── texture.rs   # Texture management
│           ├── colormap.rs  # Colormap LUTs
│           └── shaders.wgsl # GPU shaders
├── static/
│   └── index.html       # Main HTML page
└── README.md            # This file
```

## Troubleshooting

### "WebGPU is not supported"
- Use Chrome 113+ or Edge 113+
- For Firefox: enable `dom.webgpu.enabled` in `about:config`
- Safari: WebGPU support is limited; use Chrome/Edge

### "Failed to load WASM module"
- Ensure you built the WASM client: `cd apps/radar-web/client && wasm-pack build --target web --dev`
- Ensure you copied the artifacts: `cp -r apps/radar-web/client/pkg/* apps/radar-web/static/`

### "ModuleNotFoundError: No module named 'radar_backend'"
- Run the server from the repository root, not from inside `apps/radar-web/`
- The Python backend is loaded from `libs/radar-core/python/`

### Low frame rate
- Release build is significantly faster than dev build
- Complex test patterns (noise) are slower than simple ones
- Check browser DevTools console for WebGPU errors

## Development

### Rebuild WASM on changes

```bash
# Watch mode (requires cargo-watch)
cargo watch -w apps/radar-web/client/src -s \
  "cd apps/radar-web/client && wasm-pack build --target web --dev && cp -r pkg/* ../static/"
```

### Run with debug logging

```bash
RUST_LOG=debug cargo run -p radar-web -- --synthetic
```
