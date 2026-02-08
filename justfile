# Justfile for aleph-phaser project
# Run all commands from repo root inside `nix develop` shell

# Default recipe
default:
    @just --list

# Build and run radar-web (full rebuild)
radar-web:
    @echo "==> Building WASM client..."
    cd apps/radar-web/client && wasm-pack build --target web --dev
    @echo "==> Copying WASM artifacts to static..."
    cp -r apps/radar-web/client/pkg/* apps/radar-web/static/
    @echo "==> Starting radar-web server..."
    cargo run -p radar-web -- --synthetic

# Build radar-web release (optimized)
radar-web-release:
    @echo "==> Building WASM client (release)..."
    cd apps/radar-web/client && wasm-pack build --target web --release
    @echo "==> Copying WASM artifacts to static..."
    cp -r apps/radar-web/client/pkg/* apps/radar-web/static/
    @echo "==> Starting radar-web server..."
    cargo run -p radar-web --release -- --synthetic

# Build WASM client only (no server start)
radar-web-build:
    @echo "==> Building WASM client..."
    cd apps/radar-web/client && wasm-pack build --target web --dev
    @echo "==> Copying WASM artifacts to static..."
    cp -r apps/radar-web/client/pkg/* apps/radar-web/static/
    @echo "==> Done! Run with: cargo run -p radar-web -- --synthetic"

# Run radar-web server only (assumes WASM already built)
radar-web-serve:
    cargo run -p radar-web -- --synthetic

# Build and run TUI radar
tui-radar:
    cargo run -p tui-radar --release -- --synthetic

# Check all packages compile
check:
    cargo check --workspace

# Run tests
test:
    cargo test --workspace

# Clean build artifacts
clean:
    cargo clean
    rm -rf apps/radar-web/client/pkg
    rm -f apps/radar-web/static/radar_web_client*
    rm -f apps/radar-web/static/package.json
