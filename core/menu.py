
import json
import os
import platform
import re
import socket
import time
from core.config import config
from core.menu_manager import Menu, MenuItem, menu_manager

from core.event_system import event_system
from core.process_manager import process_manager
from core.constants import constants
from core.functions import *
import psutil

from core.logger import setup_logger
logger = setup_logger(__name__)


def menu_creator(menu):
        
        menu.add_item(MenuItem( name="HOST INFORMATION", submenu=Menu("HOST INFORMATION"), action_select=lambda item: (update_host_information_menu(item))))
        menu.add_item(MenuItem( name="SYSTEM INFORMATION", submenu=Menu("SYSTEM INFORMATION"), action_select=lambda item: (update_system_information_menu(item))))
        menu.add_item(MenuItem( name="SETTINGS", submenu=Menu("SETTINGS"), action_select=lambda item: (update_settings_menu(item))))
        

        menu.add_item(MenuItem( name="PROCESS MANAGER", submenu=Menu("PROCESS LIST"), action_select=lambda item: (update_process_manager_menu(item)), action_update=lambda item:(update_process_manager_menu(item))))
        menu.add_item(MenuItem( name="PLUGIN MANAGER", submenu=Menu("PLUGIN LIST"), action_select=lambda item: (update_plugin_manager_menu(item))))
        menu.add_item(MenuItem(name="P4WNP1 TEMPLATES", submenu=Menu("SELECT TEMPLATE"), action_select=lambda item: (update_p4wnp1_templates_menu(item)))) 
        menu.add_item(MenuItem(name="USB MASS STORAGE", submenu=Menu("SELECT IMAGE TO MOUNT"), action_select=lambda item: (update_usb_mass_storage_menu(item))))
        menu.add_item(MenuItem(name="HID SCRIPTS & DEVICES", submenu=Menu("HID SCRIPTS & DEVICES"), action_select=lambda item: (update_hid_menu(item))))

        submenu=Menu("RESTART OR SHUTDOWN")
        submenu.add_item(MenuItem(name="RESTART P4WNPET", action_select=lambda item:(restart_p4wnpet() )))
        submenu.add_item(MenuItem(name="RESTART P4WNP1", action_select=lambda item:(run_command("sudo systemctl restart P4wnP1.service") )))
        submenu.add_item(MenuItem(name="RESTART SYSTEM", action_select=lambda item:(run_command("sudo reboot"))))
        submenu.add_item(MenuItem(name="SHUTDOWN", action_select=lambda item:(run_command("sudo shutdown") )))
        menu.add_item(MenuItem(name="RESTART", submenu=submenu))


def update_menuitem_text(menuitem, text):
     logger.info(f"Actualizando {menuitem.name} con {text}")
     menuitem.name=text


def update_filesearch_menu(menuitem, base_path, action_for_file, file_extension=".json", initial_base_path=None):
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
    #if not hasattr(menuitem.submenu, 'add_item'):
    #    menuitem.submenu = Menu(f"HIDFILESSEARCH - {base_path}")

    # Limpiar el submenú antes de actualizarlo
    menuitem.submenu.items.clear()

    # Añadir opción de volver atrás como el primer item solo si no estamos en `initial_base_path`
    if base_path != initial_base_path:
        # Solo permitir retroceso si `os.path.dirname(base_path)` no sale de `initial_base_path`
        parent_path = os.path.dirname(base_path)
        if os.path.commonpath([parent_path, initial_base_path]) == initial_base_path:
            menuitem.submenu.add_item(MenuItem(".. (parent directory)", action_select=lambda item: update_filesearch_menu(item, parent_path, action_for_file, file_extension, initial_base_path)))
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
            if not directory.startswith("."): # ignorar archivos ocultos
                dir_item = MenuItem(
                    name=f"[DIR] {directory}",
                    submenu=Menu(f"{directory} - {base_path}"),
                    action_select=lambda item, path=full_path: update_filesearch_menu(item, path, action_for_file, file_extension, initial_base_path)
                )
                menuitem.submenu.add_item(dir_item)

        # Añadir archivos después de los directorios
        for file in files:
            full_path = os.path.join(base_path, file)
            if not file.startswith("."): # ignorar archivos ocultos
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
    #menuitem.submenu.add_item(MenuItem(constants['separator']))
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item  


# region SETTINGS
# (IDEAS BYTHEWAY)
 
