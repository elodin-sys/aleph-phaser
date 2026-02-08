# Aleph-Phaser Integration

This repository demonstrates the Analog Devices CN0566 Phaser development kit running on the Elodin Aleph edge compute platform, which features an NVIDIA Orin NX 16GB module. The integration uses a hybrid architecture that combines the computational power of the Orin NX with the existing Raspberry Pi-based control infrastructure.

https://github.com/user-attachments/assets/64733e7c-0bc6-4698-9362-03058d7d20c4

## Overview

The project establishes a complete working integration between the Aleph and the Phaser X-band phased array radar kit. This includes direct PlutoSDR connectivity over USB, network-based control of the Phaser board through the Raspberry Pi, and a suite of demonstration scripts covering basic signal capture, beam steering, and radar lab exercises. Performance benchmarks confirm that the Orin NX significantly outperforms the original Raspberry Pi for signal processing tasks, with FFT operations completing in under a millisecond and beam sweeps finishing well within acceptable time limits.

Building on this foundation, the repository includes GPU-accelerated radar processing demos that showcase capabilities impractical on the Raspberry Pi. These include real-time range-Doppler map generation at over 30 frames per second, CFAR target detection with substantial speedups over CPU implementations, and micro-Doppler spectrogram analysis suitable for drone detection applications. The demos automatically fall back to CPU processing when GPU acceleration is unavailable.

## Architecture

```
┌─────────────────────┐     USB-C      ┌─────────────────┐
│  Aleph Orin NX      │◄──────────────►│    PlutoSDR     │
│  (192.168.4.186)    │                │  (192.168.2.1)  │
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

The Aleph handles high-performance data processing, FFT computation, and beamforming calculations using Python and pyadi-iio. The PlutoSDR connects directly to the Aleph via USB-C and appears as a network device at 192.168.2.1. The Raspberry Pi retains responsibility for low-level SPI communication with the ADAR1000 beamformers and ADF4159 PLL, preserving compatibility with existing calibration routines.

## Performance

Benchmarks on the NVIDIA Orin NX 16GB running Linux 5.10.216 show FFT processing of 1024 samples completing in 0.036 ms (target was under 1 ms) and 8192 samples in 0.235 ms (target was under 5 ms). A full beam sweep across 25 angles completes in 3.2 seconds, well under the 5-second target. The system has 14 GB of memory available for processing.

## Quick Start

### Install Determinate Systems Nix (recommended)
```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Add the SSH key and deploy the NixOS configuration to the Aleph:

```bash
ssh-add ssh/aleph-phaser
./deploy.sh -h 192.168.4.186 -u aleph-phaser
```

Verify connectivity by SSHing to the Aleph and testing both the PlutoSDR and Phaser:

```bash
ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.186
iio_info -u ip:192.168.2.1
iio_info -u ip:192.168.4.184
python3 -c "import adi; print(adi.ad9361(uri='ip:192.168.2.1').sample_rate)"
```

Demo scripts are automatically deployed to `/opt/phaser/scripts/` on the Aleph. Run CPU-based demos immediately after deployment:

```bash
python3 /opt/phaser/scripts/cpu-demos/aleph_minimal_example.py --output-dir /tmp/output
python3 /opt/phaser/scripts/cpu-demos/aleph_beam_steering.py --output-dir /tmp/output
# or 
cd /opt/phaser/scripts/cpu-demos
python3 run_cpu_demos.py --output-dir /tmp/cpu_results
```

For GPU-accelerated demos:

```bash
cd /opt/phaser/scripts/gpu-demos
python3 run_gpu_demo.py --live --output-dir /tmp/gpu_results
```

Copy back the results to review:
```bash
scp -r -i "ssh/aleph-phaser" aleph-phaser@192.168.4.186:/tmp/cpu_results/ ./results/cpu-demos
scp -r -i "ssh/aleph-phaser" aleph-phaser@192.168.4.186:/tmp/gpu_results/ ./results/gpu-demos
```

## Hardware Requirements

