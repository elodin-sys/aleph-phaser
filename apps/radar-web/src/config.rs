//! Server configuration.

/// Server configuration parameters.
pub struct ServerConfig {
    /// Bind host address.
    pub host: String,
    /// Bind port.
    pub port: u16,
    /// Frame acquisition interval in milliseconds.
    pub frame_interval_ms: u32,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            port: 8080,
            frame_interval_ms: 33, // ~30 FPS
        }
    }
}
