# Shared Radar Configuration
#
# Defines aleph-phaser.radar.* options that are the single source of truth
# for radar hardware parameters. Both radar-web (systemd service) and
# tui-radar (wrapper binary) consume these values, ensuring consistent
# configuration across all frontends.
#
# Set these once in flake.nix and both apps use them automatically.

{ config, lib, ... }:

with lib;

{
  options.aleph-phaser.radar = {
    mode = mkOption {
      type = types.str;
      default = "hardware";
      description = ''
        Radar operating mode: "hardware" (PlutoSDR + Phaser) or "synthetic" (test patterns).
      '';
    };

    sdrUri = mkOption {
      type = types.str;
      default = "ip:192.168.2.1";
      description = "PlutoSDR URI. IP mode required: gpio_tdd_ext_sync not exposed over USB.";
    };

    phaserUri = mkOption {
      type = types.str;
      default = "ip:192.168.4.184";
      description = "Phaser board / Raspberry Pi URI (SPI control over WiFi).";
    };

    numChirps = mkOption {
      type = types.int;
      default = 128;
      description = ''
        Chirps per frame (Doppler bins). Controls velocity resolution and capture speed.
        128 = fast (~2 FPS), 256 = balanced (~1.3 FPS), 512 = full-res (~0.7 FPS).
      '';
    };

    rampTimeUs = mkOption {
      type = types.int;
      default = 100;
      description = ''
        FMCW chirp ramp time in microseconds. Controls range coverage and SDR data volume.
        100 = close-range/fast (360 bins, ~2 MB), 500 = full-range (1800 bins, ~8 MB).
      '';
    };

    maxRange = mkOption {
      type = types.float;
      default = 3.0;
      description = "Maximum display range in meters. 3.0 = desktop demo (~10 feet), 100.0 = full range.";
    };

    rxGain = mkOption {
      type = types.int;
      default = 30;
      description = ''
        Receive gain in dB (AD9361). Must be between -3 and 70.
        30 = conservative, 60 = ADI Phaser lab default (higher sensitivity).
      '';
    };

    dcSuppression = mkOption {
      type = types.bool;
      default = false;
      description = ''
        Enable DC leakage suppression (per-chirp mean subtraction).
        False matches the ADI Phaser lab reference. True removes stationary
        clutter but also removes all zero-Doppler content.
      '';
    };
  };
}
