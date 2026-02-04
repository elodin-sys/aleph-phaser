//! Braille-based heatmap rendering with true color

use ndarray::Array2;
use ratatui::{
    prelude::*,
    widgets::{
        canvas::{Canvas, Points},
        Block, Borders, Paragraph,
    },
};

use super::colormap::Colormap;

/// Render a Range-Doppler heatmap using Braille characters and true color
#[allow(clippy::too_many_arguments)]
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
            // Calculate canvas resolution (Braille: 2 dots wide x 4 dots tall per char)
            let canvas_width = (area.width.saturating_sub(2) as usize * 2).max(1);
            let canvas_height = (area.height.saturating_sub(2) as usize * 4).max(1);

            // Use bilinear interpolation for smooth rendering when canvas resolution
            // exceeds data resolution (e.g., 30 range bins stretched to 400+ pixels)
            for cy in 0..canvas_height {
                // Calculate floating-point doppler index for interpolation
                let d_f = if canvas_height > 1 {
                    cy as f64 * (n_doppler - 1) as f64 / (canvas_height - 1) as f64
                } else {
                    0.0
                };

                // Get surrounding doppler indices
                let d0 = (d_f.floor() as usize).min(n_doppler - 1);
                let d1 = (d0 + 1).min(n_doppler - 1);
                let df = d_f - d0 as f64; // Fractional part for interpolation

                // Map to world Y coordinate
                let y = min_doppler + (d_f / (n_doppler - 1).max(1) as f64) * (max_doppler - min_doppler);

                for cx in 0..canvas_width {
                    // Calculate floating-point range index for interpolation
                    let r_f = if canvas_width > 1 {
                        cx as f64 * (n_range - 1) as f64 / (canvas_width - 1) as f64
                    } else {
                        0.0
                    };

                    // Get surrounding range indices
                    let r0 = (r_f.floor() as usize).min(n_range - 1);
                    let r1 = (r0 + 1).min(n_range - 1);
                    let rf = r_f - r0 as f64; // Fractional part for interpolation

                    // Map to world X coordinate
                    let x = min_range + (r_f / (n_range - 1).max(1) as f64) * (max_range - min_range);

                    // Bilinear interpolation: sample 4 surrounding values and blend
                    let v00 = rd_map[[d0, r0]] as f64;
                    let v01 = rd_map[[d0, r1]] as f64;
                    let v10 = rd_map[[d1, r0]] as f64;
                    let v11 = rd_map[[d1, r1]] as f64;

                    let val = (v00 * (1.0 - df) * (1.0 - rf)
                        + v01 * (1.0 - df) * rf
                        + v10 * df * (1.0 - rf)
                        + v11 * df * rf) as f32;

                    // Normalize to 0-1 and get color
                    let normalized = ((val - min_db) / (max_db - min_db)).clamp(0.0, 1.0);
                    let color = colormap.to_color(normalized);

                    // Draw the point
                    ctx.draw(&Points {
                        coords: &[(x, y)],
                        color,
                    });
                }
            }
        });

    frame.render_widget(canvas, area);
}

/// Render debug overlay showing coordinate info at corners
#[allow(clippy::too_many_arguments)]
pub fn render_debug_overlay(
    frame: &mut Frame,
    area: Rect,
    rd_map: &Array2<f32>,
    n_range: usize,
    n_doppler: usize,
    range_bounds: (f64, f64),
    doppler_bounds: (f64, f64),
) {
    let (min_range, max_range) = range_bounds;
    let (min_doppler, max_doppler) = doppler_bounds;

    // Inner area (excluding border)
    let inner = Rect::new(
        area.x + 1,
        area.y + 1,
        area.width.saturating_sub(2),
        area.height.saturating_sub(2),
    );

    // Get corner values from the rd_map
    let corners = [
        // (d_idx, r_idx, label, x_pos, y_pos)
        (0, 0, "BL", inner.x, inner.bottom().saturating_sub(1)),  // bottom-left
        (0, n_range.saturating_sub(1), "BR", inner.right().saturating_sub(20), inner.bottom().saturating_sub(1)),  // bottom-right
        (n_doppler.saturating_sub(1), 0, "TL", inner.x, inner.y),  // top-left
        (n_doppler.saturating_sub(1), n_range.saturating_sub(1), "TR", inner.right().saturating_sub(20), inner.y),  // top-right
    ];

    for (d_idx, r_idx, label, x_pos, y_pos) in corners {
        let val = if d_idx < rd_map.dim().0 && r_idx < rd_map.dim().1 {
            rd_map[[d_idx, r_idx]]
        } else {
            0.0
        };

        // Calculate physical coordinates
        let range_m = min_range + (r_idx as f64 / (n_range.saturating_sub(1).max(1)) as f64) * (max_range - min_range);
        let doppler_hz = min_doppler + (d_idx as f64 / (n_doppler.saturating_sub(1).max(1)) as f64) * (max_doppler - min_doppler);

        // Create overlay text
        let text = format!(
            "{}: [{},{}] v={:.1} r={:.1}m d={:.0}Hz",
            label, d_idx, r_idx, val, range_m, doppler_hz
        );

        let overlay_area = Rect::new(x_pos, y_pos, text.len() as u16 + 2, 1);
        if overlay_area.right() <= area.right() && overlay_area.bottom() <= area.bottom() {
            let overlay = Paragraph::new(text)
                .style(Style::default().fg(Color::White).bg(Color::Rgb(40, 40, 40)));
            frame.render_widget(overlay, overlay_area);
        }
    }

    // Also show dimensions info at center-top
    let dims_text = format!(" dims: {}x{} (DxR) ", n_doppler, n_range);
    let dims_x = area.x + (area.width.saturating_sub(dims_text.len() as u16)) / 2;
    let dims_area = Rect::new(dims_x, area.y + 2, dims_text.len() as u16, 1);
    let dims_overlay = Paragraph::new(dims_text)
        .style(Style::default().fg(Color::Cyan).bg(Color::Rgb(40, 40, 40)));
    frame.render_widget(dims_overlay, dims_area);

    // Show coordinate system info
    let coord_text = " rd_map[d,r]: d=Doppler(row), r=Range(col) ";
    let coord_x = area.x + (area.width.saturating_sub(coord_text.len() as u16)) / 2;
    let coord_area = Rect::new(coord_x, area.y + 3, coord_text.len() as u16, 1);
    let coord_overlay = Paragraph::new(coord_text)
        .style(Style::default().fg(Color::Yellow).bg(Color::Rgb(40, 40, 40)));
    frame.render_widget(coord_overlay, coord_area);
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
        Span::raw(" ".repeat((area.width as usize).saturating_sub(20) / 2)),
        Span::styled("Range (m)", Style::default().fg(Color::Yellow)),
        Span::raw(" ".repeat((area.width as usize).saturating_sub(20) / 2)),
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
