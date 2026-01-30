//! Spectrum display widgets

use ratatui::{
    prelude::*,
    widgets::{
        canvas::{Canvas, Line as CanvasLine, Points},
        Block, Borders,
    },
};

use super::colormap::Colormap;

/// Render a 1D spectrum plot
#[allow(clippy::too_many_arguments)]
pub fn render_spectrum(
    frame: &mut Frame,
    area: Rect,
    data: &[f32],
    colormap: Colormap,
    min_db: f32,
    max_db: f32,
    x_bounds: (f64, f64),
    title: &str,
    x_label: &str,
) {
    let (x_min, x_max) = x_bounds;
    let n = data.len();

    let canvas = Canvas::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(title)
                .title_style(Style::default().fg(Color::White).bold()),
        )
        .marker(symbols::Marker::Braille)
        .x_bounds([x_min, x_max])
        .y_bounds([min_db as f64, max_db as f64])
        .background_color(colormap.background())
        .paint(|ctx| {
            // Draw the spectrum as a filled area using points
            for (i, &val) in data.iter().enumerate() {
                let x = x_min + (i as f64 / n as f64) * (x_max - x_min);
                let y = val as f64;
                
                // Normalize for color
                let normalized = ((val - min_db) / (max_db - min_db)).clamp(0.0, 1.0);
                let color = colormap.to_color(normalized);

                // Draw a point at the spectrum value
                ctx.draw(&Points {
                    coords: &[(x, y)],
                    color,
                });

                // Fill down to the minimum to create a filled effect
                let fill_steps = 5;
                for step in 1..=fill_steps {
                    let fill_y = min_db as f64 + (y - min_db as f64) * (1.0 - step as f64 / fill_steps as f64);
                    let fill_normalized = ((fill_y as f32 - min_db) / (max_db - min_db)).clamp(0.0, 1.0);
                    let fill_color = colormap.to_color(fill_normalized * 0.5); // Dimmer fill
                    ctx.draw(&Points {
                        coords: &[(x, fill_y)],
                        color: fill_color,
                    });
                }
            }

            // Draw horizontal grid lines
            let grid_color = Color::Rgb(60, 60, 60);
            for db in [-60, -40, -20, 0].iter() {
                if (*db as f32) >= min_db && (*db as f32) <= max_db {
                    ctx.draw(&CanvasLine {
                        x1: x_min,
                        y1: *db as f64,
                        x2: x_max,
                        y2: *db as f64,
                        color: grid_color,
                    });
                }
            }
        });

    frame.render_widget(canvas, area);

    // Render axis labels
    let bottom_area = Rect::new(area.x + 1, area.bottom() - 1, area.width - 2, 1);
    let label_line = Line::from(vec![
        Span::raw(format!("{:.0}", x_min)),
        Span::raw(" ".repeat((area.width as usize).saturating_sub(x_label.len() + 16) / 2)),
        Span::styled(x_label, Style::default().fg(Color::Yellow)),
        Span::raw(" ".repeat((area.width as usize).saturating_sub(x_label.len() + 16) / 2)),
        Span::raw(format!("{:.0}", x_max)),
    ]);
    frame.render_widget(label_line, bottom_area);
}

/// Render a color scale legend
pub fn render_color_scale(
    frame: &mut Frame,
    area: Rect,
    colormap: Colormap,
    min_db: f32,
    max_db: f32,
) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title("Power (dB)")
        .title_style(Style::default().fg(Color::White).bold());
    let inner = block.inner(area);
    frame.render_widget(block, area);

    // Draw the color gradient
    let gradient_width = inner.width.saturating_sub(8);
    if gradient_width > 0 {
        let gradient_area = Rect::new(inner.x + 4, inner.y, gradient_width, 1);
        
        let mut spans = Vec::new();
        for i in 0..gradient_width as usize {
            let normalized = i as f32 / gradient_width as f32;
            let color = colormap.to_color(normalized);
            spans.push(Span::styled("█", Style::default().fg(color)));
        }
        frame.render_widget(Line::from(spans), gradient_area);

        // Labels
        let label_area = Rect::new(inner.x, inner.y + 1, inner.width, 1);
        let label_line = Line::from(vec![
            Span::raw(format!("{:.0}dB", min_db)),
            Span::raw(" ".repeat((inner.width as usize).saturating_sub(16) / 2)),
            Span::styled(colormap.name(), Style::default().fg(Color::Cyan)),
            Span::raw(" ".repeat((inner.width as usize).saturating_sub(16) / 2)),
            Span::raw(format!("{:.0}dB", max_db)),
        ]);
        frame.render_widget(label_line, label_area);
    }
}
