{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.plutosdr;
  
  # ADI's official udev rules for PlutoSDR
  plutoUdevRules = ''
    # Allow "plugdev" group read/write access to ADI PlutoSDR devices
    # DFU Mode
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b674", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a32", MODE="0664", GROUP="plugdev"
    # SDR Mode
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", MODE="0664", GROUP="plugdev"
    # Keep ModemManager from probing it
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", ENV{ID_MM_DEVICE_IGNORE}="1"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", ENV{ID_MM_DEVICE_IGNORE}="1"
  '';
in {
  options.services.plutosdr = {
    enable = mkEnableOption "PlutoSDR support for CN0566 Phaser";
    
    enableGnuRadio = mkOption {
      type = types.bool;
      default = false;
      description = "Enable GNU Radio support (heavier installation)";
    };
    
    enableNetworkServer = mkOption {
      type = types.bool;
      default = true;
      description = "Enable iiod network server to expose PlutoSDR over network (port 30431)";
    };
    
    enableGpuDemos = mkOption {
      type = types.bool;
      default = false;
      description = "Enable GPU-accelerated radar demos (CuPy for CUDA acceleration)";
    };
    
    users = mkOption {
      type = types.listOf types.str;
      default = [];
      description = "Users to add to plugdev and dialout groups for PlutoSDR access";
    };
  };

  config = mkIf cfg.enable {
    # GPU support: tell the shared python-env module to include CuPy
    aleph-phaser.enableGpu = mkIf cfg.enableGpuDemos true;

    # Core packages for PlutoSDR and Phaser
    # Note: Python environment is managed by nix/modules/python-env.nix (single env for everything)
    environment.systemPackages = with pkgs; [
      # Core IIO libraries
      libiio
      
      # libiio also provides iiod for network IIO proxy (used by iio-proxy service)
      
      # Phaser data files (filters, calibration, etc.)
      # Installed to /opt/phaser via symlink below
      phaser-data

      # Our custom PlutoSDR test tool
      test-plutosdr  # Available as 'test-plutosdr' command
    
      # Optional: GNU Radio stack
    ] ++ (optionals cfg.enableGnuRadio [
      gnuradio
      # Note: gr-iio would need to be packaged separately
    ]);
    
    # Create /opt/phaser symlink pointing to phaser-data files
    # This provides a stable path for scripts to reference:
    #   /opt/phaser/filters/LTE20_MHz.ftr
    #   /opt/phaser/calibration/...
    environment.etc."opt-phaser".source = "${pkgs.phaser-data}/share/phaser";
    
    # Create the actual /opt/phaser symlink
    systemd.tmpfiles.rules = [
      "L+ /opt/phaser - - - - /etc/opt-phaser"
    ];
    
    # Create the plugdev group
    users.groups.plugdev = {};
    
    # Add configured users to necessary groups
    users.users = builtins.listToAttrs (map (user: {
      name = user;
      value = {
        extraGroups = [ "plugdev" "dialout" ];
      };
    }) cfg.users);
    
    # Install udev rules for PlutoSDR
    services.udev.extraRules = plutoUdevRules;
    
    # Open firewall port for iiod if network server is enabled
    networking.firewall.allowedTCPPorts = mkIf cfg.enableNetworkServer [ 30431 ];
    
    # IIO daemon that proxies the PlutoSDR's IIO context to network clients.
    # iiod natively understands the IIO protocol including buffer streaming,
    # unlike the previous socat TCP relay which broke sdr.rx() operations.
    # Mac clients connect to Aleph:30431 and get full IIO access to the Pluto.
    systemd.services.iio-proxy = mkIf cfg.enableNetworkServer {
      description = "IIO Daemon - Serve PlutoSDR IIO context to network clients";
      after = [ "network.target" "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      
      serviceConfig = {
        Type = "simple";
        ExecStart = "${pkgs.libiio}/bin/iiod -u ip:192.168.2.1 -p 30431";
        Restart = "on-failure";
        RestartSec = "5s";
      };
    };
    
    # Optionally disable ModemManager if it causes issues
    # Uncomment if you experience device conflicts
    # services.modem-manager.enable = false;
  };
}
