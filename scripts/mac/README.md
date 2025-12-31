# Mac-based Phaser Demos

Run Phaser demos with Qt visualization on your Mac while the hardware is connected to Aleph.

## Architecture

```
┌─────────────────┐                    ┌─────────────────────┐
│      Mac        │◄─── Network ──────►│  Aleph (socat)      │
│  (Qt Display)   │    port 30431      │  TCP proxy to Pluto │
│                 │                    │  192.168.4.186      │
│  pyadi-iio      │                    └─────────────────────┘
│  PyQt5          │                              │
│  pyqtgraph      │                              │ USB-Ethernet
└────────┬────────┘                              ▼
         │                             ┌─────────────────┐
         │                             │    PlutoSDR     │
         │                             │  192.168.2.1    │
         │                             └─────────────────┘
         │
         │◄──── Network ──────────────►┌─────────────────┐
                                       │  Raspberry Pi   │
                                       │  (Phaser iiod)  │
                                       │  192.168.4.184  │
                                       └─────────────────┘
```

The Aleph runs a socat TCP proxy that forwards port 30431 to the PlutoSDR,
allowing Mac clients to access the SDR over the network.

## Setup

### 1. Install Python dependencies on Mac (using uv)

```bash
cd scripts/mac

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv sync
```

Or install with pip if you prefer:
```bash
pip install -r requirements.txt
```

### 2. Ensure iiod is running on Aleph

The Aleph runs an iiod server that proxies PlutoSDR access over the network.

Check status:
```bash
ssh aleph-phaser@192.168.4.186 'systemctl status iiod'
```

If not running:
```bash
ssh aleph-phaser@192.168.4.186 'sudo systemctl start iiod'
```

### 3. Verify Phaser/Pi is accessible

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

### FMCW Radar with ChirpSync

FMCW radar using the Pluto TDD engine for synchronized chirp FFT data collection.

⚠️ **Limitation**: ChirpSync requires a **physical sync cable** between Phaser and PlutoSDR.
In the Aleph hybrid architecture (PlutoSDR on Aleph, Phaser on Pi), there is no physical
sync path, so this demo will likely timeout. Use `FMCW_RADAR_Waterfall_Mac.py` instead.

```bash
python3 FMCW_RADAR_Waterfall_ChirpSync_Mac.py
```

### CFAR Radar Waterfall

CFAR (Constant False Alarm Rate) target detection with adjustable parameters:

```bash
python3 CFAR_RADAR_Waterfall_Mac.py
```

Features:
- Plot/Apply CFAR threshold toggle
- Adjustable CFAR bias, guard cells, and reference cells
- Beam steering control

### CFAR Radar with ChirpSync

CFAR target detection using the Pluto TDD engine for synchronized chirp collection.

⚠️ **Limitation**: ChirpSync requires a **physical sync cable** between Phaser and PlutoSDR.
In the Aleph hybrid architecture (PlutoSDR on Aleph, Phaser on Pi), there is no physical
sync path, so this demo will likely timeout. Use `CFAR_RADAR_Waterfall_Mac.py` instead.

```bash
python3 CFAR_RADAR_Waterfall_ChirpSync_Mac.py
```

## Demo Summary

| Script | Radar Type | Works with Aleph? | Description |
|--------|------------|-------------------|-------------|
| `CW_RADAR_Waterfall_Mac.py` | CW | ✅ Yes | Basic continuous wave radar |
| `FMCW_RADAR_Waterfall_Mac.py` | FMCW | ✅ Yes | Frequency modulated, range display |
| `CFAR_RADAR_Waterfall_Mac.py` | CFAR | ✅ Yes | Target detection with adaptive threshold |
| `FMCW_RADAR_Waterfall_ChirpSync_Mac.py` | FMCW | ⚠️ No* | TDD-synced chirp (needs sync cable) |
| `CFAR_RADAR_Waterfall_ChirpSync_Mac.py` | CFAR | ⚠️ No* | TDD-synced CFAR (needs sync cable) |

\* ChirpSync demos require a physical sync cable between Phaser and PlutoSDR which doesn't exist in the Aleph hybrid setup.

## Configuration

Edit the IP addresses at the top of each script if your network differs:

```python
# Aleph IP - iiod proxies the PlutoSDR on port 30431
aleph_ip = "192.168.4.186"
sdr_ip = f"ip:{aleph_ip}:30431"

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

**This is normal** if you haven't run calibration on the Pi. The Phaser will work with
default gain/phase values. To run calibration:

```bash
ssh analog@192.168.4.184
cd ~/pyadi-iio/examples/phaser
python3 phaser_prod_tst.py
```

Note: Calibration files are stored on the Pi's filesystem, not the Aleph.

### Connection refused to Aleph

1. Check Aleph is reachable: `ping 192.168.4.186`
2. Check iiod is running: `ssh aleph-phaser@192.168.4.186 'systemctl status iiod'`
3. Check firewall allows port 30431

### Connection refused to Phaser/Pi

1. Check Pi is reachable: `ping 192.168.4.184`
2. Check iiod is running on Pi: `ssh analog@192.168.4.184 'systemctl status iiod'`

### Script hangs or times out

If the Qt window opens but becomes unresponsive, or you see timeout errors:

1. **Check PlutoSDR connection**: The Pluto may have lost its USB connection
   ```bash
   ssh aleph-phaser@192.168.4.186 'iio_info -u ip:192.168.2.1 | head -5'
   ```

2. **Restart the iio-proxy service on Aleph**:
   ```bash
   ssh aleph-phaser@192.168.4.186 'sudo systemctl restart iio-proxy'
   ```

3. **Power cycle the PlutoSDR** if it's in a bad state

### "No module named 'iio'"

Install pyadi-iio which includes the Python bindings:
```bash
pip install pyadi-iio
```

### PyQt5 errors on macOS

If you see Qt platform plugin errors:
```bash
pip install --upgrade PyQt5
```

Or try using a Python from Homebrew:
```bash
brew install python@3.11
/opt/homebrew/bin/python3.11 -m pip install -r requirements.txt
```

## Network Ports

| Service | Host | Port | Description |
|---------|------|------|-------------|
| iiod | Aleph (192.168.4.186) | 30431 | PlutoSDR proxy |
| iiod | Pi (192.168.4.184) | 30431 | Phaser control |
