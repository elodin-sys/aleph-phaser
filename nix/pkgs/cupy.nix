# CuPy - GPU-accelerated NumPy-compatible array library
#
# CuPy provides GPU-accelerated computing using CUDA.
# On Jetson Orin NX, this enables dramatic speedups for:
#   - FFT operations (10-100x faster)
#   - Matrix operations
#   - Signal processing (CFAR, STFT, etc.)
#
# Usage in Python:
#   import cupy as cp
#   gpu_array = cp.array([1, 2, 3])
#   fft_result = cp.fft.fft(gpu_array)

{ lib
, python3
, fetchurl
, autoPatchelfHook
, stdenv
}:

let
  # Fetch the pre-built wheel for aarch64 + CUDA 12.x + Python 3.12
  wheelSrc = fetchurl {
    url = "https://files.pythonhosted.org/packages/12/c5/7e7fc4816d0de0154e5d9053242c3a08a0ca8b43ee656a6f7b3b95055a7b/cupy_cuda12x-13.6.0-cp312-cp312-manylinux2014_aarch64.whl";
    sha256 = "a6970ceefe40f9acbede41d7fe17416bd277b1bd2093adcde457b23b578c5a59";
  };
in
python3.pkgs.buildPythonPackage rec {
  pname = "cupy-cuda12x";
  version = "13.6.0";
  format = "wheel";

  src = wheelSrc;

  nativeBuildInputs = [
    autoPatchelfHook
  ];

  # Runtime dependencies
  buildInputs = [
    stdenv.cc.cc.lib  # libstdc++
  ];

  propagatedBuildInputs = with python3.pkgs; [
    numpy
    fastrlock
  ];

  # The wheel contains CUDA bindings that need the JetPack CUDA runtime
  # autoPatchelfHook will handle most library patching
  autoPatchelfIgnoreMissingDeps = [
    "libcuda.so.1"
    "libcudart.so.12"
    "libcublas.so.12"
    "libcufft.so.11"
    "libcurand.so.10"
    "libcusparse.so.12"
    "libcusolver.so.11"
    "libnvrtc.so.12"
    "libcudnn.so.8"
    "libcudnn.so.9"
    "libnccl.so.2"
  ];

  # Skip tests - they require GPU hardware
  doCheck = false;
  
  # Skip import check during build (no GPU available in build sandbox)
  pythonImportsCheck = [ ];

  meta = with lib; {
    description = "CuPy: NumPy & SciPy for GPU (CUDA 12.x)";
    homepage = "https://cupy.dev/";
    license = licenses.mit;
    maintainers = [ ];
    platforms = [ "aarch64-linux" ];
  };
}
