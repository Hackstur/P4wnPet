import asyncio
import os
import random
import shutil
import threading
import time
from core.config import config
from core.event_system import event_system
from core.process_manager import process_manager
from core.module_manager import ModuleManager
from core.menu_manager import Menu, MenuItem, MenuManager
from core.functions import *




from core.logger import setup_logger

logger = setup_logger(__name__)

class Pet:
    def __init__(self, name="P4wnPet"):
        global config      
        # Inicializa el nombre del pet
        config.data.pet.name = getattr(config.data.pet, 'name', name)
        
        # Inicializa datebirth con el valor existente o con el tiempo actual si no existe
        config.data.pet.datebirth = getattr(config.data.pet, 'datebirth', time.time())
        
        # Asegúrate de que happiness, tiredness y hunger se inicialicen adecuadamente
        config.data.pet.happiness = getattr(config.data.pet, 'happiness', 50)
        config.data.pet.tiredness = getattr(config.data.pet, 'tiredness', 50)
        config.data.pet.hunger = getattr(config.data.pet, 'hunger', 50)

        # Control flag
        self.running = True

        # CONSTANTS ARRAY
        self.constants={
            'separator'                 : "=======================",
            'switch'                    : ['ON', 'OFF'] ,
            'wifi_channels_24g'         : ['DEFAULT',1,2,3,4,5,6,7,8,9,10,11,12,13],

            #beacon flood options
            'beacon_flood_cypher'       : ['AD-HOC', 'WEP', '54 MB', 'WPA TKIP', 'WPA AES'],
            'beacon_flood_pps'          : ['DEFAULT', 100, 250, 500, 1000],

            'auth_dos_pps'              : ['DEFAULT', 100, 250, 500, 1000],
            'auth_dos_target'           : ['ALL IN RANGE', 'TARGET WIFI AP']
        }

        


    def start(self):
        # START!!
        # Menu Manager
        self.menu_manager = MenuManager(event_system)
  
        # Module Manager
        self.module_manager=ModuleManager(event_system)
        self.module_manager.scan_modules()  # Escanear y registrar módulos
        for module_name, is_active in self.module_manager.modules_status.items():
            if is_active:
                self.module_manager.load_module(module_name)  # Cargar módulo

        # ACTIVAMOS ESTE POR DEFECTO EN DEBUG (NOTA!) (preparar algo similar en consola)
        module_to_activate = "SH1106_128_64"
        if module_to_activate:
            if not self.module_manager.is_module_active(module_to_activate):
                self.module_manager.toggle_module(module_to_activate)  # Activar el módulo


         # LOAD MENU
        self.main_menu=Menu("P4WNPET")
        self.create_menu() # creamos el menu inicial
        self.menu_manager.set_menu(self.main_menu)

        # START!!
        event_system.publish("event_p4wnpet_start",self) #EVENTO event_p4wnpet_start (diseñado para iniciar todos los modulos relacionados)
        


    def save_config(self):
        try:
            config.save_to_file("config/p4wnpet.json")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get_status(self):
        return {
            "name": config.data.pet.name,
            "datebirth": config.data.datebirth,
            "happiness": config.data.pet.happiness,
            "tiredness": config.data.pet.tiredness,
            "hunger": config.data.pet.hunger
        }

    def cleanup(self):
        self.running = False


    def create_menu(self):

        
        self.main_menu.add_item(MenuItem(
            name="SYSTEM INFORMATION",
            submenu=Menu("SYSTEM INFORMATION"),
            action_select=lambda item: (
                
            )
        ))
       
        self.main_menu.add_item(MenuItem( 
            name="PROCESS MANAGER",
            submenu=Menu("PROCESS LIST"),
            action_select=lambda item: (
                self.update_process_menu(item)
            )
        ))



        self.main_menu.add_item(MenuItem(
            name="P4WNPET SETTINGS",
            submenu=Menu("P4WNPET SETTINGS"),
            action_select=lambda item: (
                
            )
        ))

        #evento para alertar a los modulos de inyectar su menu en la primera seccion
        event_system.publish("event_p4wnpet_modulesmenu",self) #EVENTO event_p4wnpet_modulesmenu(pensado para que los modulos inyecten sus propios menus)

        
        self.main_menu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador


        self.main_menu.add_item(MenuItem(
            name="P4WNP1 TEMPLATES",
            submenu=Menu("SELECT TEMPLATE"),
            action_select=lambda item: (
                self.update_templates_menu(item)
            )
        ))


        self.main_menu.add_item(MenuItem(
            name="USB MASS STORAGE",
            submenu=Menu("USB MASS STORAGE"),
            action_select=lambda item: (
                self.update_storage_menu(item)
            )
        ))

        self.main_menu.add_item(MenuItem(
            name="HID TOOLS & DEVICES",
            submenu=Menu("HID TOOLS & DEVICES"),
            action_select=lambda item: (
                self.update_hid_menu(item)
            )
        ))

        self.main_menu.add_item(MenuItem(
            name="WIFI AUDIT TOOLS",
            submenu=Menu("WIFI AUDIT TOOLS"),
            action_select=lambda item: (
                self.update_wifi_menu(item)
            )
        ))

        self.main_menu.add_item(MenuItem(
            name="BLUETOOTH AUDIT TOOLS",
            submenu=Menu("BLUETOOTH TOOLS"),
            action_select=lambda item: (
                self.update_bluetooth_menu(item)
            )
        ))


        self.main_menu.add_item(MenuItem(
            name="LAN RECON & XPLOIT",
            submenu=Menu("LAN RECON TOOLS"),
            action_select=lambda item: (
                self.update_lan_menu(item)
            )
        ))

        self.main_menu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador

        self.main_menu.add_item(MenuItem(
            name="RESTART SERVICES",
            action_select=lambda item: (
                
            )
        ))

        self.main_menu.add_item(MenuItem(
            name="RESTART SYSTEM",
            action_select=lambda item: (
                
            )
        ))

        self.main_menu.add_item(MenuItem(
            name="SHUTDOWN SYSTEM",
            action_select=lambda item: (
                
            )
        ))


    # GENERACION DE MENUS DINAMICOS PARA PROCESS MANAGER
    def update_process_menu(self, menuitem):
        menuitem.submenu.items.clear()

        processes=process_manager.list_processes()
        for process in processes:
            menuitem.submenu.add_item(MenuItem(
                name=str(process['pid'])+"-"+process['name'],
                value=process['pid'],
                submenu=Menu("PID: "+str(process['pid'])),
                action_select=lambda item: (
                    #crear submenu con opciones de gestion
                    self.update_process_submenu(item)
                )                
            ))


        menuitem.submenu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item  

        

    def update_process_submenu(self, menuitem):
        menuitem.submenu.items.clear()

        menuitem.submenu.add_item(MenuItem(
                name="STOP",
                action_select=lambda item: (
                    process_manager.stop_process(pid=menuitem.value)
                )
            ))

        menuitem.submenu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item  # incluir update para menu padre

     

    # GENERACION DE MENUS DINAMICOS PARA P4WNP1 TEMPLATES
    def set_template(self, item):
        run_command("P4wnP1_cli template deploy "+item.value+ " "+item.name)
         # ALERT!!
        event_system.publish("event_p4wnpet_alert", f"Template {item.value} deployed!", ok_callback=True) #EVENTO event_p4wnpet_salert

    def update_template_submenu(self, menu_name, command_flag):
        """Crea un submenú basado en el nombre del menú y el flag de comando"""
        submenu = Menu(f"{menu_name.upper()} TEMPLATES")
        templates = run_command(f"P4wnP1_cli template list {command_flag}").splitlines()[2:]

        for template in templates:
            if template.strip():
                item = MenuItem(template, action_select=self.set_template)
                item.value = command_flag
                submenu.add_item(item)

        submenu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador
        submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item
        return submenu
    
    def update_templates_menu(self, menuitem):

        menuitem.submenu.items.clear()
        # Crear todos los submenús de plantillas usando la función genérica
        submenu_templates_usb = self.update_template_submenu("USB", "-u")
        submenu_templates_wifi = self.update_template_submenu("WIFI", "-w")
        submenu_templates_bluetooth = self.update_template_submenu("BLUETOOTH", "-b")
        submenu_templates_network = self.update_template_submenu("NETWORK", "-n")
        submenu_templates_trigger = self.update_template_submenu("TRIGGER", "-t")
        submenu_templates_master = self.update_template_submenu("MASTER", "-f")

        # Agregar submenús específicos al submenú de templates
        menuitem.submenu.add_item(MenuItem("USB TEMPLATES", submenu=submenu_templates_usb))
        menuitem.submenu.add_item(MenuItem("WIFI TEMPLATES", submenu=submenu_templates_wifi))
        menuitem.submenu.add_item(MenuItem("BLUETOOTH TEMPLATES", submenu=submenu_templates_bluetooth))
        menuitem.submenu.add_item(MenuItem("NETWORK TEMPLATES", submenu=submenu_templates_network))
        menuitem.submenu.add_item(MenuItem("TRIGGER TEMPLATES", submenu=submenu_templates_trigger))
        menuitem.submenu.add_item(MenuItem("MASTER TEMPLATES", submenu=submenu_templates_master))
        menuitem.submenu.add_item(MenuItem(self.constants['separator'], action_select=None))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item      

    # GENERACION DE MENUS DINAMICOS PARA USB MASS STORAGE
    def update_storage_menu(self, menuitem):
        menuitem.submenu.items.clear()
        menuitem.submenu.add_item(MenuItem("CREATE USB/CD IMAGE"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        # buscar imagenes disponibles para montar:
        files = os.listdir("/usr/local/P4wnP1/ums/flashdrive/")
        for file in files:
            if not file.startswith("."): # ignorar archivos ocultos
                file_path = os.path.join("/usr/local/P4wnP1/ums/flashdrive/", file)
                if os.path.isfile(file_path):  # Solo agregar si es un archivo (ignorar carpetas)
                    menuitem.submenu.add_item(MenuItem(file))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item


    def mount_storage_file(self, menuitem):
        a=1

    # GENERACION DE MENUS DINAMICOS PARA HID INJECTOR

    def launch_hidscript(self, path):
        path=path.replace("/usr/local/P4wnP1/HIDScripts/","")
        hid_cmd = ['P4wnP1_cli', 'hid', 'run', '-n', path]
        process_manager.add_process(hid_cmd, name=f"HID-{os.path.basename(path)}")


    def launch_hidshellscript(self, path):
        logger.info("Lanzando script: "+path)
        _, extension = os.path.splitext(path)

        if extension==".ps1":       #  POWERSHEL
            # lanzamos primero las configuraciones generales (TO-DO)
            run_command("P4wnP1_cli hid run -c \"layout('es'); typingSpeed(100,50);\"") 

            # lanzar consola powershell
            run_command("P4wnP1_cli hid run -c \"press('GUI r'); delay(500); type('powershell\\n'); delay(500); \"") 
            
            
            #press("GUI r");
	        #delay(500);
	        #type("powershell\n")

            # Leer el archivo de PowerShell línea por línea
            # Leer el archivo de PowerShell línea por línea
            try:
                with open(path, 'r') as script_file:
                    for line in script_file:  # Leer el archivo línea por línea
                        if line:  # Verificar que la línea no esté vacía
                            # Escapar las comillas simples y las comillas dobles para que se manejen correctamente
                            line = line.replace("'", "\\'")  # Escapar comillas simples
                            line = line.replace('"', '\\"')  # Escapar comillas dobles

                            # Generar el comando
                            command = f'P4wnP1_cli hid run -c "type(\\"{line.strip()}\\")"'

                            # Ejecutar el comando
                            run_command(command)

            except Exception as e:
                logger.error(f"Error al leer el script de PowerShell: {e}")









    def update_hid_menu(self, menuitem):
        menuitem.submenu.items.clear()
        
        menuitem.submenu.add_item(MenuItem(
            name="HIDSCRIPTS",
            submenu=Menu("HIDSCRIPTS"),
            action_select=lambda item: (
                self.update_hidfilesearch_menu(menuitem=item, base_path="/usr/local/P4wnP1/HIDScripts/", file_extension=".js", action_for_file=self.launch_hidscript)
            )
        )) # buscar y lanzar hidscripts

        #menuitem.submenu.add_item(MenuItem("DUCKYSRIPTS")) # buscar y lanzar duckyscripts

        menuitem.submenu.add_item(MenuItem(
            name="JOKERSHELL",
            submenu=Menu("JOKERSHELL"),
            action_select=lambda item: (
                self.update_hidfilesearch_menu(menuitem=item, base_path="/root/Tools/JokerShell/", file_extension=".ps1", action_for_file=self.launch_hidshellscript)
            )
            
        )) # buscar y lanzar scripts jokershell

        menuitem.submenu.add_item(MenuItem("OS RELATED")) # buscar y lanzar scripts dedicados para cada SO
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("HID MOUSE"))
        menuitem.submenu.add_item(MenuItem("HID KEYBOARD"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador



        menuitem.submenu.add_item(MenuItem("SPEED   : 100-50"))
        menuitem.submenu.add_item(MenuItem("LAYOUT  : ES-ES"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item






    def update_hidfilesearch_menu(self, menuitem, base_path, action_for_file, file_extension=".json", initial_base_path=None):
        """
        Actualiza el menú de "HIDFILESSEARCH" con archivos y subdirectorios, navegando solo dentro de la ruta base indicada.

        :param menuitem: El ítem de menú al que se actualizará el submenú.
        :param base_path: La ruta actual de búsqueda de los archivos y carpetas.
        :param action_for_file: La función que se ejecutará al seleccionar un archivo con la extensión especificada.
        :param file_extension: La extensión de archivo que se buscará (por ejemplo, ".json").
        :param initial_base_path: La ruta de inicio que delimita la navegación. Se establece solo en la primera llamada.
        """
        # Establecer `initial_base_path` solo en la primera llamada
        if initial_base_path is None:
            initial_base_path = base_path

        # Asegurarse de que el submenú de menuitem sea un objeto que tenga el método add_item
        if not hasattr(menuitem.submenu, 'add_item'):
            menuitem.submenu = Menu(f"HIDFILESSEARCH - {base_path}")

        # Limpiar el submenú antes de actualizarlo
        menuitem.submenu.items.clear()

        # Añadir opción de volver atrás como el primer item solo si no estamos en `initial_base_path`
        if base_path != initial_base_path:
            # Solo permitir retroceso si `os.path.dirname(base_path)` no sale de `initial_base_path`
            parent_path = os.path.dirname(base_path)
            if os.path.commonpath([parent_path, initial_base_path]) == initial_base_path:
                menuitem.submenu.add_item(MenuItem(".. (parent directory)", action_select=lambda item: self.update_hidfilesearch_menu(item, parent_path, action_for_file, file_extension, initial_base_path)))
        else:
            # En la ruta de inicio, se muestra "Back" para ir al menú anterior
            #menuitem.submenu.add_item(MenuItem("Back", action_select=self.menu_manager.back))
            a=1
        # Bandera para indicar si se encontraron items
        items_found = False

        # Listas temporales para almacenar directorios y archivos por separado
        directories = []
        files = []

        # Explorar el contenido de la ruta base
        try:
            for entry in os.listdir(base_path):
                full_path = os.path.join(base_path, entry)

                if os.path.isdir(full_path):
                    # Añadir directorio a la lista de directorios
                    directories.append(entry)
                    items_found = True
                elif os.path.isfile(full_path) and entry.endswith(file_extension):
                    # Añadir archivo a la lista de archivos
                    files.append(entry)
                    items_found = True

            # Ordenar directorios y archivos alfabéticamente
            directories.sort()
            files.sort()

            # Añadir directorios primero en el submenú
            for directory in directories:
                full_path = os.path.join(base_path, directory)
                dir_item = MenuItem(
                    name=f"[DIR] {directory}",
                    submenu=Menu(f"{directory} - {base_path}"),
                    action_select=lambda item, path=full_path: self.update_hidfilesearch_menu(item, path, action_for_file, file_extension, initial_base_path)
                )
                menuitem.submenu.add_item(dir_item)

            # Añadir archivos después de los directorios
            for file in files:
                full_path = os.path.join(base_path, file)
                file_item = MenuItem(
                    name=file,
                    action_select=lambda item, path=full_path: action_for_file(path)
                )
                menuitem.submenu.add_item(file_item)

        except Exception as e:
            logger.error(f"Error al cargar el contenido de {base_path}: {e}")

        # Si no se encontraron items, agregar un mensaje indicando que no hay archivos en el directorio
        if not items_found:
            menuitem.submenu.add_item(MenuItem("No files found"))

        # Añadir un separador
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))
        menuitem.submenu.add_item(MenuItem("Back", action_select=self.menu_manager.back))






    # GENERACION DE MENUS DINAMICOS PARA WIFI AUDIT TOOLS
    
    def update_wifi_menu(self, menuitem):
        menuitem.submenu.items.clear()

        temp=getattr(config.data.wifi, 'nic', None)
        text=temp if temp else "NOT SELECTED"
        menuitem.submenu.add_item(MenuItem(
            name=f"NIC   : {text}", 
            submenu=Menu("SELECT WNIC"),
            action_select=lambda item: (
                self.update_wifinic_submenu(item)
            ),
            action_update=lambda item: (
                setattr(item, 'name', f"NIC   : {getattr(config.data.wifi, 'nic', 'NOT SELECTED')}")
            )
        ))

        temp=getattr(config.data.wifi.target_ap, 'essid', None)
        text=temp if temp else "NOT SELECTED"
        menuitem.submenu.add_item(MenuItem(
            #name="TARGET:",
            name=f"TARGET: {text}",
            submenu=Menu("SELECT TARGET AP"),
            action_select=lambda item: ( 
                self.update_targetap_menu(item)
            ),
            action_update=lambda item: (
                setattr(item, 'name', f"TARGET: {getattr(config.data.wifi.target_ap, 'essid', 'NOT SELECTED')}")
            )
        ))


        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        

        menuitem.submenu.add_item(MenuItem(
            name=f"{'DISABLE MONITOR MODE' if is_monitor_mode(getattr(config.data.wifi, 'nic', 'wlan0')) else 'ENABLE MONITOR MODE'}",  # Llama a la función aquí
            action_select=lambda item: (
                self.switch_monitor_mode(item)
            )
        ))

        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador


        menuitem.submenu.add_item(MenuItem(
            name="GET WPA HANDSHAKE",
            action_select=lambda item: (
                logger.info("LANZANDO COMANDO WPA HANDSHAKE"),
                self.get_handshake(item)
            )
        ))
        
        
        
        menuitem.submenu.add_item(MenuItem(
            name="STOP BEACON FLOOD" if process_manager.process_exists(name="BeaconFlood") else "START BEACON FLOOD",
            action_select=lambda item: (
                self.switch_beacon_flood(item)
            )
        ))
        
        
        menuitem.submenu.add_item(MenuItem("WPS ONESHOT"))

        menuitem.submenu.add_item(MenuItem("WEP CRACK"))
        
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item

        #END MENU


    def update_wifinic_submenu(self, menuitem):
        menuitem.submenu.items.clear()
        """
        Actualiza el submenú con las interfaces de red WiFi disponibles (NICs).
        :param submenu: El submenú actual que se actualizará con las NICs WiFi disponibles.
        """
        try:
            # Obtener todas las interfaces de red disponibles
            nics = run_command("ip link show").splitlines()
            # Filtrar solo las interfaces WiFi (nombre que empieza por 'wl')
            wifi_nic_list = [line.split(":")[1].strip() for line in nics if ": " in line and line.split(":")[1].strip().startswith("wl")]

            # Añadir cada tarjeta de red WiFi como ítem en el menú
            for nic in wifi_nic_list:
                if nic.strip():
                    nic_item = MenuItem(
                        name=nic,
                        action_select=lambda item, nic=nic: (
                            self.set_wifi_nic(nic)
                          )  # Pasar la NIC seleccionada a la acción
                    )
                    menuitem.submenu.add_item(nic_item)

            # Añadir un separador
            menuitem.submenu.add_item(MenuItem(self.constants['separator']))

            # Añadir opción para volver atrás
            menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back))


        except Exception as e:
            # Emitir un evento en caso de error
            self.event_system.publish('menu_error', {'error': str(e)})

    def set_wifi_nic(self, nic):
        config.data.wifi.nic=nic
        logger.info(f"Selected NIC: {config.data.wifi.nic}")

    def set_target_ap(self, menuitem):
        config.data.wifi.target_ap=menuitem.value
        logger.info("Seleccionando AP objetivo: "+config.data.wifi.target_ap.essid)
  
    def update_targetap_menu(self, menuitem):
        """
        Actualiza el submenú con las redes WiFi disponibles, utilizando airodump-ng si la interfaz
        está en modo monitor, y iwlist si está en modo normal.
        """
        try:
            interface = "wlan0"

            # Verificar si la interfaz está en modo monitor
            if is_monitor_mode(interface):
                # Escanear redes WiFi con airodump-ng
                networks = scan_wifi_with_airodump(interface)
            else:
                # Escanear redes WiFi con iwlist
                networks = scan_wifi_with_iwlist(interface)

            if not networks:
                logger.error("No se detectaron redes WiFi.")

            # Limpiar los ítems actuales del submenú
            menuitem.submenu.items.clear()

            # Añadir cada red WiFi como ítem en el menú
            for bssid, essid, security, channel in networks:
                # Crear el objeto Network con la información de la red
                network=Network(bssid=bssid, essid=essid, security=security, channel=channel)
               
                # Crear el ítem del menú con ESSID, tipo de seguridad y canal, y asignar el objeto Network como value
                network_item = MenuItem(
                    name=f"[{security}] {essid}",
                    value=network,  # Almacena el objeto Network en lugar de solo el BSSID
                    action_select=lambda item: (
                        self.set_target_ap(item),  # Pasar el objeto Network al seleccionar
                        self.menu_manager.back()
                    )
                )
                menuitem.submenu.add_item(network_item)

            # Añadir un separador
            menuitem.submenu.add_item(MenuItem(self.constants['separator'], action_select=None))

            # Añadir opción para volver atrás
            menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back))

        except Exception as e:
            # Emitir un evento en caso de error
            logger.info('menu_error', {'error': str(e)})


    def switch_monitor_mode(self, menuitem):
        if is_monitor_mode(config.data.wifi.nic):
            event_system.publish("event_p4wnpet_alert", f"Disabling monitor mode") #EVENTO event_p4wnpet_salert
            disable_monitor_mode(config.data.wifi.nic)
            menuitem.name="ENABLE MONITOR MODE"
        else:
            event_system.publish("event_p4wnpet_alert", f"Enabling monitor mode") #EVENTO event_p4wnpet_salert
            enable_monitor_mode(config.data.wifi.nic)
            menuitem.name="DISABLE MONITOR MODE"


    def switch_beacon_flood(self, menuitem):
        if process_manager.process_exists(name="BeaconFlood"):
            proc = process_manager.get_process_by_name("BeaconFlood")
            if proc:
                logger.info("BeaconFlood Existe. Deteniendo Beacon Flood...")
                process_manager.stop_process(name="BeaconFlood")  # Detener por nombre
                menuitem.name = "START BEACON FLOOD"
            else:
                logger.warning("El proceso BeaconFlood no se encontró al intentar detenerlo.")
        else:
            logger.info("BeaconFlood no existe. Iniciando Beacon Flood...")
            process_manager.add_process(['sudo', 'mdk3', 'wlan0mon', 'b'], name="BeaconFlood")
            menuitem.name = "STOP BEACON FLOOD"


            

    def get_handshake(self, menuitem, bssid=None, essid=None, interface="wlan0mon"):
        """
        Captura el handshake de una red WiFi específica y lanza ataques de desautenticación
        a los clientes conectados, si es necesario.
        
        Args:
            menuitem: El menú de la interfaz para actualizar el estado.
            bssid (str): BSSID de la red WiFi.
            essid (str): ESSID de la red WiFi.
            interface (str): Interfaz de red a usar para el ataque. Por defecto, 'wlan0mon'.
        """

        if not bssid:
            bssid = config.data.wifi.target_ap.bssid
        
        if not essid:
            essid = config.data.wifi.target_ap.essid
        
        logger.info(f"Preparando handshake capture para {bssid} {essid}")

        # Ruta donde se almacenarán los handshakes
        handshake_base_dir = "loot/handshakes/"
        handshake_dir = os.path.join(handshake_base_dir, f"{bssid}_{essid}/")
        capture_file = os.path.join(handshake_dir, 'capture-01.cap')

        # Comprobar si el directorio para esta red ya existe
        if os.path.exists(handshake_dir):
            logger.info(f"El directorio de handshake ya existe para {essid} (BSSID: {bssid}).")
            
            # Comprobar si existe un archivo de captura
            if os.path.exists(capture_file):
                # Verificar si hay un handshake válido
                if verify_handshake(handshake_dir, bssid, check_only=True):
                    logger.info(f"El archivo de captura ya contiene un handshake válido para {essid} (BSSID: {bssid}).")
                    return
                else:
                    logger.warning(f"El archivo de captura no contiene un handshake válido. Reiniciando la captura...")
                    # Eliminar todos los archivos en el directorio
                    shutil.rmtree(handshake_dir)
                    os.makedirs(handshake_dir)
            else:
                logger.info(f"No se encontró un archivo de captura existente. Iniciando nuevo proceso de captura.")
                os.makedirs(handshake_dir)
        else:
            # Crear el directorio para almacenar los handshakes
            os.makedirs(handshake_dir)
            logger.info(f"Directorio de handshake creado: {handshake_dir}")

        # Iniciar el proceso para capturar el handshake
        capture_cmd = ['sudo', 'airodump-ng', '--bssid', bssid, '-w', os.path.join(handshake_dir, 'capture'), '--essid', essid, interface]
        process_manager.add_process(capture_cmd, name=f"HandshakeCapture-{bssid}")

        # Emitimos un evento a la UI informando que hemos iniciado la captura del handshake
        logger.info(f"Proceso de captura de handshake iniciado para {essid} (BSSID: {bssid}).")

        # Obtener los clientes conectados a la red
        clients = get_connected_clients(bssid)

        # Lanzar un ataque de desautenticación a cada cliente conectado
        if clients:
            logger.info(f"Lanzando ataques de desautenticación a los clientes conectados a {essid}...")
            for client in clients:
                deauth_cmd = ['sudo', 'aireplay-ng', '--deauth', '0', '-a', bssid, '-c', client, interface]
                process_manager.add_process(deauth_cmd, name=f"DeauthClient-{client}")
                logger.info(f"Desautenticando cliente {client} de la red {essid}.")
        else:
            logger.warning(f"No se encontraron clientes conectados a {essid}.")

        # Iniciar la verificación en un hilo separado
        verifier_thread = threading.Thread(target=verify_handshake, args=(handshake_dir, bssid))
        verifier_thread.daemon = True  # Permitir que el hilo se cierre cuando el programa principal termine
        verifier_thread.start()



    # GENERACION DE MENUS DINAMICOS PARA BLUETOOTH PARTY
    def update_bluetooth_menu(self, menuitem):
        menuitem.submenu.items.clear()
        menuitem.submenu.add_item(MenuItem("TARGET : "))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("BLUEDUCKY"))
        menuitem.submenu.add_item(MenuItem("SPEAKER DOS"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item


    def update_lan_menu(self, menuitem):
        menuitem.submenu.items.clear()
        menuitem.submenu.add_item(MenuItem("NETWORK : 192.168.1.0/24"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("LOCAL NETWORK SCAN"))
        menuitem.submenu.add_item(MenuItem("VULNERABILITY SCAN"))
        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("SHARED FILES HARVESTER"))
        menuitem.submenu.add_item(MenuItem("BRUTEFORCE SERVICE"))



        menuitem.submenu.add_item(MenuItem(self.constants['separator']))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=self.menu_manager.back)) # back item

