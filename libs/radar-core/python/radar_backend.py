"""
Radar Backend for TUI Application

This module provides a unified interface for radar data acquisition and processing,
supporting both hardware (Phaser/PlutoSDR) and synthetic modes. All processing
uses GPU acceleration via CuPy when available.

The interface is designed for PyO3 integration with the Rust TUI application.
"""

import numpy as np
import sys
import time
from typing import Dict, Optional, Tuple


# ============================================================================
# GPU ACCELERATION SETUP
# ============================================================================
GPU_AVAILABLE = False
try:
    import cupy as cp
    # Test that CUDA is actually working
    _test = cp.array([1, 2, 3])
    _test_result = cp.sum(_test)
    del _test, _test_result
    GPU_AVAILABLE = True
    xp = cp
    print("RadarBackend: GPU acceleration ENABLED (CuPy/CUDA)")
    sys.stdout.flush()
except ImportError:
    xp = np
    print("RadarBackend: GPU acceleration DISABLED (CuPy not installed, using NumPy)")
    sys.stdout.flush()
except Exception as e:
    xp = np
    print(f"RadarBackend: GPU acceleration DISABLED (CUDA error: {e})")
    sys.stdout.flush()


def to_gpu(data):
    """Transfer data to GPU if available."""
    if GPU_AVAILABLE and isinstance(data, np.ndarray):
        return cp.asarray(data)
    return data


def to_cpu(data):
    """Transfer data from GPU to CPU."""
    if GPU_AVAILABLE and hasattr(data, 'get'):
        return data.get()
    return data if isinstance(data, np.ndarray) else np.array(data)


def get_gpu_status() -> Dict:
    """Return GPU acceleration status for logging from Rust."""
    return {
        "gpu_available": GPU_AVAILABLE,
        "backend": "cupy" if GPU_AVAILABLE else "numpy",
    }