The setup requires an Aleph Carrier Board (ES02) with an NVIDIA Orin NX 16GB module, an ADALM-PLUTO SDR connected to the Aleph via USB-C, and a CN0566 Phaser Kit which includes the Raspberry Pi, Phaser board, and HB100 radar source. The Aleph and Raspberry Pi must be on the same WiFi network.

| Device | Address | Connection |
|--------|---------|------------|
| Aleph | 192.168.4.186 | WiFi (wlan0) |
| PlutoSDR | 192.168.2.1 | USB-Ethernet (enu1) |
| Phaser/Pi | 192.168.4.184 | WiFi |

The Raspberry Pi can be accessed via SSH at `analog@192.168.4.184` with password `analog`.

## Demo Scripts

### GPU-Accelerated Demos

Located in `gpu-demos/`, these scripts demonstrate radar processing that would be impractical on a Raspberry Pi. The `gpu_benchmark.py` script provides a full performance comparison showing 10-100x speedups. The `gpu_range_doppler.py` script generates range-Doppler maps at over 30 FPS with 256K samples. The `gpu_cfar.py` script performs CFAR target detection in under 1ms for 64K samples. The `gpu_micro_doppler.py` script creates micro-Doppler spectrograms suitable for drone detection. The `run_gpu_demo.py` script runs the complete suite and generates a summary report.

These demos use CuPy for GPU acceleration when available and automatically fall back to NumPy otherwise.

### CPU Demos

Located in `cpu-demos/`, these scripts cover the core Phaser functionality. The `sdr_basic_capture.py` script performs basic PlutoSDR capture and requires only the SDR. The `test_phaser_connection.py` script verifies system connectivity. The `aleph_minimal_example.py` script detects the HB100 signal and requires the full system plus the HB100. The `aleph_beam_steering.py` script performs beam sweeps and generates antenna patterns. The `aleph_lab_exercises.py` script implements Lab 3 and Lab 4 exercises from the Phaser curriculum. The `aleph_benchmark.py` script runs performance benchmarks.

### Mac GUI Demos

Located in `scripts/mac/`, these PyQt-based scripts provide real-time radar visualization and run on a Mac connected to the Aleph over the network. They include CW radar waterfall, FMCW radar with range display, and CFAR target detection displays. Some variants require PlutoSDR firmware v0.39 or later for TDD synchronization.

Set up the Mac environment using uv:

```bash
cd scripts/mac
uv venv --python 3.12
source .venv/bin/activate
uv sync
python3 CW_RADAR_Waterfall_Mac.py
```

## Real-Time Radar Visualization

The repository includes two real-time Range-Doppler visualization applications that share a common Rust library (`libs/radar-core/`) and Python backend (`radar_backend.py`). Both use CuPy GPU-accelerated 2D FFT processing.

**TUI Radar** (`apps/tui-radar/`) renders Range-Doppler maps in the terminal using braille-character heatmaps via Ratatui. Designed for headless use over SSH. Run with `tui-radar --synthetic` for test patterns or just `tui-radar` for live hardware (the deployed binary picks up the shared radar config automatically).

**Radar Web** (`apps/radar-web/`) is an Axum web server that streams frames over WebSocket to a WASM/WebGPU browser client. Connect to `http://<aleph-ip>:8080` from any browser on the LAN. The `radar-web` systemd service starts automatically after deployment.

### Radar Configuration

Both applications share a single set of radar parameters defined in `flake.nix` under `aleph-phaser.radar`. These control the FMCW chirp waveform and directly determine the tradeoff between range coverage and frame rate.

The two key parameters are `rampTimeUs` (chirp duration) and `numChirps` (Doppler bins per frame). Together they determine how much data the PlutoSDR must capture and transfer per frame. Since the PlutoSDR uses USB 2.0, the raw IQ data transfer is the dominant bottleneck (93% of frame time), so reducing data volume is the most effective way to increase frame rate.

