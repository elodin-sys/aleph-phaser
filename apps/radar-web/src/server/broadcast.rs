//! Frame broadcast infrastructure.
//!
//! Manages frame acquisition from radar-core and distributes
//! encoded frames to all connected WebSocket clients.
//! Also handles bidirectional command/response protocol.
//!
//! Frame acquisition runs on a dedicated std::thread (RadarSource is !Send
//! due to PyO3) and sends frames over a channel; a tokio task receives and
//! broadcasts so the async runtime is not blocked by Python/GIL.

use radar_core::{RadarConfig, RadarSource, RadarFrame, TestPattern};
use serde::{Deserialize, Serialize};
use std::sync::mpsc::{self, RecvTimeoutError};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};
use tokio::sync::broadcast;
use tracing::{error, info, warn};

/// Commands that can be sent from clients to the radar acquisition loop.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "cmd", rename_all = "snake_case")]
pub enum RadarCommand {
    /// Cycle to the next test pattern (synthetic mode only).
    CyclePattern,
    /// Set a specific test pattern by name.
    SetPattern { pattern: String },
    /// Toggle MTI filter on/off.
    ToggleMti,
    /// Set MTI filter to a specific state.
    SetMti { enabled: bool },
    /// Toggle DC leakage suppression on/off.
    ToggleDc,
    /// Export current frame to disk.
    Export,
    /// Request current state.
    GetState,
    /// Pause frame acquisition.
    Pause,
    /// Resume frame acquisition.
    Resume,
    /// Reset to defaults.
    Reset,
}

/// Current radar state, broadcast to all connected clients.
#[derive(Debug, Clone, Serialize)]
pub struct RadarState {
    /// Event type for client to distinguish message types.
    pub event: String,
    /// Operating mode ("synthetic" or "hardware").
    pub mode: String,
    /// Current test pattern name (synthetic mode only).
    pub pattern: String,
    /// Whether MTI filter is enabled.
    pub mti_enabled: bool,
    /// Whether acquisition is paused.
    pub paused: bool,
    /// Current scale minimum (dB).
    pub scale_min: f32,
    /// Current scale maximum (dB).
    pub scale_max: f32,
    /// Frame dimensions.
    pub n_doppler: u32,
    pub n_range: u32,
}

impl RadarState {
    /// Create a state update message.
    pub fn state_update(
        mode: &str,
        pattern: &str,
        mti_enabled: bool,
        paused: bool,
        scale_min: f32,
        scale_max: f32,
        n_doppler: u32,
        n_range: u32,
    ) -> Self {
        Self {
            event: "state_update".to_string(),
            mode: mode.to_string(),
            pattern: pattern.to_string(),
            mti_enabled,
            paused,
            scale_min,
            scale_max,
            n_doppler,
            n_range,
        }
    }
}

/// Response to specific commands (e.g., export result).
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "event", rename_all = "snake_case")]
pub enum CommandResponse {
    /// Export completed successfully.
    ExportResult { success: bool, path: Option<String>, error: Option<String> },
    /// Error response.
    Error { message: String },
    /// Toast message for client to display.
    Toast { message: String, level: String },
}

/// Broadcast channel for distributing encoded frames.
#[derive(Clone)]
pub struct FrameBroadcast {
    sender: broadcast::Sender<Arc<Vec<u8>>>,
}

impl FrameBroadcast {
    /// Create a new broadcast channel with the given capacity.
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self { sender }
    }

    /// Subscribe to receive frames.
    pub fn subscribe(&self) -> broadcast::Receiver<Arc<Vec<u8>>> {
        self.sender.subscribe()
    }

    /// Send a frame to all subscribers.
    pub fn send(&self, frame: Arc<Vec<u8>>) -> Result<usize, broadcast::error::SendError<Arc<Vec<u8>>>> {
        self.sender.send(frame)
    }

    /// Get the number of active receivers.
    pub fn receiver_count(&self) -> usize {
        self.sender.receiver_count()
    }
}

