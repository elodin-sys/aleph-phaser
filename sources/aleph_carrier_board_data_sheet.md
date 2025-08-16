ES02 Aleph Carrier Board Data Sheet
April 2025
• Carrier board revision: 2.0.0




                                    Figure 1: Aleph Carrier Board


Contents
  1. Overview . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     1.1. Key Features . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
  2. Specifications . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     2.1. Environmental . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     2.2. Mechanical . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
     2.3. Electrical and Hardware . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
          2.3.1. Buttons . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
          2.3.2. Connectivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
                  2.3.2.1. Board to Board Connector Pinout . . . . . . . . . . . . . . . . 7
          2.3.3. Compatible SOMs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
  3. Software . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
     3.1. Operating System Support . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9




ES02-01                                                                                                         1/9
Overview
The Aleph Carrier Board is a space-grade flight computer designed to house and
interface the NVIDIA Jetson Orin NX SOM series for high-performance, on-orbit
compute. Aleph enables AI-based autonomy, real-time image processing, and
advanced decision-making directly on-board, reducing ground station dependency
and latency.

Key Features
• Peripheral support: 2× I2C, 1× UART, CAN, SPI, USB FS, USB SS+ (10 Gbps),
  Serial Debug, Gigabit Ethernet
• High-speed interfaces: PCIe x4, x2, x1; M.2 E-Key and M-Key
• Operational temperature range: –40°C to +85°C
• Compact mechanical design: 89 × 53.5 × 19.3 mm
• Modular and open software stack: Runs Elodin’s open-source flight software
  modules or fully user-defined mission software.
• All components and materials are selected for low outgassing.

Specifications
Environmental
   Minimum operating temperature (ºC)                     −45
   Maximum operating temperature (ºC)                      85
              ROHS compliant                              Yes
                                             Please contact us for further
          Vibration qualification
                                                      information




ES02-01                                                                        2/9
Mechanical
             Dimensions (mm)                    Refer to Figure 2, 3, 4
             Base Material                            Isola 370HR
             Surface finish                              ENIG




             Figure 2: Aleph Carrier Board Top View




ES02-01                                                             3/9
          Figure 3: Aleph Carrier Board Front View




          Figure 4: Aleph Carrier Board Side View




ES02-01                                              4/9
Electrical and Hardware
             Minimum operating supply voltage (V)                   5
             Maximum operating supply voltage (V)                   20
                                                                 Idle: 10
                    Power consumption (W)
                                                                 Peak: 40


Buttons
           Designator                               Function
              SW2                               Force Recovery
              SW3                                    Reset




             Figure 5: Aleph Carrier Board Buttons Callout




ES02-01                                                                  5/9
Connectivity
Designator     Connector Type             Interface
                                          22-pin MIPI, similar to
J1, J2         2x CSI-2 Interface
                                          Raspberry Pi 5
                                          • 2x PCIe 4.0 x1
                                          • USB-SS (5 Gbps)
                                          • 2x I2C (VDDIO 3.3 V)
               Samtech ERF5-050 B2B       • SPI (VDDIO 1.8 V)
J3
               connector                  • CAN TTL (VDDIO 3.3 V)
                                          • UART (VDDIO 1.8 V)
                                          • 6x GPIO (VDDIO 1.8 V)
                                          • GigE
J4             MOLEX_0533980471 (4-pin)   Jetson fan connector
J5             260 Position SODIMM        SOM connector
                                          • PCIe 4.0 x1
                                          • USB HS (480 Mbps)
J6             M.2 E Key
                                          • I2C
                                          • UART
J7             M.2 M Key                  PCIe 4.0 x4
                                          Serial Debug Port with
J8             USB-C
                                          USB Power Delivery
                                          USB-SS+ (10 Gbps) with
J9             USB-C                      USB Power Delivery and
                                          DisplayPort Alt mode
J10            USB-C                      USB-SS+ (10 Gbps)




ES02-01                                                             6/9
                         Figure 6: Connector Callouts

Board to Board Connector Pinout
 Pin-1      GND                PCIE3-     Pin-51   GBE-MDI2_N   Pin-76    CAN-RX
                     Pin-26
 Pin-2      GND                CLKREQ
                                          Pin-52      GND
                                                                Pin-77   I2C1-SDA
 Pin-3    PE3T0_N    Pin-27      GND      Pin-53      GND
 Pin-4      GND                                                 Pin-78    CAN-TX
                     Pin-28   PCIE-WAKE             GBE-LED-
                                          Pin-54
 Pin-5    PE3T0_P                                     ACT       Pin-79   I2C1-SCL
                     Pin-29     GPIO1
           PCIE2-                                   GBE-LED-
 Pin-6                                    Pin-55                Pin-80      GND
           RX0_N     Pin-30      GND                  LINK
 Pin-7      GND                           Pin-56      GND       Pin-81      GND
                     Pin-31     GPIO7
           PCIE2-                         Pin-57      GND       Pin-82   PMIC_BBAT
 Pin-8               Pin-32    GPIO13
           RX0_P
                                                   EXP-USB1-
 Pin-9    PE2T0_N                         Pin-58                Pin-83    SPARE0
                     Pin-33     GPIO9                 D_P
 Pin-10     GND                                                 Pin-84    SPARE1
                     Pin-34    GPIO12     Pin-59    SPI0-SCK
 Pin-11   PE2T0_P
                                                   EXP-USB1-    Pin-85      GND
          PCIE2/3-   Pin-35      GND      Pin-60
 Pin-12                                               D_N
           RX1_N     Pin-36    GPIO11                           Pin-86    EXP-VDD
                                          Pin-61   SPI0-MOSI
 Pin-13     GND                                                 Pin-87      GND
                     Pin-37   UART1-RXD   Pin-62      GND
          PCIE2/3-
 Pin-14                                   Pin-63   SPI0-MISO    Pin-88    EXP-VDD
           RX1_P     Pin-38      GND


