//! Data acquisition module
//!
//! Provides a unified interface to the Python RadarBackend for both
//! hardware and synthetic data sources. All radar processing is done
//! in Python (with GPU acceleration via CuPy), and only the final
//! Range-Doppler map is returned to Rust for display.

use color_eyre::{eyre::eyre, Result};
use ndarray::Array2;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::config::RadarConfig;

/// Data source that wraps the Python RadarBackend
pub struct DataSource {
    py_backend: Py<PyAny>,

    /// Dimensions of the output RD map
    pub n_doppler: usize,
    pub n_range: usize,
    
    /// Display value range (from Python's min_scale, max_scale)
    pub min_scale: f32,
    pub max_scale: f32,
}

impl DataSource {
    /// Create a new data source
    pub fn new(config: &RadarConfig) -> Result<Self> {
        Python::with_gil(|py| {
            // Add the python directory to the path
            let sys = py.import_bound("sys")?;
            let path = sys.getattr("path")?;

            // Try multiple possible locations for the Python module
            let possible_paths = [
                "python", // Relative to CWD
                "./python",
                "../python",
                "/opt/phaser/scripts/tui-radar/python", // Deployed location
            ];

            for p in possible_paths {
                let _ = path.call_method1("insert", (0, p));
            }

            // Import our radar_backend module
            let radar_backend = py.import_bound("radar_backend").map_err(|e| {
                eyre!("Failed to import radar_backend module: {}. Make sure radar_backend.py is in the python directory.", e)
            })?;

            // Determine mode
            let mode = if config.synthetic {
                "synthetic"
            } else {
                "hardware"
            };

            // Create kwargs for the factory function
            let kwargs = PyDict::new_bound(py);
            kwargs.set_item("mode", mode)?;
            kwargs.set_item("sdr_uri", &config.sdr_uri)?;
            kwargs.set_item("phaser_uri", &config.phaser_uri)?;
            kwargs.set_item("sample_rate", config.sample_rate)?;
            kwargs.set_item("num_chirps", config.n_doppler)?;
            kwargs.set_item("ramp_time_us", config.ramp_time_us)?;
            kwargs.set_item("chirp_bw", config.chirp_bw)?;
            kwargs.set_item("center_freq", config.center_freq)?;
            kwargs.set_item("output_freq", config.output_freq)?;
            kwargs.set_item("rx_gain", config.rx_gain)?;
            kwargs.set_item("max_range", config.max_range)?;
            kwargs.set_item("test_pattern", &config.test_pattern)?;

            // Create the backend
            let backend = radar_backend
                .getattr("create_backend")?
                .call((), Some(&kwargs))?;

            // Get dimensions from Python
            let dims: (usize, usize) = backend.call_method0("get_dimensions")?.extract()?;
            let (n_doppler, n_range) = dims;

            // Get display range from Python config
            let py_config = backend.call_method0("get_config")?;
            let min_scale: f32 = py_config.get_item("min_scale")?.extract()?;
            let max_scale: f32 = py_config.get_item("max_scale")?.extract()?;

            Ok(Self {
                py_backend: backend.unbind(),
                n_doppler,
                n_range,
                min_scale,
                max_scale,
            })
        })
    }

    /// Capture a frame from the data source
    /// Returns a 2D array of dB values, shape (n_doppler, n_range)
    pub fn capture(&mut self) -> Result<Array2<f32>> {
        Python::with_gil(|py| {
            // Call get_frame() on the Python backend
            let frame = self.py_backend.bind(py).call_method0("get_frame")?;

            // Convert numpy array to Rust ndarray
            let numpy = py.import_bound("numpy")?;
            let frame_np = frame.call_method1("astype", (numpy.getattr("float32")?,))?;

            // Get shape
            let shape: (usize, usize) = frame_np.getattr("shape")?.extract()?;

            // Get data as flat list and convert to Array2
            let flat: Vec<f32> = frame_np
                .call_method0("flatten")?
                .call_method0("tolist")?
                .extract()?;

            let array = Array2::from_shape_vec((shape.0, shape.1), flat)
                .map_err(|e| eyre!("Failed to create array: {}", e))?;

            Ok(array)
        })
    }

    /// Set MTI filter state
    pub fn set_mti(&mut self, enabled: bool) -> Result<()> {
        Python::with_gil(|py| {
            self.py_backend
                .bind(py)
                .call_method1("set_mti", (enabled,))?;
            Ok(())
        })
    }

    /// Set test pattern (synthetic mode only)
    pub fn set_test_pattern(&mut self, pattern: &str) -> Result<()> {
        Python::with_gil(|py| {
            self.py_backend
                .bind(py)
                .call_method1("set_test_pattern", (pattern,))?;
            Ok(())
        })
    }

    /// Cycle to next test pattern (synthetic mode only)
    pub fn cycle_test_pattern(&mut self) -> Result<String> {
        Python::with_gil(|py| {
            let result = self
                .py_backend
                .bind(py)
                .call_method0("cycle_test_pattern")?;
            let pattern: String = result.extract()?;
            Ok(pattern)
        })
    }

    /// Get current test pattern name (synthetic mode only)
    pub fn get_test_pattern(&self) -> Result<String> {
        Python::with_gil(|py| {
            let result = self.py_backend.bind(py).call_method0("get_test_pattern")?;
            let pattern: String = result.extract()?;
            Ok(pattern)
        })
    }

    /// Export current frame to a file
    pub fn export_frame(&self, directory: &str) -> Result<String> {
        Python::with_gil(|py| {
            let result = self
                .py_backend
                .bind(py)
                .call_method1("export_frame", (directory,))?;
            let path: String = result.extract()?;
            Ok(path)
        })
    }

    /// Shutdown the data source
    pub fn shutdown(&self) {
        let _ = Python::with_gil(|py| -> PyResult<()> {
            self.py_backend.bind(py).call_method0("shutdown")?;
            Ok(())
        });
    }

    /// Check if this is synthetic mode
    #[allow(dead_code)]
    pub fn is_synthetic(&self) -> bool {
        Python::with_gil(|py| {
            self.py_backend
                .bind(py)
                .getattr("mode")
                .and_then(|m| m.extract::<String>())
                .map(|m| m == "synthetic")
                .unwrap_or(true)
        })
    }
}

impl Drop for DataSource {
    fn drop(&mut self) {
        self.shutdown();
    }
}
