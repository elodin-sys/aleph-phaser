//! GPU-Accelerated Range-Doppler Radar TUI
//!
//! A real-time terminal user interface for visualizing Range-Doppler maps
//! from the CN0566 Phaser radar system, designed for high frame rates
//! over SSH connections to the Aleph/Orin NX platform.
//!
//! All radar processing is handled by the Python backend (radar_backend.py)
//! which uses CuPy for GPU acceleration. The Rust TUI only handles display
//! and user input.

mod app;
mod config;
mod data;
mod processing;
mod ui;

use clap::Parser;
use color_eyre::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::prelude::*;
use std::io::stdout;
use std::time::{Duration, Instant};

use app::App;
use config::RadarConfig;

/// GPU-Accelerated Range-Doppler Radar TUI
///
/// Displays real-time Range-Doppler maps from the CN0566 Phaser radar.
/// Processing is done in Python with CuPy GPU acceleration.
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// PlutoSDR URI (e.g., ip:192.168.2.1)
    #[arg(long, default_value = "ip:192.168.2.1")]
    sdr_uri: String,

    /// Phaser/Raspberry Pi URI (e.g., ip:192.168.4.184)
    #[arg(long, default_value = "ip:192.168.4.184")]
    phaser_uri: String,

    /// Use synthetic data (no hardware required)
    #[arg(long, short)]
    synthetic: bool,

    /// Target frame rate
    #[arg(long, default_value = "30")]
    fps: u32,

    /// Number of chirps per frame (Doppler bins). More = finer velocity resolution but slower capture.
    #[arg(long, default_value = "256")]
    num_chirps: usize,

    /// Maximum range to display (meters)
    #[arg(long, default_value = "10.0")]
    max_range: f64,

    /// Chirp bandwidth (Hz)
    #[arg(long, default_value = "500000000")]
    chirp_bw: f64,

    /// Ramp time (microseconds)
    #[arg(long, default_value = "500")]
    ramp_time_us: u32,

    /// Sample rate (Hz)
    #[arg(long, default_value = "4000000")]
    sample_rate: u64,

    /// Receive gain (dB)
    #[arg(long, default_value = "30")]
    rx_gain: i32,

    /// Enable DC leakage suppression (per-chirp mean subtraction)
    #[arg(long, default_value = "false")]
    dc_suppression: bool,

    /// Test pattern for synthetic mode (animated, corner_dots, gradient_h, gradient_v, center_target, grid, diagonal, checkerboard)
    #[arg(long, short = 't', default_value = "animated")]
    pattern: String,
}

fn main() -> Result<()> {
    color_eyre::install()?;
    let args = Args::parse();

    // Create radar configuration (n_range is calculated by Python backend)
    let config = RadarConfig {
        sdr_uri: args.sdr_uri,
        phaser_uri: args.phaser_uri,
        synthetic: args.synthetic,
        target_fps: args.fps,
        n_doppler: args.num_chirps,
        max_range: args.max_range,
        chirp_bw: args.chirp_bw,
        ramp_time_us: args.ramp_time_us,
        sample_rate: args.sample_rate,
        center_freq: 2_100_000_000,
        output_freq: 9_900_000_000,
        rx_gain: args.rx_gain,
        dc_suppression: args.dc_suppression,
        test_pattern: args.pattern,
    };

    // Print configuration summary
    eprintln!("TUI Radar Configuration:");
    eprintln!(
        "  Mode: {}",
        if config.synthetic {
            "Synthetic"
        } else {
            "Hardware"
        }
    );
    if config.synthetic {
        eprintln!("  Test Pattern: {}", config.test_pattern);
    }
    eprintln!("  Doppler bins (chirps): {}", config.n_doppler);
    eprintln!("  Expected range bins: {}", config.expected_n_range());
    eprintln!("  Target FPS: {}", config.target_fps);
    if !config.synthetic {
        eprintln!("  SDR URI: {}", config.sdr_uri);
        eprintln!("  Phaser URI: {}", config.phaser_uri);
    }
    eprintln!();

    // Initialize app (Python backend) BEFORE entering raw mode
    // This way hardware errors are shown cleanly without breaking the terminal
    let mut app = App::new(config)?;

    // Setup terminal (only after app is successfully initialized)
    enable_raw_mode()?;
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Run the app
    let result = run_app(&mut terminal, &mut app);

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = result {
        eprintln!("Error: {err:?}");
    }

    Ok(())
}

fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App) -> Result<()> {
    let tick_rate = Duration::from_millis(1000 / app.config.target_fps as u64);
    let mut last_tick = Instant::now();

    loop {
        // Draw UI
        terminal.draw(|frame| ui::draw(frame, app))?;

        // Handle input with timeout
        let timeout = tick_rate.saturating_sub(last_tick.elapsed());
        if crossterm::event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') | KeyCode::Esc => return Ok(()),
                        KeyCode::Char('p') => app.toggle_pause(),
                        KeyCode::Char('+') | KeyCode::Char('=') => app.increase_gain(),
                        KeyCode::Char('-') => app.decrease_gain(),
                        KeyCode::Char('c') => app.cycle_colormap(),
                        KeyCode::Char('m') => app.toggle_mti(),
                        KeyCode::Char('a') => app.toggle_auto_scale(),
                        KeyCode::Char('t') => app.cycle_test_pattern(),
                        KeyCode::Char('d') => app.toggle_debug_overlay(),
                        KeyCode::Char('e') => app.export_frame(),
                        KeyCode::Char('r') => app.reset(),
                        _ => {}
                    }
                }
            }
        }

        // Update on tick
        if last_tick.elapsed() >= tick_rate {
            if !app.paused {
                app.update()?;
            }
            last_tick = Instant::now();
        }
    }
}
