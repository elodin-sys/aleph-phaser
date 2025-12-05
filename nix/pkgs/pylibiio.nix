{ lib
, python3
, fetchPypi
, libiio
, pkg-config
}:

let
  # libiio in nixpkgs 25.05 has split outputs
  # The library files are in the 'lib' output, not the default output
  libiioLib = lib.getLib libiio;
in
python3.pkgs.buildPythonPackage rec {
  pname = "pylibiio";
  version = "0.25";
  
  src = fetchPypi {
    inherit pname version;
    sha256 = "sha256-8mFasgCT7IyodBfx4439yhuqIacZMo9LJ9KMmbHSPrU=";
  };

  # pylibiio needs the libiio C library
  buildInputs = [ libiio ];
  nativeBuildInputs = [ pkg-config ];
  
  # Runtime dependencies - ensure libiio is available at runtime
  propagatedBuildInputs = [ libiio ];
  
  # The setup.py checks for libiio but we need to help it find it
  preBuild = ''
    # Set environment variables to help setup.py find libiio
    # Use libiioLib which points to the lib output
    export CFLAGS="-I${libiio.dev or libiio}/include"
    export LDFLAGS="-L${libiioLib}/lib"
    export LD_LIBRARY_PATH="${libiioLib}/lib:$LD_LIBRARY_PATH"
    export LIBRARY_PATH="${libiioLib}/lib:$LIBRARY_PATH"
    
    # Patch setup.py to remove the library check - we're providing it via Nix
    # The check is in the custom install command
    sed -i 's/self\._check_libiio_installed()/pass/' setup.py
  '';
  
  # Ensure libiio library can be found at runtime
  postInstall = ''
    # Debug: show what's available
    echo "Looking for libiio in: ${libiioLib}/lib"
    ls -la ${libiioLib}/lib/ || echo "lib dir not found"
    
    # Find the actual libiio library file
    LIBIIO_LIB=""
    for f in ${libiioLib}/lib/libiio.so.0 ${libiioLib}/lib/libiio.so ${libiioLib}/lib/libiio.so.*; do
      if [ -f "$f" ]; then
        LIBIIO_LIB="$f"
        break
      fi
    done
    
    if [ -z "$LIBIIO_LIB" ]; then
      echo "ERROR: Could not find libiio.so in ${libiioLib}/lib"
      echo "Checking other locations..."
      
      # Try the out output
      for f in ${libiio.out or libiio}/lib/libiio.so.0 ${libiio.out or libiio}/lib/libiio.so; do
        if [ -f "$f" ]; then
          LIBIIO_LIB="$f"
          echo "Found in out: $LIBIIO_LIB"
          break
        fi
      done
    fi
    
    if [ -z "$LIBIIO_LIB" ]; then
      echo "ERROR: Could not find libiio.so anywhere"
      exit 1
    fi
    
    echo "Found libiio at: $LIBIIO_LIB"
    
    # Patch the installed iio.py to use the absolute path
    for pyfile in $out/lib/python*/site-packages/iio.py; do
      if [ -f "$pyfile" ]; then
        echo "Patching $pyfile to use libiio path: $LIBIIO_LIB"
        
        # Use substituteInPlace for better Nix integration
        substituteInPlace "$pyfile" \
          --replace-quiet "find_library('iio')" "'$LIBIIO_LIB'" \
          --replace-quiet "find_library('libiio')" "'$LIBIIO_LIB'" \
          --replace-quiet "find_library(_iiolib)" "'$LIBIIO_LIB'" || true
          
        # Verify the patch worked
        if grep -q "$LIBIIO_LIB" "$pyfile"; then
          echo "Successfully patched iio.py"
        else
          echo "WARNING: Patch may not have applied correctly"
          grep -n "find_library\|libiio" "$pyfile" || true
        fi
      fi
    done
    
    # Create references to prevent garbage collection
    mkdir -p $out/nix-support
    echo "${libiio}" >> $out/nix-support/propagated-native-build-inputs
    echo "${libiioLib}" >> $out/nix-support/propagated-native-build-inputs
  '';

  # Disable import check as it requires the full environment
  pythonImportsCheck = [ ];

  meta = with lib; {
    description = "Python bindings for libiio";
    homepage = "https://github.com/analogdevicesinc/libiio";
    license = licenses.lgpl21Plus;
    maintainers = [ ];
    platforms = platforms.linux;
  };
}
