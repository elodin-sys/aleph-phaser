//! Synthetic data generation for testing

use ndarray::Array2;
use std::f32::consts::PI;

/// Synthetic radar data generator
pub struct SyntheticSource {
    n_range: usize,
    n_doppler: usize,
    frame: u64,
    /// Simulated targets: (range_frac, doppler_frac, amplitude_db, velocity)
    targets: Vec<Target>,
    rng: Rng,
}

/// A synthetic radar target
struct Target {
    range_frac: f32,    // 0.0 to 1.0 position in range
    doppler_frac: f32,  // 0.0 to 1.0 position in doppler
    amplitude_db: f32,  // Signal strength in dB
    velocity: f32,      // Motion rate
    range_sigma: f32,   // Target spread in range
    doppler_sigma: f32, // Target spread in doppler
}

impl SyntheticSource {
    /// Create a new synthetic data source
    pub fn new(n_range: usize, n_doppler: usize) -> Self {
        // Create interesting simulated targets
        let targets = vec![
            // Stationary target at mid-range (like a building or parked car)
            Target {
                range_frac: 0.3,
                doppler_frac: 0.5,  // Zero Doppler (center)
                amplitude_db: -8.0,
                velocity: 0.0,
                range_sigma: 8.0,
                doppler_sigma: 6.0,
            },
            // Moving target approaching (car coming toward radar)
            Target {
                range_frac: 0.5,
                doppler_frac: 0.65,
                amplitude_db: -12.0,
                velocity: 0.3,
                range_sigma: 6.0,
                doppler_sigma: 8.0,
            },
            // Moving target receding (car going away)
            Target {
                range_frac: 0.7,
                doppler_frac: 0.35,
                amplitude_db: -10.0,
                velocity: -0.2,
                range_sigma: 7.0,
                doppler_sigma: 7.0,
            },
            // Fast moving target (drone or bird)
            Target {
                range_frac: 0.4,
                doppler_frac: 0.78,
                amplitude_db: -18.0,
                velocity: 0.8,
                range_sigma: 4.0,
                doppler_sigma: 10.0,
            },
            // Close slow target (person walking)
            Target {
                range_frac: 0.15,
                doppler_frac: 0.53,
                amplitude_db: -6.0,
                velocity: 0.05,
                range_sigma: 5.0,
                doppler_sigma: 12.0,
            },
            // Distant weak target
            Target {
                range_frac: 0.85,
                doppler_frac: 0.45,
                amplitude_db: -25.0,
                velocity: -0.1,
                range_sigma: 10.0,
                doppler_sigma: 5.0,
            },
        ];

        Self {
            n_range,
            n_doppler,
            frame: 0,
            targets,
            rng: Rng::new(42),
        }
    }

    /// Generate a Range-Doppler map directly (dB values)
    /// This bypasses FFT processing for clean synthetic visualization
    pub fn generate_rd_map(&mut self) -> Array2<f32> {
        let mut rd_map = Array2::zeros((self.n_doppler, self.n_range));

        // Add smooth noise floor
        let noise_floor_db = -50.0_f32;
        for d in 0..self.n_doppler {
            for r in 0..self.n_range {
                // Smooth Gaussian noise
                let noise_var = self.rng.next_gaussian() * 3.0;
                rd_map[[d, r]] = noise_floor_db + noise_var;
            }
        }

        // Add targets as smooth 2D Gaussian peaks
        let time = self.frame as f32 * 0.05;
        for target in &self.targets {
            // Animate target position smoothly
            let range_center = target.range_frac * self.n_range as f32
                + (time * target.velocity * 8.0).sin() * 20.0;
            let doppler_center = target.doppler_frac * self.n_doppler as f32
                + (time * 0.3 + target.velocity).sin() * 10.0;

            // Add smooth Gaussian blob
            for d in 0..self.n_doppler {
                for r in 0..self.n_range {
                    let range_dist = (r as f32 - range_center) / target.range_sigma;
                    let doppler_dist = (d as f32 - doppler_center) / target.doppler_sigma;
                    let dist_sq = range_dist * range_dist + doppler_dist * doppler_dist;
                    
                    if dist_sq < 25.0 {  // Only compute within 5 sigma
                        let gauss = (-0.5 * dist_sq).exp();
                        // Target amplitude scaled by Gaussian
                        let target_contribution = target.amplitude_db + 50.0; // Shift to positive
                        let contribution = target_contribution * gauss;
                        
                        // Soft maximum to combine with existing value
                        let existing = rd_map[[d, r]] + 50.0;
                        let combined = (existing.exp() + contribution.exp()).ln();
                        rd_map[[d, r]] = combined - 50.0;
                    }
                }
            }
        }

        // Normalize so max is 0 dB
        let max_val = rd_map.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        for val in rd_map.iter_mut() {
            *val -= max_val;
        }

        self.frame += 1;
        rd_map
    }
}

/// High-quality pseudo-random number generator (xoshiro256**)
struct Rng {
    state: [u64; 4],
}

impl Rng {
    fn new(seed: u64) -> Self {
        // Initialize state using SplitMix64
        let mut state = [0u64; 4];
        let mut x = seed;
        for s in state.iter_mut() {
            x = x.wrapping_add(0x9e3779b97f4a7c15);
            let mut z = x;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            *s = z ^ (z >> 31);
        }
        Self { state }
    }

    fn next_u64(&mut self) -> u64 {
        let result = self.state[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = self.state[1] << 17;

        self.state[2] ^= self.state[0];
        self.state[3] ^= self.state[1];
        self.state[1] ^= self.state[2];
        self.state[0] ^= self.state[3];

        self.state[2] ^= t;
        self.state[3] = self.state[3].rotate_left(45);

        result
    }

    /// Generate f32 in [0, 1)
    fn next_f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32
    }

    /// Generate Gaussian-distributed value using Box-Muller
    fn next_gaussian(&mut self) -> f32 {
        let u1 = self.next_f32().max(1e-10);
        let u2 = self.next_f32();
        (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
    }
}
