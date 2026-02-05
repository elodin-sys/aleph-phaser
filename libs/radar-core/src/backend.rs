//! Python backend wrapper using PyO3.
//!
//! This module provides the PyO3 bridge to the Python `radar_backend` module
//! which handles all radar data acquisition and processing.

use ndarray::Array2;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::config::{RadarConfig, RadarMode};
use crate::error::RadarError;
use crate::frame::FrameDimensions;

/// Python backend wrapper.
///
/// This struct holds the Python backend object and provides methods
/// to interact with it from Rust.
pub struct PythonBackend {
    py_backend: Py<PyAny>,
    n_doppler: usize,
    n_range: usize,
    min_scale: f32,
    max_scale: f32,
    mti_enabled: bool,
}

impl PythonBackend {
    /// Create a new Python backend with the given configuration.
    pub fn new(config: &RadarConfig) -> Result<Self, RadarError> {
        Python::with_gil(|py| {
            // Add the python directory to the path
            let sys = py.import_bound("sys")?;
            let path = sys.getattr("path")?;

            // Try multiple possible locations for the Python module
            let possible_paths = Self::get_python_paths();
            for p in possible_paths {
                let _ = path.call_method1("insert", (0, p));
            }

            // Import our radar_backend module
            let radar_backend = py.import_bound("radar_backend").map_err(|e| {
                RadarError::ImportError(format!(
                    "Failed to import radar_backend module: {}. \
                     Make sure radar_backend.py is in the python directory.",
                    e
                ))
            })?;

            // Determine mode
            let mode = match config.mode {
                RadarMode::Hardware => "hardware",
                RadarMode::Synthetic => "synthetic",
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
            kwargs.set_item("test_pattern", config.test_pattern.name())?;

            // Create the backend
            let backend = radar_backend
                .getattr("create_backend")?
                .call((), Some(&kwargs))
                .map_err(|e| RadarError::InitializationError(e.to_string()))?;

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
                mti_enabled: false,
            })
        })
    }

    /// Get possible paths for the Python module.
    fn get_python_paths() -> Vec<&'static str> {
        vec![
            // Development paths (relative to CWD)
            "python",
            "./python",
            "../python",
            // Library paths (relative to radar-core)
            "libs/radar-core/python",
            "../libs/radar-core/python",
            "../../libs/radar-core/python",
            // Deployed location (Nix package)
            "/opt/phaser/lib/python",
        ]
    }

    /// Capture a frame from the data source.
    ///
    /// Returns a 2D array of dB values, shape (n_doppler, n_range).
    pub fn capture(&mut self) -> Result<Array2<f32>, RadarError> {
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

            let array = Array2::from_shape_vec((shape.0, shape.1), flat)?;

            Ok(array)
        })
    }

    /// Get frame dimensions.
    pub fn dimensions(&self) -> FrameDimensions {
        FrameDimensions {
            n_doppler: self.n_doppler as u32,
            n_range: self.n_range as u32,
        }
    }

    /// Get minimum scale value.
    pub fn min_scale(&self) -> f32 {
        self.min_scale
    }

    /// Get maximum scale value.
    pub fn max_scale(&self) -> f32 {
        self.max_scale
    }

    /// Get MTI filter state.
    pub fn mti_enabled(&self) -> bool {
        self.mti_enabled
    }

    /// Set MTI filter state.
    pub fn set_mti(&mut self, enabled: bool) -> Result<(), RadarError> {
        Python::with_gil(|py| {
            self.py_backend
                .bind(py)
                .call_method1("set_mti", (enabled,))?;
            self.mti_enabled = enabled;
            Ok(())
        })
    }

    /// Set test pattern (synthetic mode only).
    pub fn set_test_pattern(&mut self, pattern: &str) -> Result<(), RadarError> {
        Python::with_gil(|py| {
            self.py_backend
                .bind(py)
                .call_method1("set_test_pattern", (pattern,))?;
            Ok(())
        })
    }

    /// Cycle to next test pattern (synthetic mode only).
    ///
    /// Returns the name of the new pattern.
    pub fn cycle_test_pattern(&mut self) -> Result<String, RadarError> {
        Python::with_gil(|py| {
            let result = self
                .py_backend
                .bind(py)
                .call_method0("cycle_test_pattern")?;
            let pattern: String = result.extract()?;
            Ok(pattern)
        })
    }

    /// Get current test pattern name (synthetic mode only).
    pub fn get_test_pattern(&self) -> Result<String, RadarError> {
        Python::with_gil(|py| {
            let result = self.py_backend.bind(py).call_method0("get_test_pattern")?;
            let pattern: String = result.extract()?;
            Ok(pattern)
        })
    }

    /// Export current frame to a file.
    ///
    /// Returns the path to the exported file.
    pub fn export_frame(&self, directory: &str) -> Result<String, RadarError> {
        Python::with_gil(|py| {
            let result = self
                .py_backend
                .bind(py)
                .call_method1("export_frame", (directory,))?;
            let path: String = result.extract()?;
            Ok(path)
        })
    }

    /// Shutdown the data source.
    pub fn shutdown(&self) {
        let _ = Python::with_gil(|py| -> PyResult<()> {
            self.py_backend.bind(py).call_method0("shutdown")?;
            Ok(())
        });
    }

    /// Check if this is synthetic mode.
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

impl Drop for PythonBackend {
    fn drop(&mut self) {
        self.shutdown();
    }
}
