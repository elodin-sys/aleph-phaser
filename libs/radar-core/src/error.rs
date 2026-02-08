//! Error types for radar-core library.

use thiserror::Error;

/// Errors that can occur during radar operations.
#[derive(Debug, Error)]
pub enum RadarError {
    /// Python backend initialization failed.
    #[error("Failed to initialize Python backend: {0}")]
    InitializationError(String),

    /// Python module import failed.
    #[error("Failed to import Python module: {0}")]
    ImportError(String),

    /// Frame capture failed.
    #[error("Failed to capture frame: {0}")]
    CaptureError(String),

    /// Invalid test pattern name.
    #[error("Invalid test pattern: {0}")]
    InvalidPattern(String),

    /// Configuration error.
    #[error("Configuration error: {0}")]
    ConfigError(String),

    /// Hardware connection failed.
    #[error("Hardware connection failed: {0}")]
    HardwareError(String),

    /// Export operation failed.
    #[error("Export failed: {0}")]
    ExportError(String),

    /// Generic Python error.
    #[error("Python error: {0}")]
    PythonError(String),

    /// Array shape mismatch.
    #[error("Array shape error: {0}")]
    ShapeError(String),
}

impl From<pyo3::PyErr> for RadarError {
    fn from(err: pyo3::PyErr) -> Self {
        RadarError::PythonError(err.to_string())
    }
}

impl From<ndarray::ShapeError> for RadarError {
    fn from(err: ndarray::ShapeError) -> Self {
        RadarError::ShapeError(err.to_string())
    }
}