# ============================================================================
# RADAR BACKEND CLASS
# ============================================================================
class RadarBackend:
    """
    Unified radar backend for TUI - handles both hardware and synthetic modes.
    
    Provides a single `get_frame()` method that returns processed Range-Doppler
    maps regardless of the data source.
    """

    def __init__(
        self,
        mode: str,
        sdr_uri: str = "ip:192.168.2.1",
        phaser_uri: str = "ip:192.168.4.184",
        sample_rate: int = 4_000_000,
        num_chirps: int = 512,
        ramp_time_us: int = 500,
        chirp_bw: float = 500_000_000,
        center_freq: int = 2_100_000_000,
        output_freq: int = 9_900_000_000,
        rx_gain: int = 30,
        signal_freq: float = 100_000,
        max_range: float = 10.0,
    ):
        """
        Initialize the radar backend.
        
        Args:
            mode: 'hardware' or 'synthetic'
            sdr_uri: PlutoSDR URI (for hardware mode)
            phaser_uri: Phaser/Raspberry Pi URI (for hardware mode)
            sample_rate: ADC sample rate in Hz
            num_chirps: Number of chirps (Doppler bins)
            ramp_time_us: Chirp ramp time in microseconds
            chirp_bw: Chirp bandwidth in Hz
            center_freq: SDR center frequency in Hz
            output_freq: Phaser output frequency in Hz
            rx_gain: Receive gain in dB
            signal_freq: Signal/IF frequency in Hz
            max_range: Maximum display range in meters
        """
        self.mode = mode
        self.sdr_uri = sdr_uri
        self.phaser_uri = phaser_uri
        
        # Store configuration
        self.sample_rate = sample_rate
        self.num_chirps = num_chirps
        self.ramp_time_us = ramp_time_us
        self.chirp_bw = chirp_bw
        self.center_freq = center_freq
        self.output_freq = output_freq
        self.rx_gain = rx_gain
        self.signal_freq = signal_freq
        self.max_range = max_range
        
        # Calculate derived parameters (matching Jon's script exactly)
        self.ramp_time_s = ramp_time_us / 1e6
        self.begin_offset_time = 0.1 * self.ramp_time_s
        self.good_ramp_samples = int((self.ramp_time_s - self.begin_offset_time) * sample_rate)
        self.pri_ms = ramp_time_us / 1000 + 0.2
        self.n_frame = int(self.pri_ms / 1000 * sample_rate)
        
        # Calculate FMCW range axis (matching Jon's script)
        # freq = linspace(-sample_rate/2, sample_rate/2, n_samples)
        # dist = (freq - signal_freq) * c / (2 * slope)
        c = 3e8  # speed of light
        slope = chirp_bw / self.ramp_time_s
        freq_axis = np.fft.fftshift(np.fft.fftfreq(self.good_ramp_samples, 1/sample_rate))
        self.range_axis = (freq_axis - signal_freq) * c / (2 * slope)
        
        # Find indices for 0m to max_range (the displayable region)
        self.range_start_idx = int(np.argmin(np.abs(self.range_axis - 0)))
        self.range_end_idx = int(np.argmin(np.abs(self.range_axis - max_range)))
        
        # Ensure we have at least some range bins
        if self.range_end_idx <= self.range_start_idx:
            self.range_end_idx = self.range_start_idx + 50  # fallback
        
        # Output dimensions (sliced to displayable range)
        self.n_doppler = num_chirps
        self.n_range_full = self.good_ramp_samples  # full FFT size
        self.n_range = self.range_end_idx - self.range_start_idx  # displayed range bins
        
        print(f"Range axis: full={self.n_range_full} bins, display={self.n_range} bins (idx {self.range_start_idx}-{self.range_end_idx})")
        
        # MTI filter state
        self.mti_enabled = False
        self.previous_frame = None
        
        # Display scaling (matching Jon's imshow vmin/vmax, not clip range)
        # Jon clips to [0, 50] but displays with vmax=8
        # Our data typically ranges from ~0.3 to ~7.6 in log10 scale
        self.min_scale = 0
        self.max_scale = 8
        
        # Hardware objects (initialized in _init_hardware)
        self.sdr = None
        self.phaser = None
        self.tdd = None
        self.sdr_pins = None
        self._hardware_initialized = False
        self._gpu_status_logged = False
        self._last_raw_data = None
        self._last_rx_bursts = None
        # Pre-allocated GPU buffer for rx_bursts (reused each frame to avoid allocator churn)
        self._gpu_rx_buf = None
        
        # Synthetic state
        self._frame_count = 0
        self._synthetic_targets = None
        
        # Initialize based on mode
        if mode == 'hardware':
            self._init_hardware()
        else:
            self._init_synthetic()
        
        print(f"RadarBackend initialized: mode={mode}, n_doppler={self.n_doppler}, n_range={self.n_range}")

    def _init_hardware(self):
        """Initialize hardware connections and configuration."""
        try:
            import adi
            
            # Connect to devices
            self.sdr = adi.ad9361(uri=self.sdr_uri)
            self.phaser = adi.CN0566(uri=self.phaser_uri, sdr=self.sdr)
            self.tdd = adi.tddn(self.sdr_uri)
            self.sdr_pins = adi.one_bit_adc_dac(self.sdr_uri)
            
            # Configure Phaser
            self.phaser.configure(device_mode="rx")
            self.phaser.element_spacing = 0.014
            self.phaser.load_gain_cal()
            self.phaser.load_phase_cal()
            
            # Set all channels to max gain
            for i in range(8):
                self.phaser.set_chan_phase(i, 0)
                self.phaser.set_chan_gain(i, 127, apply_cal=True)
            
            # Configure GPIOs
            self.phaser._gpios.gpio_tx_sw = 0
            self.phaser._gpios.gpio_vctrl_1 = 1
            self.phaser._gpios.gpio_vctrl_2 = 1
            
            # Configure SDR Rx
            self.sdr.sample_rate = int(self.sample_rate)
            self.sdr.rx_lo = int(self.center_freq)
            self.sdr.rx_enabled_channels = [0, 1]
            self.sdr.gain_control_mode_chan0 = 'manual'
            self.sdr.gain_control_mode_chan1 = 'manual'
            self.sdr.rx_hardwaregain_chan0 = int(self.rx_gain)
            self.sdr.rx_hardwaregain_chan1 = int(self.rx_gain)
            
            # Configure SDR Tx
            self.sdr.tx_lo = int(self.center_freq)
            self.sdr.tx_enabled_channels = [0, 1]
            self.sdr.tx_cyclic_buffer = True
            self.sdr.tx_hardwaregain_chan0 = -88
            self.sdr.tx_hardwaregain_chan1 = 0
            
            # Configure ADF4159 (ramping PLL)
            vco_freq = int(self.output_freq + self.signal_freq + self.center_freq)
            num_steps = int(self.ramp_time_us)
            
            self.phaser.frequency = int(vco_freq / 4)
            self.phaser.freq_dev_range = int(self.chirp_bw / 4)
            self.phaser.freq_dev_step = int((self.chirp_bw / 4) / num_steps)
            self.phaser.freq_dev_time = int(self.ramp_time_us)
            self.phaser.delay_word = 4095
            self.phaser.delay_clk = "PFD"
            self.phaser.delay_start_en = 0
            self.phaser.ramp_delay_en = 0
            self.phaser.trig_delay_en = 0
            self.phaser.ramp_mode = "single_sawtooth_burst"
            self.phaser.sing_ful_tri = 0
            self.phaser.tx_trig_en = 1
            self.phaser.enable = 0
            
            # Configure TDD
            self.sdr_pins.gpio_tdd_ext_sync = True
            self.sdr_pins.gpio_phaser_enable = True
            self.tdd.enable = False
            self.tdd.sync_external = True
            self.tdd.startup_delay_ms = 0
            self.tdd.frame_length_ms = self.pri_ms
            self.tdd.burst_count = self.num_chirps
            
            for ch in range(3):
                self.tdd.channel[ch].enable = True
                self.tdd.channel[ch].polarity = False
                self.tdd.channel[ch].on_raw = 0
                self.tdd.channel[ch].off_raw = 10
            
            self.tdd.enable = True
            
            # Calculate and set buffer size
            total_time_ms = self.pri_ms * self.num_chirps
            buffer_size = 2 ** int(np.ceil(np.log2(total_time_ms / 1000 * self.sample_rate)))
            buffer_size = min(buffer_size, 2**22)
            self.sdr.rx_buffer_size = buffer_size
            self.buffer_size = buffer_size
            # No stale DMA buffers: single kernel buffer for lowest latency (see beamforming-example, aleph_minimal_example)
            self.sdr._rxadc.set_kernel_buffers_count(1)
            buffer_time_ms = buffer_size / self.sample_rate * 1000
            print(
                f"RadarBackend: buffer_size={buffer_size} total_time_ms={total_time_ms:.1f} buffer_time_ms={buffer_time_ms:.1f}",
                flush=True,
            )
            
            # Calculate start offset
            self.start_offset_time = self.tdd.channel[0].on_ms / 1e3 + self.begin_offset_time
            self.start_offset_samples = int(self.start_offset_time * self.sample_rate)
            
            # Create and transmit waveform
            N = 2**18
            fc = int(self.signal_freq)
            ts = 1 / float(self.sample_rate)
            t = np.arange(0, N * ts, ts)
            i = np.cos(2 * np.pi * t * fc) * 2**14
            q = np.sin(2 * np.pi * t * fc) * 2**14
            iq = 0.9 * (i + 1j * q)
            self.sdr.tx([iq, iq])
            # Note: warmup rx() is not possible in TDD burst mode because rx() blocks until
            # a GPIO burst trigger fires. With set_kernel_buffers_count(1), stale buffers are
            # already eliminated so a warmup is unnecessary.
            
            self._hardware_initialized = True
            print("RadarBackend: Hardware initialized successfully")
            
        except ImportError as e:
            raise RuntimeError(
                f"Hardware mode requires pyadi-iio. Import failed: {e}\n"
                "Install with: pip install pyadi-iio\n"
                "Or use --synthetic flag for testing without hardware."
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Hardware initialization failed: {e}\n"
                f"  SDR URI: {self.sdr_uri}\n"
                f"  Phaser URI: {self.phaser_uri}\n"
                "Use --synthetic flag to run without hardware."
            ) from e

    def _init_synthetic(self):
        """Initialize synthetic data generator state."""
        self._frame_count = 0
        
        # Test pattern mode (None = use animated targets)
        # Valid patterns: 'animated', 'corner_dots', 'gradient_h', 'gradient_v', 
        #                 'center_target', 'grid', 'diagonal', 'checkerboard',
        #                 'hb100_stationary', 'hb100_walking', 'dc_leakage'
        self._test_pattern = 'animated'
        
        # Available patterns for cycling
        self._available_patterns = [
            'animated', 'corner_dots', 'gradient_h', 'gradient_v',
            'center_target', 'grid', 'diagonal', 'checkerboard',
            'hb100_stationary', 'hb100_walking', 'dc_leakage'
        ]
        
        # Create interesting simulated targets for 'animated' pattern
        # Each target: (range_frac, doppler_frac, amplitude_db, velocity, range_sigma, doppler_sigma)
        self._synthetic_targets = [
            # Stationary target at mid-range (like a building)
            {'range_frac': 0.3, 'doppler_frac': 0.5, 'amp_db': -8, 'velocity': 0.0,
             'range_sigma': 15, 'doppler_sigma': 10},
            # Moving target approaching (car coming toward radar)
            {'range_frac': 0.5, 'doppler_frac': 0.65, 'amp_db': -12, 'velocity': 0.3,
             'range_sigma': 12, 'doppler_sigma': 15},
            # Moving target receding (car going away)
            {'range_frac': 0.7, 'doppler_frac': 0.35, 'amp_db': -10, 'velocity': -0.2,
             'range_sigma': 14, 'doppler_sigma': 12},
            # Fast moving target (drone or bird)
            {'range_frac': 0.4, 'doppler_frac': 0.78, 'amp_db': -18, 'velocity': 0.8,
             'range_sigma': 8, 'doppler_sigma': 20},
            # Close slow target (person walking)
            {'range_frac': 0.15, 'doppler_frac': 0.53, 'amp_db': -6, 'velocity': 0.05,
             'range_sigma': 10, 'doppler_sigma': 18},
        ]
        
        # Pre-allocate random state for reproducible noise
        self._rng = np.random.default_rng(42)
        
        print("RadarBackend: Synthetic mode initialized")

    def set_mti(self, enabled: bool):
        """Enable or disable MTI filter."""
        self.mti_enabled = enabled
        if not enabled:
            self.previous_frame = None

    def set_test_pattern(self, pattern: str):
        """Set the test pattern for synthetic mode.
        
        Args:
            pattern: One of 'animated', 'corner_dots', 'gradient_h', 'gradient_v',
                    'center_target', 'grid', 'diagonal', 'checkerboard',
                    'hb100_stationary', 'hb100_walking', 'dc_leakage'
        """
        if pattern not in self._available_patterns:
            raise ValueError(f"Unknown pattern '{pattern}'. Available: {self._available_patterns}")
        self._test_pattern = pattern
        print(f"RadarBackend: Test pattern set to '{pattern}'")

    def get_test_pattern(self) -> str:
        """Get the current test pattern name."""
        return self._test_pattern

    def get_available_patterns(self) -> list:
        """Get list of available test patterns."""
        return self._available_patterns.copy()

    def cycle_test_pattern(self) -> str:
        """Cycle to the next test pattern and return its name."""
        current_idx = self._available_patterns.index(self._test_pattern)
        next_idx = (current_idx + 1) % len(self._available_patterns)
        self._test_pattern = self._available_patterns[next_idx]
        print(f"RadarBackend: Test pattern cycled to '{self._test_pattern}'")
        return self._test_pattern

    def get_frame(self) -> np.ndarray:
        """
        Capture and process one frame.
        
        Returns:
            2D numpy array of dB values, shape (n_doppler, n_range).
            Values are normalized so max = 0 dB.
        """
        if self.mode == 'hardware':
            return self._get_hardware_frame()
        else:
            return self._get_synthetic_frame()

    def _get_hardware_frame(self) -> np.ndarray:
        """Capture and process a frame from hardware."""
        if not self._hardware_initialized:
            raise RuntimeError("Hardware not initialized")
        
        # Trigger burst (matching Jon's script)
        self.phaser._gpios.gpio_burst = 0
        self.phaser._gpios.gpio_burst = 1
        self.phaser._gpios.gpio_burst = 0
        
        # Capture data
        data = self.sdr.rx()
        chan1 = data[0]
        chan2 = data[1]
        sum_data = chan1 + chan2
        
        # Store raw data for diagnostics
        self._last_raw_data = sum_data
        
        # Reshape into chirps (vectorized)
        start_indices = self.start_offset_samples + np.arange(self.num_chirps) * self.n_frame
        offsets = start_indices[:, np.newaxis] + np.arange(self.good_ramp_samples)
        rx_bursts = sum_data[offsets].copy()
        
        # Store reshaped data for diagnostics
        self._last_rx_bursts = rx_bursts
        
        # Apply MTI filter if enabled
        if self.mti_enabled:
            rx_bursts = self._apply_mti(rx_bursts)
        
        # Process to Range-Doppler map
        rd_map = self._process_to_rd_map(rx_bursts)
        
        return rd_map
    
    def get_raw_diagnostics(self) -> dict:
        """Get raw signal diagnostics from last capture."""
        if not hasattr(self, '_last_raw_data') or self._last_raw_data is None:
            return None
        
        raw = self._last_raw_data
        bursts = self._last_rx_bursts if hasattr(self, '_last_rx_bursts') else None
        
        diag = {
            'raw_len': len(raw),
            'raw_dtype': str(raw.dtype),
            'raw_abs_min': float(np.abs(raw).min()),
            'raw_abs_max': float(np.abs(raw).max()),
            'raw_abs_mean': float(np.abs(raw).mean()),
            'raw_power_db': float(10 * np.log10(np.mean(np.abs(raw)**2) + 1e-12)),
        }
        
        if bursts is not None:
            # FFT magnitude stats (before log)
            fft_mag = np.abs(np.fft.fft2(bursts))
            diag['fft_mag_min'] = float(fft_mag.min())
            diag['fft_mag_max'] = float(fft_mag.max())
            diag['fft_mag_mean'] = float(fft_mag.mean())
            diag['fft_log10_min'] = float(np.log10(fft_mag.max() + 1e-12))
            diag['fft_log10_max'] = float(np.log10(fft_mag.min() + 1e-12))
            
            # Check for signal vs noise
            diag['bursts_shape'] = bursts.shape
            diag['burst0_power_db'] = float(10 * np.log10(np.mean(np.abs(bursts[0])**2) + 1e-12))
        
        return diag

    def _get_synthetic_frame(self) -> np.ndarray:
        """Generate a synthetic Range-Doppler frame.
        
        Returns values in log10 scale matching hardware output.
        Values range from min_scale to max_scale (default 0 to 8).
        
        If a test pattern is set, generates that pattern instead of animated targets.
        """
        if self._test_pattern != 'animated':
            return self._get_test_pattern_frame()
        
        return self._get_animated_frame()

    def _get_animated_frame(self) -> np.ndarray:
        """Generate an animated frame with moving targets."""
        # Use log10 scale to match hardware output (not dB!)
        # Noise floor around 1-2 in log10 scale (10^1 to 10^2 magnitude)
        noise_floor = 1.5
        rd_map = np.full((self.n_doppler, self.n_range), noise_floor, dtype=np.float32)
        
        # Add smooth noise variation
        noise = self._rng.standard_normal((self.n_doppler, self.n_range)).astype(np.float32) * 0.3
        rd_map += noise
        
        # Animate time
        t = self._frame_count * 0.05
        
        # Add targets as smooth 2D Gaussian peaks
        for target in self._synthetic_targets:
            # Animate target position
            range_center = target['range_frac'] * self.n_range + np.sin(t * target['velocity'] * 8) * 30
            doppler_center = target['doppler_frac'] * self.n_doppler + np.sin(t * 0.3 + target['velocity']) * 15
            
            # Create coordinate grids
            r_idx = np.arange(self.n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            # Gaussian blob
            range_dist = (R - range_center) / target['range_sigma']
            doppler_dist = (D - doppler_center) / target['doppler_sigma']
            dist_sq = range_dist**2 + doppler_dist**2
            
            gauss = np.exp(-0.5 * dist_sq)
            # Target peaks: log10 scale, so 7 = strong target (10^7 magnitude)
            # Convert from dB-like amplitude to log10 scale
            target_log10 = (target['amp_db'] + 70) / 10  # -20 dB -> 5.0, 0 dB -> 7.0
            target_contribution = (target_log10 - noise_floor) * gauss
            
            # Add target contribution
            rd_map = np.maximum(rd_map, noise_floor + target_contribution)
        
        # Clip to display range (matching hardware processing)
        rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        self._frame_count += 1
        
        return rd_map.astype(np.float32)

    def _get_test_pattern_frame(self) -> np.ndarray:
        """Generate a test pattern frame for visual validation.
        
        Test patterns are designed to verify:
        - Coordinate mapping (which corner is which)
        - Axis orientation (range vs doppler)
        - Color mapping (min to max scale)
        - Interpolation behavior
        
        Coordinate system:
        - rd_map[d, r] where d=Doppler index, r=Range index
        - d=0 is bottom (negative max Doppler), d=n_doppler-1 is top (positive max Doppler)
        - r=0 is left (0 meters), r=n_range-1 is right (max_range meters)
        
        NOTE: The aspect ratio can be extreme (e.g., 512x30 = 17:1). Patterns are
        designed to be visible even with this aspect ratio by using appropriately
        sized features in each dimension independently.
        """
        rd_map = np.full((self.n_doppler, self.n_range), self.min_scale, dtype=np.float32)
        
        if self._test_pattern == 'corner_dots':
            # Place bright regions at corners with different intensities
            # This helps verify coordinate orientation
            # Use independent radii for each axis to handle extreme aspect ratios
            # Radius should be ~15% of each dimension to be clearly visible
            radius_d = max(20, self.n_doppler // 7)  # ~15% of Doppler height
            radius_r = max(4, self.n_range // 7)     # ~15% of Range width
            
            corners = [
                # (d_idx, r_idx, intensity_fraction, label)
                (0, 0, 1.0, "bottom-left"),           # d=0, r=0: bottom-left (brightest)
                (0, self.n_range-1, 0.75, "bottom-right"),  # d=0, r=max: bottom-right
                (self.n_doppler-1, 0, 0.5, "top-left"),     # d=max, r=0: top-left
                (self.n_doppler-1, self.n_range-1, 0.35, "top-right"),  # d=max, r=max: top-right (dimmest but visible)
            ]
            
            for d_center, r_center, intensity, label in corners:
                # Create an elliptical dot with different radii for each axis
                for dd in range(-radius_d, radius_d+1):
                    for dr in range(-radius_r, radius_r+1):
                        d = d_center + dd
                        r = r_center + dr
                        if 0 <= d < self.n_doppler and 0 <= r < self.n_range:
                            # Normalized distance for ellipse
                            dist_norm = np.sqrt((dd / radius_d)**2 + (dr / radius_r)**2)
                            if dist_norm <= 1.0:
                                # Gaussian falloff (less aggressive for better visibility)
                                val = intensity * np.exp(-1.5 * dist_norm**2)
                                rd_map[d, r] = max(rd_map[d, r], 
                                    self.min_scale + val * (self.max_scale - self.min_scale))
        
        elif self._test_pattern == 'gradient_h':
            # Horizontal gradient: left (r=0) is min, right (r=max) is max
            # This validates the Range axis (horizontal)
            for r in range(self.n_range):
                val = self.min_scale + (r / max(1, self.n_range - 1)) * (self.max_scale - self.min_scale)
                rd_map[:, r] = val
        
        elif self._test_pattern == 'gradient_v':
            # Vertical gradient: bottom (d=0) is min, top (d=max) is max
            # This validates the Doppler axis (vertical)
            for d in range(self.n_doppler):
                val = self.min_scale + (d / max(1, self.n_doppler - 1)) * (self.max_scale - self.min_scale)
                rd_map[d, :] = val
        
        elif self._test_pattern == 'center_target':
            # Single bright Gaussian blob at the center
            # This validates basic target rendering
            # Use different sigmas for each axis to maintain visibility
            cx = self.n_range // 2
            cy = self.n_doppler // 2
            sigma_r = max(2, self.n_range // 6)
            sigma_d = max(10, self.n_doppler // 6)
            
            r_idx = np.arange(self.n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            dist_sq = ((R - cx) / sigma_r)**2 + ((D - cy) / sigma_d)**2
            gauss = np.exp(-0.5 * dist_sq)
            
            rd_map = self.min_scale + gauss * (self.max_scale - self.min_scale)
        
        elif self._test_pattern == 'grid':
            # Regular grid pattern - helps verify scaling and spacing
            # Use 5 lines in each direction for visibility with extreme aspect ratios
            n_lines = 5
            
            # Vertical lines (constant range) - thick enough to be visible
            line_width_r = max(1, self.n_range // 20)
            line_spacing_r = max(1, self.n_range // n_lines)
            for i in range(n_lines + 1):
                r_center = min(i * line_spacing_r, self.n_range - 1)
                for dr in range(-line_width_r, line_width_r + 1):
                    rr = r_center + dr
                    if 0 <= rr < self.n_range:
                        rd_map[:, rr] = np.maximum(rd_map[:, rr], self.max_scale * 0.7)
            
            # Horizontal lines (constant Doppler) - thick enough to be visible
            line_width_d = max(5, self.n_doppler // 50)  # Thicker to account for aspect ratio
            line_spacing_d = max(1, self.n_doppler // n_lines)
            for i in range(n_lines + 1):
                d_center = min(i * line_spacing_d, self.n_doppler - 1)
                for dd in range(-line_width_d, line_width_d + 1):
                    dd_idx = d_center + dd
                    if 0 <= dd_idx < self.n_doppler:
                        rd_map[dd_idx, :] = np.maximum(rd_map[dd_idx, :], self.max_scale * 0.7)
            
            # Make intersections brighter with larger markers
            for i in range(n_lines + 1):
                for j in range(n_lines + 1):
                    r_center = min(i * line_spacing_r, self.n_range - 1)
                    d_center = min(j * line_spacing_d, self.n_doppler - 1)
                    for dr in range(-line_width_r*2, line_width_r*2 + 1):
                        for dd in range(-line_width_d*2, line_width_d*2 + 1):
                            rr = r_center + dr
                            dd_idx = d_center + dd
                            if 0 <= rr < self.n_range and 0 <= dd_idx < self.n_doppler:
                                rd_map[dd_idx, rr] = self.max_scale
        
        elif self._test_pattern == 'diagonal':
            # Diagonal line from bottom-left to top-right
            # This validates that both axes are correctly oriented
            # Use different line widths for each axis
            line_width_r = max(2, self.n_range // 15)
            line_width_d = max(10, self.n_doppler // 30)
            
            # Step through the larger dimension
            steps = max(self.n_range, self.n_doppler)
            for i in range(steps):
                r = int(i * (self.n_range - 1) / max(1, steps - 1))
                d = int(i * (self.n_doppler - 1) / max(1, steps - 1))
                
                for dr in range(-line_width_r, line_width_r + 1):
                    for dd in range(-line_width_d, line_width_d + 1):
                        rr = r + dr
                        dd_idx = d + dd
                        if 0 <= rr < self.n_range and 0 <= dd_idx < self.n_doppler:
                            rd_map[dd_idx, rr] = self.max_scale
        
        elif self._test_pattern == 'checkerboard':
            # Checkerboard pattern - helps identify any axis flipping
            # Use 4x4 pattern for better visibility with extreme aspect ratios
            cells_r = 4
            cells_d = 4
            cell_width = max(1, self.n_range // cells_r)
            cell_height = max(1, self.n_doppler // cells_d)
            
            for d in range(self.n_doppler):
                for r in range(self.n_range):
                    cell_r = r // cell_width
                    cell_d = d // cell_height
                    if (cell_r + cell_d) % 2 == 0:
                        rd_map[d, r] = self.max_scale
                    else:
                        rd_map[d, r] = self.min_scale
        
        elif self._test_pattern == 'hb100_stationary':
            # Simulate HB100 at ~3m, stationary (zero Doppler)
            # This is what you should see with HB100 placed at ~3m from phaser
            #
            # Expected appearance:
            # - Bright spot at center Doppler (d = n_doppler/2)
            # - Range bin corresponding to ~3 meters
            # - Some spread in range due to FFT windowing
            # - Noise floor everywhere else
            
            # Calculate range bin for 3 meters
            # range_resolution = c / (2 * chirp_bw) 
            # With chirp_bw = 500 MHz, range_res = 0.3m
            # But we're displaying sliced range, so 3m should be around 30% of display
            target_range_m = 3.0  # meters
            target_range_fraction = target_range_m / self.max_range
            target_r = int(target_range_fraction * self.n_range)
            target_r = min(max(0, target_r), self.n_range - 1)
            
            # Zero Doppler = center of Doppler axis
            target_d = self.n_doppler // 2
            
            # Add noise floor
            noise_floor = self.min_scale + 1.5
            rd_map[:, :] = noise_floor
            noise = np.random.standard_normal((self.n_doppler, self.n_range)).astype(np.float32) * 0.3
            rd_map += noise
            
            # Add target as elliptical Gaussian
            # Wider in Doppler (velocity spread), narrower in range
            sigma_r = max(2, self.n_range // 15)  # ~7% of range
            sigma_d = max(10, self.n_doppler // 30)  # ~3% of Doppler
            
            r_idx = np.arange(self.n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            dist_sq = ((R - target_r) / sigma_r)**2 + ((D - target_d) / sigma_d)**2
            target_gauss = np.exp(-0.5 * dist_sq)
            
            # Target should be ~20-30 dB above noise floor
            # In log10 scale, that's about 2-3 units above noise
            target_level = self.max_scale - 1.0
            rd_map = np.maximum(rd_map, noise_floor + target_gauss * (target_level - noise_floor))
            
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        elif self._test_pattern == 'hb100_walking':
            # Simulate HB100 moving toward the radar (walking speed ~1.5 m/s)
            # This creates a target offset from zero Doppler
            #
            # Expected appearance:
            # - Bright spot above center Doppler (positive Doppler = approaching)
            # - Range bin around ~4 meters
            # - May have some spread due to motion
            
            target_range_m = 4.0
            target_range_fraction = target_range_m / self.max_range
            target_r = int(target_range_fraction * self.n_range)
            target_r = min(max(0, target_r), self.n_range - 1)
            
            # Doppler shift for 1.5 m/s approaching
            # Doppler_Hz = 2 * v * f_c / c
            # With f_c = 10.5 GHz, v = 1.5 m/s: fd ≈ 105 Hz
            # Doppler resolution = 1 / (num_chirps * ramp_time)
            #                    = 1 / (512 * 500e-6) = 3.9 Hz
            # So 105 Hz = ~27 Doppler bins from center
            walking_speed_mps = 1.5
            center_freq_hz = 10.5e9
            c = 3e8
            doppler_hz = 2 * walking_speed_mps * center_freq_hz / c
            doppler_res = 1 / (self.num_chirps * self.ramp_time_us * 1e-6)
            doppler_bins_offset = int(doppler_hz / doppler_res)
            
            # Positive Doppler = upper half (approaching)
            target_d = self.n_doppler // 2 + doppler_bins_offset
            target_d = min(max(0, target_d), self.n_doppler - 1)
            
            # Add noise floor
            noise_floor = self.min_scale + 1.5
            rd_map[:, :] = noise_floor
            noise = np.random.standard_normal((self.n_doppler, self.n_range)).astype(np.float32) * 0.3
            rd_map += noise
            
            # Add target - slightly more spread due to motion
            sigma_r = max(2, self.n_range // 12)
            sigma_d = max(15, self.n_doppler // 20)
            
            r_idx = np.arange(self.n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            dist_sq = ((R - target_r) / sigma_r)**2 + ((D - target_d) / sigma_d)**2
            target_gauss = np.exp(-0.5 * dist_sq)
            
            target_level = self.max_scale - 1.0
            rd_map = np.maximum(rd_map, noise_floor + target_gauss * (target_level - noise_floor))
            
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        elif self._test_pattern == 'dc_leakage':
            # Simulate DC leakage / direct path interference
            # This is common in real radar systems - a bright line at zero Doppler
            # often with maximum intensity at zero range
            #
            # Expected appearance:
            # - Bright horizontal line across entire range at center Doppler
            # - Brightest at near range (left side)
            # - Decaying with range
            
            # Add noise floor
            noise_floor = self.min_scale + 1.5
            rd_map[:, :] = noise_floor
            noise = np.random.standard_normal((self.n_doppler, self.n_range)).astype(np.float32) * 0.2
            rd_map += noise
            
            # DC component - horizontal line at center Doppler
            center_d = self.n_doppler // 2
            dc_width = max(5, self.n_doppler // 50)  # ~2% of Doppler
            
            for dd in range(-dc_width, dc_width + 1):
                d = center_d + dd
                if 0 <= d < self.n_doppler:
                    # Decay with range (1/r falloff in log scale)
                    for r in range(self.n_range):
                        range_decay = 1.0 - 0.5 * (r / self.n_range)  # Linear decay
                        dc_level = self.max_scale * range_decay * np.exp(-0.5 * (dd / (dc_width/2))**2)
                        rd_map[d, r] = max(rd_map[d, r], dc_level)
            
            # Add a real target at ~5m to show it through the DC
            target_r = int(0.5 * self.n_range)  # 5m with 10m max
            target_d = center_d + 20  # Slight positive Doppler
            if target_d < self.n_doppler:
                sigma_r = max(2, self.n_range // 15)
                sigma_d = max(10, self.n_doppler // 40)
                
                r_idx = np.arange(self.n_range)
                d_idx = np.arange(self.n_doppler)
                R, D = np.meshgrid(r_idx, d_idx)
                
                dist_sq = ((R - target_r) / sigma_r)**2 + ((D - target_d) / sigma_d)**2
                target_gauss = np.exp(-0.5 * dist_sq)
                
                rd_map = np.maximum(rd_map, noise_floor + target_gauss * (self.max_scale - 1 - noise_floor))
            
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        return rd_map.astype(np.float32)

    def _apply_mti(self, rx_bursts: np.ndarray) -> np.ndarray:
        """
        Apply phase-corrected 2-pulse canceller MTI filter.
        Matching Jon's implementation exactly.
        """
        rx_chirps = to_gpu(rx_bursts)
        num_samples = rx_chirps.shape[1]
        
        # Create output array
        Chirp2P = xp.ones([self.num_chirps, num_samples], dtype=xp.complex128)
        
        for chirp in range(self.num_chirps - 1):
            chirpI = rx_chirps[chirp, :]
            chirpI1 = rx_chirps[chirp + 1, :]
            
            # Correlation to find phase difference
            chirp_correlation = xp.correlate(chirpI, chirpI1, 'valid')
            angle_diff = xp.angle(chirp_correlation)
            
            # Phase-corrected subtraction
            Chirp2P[chirp, :] = chirpI1 - chirpI * xp.exp(-1j * angle_diff[0])
        
        if GPU_AVAILABLE:
            cp.cuda.Stream.null.synchronize()
        
        return Chirp2P

    def _process_to_rd_map(self, rx_bursts) -> np.ndarray:
        """
        Process IQ data to Range-Doppler map using GPU.
        Matching Jon's freq_process exactly.
        
        Returns values in log10 scale (not dB), clipped to [min_scale, max_scale].
        Shape: (n_doppler, n_range) - rows are Doppler bins, columns are Range bins.
        The range axis is sliced to only include 0 to max_range meters.
        For display, use vmin=min_scale, vmax=max_scale.
        """
        data_gpu = to_gpu(rx_bursts)
        
        # 2D FFT with shift
        # Input: (num_chirps, good_ramp_samples) = (n_doppler, n_range_full)
        # Output after fft2: (n_doppler, n_range_full) - Doppler along rows, Range along columns
        # fftshift centers DC in both dimensions
        rx_bursts_fft = xp.fft.fftshift(xp.abs(xp.fft.fft2(data_gpu)))
        
        # Convert to log10 scale (matching Jon's script exactly - NOT dB!)
        range_doppler_data = xp.log10(xp.maximum(rx_bursts_fft, 1e-12))
        
        # Slice to only include the displayable range (0 to max_range meters)
        # This is equivalent to Jon's ax.set_ylim([0, max_range])
        range_doppler_data = range_doppler_data[:, self.range_start_idx:self.range_end_idx]
        
        # Clip to display range (matching Jon's script)
        range_doppler_data = xp.clip(range_doppler_data, self.min_scale, self.max_scale)
        
        if GPU_AVAILABLE:
            cp.cuda.Stream.null.synchronize()
        
        return to_cpu(range_doppler_data).astype(np.float32)

    def get_dimensions(self) -> Tuple[int, int]:
        """Return (n_doppler, n_range) dimensions of output frames."""
        return (self.n_doppler, self.n_range)

    def get_dimensions_full(self) -> Tuple[int, int]:
        """Return (n_doppler, n_range_full) dimensions for full-resolution frames."""
        return (self.n_doppler, self.n_range_full)

    def get_frame_full_resolution(self) -> np.ndarray:
        """
        Get full-resolution frame without range slicing.
        
        Returns:
            2D numpy array of shape (n_doppler, n_range_full) where n_range_full
            is typically 1800 bins covering the full unambiguous range (~54m).
            Values are in log10 scale [min_scale, max_scale].
            
        This is useful for web visualization where client-side zoom is desired,
        allowing users to explore the full range without re-acquiring data.
        """
        if self.mode == 'hardware':
            return self._get_hardware_frame_full()
        else:
            return self._get_synthetic_frame_full()

    def _get_hardware_frame_full(self) -> np.ndarray:
        """Capture and process a full-resolution frame from hardware."""
        if not self._hardware_initialized:
            raise RuntimeError("Hardware not initialized")
        
        # Log GPU status once so it appears with timing lines in journalctl
        if not self._gpu_status_logged:
            status = get_gpu_status()
            print(
                f"RadarBackend: gpu_available={status['gpu_available']} backend={status['backend']} (first hardware frame)",
                flush=True,
            )
            self._gpu_status_logged = True
        
        t0 = time.perf_counter()
        # Trigger burst (matching Jon's script)
        self.phaser._gpios.gpio_burst = 0
        self.phaser._gpios.gpio_burst = 1
        self.phaser._gpios.gpio_burst = 0
        t1 = time.perf_counter()
        
        # Capture data
        data = self.sdr.rx()
        t2 = time.perf_counter()
        chan1 = data[0]
        chan2 = data[1]
        sum_data = chan1 + chan2
        t3 = time.perf_counter()
        
        # Store raw data for diagnostics
        self._last_raw_data = sum_data
        
        # Reshape into chirps (vectorized: one indexing op instead of 512-loop)
        start_indices = self.start_offset_samples + np.arange(self.num_chirps) * self.n_frame
        offsets = start_indices[:, np.newaxis] + np.arange(self.good_ramp_samples)
        rx_bursts = sum_data[offsets].copy()
        t4 = time.perf_counter()
        
        # Store reshaped data for diagnostics
        self._last_rx_bursts = rx_bursts
        
        # Apply MTI filter if enabled
        if self.mti_enabled:
            rx_bursts = self._apply_mti(rx_bursts)
        
        # Process to Range-Doppler map (full resolution, no slicing) with fine-grained timing
        process_timings = {}
        rd_map = self._process_to_rd_map_full(rx_bursts, timings=process_timings)
        t5 = time.perf_counter()
        
        gpio_ms = (t1 - t0) * 1000
        sdr_rx_ms = (t2 - t1) * 1000
        channel_sum_ms = (t3 - t2) * 1000
        reshape_ms = (t4 - t3) * 1000
        process_total_ms = (t5 - t4) * 1000
        total_ms = (t5 - t0) * 1000
        to_gpu_ms = process_timings.get("to_gpu_ms", 0)
        fft_ms = process_timings.get("fft_ms", 0)
        log10_clip_ms = process_timings.get("log10_clip_ms", 0)
        sync_ms = process_timings.get("sync_ms", 0)
        to_cpu_ms = process_timings.get("to_cpu_ms", 0)
        astype_ms = process_timings.get("astype_ms", 0)
        print(
            f"RadarBackend timing: gpio_ms={gpio_ms:.3f} sdr_rx_ms={sdr_rx_ms:.2f} channel_sum_ms={channel_sum_ms:.3f} "
            f"reshape_ms={reshape_ms:.2f} to_gpu_ms={to_gpu_ms:.2f} fft_ms={fft_ms:.2f} log10_clip_ms={log10_clip_ms:.2f} "
            f"sync_ms={sync_ms:.2f} to_cpu_ms={to_cpu_ms:.2f} astype_ms={astype_ms:.3f} process_total_ms={process_total_ms:.2f} total_ms={total_ms:.2f}",
            flush=True,
        )
        
        return rd_map

    def _get_synthetic_frame_full(self) -> np.ndarray:
        """Generate a full-resolution synthetic Range-Doppler frame.
        
        Creates a frame at full resolution (n_doppler x n_range_full) with
        targets positioned appropriately for the full range axis.
        If a test pattern is set, generates that pattern instead of animated targets.
        """
        if self._test_pattern != 'animated':
            return self._get_test_pattern_frame_full()
        
        return self._get_animated_frame_full()

    def _get_animated_frame_full(self) -> np.ndarray:
        """Generate an animated full-resolution frame with moving targets."""
        # Use log10 scale to match hardware output
        noise_floor = 1.5
        rd_map = np.full((self.n_doppler, self.n_range_full), noise_floor, dtype=np.float32)
        
        # Add smooth noise variation
        noise = self._rng.standard_normal((self.n_doppler, self.n_range_full)).astype(np.float32) * 0.3
        rd_map += noise
        
        # Animate time
        t = self._frame_count * 0.05
        
        # Calculate max range for full resolution (approximately 54m with default settings)
        c = 3e8
        slope = self.chirp_bw / self.ramp_time_s
        max_range_full = (self.n_range_full * self.sample_rate / self.n_range_full) * c / (2 * slope) / self.sample_rate
        # Simplified: use the range_axis to find actual max range
        max_range_full = abs(self.range_axis[-1] - self.range_axis[0])
        
        # Scale factor to map display range fraction to full range
        range_scale = self.max_range / max_range_full if max_range_full > 0 else 1.0
        
        # Add targets as smooth 2D Gaussian peaks (scaled for full range)
        for target in self._synthetic_targets:
            # Animate target position - scale range to full resolution
            range_frac_full = target['range_frac'] * range_scale
            range_center = range_frac_full * self.n_range_full + np.sin(t * target['velocity'] * 8) * 30
            doppler_center = target['doppler_frac'] * self.n_doppler + np.sin(t * 0.3 + target['velocity']) * 15
            
            # Create coordinate grids
            r_idx = np.arange(self.n_range_full)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            # Scale sigma for full resolution
            range_sigma = target['range_sigma'] * (self.n_range_full / self.n_range)
            
            # Gaussian blob
            range_dist = (R - range_center) / range_sigma
            doppler_dist = (D - doppler_center) / target['doppler_sigma']
            dist_sq = range_dist**2 + doppler_dist**2
            
            gauss = np.exp(-0.5 * dist_sq)
            target_log10 = (target['amp_db'] + 70) / 10
            target_contribution = (target_log10 - noise_floor) * gauss
            
            rd_map = np.maximum(rd_map, noise_floor + target_contribution)
        
        # Clip to display range
        rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        self._frame_count += 1
        
        return rd_map.astype(np.float32)

    def _get_test_pattern_frame_full(self) -> np.ndarray:
        """Generate a full-resolution test pattern frame for visual validation.
        
        Same patterns as _get_test_pattern_frame() but at full resolution
        (n_doppler x n_range_full).
        """
        n_range = self.n_range_full  # Use full resolution
        
        # Start with a dark background
        rd_map = np.full((self.n_doppler, n_range), self.min_scale, dtype=np.float32)
        
        if self._test_pattern == 'corner_dots':
            # Place bright regions at corners with different intensities
            radius_d = max(20, self.n_doppler // 7)
            radius_r = max(50, n_range // 7)
            
            corners = [
                (0, 0, 0.6),
                (0, n_range - 1, 0.7),
                (self.n_doppler - 1, 0, 0.8),
                (self.n_doppler - 1, n_range - 1, 1.0),
            ]
            
            for d_corner, r_corner, val in corners:
                for d in range(max(0, d_corner - radius_d), min(self.n_doppler, d_corner + radius_d + 1)):
                    for r in range(max(0, r_corner - radius_r), min(n_range, r_corner + radius_r + 1)):
                        d_dist = abs(d - d_corner) / max(1, radius_d)
                        r_dist = abs(r - r_corner) / max(1, radius_r)
                        dist = np.sqrt(d_dist**2 + r_dist**2)
                        if dist <= 1.0:
                            intensity = (1.0 - dist) * val
                            rd_map[d, r] = max(rd_map[d, r],
                                              self.min_scale + intensity * (self.max_scale - self.min_scale))
        
        elif self._test_pattern == 'gradient_h':
            # Horizontal gradient
            for r in range(n_range):
                val = self.min_scale + (r / max(1, n_range - 1)) * (self.max_scale - self.min_scale)
                rd_map[:, r] = val
        
        elif self._test_pattern == 'gradient_v':
            # Vertical gradient
            for d in range(self.n_doppler):
                val = self.min_scale + (d / max(1, self.n_doppler - 1)) * (self.max_scale - self.min_scale)
                rd_map[d, :] = val
        
        elif self._test_pattern == 'center_target':
            # Single bright Gaussian blob at the center
            cx = n_range // 2
            cy = self.n_doppler // 2
            sigma_r = max(20, n_range // 20)
            sigma_d = max(20, self.n_doppler // 20)
            
            r_idx = np.arange(n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            gauss = np.exp(-0.5 * (((R - cx) / sigma_r)**2 + ((D - cy) / sigma_d)**2))
            rd_map = self.min_scale + gauss * (self.max_scale - self.min_scale)
        
        elif self._test_pattern == 'grid':
            # Regular grid pattern
            n_lines = 5
            
            # Vertical lines (constant range)
            line_width_r = max(5, n_range // 50)
            for i in range(n_lines):
                r = int((i + 0.5) * n_range / n_lines)
                r_start = max(0, r - line_width_r // 2)
                r_end = min(n_range, r + line_width_r // 2 + 1)
                rd_map[:, r_start:r_end] = self.max_scale
            
            # Horizontal lines (constant Doppler)
            line_width_d = max(5, self.n_doppler // 50)
            for i in range(n_lines):
                d = int((i + 0.5) * self.n_doppler / n_lines)
                d_start = max(0, d - line_width_d // 2)
                d_end = min(self.n_doppler, d + line_width_d // 2 + 1)
                rd_map[d_start:d_end, :] = self.max_scale
        
        elif self._test_pattern == 'diagonal':
            # Diagonal line from bottom-left to top-right
            line_width_r = max(5, n_range // 30)
            line_width_d = max(10, self.n_doppler // 30)
            
            for d in range(self.n_doppler):
                r_center = int(d * n_range / self.n_doppler)
                for rr in range(max(0, r_center - line_width_r), min(n_range, r_center + line_width_r + 1)):
                    for dd_offset in range(-line_width_d // 2, line_width_d // 2 + 1):
                        dd_idx = d + dd_offset
                        if 0 <= dd_idx < self.n_doppler:
                            rd_map[dd_idx, rr] = self.max_scale
        
        elif self._test_pattern == 'checkerboard':
            # Checkerboard pattern
            cells_r = 8
            cells_d = 4
            cell_width = max(1, n_range // cells_r)
            cell_height = max(1, self.n_doppler // cells_d)
            
            for d in range(self.n_doppler):
                for r in range(n_range):
                    cell_r = r // cell_width
                    cell_d = d // cell_height
                    if (cell_r + cell_d) % 2 == 0:
                        rd_map[d, r] = self.max_scale
                    else:
                        rd_map[d, r] = self.min_scale
        
        elif self._test_pattern == 'hb100_stationary':
            # Simulate HB100 at ~3m, stationary (zero Doppler)
            range_bin = int(3.0 / abs(self.range_axis[-1] - self.range_axis[0]) * n_range) if len(self.range_axis) > 1 else n_range // 3
            doppler_bin = self.n_doppler // 2
            
            sigma_r = max(20, n_range // 50)
            sigma_d = max(10, self.n_doppler // 30)
            
            r_idx = np.arange(n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            gauss = np.exp(-0.5 * (((R - range_bin) / sigma_r)**2 + ((D - doppler_bin) / sigma_d)**2))
            rd_map = self.min_scale + gauss * (self.max_scale - self.min_scale) * 0.9
            
            # Add some noise
            noise = self._rng.standard_normal((self.n_doppler, n_range)).astype(np.float32) * 0.2
            rd_map += noise
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        elif self._test_pattern == 'hb100_walking':
            # Simulate HB100 moving toward the radar (walking speed ~1.5 m/s)
            range_bin = int(3.0 / abs(self.range_axis[-1] - self.range_axis[0]) * n_range) if len(self.range_axis) > 1 else n_range // 3
            doppler_offset = int(self.n_doppler * 0.15)
            doppler_bin = self.n_doppler // 2 + doppler_offset
            
            sigma_r = max(20, n_range // 50)
            sigma_d = max(10, self.n_doppler // 30)
            
            r_idx = np.arange(n_range)
            d_idx = np.arange(self.n_doppler)
            R, D = np.meshgrid(r_idx, d_idx)
            
            gauss = np.exp(-0.5 * (((R - range_bin) / sigma_r)**2 + ((D - doppler_bin) / sigma_d)**2))
            rd_map = self.min_scale + gauss * (self.max_scale - self.min_scale) * 0.9
            
            # Add some noise
            noise = self._rng.standard_normal((self.n_doppler, n_range)).astype(np.float32) * 0.2
            rd_map += noise
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        elif self._test_pattern == 'dc_leakage':
            # Simulate DC leakage - bright line at zero Doppler
            dc_bin = self.n_doppler // 2
            dc_width = max(5, self.n_doppler // 50)
            
            for d in range(max(0, dc_bin - dc_width), min(self.n_doppler, dc_bin + dc_width + 1)):
                d_dist = abs(d - dc_bin) / max(1, dc_width)
                intensity = 1.0 - d_dist
                rd_map[d, :] = self.min_scale + intensity * (self.max_scale - self.min_scale) * 0.8
            
            # Brighter at near range
            for r in range(n_range):
                r_factor = 1.0 - (r / n_range) * 0.5
                rd_map[:, r] *= r_factor
            
            # Add noise
            noise = self._rng.standard_normal((self.n_doppler, n_range)).astype(np.float32) * 0.15
            rd_map += noise
            rd_map = np.clip(rd_map, self.min_scale, self.max_scale)
        
        self._frame_count += 1
        return rd_map.astype(np.float32)

    def _process_to_rd_map_full(self, rx_bursts, timings: Optional[Dict] = None):
        """
        Process IQ data to full-resolution Range-Doppler map.
        
        Unlike _process_to_rd_map(), this returns the full range axis without slicing.
        Shape: (n_doppler, n_range_full) - typically (512, 1800).
        If timings is a dict, it is filled with per-substep ms (to_gpu_ms, fft_ms, etc.).
        Returns (rd_map, timings) if timings was passed, else rd_map only.
        """
        t = {}
        t0 = time.perf_counter()
        # Reuse pre-allocated GPU buffer when available to reduce allocator pressure
        if GPU_AVAILABLE and self._gpu_rx_buf is not None and self._gpu_rx_buf.shape == rx_bursts.shape:
            self._gpu_rx_buf.set(np.ascontiguousarray(rx_bursts))
            data_gpu = self._gpu_rx_buf
        else:
            data_gpu = to_gpu(rx_bursts)
            if GPU_AVAILABLE and rx_bursts.shape == (self.num_chirps, self.good_ramp_samples):
                self._gpu_rx_buf = data_gpu if hasattr(data_gpu, 'get') else cp.asarray(data_gpu)
        t["to_gpu_ms"] = (time.perf_counter() - t0) * 1000
        
        t1 = time.perf_counter()
        rx_bursts_fft = xp.fft.fftshift(xp.abs(xp.fft.fft2(data_gpu)))
        t["fft_ms"] = (time.perf_counter() - t1) * 1000
        
        t2 = time.perf_counter()
        range_doppler_data = xp.log10(xp.maximum(rx_bursts_fft, 1e-12))
        range_doppler_data = xp.clip(range_doppler_data, self.min_scale, self.max_scale)
        t["log10_clip_ms"] = (time.perf_counter() - t2) * 1000
        
        t3 = time.perf_counter()
        if GPU_AVAILABLE:
            cp.cuda.Stream.null.synchronize()
        t["sync_ms"] = (time.perf_counter() - t3) * 1000
        
        t4 = time.perf_counter()
        out_cpu = to_cpu(range_doppler_data)
        t["to_cpu_ms"] = (time.perf_counter() - t4) * 1000
        
        t5 = time.perf_counter()
        rd_map = out_cpu.astype(np.float32)
        t["astype_ms"] = (time.perf_counter() - t5) * 1000
        
        if timings is not None:
            timings.update(t)
        return rd_map

    def get_config(self) -> Dict:
        """Return current configuration as dictionary."""
        config = {
            'mode': self.mode,
            'sample_rate': self.sample_rate,
            'num_chirps': self.num_chirps,
            'ramp_time_us': self.ramp_time_us,
            'chirp_bw': self.chirp_bw,
            'center_freq': self.center_freq,
            'output_freq': self.output_freq,
            'rx_gain': self.rx_gain,
            'n_doppler': self.n_doppler,
            'n_range': self.n_range,
            'min_scale': self.min_scale,
            'max_scale': self.max_scale,
            'gpu_available': GPU_AVAILABLE,
            'mti_enabled': self.mti_enabled,
        }
        # Add pattern info for synthetic mode
        if self.mode == 'synthetic':
            config['test_pattern'] = self._test_pattern
            config['available_patterns'] = self._available_patterns
        return config

    def get_gpu_status(self) -> Dict:
        """Return GPU acceleration status for logging from Rust."""
        return get_gpu_status()

    def export_frame(self, directory: str, frame: np.ndarray = None) -> str:
        """Export the current frame to a file for offline analysis.
        
        Args:
            directory: Directory to save files to
            frame: Optional frame to export. If None, captures a new frame.
            
        Returns:
            Path to the exported .npy file
        """
        import os
        import json
        from datetime import datetime
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Get frame if not provided
        if frame is None:
            frame = self.get_frame()
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Save frame as numpy array
        frame_path = os.path.join(directory, f"frame_{timestamp}.npy")
        np.save(frame_path, frame)
        
        # Save metadata
        meta_path = os.path.join(directory, f"frame_{timestamp}_meta.json")
        metadata = {
            'timestamp': timestamp,
            'shape': list(frame.shape),
            'dtype': str(frame.dtype),
            'min': float(frame.min()),
            'max': float(frame.max()),
            'mean': float(frame.mean()),
            'std': float(frame.std()),
            'config': self.get_config(),
        }
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"RadarBackend: Exported frame to {frame_path}")
        return frame_path

    def shutdown(self):
        """Clean up resources."""
        if self._hardware_initialized and self.sdr:
            try:
                self.sdr.tx_destroy_buffer()
                print("RadarBackend: Hardware shutdown complete")
            except Exception as e:
                print(f"RadarBackend: Shutdown error: {e}")


# ============================================================================
# FACTORY FUNCTIONS FOR PYO3
# ============================================================================
def create_backend(
    mode: str,
    sdr_uri: str = "ip:192.168.2.1",
    phaser_uri: str = "ip:192.168.4.184",
    sample_rate: int = 4_000_000,
    num_chirps: int = 512,
    ramp_time_us: int = 500,
    chirp_bw: float = 500_000_000,
    center_freq: int = 2_100_000_000,
    output_freq: int = 9_900_000_000,
    rx_gain: int = 30,
    max_range: float = 10.0,
    test_pattern: str = "animated",
) -> RadarBackend:
    """Factory function for creating a RadarBackend instance.
    
    Args:
        mode: 'hardware' or 'synthetic'
        test_pattern: For synthetic mode, the test pattern to use.
            Options: 'animated' (default), 'corner_dots', 'gradient_h', 
            'gradient_v', 'center_target', 'grid', 'diagonal', 'checkerboard',
            'hb100_stationary', 'hb100_walking', 'dc_leakage'
    """
    backend = RadarBackend(
        mode=mode,
        sdr_uri=sdr_uri,
        phaser_uri=phaser_uri,
        sample_rate=sample_rate,
        num_chirps=num_chirps,
        ramp_time_us=ramp_time_us,
        chirp_bw=chirp_bw,
        center_freq=center_freq,
        output_freq=output_freq,
        rx_gain=rx_gain,
        max_range=max_range,
    )
    
    # Set test pattern if in synthetic mode
    if mode == 'synthetic' and test_pattern != 'animated':
        backend.set_test_pattern(test_pattern)
    
    return backend


def is_gpu_available() -> bool:
    """Check if GPU acceleration is available."""
    return GPU_AVAILABLE


# ============================================================================
# STANDALONE TEST
# ============================================================================
if __name__ == "__main__":
    import argparse
    import os
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Test RadarBackend")
    parser.add_argument("--mode", choices=["synthetic", "hardware"], default="synthetic")
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--sdr-uri", default="ip:192.168.2.1", help="SDR URI (e.g., 'usb:' or 'ip:192.168.2.1')")
    parser.add_argument("--phaser-uri", default="ip:192.168.4.184", help="Phaser board URI")
    parser.add_argument("--export", type=str, help="Export frames to directory (creates .npy files)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between frames in seconds")
    args = parser.parse_args()
    
    print(f"Testing RadarBackend in {args.mode} mode...")
    print(f"  SDR URI: {args.sdr_uri}")
    print(f"  Phaser URI: {args.phaser_uri}")
    
    backend = create_backend(mode=args.mode, sdr_uri=args.sdr_uri, phaser_uri=args.phaser_uri)
    config = backend.get_config()
    print(f"Config: {config}")
    
    # Setup export directory if requested
    export_dir = None
    if args.export:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(args.export, f"capture_{timestamp}")
        os.makedirs(export_dir, exist_ok=True)
        print(f"Exporting frames to: {export_dir}")
        # Save config
        import json
        with open(os.path.join(export_dir, "config.json"), "w") as f:
            json.dump(config, f, indent=2)
    
    times = []
    frames_data = []
    raw_diagnostics = []
    
    for i in range(args.frames):
        start = time.perf_counter()
        frame = backend.get_frame()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        
        # Get raw diagnostics for hardware mode
        if args.mode == 'hardware':
            diag = backend.get_raw_diagnostics()
            if diag and i == 0:  # Print detailed diagnostics for first frame
                print(f"\n--- Raw Signal Diagnostics (Frame 0) ---")
                print(f"  Raw buffer length: {diag['raw_len']} samples")
                print(f"  Raw |signal| range: {diag['raw_abs_min']:.2e} to {diag['raw_abs_max']:.2e}")
                print(f"  Raw |signal| mean: {diag['raw_abs_mean']:.2e}")
                print(f"  Raw power: {diag['raw_power_db']:.1f} dB")
                if 'fft_mag_max' in diag:
                    print(f"  FFT magnitude range: {diag['fft_mag_min']:.2e} to {diag['fft_mag_max']:.2e}")
                    print(f"  FFT log10 range: {diag['fft_log10_max']:.2f} to {diag['fft_log10_min']:.2f}")
                    print(f"  Burst 0 power: {diag['burst0_power_db']:.1f} dB")
                print("")
            raw_diagnostics.append(diag)
        
        # Calculate some statistics to check if data is changing
        frame_stats = {
            "min": float(frame.min()),
            "max": float(frame.max()),
            "mean": float(frame.mean()),
            "std": float(frame.std()),
        }
        
        print(f"Frame {i+1}: shape={frame.shape}, min={frame_stats['min']:.1f} dB, max={frame_stats['max']:.1f} dB, "
              f"mean={frame_stats['mean']:.1f} dB, std={frame_stats['std']:.2f}, time={elapsed*1000:.1f} ms")
        
        if export_dir:
            # Save individual frame
            np.save(os.path.join(export_dir, f"frame_{i:04d}.npy"), frame)
            frames_data.append(frame_stats)
        
        if args.delay > 0:
            time.sleep(args.delay)
    
    avg_time = np.mean(times) * 1000
    fps = 1000 / avg_time
    print(f"\nAverage: {avg_time:.1f} ms ({fps:.1f} FPS)")
    
    if export_dir and frames_data:
        # Analyze frame-to-frame variation
        stds = [f["std"] for f in frames_data]
        means = [f["mean"] for f in frames_data]
        print(f"\nFrame variation analysis:")
        print(f"  Mean of means: {np.mean(means):.2f} dB")
        print(f"  Std of means: {np.std(means):.4f} dB (higher = more variation between frames)")
        print(f"  Mean of stds: {np.mean(stds):.2f} (higher = more variation within frames)")
        
        # Save summary
        import json
        summary = {
            "frames": frames_data,
            "timing_ms": times,
            "avg_fps": fps,
            "mean_of_means": float(np.mean(means)),
            "std_of_means": float(np.std(means)),
        }
        
        # Add raw diagnostics if available
        if raw_diagnostics and raw_diagnostics[0]:
            # Convert numpy types in diagnostics for JSON serialization
            clean_diag = []
            for d in raw_diagnostics:
                if d:
                    cd = {}
                    for k, v in d.items():
                        if isinstance(v, tuple):
                            cd[k] = list(v)
                        else:
                            cd[k] = v
                    clean_diag.append(cd)
            summary["raw_diagnostics"] = clean_diag
        
        with open(os.path.join(export_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nData saved to: {export_dir}")
    
    backend.shutdown()
