//! Phaser control via PyO3/pyadi-iio

use color_eyre::Result;

#[cfg(feature = "python")]
use color_eyre::eyre::eyre;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyDict;

/// Phaser controller using PyO3 to call pyadi-iio
pub struct PhaserController {
    #[allow(dead_code)]
    sdr_uri: String,
    #[allow(dead_code)]
    phaser_uri: String,
    #[cfg(feature = "python")]
    py_phaser: Option<Py<PyAny>>,
    #[cfg(feature = "python")]
    #[allow(dead_code)]
    py_sdr: Option<Py<PyAny>>,
    initialized: bool,
}

impl PhaserController {
    /// Create a new Phaser controller
    pub fn new(sdr_uri: &str, phaser_uri: &str) -> Result<Self> {
        #[allow(unused_mut)]
        let mut controller = Self {
            sdr_uri: sdr_uri.to_string(),
            phaser_uri: phaser_uri.to_string(),
            #[cfg(feature = "python")]
            py_phaser: None,
            #[cfg(feature = "python")]
            py_sdr: None,
            initialized: false,
        };

        // Try to initialize Python/pyadi-iio
        #[cfg(feature = "python")]
        if let Err(e) = controller.initialize() {
            eprintln!("Warning: Could not initialize Phaser controller: {}", e);
            eprintln!("Running in degraded mode (synthetic data only)");
        }

        #[cfg(not(feature = "python"))]
        eprintln!("Note: Python support disabled. Running in synthetic mode only.");

        Ok(controller)
    }

    /// Initialize Python environment and pyadi-iio
    #[cfg(feature = "python")]
    fn initialize(&mut self) -> Result<()> {
        Python::with_gil(|py| {
            // Import pyadi-iio
            let adi = py.import_bound("adi").map_err(|e| {
                eyre!("Failed to import pyadi-iio: {}. Is it installed?", e)
            })?;

            // Create SDR object
            let sdr = adi
                .getattr("ad9361")?
                .call1((&self.sdr_uri,))?;

            // Create Phaser object
            let kwargs = PyDict::new_bound(py);
            kwargs.set_item("uri", &self.phaser_uri)?;
            kwargs.set_item("sdr", &sdr)?;
            
            let phaser = adi
                .getattr("CN0566")?
                .call((), Some(&kwargs))?;

            // Configure for receive mode
            phaser.call_method1("configure", ("rx",))?;

            // Store references
            self.py_sdr = Some(sdr.unbind());
            self.py_phaser = Some(phaser.unbind());
            self.initialized = true;

            Ok(())
        })
    }

    /// Set the Phaser output frequency
    #[allow(dead_code)]
    #[cfg(feature = "python")]
    pub fn set_frequency(&self, freq_hz: u64) -> Result<()> {
        if !self.initialized {
            return Ok(());
        }

        Python::with_gil(|py| {
            if let Some(ref phaser) = self.py_phaser {
                phaser.setattr(py, "frequency", freq_hz / 4)?;
            }
            Ok(())
        })
    }

    /// Set channel gains
    #[allow(dead_code)]
    #[cfg(feature = "python")]
    pub fn set_channel_gains(&self, gains: &[u8; 8]) -> Result<()> {
        if !self.initialized {
            return Ok(());
        }

        Python::with_gil(|py| {
            if let Some(ref phaser) = self.py_phaser {
                let p = phaser.bind(py);
                for (i, &gain) in gains.iter().enumerate() {
                    let kwargs = PyDict::new_bound(py);
                    kwargs.set_item("apply_cal", true)?;
                    p.call_method("set_chan_gain", (i, gain), Some(&kwargs))?;
                }
            }
            Ok(())
        })
    }

    /// Configure FMCW parameters
    #[allow(dead_code)]
    #[cfg(feature = "python")]
    pub fn configure_fmcw(&self, chirp_bw: f64, ramp_time_us: u32) -> Result<()> {
        if !self.initialized {
            return Ok(());
        }

        Python::with_gil(|py| {
            if let Some(ref phaser) = self.py_phaser {
                let p = phaser.bind(py);
                p.setattr("freq_dev_range", (chirp_bw / 4.0) as i64)?;
                p.setattr("freq_dev_step", ((chirp_bw / 4.0) / ramp_time_us as f64) as i64)?;
                p.setattr("freq_dev_time", ramp_time_us)?;
                p.setattr("ramp_mode", "single_sawtooth_burst")?;
                p.setattr("enable", 0)?; // Write last to update registers
            }
            Ok(())
        })
    }

    /// Trigger a radar burst
    pub fn trigger_burst(&self) -> Result<()> {
        #[cfg(feature = "python")]
        if self.initialized {
            Python::with_gil(|py| -> pyo3::PyResult<()> {
                if let Some(ref phaser) = self.py_phaser {
                    let p = phaser.bind(py);
                    let gpios = p.getattr("_gpios")?;
                    gpios.setattr("gpio_burst", 0)?;
                    gpios.setattr("gpio_burst", 1)?;
                    gpios.setattr("gpio_burst", 0)?;
                }
                Ok(())
            })?;
        }
        Ok(())
    }

    /// Check if connected
    #[allow(dead_code)]
    pub fn is_connected(&self) -> bool {
        self.initialized
    }
}