def update_settings_menu(menuitem):
    menuitem.submenu.items.clear()

    # DWC2 SWITCH (in order to connect things to our pi)
    menuitem.submenu.add_item(MenuItem(
        name="DWC2: ENABLED" if is_dwc2_enabled() else "DWC2: DISABLED"
        #action_select=toggle_dwc2_mode()
    ))

    menuitem.submenu.add_item(MenuItem(
        name="OVERCLOCK: NONE"
    ))

    menuitem.submenu.add_item(MenuItem(
        name="CLEAR TEMPORAL FILES",
        action_select=run_command("rm -rf /tmp/HIDscript*")
    ))



    event_system.publish("p4wn_settings_menu", menuitem)
    # Elemento de retorno al menú anterior
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item


#endregion

#region HOST INFORMATION

def update_host_information_menu(menuitem):
    menuitem.submenu.items.clear()
    #return os name if found ex. Microsoft Windows 7 ,  Linux 3.X
    #return(shell("nmap -p 22,80,445,65123,56123 -O " + ips + " | grep Running: | cut -d \":\" -f2 | cut -d \"|\" -f1"))
    #return(shell("nmap -p 22,80,445,65123,56123 -O " + ips + " | grep \"OS details:\" | cut -d \":\" -f2 | cut -d \",\" -f1"))
    #res=run_command("nmap -p 22,80,445,65123,5613 -O 172.16.0.2")
    output=run_command("nmap -O 172.16.0.2")

    open_ports = []
    detected_os = "Not detected"

    # Detect operating system
    os_running_match = re.search(r"Running:\s+(.*)", output)
    os_details_match = re.search(r"OS details:\s+(.*)", output)
    if os_running_match:
        detected_os = os_running_match.group(1).strip()
        menuitem.submenu.add_item(MenuItem(f"OS: {detected_os}"))
        if os_details_match:
            menuitem.submenu.add_item(MenuItem(f"OS: {os_details_match.group(1).strip().replace(detected_os,'')}"))


    # Extract open ports
    for line in output.splitlines():
        # Look for lines with open ports (format: port/protocol state service)
        port_match = re.match(r"(\d+/tcp)\s+open\s+([\w-]+)", line)
        if port_match:
            port = port_match.group(1)
            service = port_match.group(2)
            open_ports.append({"port": port, "service": service})
            menuitem.submenu.add_item(MenuItem(f"{port}:{service}"))



    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

    logger.info(output)

#endregion

#region SYSTEM INFORMATION

def update_system_information_menu(menuitem):
    menuitem.submenu.items.clear()
    
    # Modelo de Raspberry Pi
    try:
        with open("/proc/device-tree/model", "r") as f:
            raspberry_model = f.read().strip()
    except FileNotFoundError:
        raspberry_model = "Modelo de Raspberry no disponible"
    menuitem.submenu.add_item(MenuItem(f"{raspberry_model.lower().replace('raspberry ', '')}"))
    
    # Memoria RAM
    memory = psutil.virtual_memory()
    available_mb = memory.available // (1024 ** 2)
    total_mb = memory.total // (1024 ** 2)
    menuitem.submenu.add_item(MenuItem(f"RAM   : {total_mb-available_mb}/{total_mb} MB"))

    
    # Uso de CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    menuitem.submenu.add_item(MenuItem(f"CPU   : {cpu_usage} %"))
    
    # Temperatura de la CPU (si está disponible)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp_celsius = int(f.read()) / 1000
        menuitem.submenu.add_item(MenuItem(f"TEMP  : {cpu_temp_celsius:.1f}°C"))
    except FileNotFoundError:
        menuitem.submenu.add_item(MenuItem("TEMP  : CANT MEASURE"))
    
    # Espacio en Disco
    disk_usage = psutil.disk_usage('/')
    used_gb = disk_usage.used / (1024 ** 3)
    total_gb = disk_usage.total / (1024 ** 3)
    menuitem.submenu.add_item(MenuItem(f"DISK: {used_gb:.2f}/{total_gb:.2f} GB"))
    
    # Velocidad de I/O (basica) Ralentiza mucho la apertura del menu, darle un par de vueltas
    #menuitem.submenu.add_item(MenuItem(f"WRITE SD: {measure_write_speed('/root/')} Mbps"))
    #menuitem.submenu.add_item(MenuItem(f"READ SD: {measure_read_speed('/root/')} Mbps"))


    # Información del kernel y del sistema operativo
    kernel_version = platform.release()
    os_name = platform.system() + " " + platform.version()
    menuitem.submenu.add_item(MenuItem(f"KERNEL: {kernel_version}"))
    menuitem.submenu.add_item(MenuItem(f"OS    : {os_name}"))
    
    # Tiempo de actividad (Uptime)
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    menuitem.submenu.add_item(MenuItem(f"UPTIME: {int(uptime_hours)}h {int(uptime_minutes)}m"))
    
    # Uso de red
    net_io = psutil.net_io_counters()
    menuitem.submenu.add_item(MenuItem(f"DATA SEND: {net_io.bytes_sent / (1024 ** 2):.2f} MB"))
    menuitem.submenu.add_item(MenuItem(f"DATA RECV: {net_io.bytes_recv / (1024 ** 2):.2f} MB"))
    
    # Número de procesos en ejecución
    process_count = len(psutil.pids())
    menuitem.submenu.add_item(MenuItem(f"PROCS : {process_count}"))
    
    # Tiempo desde el último reinicio del sistema
    boot_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time()))
    menuitem.submenu.add_item(MenuItem(f"BOOT: {boot_time}"))
    
    # Archivos y límites del sistema (inodos y otros datos)
    try:
        statvfs = os.statvfs('/')
        free_inodes = statvfs.f_favail
        total_inodes = statvfs.f_files
        menuitem.submenu.add_item(MenuItem(f"INODES: {free_inodes}/{total_inodes}"))
    except Exception:
        menuitem.submenu.add_item(MenuItem("INODES: No disponible"))
    
    # Elemento de retorno al menú anterior
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

