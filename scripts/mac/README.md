# Mac-based Phaser Demos

Run Phaser demos with real-time visualization on your Mac while the hardware is connected to the Aleph. All Python dependencies are provided by the nix develop shell.

## Architecture

```
+-------------------+                    +-------------------------+
|      Mac          |<--- Network ------>|  Aleph (iiod proxy)     |
|  (Display)        |    port 30431      |  iiod -u ip:192.168.2.1 |
|                   |                    |  192.168.4.181          |
|  pyadi-iio        |                    +-------------------------+
|  matplotlib       |                              |
|  PyQt5/pyqtgraph  |                              | USB-Ethernet
+--------+----------+                              v
         |                             +-------------------+
         |                             |    PlutoSDR       |
         |                             |  192.168.2.1      |
         |                             +-------------------+
         |
         |<---- Network -------------->+-------------------+
                                       |  Raspberry Pi     |
                                       |  (Phaser iiod)    |
                                       |  192.168.4.184    |
                                       +-------------------+
```

The Aleph runs an `iiod` daemon that proxies the PlutoSDR's IIO context to network clients on port 30431. Unlike a raw TCP relay, `iiod` natively understands the IIO protocol including buffer streaming, which is required for `sdr.rx()` to work remotely.

## Setup

### 1. Enter the nix develop shell

All Python dependencies (pyadi-iio, PyQt5, pyqtgraph, matplotlib, scipy, numpy) are provided by the nix shell. No pip or uv needed.

```bash
cd /path/to/aleph-phaser
nix develop
cd scripts/mac
```

### 2. Ensure the IIO proxy is running on Aleph

The Aleph runs an `iiod` daemon (`iio-proxy` service) that serves the PlutoSDR's IIO context to network clients on port 30431.

Check status:
```bash
ssh aleph-phaser@192.168.4.181 'systemctl status iio-proxy'
```

If not running:
```bash
ssh aleph-phaser@192.168.4.181 'sudo systemctl start iio-proxy'
```

### 3. Stop radar-web if running (for Range-Doppler and ChirpSync demos)

The PlutoSDR only supports one active client at a time. If radar-web is running, stop it first:

```bash
ssh aleph-phaser@192.168.4.181 'sudo systemctl stop radar-web'
```

Wait ~20 seconds for the PlutoSDR to reboot (radar-web reboots the Pluto on shutdown to reset the DMA engine).

### 4. Verify Phaser/Pi is accessible

```bash
ping 192.168.4.184
```

## Running the Demos

### CW Radar Waterfall

Real-time CW radar with FFT spectrum and waterfall display:

```bash
python3 CW_RADAR_Waterfall_Mac.py
```

### FMCW Radar Waterfall

FMCW radar with range display, chirp bandwidth control, and beam steering:

```bash
python3 FMCW_RADAR_Waterfall_Mac.py
```

### Range-Doppler Plot

Live Range-Doppler map using TDD burst mode with matplotlib. This is the reference implementation for validating radar-web and tui-radar output -- it uses the same processing pipeline as ADI's original `Range_Doppler_Plot.py`.

Requires exclusive SDR access (stop radar-web first). On exit, the script reboots the PlutoSDR to reset the DMA engine for subsequent CW demos.

```bash
# Stop radar-web first, wait ~20s for Pluto reboot
ssh aleph-phaser@192.168.4.181 'sudo systemctl stop radar-web'
sleep 20

python3 Range_Doppler_Plot_Mac.py
```

Default parameters match the ADI Phaser lab reference: `ramp_time=300us`, `num_chirps=256`, `rx_gain=60`, `mti_filter=True`. Edit the configuration section at the top of the script to change these.

### CFAR Radar Waterfall

CFAR (Constant False Alarm Rate) target detection with adjustable parameters:

```bash
python3 CFAR_RADAR_Waterfall_Mac.py
```

Features: Plot/Apply CFAR threshold toggle, adjustable CFAR bias, guard cells, reference cells, beam steering control.

### FMCW Radar with ChirpSync

FMCW radar using the Pluto TDD engine for synchronized chirp FFT data collection.

**Limitation**: ChirpSync requires a physical sync cable between Phaser and PlutoSDR. In the Aleph hybrid architecture (PlutoSDR on Aleph, Phaser on Pi), there is no physical sync path, so this demo will likely timeout. Use `FMCW_RADAR_Waterfall_Mac.py` instead.

