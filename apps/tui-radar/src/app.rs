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
    /// Minimum display value (dB) - base scale from Python
    pub min_db: f32,
    /// Maximum display value (dB) - base scale from Python
    pub max_db: f32,
    /// Auto-scale mode (like thermal camera)
    pub auto_scale: bool,
    /// Current auto-scaled min (smoothed)
    auto_min: f32,
    /// Current auto-scaled max (smoothed)
    auto_max: f32,
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
    /// Current test pattern (synthetic mode only)
    pub test_pattern: String,
    /// Debug overlay mode
    pub debug_overlay: bool,
    /// Last status message (for export notifications, etc.)
    pub status_message: Option<String>,
    /// Frame count for status message timeout
    status_message_frames: u64,
}

impl App {
    /// Create a new application instance
    pub fn new(config: RadarConfig) -> Result<Self> {
        // Create data source (Python backend)
        let data_source = DataSource::new(&config)?;

        // Get actual dimensions and display range from the backend
        let n_doppler = data_source.n_doppler;
        let n_range = data_source.n_range;
        let min_db = data_source.min_scale;
        let max_db = data_source.max_scale;

        // Initialize empty arrays with correct dimensions
        let rd_map = Array2::zeros((n_doppler, n_range));
        let range_spectrum = vec![0.0; n_range];
        let doppler_spectrum = vec![0.0; n_doppler];

        let is_synthetic = config.synthetic;
        let test_pattern = config.test_pattern.clone();

        Ok(Self {
            config,
            data_source,
            rd_map,
            range_spectrum,
            doppler_spectrum,
            colormap: Colormap::Inferno,
            gain_db: 0.0,
            min_db,
            max_db,
            auto_scale: true,  // Enable auto-scale by default
            auto_min: min_db,
            auto_max: max_db,
            mti_enabled: false,
            paused: false,
            frame_count: 0,
            fps: 0.0,
            last_fps_time: Instant::now(),
            frame_time_ms: 0.0,
            n_doppler,
            n_range,
            is_synthetic,
            test_pattern,
            debug_overlay: false,
            status_message: None,
            status_message_frames: 0,
        })
    }

    /// Update application state (called each frame)
    pub fn update(&mut self) -> Result<()> {
        let frame_start = Instant::now();

        // Capture and process frame (all done in Python)
        self.rd_map = self.data_source.capture()?;

        self.frame_time_ms = frame_start.elapsed().as_secs_f32() * 1000.0;

        // Update auto-scale bounds if enabled
        if self.auto_scale {
            self.update_auto_scale();
        }

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

        // Clear status message after ~3 seconds (90 frames at 30fps)
        if self.status_message.is_some() {
            self.status_message_frames += 1;
            if self.status_message_frames > 90 {
                self.status_message = None;
                self.status_message_frames = 0;
            }
        }

        Ok(())
    }

    /// Update auto-scale bounds based on current frame
    fn update_auto_scale(&mut self) {
        // Find current frame min/max
        let mut frame_min = f32::INFINITY;
        let mut frame_max = f32::NEG_INFINITY;
        
        for &val in self.rd_map.iter() {
            if val < frame_min {
                frame_min = val;
            }
            if val > frame_max {
                frame_max = val;
            }
        }
        
        // Ensure we have a valid range
        if frame_max <= frame_min {
            frame_max = frame_min + 1.0;
        }
        
        // Add a small margin (5%) for visual comfort
        let range = frame_max - frame_min;
        let margin = range * 0.05;
        frame_min -= margin;
        frame_max += margin;
        
        // Smooth the transition (exponential moving average)
        // Higher alpha = faster response, lower alpha = smoother
        let alpha = 0.3;
        self.auto_min = self.auto_min * (1.0 - alpha) + frame_min * alpha;
        self.auto_max = self.auto_max * (1.0 - alpha) + frame_max * alpha;
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

    /// Increase display gain (shift display window up)
    pub fn increase_gain(&mut self) {
        // Gain shifts the display window; max shift is limited by scale range
        let range = self.max_db - self.min_db;
        self.gain_db = (self.gain_db + range * 0.1).min(range);
    }

    /// Decrease display gain (shift display window down)
    pub fn decrease_gain(&mut self) {
        let range = self.max_db - self.min_db;
        self.gain_db = (self.gain_db - range * 0.1).max(-range);
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

    /// Toggle auto-scale mode
    pub fn toggle_auto_scale(&mut self) {
        self.auto_scale = !self.auto_scale;
        if self.auto_scale {
            // Reset auto bounds to current frame when re-enabling
            self.auto_min = self.min_db;
            self.auto_max = self.max_db;
        }
    }

    /// Cycle through test patterns (synthetic mode only)
    pub fn cycle_test_pattern(&mut self) {
        if self.is_synthetic {
            if let Ok(pattern) = self.data_source.cycle_test_pattern() {
                self.test_pattern = pattern;
            }
        }
    }

    /// Toggle debug overlay
    pub fn toggle_debug_overlay(&mut self) {
        self.debug_overlay = !self.debug_overlay;
    }

    /// Export current frame to file
    pub fn export_frame(&mut self) {
        match self.data_source.export_frame("./exports") {
            Ok(path) => {
                self.status_message = Some(format!("Exported: {}", path));
                self.status_message_frames = 0;
            }
            Err(e) => {
                self.status_message = Some(format!("Export failed: {}", e));
                self.status_message_frames = 0;
            }
        }
    }

    /// Reset to default state
    pub fn reset(&mut self) {
        self.gain_db = 0.0;
        self.mti_enabled = false;
        self.auto_scale = true;
        self.debug_overlay = false;
        let _ = self.data_source.set_mti(false);
        self.colormap = Colormap::Inferno;
        // Reset test pattern to animated
        if self.is_synthetic {
            let _ = self.data_source.set_test_pattern("animated");
            self.test_pattern = "animated".to_string();
        }
    }

    /// Get effective min value for display
    pub fn display_min_db(&self) -> f32 {
        if self.auto_scale {
            self.auto_min
        } else {
            self.min_db - self.gain_db
        }
    }

    /// Get effective max value for display
    pub fn display_max_db(&self) -> f32 {
        if self.auto_scale {
            self.auto_max
        } else {
            self.max_db - self.gain_db
        }
    }
}

impl Drop for App {
    fn drop(&mut self) {
        self.data_source.shutdown();
    }
}
