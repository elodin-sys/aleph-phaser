Phased Array Exploration Workshop
Using Analog Device’s Adalm-PHaser

June 20, 2022


Phased Array Exploration Workshop
Using Analog Device’s Adalm-PHaser

June 20, 2022



Contents
Introduction	3
1.	Background and Purpose	3
2.	Additional Information and Resources	3
3.	Lab Setup	4
SDR and Software Control	7
1.	Training Objective	7
2.	Instructions	7
3.	Understand the Script	8
4.	Modify and Re-Run the script	8
Steering Angle	9
1.	Training Objective	9
2.	Instructions	9
Array Factor and Beamwidth	11
1.	Training Objective	11
2.	Instructions	11
Array Factor Measurements	12
1.	Training Objective	12
2.	Instructions	13
Measuring the Actual Antenna Pattern	15
1.	Training Objective	15
2.	Instructions	15
Sidelobes and Tapering	17
1.	Training Objective	17
2.	Instructions	17
Grating Lobes	18
1.	Training Objective	18
2.	Instructions	18
Beam Squint	20
1.	Training Objective	20
2.	Instructions	20
Quantization Sidelobes	22
1.	Training Objective	22
2.	Instructions	22
Hybrid Beamforming	24
1.	Training Objective	24
1.	Instructions	24
Monopulse Tracking	28
1.	Training Objective	28
2.	Instructions	28
FMCW Radar	30
1.	Training Objective	30
2.	Setup	30
3.	Instructions	32
Appendix:  ADALM-Phaser Frequency Plan	33


Introduction
Background and Purpose
Phased array beamforming has been used in radars and communication systems since the mid 20th century.  But in recent years, these systems have seen greater adoption in areas such as 5G mobile communications, automotive radar, satellite communications, and military applications.  
Yet, it can be difficult to gain an intuitive understanding of the fundamental concepts of these electronically steered arrays (ESA).  Therefore, the purpose of this workshop is to demystify the phased array terminology and equip you with a basic understanding of its underlying principles.  This will be accomplished with step by step, hands-on, labs covering the following topics:
	•	Using software to control the array and process data
	•	Setting the antenna’s steering angle
	•	Understanding the phased array’s antenna pattern
	•	Observing Antenna Impairments:
	•	Sidelobes and Tapering
	•	Grating Lobes
	•	Beam Squint
	•	Quantization Sidelobes
	•	Analog, Digital, and Hybrid Beamforming
	•	Monopulse Tracking
	•	FMCW Phased Array Radar

Additional Information and Resources
	•	More information on the hardware and software control can be found here:
wiki.analog.com/phaser
This site is still under development, with anticipated hardware launch end of summer 2022

	•	Much of this presentation and resultant lab exercises were taken from this article series:
https://www.analog.com/en/analog-dialogue/articles/phased-array-antenna-patterns-part1.html

	•	More information on Pluto and its software control can be found here:
wiki.analog.com/sdrseminars



Lab Setup
To accomplish these labs, we will be using Analog Device’s ADALM-PHASER (wiki.analog.com/phaser).  
The Phaser has the Pluto and Raspberry Pi directly attached to it.  Therefore, the only connections necessary are a 5V, 3A USB-C power supply, keyboard, mouse, and HDMI monitor.  All of these except the power supply are directly attached to the Raspberry Pi. After the peripherals are connected, apply power to the USB-C port on the Phaser board itself. (Leave the Raspberry Pi USB-C port disconnected.)  
To accomplish these labs, we will be using Analog Device’s ADALM-PHASER (wiki.analog.com/phaser).  
The Phaser has the Pluto and Raspberry Pi directly attached to it.  Therefore, the only connections necessary are a 5V, 3A USB-C power supply, keyboard, mouse, and HDMI monitor.  All of these except the power supply are directly attached to the Raspberry Pi. After the peripherals are connected, apply power to the USB-C port on the Phaser board itself. (Leave the Raspberry Pi USB-C port disconnected.)  



Figure 1: Standard lab setup





To generate the RF source for the phased array antennas to receive, we could use an antenna connected to the Phaser’s Tx port.  But instead, for most of the lab, it will be easier to use the battery powered HB100.  The “HB100” is a low cost 10.5 GHz source commonly used in occupancy detection systems.  The version we use is the SEN0192 from DF Robot:  https://www.dfrobot.com/product-1403.html.

