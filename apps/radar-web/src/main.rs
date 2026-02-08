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

    /// Number of chirps per frame (Doppler bins). More = finer velocity resolution but slower capture.
    #[arg(long, default_value = "256")]
    num_chirps: usize,

    /// Chirp ramp time in microseconds. Shorter = fewer range bins but faster SDR capture.
    #[arg(long, default_value = "500")]
    ramp_time_us: u32,

    /// Maximum display range in meters.
    #[arg(long, default_value = "10.0")]
    max_range: f64,

    /// Receive gain in dB (AD9361). Must be between -3 and 70.
    #[arg(long, default_value = "30")]
    rx_gain: i32,

    /// Enable DC leakage suppression (per-chirp mean subtraction).
    #[arg(long, default_value = "false")]
    dc_suppression: bool,
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
    let mut radar_config = if args.synthetic {
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
    radar_config.n_doppler = args.num_chirps;
    radar_config.ramp_time_us = args.ramp_time_us;
    radar_config.max_range = args.max_range;
    radar_config.rx_gain = args.rx_gain;
    radar_config.dc_suppression = args.dc_suppression;

    info!("Chirps per frame (Doppler bins): {}", radar_config.n_doppler);
    info!(
        "Range config: ramp={}us, bins={}, max={:.1}m, resolution={:.2}m",
        radar_config.ramp_time_us,
        radar_config.n_range_full(),
        radar_config.max_range,
        radar_config.range_resolution()
    );

    // Log estimated data volume for operator visibility
    let pri_ms = radar_config.ramp_time_us as f64 / 1000.0 + 0.2;
    let n_frame = (pri_ms / 1000.0 * radar_config.sample_rate as f64) as u64;
    let buffer_size = (radar_config.n_doppler as u64 * n_frame).next_power_of_two();
    let raw_kb = 2 * buffer_size * 4 / 1024;
    info!(
        "SDR transfer estimate: buffer={}K samples, raw={}KB",
        buffer_size / 1024,
        raw_kb
    );

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