/// Broadcast channel for state updates (JSON text messages).
#[derive(Clone)]
pub struct StateBroadcast {
    sender: broadcast::Sender<String>,
}

impl StateBroadcast {
    /// Create a new state broadcast channel.
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self { sender }
    }

    /// Subscribe to receive state updates.
    pub fn subscribe(&self) -> broadcast::Receiver<String> {
        self.sender.subscribe()
    }

    /// Broadcast a state update to all clients.
    pub fn send_state(&self, state: &RadarState) {
        if let Ok(json) = serde_json::to_string(state) {
            let _ = self.sender.send(json);
        }
    }

    /// Broadcast a command response to all clients.
    pub fn send_response(&self, response: &CommandResponse) {
        if let Ok(json) = serde_json::to_string(response) {
            let _ = self.sender.send(json);
        }
    }
}

/// Command sender for WebSocket handlers (used from async; try_send is non-blocking).
pub type CommandSender = mpsc::SyncSender<RadarCommand>;

/// Runs the frame acquisition loop on a dedicated std::thread.
/// RadarSource is !Send (PyO3), so it cannot be moved into spawn_blocking.
/// This thread owns the radar and sends raw frames via frame_tx; encoding runs on the receiver
/// so capture N+1 can overlap with encode/send of frame N (pipelining).
pub fn run_acquisition_thread(
    config: Arc<RadarConfig>,
    command_rx: mpsc::Receiver<RadarCommand>,
    frame_tx: mpsc::SyncSender<RadarFrame>,
    state_broadcast: StateBroadcast,
    interval_ms: u32,
) {
    thread::spawn(move || {
        acquisition_loop_sync(config, command_rx, frame_tx, state_broadcast, interval_ms);
    });
}

/// Synchronous acquisition loop (runs on dedicated thread).
fn acquisition_loop_sync(
    config: Arc<RadarConfig>,
    command_rx: mpsc::Receiver<RadarCommand>,
    frame_tx: mpsc::SyncSender<RadarFrame>,
    state_broadcast: StateBroadcast,
    interval_ms: u32,
) {
    info!("Starting frame acquisition loop (dedicated thread)");

    let mut radar = match RadarSource::new((*config).clone()) {
        Ok(r) => r,
        Err(e) => {
            error!("Failed to create RadarSource: {}", e);
            return;
        }
    };

    let dims = radar.dimensions_full();
    info!(
        "Radar initialized: {}x{} full-resolution frames",
        dims.n_doppler, dims.n_range
    );

    let interval = Duration::from_millis(interval_ms as u64);
    let mut frame_count: u64 = 0;
    let mut last_log = Instant::now();
    #[allow(unused_assignments)]
    let mut last_capture_ms: Option<f64> = None;
    #[allow(unused_assignments)]
    let mut last_total_ms: Option<f64> = None;
    #[allow(unused_assignments)]
    let mut last_frame_data_len: Option<usize> = None;
    let mut paused = false;

    let is_synthetic = radar.is_synthetic();
    let initial_pattern = if is_synthetic {
        radar.get_test_pattern().map(|p| p.name().to_string()).unwrap_or_default()
    } else {
        String::new()
    };

    let (scale_min, scale_max) = radar.scale_range();
    let initial_state = RadarState::state_update(
        if is_synthetic { "synthetic" } else { "hardware" },
        &initial_pattern,
        radar.mti_enabled(),
        paused,
        scale_min,
        scale_max,
        dims.n_doppler,
        dims.n_range,
    );
    state_broadcast.send_state(&initial_state);

    loop {
        match command_rx.recv_timeout(interval) {
            Ok(cmd) => {
                handle_command_sync(&mut radar, &state_broadcast, cmd, &mut paused);
            }
            Err(RecvTimeoutError::Timeout) => {
                if paused {
                    continue;
                }
                let t0 = Instant::now();
                let frame = match radar.get_frame_full() {
                    Ok(f) => f,
                    Err(e) => {
                        warn!("Frame capture error: {}", e);
                        continue;
                    }
                };
                let t1 = Instant::now();
                last_capture_ms = Some(t1.duration_since(t0).as_secs_f64() * 1000.0);
                last_frame_data_len = Some(frame.dimensions.total_samples() * 4);
                // Send raw frame so receiver can encode while we start next capture (pipelining)
                if frame_tx.send(frame).is_err() {
                    break;
                }
                frame_count += 1;
                last_total_ms = Some(t1.duration_since(t0).as_secs_f64() * 1000.0);
                if last_log.elapsed() > Duration::from_secs(5) {
                    let fps = frame_count as f64 / last_log.elapsed().as_secs_f64();
                    info!(
                        capture_ms = last_capture_ms.unwrap_or(0.0),
                        total_ms = last_total_ms.unwrap_or(0.0),
                        frame_data_bytes = last_frame_data_len.unwrap_or(0),
                        "Frame stats: {} frames, {:.1} FPS (encode on receiver)",
                        frame_count, fps
                    );
                    frame_count = 0;
                    last_log = Instant::now();
                }
            }
            Err(RecvTimeoutError::Disconnected) => break,
        }
    }
}

