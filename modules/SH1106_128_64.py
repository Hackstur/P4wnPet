import asyncio
import os
from modules.SH1106.SH1106 import SH1106
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
from core.event_system import event_system
from core.logger import setup_logger
from modules.SH1106.sprite import Sprite
from core.menu_manager import Menu, MenuItem

logger = setup_logger(__name__)

class Fonts:
    Default = ImageFont.load_default()
    MenuItem = ImageFont.truetype('modules/SH1106/fonts/pzim3x5.ttf', 10)
    MenuTitle = ImageFont.truetype('modules/SH1106/fonts/FreePixel.ttf', 12)
    KeyBoard = ImageFont.truetype('modules/SH1106/fonts/FreePixel.ttf', 8)
    Text = ImageFont.truetype('modules/SH1106/fonts/miscfs__.ttf', 14)

class SH1106_128_64:
    def __init__(self):
        self.p4wnpet = None
        self.active = False  # Estado del módulo

        # ADJUST MENU
        self.menu_max_lines = 5
        self.menu_line_size = 9

        # SET KEYS (GPIO)
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

    def initialize(self, event_system):
        # SH1106 DISPLAY
        self.display = SH1106()
        self.display.Init()
        self.display.clear()
        self.image = Image.new('1', (self.display.width, self.display.height), "WHITE")
        self.draw = ImageDraw.Draw(self.image)

        #INTRO       
        self.image.paste(Image.open("modules/SH1106/images/intro.png"), (0, 0))

        self.wifi_icons = Image.open("modules/SH1106/images/wifi_signal.png")
        self.menu_icon = Image.open("modules/SH1106/images/menu_icon.png")
        self.menu_close = Image.open("modules/SH1106/images/menu_close.png")


        self.pet_skin="pumpkin"
        #self.pet_icons_normal=Image.open(f"modules/SH1106/p4wnpet_skins/{self.pet_skin}/{self.pet_skin}_normal.png")

        self.pet_positions= {
            'stay_normal'       : (0, [0, 1, 2, 3]),                   # Índice de frame para salsear
            'walk_right_normal' : (1, [0, 1, 2, 3]),
            'walk_left_normal'  : (2, [0, 1, 2, 3])
        }

        logger.info(f"PET SKIN: {self.pet_skin} in modules/SH1106/p4wnpet_skins/{self.pet_skin}/{self.pet_skin}_normal.png")
        self.pet_sprite=Sprite(f"modules/SH1106/p4wnpet_skins/{self.pet_skin}/{self.pet_skin}_normal.png", 32, 32, self.pet_positions, frame_duration=0, columns=4, behavior_type="bounce", screen_width=90, screen_height=30, offset=(0,11) )
        self.pet_sprite.set_animation("stay_normal")
       
        


        buffer = self.display.getbuffer(self.image)
        self.display.ShowImage(buffer)

        # GPIO INITS
        GPIO.setmode(GPIO.BCM)

        # Configurar cada pin como entrada con resistencia pull-up
        for key in self.key.values():
            GPIO.setup(key, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Asignar eventos de detección para los botones
        for key in self.key.values():
            GPIO.add_event_detect(key, GPIO.FALLING, bouncetime=300)

        

        # SUBSCRIBE EVENTS
        event_system.subscribe("event_p4wnpet_start", self._on_start)  # evento START
        event_system.subscribe("event_p4wnpet_alert", self._on_alert)  # evento ALERT
        event_system.subscribe("event_p4wnpet_modulesmenu", self._on_menu)  # evento ALERT

        logger.info("Module SH1106_128_64 Loaded!")

  
    
    def run(self):
        while self.active:
            #self.display.clear()
            self.draw.rectangle((0, 0, self.display.width, self.display.height), outline=1, fill=1)

            if GPIO.event_detected(self.key['down']):
                logger.info("KEY DOWN")
               

            elif GPIO.event_detected(self.key['up']):
                logger.info("KEY UP")
              

            elif GPIO.event_detected(self.key['press']):
               logger.info("KEY PRESS")

            elif GPIO.event_detected(self.key['right']):
                logger.info("KEY RIGHT")

            elif GPIO.event_detected(self.key['left']):
                logger.info("KEY LEFT")

            elif GPIO.event_detected(self.key['key1']): # OPEN MAIN MENU
                logger.info("KEY 1")
                self.open_menu()
                

            elif GPIO.event_detected(self.key['key2']):
                logger.info("KEY 2")

            elif GPIO.event_detected(self.key['key3']):
                logger.info("KEY 3")
            


            # dibujar cositas
            self.draw.rectangle((0, 0, self.display.width, self.display.height), outline=1, fill=1)
            #self.draw.rectangle((0, 12, 64, self.display.height-1), outline=0, fill=1)  # PET BOX
            self.pet_sprite.update()

            self.pet_sprite.draw(self.image)
            self.draw_status_bar()


            buffer = self.display.getbuffer(self.image)
            self.display.ShowImage(buffer)
      

        
    def open_menu(self):
        keep=True
        print("Menu "+self.p4wnpet.main_menu.name)
        while keep:
            #self.display.clear()

            self.draw.rectangle((0, 0, self.display.width, self.display.height), outline=1, fill=1)

            if GPIO.event_detected(self.key['down']):
                logger.info("KEY DOWN")
                current_index = self.p4wnpet.menu_manager.current_menu.current_index
                if current_index < len(self.p4wnpet.menu_manager.current_menu.items) - 1:
                    self.update_menu_selection(current_index, increment=True)
                

            elif GPIO.event_detected(self.key['up']):
                logger.info("KEY UP")
                current_index = self.p4wnpet.menu_manager.current_menu.current_index
                if current_index > 0:
                    self.update_menu_selection(current_index, increment=False)

            elif GPIO.event_detected(self.key['press']):
                logger.info("KEY PRESS")
                if self.p4wnpet.menu_manager.current_menu.get_current_item().action_select:
                    self.p4wnpet.menu_manager.select_current_item()
                elif self.p4wnpet.menu_manager.current_menu.get_current_item().submenu:
                    
                    self.p4wnpet.menu_manager.select_current_item()
               
            elif GPIO.event_detected(self.key['right']):
                logger.info("KEY RIGHT")

            elif GPIO.event_detected(self.key['left']):
                logger.info("KEY LEFT")

            elif GPIO.event_detected(self.key['key1']): # OPEN MAIN MENU
                logger.info("KEY 1")
                if len(self.p4wnpet.menu_manager.menu_stack) > 1:
                    self.p4wnpet.menu_manager.back()
                else:
                    keep=False
                    


            elif GPIO.event_detected(self.key['key2']):
                logger.info("KEY 2")

            elif GPIO.event_detected(self.key['key3']):
                logger.info("KEY 3")
            

            self.draw_menu(self.p4wnpet.menu_manager.current_menu)

            buffer = self.display.getbuffer(self.image)
            self.display.ShowImage(buffer)

            # dibujar cositas
            
    
    def get_wifi_icon(self, wifi_strength):
        """Devuelve un icono de Wi-Fi basado en la intensidad de la señal."""
        icon_width = 17
        icon_height = 12
        icon_x = wifi_strength * icon_width
        return self.wifi_icons.crop((icon_x, 0, icon_x + icon_width, icon_height))
    
    def get_text_width(self,text, font):
        """
        Obtiene el ancho de un texto renderizado en píxeles.
        
        Args:
            draw (ImageDraw.Draw): El objeto ImageDraw para dibujar texto.
            text (str): El texto a medir.
            font (ImageFont): La fuente utilizada para renderizar el texto.
            
        Returns:
            int: El ancho del texto en píxeles.
        """
        # Obtenemos el tamaño del texto (ancho, alto)
        text_size = self.draw.textsize(text, Fonts.MenuItem)
        
        # Retornamos el ancho
        return text_size[0]
    
    def draw_dotted_line(self, start, end, spacing=2, fill=1):
        """
        Dibuja una línea recta de puntos entre dos puntos dados.
        
        Args:
            draw (ImageDraw.Draw): El objeto de dibujo.
            start (tuple): Punto de inicio de la línea (x, y).
            end (tuple): Punto final de la línea (x, y).
            spacing (int): La distancia entre los puntos de la línea.
            fill (int): Color de los puntos (1 para blanco o 0 para negro en imágenes de 1 bit).
        """
        x1, y1 = start
        x2, y2 = end

        # Calcular la distancia entre los puntos de inicio y fin
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        # Calcular cuántos puntos deben dibujarse en la línea
        steps = int(distance // spacing)

        # Calcular el incremento en x e y por cada paso
        delta_x = (x2 - x1) / steps
        delta_y = (y2 - y1) / steps

        # Dibujar los puntos
        for i in range(steps + 1):
            x = int(x1 + delta_x * i)
            y = int(y1 + delta_y * i)
            self.draw.point((x, y), fill=fill)
    
    def draw_status_bar(self):
        self.draw.rectangle((0, 0, self.display.width, 11), outline=0, fill=0)  # Rectángulo de la barra
        
        wifi_icon = self.get_wifi_icon(0) # icono wifi
        self.image.paste(wifi_icon, (0, 0))

        #text_width=self.get_text_width(str(system_info.data.ap_count), Fonts.MenuItem)
        #self.draw.rectangle((10, 6, text_width+11, 11), outline=0, fill=0) # APs in rango... no se si ponerlo o no, ocupa algo de espacio. en reserva
        #self.draw.text((17, 6), str(system_info.data.ap_count), font=Fonts.MenuItem, fill=1)

        #self.draw_dotted_line((17,0), (17,11))

        self.image.paste(self.menu_icon, (116, 0))


    def update_menu_selection(self, current_index, increment):
        if increment:
            self.p4wnpet.menu_manager.current_menu.items[current_index].selected = False
            self.p4wnpet.menu_manager.navigate_down()
            new_index = current_index + 1
        else:
            self.p4wnpet.menu_manager.current_menu.items[current_index].selected = False
            self.p4wnpet.menu_manager.navigate_up()
            new_index = current_index - 1

        self.p4wnpet.menu_manager.current_menu.items[new_index].selected = True

        # Control de desplazamiento en el menú
        if (increment and new_index - self.p4wnpet.menu_manager.current_menu.menu_cur_top > (self.menu_max_lines // 2) + 1) or \
           (not increment and new_index < self.p4wnpet.menu_manager.current_menu.menu_cur_top):
            self.p4wnpet.menu_manager.current_menu.menu_cur_top += 1 if increment else -1

    def draw_menu(self, menu):
        self.draw.rectangle((0, 0, self.display.width, 11), outline=0, fill=0)
        self.draw.text((1, 1), menu.name, font=Fonts.MenuTitle, fill=1)
        self.image.paste(self.menu_close, (116,0))


        y = 14
        index = 0
        self.draw.rectangle((0, y, self.display.width, self.display.height), outline=1, fill=1)

        for item in menu.items:
            if index >= self.p4wnpet.menu_manager.current_menu.menu_cur_top and \
               index < self.p4wnpet.menu_manager.current_menu.menu_cur_top + self.menu_max_lines:
                if index == menu.current_index:
                    self.draw.rectangle((2, ((index - self.p4wnpet.menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y,
                                         self.display.width - 5,
                                         ((index - self.p4wnpet.menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + self.menu_line_size - 1), outline=1, fill=0)
                    text = item.name
                    if item.options:
                        text += str(item.options[item.options_index])
                    self.draw.text((4, ((index - self.p4wnpet.menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + 2), text, font=Fonts.MenuItem, fill=1)
                else:
                    text = item.name
                    if item.options:
                        text += str(item.options[item.options_index])
                    self.draw.text((4, ((index - self.p4wnpet.menu_manager.current_menu.menu_cur_top) * self.menu_line_size) + y + 2), text, font=Fonts.MenuItem, fill=0)
            index += 1

        for p in range(14, 64, 2):
            self.draw.point((126, p), fill=0)

        visible_items = self.menu_max_lines
        if len(menu.items) > visible_items:
            scrollbar_height = max(5, int(visible_items / len(menu.items) * (self.display.height - y)))
            scrollbar_position = int(((menu.current_index / len(menu.items)) * (self.display.height - y - scrollbar_height)) + y)

            self.draw.rectangle((self.display.width - 4, scrollbar_position, self.display.width, scrollbar_position + scrollbar_height), outline=1, fill=0)

    def split_message(self, message, max_width, font):
        lines = []
        words = message.split(' ')
        current_line = ""

        for word in words:
            line_width, _ = self.draw.textsize(current_line + word + " ", font=font)

            if line_width <= max_width:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines

    #async
    def display_message(self, message="", ok_callback=None):
        self.draw.rectangle((0, 0, self.display.width - 1, self.display.height - 1), outline=0, fill=1)
        lines = self.split_message(message, self.display.width - 4, Fonts.Text)

        y = 14
        for i, line in enumerate(lines):
            self.draw.text((4, y + i * 14), line, font=Fonts.Text, fill=0)

        if ok_callback:
            self.draw.rectangle((30, self.display.height - 18, self.display.width - 30, self.display.height - 6), outline=0, fill=0)
            self.draw.text((45, self.display.height - 17), "OK", font=Fonts.MenuItem, fill=1)

        buffer = self.display.getbuffer(self.image)
        self.display.ShowImage(buffer)

        if ok_callback == True:
            while True:
                if GPIO.event_detected(self.key['key2']):
                    logger.info("OK button pressed. Exiting message display.")
                    break

    def _on_start(self, p4wnpet):
        try:
            self.active = True
            self.p4wnpet = p4wnpet
            asyncio.create_task(self.run())  # Crear tarea asíncrona
        except Exception as e:
            logger.info(f"Error al pintar pantalla {e}")

    def _on_stop(self, p4wnpet):
        self.active = False

    def _on_menu(self, p4wnpet):
        logger.info("Inyectando menus del modulo SH1106")
        p4wnpet.main_menu.add_item(MenuItem(
                name="SH1106 DISPLAY SETTINGS",
                submenu=Menu("SH1106 DISPLAY"),
                action_select=lambda item: (
                    self.update_submenu(item)
                )
            ))
        
    def update_submenu(self, menuitem):
        menuitem.submenu.items.clear()
        menuitem.submenu.add_item(MenuItem("P4WNPET SKIN"))
        menuitem.submenu.add_item(MenuItem("MENUS SKIN"))
        menuitem.submenu.add_item(MenuItem(self.p4wnpet.constants['separator'], action_select=None))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.p4wnpet.menu_manager.back)) # back item  

    def _on_alert(self, message, ok_callback=None):
        self.display_message(message, ok_callback)
        #asyncio.create_task(self.display_message(message, ok_callback))