“HB100”
“HB100”
https://www.limpkin.fr/public/HB100/HB100_Microwave_Sensor_Module_Datasheet.pdf

Using the HB100 allows us to have complete freedom in moving around the X band RF source.  This will be most useful in the Monopulse Tracking lab where we can move the RF source around the room and observe the lock and tracking.  



SDR and Software Control
	•	Training Objective

In this lab, we will learn how to control the Pluto SDR (software defined radio).  

We will aim the HB100 (approx. 10.5 GHz) at the Phaser board.  The Phaser will mix down that 10.5 GHz signal to about 2.2 GHz.  We then digitize that 2.2 GHz signal and plot the time and frequency spectrum.  By doing this we can see exactly what our HB100 frequency is (it is not well controlled – it could be anywhere from 10.1 to 10.7 GHz!).  And we can also see if there are any other signals nearby our HB100’s frequency.  
Instructions
	•	Aim the HB100 at the Phaser

	•	Open Thonny, by choosing Start  Programming  Thonny

	•	Select the “cn0566_minimal_example.py” tab

Figure 2: Run CN0566_minimal_example_test.py
	•	Click “Run”   
 

	•	View the resultant graph:

Figure 3: Plotting the Receive Signal of the HB100 
Understand the Script

Let’s understand that Python script we just ran, and make some modifications to it

Here’s what we’ve done:
	•	Received the 10.525 GHz signal
	•	Downconverted it to 2.2 GHz
	•	Received the 2.2 GHz IF with the Pluto SDR
	•	Set the Pluto’s internal PLLs to 2.2 GHz minus a small offset
	•	Set the Pluto’s ADC sample rate to 30 MSPS
	•	Loaded a 20 MHz wide digital filter into the Pluto
	•	Capture a buffer of 1024 samples
	•	Plot the time domain samples
	•	Take the FFT of the samples, then plot.

So what does that Python script do??   The python script, “cn0566_minimal_example.py” first takes care of some housekeeping operations - set the antenna to zero phase, equal gain on all elements, and set a few parameters in the Pluto SDR.  Then we are simply plotting the buffers of data from Pluto.  
	•	Change line 176 to something between -10e6 and +10e6 (your choice!).  And re-run the script.

Steering Angle
	•	Training Objective

In this lab, we’ll explore the relationship between the element to element phase shift and the resulting electrical steering angle

Instructions
	•	Find the “cn0566_gui.py” tab


	•	Press the green “Run” button
 
	•	You’ll see the FFT (amplitude vs frequency) of the HB100 source as received by the Phaser’s array:

	•	By adjusting the “Steering Angle” slider bar, you can change the phase values of each element.

	•	Move the HB100 to an angle of about 30 deg.  The protractor, can help you point this somewhat accurately.  Just place it on top of the Raspberry Pi, and move the arrow to 30 deg.



	•	Now slide the “Steering Angle” to find the phase delta that produces the maximum FFT amplitude.
	•	What phase delta do you observe that produces the maximum FFT amplitude?

	•	Now click on the “Rectangular Plot” tab


	•	This plots the peak FFT amplitude vs the selected steering angle

	•	Move the Steering Angle slider bar again.  

	•	Does the amplitude move in a predictable way?  What do you think is happening?   



Array Factor and Beamwidth
	•	Training Objective

In this lab, we will directly observe the array factor equation.  And then observe how the beamwidth changes with steering angle.  

Instructions
	•	In the Phaser GUI, select “Lab 2: Array Factor”

	•	Slowly move the HB100 in a half-circle around the array and observe the changes
	•	Does the main lobe’s beamwidth remain constant as you move the RF source?





	•	In the Phaser GUI, select “Polar Plot”

	•	This is the same data, just displayed on a polar grid
	•	Slowly move the HB100 in a half-circle around the array and observe the changes again

Array Factor Measurements
	•	Training Objective

In this lab, we will make measurements on the array pattern and compare to the theoretical values  

Recall that the array factor of a uniform, equally weighted (constant amplitude), linear array is given by:

