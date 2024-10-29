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

**P4wnPet** is a Python application designed for the Raspberry Pi Zero W and is closely integrated with the P4wnP1 ALOA framework. Conceptually, it’s a “tamagotchi” with hacking capabilities, enabling users to interact with a virtual pet that can execute various commands through its menu system.

Although still in its early stages, P4wnPet currently focuses on the character's animations, while commands and plugins are under development. Given its experimental nature, P4wnPet is highly flexible, with the design and functionality evolving rapidly as new features and adjustments are added. This playful yet technical project aims to provide both entertainment and potentially useful functionalities through the P4wnP1 ALOA platform.

For today, im focus on develop new ideas or systems for P4wnPet, some of them maybe dont work because im sure it will work in a future.

The things actually work:

- P4wnPet strong core. Module system, Event system and Process Manager.
- P4wnPet menu for P4wnP1 Template list. You can load a template from menu.
- P4wnPet menu for HID scripts & devices:
  - P4wnP1 HIDScript
  - OS SHELL Scripts (Powershell, CMD, etc)
  - HID Mouse & Keyboard (Not integrated yet, but works "fine")

- P4wnPet menu fir WIFI audit tools:
  - Get Wpa Handshake
  - MDK3 Beacon Flood

My prayer list:
- Bluetooth P4wns (Some works on console, like BlueDucky attacks or scan)
- Improve get the handshake by deauth attack (actually the function say "no clients in ap" LOL)
-Better core: Im thinking get out the menu from pet class, and maybe transform some utils in modules (wifi audit, etc)
-Better system: Make the app install automatically the service for itself, restart when break, etc.
-Tamagotchi system: Actually the pet its only a sprite walking trough the screen.
-UI system: Actually the UI have nothing... i need to develop a background process who change the icons of wifi, bluetooth, aps in range, etc.

<br/>



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
