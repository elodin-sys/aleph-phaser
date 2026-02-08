//! Data acquisition module
//!
//! This module provides a thin wrapper around radar_core::RadarSource,
//! maintaining API compatibility with the existing TUI application while
//! delegating all radar processing to the shared library.

use color_eyre::{eyre::eyre, Result};
use ndarray::Array2;

use crate::config::RadarConfig;

// Re-export useful types from radar-core
pub use radar_core::TestPattern;

/// Data source that wraps radar_core::RadarSource
///
/// This struct provides backward compatibility with the existing TUI code
/// while using the shared radar-core library for all operations.
pub struct DataSource {
    source: radar_core::RadarSource,
}

impl DataSource {
    /// Create a new data source
    pub fn new(config: &RadarConfig) -> Result<Self> {
        // Convert TUI config to radar-core config
        let core_config = config.to_core_config();
        
        let source = radar_core::RadarSource::new(core_config)
            .map_err(|e| eyre!("Failed to initialize radar source: {}", e))?;

        Ok(Self { source })
    }

    /// Get number of Doppler bins
    pub fn n_doppler(&self) -> usize {
        self.source.dimensions().n_doppler as usize
    }

    /// Get number of range bins
    pub fn n_range(&self) -> usize {
        self.source.dimensions().n_range as usize
    }

    /// Get minimum display scale
    pub fn min_scale(&self) -> f32 {
        self.source.scale_range().0
    }

    /// Get maximum display scale
    pub fn max_scale(&self) -> f32 {
        self.source.scale_range().1
    }

    /// Capture a frame from the data source
    /// Returns a 2D array of dB values, shape (n_doppler, n_range)
    pub fn capture(&mut self) -> Result<Array2<f32>> {
        self.source
            .capture_raw()
            .map_err(|e| eyre!("Failed to capture frame: {}", e))
    }

    /// Set MTI filter state
    pub fn set_mti(&mut self, enabled: bool) -> Result<()> {
        self.source
            .set_mti_enabled(enabled)
            .map_err(|e| eyre!("Failed to set MTI: {}", e))
    }

    /// Set test pattern (synthetic mode only)
    pub fn set_test_pattern(&mut self, pattern: &str) -> Result<()> {
        let p = TestPattern::from_name(pattern)
            .ok_or_else(|| eyre!("Unknown pattern: {}", pattern))?;
        self.source
            .set_test_pattern(p)
            .map_err(|e| eyre!("Failed to set pattern: {}", e))
    }

    /// Cycle to next test pattern (synthetic mode only)
    pub fn cycle_test_pattern(&mut self) -> Result<String> {
        let pattern = self.source
            .cycle_test_pattern()
            .map_err(|e| eyre!("Failed to cycle pattern: {}", e))?;
        Ok(pattern.name().to_string())
    }

    /// Get current test pattern name (synthetic mode only)
    #[allow(dead_code)]
    pub fn get_test_pattern(&self) -> Result<String> {
        let pattern = self.source
            .get_test_pattern()
            .map_err(|e| eyre!("Failed to get pattern: {}", e))?;
        Ok(pattern.name().to_string())
    }

    /// Export current frame to a file
    pub fn export_frame(&self, directory: &str) -> Result<String> {
        let path = self.source
            .export_frame(directory)
            .map_err(|e| eyre!("Failed to export frame: {}", e))?;
        Ok(path.to_string_lossy().to_string())
    }

    /// Shutdown the data source
    pub fn shutdown(&self) {
        self.source.shutdown();
    }

    /// Check if this is synthetic mode
    #[allow(dead_code)]
    pub fn is_synthetic(&self) -> bool {
        self.source.is_synthetic()
    }
}

impl Drop for DataSource {
    fn drop(&mut self) {
        self.shutdown();
    }
}