ES02-01                                                                           7/9
           PCIE2-      Pin-39   UART1-RXD             EXP-USB1-   Pin-89      GND
 Pin-15                                      Pin-64
           CLK_N                                         D_N
                       Pin-40      GND                            Pin-90    EXP-VDD
 Pin-16      GND                             Pin-65   SPI0-CS0
           PCIE2-      Pin-41      GND                 USBSS1-    Pin-91      GND
 Pin-17                                      Pin-66
           CLK_P                                        RX_P
                       Pin-42   GBE-MDI1_P                        Pin-92    EXP-VDD
           PCIE3-                            Pin-67   SPI0-CS1
 Pin-18
           CLK_N       Pin-43   GBE-MDI0_P                        Pin-93      GND
                                             Pin-68     GND
 Pin-19      GND       Pin-44   GBE-MDI1_N   Pin-69     GND       Pin-94    EXP-VDD
           PCIE3-
 Pin-20                Pin-45   GBE-MDI0_N             USBSS1-    Pin-95      GND
           CLK_P                             Pin-70
                                                        TX_N
 Pin-21   PCIE2-RST    Pin-46      GND                            Pin-96    EXP-VDD
                                             Pin-71   I2C0-SDA
 Pin-22      GND
                       Pin-47      GND                            Pin-97      GND
                                                       USBSS1-
           PCIE2-                            Pin-72
 Pin-23                Pin-48   GBE-MDI3_P              TX_P
           CLKREQ                                                 Pin-98    EXP-VDD
           PCIE3-                            Pin-73   I2C0-SCL
 Pin-24                Pin-49   GBE-MDI2_P                        Pin-99      GND
           CLK_P                             Pin-74     GND
                       Pin-50   GBE-MDI3_N                        Pin-100   EXP-VDD
 Pin-25      GND                             Pin-75     GND




                    Figure 7: Board to Board Connector Reference




ES02-01                                                                             8/9
Compatible SOMs
The Aleph Carrier Board supports all NVIDIA Jetson Orin NX series SOMs (8GB and
16GB variants) and the Jetson Orin Nano series SOMs. The board interfaces and
houses the some using a 260 position SODIMM connector. It provides full
electrical and mechanical compatibility per NVIDIA design guidelines.

                                                                 Jetson Orin Nano
           SOM        Jetson Orin NX 8GB Jetson Orin NX 16GB
                                                                        8GB
   AI performance
                             117                  157                   67
 (Sparse INT8 TOPS)
                      1024-core NVIDIA      1024-core NVIDIA     1024-core NVIDIA
                           Ampere                Ampere               Ampere
           GPU        architecture GPU      architecture GPU     architecture GPU
                       with 32 Tensor        with 32 Tensor       with 32 Tensor
                            Cores                 Cores                Cores
 GPU max frequency
                            1173                 1173                  1020
       (MHz)
                          6-core Arm®          8-core Arm®          6-core Arm®
                      Cortex®-A78AE v8.2   Cortex®-A78AE v8.2   Cortex®-A78AE v8.2
           CPU
                       64-bit CPU 1.5MB     64-bit CPU 2MB L2    64-bit CPU 1.5MB
                          L2 + 4MB L3            + 4MB L3           L2 + 4MB L3
 CPU max frequency
                              2                    2                   1.7
       (GHz)
   DL accelerator        1x NVDLA v2          2x NVDLA v2               -
 DLA max frequency
                            1.23                 1.23                   -
       (GHz)
                      8GB 128-bit LPDDR5      16GB 128-bit      8GB 128-bit LPDDR5
          Memory
                          102.4GB/s         LPDDR5 102.4GB/s         102 GB/s
                      Supports external    Supports external    Supports external
      Storage
                             NVMe                NVMe                  NVMe
 Vision Accelerator       1x PVA v2            1x PVA v2                -


Software
Operating System Support
The Aleph Carrier Board flight computer comes pre-flashed with NixOS. The system
is also compatible with Jetpack and Yocto.




ES02-01                                                                         9/9
