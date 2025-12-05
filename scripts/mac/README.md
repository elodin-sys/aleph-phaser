# Mac-based Phaser Demos

Run Phaser demos with Qt visualization on your Mac while the hardware is connected to Aleph.

## Architecture

```
┌─────────────────┐                    ┌─────────────────────┐
│      Mac        │◄─── Network ──────►│  Aleph (socat)      │
│  (Qt Display)   │    port 30431      │  TCP proxy to Pluto │
│                 │                    │  192.168.4.181      │
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
ssh aleph-phaser@192.168.4.181 'systemctl status iiod'
```

If not running:
```bash
ssh aleph-phaser@192.168.4.181 'sudo systemctl start iiod'
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

## Configuration

Edit the IP addresses at the top of each script if your network differs:

```python
# Aleph IP - iiod proxies the PlutoSDR on port 30431
aleph_ip = "192.168.4.181"
sdr_ip = f"ip:{aleph_ip}:30431"

# Raspberry Pi (Phaser) IP
phaser_ip = "192.168.4.184"
rpi_ip = f"ip:{phaser_ip}"
```

## Troubleshooting

### Connection refused to Aleph

1. Check Aleph is reachable: `ping 192.168.4.181`
2. Check iiod is running: `ssh aleph-phaser@192.168.4.181 'systemctl status iiod'`
3. Check firewall allows port 30431

### Connection refused to Phaser/Pi

1. Check Pi is reachable: `ping 192.168.4.184`
2. Check iiod is running on Pi: `ssh analog@192.168.4.184 'systemctl status iiod'`

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
| iiod | Aleph (192.168.4.181) | 30431 | PlutoSDR proxy |
| iiod | Pi (192.168.4.184) | 30431 | Phaser control |
