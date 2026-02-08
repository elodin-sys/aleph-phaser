#!/usr/bin/env python3
"""
Capture a single full-resolution frame from hardware and save to exports/.

Run on the device (e.g. via SSH) to export a frame for offline validation
without needing the web UI. Usage:

  python capture_one_frame.py
  python capture_one_frame.py --output /tmp/exports --sdr-uri ip:192.168.2.1 --phaser-uri ip:192.168.4.184
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Capture one full-resolution frame from radar hardware")
    parser.add_argument("--output", "-o", default="./exports", help="Output directory")
    parser.add_argument("--sdr-uri", default="ip:192.168.2.1", help="PlutoSDR URI")
    parser.add_argument("--phaser-uri", default="ip:192.168.4.184", help="Phaser URI")
    args = parser.parse_args()

    from radar_backend import create_backend

    print("Initializing hardware backend...")
    backend = create_backend(mode="hardware", sdr_uri=args.sdr_uri, phaser_uri=args.phaser_uri)
    print("Capturing one full-resolution frame...")
    frame = backend.get_frame_full_resolution()
    print(f"Frame shape: {frame.shape}")

    os.makedirs(args.output, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frame_path = os.path.join(args.output, f"frame_{timestamp}.npy")
    meta_path = os.path.join(args.output, f"frame_{timestamp}_meta.json")

    import numpy as np
    np.save(frame_path, frame)
    metadata = {
        "timestamp": timestamp,
        "shape": list(frame.shape),
        "dtype": str(frame.dtype),
        "min": float(frame.min()),
        "max": float(frame.max()),
        "mean": float(frame.mean()),
        "std": float(frame.std()),
        "config": backend.get_config(),
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved {frame_path}")
    print(f"Saved {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
