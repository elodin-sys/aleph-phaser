# TUI Radar Application
#
# GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser.
# Rust TUI with Python backend (PyO3) for radar processing via CuPy.
#
# This package builds from a Cargo workspace at the repository root.
# The radar-core library provides the PyO3 bridge to Python.
#
# Uses rust-overlay for modern Rust toolchain (1.88+) to support latest crate ecosystem.
#
# Usage:
#   tui-radar --synthetic  # Run with synthetic data
#   tui-radar              # Run with live hardware

{ lib, makeRustPlatform, rust-bin, pkg-config, python3, makeWrapper, workspaceSrc
, pythonEnv ? null, cudaPackages ? null, defaultArgs ? "" }:

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

  # Build from workspace root
  src = workspaceSrc;
  cargoLock.lockFile = "${workspaceSrc}/Cargo.lock";

  # Only build the tui-radar package from the workspace
  buildAndTestSubdir = "apps/tui-radar";
  
  nativeBuildInputs = [ 
    pkg-config 
    python3      # Needed for PyO3 build script
    makeWrapper  # For wrapping the binary with env vars
  ];
  
  buildInputs = [
    python3      # For PyO3 (Python embedding)
  ];

  # Set Python path for PyO3 build
  PYO3_PYTHON = "${python3}/bin/python3";

  # Install the Python backend and tools from radar-core
  postInstall = ''
    mkdir -p $out/lib/python
    cp ${workspaceSrc}/libs/radar-core/python/*.py $out/lib/python/
  '';

  # Set up runtime environment to find Python module and CUDA headers.
  # PYTHONHOME must point to the unified Python env (with CuPy, pyadi-iio, etc.)
  # so the PyO3-embedded interpreter finds all site-packages.
  # CUDA vars are needed for CuPy JIT kernel compilation.
  postFixup = let
    envArgs = lib.concatStringsSep " "
      (lib.optional (pythonEnv != null) "--set PYTHONHOME \"${pythonEnv}\""
       ++ lib.optionals (cudaPackages != null) [
         "--set CUDA_PATH \"${cudaPackages.cudatoolkit}\""
         "--set CUPY_INCLUDE_PATH \"${cudaPackages.cudatoolkit}/include\""
       ]);
    # Default CLI flags baked into the wrapper (e.g. radar params from shared config).
    # User can still override any flag on the command line (clap takes the last value).
    flagsArg = lib.optionalString (defaultArgs != "") ''--add-flags "${defaultArgs}"'';
  in ''
    wrapProgram $out/bin/tui-radar \
      --set RADAR_BACKEND_PATH "$out/lib/python" \
      --prefix PYTHONPATH : "$out/lib/python" \
      ${envArgs} \
      ${flagsArg}
  '';

  meta = with lib; {
    description = "GPU-accelerated Range-Doppler radar TUI for CN0566 Phaser";
    homepage = "https://github.com/elodin-sys/aleph-phaser";
    license = licenses.mit;
    platforms = [ "aarch64-linux" ];
    mainProgram = "tui-radar";
  };
}
