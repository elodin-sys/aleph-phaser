//! Server module.

mod broadcast;
mod routes;
mod websocket;

use crate::config::ServerConfig;
use axum::Router;
use radar_core::RadarConfig;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::net::TcpListener;
use tokio::sync::mpsc;
use tower_http::cors::{Any, CorsLayer};
use tower_http::services::ServeDir;
use tracing::info;

pub use broadcast::{FrameBroadcast, StateBroadcast};

/// Run the radar web server.
pub async fn run(radar_config: Arc<RadarConfig>, config: ServerConfig) -> anyhow::Result<()> {
    // Create broadcast channel for frame distribution (binary)
    let frame_broadcast = FrameBroadcast::new(16);

    // Create broadcast channel for state updates (JSON)
    let state_broadcast = StateBroadcast::new(16);

    // Create command channel for client commands to acquisition loop
    let (command_tx, command_rx) = mpsc::channel(32);

    // Start frame acquisition task
    let acq_frame_broadcast = frame_broadcast.clone();
    let acq_state_broadcast = state_broadcast.clone();
    let acq_config = radar_config.clone();
    let interval_ms = config.frame_interval_ms;
    tokio::spawn(async move {
        broadcast::acquisition_loop(
            acq_config,
            acq_frame_broadcast,
            acq_state_broadcast,
            command_rx,
            interval_ms,
        )
        .await;
    });

    // Determine static files directory
    // Check for RADAR_WEB_STATIC_DIR env var (set by Nix), fallback to dev path
    let static_dir = std::env::var("RADAR_WEB_STATIC_DIR")
        .unwrap_or_else(|_| "apps/radar-web/static".to_string());
    info!("Serving static files from: {}", static_dir);

    // Build router
    let app = Router::new()
        .merge(routes::api_routes(radar_config.clone()))
        .merge(websocket::ws_routes(
            frame_broadcast,
            state_broadcast,
            command_tx,
        ))
        .fallback_service(ServeDir::new(&static_dir))
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        );

    // Bind and serve
    let addr: SocketAddr = format!("{}:{}", config.host, config.port).parse()?;
    let listener = TcpListener::bind(addr).await?;
    info!("Server listening on http://{}", addr);

    axum::serve(listener, app).await?;

    Ok(())
}