#endregion

#region P4WNP1 TEMPLATES 

def update_p4wnp1_templates_menu(menuitem):
        menuitem.submenu.items.clear()
        logger.info("Creando menu P4wnP1 templates")
        # Crear todos los submenús de plantillas usando la función genérica
        submenu_templates_usb = update_p4wnp1_templates_submenu("USB", "-u")
        submenu_templates_wifi = update_p4wnp1_templates_submenu("WIFI", "-w")
        submenu_templates_bluetooth = update_p4wnp1_templates_submenu("BLUETOOTH", "-b")
        submenu_templates_network = update_p4wnp1_templates_submenu("NETWORK", "-n")
        submenu_templates_trigger = update_p4wnp1_templates_submenu("TRIGGER", "-t")
        submenu_templates_master = update_p4wnp1_templates_submenu("MASTER", "-f")

        # Agregar submenús específicos al submenú de templates
        menuitem.submenu.add_item(MenuItem("USB TEMPLATES", submenu=submenu_templates_usb))
        menuitem.submenu.add_item(MenuItem("WIFI TEMPLATES", submenu=submenu_templates_wifi))
        menuitem.submenu.add_item(MenuItem("BLUETOOTH TEMPLATES", submenu=submenu_templates_bluetooth))
        menuitem.submenu.add_item(MenuItem("NETWORK TEMPLATES", submenu=submenu_templates_network))
        menuitem.submenu.add_item(MenuItem("TRIGGER TEMPLATES", submenu=submenu_templates_trigger))
        menuitem.submenu.add_item(MenuItem("MASTER TEMPLATES", submenu=submenu_templates_master))
        #menuitem.submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
        menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item     

def update_p4wnp1_templates_submenu(menu_name, command_flag):
        logger.info("Creando submenu P4wnP1"+menu_name)
        submenu = Menu(f"{menu_name.upper()} TEMPLATES")
        templates = run_command(f"P4wnP1_cli template list {command_flag}").splitlines()[2:]

        for template in templates:
            if template.strip():
                item = MenuItem(
                      template, 
                      action_select=lambda item, flag=command_flag, name=template.strip(): run_p4wnp1_template(flag, name))
                item.value = command_flag
                submenu.add_item(item)

        #submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
        submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item
        return submenu

#endregion

#region PROCESS MANAGER

def update_process_manager_menu(menuitem):
    menuitem.submenu.items.clear()
    processes=process_manager.list_processes()
    for process in processes:
        menuitem.submenu.add_item(MenuItem(
            name=str(process['pid'])+"-"+process['name'],
            value=process['pid'],
            submenu=Menu("PID: "+str(process['pid'])),
            action_select=lambda item: (
                #crear submenu con opciones de gestion
                update_process_manager_submenu(item)
            ),
            action_update=lambda item: ( update_process_manager_menu(menuitem) )
        ))
    #menuitem.submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item  


def update_process_manager_submenu(menuitem):
    menuitem.submenu.items.clear()
    menuitem.submenu.add_item(MenuItem(
            name="STOP",
            action_select=lambda item, pid=menuitem.value: (
                process_manager.stop_process(pid=pid),
                menu_manager.back()
            )
        ))
    #menuitem.submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item  # incluir update para menu padre



#endregion


#region plugin MANAGER
def update_plugin_manager_menuitem(menuitem):
    from core.plugin_manager import plugin_manager
    plugin_name=menuitem.name.replace(": ON", "").replace(": OFF", "")
    menuitem.name=f"{plugin_name}: {'ON' if plugin_manager.is_plugin_active(plugin_name) else 'OFF'}"

