# Radar Web

WebGPU-based radar visualization web application. Provides real-time range-Doppler map visualization in a browser with full interactivity including zoom, pan, colormap selection, and all test patterns.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         Browser                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                  WASM Client                           │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │   │
│  │  │ WebSocket │  │ Protocol  │  │  WebGPU Renderer  │   │   │
│  │  │  Client   │──│  Decoder  │──│  (wgpu + shaders) │   │   │
│  │  └───────────┘  └───────────┘  └───────────────────┘   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              │ (binary frames + JSON commands)
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                       Axum Server                              │
│  ┌───────────┐  ┌───────────────┐  ┌─────────────────────────┐ │
│  │   REST    │  │   WebSocket   │  │    Frame Acquisition    │ │
│  │   API     │  │   Handler     │──│    Loop (tokio)         │ │
│  └───────────┘  └───────────────┘  └─────────────────────────┘ │
│                                              │                 │
│                                              ▼                 │
│                                    ┌─────────────────────────┐ │
│                                    │      radar-core         │ │
│                                    │   (Python backend)      │ │
│                                    └─────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
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

### GPU not used (CuPy / GR3D_FREQ 0%)
If `tegrastats` shows `GR3D_FREQ 0%` and timing shows ~60 ms `fft_ms`, the Python backend is using NumPy (CPU) instead of CuPy (GPU).

1. **Check GPU status in logs** – After deploy, run `journalctl -u radar-web --no-pager | head -80` and look for:
   - At import: `RadarBackend: GPU acceleration ENABLED (CuPy/CUDA)` or `DISABLED (...)`.
   - On first hardware frame: `RadarBackend: gpu_available=True backend=cupy` or `gpu_available=False backend=numpy`.
2. **LD_LIBRARY_PATH** – CuPy needs the CUDA driver and runtime on `LD_LIBRARY_PATH`. The radar-web service gets this from `config.aleph-phaser.cudaEnv` (see `nix/modules/python-env.nix`), which uses `environment.variables.LD_LIBRARY_PATH` when set (e.g. by the aleph-dev module). If that isn’t set, the service falls back to the cudatoolkit lib path; on Jetson, the nvidia driver (`libcuda.so.1`) may live in a path that only aleph-dev sets. Ensure the NixOS config that sets up the Jetson (aleph-dev / jetpack) sets `environment.variables.LD_LIBRARY_PATH` so the radar-web service inherits it.
3. **CuPy in the Python env** – GPU is only enabled when `services.plutosdr.enableGpuDemos = true` (or equivalent) so that `aleph-phaser.enableGpu` is true and the unified Python env includes CuPy.

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

## Deploy

From the **repository root** (optionally inside `nix develop`):

```bash
# Deploy NixOS config (including radar-web service when enabled) to the default host
./deploy.sh

# Override host, user, or SSH key
./deploy.sh -h 192.168.4.185 -u aleph
./deploy.sh -h 192.168.4.185 -u aleph -k ./ssh/aleph-phaser
```

The deploy script builds the NixOS system (see `flake.nix`), pushes it to the target, and runs `switch-to-configuration switch`. The radar-web systemd service is started when `services.radar-web.enable` is true in the selected NixOS config.

## Testing

### Local (synthetic)

```bash
cargo run -p radar-web -- --synthetic
```

Then open http://localhost:8080 and confirm the range-Doppler view and keyboard controls work.

### Local (hardware)

```bash
cargo run -p radar-web -- --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.2.1
```

### After deploy

```bash
# Service status (on the device or via SSH)
sudo systemctl status radar-web

# API health check
curl http://HOST:8080/api/status

# Logs (GPU status, frame timing, errors)
journalctl -u radar-web -f
```

Replace `HOST` with the device IP (e.g. the Aleph host). For GPU observability, on the device run `sudo tegrastats --interval 500` and look for `GR3D_FREQ` during frame processing.

## Validating hardware display

To confirm that hardware mode matches synthetic (range 0 m at left, target visible):

1. **Deploy** (from repo root): `./deploy.sh -h 192.168.4.181 -u aleph-phaser`
2. **SSH** to the device: `ssh -i ./ssh/aleph-phaser aleph-phaser@192.168.4.181`
3. **Check connectivity**: `ping 192.168.2.1` (Pluto); `sudo systemctl status radar-web`; `journalctl -u radar-web -f` for logs.
4. Open the web UI at `http://192.168.4.181:8080` in hardware mode. With an HB100 at ~1 m, you should see a bright spot near the left edge and no DC cross at center.
5. **Export a frame**: Press `E` in the web UI. Frames are written to `/var/lib/radar-web/exports/` on the device.
6. **Copy exports locally** (from repo root):
   ```bash
   mkdir -p exports
   scp -r -i ./ssh/aleph-phaser aleph-phaser@192.168.4.181:/var/lib/radar-web/exports ./exports
   ```
7. **Run pipeline diagnostic** (generates plots if matplotlib is available):
   ```bash
   nix develop --command python libs/radar-core/python/validate_web_pipeline.py \
     exports/frame_YYYYMMDD_HHMMSS.npy -o exports/pipeline_diag --target-range 1.0
   ```
8. **Run hardware validation** (note the `--validate` flag):
   ```bash
   nix develop --command python libs/radar-core/python/validate_hardware.py \
     --validate exports/frame_YYYYMMDD_HHMMSS.npy
   ```

### Troubleshooting: HB100 not visible (only DC at 0 m)

If exported frames show only DC leakage and no target at 1 m, TDD may be unsynchronized with the ADF4159 ramp (common in USB mode).

1. **Smoke test — use IP mode**  
   In `flake.nix`, set `services.radar-web.sdrUri = "ip:192.168.2.1";`, redeploy, then export again with HB100 at 1 m and run `validate_web_pipeline.py`. If the target appears, the cause was USB TDD sync.

2. **Fix USB TDD sync**  
   The backend now writes `gpio_tdd_ext_sync` in USB mode (`radar_backend.py`). If the one-bit-adc-dac output label differs on your device, inspect IIO channels on the device:
   ```bash
   python3 -c "
   import iio
   ctx = iio.Context('usb:')
   for d in ctx.devices:
       if 'one-bit-adc-dac' in (d.name or ''):
           for ch in d.channels:
               labels = {k: ch.attrs[k].value for k in ch.attrs}
               print(f'  ch={ch.id} output={ch.output} attrs={labels}')
   "
   ```
   Then update the `_set_out` label in the `gpio_tdd_ext_sync` setter if needed.

3. **Fallback — run reference script on device**  
   If IP mode still does not show the target, confirm the physical setup with the original lab script (stop radar-web first so the SDR is free):
   ```bash
   ssh -i ./ssh/aleph-phaser aleph-phaser@192.168.4.181
   sudo systemctl stop radar-web
   # On device, run with appropriate URIs (e.g. SDR and Phaser IPs)
   # scripts/gpu-demos/gpu_range_doppler.py uses ip:ALEPH_IP for SDR and ip:PHASER_IP for Phaser
   ```
   If the reference script shows the HB100, the issue is in radar-web config; if not, check antenna/cabling and HB100 placement.
