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
    
    users = mkOption {
      type = types.listOf types.str;
      default = [];
      description = "Users to add to plugdev and dialout groups for PlutoSDR access";
    };
  };

  config = mkIf cfg.enable {
    # Core packages for PlutoSDR and Phaser
    environment.systemPackages = with pkgs; [
      # Core IIO libraries
      libiio
      
      # Python environment with necessary packages
      (python3.withPackages (ps: with ps; [
        # Core dependencies
        numpy
        matplotlib
        scipy
        
        # ADI hardware control - properly packaged
        pyadi-iio  # Includes pylibiio dependency
        
        # Additional useful packages
        # ipython
        # jupyter
        
        # Network communication (for remote Phaser)
        paramiko
      ]))
      
      # Optional: GNU Radio stack
    ] ++ (optionals cfg.enableGnuRadio [
      gnuradio
      # Note: gr-iio would need to be packaged separately
    ]);
    
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
    
    # Optionally disable ModemManager if it causes issues
    # Uncomment if you experience device conflicts
    # services.modem-manager.enable = false;
  };
}
