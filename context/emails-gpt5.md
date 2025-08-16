## CN0566 Phaser × Elodin Aleph — Email Thread Summary

- **Timeframe**: Apr 9, 2025 → Jun 30, 2025
- **Participants**:
  - **Dan Driscoll** (Elodin, CEO & Co‑founder)
  - **Jon Kraft** (Analog Devices)
  - **Dave LoCascio** (Analog Devices, Director of System Platforms)
  - **Akhil Velagapudi** (Elodin)

### Purpose
- **Goal**: Demonstrate running Analog Devices CN0566 Phaser development kit demos using the NVIDIA Jetson Orin NX 16 GB on the Elodin Aleph carrier, leveraging Aleph’s compute as a companion to ADI radar platforms (start with Phaser; potentially expand to higher‑performance systems).

### Key Events (Timeline)
- **Apr 9**: Dan initiates contact with ADI; Jon expresses interest and proposes a call.
- **May 22**: Kickoff: Explore Aleph as an AI‑capable companion for ADI radar platforms; start with Phaser.
- **May 31**: Dan completes quickstart; notes Aleph OS is headless and may need GUI/VNC for some workflows; asks about fully headless/SSH workflows.
- **Jun 2**: Jon confirms headless operation is feasible:
  - Control via Python, creating the Phaser object with the Raspberry Pi IP `phaser.local`.
  - Provides examples: [PhaserBeamforming (examples)](https://github.com/jonkraft/PhaserBeamforming) and a ~100 m drone detection video: [YouTube](https://youtu.be/M1eXeqN1c-I?si=87EMvlv-dflUdX7i&t=445).
- **May 31 (thread)**: Internal Elodin discussion clarifies the integration path:
  - Prefer connecting PlutoSDR directly to Aleph; VNC on Aleph has limited value without radio I/O.
  - Headless path is viable: ADI labs use `matplotlib`/Thonny over SSH. Minimal CN0566 example: [pyadi‑iio cn0566_minimal_example.py](https://github.com/analogdevicesinc/pyadi-iio/blob/cn0566_dev/examples/cn0566/cn0566_minimal_example.py).
  - Hardware constraint for full Pi replacement: Two SPI devices (**ADF4159**, **ADAR1000**) lack chip selects; requires an **SPI mux** on a custom Aleph expansion board. Multiplexing mainly for calibration; normal operation may not require it. Interim approach: keep Pi for calibration; run GNU Radio ↔ PlutoSDR on Aleph.
- **Jun 30**: Jon confirms ordering the correct Aleph unit; Dan confirms and notes Aleph‑Phaser bring‑up exploration has started.

### Current Understanding
- **Headless operation** via SSH/Python is supported; on‑device GUI is not strictly required.
- **Immediate focus**: Get PlutoSDR working directly with Aleph and validate CN0566 demos headless.
- **Calibration dependency**: Fully eliminating the Raspberry Pi likely requires an SPI mux expansion for ADF4159/ADAR1000 calibration.

### Open Questions / Risks
- **SPI mux**: Design/availability, scope, and ownership for an Aleph expansion to support calibration.
- **Software split**: Interim division of responsibilities between Aleph and Raspberry Pi (e.g., calibration on Pi vs. runtime on Aleph).
- **GUI needs**: Which demo workflows benefit from on‑device GUI vs. remote plotting/IDE over SSH.

### References
- **Examples**: [PhaserBeamforming (Jon Kraft)](https://github.com/jonkraft/PhaserBeamforming)
- **CN0566 minimal**: [pyadi‑iio cn0566_minimal_example.py](https://github.com/analogdevicesinc/pyadi-iio/blob/cn0566_dev/examples/cn0566/cn0566_minimal_example.py)
- **Demo video**: [Drone at ~100 m](https://youtu.be/M1eXeqN1c-I?si=87EMvlv-dflUdX7i&t=445)

### Action Items (Proposed)
- **Short‑term**:
  - Connect PlutoSDR to Aleph; validate IIO/pyadi‑iio and run CN0566 minimal headless.
  - Document the calibration workflow with the existing Pi; define command sequence and data handoff.
- **Mid‑term**:
  - Evaluate/design SPI mux expansion to support ADF4159/ADAR1000 calibration from Aleph.
  - Assess need and approach for a GUI/VNC Aleph OS image variant.

### Notable Quotes (Abridged)
- Jon: “Operate without the Rasp Pi desktop… create the Phaser object with IP `phaser.local`.”
- Akhil: “No real value in VNC on Aleph without direct SDR access.”
- Akhil: “ADI chips don’t have SPI chip selects… need a SPI mux (mainly for calibration).”
- Dan: “Aleph should be able to do everything the Pi can do… ideal for a hot‑swap with the Pi.”

—
Source: Consolidated from `sources/emails.md`.
