# Radar Web Service
#
# Optional systemd service for the WebGPU radar visualization server.
# Serves the web UI on port 8080; connect to Aleph IP (e.g. 192.168.4.181:8080).
#
# Python environment and CUDA env vars come from nix/modules/python-env.nix.

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.radar-web;

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
  ];
in {
  options.services.radar-web = {
    enable = mkEnableOption "radar-web WebGPU visualization server";

    mode = mkOption {
      type = types.str;
      default = "hardware";
      description = "Run mode: \"synthetic\" (no hardware) or \"hardware\" (PlutoSDR + Phaser)";
    };

    sdrUri = mkOption {
      type = types.str;
      default = "ip:192.168.2.1";
      description = "PlutoSDR URI (e.g. ip:192.168.2.1 for USB-ethernet)";
    };

    phaserUri = mkOption {
      type = types.str;
      default = "ip:192.168.4.184";
      description = "Phaser board URI (e.g. ip:192.168.4.184 over WiFi)";
    };

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

    numChirps = mkOption {
      type = types.int;
      default = 256;
      description = "Number of chirps per frame (Doppler bins). More chirps = finer velocity resolution but slower capture. 128-512 typical.";
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
