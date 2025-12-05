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
./deploy.sh -h 192.168.4.181 -u aleph-phaser
```

Verify connectivity by SSHing to the Aleph and testing both the PlutoSDR and Phaser:

```bash
ssh -i ssh/aleph-phaser aleph-phaser@192.168.4.181
iio_info -u ip:192.168.2.1
iio_info -u ip:192.168.4.184
python3 -c "import adi; print(adi.ad9361(uri='ip:192.168.2.1').sample_rate)"
```

Demo scripts are automatically deployed to `/opt/phaser/scripts/` on the Aleph. Run CPU-based demos immediately after deployment:

```bash
python3 /opt/phaser/scripts/cpu-demos/aleph_minimal_example.py --output-dir /tmp/output
python3 /opt/phaser/scripts/cpu-demos/aleph_beam_steering.py --output-dir /tmp/output
```

For GPU-accelerated demos:

```bash
cd /opt/phaser/scripts/gpu-demos
python3 run_gpu_demo.py --output-dir /tmp/gpu_results
```

## Hardware Requirements

The setup requires an Aleph Carrier Board (ES02) with an NVIDIA Orin NX 16GB module, an ADALM-PLUTO SDR connected to the Aleph via USB-C, and a CN0566 Phaser Kit which includes the Raspberry Pi, Phaser board, and HB100 radar source. The Aleph and Raspberry Pi must be on the same WiFi network.

| Device | Address | Connection |
|--------|---------|------------|
| Aleph | 192.168.4.181 | WiFi (wlan0) |
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

## Project Structure

The repository uses NixOS for deployment. The `flake.nix` defines the system configuration and custom package overlays. The `nix/modules/plutosdr.nix` module configures PlutoSDR support, the IIO network proxy, and GPU demo packages. Custom packages in `nix/pkgs/` include `pylibiio.nix` for Python IIO bindings, `pyadi-iio.nix` for ADI hardware control, `cupy.nix` for GPU-accelerated NumPy, and `phaser-data.nix` for deploying filter files and demo scripts.

After deployment, the Aleph has demo scripts at `/opt/phaser/scripts/` with subdirectories for CPU and GPU demos, filter files at `/opt/phaser/filters/`, and any calibration data at `/opt/phaser/calibration/`.

## Troubleshooting

If the PlutoSDR is not detected, check USB connectivity with `lsusb | grep -E "0456|2fa2"` and verify the network interface with `ip addr | grep 192.168.2`.

If the Phaser or Pi is not accessible, try pinging 192.168.4.184 or scan the network with `nmap -sn 192.168.4.0/24`.

For Python import errors, redeploy to rebuild the pylibiio package with `./deploy.sh -h 192.168.4.181 -u aleph-phaser`.

If no HB100 signal appears, check the HB100 battery, aim it directly at the array from about 1 meter distance, and look for a peak approximately 1 MHz offset from DC.

## Technical Notes

The `pylibiio` package required modifications for nixpkgs 25.05 to handle split outputs correctly. It uses `lib.getLib libiio` to locate the library output and includes dynamic library path detection in the postInstall phase.

The hybrid architecture provides the best of both platforms: the Aleph handles high-performance FFT, DSP, and data processing while the Pi manages low-level SPI communication and calibration. This preserves compatibility with existing Phaser tooling while enabling significantly more demanding signal processing workloads.

## References

- [CN0566 Wiki](https://wiki.analog.com/resources/eval/user-guides/circuits-from-the-lab/cn0566)
- [pyadi-iio Documentation](https://analogdevicesinc.github.io/pyadi-iio/)
