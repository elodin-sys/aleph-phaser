# TUI Radar Application
#
# GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser.
# Rust TUI with Python backend (PyO3) for radar processing via CuPy.
#
# Uses rust-overlay for modern Rust toolchain (1.88+) to support latest crate ecosystem.
#
# Usage:
#   tui-radar --synthetic  # Run with synthetic data
#   tui-radar              # Run with live hardware

{ lib, makeRustPlatform, rust-bin, pkg-config, python3, appsSrc }:

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
in
rustPlatform.buildRustPackage {
  pname = "tui-radar";
  version = "0.1.0";

  src = "${appsSrc}/tui-radar";
  cargoLock.lockFile = "${appsSrc}/tui-radar/Cargo.lock";

  nativeBuildInputs = [ 
    pkg-config 
    python3      # Needed for PyO3 build script
  ];
  
  buildInputs = [
    python3      # For PyO3 (Python embedding)
  ];

  # No build features needed - Python is always required
  # buildFeatures = [];

  # Set Python path for PyO3 build
  PYO3_PYTHON = "${python3}/bin/python3";

  meta = with lib; {
    description = "GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser";
    homepage = "https://github.com/elodin-sys/aleph-phaser";
    license = licenses.mit;
    platforms = [ "aarch64-linux" ];
    mainProgram = "tui-radar";
  };
}
