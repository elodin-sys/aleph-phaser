//! Radar Web Server
//!
//! High-performance WebGPU radar visualization server that streams
//! full-resolution frames to browser clients via WebSocket.

mod config;
mod server;

use clap::Parser;
use config::ServerConfig;
use radar_core::{RadarConfig, TestPattern};
use std::sync::Arc;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

#[derive(Parser, Debug)]
#[command(name = "radar-web")]
#[command(about = "WebGPU radar visualization web server")]
struct Args {
    /// Run in synthetic data mode (no hardware required)
    #[arg(long)]
    synthetic: bool,

    /// PlutoSDR URI (e.g., ip:192.168.2.1)
    #[arg(long)]
    sdr_uri: Option<String>,

    /// Phaser board URI (e.g., ip:192.168.2.1)
    #[arg(long)]
    phaser_uri: Option<String>,

    /// Server bind address
    #[arg(long, default_value = "0.0.0.0")]
    host: String,

    /// Server port
    #[arg(long, default_value = "8080")]
    port: u16,

    /// Target frame rate in FPS
    #[arg(long, default_value = "30")]
    fps: u32,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    let args = Args::parse();

    // Build radar config
    let radar_config = if args.synthetic {
        info!("Starting in synthetic data mode");
        RadarConfig::synthetic(TestPattern::Animated)
    } else {
        let sdr_uri = args.sdr_uri.expect("--sdr-uri required for hardware mode");
        let phaser_uri = args
            .phaser_uri
            .expect("--phaser-uri required for hardware mode");
        info!("Connecting to hardware: SDR={}, Phaser={}", sdr_uri, phaser_uri);
        RadarConfig::hardware(&sdr_uri, &phaser_uri)
    };

    let server_config = ServerConfig {
        host: args.host,
        port: args.port,
        frame_interval_ms: 1000 / args.fps,
    };

    info!(
        "Starting radar-web server on {}:{}",
        server_config.host, server_config.port
    );
    info!("Frame rate: {} FPS ({} ms interval)", args.fps, server_config.frame_interval_ms);

    // Start the server
    server::run(Arc::new(radar_config), server_config).await
}
