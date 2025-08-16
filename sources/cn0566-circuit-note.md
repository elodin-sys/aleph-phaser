                                                                                                                                 Circuit Note
                                                                                                                                    CN-0566
                                                                 Devices Connected/Referenced                Devices Connected/Referenced
                                                                 ADAR1000      8 GHz to 16 GHz, 4-Channel, LTC4217         2 A Integrated Hot Swap
                                                                               X Band and Ku Band                          Controller
                                                                               Beamformer
                                                                 ADF4159       Direct Modulation/Fast        HMC735        VCO with Divide-by-4, 10.5 GHz
                                                                               Waveform Generating,                        to 12.2 GHz
                                                                               13 GHz, Fractional-N Frequen-
                                                                               cy Synthesizer
                                                                 ADRF5019        Silicon, SPDT Switch,          HMC652          Fixed, 2 dB Passive Attenuator
                                                                                 Nonreflective, 100 MHz                         Chip, DC to 50 GHz
                                                   ®
                              Circuits from the Lab refer-                       to 13 GHz
                              ence designs are engineered        AD8065          High Performance, 145 MHz      HMC654          Fixed Passive SMT Attenuator,
                              and tested for quick and easy                      FastFET™ Op Amps                               DC to 25 GHz
                              system integration to help solve   ADL8107         GaAs, pHEMT, MMIC, Low         ADP7118         20 V, 200 mA, Low Noise,
                              today’s analog, mixed-signal,                      Noise Amplifier, 6 GHz                         CMOS LDO Linear Regulator
                              and RF design challenges. For                      to 18 GHz
                              more information and/or sup-       LTC5548         2 GHz to 14 GHz Microwave      ADP7158         2 A, Ultralow Noise, High
                              port, visit                                        Mixer with Wideband DC to                      PSRR, Fixed Output, RF Linear
                              www.analog.com/CN0566.                             6 GHz IF                                       Regulator
                                                                 LT8609S         42 V, 2 A/3 A Peak             ADM7150         800 mA, Ultra Low Noise/High
                                                                                 Synchronous Step-Down                          PSRR LDO
                                                                                 Regulator with 2.5 μA
                                                                                 Quiescent Current
                                                                 AD7291          8-Channel, I2C, 12-Bit SAR     ADM7170         6.5 V, 500 mA, Ultralow Noise,
                                                                                 ADC with Temperature Sensor                    High PSRR, Fast Transient
                                                                                                                                Response CMOS LDO
                                                                 LT3460          1.3 MHz/650kHz Step-Up
                                                                                 DC/DC Converter in SC70,
                                                                                 ThinSOT and DFN

                                                Phased Array Development Platform

EVALUATION AND DESIGN SUPPORT                                                     nulls in the receiver's antenna pattern can be placed to reject
                                                                                  interfering signals, and a link can be maintained between two radios
► Circuit Evaluation Boards                                                       that are moving with respect to one another. Phased arrays vary
  ► CN0566 Circuit Evaluation Board (EVAL-CN0566-RPIZ)                            widely in complexity, from a few elements in a simple linear array
                                                                                  to thousands of elements in planar, cylindrical, conical, and other
► Design and Integration Files
                                                                                  shaped arrays.
  ► Schematics, Layout Files, Bill of Materials, Software
                                                                                  Phased arrays have a steep learning curve, spanning multiple
CIRCUIT FUNCTIONS AND BENEFITS                                                    technological and engineering disciplines including microwave RF
                                                                                  electronics, continuous and discrete-time signal processing, em-
Phased array beamforming has been used in radar and communi-                      bedded systems, analog-to-digital and digital-to-analog converters,
cation systems since the mid-20th century. In recent years, these                 digital design, and computer networking. Commercial phased array
systems have seen extensive adoption in areas such as 5G mobile                   systems are typically expensive and built for a single application,
communications, military and commercial radars, satellite communi-                and are not conducive to exploration of basic concepts.
cations, and automotive applications.
                                                                                  The circuit shown in Figure 1 is a low cost, simplified phased ar-
Phased array antennas (or beamforming antennas) have an elec-                     ray beamforming demonstration platform that offers a hands-on ap-
tronically steerable radiation pattern, allowing a robust communica-              proach to learning about the principles and applications of phased
tion link to be established between two radios. Power from the                    array antennas. This complete system provides an ideal tool for
transmitter can be directed toward the intended receiver, and the                 proof of concept or debugging of more complex systems. It offers
receiving antenna can be aimed at the transmitter. In addition,                   the opportunity to explore and understand advanced topics such

