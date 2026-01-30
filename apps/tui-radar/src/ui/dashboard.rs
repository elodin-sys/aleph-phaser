//! Full-screen dashboard layout

use ratatui::{
    prelude::*,
    widgets::{Block, Borders, Paragraph},
};

use crate::app::App;
use super::heatmap::render_heatmap;
use super::spectrum::{render_color_scale, render_spectrum};

/// Draw the complete dashboard
pub fn draw(frame: &mut Frame, app: &App) {
    let size = frame.area();

    // Main layout: header, content, footer
    let main_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(20),    // Content
            Constraint::Length(3),  // Performance bar
            Constraint::Length(3),  // Controls bar
        ])
        .split(size);

    // Draw header
    draw_header(frame, main_chunks[0], app);

    // Content: heatmap (left 75%) + side panels (right 25%)
    let content_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(75),  // Main heatmap
            Constraint::Percentage(25),  // Side panels
        ])
        .split(main_chunks[1]);

    // Draw main Range-Doppler heatmap
    let max_doppler = app.config.max_doppler();
    let range_bounds = (-app.config.max_range, app.config.max_range);
    let doppler_bounds = (-max_doppler, max_doppler);

    render_heatmap(
        frame,
        content_chunks[0],
        &app.rd_map,
        app.colormap,
        app.display_min_db(),
        app.display_max_db(),
        range_bounds,
        doppler_bounds,
        " RANGE-DOPPLER MAP ",
    );

    // Side panels: Range spectrum, Doppler spectrum, Color scale
    let side_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage(35),  // Range spectrum
            Constraint::Percentage(35),  // Doppler spectrum
            Constraint::Percentage(30),  // Color scale + info
        ])
        .split(content_chunks[1]);

    // Range spectrum
    render_spectrum(
        frame,
        side_chunks[0],
        &app.range_spectrum,
        app.colormap,
        app.display_min_db(),
        app.display_max_db(),
        range_bounds,
        " RANGE SPECTRUM ",
        "Range (m)",
    );

    // Doppler spectrum
    render_spectrum(
        frame,
        side_chunks[1],
        &app.doppler_spectrum,
        app.colormap,
        app.display_min_db(),
        app.display_max_db(),
        doppler_bounds,
        " DOPPLER SPECTRUM ",
        "Doppler (Hz)",
    );

    // Color scale and info
    render_color_scale(
        frame,
        side_chunks[2],
        app.colormap,
        app.display_min_db(),
        app.display_max_db(),
    );

    // Draw performance bar
    draw_performance_bar(frame, main_chunks[2], app);

    // Draw controls bar
    draw_controls_bar(frame, main_chunks[3], app);
}

/// Draw the header bar
fn draw_header(frame: &mut Frame, area: Rect, app: &App) {
    let status_style = |connected: bool| {
        if connected {
            Style::default().fg(Color::Green)
        } else {
            Style::default().fg(Color::Red)
        }
    };

    let mode = if app.config.synthetic { "SYNTHETIC" } else { "LIVE" };
    let mti = if app.mti_enabled { "ON" } else { "OFF" };

    let header = Paragraph::new(Line::from(vec![
        Span::styled(" GPU RANGE-DOPPLER RADAR ", Style::default().fg(Color::Cyan).bold()),
        Span::raw("│"),
        Span::styled(" Aleph/Orin NX ", Style::default().fg(Color::Yellow)),
        Span::raw("│"),
        Span::styled(format!(" FPS: {:.1} ", app.fps), Style::default().fg(Color::Green)),
        Span::raw("│"),
        Span::styled(
            format!(" GPU: {:.1}ms ", app.processing_time_ms),
            Style::default().fg(Color::Magenta),
        ),
        Span::raw("│"),
        Span::styled(format!(" Mode: {} ", mode), Style::default().fg(Color::White)),
        Span::raw("│"),
        Span::styled(format!(" MTI: {} ", mti), Style::default().fg(Color::White)),
        Span::raw("│"),
        Span::styled(
            format!(" {} chirps × {} samples ", app.config.n_doppler, app.config.n_range),
            Style::default().fg(Color::White),
        ),
        Span::raw("│"),
        Span::styled(" SDR ", status_style(app.sdr_connected)),
        Span::styled("●", status_style(app.sdr_connected)),
        Span::raw(" "),
        Span::styled(" Phaser ", status_style(app.phaser_connected)),
        Span::styled("●", status_style(app.phaser_connected)),
        Span::raw(" "),
        Span::styled(" GPU ", status_style(app.gpu_available)),
        Span::styled("●", status_style(app.gpu_available)),
    ]))
    .block(Block::default().borders(Borders::ALL));

    frame.render_widget(header, area);
}

/// Draw the performance metrics bar
fn draw_performance_bar(frame: &mut Frame, area: Rect, app: &App) {
    let speedup = if app.processing_time_ms > 0.0 {
        // Estimate CPU time as ~50ms for comparison
        50.0 / app.processing_time_ms
    } else {
        1.0
    };

    let perf = Paragraph::new(Line::from(vec![
        Span::styled(" PERFORMANCE ", Style::default().fg(Color::Cyan).bold()),
        Span::raw("│"),
        Span::styled(
            format!(" Processing: {:.1}ms ", app.processing_time_ms),
            Style::default().fg(Color::Green),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" Capture: {:.1}ms ", app.capture_time_ms),
            Style::default().fg(Color::Yellow),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" Total: {:.1}ms ", app.total_time_ms()),
            Style::default().fg(Color::Magenta),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" Speedup: {:.1}x ", speedup),
            Style::default().fg(Color::Cyan),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" Gain: {:+.0}dB ", app.gain_db),
            Style::default().fg(Color::White),
        ),
    ]))
    .block(Block::default().borders(Borders::ALL));

    frame.render_widget(perf, area);
}

/// Draw the controls help bar
fn draw_controls_bar(frame: &mut Frame, area: Rect, app: &App) {
    let paused_indicator = if app.paused { " [PAUSED] " } else { "" };

    let controls = Paragraph::new(Line::from(vec![
        Span::styled(paused_indicator, Style::default().fg(Color::Red).bold()),
        Span::styled(" [Q]", Style::default().fg(Color::Yellow)),
        Span::raw("uit "),
        Span::styled(" [P]", Style::default().fg(Color::Yellow)),
        Span::raw("ause "),
        Span::styled(" [+/-]", Style::default().fg(Color::Yellow)),
        Span::raw("Gain "),
        Span::styled(" [C]", Style::default().fg(Color::Yellow)),
        Span::raw("olormap "),
        Span::styled(" [M]", Style::default().fg(Color::Yellow)),
        Span::raw("TI Filter "),
        Span::styled(" [R]", Style::default().fg(Color::Yellow)),
        Span::raw("eset "),
        Span::raw("│"),
        Span::styled(
            format!(" Sample Rate: {}MHz ", app.config.sample_rate / 1_000_000),
            Style::default().fg(Color::White),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" BW: {}MHz ", app.config.chirp_bw as u64 / 1_000_000),
            Style::default().fg(Color::White),
        ),
        Span::raw("│"),
        Span::styled(
            format!(" Max Range: {:.0}m ", app.config.max_range),
            Style::default().fg(Color::White),
        ),
    ]))
    .block(Block::default().borders(Borders::ALL));

    frame.render_widget(controls, area);
}
