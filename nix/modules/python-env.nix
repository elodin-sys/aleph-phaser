# Unified Python Environment for Aleph Phaser
#
# Single Python environment used by all services and interactive sessions on the Aleph.
# Avoids multiple python3.withPackages declarations that cause Nix profile collisions.
#
# Usage in other modules:
#   config.aleph-phaser.pythonEnv   — the Python derivation (for PYTHONHOME, systemPackages, etc.)
#   config.aleph-phaser.cudaEnv     — attrset of CUDA env vars (CUDA_PATH, LD_LIBRARY_PATH, etc.)

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.aleph-phaser;
  hasCuda = pkgs ? cudaPackages;
in {
  options.aleph-phaser = {
    enableGpu = mkOption {
      type = types.bool;
      default = false;
      description = "Include CuPy and set CUDA environment variables for GPU acceleration";
    };

    pythonEnv = mkOption {
      type = types.package;
      readOnly = true;
      description = "The unified Python environment for all Aleph Phaser services and scripts";
    };

    cudaEnv = mkOption {
      type = types.attrsOf types.str;
      readOnly = true;
      description = "CUDA-related environment variables (empty attrset when GPU is disabled)";
    };
  };

  config = {
    # The one and only Python environment.
    # Superset of everything plutosdr scripts, radar-web, tui-radar, and interactive use need.
    aleph-phaser.pythonEnv = pkgs.python3.withPackages (ps: with ps; [
      # Core scientific stack
      numpy
      scipy
      matplotlib

      # Network / remote Phaser
      paramiko

      # Demo / utility
      psutil
      pillow
    ]
    # pyadi-iio is a top-level overlay package, not in python3Packages
    ++ [ pkgs.pyadi-iio ]
    ++ (optionals (cfg.enableGpu && hasCuda) [
      cupy
    ]));

    # CUDA env vars for services (radar-web, etc.).
    # Systemd services don't inherit session/environment variables, so we provide an
    # explicit attrset they can merge into their `environment` block.
    # LD_LIBRARY_PATH: use aleph-dev's value if set (driver + L4T libs); otherwise fall back
    # to cudatoolkit lib path so CuPy can at least find libcudart etc. (libcuda.so.1 is
    # typically from the system/JetPack driver on Jetson).
    aleph-phaser.cudaEnv = optionalAttrs (cfg.enableGpu && hasCuda) ({
      CUDA_PATH = "${pkgs.cudaPackages.cudatoolkit}";
      CUPY_INCLUDE_PATH = "${pkgs.cudaPackages.cudatoolkit}/include";
      LD_LIBRARY_PATH = if config.environment.variables ? LD_LIBRARY_PATH
        then config.environment.variables.LD_LIBRARY_PATH
        else "${pkgs.cudaPackages.cudatoolkit}/lib";
    });

    # Install the unified Python env into the system profile so `python3` on the
    # Aleph always has everything.
    # Note: we do NOT set environment.sessionVariables for CUDA here — the upstream
    # aleph-dev module already sets LD_LIBRARY_PATH etc. for interactive sessions.
    environment.systemPackages = [ cfg.pythonEnv ];
  };
}