/// Handle a command from a client (sync; called from acquisition thread).
fn handle_command_sync(
    radar: &mut RadarSource,
    state_broadcast: &StateBroadcast,
    cmd: RadarCommand,
    paused: &mut bool,
) {
    let is_synthetic = radar.is_synthetic();

    match cmd {
        RadarCommand::CyclePattern => {
            if is_synthetic {
                match radar.cycle_test_pattern() {
                    Ok(pattern) => {
                        info!("Cycled to pattern: {}", pattern.name());
                        broadcast_state(radar, state_broadcast, *paused);
                        state_broadcast.send_response(&CommandResponse::Toast {
                            message: format!("Pattern: {}", pattern.name()),
                            level: "info".to_string(),
                        });
                    }
                    Err(e) => {
                        warn!("Failed to cycle pattern: {}", e);
                        state_broadcast.send_response(&CommandResponse::Error {
                            message: format!("Failed to cycle pattern: {}", e),
                        });
                    }
                }
            } else {
                state_broadcast.send_response(&CommandResponse::Toast {
                    message: "Test patterns only available in synthetic mode".to_string(),
                    level: "warn".to_string(),
                });
            }
        }

        RadarCommand::SetPattern { pattern } => {
            if is_synthetic {
                if let Some(p) = TestPattern::from_name(&pattern) {
                    match radar.set_test_pattern(p) {
                        Ok(()) => {
                            info!("Set pattern to: {}", pattern);
                            broadcast_state(radar, state_broadcast, *paused);
                        }
                        Err(e) => {
                            warn!("Failed to set pattern: {}", e);
                            state_broadcast.send_response(&CommandResponse::Error {
                                message: format!("Failed to set pattern: {}", e),
                            });
                        }
                    }
                } else {
                    state_broadcast.send_response(&CommandResponse::Error {
                        message: format!("Unknown pattern: {}", pattern),
                    });
                }
            }
        }

        RadarCommand::ToggleMti => {
            let new_state = !radar.mti_enabled();
            match radar.set_mti_enabled(new_state) {
                Ok(()) => {
                    info!("MTI toggled to: {}", new_state);
                    broadcast_state(radar, state_broadcast, *paused);
                    state_broadcast.send_response(&CommandResponse::Toast {
                        message: format!("MTI: {}", if new_state { "ON" } else { "OFF" }),
                        level: "info".to_string(),
                    });
                }
                Err(e) => {
                    warn!("Failed to toggle MTI: {}", e);
                    state_broadcast.send_response(&CommandResponse::Error {
                        message: format!("Failed to toggle MTI: {}", e),
                    });
                }
            }
        }

        RadarCommand::SetMti { enabled } => {
            match radar.set_mti_enabled(enabled) {
                Ok(()) => {
                    info!("MTI set to: {}", enabled);
                    broadcast_state(radar, state_broadcast, *paused);
                }
                Err(e) => {
                    warn!("Failed to set MTI: {}", e);
                }
            }
        }

        RadarCommand::ToggleDc => {
            match radar.toggle_dc_suppression() {
                Ok(new_state) => {
                    info!("DC suppression toggled to: {}", new_state);
                    broadcast_state(radar, state_broadcast, *paused);
                    state_broadcast.send_response(&CommandResponse::Toast {
                        message: format!("DC Suppression: {}", if new_state { "ON" } else { "OFF" }),
                        level: "info".to_string(),
                    });
                }
                Err(e) => {
                    warn!("Failed to toggle DC suppression: {}", e);
                    state_broadcast.send_response(&CommandResponse::Toast {
                        message: format!("DC toggle failed: {}", e),
                        level: "error".to_string(),
                    });
                }
            }
        }

        RadarCommand::Export => {
            info!("Exporting frame...");
            match radar.export_frame("./exports") {
                Ok(path) => {
                    let path_str = path.to_string_lossy().to_string();
                    info!("Frame exported to: {}", path_str);
                    state_broadcast.send_response(&CommandResponse::ExportResult {
                        success: true,
                        path: Some(path_str.clone()),
                        error: None,
                    });
                    state_broadcast.send_response(&CommandResponse::Toast {
                        message: format!("Exported: {}", path_str),
                        level: "success".to_string(),
                    });
                }
                Err(e) => {
                    warn!("Export failed: {}", e);
                    state_broadcast.send_response(&CommandResponse::ExportResult {
                        success: false,
                        path: None,
                        error: Some(e.to_string()),
                    });
                    state_broadcast.send_response(&CommandResponse::Toast {
                        message: format!("Export failed: {}", e),
                        level: "error".to_string(),
                    });
                }
            }
        }

        RadarCommand::GetState => {
            broadcast_state(radar, state_broadcast, *paused);
        }

        RadarCommand::Pause => {
            *paused = true;
            info!("Acquisition paused");
            broadcast_state(radar, state_broadcast, *paused);
            state_broadcast.send_response(&CommandResponse::Toast {
                message: "Paused".to_string(),
                level: "info".to_string(),
            });
        }

        RadarCommand::Resume => {
            *paused = false;
            info!("Acquisition resumed");
            broadcast_state(radar, state_broadcast, *paused);
            state_broadcast.send_response(&CommandResponse::Toast {
                message: "Resumed".to_string(),
                level: "info".to_string(),
            });
        }

        RadarCommand::Reset => {
            // Reset MTI
            let _ = radar.set_mti_enabled(false);
            // Reset to default pattern if synthetic
            if is_synthetic {
                let _ = radar.set_test_pattern(TestPattern::Animated);
            }
            *paused = false;
            info!("Reset to defaults");
            broadcast_state(radar, state_broadcast, *paused);
            state_broadcast.send_response(&CommandResponse::Toast {
                message: "Reset to defaults".to_string(),
                level: "info".to_string(),
            });
        }
    }
}

/// Broadcast current state to all clients.
fn broadcast_state(radar: &RadarSource, state_broadcast: &StateBroadcast, paused: bool) {
    let is_synthetic = radar.is_synthetic();
    let pattern = if is_synthetic {
        radar.get_test_pattern().map(|p| p.name().to_string()).unwrap_or_default()
    } else {
        String::new()
    };
    let (scale_min, scale_max) = radar.scale_range();
    let dims = radar.dimensions_full();

    let state = RadarState::state_update(
        if is_synthetic { "synthetic" } else { "hardware" },
        &pattern,
        radar.mti_enabled(),
        paused,
        scale_min,
        scale_max,
        dims.n_doppler,
        dims.n_range,
    );
    state_broadcast.send_state(&state);
}
