{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.gpu-radar;
in {
  options.services.gpu-radar = {
    enable = mkEnableOption "GPU-accelerated radar signal processing";
    
    enableVisualization = mkOption {
      type = types.bool;
      default = true;
      description = "Enable visualization packages (matplotlib, etc.)";
    };
  };

  config = mkIf cfg.enable {
    # GPU radar demos rely on Python packages from plutosdr module
    # This module only adds helper scripts and configuration
    # CuPy will be installed via pip since nixpkgs doesn't have aarch64 CUDA wheels
    environment.systemPackages = with pkgs; [
      # No additional Python - use the one from plutosdr module
    ];
    
    # Create a setup script for installing CuPy
    environment.etc."gpu-radar/setup-cupy.sh" = {
      mode = "0755";
      text = ''
        #!/bin/bash
        # Setup script for CuPy on Jetson Orin NX
        # Run this once after deployment to install GPU packages
        
        set -e
        
        echo "============================================================"
        echo "Setting up CuPy for GPU-accelerated radar processing..."
        echo "============================================================"
        
        # Create a virtual environment if it doesn't exist
        VENV_PATH="$HOME/.gpu-radar-venv"
        if [ ! -d "$VENV_PATH" ]; then
          echo "Creating virtual environment at $VENV_PATH"
          python3 -m venv "$VENV_PATH" --system-site-packages
        fi
        
        # Activate and install CuPy
        source "$VENV_PATH/bin/activate"
        
        # Install CuPy with CUDA support
        # cupy-cuda12x is for CUDA 12.x (JetPack 6.x uses CUDA 12.2)
        echo "Installing CuPy (this may take a few minutes on first run)..."
        pip install --upgrade pip
        pip install cupy-cuda12x
        
        echo ""
        echo "============================================================"
        echo "Setup complete!"
        echo "============================================================"
        echo ""
        echo "To use the GPU radar demos:"
        echo "  source $VENV_PATH/bin/activate"
        echo "  python3 /path/to/gpu_benchmark.py"
        echo ""
        echo "To verify CuPy installation:"
        echo "  python3 -c 'import cupy; print(f\"GPU count: {cupy.cuda.runtime.getDeviceCount()}\")'"
        echo ""
      '';
    };
    
    # Copy GPU demo scripts to a known location
    environment.etc."gpu-radar/README.txt" = {
      mode = "0644";
      text = ''
        GPU-Accelerated Radar Signal Processing Demos
        ==============================================
        
        These demos showcase radar processing capabilities that are
        impractical on Raspberry Pi but run smoothly on the Orin NX GPU.
        
        SETUP:
          1. Run the setup script to install CuPy:
             /etc/gpu-radar/setup-cupy.sh
          
          2. Copy demo scripts from the repository to the device
          
          3. Activate the virtual environment:
             source ~/.gpu-radar-venv/bin/activate
        
        DEMOS:
          - gpu_benchmark.py: Full performance comparison
          - gpu_range_doppler.py: Range-Doppler map processing  
          - gpu_cfar.py: CFAR target detection
          - gpu_micro_doppler.py: Drone detection via micro-Doppler
        
        All demos can run with synthetic data (no hardware required):
          python3 gpu_benchmark.py --output-dir /tmp/results
        
        For live Phaser data:
          python3 gpu_range_doppler.py --sdr-uri ip:192.168.2.1 \
                                       --phaser-uri ip:192.168.4.184
      '';
    };
  };
}
