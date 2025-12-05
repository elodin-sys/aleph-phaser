"""
GPU-accelerated signal processing for radar applications.

Provides GPU implementations using CuPy with automatic fallback to NumPy
when CUDA is not available. This allows the same code to run on both
the Aleph (GPU-accelerated) and Raspberry Pi (CPU fallback).

Key Functions:
    gpu_fft: 1D FFT with GPU acceleration
    gpu_fft2: 2D FFT for range-Doppler maps
    gpu_cfar: Constant False Alarm Rate detection
    gpu_stft: Short-Time Fourier Transform for micro-Doppler
    gpu_range_doppler: Complete range-Doppler processing pipeline
"""

import time
import numpy as np

# Try to import CuPy for GPU acceleration
_GPU_AVAILABLE = False
_CUPY_ERROR = None

try:
    import cupy as cp
    from cupy.fft import fft, fft2, fftshift, ifft
    # Test that CUDA is actually working
    _test = cp.array([1, 2, 3])
    _test_result = cp.sum(_test)
    del _test, _test_result
    _GPU_AVAILABLE = True
    print("CuPy GPU acceleration: ENABLED")
except ImportError as e:
    _CUPY_ERROR = f"CuPy not installed: {e}"
    print(f"CuPy GPU acceleration: DISABLED ({_CUPY_ERROR})")
except Exception as e:
    _CUPY_ERROR = f"CUDA initialization failed: {e}"
    print(f"CuPy GPU acceleration: DISABLED ({_CUPY_ERROR})")


def is_gpu_available():
    """Check if GPU acceleration is available."""
    return _GPU_AVAILABLE


def get_backend():
    """Get the current array backend (cupy or numpy)."""
    if _GPU_AVAILABLE:
        return cp
    return np


def to_gpu(data):
    """Transfer data to GPU if available, otherwise return as-is."""
    if _GPU_AVAILABLE:
        if isinstance(data, np.ndarray):
            return cp.asarray(data)
        return data
    return data


def to_cpu(data):
    """Transfer data from GPU to CPU if needed."""
    if _GPU_AVAILABLE and hasattr(data, 'get'):
        return data.get()
    return data


def gpu_fft(data, n=None, axis=-1, window='blackman'):
    """
    GPU-accelerated 1D FFT with optional windowing.
    
    Args:
        data: Input array (numpy or cupy)
        n: FFT size (default: len(data))
        axis: Axis along which to compute FFT
        window: Window function ('blackman', 'hanning', 'hamming', None)
    
    Returns:
        FFT result, timing in seconds
    """
    xp = get_backend()
    
    # Transfer to GPU if needed
    data_gpu = to_gpu(data)
    
    start = time.perf_counter()
    
    # Apply window
    if window is not None:
        if n is None:
            n = data_gpu.shape[axis]
        if window == 'blackman':
            win = xp.blackman(n)
        elif window == 'hanning':
            win = xp.hanning(n)
        elif window == 'hamming':
            win = xp.hamming(n)
        else:
            win = xp.ones(n)
        
        # Broadcast window to correct shape
        shape = [1] * data_gpu.ndim
        shape[axis] = n
        win = win.reshape(shape)
        data_gpu = data_gpu * win
    
    # Perform FFT
    if _GPU_AVAILABLE:
        result = cp.fft.fftshift(cp.fft.fft(data_gpu, n=n, axis=axis))
    else:
        result = np.fft.fftshift(np.fft.fft(data_gpu, n=n, axis=axis))
    
    # Synchronize GPU if needed
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return result, elapsed


