//! User interface module
//!
//! Provides TUI components using Ratatui:
//! - Full-screen dashboard layout
//! - Braille-based heatmap with true color
//! - Spectrum plots
//! - Status and metrics displays

mod colormap;
mod dashboard;
mod heatmap;
mod spectrum;

pub use colormap::Colormap;
pub use dashboard::draw;
