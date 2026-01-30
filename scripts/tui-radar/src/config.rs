//! Radar configuration parameters

use serde::{Deserialize, Serialize};

/// Radar system configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RadarConfig {
    /// PlutoSDR URI
    pub sdr_uri: String,
    /// Phaser/Raspberry Pi URI
    pub phaser_uri: String,
    /// Use synthetic data instead of hardware
    pub synthetic: bool,
    /// Target frame rate (FPS)
    pub target_fps: u32,
    /// Number of range bins
    pub n_range: usize,
    /// Number of Doppler bins (chirps)
    pub n_doppler: usize,
    /// Maximum range to display (meters)
    pub max_range: f64,
    /// Chirp bandwidth (Hz)
    pub chirp_bw: f64,
    /// Ramp time (microseconds)
    pub ramp_time_us: u32,
    /// Sample rate (Hz)
    pub sample_rate: u64,
    /// Center frequency (Hz)
    pub center_freq: u64,
    /// Output frequency (Hz)
    pub output_freq: u64,
    /// Receive gain (dB)
    pub rx_gain: i32,
}

impl Default for RadarConfig {
    fn default() -> Self {
        Self {
            sdr_uri: "ip:192.168.2.1".to_string(),
            phaser_uri: "ip:192.168.4.184".to_string(),
            synthetic: true,
            target_fps: 30,
            n_range: 512,
            n_doppler: 512,
            max_range: 150.0,
            chirp_bw: 500_000_000.0,
            ramp_time_us: 500,
            sample_rate: 4_000_000,
            center_freq: 2_100_000_000,
            output_freq: 9_900_000_000,
            rx_gain: 30,
        }
    }
}

impl RadarConfig {
    /// Calculate range resolution in meters
    #[allow(dead_code)]
    pub fn range_resolution(&self) -> f64 {
        const C: f64 = 3e8; // Speed of light
        C / (2.0 * self.chirp_bw)
    }

    /// Calculate maximum unambiguous range in meters
    #[allow(dead_code)]
    pub fn max_unambiguous_range(&self) -> f64 {
        const C: f64 = 3e8;
        let ramp_time_s = self.ramp_time_us as f64 / 1e6;
        C * ramp_time_s * self.sample_rate as f64 / (2.0 * self.chirp_bw)
    }

    /// Calculate Doppler resolution in Hz
    #[allow(dead_code)]
    pub fn doppler_resolution(&self) -> f64 {
        let pri_s = self.ramp_time_us as f64 / 1e6 + 0.0002; // PRI with margin
        1.0 / (self.n_doppler as f64 * pri_s)
    }

    /// Calculate maximum Doppler frequency in Hz
    pub fn max_doppler(&self) -> f64 {
        let pri_s = self.ramp_time_us as f64 / 1e6 + 0.0002;
        let prf = 1.0 / pri_s;
        prf / 2.0
    }

    /// Calculate wavelength in meters
    #[allow(dead_code)]
    pub fn wavelength(&self) -> f64 {
        const C: f64 = 3e8;
        C / self.output_freq as f64
    }

    /// Convert Doppler frequency to velocity in m/s
    #[allow(dead_code)]
    pub fn doppler_to_velocity(&self, doppler_hz: f64) -> f64 {
        doppler_hz * self.wavelength() / 2.0
    }
}
