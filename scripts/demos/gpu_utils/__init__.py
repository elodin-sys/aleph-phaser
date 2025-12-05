"""
GPU-accelerated radar signal processing utilities.

This package provides GPU-accelerated implementations of common radar
signal processing algorithms using CuPy (CUDA) with fallback to NumPy.

Modules:
    cupy_signal: GPU FFT, CFAR, and signal processing functions
    visualization: Real-time plotting utilities
"""

from .cupy_signal import (
    get_backend,
    is_gpu_available,
    to_gpu,
    to_cpu,
    gpu_fft,
    gpu_fft2,
    gpu_cfar,
    gpu_stft,
    gpu_range_doppler,
    benchmark_fft_sizes,
)

__all__ = [
    'get_backend',
    'is_gpu_available', 
    'to_gpu',
    'to_cpu',
    'gpu_fft',
    'gpu_fft2',
    'gpu_cfar',
    'gpu_stft',
    'gpu_range_doppler',
    'benchmark_fft_sizes',
]
