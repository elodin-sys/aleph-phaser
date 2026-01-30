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

    /// Capture raw IQ data
    pub fn capture(&mut self) -> Result<Array2<Complex<f32>>> {
        match self {
            DataSource::Synthetic(src) => Ok(src.generate()),
            DataSource::Hardware { iio, phaser } => {
                // Trigger burst and capture
                phaser.trigger_burst()?;
                iio.capture()
            }
        }
    }
}
