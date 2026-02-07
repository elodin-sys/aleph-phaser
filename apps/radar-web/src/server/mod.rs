//! Server module.

mod broadcast;
mod routes;
mod websocket;

use crate::config::ServerConfig;
use axum::Router;
use radar_core::RadarConfig;
use std::net::SocketAddr;
use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use tokio::net::TcpListener;
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

    // Command channel: async handlers -> acquisition thread (sync, non-blocking try_send)
    let (command_tx, command_rx) = mpsc::sync_channel(32);
    // Frame channel: acquisition thread -> tokio (blocking recv in spawn_blocking)
    let (frame_tx, frame_rx) = mpsc::sync_channel(16);
    let frame_rx = Arc::new(Mutex::new(frame_rx));

    // Start acquisition on dedicated thread (RadarSource is !Send)
    broadcast::run_acquisition_thread(
        radar_config.clone(),
        command_rx,
        frame_tx,
        state_broadcast.clone(),
        config.frame_interval_ms,
    );

    // Task: receive frames from thread (blocking recv in spawn_blocking) and broadcast
    let frame_broadcast_for_receiver = frame_broadcast.clone();
    tokio::spawn(async move {
        loop {
            let bytes = match tokio::task::spawn_blocking({
                let frame_rx = Arc::clone(&frame_rx);
                move || frame_rx.lock().unwrap().recv()
            })
            .await
            {
                Ok(Ok(b)) => b,
                Ok(Err(_)) => break,
                Err(e) => {
                    tracing::warn!("Frame receiver task join error: {}", e);
                    break;
                }
            };
            if frame_broadcast_for_receiver.receiver_count() > 0 {
                let _ = frame_broadcast_for_receiver.send(bytes);
            }
        }
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