And plotting this for various numbers of array elements (N) gives:

From this, we can make some measurements on the array:
	•	Halfpower Beam Width (HPBW):  Main lobe beamwidth, measured 3dB down from peak
	•	First Null Beam Width (FNBW):  Spacing between main lobe nulls
	•	First Sidelobe Amplitude:  Difference in amplitude (measured in dBc) from the main lobe to the first sidelobe on either side of the main lobe.
	•	Peak Amplitude:  signal strength of the main lobe (measured in dBFS for our lab)


From the array factor equation, with a frequency of 10.3GHz and element to element (d) spacing of 14mm, we can calculate the HPBW and FNBW for various numbers of elements:

HPBW
FNBW
N=8
13°
30°
N=4
27°
62°
N=2
62°
180°

Let’s measure this now and see how close we are to these calculated values.
Instructions
	•	In the Phaser GUI, select “Lab 2: Array Factor”

	•	Move the HB100 to the mechanical boresight location (i.e. directly facing the array)
	•	Record the following:
N
Peak Amplitude (dBFS)
HPBW (°)
Measured
HPBW (°)
Calculated
FNBW (°)
Measured
FNBW (°)
Calculated
First Sidelobe Amplitude (dBc)
8


13

30



	•	How do the HPBW and FNBW values compare with the calculated values?  



	•	In the Phaser GUI, select the “Gain” tab

	•	Click the Rx1_Gain button to disable that channel.

	•	Do the same for Rx2, Rx7, and Rx8.  We now have a 4 element array!



	•	Repeat the beamwidth measurements and compare to the calculated values and to the N=8 values.
N
Peak Amplitude (dBFS)
HPBW (°)
Measured
HPBW (°)
Calculated
FNBW (°)
Measured
FNBW (°)
Calculated
First Sidelobe Amplitude (dBc)
8


13

30

4


27

62

2


62

180





Measuring the Actual Antenna Pattern
	•	Training Objective

In this lab, we’ll make a simple measurement like what you would do in an antenna chamber.  It certainly won’t be perfect, but you’ll experience the process and then we’ll measure the sidelobe levels and see how they compare to the electrical scan method.   

Instructions
	•	In the Phaser GUI, select “Lab 2: Array Factor”
	•	In the “Config” tab, select “Signal vs Time” from “Mode Selection”.  This plots the peak amplitude vs time.

	•	Now rotate the HB100 in a radius around the Phaser board –keep the HB100 pointed at Phaser!

	•	Start at the left position (-90 deg), and move around to the right position (+90 deg)
	•	Keep a smooth, consistent speed!
	•	Practice a few times, then try time it so that one smooth rotation covers the entire graph span
	•	With practice, it may look like this:


	•	Ok, so we can’t really get angular measurements from this (we can never rotate it perfectly).  But we can get accurate lobe amplitudes.  Compare these amplitudes to your earlier measurements.  How close are they?

	•	Repeat the process, but change the “Steering Angle” from 0 deg to 30 deg


Sidelobes and Tapering
	•	Training Objective

In this lab, we’ll observe the side lobe amplitudes as we reduce the gain of the antenna elements at the edge of the array.  

Recall the impact to the sidelobe gain when we “window” or “taper” an array:

Instructions
	•	In the Phaser GUI, select “Lab 3: Tapering”

	•	Press “Copy Plot to Memory”, then try one of the tapering profile buttons.  

	•	What is the impact to sidelobe level, beamwidth, and peak gain?  

	•	Select “Symmetric Taper” and invent your own profile!  Can you make a “better” taper?
Grating Lobes
	•	Training Objective

In this lab, we will vary the effective element to element spacing to observe the formation of grating lobes.  Then compare to our calculated values.  

Recall that for the mechanical broadside condition (i.e. steering angle = 0 deg), that the main lobe position simplifies to:

So if  =29mm (which is the wavelength for 10.3 GHz), and d=14mm (which is indeed the element to element spacing on the Phaser array), then there is only one real solution to the equation above.  And MAIN = 0°.  So no surprises there!  
But if we change d to 42mm, then we will see 3 main lobes!  And they will be located at:
 = sin-1(m * 29mm/42mm) = 0° and ±44°
