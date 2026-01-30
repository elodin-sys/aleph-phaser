# TUI Radar Application
#
# GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser.
# Built with full features: GPU (CUDA/cudarc) and Python (PyO3/pyadi-iio).
#
# Uses rust-overlay for modern Rust toolchain (1.88+) to support latest crate ecosystem.
#
# Usage:
#   tui-radar --synthetic  # Run with synthetic data
#   tui-radar              # Run with live hardware

{ lib, makeRustPlatform, rust-bin, libiio, pkg-config, python3, cudaPackages, appsSrc }:

let
  # Use latest stable Rust from rust-overlay for modern crate support
  rustToolchain = rust-bin.stable.latest.default.override {
    targets = [ "aarch64-unknown-linux-gnu" ];
  };
  
  # Create a rustPlatform with the modern Rust toolchain
  rustPlatform = makeRustPlatform {
    cargo = rustToolchain;
    rustc = rustToolchain;
  };
  
  cudatoolkit = cudaPackages.cudatoolkit;
in
rustPlatform.buildRustPackage {
  pname = "tui-radar";
  version = "0.1.0";

  src = "${appsSrc}/tui-radar";
  cargoLock.lockFile = "${appsSrc}/tui-radar/Cargo.lock";

  nativeBuildInputs = [ 
    pkg-config 
    cudatoolkit  # Needed for nvcc during build
    python3      # Needed for PyO3 build script
  ];
  
  buildInputs = [
    libiio                        # For industrial-io crate (PlutoSDR)
    python3                       # For PyO3 (pyadi-iio control)
    cudatoolkit                   # For cudarc (GPU acceleration)
  ];

  # Build with all features: GPU + Python
  buildFeatures = [ "full" ];

  # Set CUDA environment for cudarc build
  CUDA_PATH = "${cudatoolkit}";
  CUDA_ROOT = "${cudatoolkit}";
  CUDA_TOOLKIT_ROOT_DIR = "${cudatoolkit}";

  # Ensure the Rust compiler can find CUDA libraries and nvcc
  CUDA_INCLUDE_PATH = "${cudatoolkit}/include";
  
  # Add nvcc to PATH during build
  preBuild = ''
    export PATH="${cudatoolkit}/bin:$PATH"
  '';

  meta = with lib; {
    description = "GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser";
    homepage = "https://github.com/elodin-sys/aleph-phaser";
    license = licenses.mit;
    platforms = [ "aarch64-linux" ];
    mainProgram = "tui-radar";
  };
}
