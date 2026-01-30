//! Application state and logic

use color_eyre::Result;
use ndarray::Array2;
use std::time::{Duration, Instant};

use crate::config::RadarConfig;
use crate::data::DataSource;
use crate::ui::Colormap;

/// Application state
pub struct App {
    /// Radar configuration
    pub config: RadarConfig,
    /// Data source (Python backend handles both synthetic and hardware)
    data_source: DataSource,
    /// Current Range-Doppler map (dB)
    pub rd_map: Array2<f32>,
    /// Range spectrum (max along Doppler axis)
    pub range_spectrum: Vec<f32>,
    /// Doppler spectrum (max along Range axis)
    pub doppler_spectrum: Vec<f32>,
    /// Current colormap
    pub colormap: Colormap,
    /// Display gain adjustment (dB)
    pub gain_db: f32,
    /// Minimum display value (dB)
    pub min_db: f32,
    /// Maximum display value (dB)
    pub max_db: f32,
    /// MTI (Moving Target Indicator) filter enabled
    pub mti_enabled: bool,
    /// Paused state
    pub paused: bool,
    /// Frame counter (for FPS calculation)
    frame_count: u64,
    /// FPS measurement
    pub fps: f32,
    /// Last FPS update time
    last_fps_time: Instant,
    /// Frame time (capture + processing, ms)
    pub frame_time_ms: f32,
    /// Actual dimensions from Python backend
    pub n_doppler: usize,
    pub n_range: usize,
    /// Connection/mode status
    pub is_synthetic: bool,
}

impl App {
    /// Create a new application instance
    pub fn new(config: RadarConfig) -> Result<Self> {
        // Create data source (Python backend)
        let data_source = DataSource::new(&config)?;

        // Get actual dimensions from the backend
        let n_doppler = data_source.n_doppler;
        let n_range = data_source.n_range;

        // Initialize empty arrays with correct dimensions
        let rd_map = Array2::zeros((n_doppler, n_range));
        let range_spectrum = vec![0.0; n_range];
        let doppler_spectrum = vec![0.0; n_doppler];

        let is_synthetic = config.synthetic;

        Ok(Self {
            config,
            data_source,
            rd_map,
            range_spectrum,
            doppler_spectrum,
            colormap: Colormap::Inferno,
            gain_db: 0.0,
            min_db: -60.0,
            max_db: 0.0,
            mti_enabled: false,
            paused: false,
            frame_count: 0,
            fps: 0.0,
            last_fps_time: Instant::now(),
            frame_time_ms: 0.0,
            n_doppler,
            n_range,
            is_synthetic,
        })
    }

    /// Update application state (called each frame)
    pub fn update(&mut self) -> Result<()> {
        let frame_start = Instant::now();

        // Capture and process frame (all done in Python)
        self.rd_map = self.data_source.capture()?;

        self.frame_time_ms = frame_start.elapsed().as_secs_f32() * 1000.0;

        // Compute 1D spectra for side displays
        self.compute_spectra();

        // Update FPS counter
        self.frame_count += 1;
        let elapsed = self.last_fps_time.elapsed();
        if elapsed >= Duration::from_secs(1) {
            self.fps = self.frame_count as f32 / elapsed.as_secs_f32();
            self.frame_count = 0;
            self.last_fps_time = Instant::now();
        }

        Ok(())
    }

    /// Compute 1D spectra from the Range-Doppler map
    fn compute_spectra(&mut self) {
        let (n_doppler, n_range) = self.rd_map.dim();

        // Range spectrum: max along Doppler axis for each range bin
        self.range_spectrum.clear();
        self.range_spectrum.reserve(n_range);
        for r in 0..n_range {
            let max_val = (0..n_doppler)
                .map(|d| self.rd_map[[d, r]])
                .fold(f32::NEG_INFINITY, f32::max);
            self.range_spectrum.push(max_val);
        }

        // Doppler spectrum: max along Range axis for each Doppler bin
        self.doppler_spectrum.clear();
        self.doppler_spectrum.reserve(n_doppler);
        for d in 0..n_doppler {
            let max_val = (0..n_range)
                .map(|r| self.rd_map[[d, r]])
                .fold(f32::NEG_INFINITY, f32::max);
            self.doppler_spectrum.push(max_val);
        }
    }

    /// Toggle pause state
    pub fn toggle_pause(&mut self) {
        self.paused = !self.paused;
    }

    /// Increase display gain
    pub fn increase_gain(&mut self) {
        self.gain_db = (self.gain_db + 5.0).min(60.0);
    }

    /// Decrease display gain
    pub fn decrease_gain(&mut self) {
        self.gain_db = (self.gain_db - 5.0).max(-60.0);
    }

    /// Cycle through colormaps
    pub fn cycle_colormap(&mut self) {
        self.colormap = match self.colormap {
            Colormap::Inferno => Colormap::Plasma,
            Colormap::Plasma => Colormap::Viridis,
            Colormap::Viridis => Colormap::Magma,
            Colormap::Magma => Colormap::Inferno,
        };
    }

    /// Toggle MTI filter
    pub fn toggle_mti(&mut self) {
        self.mti_enabled = !self.mti_enabled;
        // Propagate to Python backend
        let _ = self.data_source.set_mti(self.mti_enabled);
    }

    /// Reset to default state
    pub fn reset(&mut self) {
        self.gain_db = 0.0;
        self.mti_enabled = false;
        let _ = self.data_source.set_mti(false);
        self.colormap = Colormap::Inferno;
    }

    /// Get effective min dB for display
    pub fn display_min_db(&self) -> f32 {
        self.min_db - self.gain_db
    }

    /// Get effective max dB for display
    pub fn display_max_db(&self) -> f32 {
        self.max_db - self.gain_db
    }
}

impl Drop for App {
    fn drop(&mut self) {
        self.data_source.shutdown();
    }
}
