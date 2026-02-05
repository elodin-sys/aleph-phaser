//! Colormap definitions for radar visualization.

/// Available colormaps.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Colormap {
    /// Matplotlib inferno colormap (perceptually uniform).
    Inferno,
    /// Matplotlib plasma colormap.
    Plasma,
    /// Matplotlib viridis colormap.
    Viridis,
    /// Hot (black-red-yellow-white).
    Hot,
    /// Grayscale.
    Grayscale,
}

impl Colormap {
    /// Generate a 256-entry RGBA lookup table.
    pub fn generate_lut(&self) -> Vec<u8> {
        let mut lut = Vec::with_capacity(256 * 4);

        for i in 0..256 {
            let t = i as f32 / 255.0;
            let (r, g, b) = match self {
                Colormap::Inferno => inferno(t),
                Colormap::Plasma => plasma(t),
                Colormap::Viridis => viridis(t),
                Colormap::Hot => hot(t),
                Colormap::Grayscale => (t, t, t),
            };

            lut.push((r * 255.0) as u8);
            lut.push((g * 255.0) as u8);
            lut.push((b * 255.0) as u8);
            lut.push(255); // Alpha
        }

        lut
    }
}

/// Inferno colormap (approximation).
fn inferno(t: f32) -> (f32, f32, f32) {
    // Accurate inferno using polynomial approximation
    let r = -0.0067 + t * (1.7133 + t * (-1.5708 + t * 0.8639));
    let g = -0.0087 + t * (-0.0459 + t * (2.3707 + t * (-2.2877 + t * 0.9692)));
    let b = 0.0175 + t * (2.2903 + t * (-4.7339 + t * (3.4647 - t * 1.0386)));

    (r.clamp(0.0, 1.0), g.clamp(0.0, 1.0), b.clamp(0.0, 1.0))
}

/// Plasma colormap (approximation).
fn plasma(t: f32) -> (f32, f32, f32) {
    let r = 0.0504 + t * (2.0268 + t * (-1.6618 + t * 0.5825));
    let g = -0.0307 + t * (0.3285 + t * (1.5456 + t * (-1.7829 + t * 0.9416)));
    let b = 0.5298 + t * (1.4139 + t * (-3.0191 + t * (2.1096 - t * 0.5227)));

    (r.clamp(0.0, 1.0), g.clamp(0.0, 1.0), b.clamp(0.0, 1.0))
}

/// Viridis colormap (approximation).
fn viridis(t: f32) -> (f32, f32, f32) {
    let r = 0.2670 + t * (0.0047 + t * (1.5077 + t * (-2.0037 + t * 1.2256)));
    let g = 0.0041 + t * (1.3734 + t * (-0.7177 + t * 0.3391));
    let b = 0.3293 + t * (1.5693 + t * (-3.1299 + t * (2.4184 - t * 0.6876)));

    (r.clamp(0.0, 1.0), g.clamp(0.0, 1.0), b.clamp(0.0, 1.0))
}

/// Hot colormap.
fn hot(t: f32) -> (f32, f32, f32) {
    let r = (t * 3.0).min(1.0);
    let g = ((t - 0.333) * 3.0).clamp(0.0, 1.0);
    let b = ((t - 0.666) * 3.0).clamp(0.0, 1.0);

    (r, g, b)
}
