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
use tower_http::cors::{Any, CorsLayer};
use tower_http::services::ServeDir;
use tracing::info;

pub use broadcast::FrameBroadcast;

/// Run the radar web server.
pub async fn run(radar_config: Arc<RadarConfig>, config: ServerConfig) -> anyhow::Result<()> {
    // Create broadcast channel for frame distribution
    let broadcast = FrameBroadcast::new(16);

    // Start frame acquisition task
    let acq_broadcast = broadcast.clone();
    let acq_config = radar_config.clone();
    let interval_ms = config.frame_interval_ms;
    tokio::spawn(async move {
        broadcast::acquisition_loop(acq_config, acq_broadcast, interval_ms).await;
    });

    // Determine static files directory
    // Check for RADAR_WEB_STATIC_DIR env var (set by Nix), fallback to dev path
    let static_dir = std::env::var("RADAR_WEB_STATIC_DIR")
        .unwrap_or_else(|_| "apps/radar-web/static".to_string());
    info!("Serving static files from: {}", static_dir);

    // Build router
    let app = Router::new()
        .merge(routes::api_routes(radar_config.clone()))
        .merge(websocket::ws_routes(broadcast))
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