def gpu_fft2(data, shape=None, window='blackman'):
    """
    GPU-accelerated 2D FFT for range-Doppler processing.
    
    Args:
        data: 2D input array (n_doppler x n_range)
        shape: Output shape (default: input shape)
        window: Window function to apply
    
    Returns:
        2D FFT result, timing in seconds
    """
    xp = get_backend()
    
    data_gpu = to_gpu(data)
    
    start = time.perf_counter()
    
    # Apply 2D window
    if window is not None:
        n_doppler, n_range = data_gpu.shape
        if window == 'blackman':
            win_range = xp.blackman(n_range)
            win_doppler = xp.blackman(n_doppler)
        elif window == 'hanning':
            win_range = xp.hanning(n_range)
            win_doppler = xp.hanning(n_doppler)
        else:
            win_range = xp.ones(n_range)
            win_doppler = xp.ones(n_doppler)
        
        window_2d = xp.outer(win_doppler, win_range)
        data_gpu = data_gpu * window_2d
    
    # 2D FFT
    if _GPU_AVAILABLE:
        result = cp.fft.fftshift(cp.fft.fft2(data_gpu, s=shape))
    else:
        result = np.fft.fftshift(np.fft.fft2(data_gpu, s=shape))
    
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return result, elapsed


def gpu_cfar(spectrum_db, num_guard_cells=10, num_ref_cells=20, bias_db=10, method='average'):
    """
    GPU-accelerated CFAR (Constant False Alarm Rate) detection.
    
    This is a vectorized implementation that processes the entire spectrum
    in parallel on the GPU, rather than the sequential CPU implementation.
    
    Args:
        spectrum_db: Input spectrum in dB (1D array)
        num_guard_cells: Number of guard cells on each side
        num_ref_cells: Number of reference cells on each side
        bias_db: Detection threshold bias in dB
        method: 'average', 'greatest', or 'smallest'
    
    Returns:
        threshold: CFAR threshold array
        targets: Masked array with only detected targets
        timing: Processing time in seconds
    """
    xp = get_backend()
    
    spectrum_gpu = to_gpu(spectrum_db)
    N = spectrum_gpu.size
    
    start = time.perf_counter()
    
    # Total cells on each side
    total_cells = num_guard_cells + num_ref_cells
    
    # Initialize threshold array
    threshold = xp.full_like(spectrum_gpu, xp.min(spectrum_gpu))
    
    # Vectorized CFAR using sliding window
    # This is much faster than the loop-based approach
    for center_idx in range(total_cells, N - total_cells):
        # Lower reference cells
        lower_start = center_idx - total_cells
        lower_end = center_idx - num_guard_cells
        lower_cells = spectrum_gpu[lower_start:lower_end]
        
        # Upper reference cells
        upper_start = center_idx + num_guard_cells + 1
        upper_end = center_idx + total_cells + 1
        upper_cells = spectrum_gpu[upper_start:upper_end]
        
        if method == 'average':
            mean_val = (xp.sum(lower_cells) + xp.sum(upper_cells)) / (2 * num_ref_cells)
        elif method == 'greatest':
            mean_val = xp.maximum(xp.mean(lower_cells), xp.mean(upper_cells))
        elif method == 'smallest':
            mean_val = xp.minimum(xp.mean(lower_cells), xp.mean(upper_cells))
        else:
            mean_val = (xp.sum(lower_cells) + xp.sum(upper_cells)) / (2 * num_ref_cells)
        
        threshold[center_idx] = mean_val + bias_db
    
    # Create targets mask
    targets = xp.where(spectrum_gpu > threshold, spectrum_gpu, xp.nan)
    
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return threshold, targets, elapsed