analog.com         Circuits from the Lab™ circuits from Analog Devices have been designed and built by Analog Devices                       Rev. 0 | 1 of 11
                   engineers. Standard engineering practices have been employed in the design and construction of each circuit,
                   and their function and performance have been tested and verified in a lab environment at room temperature.
                   However, you are solely responsible for testing the circuit and determining its suitability and applicability for
                   your use and application. Accordingly, in no event shall Analog Devices be liable for direct, indirect, special,
                   incidental, consequential or punitive damages due to any cause whatsoever connected to the use of any
                   Circuits from the Lab circuits. (Continued on last page)
                                                                                                                                Circuit Note
                                                                                                                                   CN-0566
as beamforming, beam steering, antenna impairments, frequency                    to digitize the intermediate frequency (IF) output. The software
modulated continuous wave (FMCW) radar, and synthetic aperture                   interface is through the Linux industrial input/output (IIO) frame-
imaging. The design consists of RF components, signal processing                 work, providing a host of debug and development utilities, and
hardware, and contains an on-board 8-element linear array antenna                cross-platform application programming interface (API) with Python,
that operates from 10.0 GHz to 10.5 GHz (X band). This frequency                 GNURadio, and MATLAB support.
range allows common low cost motion sensor modules to be used
as a microwave source.                                                           Application software can run either locally on the Raspberry Pi or
                                                                                 remotely via a wired or wireless network connection. The entire
The circuit is designed to mount directly on a Raspberry Pi, and                 system is powered via a single 5 V, 3 A, USB-C power adapter.
uses the PlutoSDR low cost software defined radio (SDR) module




                                                       Figure 1. CN0566 Simplified Block Diagram




analog.com        Circuits from the Lab™ circuits from Analog Devices have been designed and built by Analog Devices                  Rev. 0 | 2 of 11
                  engineers. Standard engineering practices have been employed in the design and construction of each circuit,
                  and their function and performance have been tested and verified in a lab environment at room temperature.
                  However, you are solely responsible for testing the circuit and determining its suitability and applicability for
                  your use and application. Accordingly, in no event shall Analog Devices be liable for direct, indirect, special,
                  incidental, consequential or punitive damages due to any cause whatsoever connected to the use of any
                  Circuits from the Lab circuits. (Continued on last page)
Circuit Note                                                                                                                CN-0566
CIRCUIT DESCRIPTION                                                     of the four signals, and the output of the combiner is significantly
                                                                        reduced.
Phased array beamforming is a signal processing technique used
in antenna arrays for radio communications, radar systems, and
medical imaging. Beamforming provides many benefits — the an-
tenna can be aimed directly at a target, which may be a transmitter,
receiver, or object being tracked in the case of radar. The antenna
pattern's nulls can also be strategically placed to avoid interfering
signals.
Forming a beam pattern involves the simultaneous transmission or
reception of signals from multiple antennas. A phase shift and gain
adjustment is applied to each channel; after which, the individual
channels are summed together in either the analog or digital do-
main, or a hybrid of both. The phase shifters are adjusted to control
the direction of the combined radio RF beam, allowing for real-time
beam steering and reconfiguration without physically moving the
antennas. The main beam width and sidelobe suppression can be
adjusted by adjusting the gain (or tapering) the array elements.                Figure 3. Delayed Signals Arrive at Combiner Out-of-Phase

The CN0566 main board implements an 8-element phased array,             In a phased array, time delay is the quantifiable delta needed for
downconverting mixers, local oscillator (LO), and digital control       beam steering. The time delay to steer the beam is equal to the
circuitry. The CN0566 outputs are two IF signals at a nominal           time it will take for the wavefront to traverse the incremental propa-
frequency of 2.2 GHz, that are digitized by a PlutoSDR module.          gation distance between elements (L). This can best be visualized
BEAMFORMING FUNDAMENTALS                                                by drawing a right triangle between the adjacent elements, as
                                                                        shown in Figure 4.
Figure 2 and Figure 3 provide a simple illustration of a wavefront
received by four antenna elements from two different directions.
The electrical beam is steered 45º to the left, toward the desired
transmitter, by inserting time delays in the receive paths, and then
summing all four signals together.
In Figure 2, that time delay (configured for a 45º beam) matches the
time difference of the wavefront striking each element. In this case,
that applied delay causes the four signals to arrive in phase at the
point of combination. This coherent combining results in a larger
signal at the output of the combiner.


                                                                                Figure 4. Geometry of Adjacent Elements to the Wavefront

                                                                        From this drawing, and noting the right angle formed, the value of L
                                                                        can be calculated using Equation 1:
                                                                        L = d sin θ                                                            (1)
                                                                        where:
                                                                        L is the incremental propagation distance between elements.
                                                                        d is the distance between elements.
                                                                        θ is the electrical beam angle (angle between mechanical boresight
                                                                        and electrical boresight).
                                                                        The time delay to steer the beam is equal to the time it will take for
          Figure 2. Delayed Signals Arrive at Combiner In-Phase         the wavefront to traverse that distance, L. Therefore, the time delay
                                                                        is calculated using Equation 2:
