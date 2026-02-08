# Radar Web Service
#
# Optional systemd service for the WebGPU radar visualization server.
# Serves the web UI on port 8080; connect to Aleph IP (e.g. 192.168.4.181:8080).
#
# Radar parameters (mode, sdrUri, phaserUri, numChirps, rampTimeUs, maxRange)
# are inherited from the shared aleph-phaser.radar.* config by default.
# Service-specific options can override them if needed.
#
# Python environment and CUDA env vars come from nix/modules/python-env.nix.

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.radar-web;
  rcfg = config.aleph-phaser.radar;

  # Build the ExecStart command line from config
  radarWebArgs = if cfg.mode == "synthetic" then
    [ "--synthetic" ]
  else
    [ "--sdr-uri" cfg.sdrUri "--phaser-uri" cfg.phaserUri ];

  fullArgs = radarWebArgs ++ [
    "--host" "0.0.0.0"
    "--port" (toString cfg.port)
    "--fps" (toString cfg.fps)
    "--num-chirps" (toString cfg.numChirps)
    "--ramp-time-us" (toString cfg.rampTimeUs)
    "--max-range" (toString cfg.maxRange)
  ];
in {
  options.services.radar-web = {
    enable = mkEnableOption "radar-web WebGPU visualization server";

    # Radar parameters default to the shared config but can be overridden per-service.
    mode = mkOption {
      type = types.str;
      default = rcfg.mode;
      description = "Run mode: \"synthetic\" (no hardware) or \"hardware\" (PlutoSDR + Phaser). Defaults to aleph-phaser.radar.mode.";
    };

    sdrUri = mkOption {
      type = types.str;
      default = rcfg.sdrUri;
      description = "PlutoSDR URI. Defaults to aleph-phaser.radar.sdrUri.";
    };

    phaserUri = mkOption {
      type = types.str;
      default = rcfg.phaserUri;
      description = "Phaser board URI. Defaults to aleph-phaser.radar.phaserUri.";
    };

    numChirps = mkOption {
      type = types.int;
      default = rcfg.numChirps;
      description = "Number of chirps per frame (Doppler bins). Defaults to aleph-phaser.radar.numChirps.";
    };

    rampTimeUs = mkOption {
      type = types.int;
      default = rcfg.rampTimeUs;
      description = "Chirp ramp time in microseconds. Defaults to aleph-phaser.radar.rampTimeUs.";
    };

    maxRange = mkOption {
      type = types.float;
      default = rcfg.maxRange;
      description = "Maximum display range in meters. Defaults to aleph-phaser.radar.maxRange.";
    };

    # Service-specific options (not shared)
    port = mkOption {
      type = types.port;
      default = 8080;
      description = "HTTP port for the web UI";
    };

    fps = mkOption {
      type = types.int;
      default = 20;
      description = "Target frame rate (conservative for Aleph)";
    };
  };

  config = mkIf cfg.enable {
    environment.systemPackages = [ pkgs.radar-web ];

    systemd.services.radar-web = {
      description = "Radar Web - WebGPU visualization server for CN0566 Phaser";
      after = [ "network.target" "network-online.target" ] ++ optional config.services.plutosdr.enable "iio-proxy.service";
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        Type = "simple";
        Restart = "on-failure";
        RestartSec = "5s";
        User = "aleph-phaser";
        Group = "users";
        # Writable cache for CuPy JIT kernel compilation
        CacheDirectory = "radar-web";
        # Export path: ./exports -> /var/lib/radar-web/exports
        StateDirectory = "radar-web";
        WorkingDirectory = "/var/lib/radar-web";
      };

      # Use the unified Python env from python-env.nix, plus CUDA vars if GPU is on.
      environment = {
        PYTHONHOME = "${config.aleph-phaser.pythonEnv}";
        CUPY_CACHE_DIR = "/var/cache/radar-web/cupy";
      } // config.aleph-phaser.cudaEnv;

      script = ''
        exec ${pkgs.radar-web}/bin/radar-web ${escapeShellArgs fullArgs}
      '';
    };
  };
}
