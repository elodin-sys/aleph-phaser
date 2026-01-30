"""
Radar Backend for TUI Application

This module provides a unified interface for radar data acquisition and processing,
supporting both hardware (Phaser/PlutoSDR) and synthetic modes. All processing
uses GPU acceleration via CuPy when available.

The interface is designed for PyO3 integration with the Rust TUI application.
"""

import numpy as np
from typing import Dict, Optional, Tuple
import time


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
except ImportError:
    xp = np
    print("RadarBackend: GPU acceleration DISABLED (CuPy not installed, using NumPy)")
except Exception as e:
    xp = np
    print(f"RadarBackend: GPU acceleration DISABLED (CUDA error: {e})")


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
        
        # Calculate derived parameters (matching Jon's script exactly)
        self.ramp_time_s = ramp_time_us / 1e6
        self.begin_offset_time = 0.1 * self.ramp_time_s
        self.good_ramp_samples = int((self.ramp_time_s - self.begin_offset_time) * sample_rate)
        self.pri_ms = ramp_time_us / 1000 + 0.2
        self.n_frame = int(self.pri_ms / 1000 * sample_rate)
        
        # Output dimensions
        self.n_doppler = num_chirps
        self.n_range = self.good_ramp_samples
        
        # MTI filter state
        self.mti_enabled = False
        self.previous_frame = None
        
        # Display scaling (matching Jon's defaults)
        self.min_scale = 0
        self.max_scale = 50
        
        # Hardware objects (initialized in _init_hardware)
        self.sdr = None
        self.phaser = None
        self.tdd = None
        self.sdr_pins = None
        self._hardware_initialized = False
        
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
            
            self._hardware_initialized = True
            print("RadarBackend: Hardware initialized successfully")
            
        except Exception as e:
            print(f"RadarBackend: Hardware initialization failed: {e}")
            print("RadarBackend: Falling back to synthetic mode")
            self.mode = 'synthetic'
            self._init_synthetic()

    def _init_synthetic(self):
        """Initialize synthetic data generator state."""
        self._frame_count = 0
        
        # Create interesting simulated targets
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
        
        # Reshape into chirps (matching Jon's get_radar_data)
        rx_bursts = np.zeros((self.num_chirps, self.good_ramp_samples), dtype=complex)
        for burst in range(self.num_chirps):
            start_index = self.start_offset_samples + burst * self.n_frame
            stop_index = start_index + self.good_ramp_samples
            rx_bursts[burst] = sum_data[start_index:stop_index]
        
        # Apply MTI filter if enabled
        if self.mti_enabled:
            rx_bursts = self._apply_mti(rx_bursts)
        
        # Process to Range-Doppler map
        rd_map = self._process_to_rd_map(rx_bursts)
        
        return rd_map

    def _get_synthetic_frame(self) -> np.ndarray:
        """Generate a synthetic Range-Doppler frame."""
        # Generate directly in dB domain for cleaner synthetic output
        rd_map = np.full((self.n_doppler, self.n_range), -50.0, dtype=np.float32)
        
        # Add smooth noise floor
        noise = self._rng.standard_normal((self.n_doppler, self.n_range)).astype(np.float32) * 3.0
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
            target_contribution = (target['amp_db'] + 50) * gauss
            
            # Soft maximum combination
            existing = rd_map + 50
            combined = np.log(np.exp(existing) + np.exp(target_contribution))
            rd_map = combined - 50
        
        # Normalize so max = 0 dB
        max_val = np.max(rd_map)
        rd_map = rd_map - max_val
        
        self._frame_count += 1
        
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
        """
        data_gpu = to_gpu(rx_bursts)
        
        # 2D FFT with shift
        rx_bursts_fft = xp.fft.fftshift(xp.abs(xp.fft.fft2(data_gpu)))
        
        # Convert to dB (using log10, matching Jon's script)
        range_doppler_data = xp.log10(xp.maximum(rx_bursts_fft, 1e-12))
        
        # Transpose to (n_doppler, n_range) and clip
        range_doppler_data = range_doppler_data.T
        range_doppler_data = xp.clip(range_doppler_data, self.min_scale, self.max_scale)
        
        # Normalize so max = 0 dB (for consistent display)
        max_val = xp.max(range_doppler_data)
        range_doppler_data = range_doppler_data - max_val
        
        if GPU_AVAILABLE:
            cp.cuda.Stream.null.synchronize()
        
        return to_cpu(range_doppler_data).astype(np.float32)

    def get_dimensions(self) -> Tuple[int, int]:
        """Return (n_doppler, n_range) dimensions of output frames."""
        return (self.n_doppler, self.n_range)

    def get_config(self) -> Dict:
        """Return current configuration as dictionary."""
        return {
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
            'gpu_available': GPU_AVAILABLE,
            'mti_enabled': self.mti_enabled,
        }

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
) -> RadarBackend:
    """Factory function for creating a RadarBackend instance."""
    return RadarBackend(
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
    )


def is_gpu_available() -> bool:
    """Check if GPU acceleration is available."""
    return GPU_AVAILABLE


# ============================================================================
# STANDALONE TEST
# ============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RadarBackend")
    parser.add_argument("--mode", choices=["synthetic", "hardware"], default="synthetic")
    parser.add_argument("--frames", type=int, default=10)
    args = parser.parse_args()
    
    print(f"Testing RadarBackend in {args.mode} mode...")
    
    backend = create_backend(mode=args.mode)
    config = backend.get_config()
    print(f"Config: {config}")
    
    times = []
    for i in range(args.frames):
        start = time.perf_counter()
        frame = backend.get_frame()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"Frame {i+1}: shape={frame.shape}, min={frame.min():.1f} dB, max={frame.max():.1f} dB, time={elapsed*1000:.1f} ms")
    
    avg_time = np.mean(times) * 1000
    fps = 1000 / avg_time
    print(f"\nAverage: {avg_time:.1f} ms ({fps:.1f} FPS)")
    
    backend.shutdown()
