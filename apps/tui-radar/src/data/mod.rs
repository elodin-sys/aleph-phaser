//! Data acquisition module
//!
//! Provides data sources for radar signal capture, including:
//! - Synthetic data generation for testing
//! - Hardware capture via PlutoSDR and Phaser

mod synthetic;
mod iio_capture;
mod phaser;

pub use synthetic::SyntheticSource;
pub use iio_capture::IioCapture;
pub use phaser::PhaserController;

use color_eyre::Result;
use ndarray::Array2;
use num_complex::Complex;

/// Captured data - either raw IQ for processing or pre-computed RD map
pub enum CapturedData {
    /// Raw IQ data that needs FFT processing
    RawIQ(Array2<Complex<f32>>),
    /// Pre-computed Range-Doppler map (dB values)
    RangeDopper(Array2<f32>),
}

/// Data source abstraction
pub enum DataSource {
    /// Synthetic data for testing
    Synthetic(SyntheticSource),
    /// Hardware capture
    Hardware {
        iio: IioCapture,
        phaser: PhaserController,
    },
}

impl DataSource {
    /// Create a synthetic data source
    pub fn new_synthetic(n_range: usize, n_doppler: usize) -> Self {
        DataSource::Synthetic(SyntheticSource::new(n_range, n_doppler))
    }

    /// Create a hardware data source
    pub fn new_hardware(sdr_uri: &str, phaser_uri: &str) -> Result<Self> {
        let iio = IioCapture::new(sdr_uri)?;
        let phaser = PhaserController::new(sdr_uri, phaser_uri)?;
        Ok(DataSource::Hardware { iio, phaser })
    }

    /// Capture data from the source
    pub fn capture(&mut self) -> Result<CapturedData> {
        match self {
            DataSource::Synthetic(src) => {
                // Synthetic mode returns pre-computed RD map directly
                // This avoids FFT artifacts in the display
                Ok(CapturedData::RangeDopper(src.generate_rd_map()))
            }
            DataSource::Hardware { iio, phaser } => {
                // Hardware mode returns raw IQ for processing
                phaser.trigger_burst()?;
                Ok(CapturedData::RawIQ(iio.capture()?))
            }
        }
    }

    /// Check if this is synthetic mode
    #[allow(dead_code)]
    pub fn is_synthetic(&self) -> bool {
        matches!(self, DataSource::Synthetic(_))
    }
}