def update_plugin_manager_menu(menuitem):
    from core.plugin_manager import plugin_manager
    menuitem.submenu.items.clear()
    for plugin_name, is_active in plugin_manager.plugins_status.items():
        menuitem.submenu.add_item(MenuItem(
            name=f"{plugin_name}: {'ON' if is_active else 'OFF'}",
            action_select=lambda item: (
                    plugin_manager.toggle_plugin(item.name.replace(": ON", "").replace(": OFF", ""))
            ),
            action_update=lambda item :(
                    update_plugin_manager_menuitem(item)
            )
        ))
    #menuitem.submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item  # incluir update para menu padre
#endregion


#region USB MASS STORAGE MENU

def update_usb_mass_storage_menu(menuitem):
    menuitem.submenu.items.clear()
    #menuitem.submenu.add_item(MenuItem("CREATE USB/CD IMAGE")) # to-do cuando tenga algo para introducir texto
    #menuitem.submenu.add_item(MenuItem(constants['separator']))  # Separador
    # buscar imagenes disponibles para montar:
    files = os.listdir("/usr/local/P4wnP1/ums/flashdrive/")
    for file in files:
        if not file.startswith("."): # ignorar archivos ocultos
            file_path = os.path.join("/usr/local/P4wnP1/ums/flashdrive/", file)
            if os.path.isfile(file_path):  # Solo agregar si es un archivo (ignorar carpetas)
                menuitem.submenu.add_item(MenuItem(file, action_select=lambda item, file=file: run_p4wnp1_ums(file)))
    #menuitem.submenu.add_item(MenuItem(constants['separator']))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

#endregion


#region HID SCRIPTS & DEVICES

# TYPE SPEED
def set_hid_type_speed(menuitem):   
    config.data.hid.type_speed=menuitem.value
    save_config()
    menu_manager.back()

def update_hid_speed_submenu(menuitem):
    menuitem.submenu.items.clear()
    for speed_name, speed_value in constants['hid']['speed'].items():
        menuitem.submenu.add_item(MenuItem(
            name=speed_name+" "+speed_value,
            value=speed_value,
            action_select=lambda item:(
                 set_hid_type_speed(item)
            )
        ))
    #menuitem.submenu.add_item(MenuItem(constants['separator']))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

# HID KEYMAP
def set_hid_keymap(menuitem):
    config.data.hid.keymap=menuitem.value
    save_config()
    menu_manager.back()

def update_hid_keymap_submenu(menuitem):
    menuitem.submenu.items.clear()

    for filename in os.listdir("/usr/local/P4wnP1/keymaps/"):
        if filename.endswith(".json"):
            file_path = os.path.join("/usr/local/P4wnP1/keymaps/", filename)
        
        # Abre y carga el archivo JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Extrae el nombre y la descripción, si existen
            name = data.get("Name", "N/A")
            description = data.get("Description", "N/A")
            menuitem.submenu.add_item(MenuItem(
                name=name,
                value=name,
                action_select=lambda item:(
                    set_hid_keymap(item)
                )
            ))
    #menuitem.submenu.add_item(MenuItem(constants['separator']))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item


# HID SCRIPTS MENU
def update_hid_menu(menuitem):
    menuitem.submenu.items.clear()

    menuitem.submenu.add_item(MenuItem(
        name=f"SPEED : {config.data.hid.type_speed}",
        submenu=Menu("SELECT HID SPEED"),
        action_select=lambda item: (
             update_hid_speed_submenu(item)
        ),
        action_update=lambda item:(
            update_menuitem_text(item, f"SPEED : {config.data.hid.type_speed}")
        )                         
    ))

    menuitem.submenu.add_item(MenuItem(
        name=f"KEYMAP: {config.data.hid.keymap}",
        submenu=Menu("Select Keymap"),
        action_select=lambda item: (
            update_hid_keymap_submenu(item)
        ),
        action_update=lambda item:(
            update_menuitem_text(item, f"KEYMAP: {config.data.hid.keymap}")
        )
        
    ))

    #menuitem.submenu.add_item(MenuItem(constants['separator']))  # Separador

    menuitem.submenu.add_item(MenuItem(  # Buscar y lanzar hidscripts propios de P4wnP1
        name="P4WNP1 HIDSCRIPTS",
        submenu=Menu("P4WNP1 HIDSCRIPTS"),
        action_select=lambda item: (
            update_filesearch_menu(menuitem=item, base_path="/usr/local/P4wnP1/HIDScripts/", file_extension=".js", action_for_file=run_p4wnp1_hidscript)
        )
    )) 

    event_system.publish("p4wn_hidscripts_menu", menuitem) # Inyectar menus de hidscripts (JokerShell, DuckyScripts, etc). no necestan hacer "clear"


    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item


#endregion