| Parameter | What it controls | Effect of reducing |
|-----------|-----------------|-------------------|
| `rampTimeUs` | Duration of each FMCW chirp. Longer chirps produce more range samples (and more range coverage). | Fewer ADC samples per chirp, smaller transfer, less range |
| `numChirps` | Number of chirps in a burst. More chirps give finer Doppler (velocity) resolution. | Fewer chirps in the burst, smaller transfer, coarser velocity |
| `maxRange` | Display cutoff in meters. Does not affect capture volume, only what's shown. | No performance impact, just display |

The current defaults are tuned for a close-range desktop demo (0-10 feet):

```nix
aleph-phaser.radar = {
    numChirps = 128;     # 128 chirps (vs Jon's original 512)
    rampTimeUs = 100;    # 100 us ramp (vs Jon's original 500 us)
    maxRange = 3.0;      # ~10 feet display
};
```

Here is how these compare to Jon Kraft's original full-resolution parameters and what each configuration costs in terms of SDR transfer time:

| Config | rampTimeUs | numChirps | Range bins | SDR data | Est. frame time | Est. FPS |
|--------|-----------|-----------|-----------|----------|----------------|---------|
| Jon's original | 500 | 512 | 1800 | 16.8 MB | ~1400 ms | ~0.7 |
| Balanced | 500 | 256 | 1800 | 8.4 MB | ~700 ms | ~1.3 |
| **Close-range (default)** | **100** | **128** | **360** | **2.1 MB** | **~210 ms** | **~4-5** |

The range resolution (0.3 meters) is unchanged across all configurations because it depends only on chirp bandwidth (500 MHz), which stays constant. The close-range config simply captures fewer samples per chirp, covering 0-11 meters instead of 0-54 meters. For a tabletop demo with a cookie sheet reflector at arm's length, this is more than enough range and the 4-5x frame rate improvement makes the display feel responsive.

To switch back to full-resolution for longer-range work, change the shared config in `flake.nix` and redeploy:

```nix
aleph-phaser.radar = {
    numChirps = 512;
    rampTimeUs = 500;
    maxRange = 10.0;
};
```

Both `tui-radar` and `radar-web` will pick up the new values. You can also override on the command line: `tui-radar --num-chirps 512 --ramp-time-us 500 --max-range 10 --synthetic`.

## Project Structure

The repository uses NixOS for deployment. The `flake.nix` defines the system configuration and custom package overlays. The `nix/modules/plutosdr.nix` module configures PlutoSDR support, the IIO network proxy, and GPU demo packages. Custom packages in `nix/pkgs/` include `pylibiio.nix` for Python IIO bindings, `pyadi-iio.nix` for ADI hardware control, `cupy.nix` for GPU-accelerated NumPy, and `phaser-data.nix` for deploying filter files and demo scripts.

After deployment, the Aleph has demo scripts at `/opt/phaser/scripts/` with subdirectories for CPU and GPU demos, filter files at `/opt/phaser/filters/`, and any calibration data at `/opt/phaser/calibration/`.

## Troubleshooting

If the PlutoSDR is not detected, check USB connectivity with `lsusb | grep -E "0456|2fa2"` and verify the network interface with `ip addr | grep 192.168.2`.

If the Phaser or Pi is not accessible, try pinging 192.168.4.184 or scan the network with `nmap -sn 192.168.4.0/24`.

For Python import errors, redeploy to rebuild the pylibiio package with `./deploy.sh -h 192.168.4.186 -u aleph-phaser`.

If no HB100 signal appears, check the HB100 battery, aim it directly at the array from about 1 meter distance, and look for a peak approximately 1 MHz offset from DC.

## Technical Notes

The `pylibiio` package required modifications for nixpkgs 25.05 to handle split outputs correctly. It uses `lib.getLib libiio` to locate the library output and includes dynamic library path detection in the postInstall phase.

The hybrid architecture provides the best of both platforms: the Aleph handles high-performance FFT, DSP, and data processing while the Pi manages low-level SPI communication and calibration. This preserves compatibility with existing Phaser tooling while enabling significantly more demanding signal processing workloads.

## References

- [CN0566 Wiki](https://wiki.analog.com/resources/eval/user-guides/circuits-from-the-lab/cn0566)
- [pyadi-iio Documentation](https://analogdevicesinc.github.io/pyadi-iio/)