The true main lobe is at 0°.  And then the ±44° are the grating lobes. And we’ll actually see those grating lobes when we do the lab below.
But we can also change d to 56mm.  And in that case we will see “main” lobes at:  
 = sin-1(m * 29mm/56mm) = 0° and ±31° and ±90°
So let’s try it out in the lab, and see those grating lobes directly.  
Instructions
	•	In the Phaser GUI, select “Lab 4: Grating Lobes”

	•	Set the RF source (HB100) to be directly in front of the array (full broadside).  

	•	Set Rx2, Rx3, Rx5, Rx6, and Rx8 to 0.  Now our d = 3 * 14 mm = 42 mm



	•	Do you see two additional “main” lobes?  Does their peak angle match our calculations?  Why are they broader than the true main lobe?



	•	Let’s try it again, but now for d=56mm

	•	Set Rx2, Rx3, Rx4, Rx6, Rx7, and Rx8 to 0.  Now our d = 4 * 14 mm = 56 mm
	•	Again, check where the grating lobes are, and compare to what we calculated previously.  


Beam Squint
	•	Training Objective

In this lab, we will observe the change in steering angle as a function of signal frequency

Recall that beam deviation (beam squint) vs frequency can be calculated as:

	•	For example
	•	Let’s set our carrier frequency to be 10.5 GHz, and f0 = 10 GHz (500 MHz of BW)
	•	We want to steer the beam to +/- 45° from mechanical boresight
	•	∆ = arcsin(10.5/10 * sin(45°)) - 45°= 3°
	•	The beam will shift 3° at 10.5 GHz vs 10 GHz

Instructions
	•	In the Phaser GUI, select “Lab 5:  Beam Squint”

	•	Set the RF source (HB100) to an angle of about 50 deg
	•	Click “Copy Plot to Memory”
	•	Record the peak angle (you can also turn on “Show Peak Angle” under “Plot Options” tab)
	•	Change the “Signal BW” slider bar to 500 MHz


	•	Record the new peak angle.  Does the difference between the two peaks match our 3° calculation?

	•	Try other signal bandwidths and observe the effect. 

	•	Try other steering angles and observe the effect

Note:  since our HB100 frequency source is fixed, we instead change the frequency at which the steering angle is calculated.  i..e the “Beam Calculated at” frequency.  Both methods are equivalent.  Its just easier to change the calculated frequency in our lab.  It also avoids other changes in the antenna pattern that would come from a new frequency.  And that lets us do a more straightforward comparison.




Quantization Sidelobes
	•	Training Objective

In this lab, we will change the phase step size and observe the formation of quantization sidelobes

Instructions
	•	In the Phaser GUI, select “Lab 6:  Quantization”

	•	Click on the Gain tab and select a taper—we don’t want any sidelobes!   (Blackman is the pre-programmed default for this lab)

	•	In the “Config” tab, set the steering angle to 15 deg

	•	Move the HB100 in an arc around the Phaser.


	•	Keep the HB100 pointed at Phaser, and move at a smooth/consistent speed
	•	With practice, it may look like this:


	•	Our Blackman taper should have suppressed all the sidelobes.  So we are just seeing the true mainlobe at 15°

	•	Now, in the “Bits” tab:  slide “Phase Shift Bits” to 2


	•	Repeat moving the HB100 in an arc.  

	•	Do you see any new sidelobes?  




Hybrid Beamforming
	•	Training Objective

In this lab, we will observe the impact of changing gain and phase at the digital level, rather than the analog level.  
	•	Instructions
	•	In the Phaser GUI, select “Lab 7:  Hybrid Control”


	•	In the “Digital” tab, you can change the gain and phase of each ADAR1000 output:
