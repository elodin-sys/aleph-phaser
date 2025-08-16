
Dan Driscoll
Apr 9, 2025, 1:18 PM

My name is Dan Driscoll. I'm the CEO & co-founder of Elodin.

Cutting right to it. I've followed along with your Phaser development kit for a while now, and I love the YouTube videos, I've even watched them with my kids to generate excitement about RF technologies and applications in general. Truly inspiring for us, thank you for creating and sharing.

We make a Jetson Orin NX-based flight computer, and while initially built for flight use-cases, it would make for a powerful AI-capable companion computer to pair with Phaser. I'd love to meet up and discuss how we might work together.

Best,
Dan

Jon Kraft
Apr 9, 2025, 3:48 PM

Hi Dan, thanks for reaching out.  That sounds very interesting!  Yes, I'd love to talk about something we could do together.  I'm traveling next week, but how about a Teams call this Friday or Saturday?  My work email is jon.kraft@analog.com


Jon Kraft
May 22, 2025, 9:28 AM

This meeting is to kick off a discussion with Dan Driscoll, CEO & co-founder of Elodin. And Dave LoCascio, Director of System Platforms at Analog Devices. 

Elodin makes a Jetson Orin NX-based flight computer, and while initially built for flight use-cases, it would make for a powerful AI-capable companion computer to pair with ADI radar platforms.  We thought we could start with Phaser and see how that works.  But possibly expand it to our higher performance systems in the future.


Dan Driscoll
May 31, 2025, 1:12 PM

I just worked through the quickstart; this thing is so cool.

From my take, the majority of the work for us here will be getting you a working Linux GUI. Our current Aleph OS is headless, meant to be as fully stripped down as possible for professional use-cases. So we'll need to layer into the image all the Gnome, VNC or other UI packages as necessary to get it ready to support Phaser. I did want to ask first, though, do you already support workflows that are 100% over an SSH connection / no GUI on the device? Send me the docs/video walk-through of that if so, and I'll see if that's something that will be more immediately doable. We want to have a GUI-included Aleph OS image anyway, so it's all good if this is your customer's preference for development.

Also, what is the max range of the Phaser? I'm sure it's dependent on the radiation source power / reflection. Just curious what you've seen.


Jon Kraft
Jun 2, 2025, 4:11 AM

Yes, you can operate without the Rasp Pi desktop.  You just plug Pluto’s USB into your computer.  And then in Python you create the Phaser object with the IP address of the Raspberry pi, which is set to phaser.local

There’s some examples of that here:  https://github.com/jonkraft/PhaserBeamforming

Yes, max range depends on the target.  But here’s a video of a small drone at 100m, and it shows up pretty well:

https://youtu.be/M1eXeqN1c-I?si=87EMvlv-dflUdX7i&t=445


Dan Driscoll
  May 31st at 1:01 PM
I just finished the full Phaser quickstart guide (there's a video running through it here). My take on it now, is the majority of the initial work here is largely just getting an Aleph image that supports all the GUI / UI aspects, and whatever VNC needs to work. I don't think you need to wait to ship this to Krackson, he just needs an Aleph to work on to start getting the Nix image built that will support this. He can test the majority of this getting started on it without the Phaser, the initialization script & running calibration and testing only happens at the very end. So feel free to get him started when ready.


Akhil Velagapudi
  May 31st at 1:15 PM
In the quickstart, the sdr is connected to the pi over usb + ethernet.
So all the gnuradio stuff is still running on pi. We need that to happen on Aleph by connecting the plutosdr to it directly. There's no real value in getting a VNC client to work on Aleph, because you can't interface with the radio at all through SSH or VNC. I think he needs the Phaser more than Aleph because if he gets any NixOS system (not ADI OS on Pi) talking to the SDR, then porting it to Aleph is pretty easy. The calibration stuff can still be done with the Pi.


Dan Driscoll
  May 31st at 1:25 PM
You're thinking with the Pi still in the solution, but I don't see that as a workable outcome. The Aleph should just be able to do everything the Pi can do, or it's really just not worth our time. I do see some evidence that they have workflows that are using an SSH connection, displaying all the results in MatLab so the need for a GUI might not be 100%, but it's certainly ideal for a hot-swap with the Pi


Akhil Velagapudi
  May 31st at 1:27 PM
Isn't that phase 3? That requires a custom expansion board. Not sure why we would start with that. @Sascha Wise correct me if I'm wrong but phases 1 + 2 were clearly with the Pi still in the picture handling all the SPI devices.


Akhil Velagapudi
  May 31st at 1:28 PM
It seems like were forcing the UI as a requirement into this. when this can run perfectly fine headless: https://github.com/analogdevicesinc/pyadi-iio/blob/cn0566_dev/examples/cn0566/cn0566_minimal_example.py


Dan Driscoll
  May 31st at 1:31 PM
yes this is good, it's just not the workflows I went through for testing it


Akhil Velagapudi
  May 31st at 1:31 PM
The lab in the url is using matplotlib and thonny as the gui/ide which supports ssh connection.


Akhil Velagapudi
  May 31st at 1:35 PM
but for all of this, you first need Aleph to talk to the sdr.


Dan Driscoll
  May 31st at 1:35 PM
No custom board needed, the stack has all the connections needed.


Akhil Velagapudi
  May 31st at 1:36 PM
It doesn't, there are 2 SPI devices and we don't expose jetson spi peripheral through connectors


Dan Driscoll
  May 31st at 1:37 PM
ah


Akhil Velagapudi
  May 31st at 1:37 PM
ADF4159 and ADAR1000


Dan Driscoll
  May 31st at 1:37 PM
Well that's unfortunate then, so that would be a change to the B2B connector pin out?


Akhil Velagapudi
  May 31st at 1:38 PM
We need a custom expansion board with a spi mux


Dan Driscoll
  May 31st at 1:39 PM
So it's already routed on the B2B but not made available


Akhil Velagapudi
  May 31st at 1:40 PM
Sort of, we need to multiplex multiple spi buses to a single one because the analog devices chips don't have spi chip selects, but this is only needed for calibration and not during normal operation. so, thats why I thought they're fine with using the pi just for that and have the Jetson do all the gnuradio <> plutosdr stuff, the stuff still running on the pi would be fairly trivial.


Jon Kraft
Jun 30, 2025, 12:43 PM

Hi Dan,

How is it going with the Phaser?  And I’m finally ordering this one today:

https://shop.elodin.systems/products/aleph-flight-computer?variant=50127470690602

That’s the correct one, right?  Sorry for the delay, I had to wait until my cost center was to switch to the proper group.  But I’m planning to order today, if we’re still on for this project. 


Dan Driscoll
Jun 30, 2025, 1:02 PM

That's the one!

No problem at all. Our developer was OOO until recently as well, and has just started looking into running the Phaser from Aleph to see how approachable it's going to be; I'm optimistic it'll be an easy bit of work to get it functioning as expected. Will keep you posted.


Jon Kraft
Jun 30, 2025, 1:09 PM

Great, ordered!

