{
  nixConfig = {
    extra-substituters = ["https://elodin-nix-cache.s3.us-west-2.amazonaws.com"];
    extra-trusted-public-keys = [
      "elodin-cache-1:vvbmIQvTOjcBjIs8Ri7xlT2I3XAmeJyF5mNlWB+fIwM="
    ];
  };

  inputs = {
    aleph.url = "github:elodin-sys/elodin/bd596cba681d06bc04088f78e7c16e2ff154c7ba?dir=aleph";
    flake-utils.follows = "aleph/flake-utils";
    nixpkgs.follows = "aleph/nixpkgs";
    self.submodules = true;
  };

  outputs = {
    nixpkgs,
    aleph,
    self,
    ...
  }: rec {
    system = "aarch64-linux";
    
    # Define custom overlay for our packages
    overlays.default = final: prev: {
      pylibiio = final.callPackage ./nix/pkgs/pylibiio.nix {};
      pyadi-iio = final.callPackage ./nix/pkgs/pyadi-iio.nix {
        pylibiio = final.pylibiio;
      };
      test-plutosdr = final.callPackage ./nix/pkgs/test-plutosdr.nix {
        pylibiio = final.pylibiio;
        pyadiIio = final.pyadi-iio;  # Map the package name correctly
      };
      # Phaser data: pass local data directory, and scripts for on-device demos
      phaser-data = final.callPackage ./nix/pkgs/phaser-data.nix {
        localDataSrc = ./data;
        scriptsSrc = ./scripts;
      };
      # Extend Python packages to include our custom packages
      python3 = prev.python3.override {
        packageOverrides = pyfinal: pyprev: {
          cupy = final.callPackage ./nix/pkgs/cupy.nix {};
        };
      };
      python3Packages = final.python3.pkgs;
    };
    
    nixosModules.default = {config, pkgs, ...}: {
      imports = with aleph.nixosModules; [
        # hardware modules
        jetpack # core module required to make jetpack-nixos work
        hardware # aleph specific hardware module, brings in the forked-kernel and device tree
        fs # module that allows building sd-card images compatible with aleph

        # networking modules
        # usb-eth # sets up the usb ethernet gadget present on aleph
        wifi # sets up wifi using iwd

        # default tooling
        aleph-setup # a setup tool that guides you through setting up wifi and a user on first login
        aleph-base # a set of default configuration options that make developing on aleph easier
        aleph-dev # a default set of packages like cuda, opencv, and git that make developing on aleph easier
        
        # Import our custom modules
        ./nix/modules/plutosdr.nix
      ];

      # overlays required to get elodin and nvidia packages
      # NOTE: Order matters! aleph.overlays.jetpack must come BEFORE aleph.overlays.default
      # so that aleph's gitReposOverlay properly overrides nvidia-jetpack with custom device tree sources
      nixpkgs.overlays = [
        aleph.overlays.jetpack  # Apply jetpack overlay first
        aleph.overlays.default  # Then apply aleph overlay (includes custom gitRepos for devicetree)
        overlays.default        # Add our custom overlay last
      ];

      system.stateVersion = "25.05";

      i18n.supportedLocales = [(config.i18n.defaultLocale + "/UTF-8")];

      # Enable PlutoSDR support with GPU demos
      services.plutosdr = {
        enable = true;
        users = [ "aleph-phaser" ];  # Add our user to plugdev/dialout groups
        enableGnuRadio = true; # long build time and heavy dependencies
        enableGpuDemos = true; # Enable GPU-accelerated radar demos
      };

      # Additional system packages for Phaser development
      environment.systemPackages = with pkgs; [
        # Development tools
        git
        vim
        tmux
        htop
        
        # Network tools for testing
        wget
        curl
        nmap
        iperf3
        
        # USB and hardware debugging
        usbutils
        pciutils
        lshw
        
        # Python development
        python3
        
        # Build tools (in case we need to compile anything)
        gcc
        gnumake
        cmake
        pkg-config
      ];

      users.users.aleph-phaser = {
        isNormalUser = true;
        openssh.authorizedKeys.keys = [
            # contents of ~/.ssh/aleph-phaser.pub:
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDwxggwJgH427UbKZcaw2sHpO+Roa+0aMfN27W0eVwQ9 aleph-phaser"
        ];
        extraGroups = [
            "wheel"
            "dialout"
            "video"
            "audio"
            "networkmanager"
            "podman"
            # Note: plugdev is added automatically by the plutosdr module
        ];
        shell = "/run/current-system/sw/bin/bash";
      };

      services.openssh.enable = true; # enable ssh
      services.openssh.settings = {
        PasswordAuthentication = true;
        PubkeyAuthentication = true;
        PermitRootLogin = "yes";
      };
      security.sudo.wheelNeedsPassword = false;
      nix.settings.trusted-users = ["@wheel" "root" "ubuntu" "aleph-phaser"];

      networking.firewall.enable = false;
    };
    # sets up two different nixos systems default and installer
    # installer is setup to be flashed to a usb drive, and contains the
    # aleph-installer tool. This tool lets you install the system to the nvme
    # drive
    nixosConfigurations = {
      default = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [nixosModules.default];
      };
    };
    packages.aarch64-linux = {
      sdimage = aleph.packages.aarch64-linux.sdimage;
      # the toplevel config, this allows you to use the deploy.sh script:
      default = nixosConfigurations.default.config.system.build.toplevel;
    };
  };
}
