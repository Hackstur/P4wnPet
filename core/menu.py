import json
import os
import platform
import re
import socket
import time
from core.config import config
from core.menu_manager import *
from core.wifi import wifi

from core.event_system import event_system
from core.process_manager import process_manager
from core.constants import *
from core.overclock import check_overclock, apply_overclock, overclock_profiles
from core.functions import *
import psutil

from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)


def menu_creator(menu):

    system_related=SubmenuItem(name="SYSTEM RELATED")
    system_related.submenu.add_item(SubmenuItem(name="SYSTEM INFORMATION", action_select=lambda item: ( update_system_information_menu(item))))
    system_related.submenu.add_item(SubmenuItem(name="SYSTEM SETTINGS", action_select=lambda item: (update_settings_menu(item))))
    system_related.submenu.add_item(SubmenuItem(name="PLUGIN MANAGER", action_select=lambda item: (update_plugin_manager_menu(item))))
    system_related.submenu.add_item(SubmenuItem(name="PROCESS MANAGER", action_select=lambda item: (update_process_manager_menu(item))))
    system_related.submenu.add_item(MenuItem("CLEAR TEMPORAL FILES", action_select=lambda item: (run_command("sudo rm -rf /tmp/HIDscript*"))))

    system_related.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back))
    menu.add_item(system_related)

    menu.add_item(SubmenuItem(name="P4WNP1 TEMPLATES", action_select=lambda item: (update_p4wnp1_templates_menu(item))))

    menu.add_item(SubmenuItem(name="USB MASS STORAGE", action_select=lambda item: (update_usb_mass_storage_menu(item))))

    menu.add_item(SubmenuItem(name="HID SCRIPTS & DEVICES", action_select=lambda item: (update_hid_menu(item))))

    menu.add_item(SubmenuItem(name="WIFI AUDIT TOOLS", action_select=lambda item: (update_wifi_menu(item))))

    restart=SubmenuItem(name="RESTART")
    restart.submenu.add_item(MenuItem(name="RESTART P4WNPET", action_select=lambda item:(restart_p4wnpet() )))
    restart.submenu.add_item(MenuItem(name="RESTART P4WNP1", action_select=lambda item:(run_command("sudo systemctl restart P4wnP1.service") )))
    restart.submenu.add_item(MenuItem(name="RESTART SYSTEM", action_select=lambda item:(run_command("sudo reboot"))))
    restart.submenu.add_item(MenuItem(name="SHUTDOWN", action_select=lambda item:(run_command("sudo shutdown") )))
    menu.add_item(restart)


def update_menuitem_text(menuitem, text):
     logger.info(f"Actualizando {menuitem.name} con {text}")
     menuitem.name=text


