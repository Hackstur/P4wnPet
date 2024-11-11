#imports 
import asyncio
import traceback
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.core.sprite_system import framerate_regulator
from luma.core import lib
from luma.oled.device import sh1106
import RPi.GPIO as GPIO
import datetime
import time
import subprocess
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import socket, sys
import os
import base64
import struct
import smbus

from core.menu_manager import Menu, MenuItem, menu_manager
from core.config import config

from core.event_system import event_system

from core.logger import setup_logger
logger = setup_logger(__name__)


class Fonts:
    Default = ImageFont.load_default()
    MenuItem = ImageFont.truetype('plugins/OLED/fonts/pzim3x5.ttf', 10)
    MenuTitle = ImageFont.truetype('plugins/OLED/fonts/FreePixel.ttf', 12)
    KeyBoard = ImageFont.truetype('plugins/OLED/fonts/FreePixel.ttf', 8)
    Text = ImageFont.truetype('plugins/OLED/fonts/miscfs__.ttf', 14)



class OLED_128x64:
    def __init__(self):
        self.name="OLED 128x64 Display"
        self.author="Hackstur"
        self.description="Manage OLED 128x64 dislay"
        
        
        
    def initialize(self):
        # LOOP LOCK
        self.active=False
        # SELF VARS
        self.key = {
            'up': 6,
            'down': 19,
            'press': 13,
            'right': 26,
            'left': 5,
            'key1': 21,
            'key2': 20,
            'key3': 16
        }
        
        # ADJUST MENU
        self.menu_max_lines = 5
        self.menu_line_size = 9

        # ICONS
        self.menu_icon=Image.open("plugins/OLED/icons/menu_icon.png")
        self.menu_close = Image.open("plugins/OLED/icons/menu_close.png")

        # IMAGE BUFFER
        self.image=Image.new('1',(128,64))

        # GPIO INITS
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(25,GPIO.OUT)
        GPIO.output(25,GPIO.HIGH)
        serial = serial = spi(device=0, port=0, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = 24, gpio_RST = 25)
        self.device=sh1106(serial, rotate=2) #sh1106
        # Configurar cada pin como entrada con resistencia pull-up-down
        for key in self.key.values():
            GPIO.setup(key, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Asignar eventos de detección para los botones
        for key in self.key.values():
            GPIO.add_event_detect(key, GPIO.FALLING, bouncetime=300)
        
        event_system.subscribe("p4wn_start", self._on_start)
        event_system.subscribe("p4wn_hidscripts_menu", self._on_hidscripts_menu)
        event_system.subscribe("p4wn_alert", self._on_alert)


    def stop(self):
        #event_system.unsubscribe("event_p4wnpet_hidscripts_menu", self._on_menu)
        pass
        

    def loop(self):
        logger.info("[OLED] Initialize main loop") 
        while self.active:

            # Crea un buffer de imagen en lugar de dibujar directamente en el dispositivo
            draw = ImageDraw.Draw(self.image)
            
            # Realiza todos los dibujos en el buffer
            draw.rectangle((0, 0, self.image.width, self.image.height), outline=0, fill=0)
            self.draw_status_bar(draw)

            # Finalmente, envía la imagen completa al dispositivo
            self.device.display(self.image)
        


            if GPIO.event_detected(self.key['key1']): # OPEN MAIN MENU
                logger.info("KEY 1")
                self.open_menu()
            else:
                a=1
                

    #region STATUS BAR

    def draw_status_bar(self, draw):
        # Realiza todos los dibujos en el buffer
        draw.rectangle((0, 0, self.image.width, 12), outline=0, fill=1)
        # Finalmente, envía la imagen completa al dispositivo
        self.image.paste(self.menu_icon, (116, 0))

    #endregion    
    
    #region MENU DRAWS      

    def open_menu(self):
            keep=True
            
            while keep:
                if GPIO.event_detected(self.key['down']):
                    logger.info("KEY DOWN")
                    current_index = menu_manager.current_menu.current_index
                    if current_index < len(menu_manager.current_menu.items) - 1:
                        self.update_menu_selection(current_index, increment=True)
                    

                elif GPIO.event_detected(self.key['up']):
                    logger.info("KEY UP")
                    current_index = menu_manager.current_menu.current_index
                    if current_index > 0:
                        self.update_menu_selection(current_index, increment=False)

                elif GPIO.event_detected(self.key['press']):
                    logger.info("KEY PRESS")
                    if menu_manager.current_menu.get_current_item().action_select:
                        menu_manager.select_current_item()
                    elif menu_manager.current_menu.get_current_item().submenu:
                        
                        menu_manager.select_current_item()
                
                elif GPIO.event_detected(self.key['right']):
                    logger.info("KEY RIGHT")

                elif GPIO.event_detected(self.key['left']):
                    logger.info("KEY LEFT")

                elif GPIO.event_detected(self.key['key1']): # OPEN MAIN MENU
                    logger.info("KEY 1")
                    if len(menu_manager.menu_stack) > 1:
                        menu_manager.back()
                    else:
                        keep=False
                        


                elif GPIO.event_detected(self.key['key2']):
                    logger.info("KEY 2")

                elif GPIO.event_detected(self.key['key3']):
                    logger.info("KEY 3")
                

                self.draw_menu(menu_manager.current_menu)
     
     
    def update_menu_selection(self, current_index, increment):
        if increment:
            menu_manager.current_menu.items[current_index].selected = False
            menu_manager.navigate_down()
            new_index = current_index + 1
        else:
            menu_manager.current_menu.items[current_index].selected = False
            menu_manager.navigate_up()
            new_index = current_index - 1

        menu_manager.current_menu.items[new_index].selected = True

        # Control de desplazamiento en el menú
        if (increment and new_index - menu_manager.current_menu.menu_cur_top > (self.menu_max_lines // 2) + 1) or \
           (not increment and new_index < menu_manager.current_menu.menu_cur_top):
            menu_manager.current_menu.menu_cur_top += 1 if increment else -1

          
    def draw_menu(self, menu):
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((0, 0, self.image.width, self.image.height), outline=0, fill=0)
        
        draw.rectangle((0, 0, self.image.width, 11), outline=0, fill=1)
        draw.text((1, 1), menu.name, font=Fonts.MenuTitle, fill=0)
        self.image.paste(self.menu_close, (116,0))


        y = 14
        index = 0
        draw.rectangle((0, y, self.image.width, self.image.height), outline=0, fill=0)

        for item in menu.items:
            if index >= menu_manager.current_menu.menu_cur_top and \
               index < menu_manager.current_menu.menu_cur_top + self.menu_max_lines:
                if index == menu.current_index:
                    draw.rectangle((2, ((index - menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y,
                                         self.image.width - 5,
                                         ((index - menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + self.menu_line_size - 1), outline=0, fill=1)
                    text = item.name
                    
                    draw.text((4, ((index - menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + 2), text, font=Fonts.MenuItem, fill=0)
                else:
                    text = item.name
                    
                    draw.text((4, ((index - menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + 2), text, font=Fonts.MenuItem, fill=1)
            index += 1

        for p in range(14, 64, 2):
            draw.point((126, p), fill=1)

        visible_items = self.menu_max_lines
        if len(menu.items) > visible_items:
            scrollbar_height = max(5, int(visible_items / len(menu.items) * (self.image.height - y)))
            scrollbar_position = int(((menu.current_index / len(menu.items)) * (self.image.height - y - scrollbar_height)) + y)

            draw.rectangle((self.image.width - 4, scrollbar_position, self.image.width, scrollbar_position + scrollbar_height), outline=0, fill=1)

        self.device.display(self.image)

    #endregion


    #region DISPLAY MESSAGE/ALERT

    def split_message(self, message, max_width, font):
        words = message.split()  # Divide el mensaje en palabras
        lines = []
        current_line = ""

        for word in words:
            # Prueba agregando la palabra a la línea actual
            test_line = current_line + " " + word if current_line else word
            # Calcula el ancho de la línea de prueba
            width, _ = font.getmask(test_line).getbbox()[2:4]  # Usamos getmask para obtener el tamaño de la línea
            if width <= max_width:
                # Si la línea cabe, la establecemos como la línea actual
                current_line = test_line
            else:
                # Si no cabe, añade la línea actual a la lista de líneas y comienza una nueva
                lines.append(current_line)
                current_line = word

        # Añade la última línea
        if current_line:
            lines.append(current_line)
        
        return lines


    def display_message(self, message="", ok_callback=None, cancel_callback=None):
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((0, 0, self.image.width - 1, self.image.height - 1), outline=0, fill=0)
        
        # Espacio disponible para el texto (dejamos espacio para el botón OK)
        usable_height = self.image.height - 24
        lines = self.split_message(message, self.image.width - 8, Fonts.Text)

        # Centramos el texto verticalmente en el área disponible
        text_height = len(lines) * 14
        start_y = (usable_height - text_height) // 2

        # Dibuja cada línea centrada en X e Y
        for i, line in enumerate(lines):
            # Usamos textbbox para obtener las dimensiones del texto
            bbox = draw.textbbox((0, 0), line, font=Fonts.Text)
            text_width = bbox[2] - bbox[0]  # Ancho del texto
            text_height = bbox[3] - bbox[1]  # Altura del texto
            x = (self.image.width - text_width) // 2
            y = start_y + i * 14
            draw.text((x, y+1), line, font=Fonts.Text, fill=1)

        # Dibuja el botón "OK" en la parte inferior
        if ok_callback:
            draw.rectangle((30, self.image.height - 18, self.image.width - 30, self.image.height - 6), outline=0, fill=1)
            draw.text((45, self.image.height - 17), "OK", font=Fonts.MenuItem, fill=0)

        # Muestra el resultado en la pantalla OLED
        self.device.display(self.image)

        # Espera interacción del usuario si `ok_callback` está activo
        if ok_callback == True:
            while True:
                if GPIO.event_detected(self.key['key2']):
                    logger.info("OK button pressed. Exiting message display.")
                    break

    #endregion


    #region EVENTS

    def _on_start(self):
        try:
            self.active=True
            asyncio.create_task(self.loop())  # Crear tarea asíncrona
        except Exception as e:
            error_traceback=traceback.format_exc()
            logger.error(f"[OLED] {e}\n{error_traceback}")

    def _on_alert(self, message, ok_callback=None, cancel_callback=None):
        self.display_message(message, ok_callback)


    def _on_hidscripts_menu(self, menuitem):
        submenu=Menu("OLED HID DEVICES")

        submenu.add_item(MenuItem(
            name="OLED HID MOUSE",
            action_select=lambda item:(self.open_mouse())
        ))
        submenu.add_item(MenuItem(
            name="OLED HID KEYBOARD",
            action_select=lambda item:(self.open_keyboard())
        ))
        submenu.add_item(MenuItem(
            name="OLED HID GAMEPAD",
            action_select=lambda item:(self.open_gamepad())
        ))
        menuitem.submenu.add_item(MenuItem(
            name="OLED HID DEVICES",
            submenu=submenu
        ))

    #endregion


    #region OLED HID DEVICES

    def open_mouse(self):
        draw = ImageDraw.Draw(self.image)
        keep=True
        while keep:

            draw.rectangle((0, 0,127,63), outline=0, fill=0) #clear canvas

            if GPIO.input(self.key['up']):
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=1, fill=0)
            else:
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'moveStepped(0,-"+str(config.data.hid.mouse_steps)+")'", shell=True)

            if GPIO.input(self.key['down']):
                draw.polygon([(30, 60), (40, 42), (20, 42)], outline=1, fill=0)
            else:
                draw.polygon([(30, 60), (40, 42), (20, 42)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'moveStepped(0,"+str(config.data.hid.mouse_steps)+")'", shell=True)

            if GPIO.input(self.key['left']):
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=1, fill=0)
            else:
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'moveStepped(-"+str(config.data.hid.mouse_steps)+",0)'", shell=True)
            
            if GPIO.input(self.key['right']):
                draw.polygon([(60, 30), (42, 21), (42, 41)], outline=1, fill=0)
            else:
                draw.polygon([(60, 30), (42, 21), (42, 41)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'moveStepped("+str(config.data.hid.mouse_steps)+",0)'", shell=True)

            if GPIO.input(self.key['press']):
                draw.rectangle((20, 22,40,40), outline=1, fill=0)
            
            else:
                draw.rectangle((20, 22,40,40), outline=1, fill=1)
                

            if GPIO.input(self.key['key1']):
                draw.ellipse((70,0,90,20), outline=1, fill=0)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True)
            else:
                draw.ellipse((70,0,90,20), outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'button(BT1)'", shell=True)

            if GPIO.input(self.key['key3']):
                draw.ellipse((70,40,90,60), outline=1, fill=0)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True)
            else:
                draw.ellipse((70,40,90,60), outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'button(BT2)'", shell=True)

            if GPIO.event_detected(self.key['key2']):
                keep=False

            draw.text((74, 28), "Key2:Exit",  font=Fonts.MenuItem, fill=1)  

            self.device.display(self.image)
            
    def open_gamepad(self):
        draw = ImageDraw.Draw(self.image)
        keep=True
        while keep:

            draw.rectangle((0, 0,127,63), outline=0, fill=0) #clear canvas

            if GPIO.input(self.key['up']):
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=1, fill=0)
            else:
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"UP\")'", shell=True)

            if GPIO.input(self.key['down']):
                draw.polygon([(30, 60), (40, 42), (20, 42)], outline=1, fill=0)
            else:
                draw.polygon([(30, 60), (40, 42), (20, 42)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"DOWN\")'", shell=True)

            if GPIO.input(self.key['left']):
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=1, fill=0)
            else:
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"LEFT\")'", shell=True)
            
            if GPIO.input(self.key['right']):
                draw.polygon([(60, 30), (42, 21), (42, 41)], outline=1, fill=0)
            else:
                draw.polygon([(60, 30), (42, 21), (42, 41)], outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"RIGHT\")'", shell=True)

            if GPIO.event_detected(self.key['press']):
                keep=False

                

            if GPIO.input(self.key['key1']):
                draw.ellipse((70,0,90,20), outline=1, fill=0)
            else:
                draw.ellipse((70,0,90,20), outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"Q\")'", shell=True)

            if GPIO.input(self.key['key2']):
                draw.ellipse((100,20,120,40), outline=1, fill=0)
            else:
                draw.ellipse((100,20,120,40), outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"W\")'", shell=True)

            if GPIO.input(self.key['key3']):
                draw.ellipse((70,40,90,60), outline=1, fill=0)
            else:
                draw.ellipse((70,40,90,60), outline=1, fill=1)
                exe=subprocess.check_output("P4wnP1_cli hid run -c 'press(\"E\")'", shell=True)


            draw.rectangle((20, 22,40,40), outline=1, fill=1)
            draw.text((22, 30), "Exit",  font=Fonts.MenuItem, fill=0)  

            self.device.display(self.image)

    def open_keyboard(self):
        layouts = {
            'lowercase': [
                ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
                ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
                ["z", "x", "c", "v", "b", "n", "m"]
            ],
            'uppercase': [
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
                ["Z", "X", "C", "V", "B", "N", "M"]
            ],
            'numbers': [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
            ],
            'symbols': [
                ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"],
                ["-", "_", "=", "+", "{", "}", "[", "]", "\\", "|"],
                ["/", ":", ";", "\"", "'", "<", ">", ",", ".", "?"]
            ]
        }
        current_layout="lowercase"
        row=0
        col=0

        draw = ImageDraw.Draw(self.image)
        keep=True
        while keep:
            draw.rectangle((0, 0,127,63), outline=0, fill=0) #clear canvas
            # Dibujar la cuadrícula del teclado
            for r, row in enumerate(layouts[current_layout]):
                for c, char in enumerate(row):
                    x = c * 12  # Espaciado entre teclas horizontal
                    y = 20 + r * 14  # Espaciado entre teclas vertical

                    # Dibujar la tecla con un borde si está seleccionada
                    if r == row and c == col:
                        draw.rectangle((x, y, x+10, y+10), outline=1, fill=1)  # Selección
                        draw.text((x+4, y+3), char, font=Fonts.MenuItem, fill=0)  # Texto de la tecla seleccionada
                    else:
                        draw.rectangle((x, y, x+10, y+10), outline=1, fill=0)  # Teclas no seleccionadas
                        draw.text((x+4, y+3), char, font=Fonts.MenuItem, fill=1)  # Texto de las teclas no seleccionadas


            self.device.display(self.image)
    #endregion