```bash
python3 FMCW_RADAR_Waterfall_ChirpSync_Mac.py
```

### CFAR Radar with ChirpSync

CFAR target detection using the Pluto TDD engine. Same ChirpSync limitation as above.

```bash
python3 CFAR_RADAR_Waterfall_ChirpSync_Mac.py
```

## Demo Summary

| Script | Radar Type | Works with Aleph? | Description |
|--------|------------|-------------------|-------------|
| `CW_RADAR_Waterfall_Mac.py` | CW | Yes | Basic continuous wave radar |
| `FMCW_RADAR_Waterfall_Mac.py` | FMCW | Yes | Frequency modulated, range display |
| `CFAR_RADAR_Waterfall_Mac.py` | CFAR | Yes | Target detection with adaptive threshold |
| `Range_Doppler_Plot_Mac.py` | Range-Doppler | Yes (stop radar-web first) | Live Range-Doppler map with TDD burst mode |
| `FMCW_RADAR_Waterfall_ChirpSync_Mac.py` | FMCW | No (needs sync cable) | TDD-synced chirp |
| `CFAR_RADAR_Waterfall_ChirpSync_Mac.py` | CFAR | No (needs sync cable) | TDD-synced CFAR |

## Configuration

Edit the IP addresses at the top of each script if your network differs:

```python
# Aleph IP - iiod proxies the PlutoSDR on port 30431
aleph_ip = "192.168.4.181"
sdr_ip = f"ip:{aleph_ip}"

# Raspberry Pi (Phaser) IP
phaser_ip = "192.168.4.184"
rpi_ip = f"ip:{phaser_ip}"
```

## Troubleshooting

### "file not found, loading default" messages

These messages come from pyadi-iio when loading Phaser calibration:
```
file not found, loading default (all gain at maximum)
file not found, loading default (no phase shift)
```

This is normal if you haven't run calibration on the Pi. The Phaser will work with default gain/phase values. To run calibration:

```bash
ssh analog@192.168.4.184
cd ~/pyadi-iio/examples/phaser
python3 phaser_prod_tst.py
```

Calibration files are stored on the Pi's filesystem, not the Aleph.

### Connection refused to Aleph

1. Check Aleph is reachable: `ping 192.168.4.181`
2. Check iio-proxy is running: `ssh aleph-phaser@192.168.4.181 'systemctl status iio-proxy'`
3. Check firewall allows port 30431

### Connection refused to Phaser/Pi

1. Check Pi is reachable: `ping 192.168.4.184`
2. Check iiod is running on Pi: `ssh analog@192.168.4.184 'systemctl status iiod'`

### Rx timeout errors (ETIMEDOUT)

If `sdr.rx()` times out with `[Errno 110]`:

1. **radar-web conflict**: Stop radar-web first: `ssh aleph-phaser@192.168.4.181 'sudo systemctl stop radar-web'` and wait ~20s for the Pluto to reboot.
2. **Stale Pluto DMA state**: If the Pluto was used with TDD burst mode (by radar-web or Range-Doppler), its DMA engine may be stuck. The scripts reboot the Pluto on exit, but if a script crashed, you may need to manually reboot: `ssh aleph-phaser@192.168.4.181 "python3 -c \"import paramiko; c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy()); c.connect('192.168.2.1',username='root',password='analog'); c.exec_command('reboot')\""` then wait ~20s.
3. **Restart iio-proxy**: `ssh aleph-phaser@192.168.4.181 'sudo systemctl restart iio-proxy'`

### Script hangs or Qt window unresponsive

1. Check PlutoSDR connection:
   ```bash
   ssh aleph-phaser@192.168.4.181 'iio_info -u ip:192.168.2.1 | head -5'
   ```
2. Power cycle the PlutoSDR if it's in a bad state

## Network Ports

| Service | Host | Port | Description |
|---------|------|------|-------------|
| iio-proxy (iiod) | Aleph (192.168.4.181) | 30431 | PlutoSDR IIO proxy (iiod serving ip:192.168.2.1) |
| iiod | Pi (192.168.4.184) | 30431 | Phaser control (native libiio daemon) |