In Figure 3, that same delay is applied; however, in this case, the
wavefront from an undesired (interfering) transmitter is perpendicu-    ∆t = L/c = d sin θ/c                                                   (2)
lar to the antenna elements. That applied delay misaligns the phase     where:
                                                                        ∆t is the incremental time delay between elements.
analog.com                                                                                                                     Rev. 0 | 3 of 11
Circuit Note                                                                                                                        CN-0566
c is the speed of light (3×108 m/s).                                         unity gain. That normalized array factor can be written as Equation
                                                                             4:
Solving for the direction to electrically steer the antenna gives:
                                                                                         sin Nπd sin θ − sin θ0
θ = sin‐1(∆t c/d)                                                            AF θ =           λ
                                                                                                                                                    (4)
                                                                                         Nsin πd sin θ − sin θ0
                                                                                               λ
But time delay can also be emulated with a phase shift, which
is common and practical in many implementations. For a narrow                where:
bandwidth system, a phase delay can be substituted in for a time             AF is the normalized array factor.
delay. That phase delay is simply computed using Equation 3:                 N is the number of elements.
                                                                             θ0 is the beam angle.
∆Φ = 2 π L/λ = 2π f L/c =2 π f d sin θ/c                               (3)
                                                                             Since the beam angle, θ0, has already been defined as a function
where:
                                                                             of phase shift between elements ∆Φ; therefore, the normalized
∆Φ is the incremental phase shift between elements.
                                                                             antenna factor can also be written as Equation 5:
λ is the signal wavelength.
f is the signal frequency.                                                                      sin N
                                                                                                      πd
                                                                                                         sin θ −
                                                                                                                 ∆Φ
                                                                                                       λ          2
                                                                             AF θ, ∆ Φ =                         ∆Φ                                 (5)
Solving for the electrical steering angle, based on the phase shift,                             Nsin πd sin θ −
                                                                                                       λ          2
gives:
                                                                             The conditions assumed in the array factor equation include:
θ = sin‐1 (∆Φ c / (2 π f d))
                                                                             ► The elements are equally spaced.
As an example, consider two antenna elements spaced 14 mm                    ► There is an equal phase shift between elements.
apart. If a 10.3 GHz wavefront is arriving at 30º from mechanical
                                                                             ► The elements are all at equal amplitude.
boresight, then what is the optimal phase shift between the two
elements?                                                                    Figure 5 is the array factor for an 8-element array, d = λ/2, θ0 = 30° .
θ = 30° = 0.52 rad

            3×108 m/s
λ = fc =    10.3 GHz      = 0.0291 m

        (2π×d×sinθ)   2π×0.014×sin(0.52)
∆Φ =         λ      =     0.0291 m


ΔΦ = 1.53 rad = 87.4°
So, if the wavefront is arriving at θ = 30º, and then the phase of the
neighboring element is shifted by 87.4º, this will cause the individual
signals of both elements to add coherently. This maximizes the
antenna gain in that direction.
ANTENNA PATTERN FOR A LINEAR ARRAY
                                                                                            Figure 5. Array Factor, N=8, d = λ/2, θ0 = 30°
In addition to steering angle, it is useful to understand and manipu-
late the complete antenna gain pattern. The antenna pattern is a             RF DESIGN
combination of the element factor and the array factor. The element
factor is the radiating pattern of an element, and it is fixed by            Receive Antenna and LNAs
the construction of that element. The array factor is the beam
                                                                             Connecting a receiver to an antenna array is not trivial. At micro-
pattern that can be electrically controlled by shifting the phase and
                                                                             wave frequencies, cables and connectors must be low-loss and
amplitude of each element.
                                                                             length-matched. The CN0566 eliminates these concerns by includ-
The array factor is calculated based on array geometry (d for                ing an on-board 8-element patch antenna that operates from 10
the CN0566's uniform linear array) and beam weights (amplitude               GHz to 10.5 GHz as shown in Figure 6.
and phase). Deriving the array factor for a uniform linear array is
                                                                             Each element consists of four sub-elements that are summed
straightforward, but the details are best covered in the references
                                                                             equally via printed circuit board (PCB) trace Wilkinson splitters,
cited at the end of this circuit note.
                                                                             resulting in a narrowing of the beam pattern in the horizontal
Since the primary concern is how the gain changes with angle, it is          direction. A quarter-wavelength shorting stub provides electrostatic
often more instructive to plot the normalized array factor relative to       discharge (ESD) protection. Each element is capacitively coupled
                                                                             to a 6 GHz to 18 GHz, 24 dB gain ADL8107 low noise amplifier

