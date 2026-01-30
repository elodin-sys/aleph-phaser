//! Signal processing module
//!
//! Provides Range-Doppler map generation with:
//! - 2D FFT processing
//! - Windowing functions
//! - MTI filtering
//! - GPU acceleration (optional)

mod range_doppler;
mod window;

#[cfg(feature = "gpu")]
mod gpu_fft;

pub use range_doppler::RangeDopplerProcessor;
