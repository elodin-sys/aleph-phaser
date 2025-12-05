# Phaser Data Files

This directory contains data files that are deployed to the Aleph at `/opt/phaser/`.

## Directory Structure

```
data/
├── filters/                          # SDR filter files (.ftr)
│   ├── LTE5_MHz.ftr                  # (for reference, fetched from URL)
│   ├── LTE10_MHz.ftr
│   └── LTE20_MHz.ftr
├── calibration/                      # Calibration files (LOCAL)
│   └── example_gain_cal.json         # Example calibration file
└── README.md
```

## How It Works

The `phaser-data` Nix package handles two types of files:

1. **URL-fetched files** (filters) - Downloaded from ADI's GitHub during build
2. **Local files** (calibration, configs) - Copied from this `data/` directory

This hybrid approach means:
- Standard filters are always available without committing large files
- Custom calibration data can be version-controlled with your project

## Deployment

Files are automatically deployed when you run:

```bash
./deploy.sh -h <aleph-ip> -u aleph-phaser
```

They are installed to `/opt/phaser/` on the device:
- `/opt/phaser/filters/LTE20_MHz.ftr`
- `/opt/phaser/calibration/example_gain_cal.json`

## Usage in Scripts

```python
# Load a filter file
my_sdr.filter = "/opt/phaser/filters/LTE20_MHz.ftr"

# Load calibration data
import json
with open("/opt/phaser/calibration/example_gain_cal.json") as f:
    cal_data = json.load(f)
    
# Apply calibration
for i, gain in cal_data["element_gains"].items():
    my_phaser.set_chan_gain(int(i), int(127 * gain), apply_cal=False)
```

## Adding New Files

### Option 1: Local Files (calibration, custom configs)

Just add files to the appropriate subdirectory:

```bash
# Add calibration data
cp my_board_calibration.json data/calibration/

# Add custom waveforms
mkdir -p data/waveforms
cp my_waveform.csv data/waveforms/

# IMPORTANT: Add to git (required for Nix flakes)
git add data/

# Deploy
./deploy.sh -h <aleph-ip> -u aleph-phaser
```

Supported directories (auto-detected):
- `calibration/` - Calibration files
- `waveforms/` - Waveform data
- `configs/` - Configuration files
- `filters/` - Custom filter files (overrides URL versions)

### Option 2: URL-fetched Files (standard filters)

For files from external URLs, edit `nix/pkgs/phaser-data.nix`:

```nix
# Add a new fetchurl
my_filter = fetchurl {
  url = "https://example.com/my_filter.ftr";
  sha256 = "<hash>";  # Get with: nix-prefetch-url <url>
};

# Add to installPhase
cp ${my_filter} $out/share/phaser/filters/my_filter.ftr
```

## Filter Files

| File | Bandwidth | Source |
|------|-----------|--------|
| `LTE5_MHz.ftr` | 5 MHz | URL (ADI GitHub) |
| `LTE10_MHz.ftr` | 10 MHz | URL (ADI GitHub) |
| `LTE20_MHz.ftr` | 20 MHz | URL (ADI GitHub) |

## Calibration Files

| File | Description | Source |
|------|-------------|--------|
| `example_gain_cal.json` | Example gain calibration | Local |

To create calibration for your specific board, copy and modify the example:

```bash
cp data/calibration/example_gain_cal.json data/calibration/my_board_SN12345.json
# Edit with your measured values
```