analog.com                                                                                                                             Rev. 0 | 4 of 11
Circuit Note                                                                                                               CN-0566
via 10 nF capacitors, and an external antenna can be connected
via optional subminiature push-on (SMP) connectors. The LNAs
increase the sensitivity of the array, providing a sharp beam pattern
even with low power microwave sources.



                                                                                     Figure 8. ADAR1000 Operation in Receive Mode

                                                                        Local Oscillator/Synthesizer
                                                                        The ADF4159 phase-locked loop (PLL) and the HMC735 voltage-
                                                                        controlled oscillator (VCO) combine to form a frequency synthesizer
                                                                        with a range of 10.5 GHz to 12.7 GHz as shown in Figure 9.
                                                                        This signal is used to drive the LO port of all the mixers. For
                                                                        communications and other fixed-frequency applications, the LO
                                                                        frequency is typically set to 2.2 GHz above the desired signal at the
                                                                        antenna. Therefore, the LO is generally between 12 GHz and 12.7
                                                                        GHz. The ADF4159 is also capable of generating FMCW ramps
                                                                        or "chirps" for radar applications. The ADF4159 includes a variety
      Figure 6. 8-Element Antenna Patch and ADL8107 Block Diagram       of chirp ramp rates and shapes including sawtooth, triangular, and
                                                                        parabolic.
Figure 7 shows the on-board antenna’s gain vs. frequency. The -3
dB bandwidth is 9.9 GHz to 10.8 GHz.                                    Alternatively, the on-board synthesizer can be disabled, and an
                                                                        external LO can be applied to the LO input SMA connector. This
                                                                        allows the CN0566 to be synchronized to an external radio, or
                                                                        several CN0566 boards to be synchronized to a single LO. Whether
                                                                        generated on-board or externally, the local oscillator is split using
                                                                        monolithic microwave integrated circuit (MMIC) splitter or combin-
                                                                        ers to the two receive mixers, and to either the on-board transmit
                                                                        path or to an LO output port as shown in Figure 1.




                  Figure 7. Antenna Gain vs. Frequency                                   Figure 9. CN0566 Synthesizer Circuitry

Beamformers                                                             Mixers and Filtering
The core of the CN0566 is a pair of ADAR1000 4-channel, 8 GHz to        The RFIO output of the ADAR1000 passes through a 10.6 GHz low
16 GHz, X band and Ku band beamformers. The ADAR1000 allows             pass filter and then enters the RF port of the LTC5548 mixer, as
per-channel, 360° phase adjustment with 2.8° resolution, and 31         shown in Figure 10.
dB gain adjustment with 0.5 dB resolution. The two ADAR1000s
are capable of bidirectional, half-duplex operation; however, the
CN0566 only connects the ADAR1000 receive paths. The outputs
of the ADL8107 LNAs are phase and amplitude shifted by an
ADAR1000, and then summed together at its RFIO output as
shown in Figure 8.




                                                                                      Figure 10. CN0566 Mixers and Filtering Path


analog.com                                                                                                                        Rev. 0 | 5 of 11
Circuit Note                                                                                                                  CN-0566
The low pass filter removes the high-side image of the mixer (which
in the figure above will appear at 12.2 GHz + 2.2 GHz = 14.4 GHz)
as well as any reradiation of the LO (12.2 GHz). The LTC5548
mixer outputs an IF of 2.2 GHz, which is filtered by a 2.5 GHz low
pass filter.
Figure 11 shows the measured results of the receive signal path
(ADL8107 + ADAR1000 + 10.62 GHz low pass filter + LTC5548 +
2.5 GHz low pass filter). This is for an LO of 12.2 GHz, antenna
                                                                             Figure 13. Transmit Output for a 2.1 GHz tone (without filtering)
input of 10 GHz, and an IF of 2.2 GHz. Note that the 12.2 GHz
and the 14.4 GHz will be further attenuated by the input bandwidth     After passing through the 2.5 GHz low pass filter, only the primary
of the PlutoSDR, resulting in an SFDR of approximately 56 dBc as       signal is visible above the noise floor. This "cleaned up" signal is
shown by markers M1 to M4 (-23 dBm + 79 dBm = 56 dBc).                 then fed onto the IF of the LTC5548 and upconverted to 10 GHz to
                                                                       10.3 GHz.
                                                                       The 10 GHz to 10.3 GHz RF is then filtered by a 10.6 GHz low
                                                                       pass filter, and amplified by an ADL8107 24 dB LNA, and finally
                                                                       bandpass filtered by a 9.7 GHz to 11.95 GHz filter. Figure 14 shows
                                                                       the mixer output without filtering.



            Figure 11. CN0566 Spurious Free Dynamic Range

