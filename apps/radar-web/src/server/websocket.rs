//! WebSocket handler for streaming radar frames and bidirectional commands.

use super::broadcast::{CommandSender, FrameBroadcast, RadarCommand, StateBroadcast};
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
use tokio::sync::mpsc;
use tracing::{debug, info, warn};

/// WebSocket state shared across handlers.
#[derive(Clone)]
pub struct WsState {
    /// Broadcast channel for binary frame data.
    pub frame_broadcast: FrameBroadcast,
    /// Broadcast channel for JSON state updates.
    pub state_broadcast: StateBroadcast,
    /// Sender for commands to the acquisition loop.
    pub command_tx: CommandSender,
}

/// Global client counter for logging.
static CLIENT_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Build WebSocket routes.
pub fn ws_routes(
    frame_broadcast: FrameBroadcast,
    state_broadcast: StateBroadcast,
    command_tx: CommandSender,
) -> Router {
    let state = WsState {
        frame_broadcast,
        state_broadcast,
        command_tx,
    };

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

    let (mut ws_sender, mut ws_receiver) = socket.split();

    // Subscribe to frame broadcast (binary messages)
    let mut frame_rx = state.frame_broadcast.subscribe();
    // Subscribe to state broadcast (JSON text messages)
    let mut state_rx = state.state_broadcast.subscribe();
    // Command sender for this client
    let command_tx = state.command_tx.clone();

    // Request initial state when client connects (try_send is non-blocking)
    let _ = command_tx.try_send(RadarCommand::GetState);

    // Create a channel to merge outgoing messages
    let (outgoing_tx, mut outgoing_rx) = mpsc::channel::<Message>(64);

    // Task to forward frames (binary) and state updates (text) to outgoing channel
    let frame_tx = outgoing_tx.clone();
    let frame_task = tokio::spawn(async move {
        loop {
            tokio::select! {
                // Binary frame data
                Ok(frame_bytes) = frame_rx.recv() => {
                    let msg = Message::Binary(frame_bytes.as_ref().clone().into());
                    if frame_tx.send(msg).await.is_err() {
                        break;
                    }
                }
                // JSON state updates
                Ok(json) = state_rx.recv() => {
                    let msg = Message::Text(json.into());
                    if frame_tx.send(msg).await.is_err() {
                        break;
                    }
                }
            }
        }
    });

    // Task to send outgoing messages to WebSocket
    let send_task = tokio::spawn(async move {
        while let Some(msg) = outgoing_rx.recv().await {
            if ws_sender.send(msg).await.is_err() {
                debug!("Client {} send error, disconnecting", client_id);
                break;
            }
        }
    });

    // Task to handle incoming messages (commands and ping/pong)
    let recv_task = tokio::spawn(async move {
        while let Some(msg) = ws_receiver.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    // Parse JSON command
                    debug!("Client {} sent command: {}", client_id, text);
                    match serde_json::from_str::<RadarCommand>(&text) {
                        Ok(cmd) => {
                            if command_tx.try_send(cmd).is_err() {
                                warn!("Client {} command channel full or closed", client_id);
                            }
                        }
                        Err(e) => {
                            warn!("Client {} invalid command '{}': {}", client_id, text, e);
                        }
                    }
                }
                Ok(Message::Close(_)) => {
                    debug!("Client {} sent close frame", client_id);
                    break;
                }
                Ok(Message::Ping(_)) => {
                    debug!("Client {} ping", client_id);
                    // Pong is handled automatically by axum
                }
                Ok(Message::Pong(_)) => {
                    // Ignore pong
                }
                Ok(Message::Binary(_)) => {
                    // Clients shouldn't send binary, ignore
                    debug!("Client {} sent unexpected binary message", client_id);
                }
                Err(e) => {
                    warn!("Client {} receive error: {}", client_id, e);
                    break;
                }
            }
        }
    });

    // Wait for any task to complete (client disconnect or error)
    tokio::select! {
        _ = frame_task => {
            debug!("Client {} frame task ended", client_id);
        }
        _ = send_task => {
            debug!("Client {} send task ended", client_id);
        }
        _ = recv_task => {
            debug!("Client {} recv task ended", client_id);
        }
    }

    info!("Client {} disconnected", client_id);
}
