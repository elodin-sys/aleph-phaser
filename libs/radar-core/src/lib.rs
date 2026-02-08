//! Radar Core Library
//!
//! This library provides the shared radar backend infrastructure for both
//! the TUI application and future web application. It includes:
//!
//! - **Configuration types**: `RadarConfig`, `RadarMode`
//! - **Frame types**: `RadarFrame`, `FrameDimensions`, `FrameFormat`, `FrameData`
//! - **Test patterns**: `TestPattern` enum with all synthetic patterns
//! - **Wire protocol**: `FrameHeader`, `EncodedFrame` for streaming
//! - **Backend**: `RadarSource` wrapping the Python PyO3 bridge
//!
//! # Example
//!
//! ```no_run
//! use radar_core::{RadarConfig, RadarMode, RadarSource, TestPattern};
//!
//! let config = RadarConfig {
//!     mode: RadarMode::Synthetic,
//!     test_pattern: TestPattern::Animated,
//!     ..Default::default()
//! };
//!
//! let mut source = RadarSource::new(config).unwrap();
//! let frame = source.get_frame().unwrap();
//! println!("Frame dimensions: {:?}", frame.dimensions);
//! ```

pub mod config;
pub mod error;
pub mod frame;
pub mod patterns;
pub mod protocol;

mod backend;

// Re-export main types at crate root
pub use config::{RadarConfig, RadarMode};
pub use error::RadarError;
pub use frame::{FrameData, FrameDimensions, FrameFormat, RadarFrame};
pub use patterns::TestPattern;
pub use protocol::{EncodedFrame, FrameHeader};

use ndarray::Array2;
use std::path::PathBuf;

/// Main entry point for radar data acquisition.
///
/// `RadarSource` wraps the Python backend and provides a clean Rust API
/// for capturing radar frames in both hardware and synthetic modes.
pub struct RadarSource {
    backend: backend::PythonBackend,
    config: RadarConfig,
}

impl RadarSource {
    /// Create a new radar source with the given configuration.
    ///
    /// This initializes the Python backend and prepares for data acquisition.
    /// In hardware mode, it connects to the SDR and Phaser devices.
    /// In synthetic mode, it sets up the test pattern generator.
    pub fn new(config: RadarConfig) -> Result<Self, RadarError> {
        let backend = backend::PythonBackend::new(&config)?;
        Ok(Self { backend, config })
    }

    /// Get the current configuration.
    pub fn config(&self) -> &RadarConfig {
        &self.config
    }

    /// Get the next frame from the radar source.
    ///
    /// Returns a `RadarFrame` containing the Range-Doppler map data
    /// sliced to the configured display range.
    pub fn get_frame(&mut self) -> Result<RadarFrame, RadarError> {
        let data = self.backend.capture()?;
        let dims = self.backend.dimensions();

        Ok(RadarFrame {
            dimensions: dims,
            format: FrameFormat::Float32,
            data: FrameData::Float32(data.into_raw_vec_and_offset().0),
            scale_min: self.backend.min_scale(),
            scale_max: self.backend.max_scale(),
            range_min_m: 0.0,
            range_max_m: self.config.max_range as f32,
            doppler_min_hz: -self.config.max_doppler() as f32,
            doppler_max_hz: self.config.max_doppler() as f32,
            mti_enabled: self.backend.mti_enabled(),
        })
    }

    /// Get the raw frame data as an ndarray (for direct display).
    ///
    /// This is a convenience method for TUI applications that work
    /// directly with ndarray for rendering.
    pub fn capture_raw(&mut self) -> Result<Array2<f32>, RadarError> {
        self.backend.capture()
    }

