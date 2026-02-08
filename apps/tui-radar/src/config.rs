//! Radar configuration parameters
//!
//! This module provides the TUI-specific configuration that wraps
//! radar_core::RadarConfig with additional display parameters.

use serde::{Deserialize, Serialize};

/// Radar system configuration
///
/// This configuration extends radar_core::RadarConfig with TUI-specific
/// parameters like target_fps and synthetic flag (for CLI compatibility).
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
    /// DC leakage suppression
    pub dc_suppression: bool,
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
            dc_suppression: false,
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

    /// Convert to radar_core::RadarConfig
    pub fn to_core_config(&self) -> radar_core::RadarConfig {
        let mode = if self.synthetic {
            radar_core::RadarMode::Synthetic
        } else {
            radar_core::RadarMode::Hardware
        };

        let test_pattern = radar_core::TestPattern::from_name(&self.test_pattern)
            .unwrap_or_default();

        radar_core::RadarConfig {
            mode,
            sdr_uri: self.sdr_uri.clone(),
            phaser_uri: self.phaser_uri.clone(),
            sample_rate: self.sample_rate,
            n_doppler: self.n_doppler,
            ramp_time_us: self.ramp_time_us,
            chirp_bw: self.chirp_bw,
            center_freq: self.center_freq,
            output_freq: self.output_freq,
            rx_gain: self.rx_gain,
            max_range: self.max_range,
            target_fps: self.target_fps,
            dc_suppression: self.dc_suppression,
            test_pattern,
        }
    }

    /// Create from radar_core::RadarConfig with TUI defaults
    #[allow(dead_code)]
    pub fn from_core_config(core: &radar_core::RadarConfig) -> Self {
        Self {
            sdr_uri: core.sdr_uri.clone(),
            phaser_uri: core.phaser_uri.clone(),
            synthetic: core.mode == radar_core::RadarMode::Synthetic,
            target_fps: core.target_fps,
            n_doppler: core.n_doppler,
            max_range: core.max_range,
            chirp_bw: core.chirp_bw,
            ramp_time_us: core.ramp_time_us,
            sample_rate: core.sample_rate,
            center_freq: core.center_freq,
            output_freq: core.output_freq,
            rx_gain: core.rx_gain,
            dc_suppression: core.dc_suppression,
            test_pattern: core.test_pattern.name().to_string(),
        }
    }
}
