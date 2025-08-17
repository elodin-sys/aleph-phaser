{
  nixConfig = {
    extra-substituters = ["http://ci-arm1.elodin.dev:5000"];
    extra-trusted-public-keys = [
      "builder-cache-1:q7rDGIQgkg1nsxNEg7mHN1kEDuxPmJhQpuIXCCwLj8E="
    ];
  };

  inputs = {
    aleph.url = "github:elodin-sys/elodin?ref=v0.14.2&dir=images/aleph";
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
    nixosModules.default = {config, ...}: {
      imports = with aleph.nixosModules; [
        # hardware modules
        jetpack # core module required to make jetpack-nixos work
        hardware # aleph specific hardware module, brings in the forked-kernel and device tree
        fs # module that allows building sd-card images compatible with aleph

        # networking modules
        usb-eth # sets up the usb ethernet gadget present on aleph
        wifi # sets up wifi using iwd

        # default tooling
        aleph-setup # a setup tool that guides you through setting up wifi and a user on first login
        aleph-base # a set of default configuration options that make developing on aleph easier
        aleph-dev # a default set of packages like cuda, opencv, and git that make developing on aleph easier
      ];

      # overlays required to get elodin and nvidia packages
      nixpkgs.overlays = [
        aleph.overlays.default
        aleph.overlays.jetpack
      ];

      system.stateVersion = "24.11";

      i18n.supportedLocales = [(config.i18n.defaultLocale + "/UTF-8")];

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