Transmitter Signal Path
While the beamforming section of the CN0566 is receive only, a
transmit output is provided for driving an external antenna. For an-
tenna pattern measurements, the antenna can be positioned facing                      Figure 14. Output Signal without Mixer Filters
the array at various angles. The frequency of the transmit is known
exactly as it is derived from the on-board LO, simplifying digital     Figure 15 shows the transmit output after amplification and band-
signal processing. The transmitter can also be used to illuminate a    pass filtering.
target scene when the CN0566 is used in Doppler and FMCW radar
applications.
As shown in Figure 12, the transmitter signal path starts with the
transmit input subminiature version A (SMA) connector and outputs
to a separate transmit antenna through the two transmit output
SMA connectors, TX1 and TX2.


                                                                                          Figure 15. Transmit Output Spectrum


               Figure 12. CN0566 Transmitter Signal Path               Virtual Arrays

The transmit input is generally the same frequency as the receive      The CN0566 can also be used in virtual arrays, a technique most
IF, which is about 2.2 GHz. This transmit input can either be          commonly used in radar systems. In this mode, two transmitter
a continuous wave, modulated communications, or radar signal.          outputs are used, with each transmitter at a different distance from
Since the output of many SDRs (including that of the PlutoSDR)         the receive array. As shown in Figure 16, the transmit outputs are
use a square wave LO, it produces harmonics of the LO frequency.       toggled at the end of a programmable number of PLL chirps. The
Therefore, the transmit input signal must first pass through a low     data is then combined to create a virtual array that appears to have
pass filter. Figure 13 shows the transmit output of the PlutoSDR for   twice the number of receive elements. Therefore, the receive beam
a 2.1 GHz tone (without filtering).                                    is narrower, but it takes twice the amount of time to gather the data.




analog.com                                                                                                                       Rev. 0 | 6 of 11
Circuit Note                                                                                                                   CN-0566




                        Figure 16. Virtual Arrays

Transmit antenna switching is triggered by the end of a program-                                Figure 18. CN0566 Power Tree
mable number of PLL chirps. The ADF4159's MUXOUT pin can
be programmed to indicate the end of a ramp, and this signal              The LTC4217 integrated hot swap controller allows the CN0566 to
is level-shifted and applied to the clock input of a 7-stage ripple       be safely inserted and removed by limiting the amount of inrush
counter, as shown in Figure 17. Three general-purpose input/output        current to the load supply during power-up, and provides a conven-
(GPIO) signals from the Raspberry Pi drive a data multiplexer             ient means of measuring the board's power consumption via the
inputs, selecting antenna toggle rates of 2, 4, 8, 16, 32, 64, or 128     IMON output.
chirps.                                                                   The LT8609S is a monolithic constant frequency current-mode
                                                                          step-down DC/DC converter. This device steps down the 5 V input
                                                                          voltage to 3.3 V. This output is then fed into the ADP7158 LDO,
                                                                          which powers the beamformers, LNA, mixers, switches, and ADC at
                                                                          3.3 V.
                                                                          The ADM7150 LDO provides the 1.8 V analog supply rail for the
                                                                          digital-level translators and ADF4159.
                                                                          The ADM7170 is a low quiescent current, low dropout linear regula-
                                                                          tor that powers the HMC735 VCO. This high output current LDO is
                                                                          ideal for regulation in noise-sensitive applications such as ADC and
                                                                          DAC circuits, precision amplifiers, PLLs/VCOs, and clocking ICs.
                   Figure 17. Transmit Antenna Switch
                                                                          The LT3460 step-up DC/DC converter and ADP7118 LDO boost the
DIGITAL CONTROL AND LEVEL SHIFTING                                        5 V input voltage to 15 V, then regulate to 14 V, which is used as
                                                                          the supply of the AD8065 amplifier. It uses a constant frequency,
A Raspberry Pi 4 platform board provides all serial peripheral            current-mode control scheme to provide line and load regulation.
interface (SPI), I2C, and discrete digital I/O control signals. The       The ADP7118 is a CMOS, low dropout linear regulator that provides
Raspberry Pi has logic levels of 3.3 V, which are either used directly    high power supply rejection, minimizing synthesizer phase noise.
or level-shifted to 1.8 V for interfacing with the ADAR1000 and
ADF4159. Dual supply level translators are used, with supply pins         SYSTEM MONITORING AND CONTROL
tied directly to the Raspberry Pi's 3.3 V logic supply and the 1.8 V      The AD7291 8-channel, I2C, 12-bit successive approximation regis-
digital supply. This ensures that the device's digital pins never see a   ter (SAR) ADC with temperature sensor provides extensive system
high logic level when not powered.                                        diagnostics. All supply voltages are monitored, as well as the VCO
The ADF4159 MUXOUT also serves as a PLL lock indicator and                tuning voltage. The AD7291 input range is 0 V to 2.5 V; resistor
an end-of-ramp indicator in FMCW modes. A 3.3 V, level-shifted            dividers scale the measured voltage appropriately. The ADC is
version of MUXOUT drives an LED indicator that shows the PLL              placed close to the ADAR1000s, providing an approximate meas-
lock state.                                                               urement of the board's temperature rise. The measured parameters
                                                                          and scale factors are shown in Table 1.
