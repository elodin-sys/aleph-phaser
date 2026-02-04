//! Radar configuration parameters
//!
//! Note: The Python backend (radar_backend.py) calculates n_range automatically
//! from ramp_time_us and sample_rate to match Jon's script exactly:
//!   n_range = int(0.9 * ramp_time_us * sample_rate / 1e6)

use serde::{Deserialize, Serialize};

/// Available test patterns for synthetic mode
pub const AVAILABLE_PATTERNS: &[&str] = &[
    "animated",
    "corner_dots",
    "gradient_h",
    "gradient_v",
    "center_target",
    "grid",
    "diagonal",
    "checkerboard",
];

/// Radar system configuration
///
/// These parameters are passed to the Python RadarBackend which handles
/// all radar processing. Parameters match Jon's Range_Doppler_Plot_Aleph.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RadarConfig {
    /// PlutoSDR URI (e.g., "ip:192.168.2.1")
    pub sdr_uri: String,
    /// Phaser/Raspberry Pi URI (e.g., "ip:192.168.4.184")
    pub phaser_uri: String,
    /// Use synthetic data instead of hardware
    pub synthetic: bool,
    /// Target frame rate (FPS) for TUI display
    pub target_fps: u32,
    /// Number of Doppler bins (num_chirps in Jon's script)
    pub n_doppler: usize,
    /// Maximum range to display (meters) - display limit only
    pub max_range: f64,
    /// Chirp bandwidth (Hz) - default 500 MHz
    pub chirp_bw: f64,
    /// Ramp time (microseconds) - default 500 us
    pub ramp_time_us: u32,
    /// Sample rate (Hz) - default 4 MHz
    pub sample_rate: u64,
    /// SDR center frequency (Hz) - default 2.1 GHz
    pub center_freq: u64,
    /// Phaser output frequency (Hz) - default 9.9 GHz
    pub output_freq: u64,
    /// Receive gain (dB) - default 30
    pub rx_gain: i32,
    /// Test pattern for synthetic mode
    pub test_pattern: String,
}

impl Default for RadarConfig {
    fn default() -> Self {
        // Default values match Jon's Range_Doppler_Plot_Aleph.py
        Self {
            sdr_uri: "ip:192.168.2.1".to_string(),
            phaser_uri: "ip:192.168.4.184".to_string(),
            synthetic: true,
            target_fps: 30,
            n_doppler: 512,  // num_chirps in Jon's script
            max_range: 10.0, // Match Jon's display default
            chirp_bw: 500_000_000.0,
            ramp_time_us: 500,
            sample_rate: 4_000_000,
            center_freq: 2_100_000_000,
            output_freq: 9_900_000_000,
            rx_gain: 30,
            test_pattern: "animated".to_string(),
        }
    }
}

impl RadarConfig {
    /// Calculate expected n_range (for informational purposes)
    /// The actual value is calculated by Python backend
    pub fn expected_n_range(&self) -> usize {
        let ramp_time_s = self.ramp_time_us as f64 / 1e6;
        let begin_offset = 0.1 * ramp_time_s;
        ((ramp_time_s - begin_offset) * self.sample_rate as f64) as usize
    }

    /// Calculate PRI (Pulse Repetition Interval) in seconds
    fn pri_s(&self) -> f64 {
        self.ramp_time_us as f64 / 1e6 + 0.0002 // Match Jon's: ramp_time/1e3 + 0.2 ms
    }

    /// Calculate maximum Doppler frequency in Hz
    pub fn max_doppler(&self) -> f64 {
        let prf = 1.0 / self.pri_s();
        prf / 2.0
    }
}
