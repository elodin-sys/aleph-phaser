//! Radar configuration types.

use serde::{Deserialize, Serialize};

use crate::patterns::TestPattern;

/// Radar operating mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RadarMode {
    /// Use real hardware (PlutoSDR + Phaser).
    Hardware,
    /// Use synthetic test data.
    Synthetic,
}

impl Default for RadarMode {
    fn default() -> Self {
        Self::Synthetic
    }
}

/// Radar system configuration.
///
/// These parameters control both the hardware operation (when in hardware mode)
/// and the signal processing parameters. Many values are passed to the Python
/// backend which handles all radar processing.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RadarConfig {
    // === Mode Selection ===
    /// Operating mode (hardware or synthetic).
    pub mode: RadarMode,

    // === Hardware Connection ===
    /// PlutoSDR URI (e.g., "ip:192.168.2.1").
    pub sdr_uri: String,
    /// Phaser/Raspberry Pi URI (e.g., "ip:192.168.4.184").
    pub phaser_uri: String,

    // === Radar Parameters ===
    /// ADC sample rate in Hz (default: 4 MHz).
    pub sample_rate: u64,
    /// Number of Doppler bins / chirps (default: 512).
    pub n_doppler: usize,
    /// Chirp ramp time in microseconds (default: 500).
    pub ramp_time_us: u32,
    /// Chirp bandwidth in Hz (default: 500 MHz).
    pub chirp_bw: f64,
    /// SDR center frequency in Hz (default: 2.1 GHz).
    pub center_freq: u64,
    /// Phaser output frequency in Hz (default: 9.9 GHz).
    pub output_freq: u64,
    /// Receive gain in dB (default: 30).
    pub rx_gain: i32,

    // === Display Parameters ===
    /// Maximum display range in meters (default: 10.0).
    pub max_range: f64,
    /// Target frame rate in FPS (default: 30).
    pub target_fps: u32,

    // === Test Pattern (synthetic mode) ===
    /// Test pattern for synthetic mode.
    #[serde(default)]
    pub test_pattern: TestPattern,
}

impl Default for RadarConfig {
    fn default() -> Self {
        Self {
            mode: RadarMode::Synthetic,
            sdr_uri: "ip:192.168.2.1".to_string(),
            phaser_uri: "ip:192.168.4.184".to_string(),
            sample_rate: 4_000_000,
            n_doppler: 512,
            ramp_time_us: 500,
            chirp_bw: 500_000_000.0,
            center_freq: 2_100_000_000,
            output_freq: 9_900_000_000,
            rx_gain: 30,
            max_range: 10.0,
            target_fps: 30,
            test_pattern: TestPattern::default(),
        }
    }
}

impl RadarConfig {
    /// Speed of light in m/s.
    const C: f64 = 3e8;

    /// Calculate range resolution in meters.
    pub fn range_resolution(&self) -> f64 {
        Self::C / (2.0 * self.chirp_bw)
    }

    /// Calculate expected number of range bins (full FFT).
    pub fn n_range_full(&self) -> usize {
        let ramp_time_s = self.ramp_time_us as f64 / 1e6;
        let begin_offset = 0.1 * ramp_time_s;
        ((ramp_time_s - begin_offset) * self.sample_rate as f64) as usize
    }

    /// Calculate PRI (Pulse Repetition Interval) in seconds.
    fn pri_s(&self) -> f64 {
        self.ramp_time_us as f64 / 1e6 + 0.0002 // Match Jon's: ramp_time/1e3 + 0.2 ms
    }

    /// Calculate maximum Doppler frequency in Hz.
    pub fn max_doppler(&self) -> f64 {
        let prf = 1.0 / self.pri_s();
        prf / 2.0
    }

    /// Calculate Doppler resolution in Hz.
    pub fn doppler_resolution(&self) -> f64 {
        1.0 / (self.n_doppler as f64 * self.ramp_time_us as f64 * 1e-6)
    }

    /// Calculate maximum unambiguous range in meters.
    pub fn max_unambiguous_range(&self) -> f64 {
        let good_ramp_samples = self.n_range_full() as f64;
        (good_ramp_samples * Self::C) / (2.0 * self.chirp_bw)
    }

    /// Create a configuration for synthetic mode with given pattern.
    pub fn synthetic(pattern: TestPattern) -> Self {
        Self {
            mode: RadarMode::Synthetic,
            test_pattern: pattern,
            ..Default::default()
        }
    }

    /// Create a configuration for hardware mode.
    pub fn hardware(sdr_uri: &str, phaser_uri: &str) -> Self {
        Self {
            mode: RadarMode::Hardware,
            sdr_uri: sdr_uri.to_string(),
            phaser_uri: phaser_uri.to_string(),
            ..Default::default()
        }
    }
}

// Implement custom serialization for TestPattern
impl Serialize for TestPattern {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(self.name())
    }
}

impl<'de> Deserialize<'de> for TestPattern {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        TestPattern::from_name(&s)
            .ok_or_else(|| serde::de::Error::custom(format!("unknown test pattern: {}", s)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = RadarConfig::default();
        assert_eq!(config.n_doppler, 512);
        assert_eq!(config.mode, RadarMode::Synthetic);
        assert_eq!(config.sample_rate, 4_000_000);
    }

    #[test]
    fn test_range_resolution() {
        let config = RadarConfig::default();
        // With 500 MHz bandwidth: c / (2 * 500e6) = 0.3m
        let res = config.range_resolution();
        assert!((res - 0.3).abs() < 0.01);
    }

    #[test]
    fn test_n_range_full() {
        let config = RadarConfig::default();
        // 0.9 * 500us * 4MHz = 1800 samples
        assert_eq!(config.n_range_full(), 1800);
    }

    #[test]
    fn test_config_serialization() {
        let config = RadarConfig::default();
        let json = serde_json::to_string(&config).unwrap();
        assert!(json.contains("\"mode\":\"synthetic\""));
        assert!(json.contains("\"test_pattern\":\"animated\""));
    }
}
