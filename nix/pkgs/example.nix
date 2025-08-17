{ lib
, python312
, stdenv
, serviceType ? "fcs"  # "fcs" or "missile"
, adafruit-pureio
, adafruit-platformdetect
, adafruit-blinka
}:

let
  pythonEnv = python312.withPackages (ps: with ps; [
    grpcio
    grpcio-tools
    protobuf
    netifaces
    hidapi
    adafruit-pureio
    adafruit-platformdetect
    adafruit-blinka
  ]);
  
  # Service configuration
  serviceConfig = {
    fcs = {
      name = "fcs-service";
      description = "Guardian Fire Control System Service";
      script = "fcs_service.py";
      binName = "fcs-service";
    };
    missile = {
      name = "missile-service";
      description = "Guardian Missile Service";
      script = "missile_service.py";
      binName = "missile-service";
    };
  };
  
  config = serviceConfig.${serviceType};
in

python312.pkgs.buildPythonApplication {
  pname = config.name;
  version = "0.1.4";
  format = "other";

  src = ../../.;

  buildInputs = with python312.pkgs; [
    grpcio
    grpcio-tools
    protobuf
    netifaces
    hidapi
    adafruit-pureio
    adafruit-platformdetect
    adafruit-blinka
  ];

  buildPhase = ''
    # Compile Protocol Buffers
    python -m grpc_tools.protoc \
      --proto_path=proto \
      --python_out=. \
      --grpc_python_out=. \
      proto/message.proto
  '';

  installPhase = ''
    # Create directory structure
    mkdir -p $out/bin
    mkdir -p $out/lib/${python312.libPrefix}/site-packages/fcs

    # Copy Python files
    cp *.py $out/lib/${python312.libPrefix}/site-packages/fcs/
    cp -r proto $out/lib/${python312.libPrefix}/site-packages/fcs/
    cp message_pb2*.py $out/lib/${python312.libPrefix}/site-packages/fcs/

    # Create wrapper script that uses the Python environment with dependencies
    cat > $out/bin/${config.binName} <<EOF
    #!${stdenv.shell}
    export PYTHONPATH=$out/lib/${python312.libPrefix}/site-packages:${pythonEnv}/lib/${python312.libPrefix}/site-packages
    exec ${pythonEnv}/bin/python $out/lib/${python312.libPrefix}/site-packages/fcs/${config.script}
    EOF
    chmod +x $out/bin/${config.binName}
  '';

  meta = with lib; {
    description = config.description;
    platforms = platforms.linux;
  };
} 
