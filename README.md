<!------------------- HEADER SECTION -------------------------->
<header>
 <h1 align="center"><strong> d｡◕‿↼｡bづ </strong><br/>P4wnPet (P4wnP1 A.L.O.A based virtual pet)</h1>
  <!-- BADGET BUTTONS -->
<p align="center">
  <img src="https://img.shields.io/badge/Status-Development-lightgray.svg?style=flat" />
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat" />
 </p>
</header>
<p></p> <!-- BLANK PARAGRAPH TO FIX HTML HEADER IN GITHUB PAGES TEMPLATE -->
<!------------------- END OF HEADER SECTION -------------------->
<!-- INTRODUCTION -->

## 💬 Introduction  

**NOTE:** Im not include the requeriments yet. As a resume: I install P4wnP1 aloa image, im change the repos to debian in order to be able to update and install new packages, finally im install a lot of python3 shit, change boot.ini, etc... ill do a little guide some day.

**P4wnPet** is a Python application designed for the Raspberry Pi Zero W and is closely integrated with the P4wnP1 ALOA framework. Conceptually, it’s (will be) a "Tamagotchi" with pentest capabilities.

I'm trying to create something similar to the Bashbunny, but I believe that with P4wnP1, Kali, and a bit of creativity, it could become a 'Bashbunny on steroids' (except for the speed during Plug and Pwn, but that can be resolved by adding an external battery to the Pi Zero W). The pet is only for fun.

Currently working features:

- P4wnPet strong core: 
  - Plugin manager
  - Event system
  - Process Manager
  - Menu manager (i think can be better.. but for now, works "fine").

- 2 example plugins:
  - OLED Waveshare 128x64 display (Maybe will be moved to core)
  - JokerShell, pranks in powershell

- Menus for deploy:
  - P4wnP1 Templates

- System Information: accurated system info.

- Settings:
  - Toggle DWC2, AUDIO, HDMI
  - Overclock

- Useful Commands:
  - Clear HIDscript Temporal files
  - Restart or shutdown P4wnPet related services/System

- USB Mass Storage
  - Mount .bin images as USB

- HID P4wns
 - HIDScripts (Launch P4wnP1 HIDScripts)
 - HIDDevices (Emulate devices with P4wnP1 HIDScript)
   - Mouse
   - Gamepad
   - Keyboard (WIP)
 - HOST Information (Get information with NMAP from USB connected host)


- WIFI P4wns
  - Toggle monitor mode (maybe will be mixed with other commands to be more user friendly)
  - Bettercap recon (WIP)



Wishes:
- DuckyScript interpreter
- Bashbunny interpreter
- DigiSpark board flash
- Proxmark handler
- BlueDucky P4wn.. (start bluetooth p4wn)
- More ideas :D
- Document and optimice all code, now is CHAOS!

<br/>


Projects that inspire me:

 - https://github.com/RoganDawes/P4wnP1_aloa

 - https://github.com/NightRang3r/P4wnP1-A.L.O.A.-Payloads

 - https://github.com/evilsocket/pwnagotchi





> If you want to **improve** this project, please, **read** the [`Contributors section`](#-contribute).


## 💎 Contribute
Feel free to send us a message for anything. We'd love to ear about improve!.

Please, have a look at the [Contributor Covenant][contributor covenant].

<!-- TEAM -->

## 🏀 Team  
Only me.

<!-- LICENSE -->
## 🎓 License  
<sub> © 2024 Hackstur </sub>  

This project is released under the terms of the [MIT][license file] license.

<!------------ RELATIVE LINKS ----------->

[license file]: LICENSE  
[contributor covenant]: https://www.contributor-covenant.org/version/1/4/code-of-conduct.htm  
