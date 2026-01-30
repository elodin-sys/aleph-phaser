"""
Phaser Wrapper for PyO3 Integration

This module provides a thin Python wrapper around pyadi-iio for use
with the Rust TUI radar application via PyO3.
"""

import adi
import numpy as np
from typing import Dict, Optional, Tuple


class PhaserWrapper:
    """Wrapper for complex pyadi-iio operations that are easier in Python."""

    def __init__(self, sdr_uri: str, phaser_uri: str):
        """
        Initialize the Phaser wrapper.

        Args:
            sdr_uri: PlutoSDR URI (e.g., 'ip:192.168.2.1')
            phaser_uri: Phaser/Raspberry Pi URI (e.g., 'ip:192.168.4.184')
        """
        self.sdr_uri = sdr_uri
        self.phaser_uri = phaser_uri
        self.sdr = None
        self.phaser = None
        self.tdd = None
        self.sdr_pins = None
        self._initialized = False

    def connect(self) -> bool:
        """Connect to hardware and initialize devices."""
        try:
            self.sdr = adi.ad9361(uri=self.sdr_uri)
            self.phaser = adi.CN0566(uri=self.phaser_uri, sdr=self.sdr)
            self.tdd = adi.tddn(self.sdr_uri)
            self.sdr_pins = adi.one_bit_adc_dac(self.sdr_uri)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def configure_radar(
        self,
        sample_rate: int,
        num_chirps: int,
        ramp_time_us: int,
        chirp_bw: float,
        center_freq: int = 2_100_000_000,
        output_freq: int = 9_900_000_000,
        rx_gain: int = 30,
    ) -> Dict:
        """
        Full radar configuration, returns computed parameters.

        Args:
            sample_rate: ADC sample rate in Hz
            num_chirps: Number of chirps (Doppler bins)
            ramp_time_us: Chirp ramp time in microseconds
            chirp_bw: Chirp bandwidth in Hz
            center_freq: SDR center frequency in Hz
            output_freq: Phaser output frequency in Hz
            rx_gain: Receive gain in dB

        Returns:
            Dictionary with computed parameters
        """
        if not self._initialized:
            raise RuntimeError("Not connected - call connect() first")

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
        self.sdr.sample_rate = int(sample_rate)
        self.sdr.rx_lo = int(center_freq)
        self.sdr.rx_enabled_channels = [0, 1]
        self.sdr.gain_control_mode_chan0 = 'manual'
        self.sdr.gain_control_mode_chan1 = 'manual'
        self.sdr.rx_hardwaregain_chan0 = int(rx_gain)
        self.sdr.rx_hardwaregain_chan1 = int(rx_gain)

        # Configure SDR Tx
        self.sdr.tx_lo = int(center_freq)
        self.sdr.tx_enabled_channels = [0, 1]
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx_hardwaregain_chan0 = -88
        self.sdr.tx_hardwaregain_chan1 = 0

        # Configure ADF4159 (ramping PLL)
        signal_freq = 100e3
        vco_freq = int(output_freq + signal_freq + center_freq)
        num_steps = int(ramp_time_us)

        self.phaser.frequency = int(vco_freq / 4)
        self.phaser.freq_dev_range = int(chirp_bw / 4)
        self.phaser.freq_dev_step = int((chirp_bw / 4) / num_steps)
        self.phaser.freq_dev_time = int(ramp_time_us)
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
        pri_ms = ramp_time_us / 1000 + 0.2
        self.tdd.frame_length_ms = pri_ms
        self.tdd.burst_count = num_chirps

        for ch in range(3):
            self.tdd.channel[ch].enable = True
            self.tdd.channel[ch].polarity = False
            self.tdd.channel[ch].on_raw = 0
            self.tdd.channel[ch].off_raw = 10

        self.tdd.enable = True

        # Compute buffer size
        total_time_ms = pri_ms * num_chirps
        buffer_size = 2 ** int(np.ceil(np.log2(total_time_ms / 1000 * sample_rate)))
        buffer_size = min(buffer_size, 2**22)
        self.sdr.rx_buffer_size = buffer_size

        # Create and transmit waveform
        N = 2**18
        fc = int(signal_freq)
        ts = 1 / float(sample_rate)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2**14
        q = np.sin(2 * np.pi * t * fc) * 2**14
        iq = 0.9 * (i + 1j * q)
        self.sdr.tx([iq, iq])

        # Calculate ramp parameters
        ramp_time_s = ramp_time_us / 1e6
        good_ramp_samples = int((ramp_time_s - 0.1 * ramp_time_s) * sample_rate)
        frame_samples = int(pri_ms / 1000 * sample_rate)

        return {
            "buffer_size": buffer_size,
            "frame_samples": frame_samples,
            "good_ramp_samples": good_ramp_samples,
            "pri_ms": pri_ms,
        }

    def trigger_burst(self):
        """Trigger a radar burst."""
        if self._initialized:
            self.phaser._gpios.gpio_burst = 0
            self.phaser._gpios.gpio_burst = 1
            self.phaser._gpios.gpio_burst = 0

    def capture(self) -> Tuple[np.ndarray, np.ndarray]:
        """Capture IQ data from both channels."""
        if not self._initialized:
            raise RuntimeError("Not connected")
        data = self.sdr.rx()
        return data[0], data[1]

    def shutdown(self):
        """Clean up resources."""
        if self.sdr:
            try:
                self.sdr.tx_destroy_buffer()
            except:
                pass


# For PyO3 access
def create_wrapper(sdr_uri: str, phaser_uri: str) -> PhaserWrapper:
    """Factory function for creating a PhaserWrapper instance."""
    return PhaserWrapper(sdr_uri, phaser_uri)
