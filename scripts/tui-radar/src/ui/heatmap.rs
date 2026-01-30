//! Braille-based heatmap rendering with true color

use ndarray::Array2;
use ratatui::{
    prelude::*,
    widgets::{
        canvas::{Canvas, Points},
        Block, Borders,
    },
};

use super::colormap::Colormap;

/// Render a Range-Doppler heatmap using Braille characters and true color
pub fn render_heatmap(
    frame: &mut Frame,
    area: Rect,
    rd_map: &Array2<f32>,
    colormap: Colormap,
    min_db: f32,
    max_db: f32,
    range_bounds: (f64, f64),
    doppler_bounds: (f64, f64),
    title: &str,
) {
    let (n_doppler, n_range) = rd_map.dim();
    let (min_range, max_range) = range_bounds;
    let (min_doppler, max_doppler) = doppler_bounds;

    // Create the canvas with Braille markers for high resolution
    let canvas = Canvas::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(title)
                .title_style(Style::default().fg(Color::White).bold()),
        )
        .marker(symbols::Marker::Braille)
        .x_bounds([min_range, max_range])
        .y_bounds([min_doppler, max_doppler])
        .background_color(colormap.background())
        .paint(|ctx| {
            // Iterate through the Range-Doppler map and draw each point
            // We sample the data to match the canvas resolution for performance
            let canvas_width = area.width.saturating_sub(2) as usize * 2; // Braille: 2 dots per char width
            let canvas_height = area.height.saturating_sub(2) as usize * 4; // Braille: 4 dots per char height

            // Calculate step sizes for sampling
            let range_step = (n_range as f32 / canvas_width as f32).max(1.0);
            let doppler_step = (n_doppler as f32 / canvas_height as f32).max(1.0);

            // Build points for each sampled location
            let mut r = 0.0;
            while (r as usize) < n_range {
                let r_idx = r as usize;
                let x = min_range + (r_idx as f64 / n_range as f64) * (max_range - min_range);

                let mut d = 0.0;
                while (d as usize) < n_doppler {
                    let d_idx = d as usize;
                    let y = min_doppler + (d_idx as f64 / n_doppler as f64) * (max_doppler - min_doppler);

                    // Get the dB value and normalize to 0-1
                    let val = rd_map[[d_idx, r_idx]];
                    let normalized = ((val - min_db) / (max_db - min_db)).clamp(0.0, 1.0);
                    let color = colormap.to_color(normalized);

                    // Draw the point
                    ctx.draw(&Points {
                        coords: &[(x, y)],
                        color,
                    });

                    d += doppler_step;
                }
                r += range_step;
            }
        });

    frame.render_widget(canvas, area);
}

/// Render axis labels around the heatmap
#[allow(dead_code)]
pub fn render_axis_labels(
    frame: &mut Frame,
    area: Rect,
    range_bounds: (f64, f64),
    doppler_bounds: (f64, f64),
) {
    let (min_range, max_range) = range_bounds;
    let (min_doppler, max_doppler) = doppler_bounds;

    // X-axis labels (Range)
    let x_label_area = Rect::new(area.x, area.bottom() - 1, area.width, 1);
    let x_label = Line::from(vec![
        Span::raw(format!("{:.0}", min_range)),
        Span::raw(" ".repeat(
            (area.width as usize).saturating_sub(20) / 2,
        )),
        Span::styled("Range (m)", Style::default().fg(Color::Yellow)),
        Span::raw(" ".repeat(
            (area.width as usize).saturating_sub(20) / 2,
        )),
        Span::raw(format!("{:.0}", max_range)),
    ]);
    frame.render_widget(x_label, x_label_area);

    // Y-axis label (Doppler) - rendered vertically on the left
    let doppler_labels = [
        format!("{:.0}", max_doppler),
        "Doppler".to_string(),
        "(Hz)".to_string(),
        format!("{:.0}", min_doppler),
    ];

    let label_spacing = area.height as usize / (doppler_labels.len() + 1);
    for (i, label) in doppler_labels.iter().enumerate() {
        let y_pos = area.y + (i + 1) as u16 * label_spacing as u16;
        if y_pos < area.bottom() {
            let label_area = Rect::new(area.x.saturating_sub(8), y_pos, 7, 1);
            frame.render_widget(
                Line::from(Span::styled(
                    format!("{:>7}", label),
                    Style::default().fg(Color::Yellow),
                )),
                label_area,
            );
        }
    }
}
