{ lib
, python312
, stdenv
, fetchurl
, adafruit-circuitpython-typing
, adafruit-platformdetect
, adafruit-pureio
}:

python312.pkgs.buildPythonPackage rec {
  pname = "adafruit-blinka";
  version = "8.62.0";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/89/a8/fa70af6c9d6bfb9d2688f4610a33719f56a3419e9a1f69aa2dae299007f8/adafruit_blinka-8.62.0-py3-none-any.whl";
    hash = "sha256-IiNPTI+oylcXzliK6Q9xuVvPKGn4VbtHpi6drMaxCZo=";
  };

  format = "wheel";

  propagatedBuildInputs = [
    adafruit-platformdetect
    adafruit-pureio
    python312.pkgs.pyftdi
    python312.pkgs.binho-host-adapter
    python312.pkgs.sysv-ipc
    python312.pkgs.toml
    adafruit-circuitpython-typing
  ];

  doCheck = false; # Skip tests for vendored package

  meta = with lib; {
    description = "CircuitPython API for Blinka";
    homepage = "https://github.com/adafruit/Adafruit_Blinka";
    license = licenses.mit;
    platforms = platforms.linux;
  };
} 
