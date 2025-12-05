# Phaser Data Files and Scripts Package
#
# Deploys filter files, data, and demo scripts to /opt/phaser on the Aleph.
# Supports:
#   - URL-fetched files (filters from ADI GitHub)
#   - Local files (calibration data from data/ directory)
#   - Demo scripts (CPU and GPU demos from scripts/ directory)
#
# Usage:
#   /opt/phaser/filters/LTE20_MHz.ftr
#   /opt/phaser/calibration/example_gain_cal.json
#   /opt/phaser/scripts/cpu-demos/aleph_minimal_example.py
#   /opt/phaser/scripts/gpu-demos/run_gpu_demo.py

{ stdenv, lib, fetchurl, localDataSrc ? null, scriptsSrc ? null }:

let
  # Download filter files from ADI's pyadi-iio repository
  # These are standard files that don't change often
  lte20 = fetchurl {
    url = "https://raw.githubusercontent.com/analogdevicesinc/pyadi-iio/main/examples/phaser/LTE20_MHz.ftr";
    sha256 = "1qzdvxhfhnq3ir035xw7asrxb4jbgbg8a9xpy8mafv8y04p49r75";
  };
  lte10 = fetchurl {
    url = "https://raw.githubusercontent.com/analogdevicesinc/pyadi-iio/main/examples/phaser/LTE10_MHz.ftr";
    sha256 = "0n088yrki5ylvglmnrh2s62nb1fjj6vy6ghfcsaajwa51bg2pmh7";
  };
  lte5 = fetchurl {
    url = "https://raw.githubusercontent.com/analogdevicesinc/pyadi-iio/main/examples/phaser/LTE5_MHz.ftr";
    sha256 = "1r9bf36ispcqy9rsp46khk5lwrbbb9i5ldc32nlpx3kyfigw6dip";
  };
in
stdenv.mkDerivation {
  pname = "phaser-data";
  version = "1.0.0";

  # No src needed for URL-only approach, but we accept local data
  src = localDataSrc;
  dontUnpack = localDataSrc == null && scriptsSrc == null;
  dontBuild = true;
  dontConfigure = true;

  installPhase = ''
    mkdir -p $out/share/phaser/filters
    mkdir -p $out/share/phaser/calibration
    mkdir -p $out/share/phaser/scripts

    # Install URL-fetched filter files
    cp ${lte20} $out/share/phaser/filters/LTE20_MHz.ftr
    cp ${lte10} $out/share/phaser/filters/LTE10_MHz.ftr
    cp ${lte5} $out/share/phaser/filters/LTE5_MHz.ftr

    # Install local data files if source is provided
    ${lib.optionalString (localDataSrc != null) ''
      echo "Installing local data files..."
      
      # Copy local filter files (if any custom ones exist)
      if [ -d ${localDataSrc}/filters ]; then
        for f in ${localDataSrc}/filters/*; do
          if [ -f "$f" ]; then
            # Don't overwrite URL-fetched files unless local version exists
            cp -n "$f" $out/share/phaser/filters/ || cp "$f" $out/share/phaser/filters/
          fi
        done
      fi
      
      # Copy calibration files
      if [ -d ${localDataSrc}/calibration ]; then
        cp -r ${localDataSrc}/calibration/* $out/share/phaser/calibration/
        echo "Installed calibration files:"
        ls -la $out/share/phaser/calibration/
      fi

      # Support for additional data directories
      for dir in waveforms configs; do
        if [ -d "${localDataSrc}/$dir" ]; then
          mkdir -p $out/share/phaser/$dir
          cp -r ${localDataSrc}/$dir/* $out/share/phaser/$dir/
          echo "Installed $dir files"
        fi
      done
    ''}

    # Install demo scripts if provided
    ${lib.optionalString (scriptsSrc != null) ''
      echo "Installing demo scripts..."
      
      # Copy CPU demos
      if [ -d ${scriptsSrc}/cpu-demos ]; then
        mkdir -p $out/share/phaser/scripts/cpu-demos
        cp -r ${scriptsSrc}/cpu-demos/* $out/share/phaser/scripts/cpu-demos/
        chmod +x $out/share/phaser/scripts/cpu-demos/*.py 2>/dev/null || true
        echo "Installed CPU demo scripts"
      fi
      
      # Copy GPU demos
      if [ -d ${scriptsSrc}/gpu-demos ]; then
        mkdir -p $out/share/phaser/scripts/gpu-demos
        cp -r ${scriptsSrc}/gpu-demos/* $out/share/phaser/scripts/gpu-demos/
        chmod +x $out/share/phaser/scripts/gpu-demos/*.py 2>/dev/null || true
        echo "Installed GPU demo scripts"
      fi
      
      # Copy Mac demos (for reference, though they run on Mac not Aleph)
      if [ -d ${scriptsSrc}/mac ]; then
        mkdir -p $out/share/phaser/scripts/mac
        cp -r ${scriptsSrc}/mac/* $out/share/phaser/scripts/mac/
        echo "Installed Mac demo scripts (for reference)"
      fi
    ''}

    echo "=== Phaser Data Installation Complete ==="
    echo "Filters:"
    ls -la $out/share/phaser/filters/
    echo "Calibration:"
    ls -la $out/share/phaser/calibration/ 2>/dev/null || echo "(none)"
    echo "Scripts:"
    ls -la $out/share/phaser/scripts/ 2>/dev/null || echo "(none)"
  '';

  meta = with lib; {
    description = "Phaser data files (filters, calibration) and demo scripts";
    license = licenses.mit;
    platforms = platforms.all;
  };
}