def set_config(path, value):
    keys = path.split('.')
    current = config.data
    try:
        for key in keys[:-1]:  # Navegar por los niveles excepto el último
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"La clave '{key}' no existe en la configuración.")

        # Establecer el nuevo valor en el nivel final
        if hasattr(current, keys[-1]):
            setattr(current, keys[-1], value)
            logger.info(f"Configuración actualizada: {path} = {value}")
            config.save_to_file("config/p4wnpet.json")  # Guardar cambios
        else:
            raise KeyError(f"La clave '{keys[-1]}' no existe en la configuración.")
    except KeyError as e:
        logger.error(f"Error al actualizar la configuración: {e}")


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
            menuitem.submenu.add_item(SubmenuItem(".. (parent directory)", action_select=lambda item: update_filesearch_menu(item, parent_path, action_for_file, file_extension, initial_base_path)))
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
                dir_item = SubmenuItem(
                    name=f"[DIR] {directory}",
                    submenu=Menu(f"{directory} - {base_path}"),
                    action_select=lambda item, path=full_path: update_filesearch_menu(item, path, action_for_file, file_extension, initial_base_path)
                )
                menuitem.submenu.add_item(dir_item)

        # Añadir archivos después de los directorios
        for file in files:
            full_path = os.path.join(base_path, file)
            if not file.startswith("."): # ignorar archivos ocultos
                file_item = SubmenuItem(
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
    else:
        menuitem.submenu.add_item(MenuItem("OS: NOT DETECTED"))
        menuitem.submenu.add_item(MenuItem("TRY INTENSE SCAN"))

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


#region SYSTEM RELATED

def update_system_information_menu(menuitem):
    menuitem.submenu.items.clear()
    
    # Modelo de Raspberry Pi
    try:
        with open("/proc/device-tree/model", "r") as f:
            raspberry_model = f.read().strip()
    except FileNotFoundError:
        raspberry_model = "UNKNOW HW MODEL"
    menuitem.submenu.add_item(MenuItem(f"{raspberry_model.lower().replace('raspberry ', '')}"))
    
    # Memoria RAM
    memory = psutil.virtual_memory()
    available_mb = memory.available // (1024 ** 2)
    total_mb = memory.total // (1024 ** 2)
    menuitem.submenu.add_item(MenuItem(f"RAM: {total_mb-available_mb}/{total_mb} MB"))

    
    # Uso de CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    menuitem.submenu.add_item(MenuItem(f"CPU: {cpu_usage} %"))
    
    # Temperatura de la CPU (si está disponible)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp_celsius = int(f.read()) / 1000
        menuitem.submenu.add_item(MenuItem(f"TEMP: {cpu_temp_celsius:.1f}°C"))
    except FileNotFoundError:
        menuitem.submenu.add_item(MenuItem("TEMP: UNKNOW"))
    
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
    menuitem.submenu.add_item(MenuItem(f"OS: {os_name}"))
    
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
    menuitem.submenu.add_item(MenuItem(f"PROCS: {process_count}"))
    
    # Archivos y límites del sistema (inodos y otros datos)
    try:
        statvfs = os.statvfs('/')
        free_inodes = statvfs.f_favail
        total_inodes = statvfs.f_files
        menuitem.submenu.add_item(MenuItem(f"INODES: {free_inodes}/{total_inodes}"))
    except Exception:
        menuitem.submenu.add_item(MenuItem("INODES: UNKNOW"))
    
    # Elemento de retorno al menú anterior
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item
    logger.info("SYSTEM INFORMATION RECOPILED!")


def update_process_manager_menu(menuitem):
    menuitem.submenu.items.clear()
    processes=process_manager.list_processes()
    for process in processes:

        submenu=Menu(f"{process['pid']} Options")
        submenu.add_item(MenuItem(name="STOP", action_select=lambda item, pid=process['pid']: (
            process_manager.stop_process(pid=pid),
            menu_manager.back()
        )))

        submenu.add_item(MenuItem("..Back", action_select=menu_manager.back))

        menuitem.submenu.add_item(SubmenuItem(
            name=str(process['pid'])+": "+process['name'],
            submenu=submenu,
            action_update=lambda item: ( update_process_manager_menu(menuitem) )
        ))
    #menuitem.submenu.add_item(MenuItem(constants['separator'], action_select=None))  # Separador
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item  


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


def update_settings_menu(menuitem):
    menuitem.submenu.items.clear()
    menuitem.submenu.add_item(SwitchItem(
        name="DWC2: ",
        state=is_dwc2_enabled(),
        labels=("DISABLED","ENABLED"),
        action_select=lambda item: ( toggle_dwc2_mode() )
    ))

    # HDMI
    menuitem.submenu.add_item(SwitchItem(
        name="HDMI: ",
        state=is_hdmi_enabled(),
        labels=("DISABLED", "ENABLED"),
        action_select=lambda item: toggle_hdmi_mode()
    ))

    # Audio
    menuitem.submenu.add_item(SwitchItem(
        name="AUDIO: ",
        state=is_audio_enabled(),
        labels=("DISABLED", "ENABLED"),
        action_select=lambda item: toggle_audio_mode()
    ))

    options_overclock=list(overclock_profiles.keys())
    menuitem.submenu.add_item(SelectorItem(
        name=f"OVERCLOCK: ",
        options=options_overclock,
        selected_index=check_overclock(),
        action_select=lambda item: ( apply_overclock(profile=item.name.split(':')[1].replace(' ','')) ) 
    ))

    #event_system.publish("p4wn_settings_menu", menuitem)
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
        menuitem.submenu.add_item(SubmenuItem("USB TEMPLATES", submenu=submenu_templates_usb))
        menuitem.submenu.add_item(SubmenuItem("WIFI TEMPLATES", submenu=submenu_templates_wifi))
        menuitem.submenu.add_item(SubmenuItem("BLUETOOTH TEMPLATES", submenu=submenu_templates_bluetooth))
        menuitem.submenu.add_item(SubmenuItem("NETWORK TEMPLATES", submenu=submenu_templates_network))
        menuitem.submenu.add_item(SubmenuItem("TRIGGER TEMPLATES", submenu=submenu_templates_trigger))
        menuitem.submenu.add_item(SubmenuItem("MASTER TEMPLATES", submenu=submenu_templates_master))
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


#region USB MASS STORAGE MENU

def update_usb_mass_storage_menu(menuitem):
    menuitem.submenu.items.clear()
    files = os.listdir("/usr/local/P4wnP1/ums/flashdrive/")
    for file in files:
        if not file.startswith("."): # ignorar archivos ocultos
            file_path = os.path.join("/usr/local/P4wnP1/ums/flashdrive/", file)
            if os.path.isfile(file_path):  # Solo agregar si es un archivo (ignorar carpetas)
                menuitem.submenu.add_item(MenuItem(file, action_select=lambda item, file=file: run_p4wnp1_ums(file)))
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

#endregion


#region HID SCRIPTS & DEVICES

def update_hid_menu(menuitem):
    menuitem.submenu.items.clear()

    menuitem.submenu.add_item(SelectorItem(
        name="SPEED: ",
        options=[f"{speed.value}" for speed in HIDspeed],
        selected_index=([f"{speed.value}" for speed in HIDspeed].index(f"{config.data.hid.type_speed}") if f"{config.data.hid.type_speed}" in [f"{speed.value}" for speed in HIDspeed] else -1),
        action_select=lambda item: ( set_config("hid.type_speed", eval(item.name.split(':')[1].replace(' ', '')) ) )
    ))


    keymap_options = [os.path.splitext(f)[0] for f in os.listdir("/usr/local/P4wnP1/keymaps/") if os.path.isfile(os.path.join("/usr/local/P4wnP1/keymaps/", f)) and f.endswith('.json')]
    menuitem.submenu.add_item(SelectorItem(
        name="KEYMAP: ",
        options=keymap_options,
        selected_index=( keymap_options.index(config.data.hid.keymap.strip()) if config.data.hid.keymap.strip() in keymap_options else -1),
        action_select=lambda item: set_config("hid.keymap", item.name.split(':')[1].strip())
    ))

    menuitem.submenu.add_item(SubmenuItem(  # Buscar y lanzar hidscripts propios de P4wnP1
        name="P4WNP1 HIDSCRIPTS",
        submenu=Menu("P4WNP1 HIDSCRIPTS"),
        action_select=lambda item: ( update_filesearch_menu(menuitem=item, base_path="/usr/local/P4wnP1/HIDScripts/", file_extension=".js", action_for_file=run_p4wnp1_hidscript))
    )) 

    event_system.publish("p4wn_hidscripts_menu", menuitem) # Inyectar menus de hidscripts (JokerShell, DuckyScripts, etc). no necestan hacer "clear"
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item

#endregion


#region WIFI AUDIT TOOLS

def update_wifi_menu(menuitem):
    menuitem.submenu.items.clear()

    menuitem.submenu.add_item(SelectorItem(
        name="WIFI NIC: ",
        options=wifi.nic.list(),
        selected_index=( wifi.nic.list().index(config.data.wifi.nic) if config.data.wifi.nic in wifi.nic.list() else -1 ),
        action_select=lambda item: ( set_config("wifi.nic", item.name.split(':')[1].strip()) )
    ))


    menuitem.submenu.add_item(SwitchItem(
        name="MONITOR MODE: ",
        state=wifi.is_monitormode(),
        labels=("DISABLED","ENABLED"),
        action_select=lambda item: ( wifi.toggle_monitormode() )
    ))

    wifi_recon=Menu("WIFI RECON")

    wifi_recon.add_item(SwitchItem(
        name="STATUS: DISABLED",
        state=wifi.is_bettercap_running(),
        labels=['DISABLED', 'ENABLED'],
        action_select=lambda item: ( wifi.toggle_bettercap() )
    ))

    
    #experimento para un monitor de logs de bettercap.... no me acaba de convencer
    wifi_recon.add_item(LogMonitorItem(
        name="SHOW LOGS",
        max_displayed_logs=100,
        log_file="/root/P4wnPet/logs/bettercap.log",
        filters=[
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[inf\] wifi using interface", "NIC:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[wifi\.ap\.new\] wifi access point", "AP+:"), 
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[wifi\.client\.new\] new station (\w{2}(:\w{2}){5}) detected for (\S+)","CL+:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[inf\] api.rest api server starting on","INF:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[war\] wifi error while activating handle: error while setting interface wlan0mon in monitor mode: Cannot set rfmon for this handle,", "WAR:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[war\] wifi could not set interface wlan0mon txpower to 30, 'Set Tx Power' requests not supported", "WAR: Set TxPower not supported"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[inf\] wifi started","INF:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[sys\.log\] \[inf\] wifi wifi channel hopper started","INF: Channel hopper started"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[wifi\.client\.probe\] station (\w{2}(:\w{2}){5}) is probing for","PRB:"),
            (r"\[BETTERCAP API\] stdout: \[\d{2}:\d{2}:\d{2}\] \[wifi\.ap\.lost\] wifi access point", "AP-:"), 
            (r"\[BETTERCAP API\] stdout: bettercap", "bettercap"),
            (r"\[BETTERCAP API\] stdout:\n", ""),
            (r"\[BETTERCAP API\] stdout:$", "")        
        ]
    ))

    menuitem.submenu.add_item(SubmenuItem(
        name="WIFI RECON",
        submenu=wifi_recon
    ))

    #menu "DEAUTH ATTACK" -> deautenticar cosas

    #menu "GET HANDSHAKE" -> obtener handshake manualmente (o dejarlo en bucle estilo pwnagotchi)

    #menu "BEACON FLOOD" -> lanzar un beaconflood

    #menu "CRACK WEP" -> Crackear WEP

    #menu "WPS ONESHOT" -> lanzar ataques WPS
        
    menuitem.submenu.add_item(MenuItem("..Back", action_select=menu_manager.back)) # back item


#endregion
