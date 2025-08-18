{ lib
, stdenv
, python3
, makeWrapper
, libiio
, pylibiio
, pyadiIio  # Note: renamed to use camelCase
}:

let
  pythonEnv = python3.withPackages (ps: [
    # Core dependencies from our test script
    ps.numpy
    ps.matplotlib
    pylibiio    # Our custom package
    pyadiIio    # Our custom package
  ]);
in
stdenv.mkDerivation rec {
  pname = "test-plutosdr";
  version = "1.0.0";
  
  # Use the local script from our repository
  src = ../../scripts;
  
  nativeBuildInputs = [ makeWrapper ];
  
  # No build phase needed for a simple script
  dontBuild = true;
  
  installPhase = ''
    runHook preInstall
    
    # Create the output directory
    mkdir -p $out/bin
    
    # Copy the script and rename it
    cp test_plutosdr.py $out/bin/test-plutosdr
    
    # Make it executable
    chmod +x $out/bin/test-plutosdr
    
    # Wrap the script with the correct Python environment
    wrapProgram $out/bin/test-plutosdr \
      --prefix PATH : "${pythonEnv}/bin:${libiio}/bin" \
      --set MPLBACKEND "Agg"
    
    runHook postInstall
  '';
  
  meta = with lib; {
    description = "PlutoSDR connection and functionality test tool";
    longDescription = ''
      A comprehensive test script for validating PlutoSDR connectivity
      and pyadi-iio functionality on the Aleph platform. Tests USB detection,
      IIO context access, and basic SDR operations.
    '';
    license = licenses.mit;
    maintainers = [ ];
    platforms = platforms.linux;
  };
}
