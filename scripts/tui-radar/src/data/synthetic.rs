//! Synthetic data generation for testing

use ndarray::Array2;
use num_complex::Complex;
use std::f32::consts::PI;

/// Synthetic radar data generator
pub struct SyntheticSource {
    n_range: usize,
    n_doppler: usize,
    frame: u64,
    /// Simulated targets: (range_bin, doppler_bin, amplitude_db, phase_rate)
    targets: Vec<(f32, f32, f32, f32)>,
}

impl SyntheticSource {
    /// Create a new synthetic data source
    pub fn new(n_range: usize, n_doppler: usize) -> Self {
        // Create some interesting simulated targets
        let targets = vec![
            // Stationary target at mid-range
            (n_range as f32 * 0.3, n_doppler as f32 * 0.5, -10.0, 0.0),
            // Moving target approaching
            (n_range as f32 * 0.5, n_doppler as f32 * 0.65, -15.0, 0.02),
            // Moving target receding
            (n_range as f32 * 0.7, n_doppler as f32 * 0.35, -12.0, -0.015),
            // Fast moving target (like drone)
            (n_range as f32 * 0.4, n_doppler as f32 * 0.8, -18.0, 0.05),
            // Close slow target
            (n_range as f32 * 0.15, n_doppler as f32 * 0.52, -8.0, 0.005),
        ];

        Self {
            n_range,
            n_doppler,
            frame: 0,
            targets,
        }
    }

    /// Generate a frame of synthetic radar data
    pub fn generate(&mut self) -> Array2<Complex<f32>> {
        let mut data = Array2::zeros((self.n_doppler, self.n_range));
        let noise_level = -50.0_f32; // dB
        let noise_amplitude = 10.0_f32.powf(noise_level / 20.0);

        // Add noise floor
        for d in 0..self.n_doppler {
            for r in 0..self.n_range {
                let noise_i = (rand_f32() - 0.5) * 2.0 * noise_amplitude;
                let noise_q = (rand_f32() - 0.5) * 2.0 * noise_amplitude;
                data[[d, r]] = Complex::new(noise_i, noise_q);
            }
        }

        // Add targets as spread Gaussian peaks with motion
        for (base_range, base_doppler, amp_db, phase_rate) in &self.targets {
            let amplitude = 10.0_f32.powf(*amp_db / 20.0);
            
            // Add motion over time
            let range_pos = *base_range + (self.frame as f32 * phase_rate * 5.0) % 20.0 - 10.0;
            let doppler_pos = *base_doppler + (self.frame as f32 * 0.01).sin() * 5.0;

            // Create a spread target (2D Gaussian)
            let range_sigma = 3.0;
            let doppler_sigma = 4.0;

            for d in 0..self.n_doppler {
                for r in 0..self.n_range {
                    let range_dist = (r as f32 - range_pos) / range_sigma;
                    let doppler_dist = (d as f32 - doppler_pos) / doppler_sigma;
                    let gauss = (-0.5 * (range_dist * range_dist + doppler_dist * doppler_dist)).exp();
                    
                    if gauss > 0.01 {
                        let phase = 2.0 * PI * rand_f32();
                        let signal = amplitude * gauss * Complex::new(phase.cos(), phase.sin());
                        data[[d, r]] += signal;
                    }
                }
            }
        }

        self.frame += 1;
        data
    }
}

/// Simple pseudo-random number generator (0.0 to 1.0)
fn rand_f32() -> f32 {
    use std::cell::Cell;
    thread_local! {
        static SEED: Cell<u64> = Cell::new(12345);
    }
    SEED.with(|seed| {
        let mut s = seed.get();
        s ^= s << 13;
        s ^= s >> 7;
        s ^= s << 17;
        seed.set(s);
        (s as f32) / (u64::MAX as f32)
    })
}
