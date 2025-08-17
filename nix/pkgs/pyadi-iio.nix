{ lib
, python3
, fetchPypi
, pylibiio
}:

python3.pkgs.buildPythonPackage rec {
  pname = "pyadi-iio";
  version = "0.0.17";
  
  # Use pyproject format for packages without setup.py
  format = "pyproject";
  
  src = fetchPypi {
    pname = "pyadi_iio";  # Note: underscore in PyPI name
    inherit version;
    sha256 = "sha256-cXSboqGltl4rrxyk8Pi8vpeDIGKkN3gMw0+HkaaJumU=";
  };

  nativeBuildInputs = with python3.pkgs; [
    setuptools
    wheel
  ];

  propagatedBuildInputs = with python3.pkgs; [
    numpy
    paramiko  # For remote device access
  ] ++ [
    pylibiio  # Our custom packaged pylibiio
  ];

  # Disable tests as they require hardware
  doCheck = false;

  # Disable import check as it requires libiio at build time
  # The library will be available when used in the actual environment
  pythonImportsCheck = [ ];

  meta = with lib; {
    description = "Python bindings for ADI hardware using IIO";
    homepage = "https://github.com/analogdevicesinc/pyadi-iio";
    license = licenses.bsd3;
    maintainers = [ ];
    platforms = platforms.linux;
  };
}