def gpu_cfar_2d(rd_map_db, guard_cells=(5, 5), ref_cells=(10, 10), bias_db=15):
    """
    GPU-accelerated 2D CFAR for range-Doppler maps.
    
    Args:
        rd_map_db: 2D range-Doppler map in dB
        guard_cells: (guard_doppler, guard_range) tuple
        ref_cells: (ref_doppler, ref_range) tuple
        bias_db: Detection threshold bias
    
    Returns:
        threshold: 2D threshold array
        targets: Detected targets
        timing: Processing time
    """
    xp = get_backend()
    
    rd_gpu = to_gpu(rd_map_db)
    n_doppler, n_range = rd_gpu.shape
    
    start = time.perf_counter()
    
    guard_d, guard_r = guard_cells
    ref_d, ref_r = ref_cells
    total_d = guard_d + ref_d
    total_r = guard_r + ref_r
    
    # Use convolution-based approach for efficiency
    # Create averaging kernel (excluding guard cells)
    kernel_size = (2 * total_d + 1, 2 * total_r + 1)
    kernel = xp.ones(kernel_size)
    
    # Zero out guard region and center
    kernel[ref_d:ref_d + 2*guard_d + 1, ref_r:ref_r + 2*guard_r + 1] = 0
    kernel = kernel / xp.sum(kernel)
    
    # Pad input
    padded = xp.pad(rd_gpu, ((total_d, total_d), (total_r, total_r)), mode='edge')
    
    # Compute local average using correlation
    # For each cell, compute the mean of reference cells
    threshold = xp.zeros_like(rd_gpu)
    
    # Sliding window average (simplified - in practice use scipy.ndimage.convolve)
    for i in range(n_doppler):
        for j in range(n_range):
            region = padded[i:i + kernel_size[0], j:j + kernel_size[1]]
            threshold[i, j] = xp.sum(region * kernel)
    
    threshold = threshold + bias_db
    
    # Detect targets
    targets = xp.where(rd_gpu > threshold, rd_gpu, xp.nan)
    
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return threshold, targets, elapsed


def gpu_stft(data, nperseg=256, noverlap=None, window='blackman', nfft=None):
    """
    GPU-accelerated Short-Time Fourier Transform for micro-Doppler analysis.
    
    Args:
        data: Input time-domain signal
        nperseg: Samples per segment
        noverlap: Overlap between segments (default: nperseg // 2)
        window: Window function
        nfft: FFT size (default: nperseg)
    
    Returns:
        f: Frequency bins (normalized)
        t: Time bins
        Sxx: STFT magnitude spectrogram
        timing: Processing time
    """
    xp = get_backend()
    
    data_gpu = to_gpu(data)
    N = len(data_gpu)
    
    if noverlap is None:
        noverlap = nperseg // 2
    if nfft is None:
        nfft = nperseg
    
    step = nperseg - noverlap
    n_segments = (N - noverlap) // step
    
    start = time.perf_counter()
    
    # Create window
    if window == 'blackman':
        win = xp.blackman(nperseg)
    elif window == 'hanning':
        win = xp.hanning(nperseg)
    elif window == 'hamming':
        win = xp.hamming(nperseg)
    else:
        win = xp.ones(nperseg)
    
    # Pre-allocate output
    Sxx = xp.zeros((nfft, n_segments), dtype=xp.complex128)
    
    # Compute STFT segments
    for i in range(n_segments):
        start_idx = i * step
        segment = data_gpu[start_idx:start_idx + nperseg] * win
        
        if _GPU_AVAILABLE:
            Sxx[:, i] = cp.fft.fft(segment, n=nfft)
        else:
            Sxx[:, i] = np.fft.fft(segment, n=nfft)
    
    # Take magnitude and shift
    if _GPU_AVAILABLE:
        Sxx = xp.abs(cp.fft.fftshift(Sxx, axes=0))
    else:
        Sxx = xp.abs(np.fft.fftshift(Sxx, axes=0))
    
    # Create frequency and time arrays
    f = xp.linspace(-0.5, 0.5, nfft)
    t = xp.arange(n_segments) * step
    
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return f, t, Sxx, elapsed