Beam1 is elements 1-4 (the left 4 elements)
Beam0 is elements 5-8 (the right 4 elements)

	•	Set Beam0 gain to 0, and copy Plot to Memory (Copy Plot A)
	•	Then set Beam0 gain back to 1 and set Beam1 gain to 0, also copy this plot to Memory (Copy Plot B)

	•	Are the results the same?  And should they be the same? What might make them different?

	•	Set Beam0 back to 1 to see the left & right beams along with the total beam


	•	Select “Lab 7:  Hybrid Control” again, to reset all the settings
	•	Set “Beam1 Phase Shift” to +180 deg, then Copy that Plot to Memory

	•	Then return “Beam1 Phase shift” to 0 deg, and set Rx1-Rx4 to +180 deg in the “Phase” tab

	•	Can you find any differences between controlling things analog (Phase/Gain tabs) or digitally?


	•	Select “Lab 7:  Hybrid Control” again, to reset all the settings
	•	Copy Plot to Memory

	•	Set Beam 0 Phase Shift to a random value

	•	Go to the “Phase” Tab and start to adjust the phases for RX1-RX4 until you re-align the gain plot with the original. Hint: You should set them all to roughly the same value relative to each other


	•	How does the value of the Phase of RX1-RX4 compare with the value of the random Beam 0 Phase?


Monopulse Tracking
	•	Training Objective

In this lab, we will implement the monopulse tracking function that we worked out in the previous lecture.  Then we will observe it lock into a target and track its angle.  

Instructions
	•	In the Phaser GUI, select “Lab 8:  Monopulse Tracking”


	•	In the “Gain” tab, select “Blackmon” taper
	•	In the “Digital” tab, select “Show Delta” and “Show Error”


	•	From the lecture, what do the “Delta”, “Phase Delta”, and “Error Function” bars represent?  
	•	Rotate the array and observe the plots’ responses

	•	In the “Config” tab, select “Tracking” from the “Mode Selection” pull down menu

	•	Move the Phaser antenna and observe the tracking function in action







FMCW Radar
	•	Training Objective

In this lab, we will implement an FMCW radar and steer the phased array receiver

Recall that an FMCW (frequency modulated continuous wave) radar transmits a continuos frequency ramped signal:

The difference between the transmit and receive frequencies is the “beat frequency”, fb.  Using this beat frequency, we can compute the range to target as:
	

In this lab, we use a ramp time of TS=0.5 ms and a default frequency ramp bandwidth of B = 500 MHz (though this is adjustable in the lab).  With these values, we should expect to see a beat frequency of 6.7 kHz per meter of distance to the target.  
Setup
The setup for this lab is different from our previous phased array labs.  We will no longer be using the HB100—in fact make sure it is turned off!  Instead, we will transmit a frequency ramped waveform from Phaser, and then receive that with the 8 element linear array.  That signal will be mixed down, using the LTC5548 on board Phaser.  The LO of that mixer is the transmit frequency ramp.  Therefore, the mixer result is just the beat frequency.  That low bandwidth makes it very easy for Pluto to digitize.  
	•	Turn off the HB100!
	•	Place the corner reflector about 1 meter from the array
	•	Place the the Vivaldi transmit antenna next to the phased array and point it at the corner reflector.
So now our setup looks like this:






Instructions
	•	From Thonny, select “RADAR_FFT_Waterfall.py” and click the green “Run” button

	•	The top right graph is the FFT of the beat frequency.  The x-axis is frequency, by default.  But can be toggled to range by clicking the “Toggle Range” checkbox
	•	The bottom right graph is running plot of the FFT, over time.  Commonly called a “waterfall” plot or spectrogram.  The amplitude of the FFT bins is represented by white.  The higher the amplitude, the brighter the white.  

	•	Move the corner reflector back and forth in front of the display.  Do you see your pattern traced out in the waterfall plot?  Try adjusting the LOW and HIGH waterfall intensity levels to eliminate spurious clutter in the plot.  

	•	Now hold the target very close to the Phaser’s array (i.e. at distance 0m).  What is the frequency of the main peak?  It won’t be exactly at 100kHz – it might be 103kHz, or 99 kHz, etc.  This is the 0m frequency, and is a crude calibration of the system.  

	•	Now move the target to approximately 1m and observe the FFT plot.  Did the frequency move by about 6.7kHz?  Try moving to 2m, or 3m.  

Freq difference = 3*6.7k=20kHz
Freq difference = 3*6.7k=20kHz
“0m” Frequency
“0m” Frequency
Target at 3m
Target at 3m

	•	With the target still at a fixed distance, try varying the steering angle of the array.  Do you notice a change in FFT amplitude as you steer away from the target?  
Appendix:  ADALM-Phaser Frequency Plan	

