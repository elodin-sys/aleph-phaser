Question:

I'm looking for examples of other software engineers who've attempted developing connecting a ADALM PLUTO SDR to something running NixOS, in my case an Nvidia Orin NX edge computer, and in particular what the configurations and libraries were needed, what udev rules and permissions were required, etc

Answer:

Got you. Here’s a compact “known-good” recipe for getting an ADALM-PLUTO talking to NixOS (including on Jetson/Orin hardware), plus examples from others who’ve done parts of this and the exact udev rules you’ll want.

# What others have done (and what we can learn)

* **Analog Devices’ official guidance**: Pluto on Linux needs a few kernel modules and a udev rules file (grants group access, and tells ModemManager to ignore the device). The page lists required modules (`cdc_acm`, `cdc_ether`, `rndis_host`, `usbnet`, `rndis_wlan`) and links the canonical `53-adi-plutosdr-usb.rules`. ([wiki.analog.com](https://wiki.analog.com/university/tools/pluto/drivers/linux))  
* **The udev rules themselves** (from ADI firmware repo): they give `MODE=0664` to the **plugdev** group for both the SDR and DFU USB IDs and set `ID_MM_DEVICE_IGNORE=1` to keep ModemManager away. ([GitHub](https://raw.githubusercontent.com/analogdevicesinc/plutosdr-fw/master/scripts/53-adi-plutosdr-usb.rules))  
* **SoapyPlutoSDR on NixOS exists**: `soapyplutosdr` is packaged in nixpkgs (handy if you use SoapySDR tooling or apps like SDR++). ([MyNixOS](https://mynixos.com/nixpkgs/package/soapyplutosdr?utm_source=chatgpt.com), [repology.org](https://repology.org/project/soapyplutosdr/versions?utm_source=chatgpt.com))  
* **GNU Radio on NixOS**: supported (3.8–3.10); Pluto integration is via ADI’s out-of-tree **gr-iio** blocks if you prefer the IIO backend. ([NixOS Wiki](https://nixos.wiki/wiki/GNU_Radio?utm_source=chatgpt.com), [wiki.analog.com](https://wiki.analog.com/resources/tools-software/linux-software/gnuradio?utm_source=chatgpt.com))  
* **Jetson/Orin notes**: People run Pluto with libiio on Jetson (e.g., Orin Nano on Ubuntu) and hit the same IIO/permissions pitfalls—so the rules below apply there too. For NixOS on Jetson, the community **jetpack-nixos** layer provides the NVIDIA kernel/firmware userspace you’ll need. ([ez.analog.com](https://ez.analog.com/linux-software-drivers/f/q-a/583835/iio-error?utm_source=chatgpt.com), [GitHub](https://github.com/anduril/jetpack-nixos?utm_source=chatgpt.com))

# Minimal NixOS setup (works on x86\_64 and Orin NX)

Add this to your NixOS configuration (flake module or `configuration.nix`). It installs the right libraries/tools, creates `plugdev`, and adds Pluto’s udev rules:

```
{ config, pkgs, ... }:
let
  # ADI’s official udev rules for Pluto
  plutoUdevRules = ''
    # allow "plugdev" group read/write access to ADI PlutoSDR devices
    # DFU
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b674", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a32", MODE="0664", GROUP="plugdev"
    # SDR
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", MODE="0664", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", MODE="0664", GROUP="plugdev"
    # keep ModemManager from probing it
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", ENV{ID_MM_DEVICE_IGNORE}="1"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2fa2", ATTRS{idProduct}=="5a02", ENV{ID_MM_DEVICE_IGNORE}="1"
  '';
in
{
  # Core userspace & SDR stacks
  environment.systemPackages = with pkgs; [
    libiio           # core IIO userspace lib + iio_info
    iio-oscilloscope # handy GUI to prove capture
    soapysdr soapyplutosdr # optional Soapy path to Pluto
    gnuradio         # GNU Radio (use gr-iio if/when packaged, see note below)
  ];

  # Make the "plugdev" group exist and add your user to it (and dialout for /dev/ttyACM0)
  users.groups.plugdev = { };
  users.users.yourUser.extraGroups = [ "plugdev" "dialout" ];

  # Install the udev rules
  services.udev.extraRules = plutoUdevRules;

  # Optional: belt & suspenders if NetworkManager’s ModemManager is installed elsewhere
  # services.modem-manager.enable = false;

  # (Orin/Jetson only) If you use a Jetson kernel via jetpack-nixos, keep that import here.
  # imports = [ <path/or flake to jetpack-nixos module> ];
}
```

**Why this works:** ADI’s own rules grant non-root access via `plugdev` and stop ModemManager from grabbing Pluto’s serial interface. That’s exactly what their Linux docs prescribe; we’re just expressing it declaratively for NixOS. ([wiki.analog.com](https://wiki.analog.com/university/tools/pluto/drivers/linux), [GitHub](https://raw.githubusercontent.com/analogdevicesinc/plutosdr-fw/master/scripts/53-adi-plutosdr-usb.rules))

# Optional stacks (pick what you need)

* **Soapy route (simple):** Apps using SoapySDR discover Pluto when `soapysdr` \+ `soapyplutosdr` are installed. Test with:

```
SoapySDRUtil --find
```

  You should see a `driver=plutosdr` device. ([MyNixOS](https://mynixos.com/nixpkgs/package/soapyplutosdr?utm_source=chatgpt.com))


* **GNU Radio \+ IIO route:** If you want GNURadio blocks that talk to IIO directly, use ADI’s **gr-iio** (may require building from source if your nixpkgs channel lacks it). ADI’s gr-iio page shows the build steps; we can package it as an overlay if you want. ([wiki.analog.com](https://wiki.analog.com/resources/tools-software/linux-software/gnuradio?utm_source=chatgpt.com))  
    
* **Python high-level API:** **pyadi-iio** is great for quick scripts but it needs **python-libiio ≥ 0.25**. If your channel is older, override or pin a newer libiio (see the ongoing nixpkgs update thread). ([GitHub](https://github.com/analogdevicesinc/pyadi-iio?utm_source=chatgpt.com))

# Test checklist (USB & IP modes)

1. **Hotplug & kernel side:** After plugging Pluto, `dmesg | tail` should show enumeration and RNDIS network iface (often `enx…`). ADI’s page shows typical messages and the 192.168.2.1 USB-Ethernet IP. ([wiki.analog.com](https://wiki.analog.com/university/tools/pluto/drivers/linux))  
     
2. **IIO discovery (USB):**

```
iio_info -s
```

   You should see `0456:b673 PlutoSDR` without needing `sudo` if the rule/group is correct. (This is exactly what ADI expects.) ([GitHub](https://github.com/analogdevicesinc/libiio/issues/57?utm_source=chatgpt.com))

   

3. **IIO over IP (USB-Ethernet):**

```
iio_info -u ip:192.168.2.1
```

   (Good fallback when USB permissions are still being tuned.) ADI documents using network contexts with Pluto. ([analogdevicesinc.github.io](https://analogdevicesinc.github.io/libiio/v0.21/index.html?utm_source=chatgpt.com))

   

4. **GUI sanity check:** launch `iio-oscilloscope` and select the Pluto context; you should be able to RX a tone/noise. ([GitHub](https://github.com/analogdevicesinc/iio-oscilloscope?utm_source=chatgpt.com), [wiki.analog.com](https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms1-ebz/software/linux/applications/iio_scope?utm_source=chatgpt.com))  
     
5. **Soapy check (if using Soapy):**

```
SoapySDRUtil --probe="driver=plutosdr"
```

   (Confirms the plugin stack.) ([MyNixOS](https://mynixos.com/nixpkgs/package/soapyplutosdr?utm_source=chatgpt.com))

# Orin NX / Jetson specifics

* If you’re **running NixOS on Orin**, use the **jetpack-nixos** module to pick up NVIDIA’s L4T kernel and userspace (CUDA, etc.). Pluto’s required USB/RNDIS modules are part of standard kernels and present in NVIDIA’s kernel; jetpack-nixos exposes them on NixOS. ([GitHub](https://github.com/anduril/jetpack-nixos?utm_source=chatgpt.com))  
* Folks have Pluto working on **Orin Nano (Ubuntu)** with libiio; errors they hit (e.g., `iio_info` contexts not found) are the same class of udev/permissions issues we solve above. ([ez.analog.com](https://ez.analog.com/linux-software-drivers/f/q-a/583835/iio-error?utm_source=chatgpt.com))

# Common gotchas

* **Group exists but rule not active:** on NixOS you can reload without reboot: `sudo udevadm control --reload-rules && sudo udevadm trigger`. (People trip on this often.) ([NixOS Discourse](https://discourse.nixos.org/t/udev-rule-not-applying-without-a-reboot/57022?utm_source=chatgpt.com))  
* **ModemManager still pokes the device:** the ADI rule sets `ID_MM_DEVICE_IGNORE=1`, but some stacks still race. If you see flapping TTYs, temporarily disable ModemManager. ([wiki.analog.com](https://wiki.analog.com/university/tools/pluto/drivers/linux))  
* **Python bindings too old:** `pyadi-iio` needs python-libiio ≥ 0.25; pin/update if your channel is older. ([GitHub](https://github.com/analogdevicesinc/pyadi-iio?utm_source=chatgpt.com))

If you want, I can turn this into a small flake (one `nixosConfiguration` and a devShell with GNU Radio \+ Soapy \+ pyadi-iio) that you can drop onto your Orin NX image.  