POWER ARCHITECTURE
                                                                          Table 1. Measured Parameters and Scale Factors
The CN0566 derives power directly from a single USB-C receptacle           AD7291 Input              Parameter             Divider Scale Factor
that provides 5 V, 3 A power. This is forwarded to the Raspberry
                                                                               VIN0                  1.8 V supply                    2 V/V
Pi through the 40-pin expansion header, as well as the rest of the
                                                                               VIN1                  3.0 V supply                    2 V/V
on-board power management. Figure 18 shows the complete power
                                                                               VIN2                  3.3 V supply                    2 V/V
tree of the CN0566.
                                                                               VIN3                  4.5 V supply                  4.01 V/V
                                                                               VIN4           Supply of AD8065 amplifier           7.98 V/V

analog.com                                                                                                                      Rev. 0 | 7 of 11
Circuit Note                                                                                                                  CN-0566
Table 1. Measured Parameters and Scale Factors (Continued)                between elements is 11.2 dB. Note that the strengths are quali-
 AD7291 Input              Parameter               Divider Scale Factor   tatively in two groups of four elements, indicating a mismatch
     VIN5                  Input voltage                   4.01 V/V       between the two channels.
     VIN6           Current monitor output of                1 A/V
                             LTC4217
     VIN7         Control voltage and modulation           7.98 V/V
                         input of HMC735


SYSTEM PERFORMANCE
Ideally, a beamforming array produces a beam that is aimed at
a desired angle and has a shape that is as close as possible
to the theoretical for a given element taper. For example, setting
every element to the same gain, with no phase shift, produces
a beam aimed at 0° (mechanical boresight), with a SIN(X)/X or
SINC1 profile. Reducing the gain of the outer elements in a trian-
gular profile produces a SINC2 profile, and applying progressively
increasing phase shifts across the elements steers the beam away
from mechanical boresight.                                                                 Figure 19. Uncalibrated Signal Strength

The ability to produce an accurate beam depends on the ability to         Next, measure and compensate for the residual mismatch between
accurately set the gain and phase of each element. The CN0566             element gains by following these steps:
includes several sources of both gain and phase error that cannot
be avoided:                                                               1. Set element 0 to maximum gain, and all other elements to
                                                                             minimum gain. Measure the RF signal strength.
► Mismatch in the elements themselves (likely the smallest error
                                                                          2. Repeat for the remaining elements, setting one element to
  source).                                                                   the maximum, the rest to a minimum. Measure the RF signal
► The ADAR1000's own gain and phase errors.                                  strength.
► A mismatch between the two ADAR1000 devices.                            3. Locate the element with the minimum gain. Calculate how much
► A mismatch between the two receive paths, including LO splitter,           the other elements' gains must be reduced to match that of the
  mixers, filters, and other passive components.                             minimum element.
► A mismatch between the receiver channels (PlutoSDR or other             4. Normalize the reduction factors to unity such that the desired
  SDR modules).                                                              beam taper can be multiplied by the reduction factors.
                                                                          5. Store these values in the gain calibration file.
System Calibration
                                                                          Figure 20 shows the signal strengths after calibration, with a maxi-
Since these errors cannot be avoided, the CN0566 software in-             mum mismatch of 0.51 dB.
cludes a calibration script. Either an external microwave source or
the on-board transmit output connected to an antenna, is placed
at mechanical boresight approximately 1 meter from the array. The
calibration script then runs through the following operations:
Measure and compensate transmit channel mismatch. This ensures
that as much of the ADAR1000s' 7-bit gain control is available for
accurately tapering the beam rather than compensating for transmit
channel mismatch. The procedure is as follows:
1. Set all ADAR1000-0 channels to zero phase, mid-scale gain;
   set all ADAR1000-1 channels to minimum gain. Measure
   RF signal strength for receive channel zero. Repeat with
   ADAR1000-0 set to zero gain.
2. Calculate how many decibels to increase the gain of the lower
   of the two receive channels such that the average mismatch is
   minimized.                                                                               Figure 20. Calibrated Signal Strength
3. Store these values to the channel calibration file.
                                                                          Next, measure and compensate for the phase mismatch between
Figure 19 shows the signal-relative signal strengths of each ele-         adjacent elements by following these steps:
ment in the array prior to compensation. The maximum mismatch

