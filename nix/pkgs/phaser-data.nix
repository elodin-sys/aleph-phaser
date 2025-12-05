# Phaser Data Files Package
#
# Deploys filter files and other data to /opt/phaser on the Aleph.
# This establishes a pattern for deploying local data files.
#
# To add new data files:
# 1. Add files to data/filters/ or create a new subdirectory in data/
# 2. Update the 'src' or add to installPhase below
# 3. Reference in scripts via /opt/phaser/<subdir>/<filename>

{ stdenv, lib, fetchurl }:

let
  # Download filter files from ADI's pyadi-iio repository
  # This ensures reproducible builds without needing local files
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

  # No src needed - we use fetchurl above
  dontUnpack = true;
  dontBuild = true;
  dontConfigure = true;

  installPhase = ''
    mkdir -p $out/share/phaser/filters
    cp ${lte20} $out/share/phaser/filters/LTE20_MHz.ftr
    cp ${lte10} $out/share/phaser/filters/LTE10_MHz.ftr
    cp ${lte5} $out/share/phaser/filters/LTE5_MHz.ftr
  '';

  meta = with lib; {
    description = "Phaser data files (filters, calibration, etc.)";
    license = licenses.mit;
    platforms = platforms.all;
  };
}
