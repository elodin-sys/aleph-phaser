# Radar Web Service
#
# Optional systemd service for the WebGPU radar visualization server.
# Serves the web UI on port 8080; connect to Aleph IP (e.g. 192.168.4.181:8080).

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.radar-web;

  # Python environment with radar backend dependencies (numpy, pyadi-iio, paramiko).
  # pyadi-iio is a top-level overlay package, not in python3Packages.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    numpy
    paramiko
  ] ++ [ pkgs.pyadi-iio ]);

  # Build the ExecStart command line from config
  radarWebArgs = if cfg.mode == "synthetic" then
    [ "--synthetic" ]
  else
    [ "--sdr-uri" cfg.sdrUri "--phaser-uri" cfg.phaserUri ];

  fullArgs = radarWebArgs ++ [
    "--host" "0.0.0.0"
    "--port" (toString cfg.port)
    "--fps" (toString cfg.fps)
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
      };

      environment = {
        PYTHONHOME = "${pythonEnv}";
      };

      script = ''
        exec ${pkgs.radar-web}/bin/radar-web ${escapeShellArgs fullArgs}
      '';
    };
  };
}
