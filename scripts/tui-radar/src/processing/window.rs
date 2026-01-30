//! Window functions for signal processing

use ndarray::{Array1, Array2};
use std::f32::consts::PI;

/// Window function types
#[derive(Debug, Clone, Copy)]
#[allow(dead_code)]
pub enum Window {
    Rectangular,
    Hanning,
    Hamming,
    Blackman,
    BlackmanHarris,
}

impl Window {
    /// Generate a 1D window of the specified length
    pub fn generate(&self, n: usize) -> Array1<f32> {
        let mut window = Array1::zeros(n);
        let n_f = n as f32;

        for i in 0..n {
            let x = i as f32 / (n_f - 1.0);
            window[i] = match self {
                Window::Rectangular => 1.0,
                Window::Hanning => 0.5 * (1.0 - (2.0 * PI * x).cos()),
                Window::Hamming => 0.54 - 0.46 * (2.0 * PI * x).cos(),
                Window::Blackman => {
                    0.42 - 0.5 * (2.0 * PI * x).cos() + 0.08 * (4.0 * PI * x).cos()
                }
                Window::BlackmanHarris => {
                    0.35875
                        - 0.48829 * (2.0 * PI * x).cos()
                        + 0.14128 * (4.0 * PI * x).cos()
                        - 0.01168 * (6.0 * PI * x).cos()
                }
            };
        }
        window
    }
}

/// Generate a 2D Blackman window
pub fn blackman_2d(n_rows: usize, n_cols: usize) -> Array2<f32> {
    let row_window = Window::Blackman.generate(n_rows);
    let col_window = Window::Blackman.generate(n_cols);

    let mut window_2d = Array2::zeros((n_rows, n_cols));
    for i in 0..n_rows {
        for j in 0..n_cols {
            window_2d[[i, j]] = row_window[i] * col_window[j];
        }
    }
    window_2d
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_blackman_window() {
        let window = Window::Blackman.generate(64);
        assert_eq!(window.len(), 64);
        // Blackman window should be symmetric and peak in the middle
        assert!(window[32] > window[0]);
        assert!((window[0] - window[63]).abs() < 0.01);
    }

    #[test]
    fn test_blackman_2d() {
        let window = blackman_2d(32, 64);
        assert_eq!(window.dim(), (32, 64));
    }
}
