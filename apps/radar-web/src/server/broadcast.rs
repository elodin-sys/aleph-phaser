//! Frame broadcast infrastructure.
//!
//! Manages frame acquisition from radar-core and distributes
//! encoded frames to all connected WebSocket clients.

use radar_core::{EncodedFrame, RadarConfig, RadarSource};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::broadcast;
use tracing::{debug, error, info, warn};

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

/// Frame acquisition loop.
///
/// Continuously captures full-resolution frames from radar-core
/// and broadcasts them to all connected clients.
pub async fn acquisition_loop(
    config: Arc<RadarConfig>,
    broadcast: FrameBroadcast,
    interval_ms: u32,
) {
    info!("Starting frame acquisition loop");

    // Create radar source
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
    let mut last_log = std::time::Instant::now();

    loop {
        // Capture full-resolution frame
        let frame = match radar.get_frame_full() {
            Ok(f) => f,
            Err(e) => {
                warn!("Frame capture error: {}", e);
                tokio::time::sleep(interval).await;
                continue;
            }
        };

        // Encode to wire format
        let encoded = EncodedFrame::from_frame(&frame);
        let bytes = Arc::new(encoded.to_bytes());

        // Broadcast to all clients (ignore if no receivers)
        let receiver_count = broadcast.receiver_count();
        if receiver_count > 0 {
            if let Err(e) = broadcast.send(bytes) {
                debug!("Broadcast send error (likely no receivers): {}", e);
            }
        }

        frame_count += 1;

        // Log stats every 5 seconds
        if last_log.elapsed() > Duration::from_secs(5) {
            let fps = frame_count as f64 / last_log.elapsed().as_secs_f64();
            info!(
                "Frame stats: {} frames, {:.1} FPS, {} clients",
                frame_count, fps, receiver_count
            );
            frame_count = 0;
            last_log = std::time::Instant::now();
        }

        tokio::time::sleep(interval).await;
    }
}
