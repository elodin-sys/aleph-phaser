//! Application state and logic

use color_eyre::Result;
use ndarray::Array2;
use std::time::{Duration, Instant};

use crate::config::RadarConfig;
use crate::data::DataSource;
use crate::processing::RangeDopplerProcessor;
use crate::ui::Colormap;

/// Application state
pub struct App {
    /// Radar configuration
    pub config: RadarConfig,
    /// Data source (synthetic or hardware)
    data_source: DataSource,
    /// Signal processor
    processor: RangeDopplerProcessor,
    /// Current Range-Doppler map (dB)
    pub rd_map: Array2<f32>,
    /// Range spectrum (sum along Doppler axis)
    pub range_spectrum: Vec<f32>,
    /// Doppler spectrum (sum along Range axis)
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
    /// Frame counter
    pub frame_count: u64,
    /// FPS measurement
    pub fps: f32,
    /// Last frame time
    last_frame_time: Instant,
    /// Processing time (ms)
    pub processing_time_ms: f32,
    /// Capture time (ms)
    pub capture_time_ms: f32,
    /// Render time (ms)
    pub render_time_ms: f32,
    /// Connection status
    pub sdr_connected: bool,
    pub phaser_connected: bool,
    pub gpu_available: bool,
}

impl App {
    /// Create a new application instance
    pub fn new(config: RadarConfig) -> Result<Self> {
        let n_range = config.n_range;
        let n_doppler = config.n_doppler;
        let synthetic = config.synthetic;

        // Initialize data source
        let data_source = if config.synthetic {
            DataSource::new_synthetic(n_range, n_doppler)
        } else {
            DataSource::new_hardware(&config.sdr_uri, &config.phaser_uri)?
        };

        // Initialize processor
        let processor = RangeDopplerProcessor::new(n_range, n_doppler);

        // Initialize empty arrays
        let rd_map = Array2::zeros((n_doppler, n_range));
        let range_spectrum = vec![0.0; n_range];
        let doppler_spectrum = vec![0.0; n_doppler];

        Ok(Self {
            config,
            data_source,
            processor,
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
            last_frame_time: Instant::now(),
            processing_time_ms: 0.0,
            capture_time_ms: 0.0,
            render_time_ms: 0.0,
            sdr_connected: synthetic,
            phaser_connected: synthetic,
            gpu_available: cfg!(feature = "gpu"),
        })
    }

    /// Update application state (called each frame)
    pub fn update(&mut self) -> Result<()> {
        let _frame_start = Instant::now();

        // Capture data
        let capture_start = Instant::now();
        let raw_data = self.data_source.capture()?;
        self.capture_time_ms = capture_start.elapsed().as_secs_f32() * 1000.0;

        // Process data
        let process_start = Instant::now();
        self.rd_map = self.processor.process(&raw_data, self.mti_enabled);
        self.processing_time_ms = process_start.elapsed().as_secs_f32() * 1000.0;

        // Compute spectra
        self.compute_spectra();

        // Update timing
        self.frame_count += 1;
        let elapsed = self.last_frame_time.elapsed();
        if elapsed >= Duration::from_secs(1) {
            self.fps = self.frame_count as f32 / elapsed.as_secs_f32();
            self.frame_count = 0;
            self.last_frame_time = Instant::now();
        }

        Ok(())
    }

    /// Compute 1D spectra from the Range-Doppler map
    fn compute_spectra(&mut self) {
        let (n_doppler, n_range) = self.rd_map.dim();

        // Range spectrum: max along Doppler axis for each range bin
        self.range_spectrum.clear();
        for r in 0..n_range {
            let max_val = (0..n_doppler)
                .map(|d| self.rd_map[[d, r]])
                .fold(f32::NEG_INFINITY, f32::max);
            self.range_spectrum.push(max_val);
        }

        // Doppler spectrum: max along Range axis for each Doppler bin
        self.doppler_spectrum.clear();
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
    }

    /// Reset to default state
    pub fn reset(&mut self) {
        self.gain_db = 0.0;
        self.mti_enabled = false;
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

    /// Get total processing time
    pub fn total_time_ms(&self) -> f32 {
        self.capture_time_ms + self.processing_time_ms + self.render_time_ms
    }
}