analog.com                                                                                                                          Rev. 0 | 8 of 11
Circuit Note                                                                                                             CN-0566
1. Set element 0, 1 to maximum gain, accounting for channel and        For half-duplex (transmit and receive) applications, the ADTR1107
   gain calibration factors.                                           is a 6 GHz to 18 GHz RF front-end. This device incorporates an
2. Set element 0 to zero phase, then step element 1 phase from 0       18 dB gain, 2.5 dB noise figure receive LNA, and a 25 dBm PSAT
   to 360º, measuring signal strength at each step.                    transmit amplifier with 22 ns switching speed between transmit and
   ► Phases are matched when the signal strength is maximized.         receive.
      However, it is much easier to locate the null when the           The ADAR1000EVAL1Z X/Ku phased array reference design is
      elements are 180° out-of-phase.                                  a 32-channel, half-duplex beamforming front-end that includes
3. Add 180° to the null phase. This is the phase that must be          an antenna with 10 GHz lattice spacing. When coupled with an
   added to element 1 to compensate for its phase mismatch.            ADXUD1AEBZ up/down converter board, an EVAL-AD9081 mixed
4. Repeat for adjacent pairs of elements (1-2, 2-3, 3-4, etc.).        front-end evaluation board and a supported FPGA development
5. Start with zero compensation for element 0 and add successive       platform, fully functional radar and communication systems can be
   adjacent element compensation values, resulting in a list of        prototyped.
   values that can be applied to the entire array.
6. Store these values in the phase calibration file.                   The ADAR3000 and ADAR3001 are 16-channel beamformers for
                                                                       the 17 GHz to 22 GHz and 27.5 GHz to 31 GHz applications,
Figure 21 shows the gain vs. phase difference between adjacent         respectively. These devices can be configured for either transmit
elements. Ideally, all nulls would be at ±180°.                        or receive, and implement a time delay (rather than phase adjust-
                                                                       ment), eliminating beam squint in wideband applications.

                                                                       The ADAR4002 single-channel, bidirectional beamformer with a
                                                                       frequency range of 0.5 GHz to 19 GHz. This device includes a
                                                                       programmable time delay from 0 ps to 508 ps (4 ps resolution) or
                                                                       0 ps to 254 ps (2 ns resolution), and 6-bit attenuation with 0.5 dB
                                                                       resolution.
                                                                       CIRCUIT EVALUATION AND TEST
                                                                       This section covers the setup and procedure for evaluating the
                                                                       EVAL-CN0566-RPIZ. For complete setup details and other impor-
                                                                       tant information, refer to the CN0566 User Guide.
                                                                       EQUIPMENT NEEDED
             Figure 21. Phase Sweeps of Adjacent Elements              ► CN0566 Kit including:
                                                                         ► EVAL-CN0566-RPIZ with attached Raspberry Pi 4 and Plu-
After calibration, gain and phase accuracy across the array ap-             toSDR
proaches the resolution of the ADAR1000 itself, which is better than     ► USB to micro-USB cable
0.5 dB with an adjustment range of 31 dB, and 2.8°, respectively.        ► SD card with Analog Devices, Inc. Kuiper Linux image
COMMON VARIATIONS                                                        ► 5 V, 3 A, USB-C wall adapter
                                                                         ► 10 GHz microwave source (motion sensor)
The CN0566 can be extended in the horizontal (azimuth) direction
by stacking additional boards side-by-side, allowing a narrower          ► Tripod
beam to be produced. A common LO must be used across all               For Running scripts locally on the Raspberry Pi
boards, and an SDR receiver with two synchronized inputs per
board must be used to digitize the IF outputs.                         ► Display monitor with HDMI
                                                                       ► Micro-HDMI to HDMI cable
If monopulse tracking and hybrid beamforming are not required,
the outputs of two or more ADAR1000s can be combined with a            ► USB keyboard and mouse
passive combiner and digitized by a single-channel ADC (such as        For running scripts on a remote host computer
the single RX input on a PlutoSDR).
                                                                       ► Windows, Linux, or Mac computer with MATLAB or Python IDE
An external, 8-element antenna can be used with the CN0566 via         ► Ethernet cable
optional SMP RF connectors. Any frequency plan that falls within
approximately 8 GHz to 14 GHz operating range can be implement-        GETTING STARTED
ed, changing the on-board splitters, low pass, and band-pass filters
accordingly.                                                           Configure the SD Card with Kuiper Linux for the CN0566 by
                                                                       following the instructions in the CN0566 User Guide. Insert the SD
                                                                       card into the Raspberry Pi's SD card slot.

analog.com                                                                                                                 Rev. 0 | 9 of 11
Circuit Note                                                            CN-0566
SETUP AND TEST
Refer to the connection diagram shown in Figure 22.




                 Figure 22. CN0566 Connection Diagram