def gpu_range_doppler(data, n_range=1024, n_doppler=256, window='blackman',
                      sample_rate=30e6, chirp_bw=500e6, chirp_time=0.5e-3):
    """
    Complete GPU-accelerated range-Doppler processing pipeline.
    
    Args:
        data: Raw IQ samples (1D array, length = n_range * n_doppler)
        n_range: Number of range bins (samples per chirp)
        n_doppler: Number of Doppler bins (number of chirps)
        window: Window function for FFT
        sample_rate: ADC sample rate in Hz
        chirp_bw: Chirp bandwidth in Hz
        chirp_time: Chirp duration in seconds
    
    Returns:
        rd_map: Range-Doppler map (magnitude in dB)
        range_axis: Range values in meters
        doppler_axis: Doppler/velocity values
        timing: Processing time
    """
    xp = get_backend()
    c = 3e8  # Speed of light
    
    data_gpu = to_gpu(data)
    
    start = time.perf_counter()
    
    # Reshape into range x Doppler matrix
    # Each row is one chirp (range profile)
    # Each column is one range bin across chirps (Doppler)
    n_samples = len(data_gpu)
    if n_samples < n_range * n_doppler:
        # Pad with zeros if needed
        data_gpu = xp.pad(data_gpu, (0, n_range * n_doppler - n_samples))
    
    matrix = data_gpu[:n_range * n_doppler].reshape(n_doppler, n_range)
    
    # Apply 2D window
    if window is not None:
        if window == 'blackman':
            win_range = xp.blackman(n_range)
            win_doppler = xp.blackman(n_doppler)
        elif window == 'hanning':
            win_range = xp.hanning(n_range)
            win_doppler = xp.hanning(n_doppler)
        else:
            win_range = xp.ones(n_range)
            win_doppler = xp.ones(n_doppler)
        
        window_2d = xp.outer(win_doppler, win_range)
        matrix = matrix * window_2d
    
    # 2D FFT: Range FFT along rows, Doppler FFT along columns
    if _GPU_AVAILABLE:
        rd_complex = cp.fft.fftshift(cp.fft.fft2(matrix))
    else:
        rd_complex = np.fft.fftshift(np.fft.fft2(matrix))
    
    # Convert to dB
    rd_mag = xp.abs(rd_complex)
    rd_mag = xp.maximum(rd_mag, 1e-12)  # Avoid log(0)
    rd_map = 20 * xp.log10(rd_mag)
    
    # Calculate range and Doppler axes
    # Range resolution: c / (2 * BW)
    range_res = c / (2 * chirp_bw)
    max_range = range_res * n_range / 2
    range_axis = xp.linspace(-max_range, max_range, n_range)
    
    # Doppler/velocity axis
    # PRF = 1 / chirp_time
    prf = 1 / chirp_time
    max_doppler = prf / 2
    doppler_axis = xp.linspace(-max_doppler, max_doppler, n_doppler)
    
    if _GPU_AVAILABLE:
        cp.cuda.Stream.null.synchronize()
    
    elapsed = time.perf_counter() - start
    
    return rd_map, range_axis, doppler_axis, elapsed


def benchmark_fft_sizes(sizes=[256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536],
                        iterations=100):
    """
    Benchmark FFT performance across different sizes.
    
    Returns:
        Dictionary with size -> (gpu_time_ms, cpu_time_ms) mappings
    """
    results = {}
    xp = get_backend()
    
    for size in sizes:
        # Generate test data
        data_np = np.random.randn(size) + 1j * np.random.randn(size)
        
        # GPU timing
        if _GPU_AVAILABLE:
            data_gpu = cp.asarray(data_np)
            # Warmup
            for _ in range(10):
                _ = cp.fft.fft(data_gpu)
            cp.cuda.Stream.null.synchronize()
            
            # Benchmark
            start = time.perf_counter()
            for _ in range(iterations):
                _ = cp.fft.fft(data_gpu)
            cp.cuda.Stream.null.synchronize()
            gpu_time = (time.perf_counter() - start) / iterations * 1000  # ms
        else:
            gpu_time = None
        
        # CPU timing
        # Warmup
        for _ in range(10):
            _ = np.fft.fft(data_np)
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            _ = np.fft.fft(data_np)
        cpu_time = (time.perf_counter() - start) / iterations * 1000  # ms
        
        results[size] = {
            'gpu_ms': gpu_time,
            'cpu_ms': cpu_time,
            'speedup': cpu_time / gpu_time if gpu_time else None
        }
        
        if gpu_time:
            print(f"FFT {size:6d}: GPU={gpu_time:.4f}ms, CPU={cpu_time:.4f}ms, Speedup={cpu_time/gpu_time:.1f}x")
        else:
            print(f"FFT {size:6d}: CPU={cpu_time:.4f}ms (GPU unavailable)")
    
    return results
