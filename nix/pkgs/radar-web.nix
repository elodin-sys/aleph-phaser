# Radar Web Application
#
# WebGPU radar visualization web server with WASM client.
# Streams full-resolution frames via WebSocket to browser clients.
#
# This package:
# 1. Builds the Axum server (radar-web) from the Cargo workspace
# 2. Builds the WASM client (radar-web-client) with wasm-pack
# 3. Bundles the WASM artifacts into static/ for serving
#
# Usage:
#   radar-web --synthetic    # Run with synthetic data on :8080
#   radar-web --sdr-uri ip:X --phaser-uri ip:X  # Run with hardware

{ lib
, makeRustPlatform
, rust-bin
, pkg-config
, python3
, makeWrapper
, workspaceSrc
, wasm-pack
, wasm-bindgen-cli
, binaryen
}:

let
  # Use latest stable Rust from rust-overlay with WASM target
  rustToolchain = rust-bin.stable.latest.default.override {
    targets = [ "aarch64-unknown-linux-gnu" "wasm32-unknown-unknown" ];
  };
  
  # Create a rustPlatform with the modern Rust toolchain
  rustPlatform = makeRustPlatform {
    cargo = rustToolchain;
    rustc = rustToolchain;
  };
in
rustPlatform.buildRustPackage {
  pname = "radar-web";
  version = "0.1.0";

  # Build from workspace root
  src = workspaceSrc;
  cargoLock.lockFile = "${workspaceSrc}/Cargo.lock";

  # Build the server package from the workspace
  buildAndTestSubdir = "apps/radar-web";
  
  nativeBuildInputs = [ 
    pkg-config 
    python3         # Needed for PyO3 build script
    makeWrapper     # For wrapping the binary with env vars
    wasm-pack       # For building WASM client
    wasm-bindgen-cli
    binaryen        # For wasm-opt optimization
  ];
  
  buildInputs = [
    python3         # For PyO3 (Python embedding)
  ];

  # Set Python path for PyO3 build
  PYO3_PYTHON = "${python3}/bin/python3";

  # Build WASM client after main cargo build
  postBuild = ''
    echo "Building WASM client..."
    cd apps/radar-web/client
    
    # Build in release mode
    wasm-pack build --target web --release --out-dir pkg
    
    # Optimize WASM binary
    ${binaryen}/bin/wasm-opt -Oz pkg/radar_web_client_bg.wasm -o pkg/radar_web_client_bg.wasm
    
    cd ../../..
  '';

  # Install the server, WASM client, and Python backend
  postInstall = ''
    # Copy WASM artifacts to static directory
    mkdir -p $out/share/radar-web/static
    cp apps/radar-web/static/index.html $out/share/radar-web/static/
    cp apps/radar-web/client/pkg/radar_web_client.js $out/share/radar-web/static/
    cp apps/radar-web/client/pkg/radar_web_client_bg.wasm $out/share/radar-web/static/
    
    # Copy Python backend
    mkdir -p $out/lib/python
    cp ${workspaceSrc}/libs/radar-core/python/*.py $out/lib/python/
  '';

  # Set up runtime environment
  postFixup = ''
    wrapProgram $out/bin/radar-web \
      --set RADAR_BACKEND_PATH "$out/lib/python" \
      --prefix PYTHONPATH : "$out/lib/python" \
      --set RADAR_WEB_STATIC_DIR "$out/share/radar-web/static"
  '';

  meta = with lib; {
    description = "WebGPU radar visualization web server for CN0566 Phaser";
    homepage = "https://github.com/elodin-sys/aleph-phaser";
    license = licenses.mit;
    platforms = [ "aarch64-linux" "x86_64-linux" ];
    mainProgram = "radar-web";
  };
}