1. Connect the PlutoSDR's center micro-USB connector to one of
   the Raspberry Pi USB ports using the supplied cable.
2. Carefully thread the tripod into the tripod mount.
3. Plug the USB-C wall adapter into the USB-C power jack on the
   EVAL-CN0566-RPIZ.
4. Power up the microwave source with two AA cells or a 3 Volt
   power supply. Aim the source at the antenna array.
To run Python examples directly on the Raspberry Pi:
1. Connect the Raspberry Pi HDMI output closest to the power
   connector to the monitor via an HDMI cable.
2. Connect the USB keyboard and mouse to the Raspberry Pi
   USB ports.
3. Open a terminal and run the cn0566_find_hb100.py script
4. Verify that the spectrum plot shows a single, prominent tone.
   Type "y", then <enter> to save the frequency.
5. Open the cn0566_gui.py script and click the RUN button. In the
   GUI screen, click the "Auto Refresh Data" check box, then the
   "Acquire Data" button. Observe the beam pattern.
To run MATLAB examples on a host computer:
1. Connect the Windows, Mac, or Linux host computer to the
   Raspberry Pi with the the Ethernet cable.
2. Open MATLAB and run the phaser_hb100_scan.m script.
3. Run the phaser_rxtx.m script and observe the beam pattern.




   Figure 23. Typical Beam Pattern with HB100 at Mechanical Boresight




analog.com                                                              Rev. 0 | 10 of 11
Circuit Note                                                                                                                                                                   CN-0566
LEARN MORE                                                                                                AD7291 Data Sheet
CN0566 Design Support Package                                                                             AD7291 Evaluation Board
Keith Benson. 2019."Phased Array Beamforming ICs Simplify An-                                             LT3460 Data Sheet
tenna Design." Analog Devices.                                                                            LT3460 Evaluation Board
Peter Delos, Sam Ringwood, and Michael Jones. "Hybrid Beam-                                               HMC735 Data Sheet
forming Receiver Dynamic Range Theory to Practice." Analog Devi-
ces.                                                                                                      HMC735 Evaluation Board
Peter Delos, Bob Broughton, and Jon Kraft. 2020. "Phased Array                                            HMC652 Data Sheet
Antenna Patterns—Part 1: Linear Array Beam Characteristics and                                            HMC654 Data Sheet
Array Factor." Analog Devices.
                                                                                                          LTC4217 Data Sheet
                                                                                                          LTC4217 Evaluation Board
DATA SHEETS AND EVALUATION BOARDS
                                                                                                          ADP7118 Data Sheet
ADAR1000 Data Sheet
                                                                                                          ADP7118 Evaluation Board
ADAR1000 Evaluation Board
                                                                                                          ADP7158 Data Sheet
ADF4159 Data Sheet
                                                                                                          ADP7158 Evaluation Board
ADF4159 Evaluation Board
                                                                                                          ADM7150 Data Sheet
ADRF5019 Data Sheet
                                                                                                          ADM7150 Evaluation Board
AD8065 Data Sheet
                                                                                                          ADM7170 Data Sheet
ADL8107 Data Sheet
                                                                                                          ADM7170 Evaluation Board
ADL8107 Evaluation Board
LTC5548 Data Sheet
                                                                                                          REVISION HISTORY
LTC5548 Evaluation Board
LT8609S Data Sheet                                                                                        04/2023—Revision 0: Initial Version
LT8609S Evaluation Board




                  ESD Caution
                  ESD (electrostatic discharge) sensitive device. Charged devices and circuit boards can discharge without detection. Although this product features patented or proprietary
                  protection circuitry, damage may occur on devices subjected to high energy ESD. Therefore, proper ESD precautions should be taken to avoid performance degradation or loss of
                  functionality.

(Continued from first page) Circuits from the Lab circuits are intended only for use with Analog Devices products and are the intellectual property of Analog Devices or its licensors. While you may
use the Circuits from the Lab circuits in the design of your product, no other license is granted by implication or otherwise under any patents or other intellectual property by application or use of the
Circuits from the Lab circuits. Information furnished by Analog Devices is believed to be accurate and reliable. However, Circuits from the Lab circuits are supplied "as is" and without warranties of
any kind, express, implied, or statutory including, but not limited to, any implied warranty of merchantability, noninfringement or fitness for a particular purpose and no responsibility is assumed by
Analog Devices for their use, nor for any infringements of patents or other rights of third parties that may result from their use. Analog Devices reserves the right to change any Circuits from the Lab
circuits at any time without notice but is under no obligation to do so.


                                                                 ©2023-2023 Analog Devices, Inc. All rights reserved. Trademarks and                                             Rev. 0 | 11 of 11
                                                                 registered trademarks are the property of their respective owners.
                                                                 One Analog Way, Wilmington, MA 01887-2356, U.S.A.