    /// Get the next full-resolution frame from the radar source.
    ///
    /// Returns a `RadarFrame` containing the Range-Doppler map data
    /// at full resolution (typically 512x1800) without range slicing.
    /// This is useful for web visualization where client-side zoom is desired.
    pub fn get_frame_full(&mut self) -> Result<RadarFrame, RadarError> {
        let data = self.backend.capture_full()?;
        let dims = self.backend.dimensions_full();

        Ok(RadarFrame {
            dimensions: dims,
            format: FrameFormat::Float32,
            data: FrameData::Float32(data.into_raw_vec_and_offset().0),
            scale_min: self.backend.min_scale(),
            scale_max: self.backend.max_scale(),
            range_min_m: 0.0,
            range_max_m: self.config.max_unambiguous_range() as f32,
            doppler_min_hz: -self.config.max_doppler() as f32,
            doppler_max_hz: self.config.max_doppler() as f32,
            mti_enabled: self.backend.mti_enabled(),
        })
    }

    /// Get full-resolution raw frame data as an ndarray.
    ///
    /// Returns the full (n_doppler x n_range_full) frame without slicing.
    pub fn capture_raw_full(&mut self) -> Result<Array2<f32>, RadarError> {
        self.backend.capture_full()
    }

    /// Get frame dimensions (sliced to display range).
    pub fn dimensions(&self) -> FrameDimensions {
        self.backend.dimensions()
    }

    /// Get full-resolution frame dimensions.
    pub fn dimensions_full(&self) -> FrameDimensions {
        self.backend.dimensions_full()
    }

    /// Get the display value range (min, max) in log10 scale.
    pub fn scale_range(&self) -> (f32, f32) {
        (self.backend.min_scale(), self.backend.max_scale())
    }

    /// Toggle MTI (Moving Target Indicator) filter.
    pub fn set_mti_enabled(&mut self, enabled: bool) -> Result<(), RadarError> {
        self.backend.set_mti(enabled)
    }

    /// Get MTI filter state.
    pub fn mti_enabled(&self) -> bool {
        self.backend.mti_enabled()
    }

    /// Toggle DC leakage suppression. Returns new state.
    pub fn toggle_dc_suppression(&mut self) -> Result<bool, RadarError> {
        let new_state = !self.backend.dc_suppression_enabled();
        self.backend.set_dc_suppression(new_state)?;
        Ok(new_state)
    }

    /// Get DC suppression state.
    pub fn dc_suppression_enabled(&self) -> bool {
        self.backend.dc_suppression_enabled()
    }

    /// Set test pattern (synthetic mode only).
    pub fn set_test_pattern(&mut self, pattern: TestPattern) -> Result<(), RadarError> {
        self.backend.set_test_pattern(pattern.name())
    }

    /// Cycle to next test pattern (synthetic mode only).
    ///
    /// Returns the new pattern name.
    pub fn cycle_test_pattern(&mut self) -> Result<TestPattern, RadarError> {
        let name = self.backend.cycle_test_pattern()?;
        TestPattern::from_name(&name).ok_or_else(|| RadarError::InvalidPattern(name))
    }

    /// Get current test pattern.
    pub fn get_test_pattern(&self) -> Result<TestPattern, RadarError> {
        let name = self.backend.get_test_pattern()?;
        TestPattern::from_name(&name).ok_or_else(|| RadarError::InvalidPattern(name))
    }

    /// Export current frame to file.
    ///
    /// Returns the path to the exported file.
    pub fn export_frame(&self, directory: &str) -> Result<PathBuf, RadarError> {
        let path = self.backend.export_frame(directory)?;
        Ok(PathBuf::from(path))
    }

    /// Check if this is synthetic mode.
    pub fn is_synthetic(&self) -> bool {
        self.config.mode == RadarMode::Synthetic
    }

    /// Shutdown the radar source and release resources.
    pub fn shutdown(&self) {
        self.backend.shutdown();
    }
}

impl Drop for RadarSource {
    fn drop(&mut self) {
        self.shutdown();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_defaults() {
        let config = RadarConfig::default();
        assert_eq!(config.n_doppler, 512);
        assert_eq!(config.mode, RadarMode::Synthetic);
    }

    #[test]
    fn test_pattern_cycling() {
        let p1 = TestPattern::Animated;
        let p2 = p1.next();
        assert_eq!(p2, TestPattern::CornerDots);
    }

    #[test]
    fn test_frame_dimensions() {
        let dims = FrameDimensions {
            n_doppler: 512,
            n_range: 30,
        };
        assert_eq!(dims.total_samples(), 512 * 30);
    }
}
