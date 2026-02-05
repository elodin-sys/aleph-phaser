//! WebSocket handler for streaming radar frames.

use super::broadcast::FrameBroadcast;
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::IntoResponse,
    routing::get,
    Router,
};
use futures_util::{SinkExt, StreamExt};
use std::sync::atomic::{AtomicU64, Ordering};
use tracing::{debug, info, warn};

/// WebSocket state.
#[derive(Clone)]
pub struct WsState {
    broadcast: FrameBroadcast,
}

/// Global client counter for logging.
static CLIENT_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Build WebSocket routes.
pub fn ws_routes(broadcast: FrameBroadcast) -> Router {
    let state = WsState { broadcast };

    Router::new()
        .route("/ws/frames", get(ws_handler))
        .with_state(state)
}

/// WebSocket upgrade handler.
async fn ws_handler(ws: WebSocketUpgrade, State(state): State<WsState>) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

/// Handle a WebSocket connection.
async fn handle_socket(socket: WebSocket, state: WsState) {
    let client_id = CLIENT_COUNTER.fetch_add(1, Ordering::SeqCst);
    info!("Client {} connected", client_id);

    let (mut sender, mut receiver) = socket.split();

    // Subscribe to frame broadcast
    let mut frame_rx = state.broadcast.subscribe();

    // Task to forward frames to client
    let send_task = tokio::spawn(async move {
        while let Ok(frame_bytes) = frame_rx.recv().await {
            // Send binary frame
            if sender
                .send(Message::Binary(frame_bytes.as_ref().clone().into()))
                .await
                .is_err()
            {
                debug!("Client {} send error, disconnecting", client_id);
                break;
            }
        }
    });

    // Task to handle incoming messages (mainly for ping/pong and close)
    let recv_task = tokio::spawn(async move {
        while let Some(msg) = receiver.next().await {
            match msg {
                Ok(Message::Close(_)) => {
                    debug!("Client {} sent close frame", client_id);
                    break;
                }
                Ok(Message::Ping(data)) => {
                    debug!("Client {} ping", client_id);
                    // Pong is handled automatically by axum
                    drop(data);
                }
                Ok(_) => {
                    // Ignore other messages
                }
                Err(e) => {
                    warn!("Client {} receive error: {}", client_id, e);
                    break;
                }
            }
        }
    });

    // Wait for either task to complete
    tokio::select! {
        _ = send_task => {
            debug!("Client {} send task ended", client_id);
        }
        _ = recv_task => {
            debug!("Client {} recv task ended", client_id);
        }
    }

    info!("Client {} disconnected", client_id);
}
