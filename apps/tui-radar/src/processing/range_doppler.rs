//! Range-Doppler map processing

use ndarray::Array2;
use num_complex::Complex;
use std::f32::consts::PI;

use super::window::blackman_2d;

/// Range-Doppler processor
pub struct RangeDopplerProcessor {
    n_range: usize,
    n_doppler: usize,
    window: Array2<f32>,
    previous_frame: Option<Array2<Complex<f32>>>,
}

impl RangeDopplerProcessor {
    /// Create a new Range-Doppler processor
    pub fn new(n_range: usize, n_doppler: usize) -> Self {
        let window = blackman_2d(n_doppler, n_range);
        Self {
            n_range,
            n_doppler,
            window,
            previous_frame: None,
        }
    }

    /// Process raw IQ data into a Range-Doppler map (dB)
    pub fn process(&mut self, data: &Array2<Complex<f32>>, mti: bool) -> Array2<f32> {
        let mut data_to_process = data.clone();

        // Apply MTI (2-pulse canceller) if enabled
        if mti {
            if let Some(ref prev) = self.previous_frame {
                for d in 0..self.n_doppler {
                    for r in 0..self.n_range {
                        data_to_process[[d, r]] = data[[d, r]] - prev[[d, r]];
                    }
                }
            }
            self.previous_frame = Some(data.clone());
        }

        // Apply 2D window
        let mut windowed = Array2::zeros((self.n_doppler, self.n_range));
        for d in 0..self.n_doppler {
            for r in 0..self.n_range {
                windowed[[d, r]] = data_to_process[[d, r]] * self.window[[d, r]];
            }
        }

        // 2D FFT (CPU implementation)
        let fft_result = self.fft_2d(&windowed);

        // FFT shift
        let shifted = self.fft_shift(&fft_result);

        // Convert to magnitude in dB
        let mut rd_map = Array2::zeros((self.n_doppler, self.n_range));
        for d in 0..self.n_doppler {
            for r in 0..self.n_range {
                let mag = shifted[[d, r]].norm();
                let db = 20.0 * (mag.max(1e-12)).log10();
                rd_map[[d, r]] = db;
            }
        }

        // Normalize to 0 dB max
        let max_val = rd_map.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        for val in rd_map.iter_mut() {
            *val -= max_val;
        }

        rd_map
    }

    /// Perform 2D FFT using row-column decomposition
    fn fft_2d(&self, data: &Array2<Complex<f32>>) -> Array2<Complex<f32>> {
        let (n_rows, n_cols) = data.dim();
        let mut result = data.clone();

        // FFT along rows (range)
        for row in 0..n_rows {
            let row_data: Vec<Complex<f32>> = (0..n_cols).map(|c| result[[row, c]]).collect();
            let fft_row = self.fft_1d(&row_data);
            for (c, val) in fft_row.iter().enumerate() {
                result[[row, c]] = *val;
            }
        }

        // FFT along columns (Doppler)
        for col in 0..n_cols {
            let col_data: Vec<Complex<f32>> = (0..n_rows).map(|r| result[[r, col]]).collect();
            let fft_col = self.fft_1d(&col_data);
            for (r, val) in fft_col.iter().enumerate() {
                result[[r, col]] = *val;
            }
        }

        result
    }

    /// Cooley-Tukey FFT (radix-2 DIT)
    fn fft_1d(&self, input: &[Complex<f32>]) -> Vec<Complex<f32>> {
        let n = input.len();
        if n <= 1 {
            return input.to_vec();
        }

        // Pad to next power of 2 if necessary
        let n_padded = n.next_power_of_two();
        let mut data: Vec<Complex<f32>> = input.to_vec();
        data.resize(n_padded, Complex::new(0.0, 0.0));

        // Bit-reversal permutation
        let mut j = 0;
        for i in 0..n_padded {
            if i < j {
                data.swap(i, j);
            }
            let mut m = n_padded / 2;
            while m >= 1 && j >= m {
                j -= m;
                m /= 2;
            }
            j += m;
        }

        // Cooley-Tukey iterative FFT
        let mut len = 2;
        while len <= n_padded {
            let half_len = len / 2;
            let angle = -2.0 * PI / len as f32;
            let wn = Complex::new(angle.cos(), angle.sin());

            for start in (0..n_padded).step_by(len) {
                let mut w = Complex::new(1.0, 0.0);
                for k in 0..half_len {
                    let u = data[start + k];
                    let t = w * data[start + k + half_len];
                    data[start + k] = u + t;
                    data[start + k + half_len] = u - t;
                    w *= wn;
                }
            }
            len *= 2;
        }

        // Return original size
        data.truncate(n);
        data
    }

    /// FFT shift (move zero frequency to center)
    fn fft_shift(&self, data: &Array2<Complex<f32>>) -> Array2<Complex<f32>> {
        let (n_rows, n_cols) = data.dim();
        let mut shifted = Array2::zeros((n_rows, n_cols));

        let row_shift = n_rows / 2;
        let col_shift = n_cols / 2;

        for r in 0..n_rows {
            for c in 0..n_cols {
                let new_r = (r + row_shift) % n_rows;
                let new_c = (c + col_shift) % n_cols;
                shifted[[new_r, new_c]] = data[[r, c]];
            }
        }

        shifted
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fft_1d() {
        let processor = RangeDopplerProcessor::new(64, 64);
        let input: Vec<Complex<f32>> = (0..8)
            .map(|i| Complex::new(i as f32, 0.0))
            .collect();
        let result = processor.fft_1d(&input);
        assert_eq!(result.len(), 8);
    }

    #[test]
    fn test_process() {
        let mut processor = RangeDopplerProcessor::new(64, 64);
        let data = Array2::from_elem((64, 64), Complex::new(1.0, 0.0));
        let rd_map = processor.process(&data, false);
        assert_eq!(rd_map.dim(), (64, 64));
    }
}
