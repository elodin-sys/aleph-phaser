ES03 Aleph Drone Expansion Board Data Sheet
April 2025
• Carrier board revision: 2.0.0




                              Figure 1: Aleph Drone Expansion Board


Contents
  1. Overview . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     1.1. Key Features . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
  2. Specifications . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     2.1. Environmental . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
     2.2. Mechanical . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
     2.3. Electrical and Hardware . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
          2.3.1. Sensors . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
          2.3.2. Microcontroller Specs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
          2.3.3. Connectivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
                  2.3.3.1. Board to Board . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
     2.4. Software . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
          2.4.1. Autopilot Support . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4




ES02-01                                                                                                         1/5
Overview
The Aleph Drone Expansion Board is a versatile, standalone flight controller
built around the high-performance STM32H7 microcontroller. Designed for seamless
integration into drone and robotics systems, it features a flight sensor suite,
exposed communication peripherals, and an onboard debugger/flasher accessible
via a single USB-C connection—streamlining development and deployment. This open
development platform supports popular autopilot firmware such as PX4 and
Betaflight, as well as Elodin’s own Roci control stack or any custom flight
software. For compute-intensive missions, it can interface directly with the
Aleph Carrier Board, enabling tight coupling between low-level control and high-
level autonomy.

Key Features
• Peripheral support: 3× UART, 2x CAN, I2C, 16x PWM, 8x GPIO, MircoSD, USB FS
  (12 Mbps) with PD
• Flight sensor suite: 2x IMU (with communication redundancy), Barometer,
  Magnetometer
• Visual status indicators: 7x status LEDs

Specifications
Environmental
   Minimum operating temperature (ºC)                     −25
   Maximum operating temperature (ºC)                      80
              ROHS compliant                              Yes
                                             Please contact us for further
          Vibration qualification
                                                      information




ES02-01                                                                         2/5
Mechanical
                 Dimensions (mm)                     Refer to Figure 2, 3, 4
                  Base Material                            Isola 370HR
                 Surface finish                                 ENIG




              Figure 2: Aleph Drone Expansion Board Top View




             Figure 3: Aleph Drone Expansion Board Front View




             Figure 4: Aleph Drone Expansion Board Side View




ES02-01                                                                  3/5
Electrical and Hardware
                 Minimum operating supply voltage (V)                            5
                 Maximum operating supply voltage (V)                        28
                    Standard power consumption (W)                               3
                 Maximum peripheral power supply (W)                         15
                          Peripheral VDD (V)                                     5
                      Peripheral logic level (V)                             3.3
                Peripheral VDD rail currant monitoring                       Yes
                    Switchable Peripheral VDD rail                           Yes
                       Over-currant protection                               Yes
                Power input reverse currant protection                       Yes
                            ESD protection                                   Yes
                      VBAT-IN voltage monitoring                             Yes
                Regulated internal voltage monitoring                        Yes
                         FRAM Capacity (Kbit)                                16


Sensors
                             IMU                                BMI323 or BMI270
                          Barometer                                     BMP581
                         Magnetometer                                   BMM350


Microcontroller Specs
The Aleph Drone Expansion Board has 2 MCUs, an STM32H7 as the main micro
controller and the an RP2040 as the debugger and flasher. This allows the RP2040
to serve several useful functions on the FC board. When flashed with debugprobe
firmware, it can serve as a CMSIS-DAP probe and USB-to-UART bridge. This
provides a convenient way to flash new firmware onto the STM32 over USB using
standard tools such as OpenOCD or probe-rs. Since the RP2040 can monitor the
STM32′s UART1 and pull its nRST low, it can also function as a watchdog.
NOTE: the RP2040 is pre-flashed with debugprobe firmware.

                                                         • ARM Cortex-M7 @ 480MHz
                        Cores
                                                         • ARM Cortex-M4 @ 240MHz
              Flash memory capacity (MB)                            2
                       RAM (MB)                                     1


Connectivity

Board to Board

Software

Autopilot Support
The Aleph Drone Expansion Board ships with an image of the Betaflight autopilot.
It is also compatible with PX4. The system can also be flashed with custom
flight control software or Elodin’s own Roci control stack or any custom flight


ES02-01                                                                              4/5
software. For instruction on how to flash the system, refer to the Elodin Docs
page.




ES02-01                                                                      5/5
