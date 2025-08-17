{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.example;
in {
  options.services.example = {
    enable = mkEnableOption "Example";
  };

  config = mkIf cfg.enable {
    environment.systemPackages = [ pkgs.example ];

    systemd.services.example = {
      description = "Example";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      serviceConfig = {
        ExecStart = "${pkgs.example}/bin/example";
        Restart = "always";
        RestartSec = "10";
        DynamicUser = true;
        StateDirectory = "example";
        WorkingDirectory = "/var/lib/example";
      };
    };
  };
} 
