# Phaser Data Files

This directory contains data files that are deployed to the Aleph at `/opt/phaser/`.

## Directory Structure

```
data/
├── filters/              # SDR filter files (.ftr)
│   ├── LTE5_MHz.ftr
│   ├── LTE10_MHz.ftr
│   └── LTE20_MHz.ftr
├── calibration/          # Calibration files (future)
└── README.md
```

## Deployment

Files in this directory are automatically deployed to the Aleph when you run:

```bash
./deploy.sh -h <aleph-ip> -u aleph-phaser
```

They are installed to `/opt/phaser/` on the device:
- `/opt/phaser/filters/LTE20_MHz.ftr`
- `/opt/phaser/calibration/...`

## Usage in Scripts

Reference deployed files using absolute paths:

```python
# Load a filter file
my_sdr.filter = "/opt/phaser/filters/LTE20_MHz.ftr"

# Load calibration data (future)
with open("/opt/phaser/calibration/gain_cal.json") as f:
    cal_data = json.load(f)
```

## Adding New Data Files

1. **Add files to the appropriate subdirectory:**
   ```bash
   cp my_new_filter.ftr data/filters/
   ```

2. **For a new category, create a subdirectory:**
   ```bash
   mkdir -p data/calibration
   cp gain_cal.json data/calibration/
   ```

3. **Update `nix/pkgs/phaser-data.nix` if adding a new category:**
   ```nix
   # In installPhase, add:
   if [ -d calibration ]; then
     mkdir -p $out/share/phaser/calibration
     cp -r calibration/* $out/share/phaser/calibration/
   fi
   ```

4. **Deploy to Aleph:**
   ```bash
   ./deploy.sh -h <aleph-ip> -u aleph-phaser
   ```

## Filter Files

The LTE filter files configure the AD9361's FIR filter for different bandwidths:

| File | Bandwidth | Use Case |
|------|-----------|----------|
| `LTE5_MHz.ftr` | 5 MHz | Narrow band, lower sample rate |
| `LTE10_MHz.ftr` | 10 MHz | Medium bandwidth |
| `LTE20_MHz.ftr` | 20 MHz | Wide band (default for Phaser) |

These are downloaded from [pyadi-iio examples](https://github.com/analogdevicesinc/pyadi-iio/tree/main/examples/phaser).
