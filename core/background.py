import re
import subprocess
import time
import traceback

from core.config import config

from core.functions import run_command

from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)

def background_worker():
    while True:
        try:
            # Ejecutar el comando 'P4wnP1_cli usb get help' y obtener la salida
            result = subprocess.run(['P4wnP1_cli', 'usb', 'get', 'help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout

            # Inicializar un diccionario para almacenar los estados
            usb_status = {
                "enabled": False,
                "product": "",
                "manufacturer": "",
                "serialnumber": "",
                "pid": "",
                "vid": "",
                "functions": {
                    "RNDIS": False,
                    "CDC_ECM": False,
                    "serial": False,
                    "HID_Mouse": False,
                    "HID_Keyboard": False,
                    "HID_Generic": False,
                    "Mass_Storage": False
                }
            }

            # Parsear la salida del comando
            for line in output.splitlines():
                if 'Enabled:' in line:
                    usb_status['enabled'] = 'true' in line
                elif 'Product:' in line:
                    usb_status['product'] = line.split(":")[1].strip()
                elif 'Manufacturer:' in line:
                    usb_status['manufacturer'] = line.split(":")[1].strip()
                elif 'Serialnumber:' in line:
                    usb_status['serialnumber'] = line.split(":")[1].strip()
                elif 'PID:' in line:
                    usb_status['pid'] = line.split(":")[1].strip()
                elif 'VID:' in line:
                    usb_status['vid'] = line.split(":")[1].strip()
                elif 'Functions:' in line:
                    # Parse functions after "Functions:" header
                    for func_line in output.splitlines():
                        if 'RNDIS:' in func_line:
                            config.data.rndis = 'true' in func_line  # Actualiza el valor de config.data.rndis
                            usb_status['functions']['RNDIS'] = 'true' in func_line
                        elif 'CDC ECM:' in func_line:
                            config.data.cdc_ecm = 'true' in func_line  # Actualiza el valor de config.data.cdc_ecm
                            usb_status['functions']['CDC_ECM'] = 'true' in func_line
                        elif 'Serial:' in func_line:
                            config.data.serial = 'true' in func_line  # Actualiza el valor de config.data.serial
                            usb_status['functions']['serial'] = 'true' in func_line
                        elif 'HID Mouse:' in func_line:
                            config.data.hid_mouse = 'true' in func_line  # Actualiza el valor de config.data.hid_mouse
                            usb_status['functions']['HID_Mouse'] = 'true' in func_line
                        elif 'HID Keyboard:' in func_line:
                            config.data.hid_keyboard = 'true' in func_line  # Actualiza el valor de config.data.hid_keyboard
                            usb_status['functions']['HID_Keyboard'] = 'true' in func_line
                        elif 'HID Generic:' in func_line:
                            config.data.hid_generic = 'true' in func_line  # Actualiza el valor de config.data.hid_generic
                            usb_status['functions']['HID_Generic'] = 'true' in func_line
                        elif 'Mass Storage:' in func_line:
                            config.data.mass_storage = 'true' in func_line  # Actualiza el valor de config.data.mass_storage
                            usb_status['functions']['Mass_Storage'] = 'true' in func_line


            # ESTADO BLUETOOTH
            # Ejecutar el comando 'rfkill list bluetooth'
            result = subprocess.run(['rfkill', 'list', 'bluetooth'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout

            # Buscar el estado de "Soft blocked" o "Hard blocked"
            if "Soft blocked: yes" in output or "Hard blocked: yes" in output:
                config.data.bluetooth=False
            elif "Soft blocked: no" in output and "Hard blocked: no" in output:
                config.data.bluetooth=True
            else:
                config.data.bluetooth=False  # No se puede determinar el estado


            # ESTADO WIFI
            # Determinar si la interfaz está en modo monitor o no
            iwconfig_result = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            iwconfig_output = iwconfig_result.stdout
            
            config.data.wifi.signal = 0  # Interfaz no encontrada
            # Verificar si la interfaz en modo monitor existe
            interface_monitor = f"{config.data.wifi.nic}mon"
            if f"{interface_monitor}" in iwconfig_output:
                active_interface = interface_monitor
            elif f"{config.data.wifi.nic}" in iwconfig_output:
                active_interface = config.data.wifi.nic
            else:
                config.data.wifi.signal = 0  # Interfaz no encontrada
                return

            # Obtener detalles de iwconfig para la interfaz activa
            iwconfig_result = subprocess.run(['iwconfig', active_interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            iwconfig_output = iwconfig_result.stdout

            # Verificar el modo
            if "Mode:Monitor" in iwconfig_output:
                config.data.wifi.signal = 0  # modo monitor
            elif "Mode:Master" in iwconfig_output:
                config.data.wifi.signal = 1  # modo AP
            elif "Mode:Managed" in iwconfig_output:
                config.data.wifi.signal = 2  # Modo client
                # Verificar si está conectado
                if "Access Point: Not-Associated" not in iwconfig_output:
                    # Aquí tiene sentido analizar la intensidad de la señal
                    config.data.wifi.signal = 3  # conectado
                    for line in iwconfig_output.splitlines():
                        if "Signal level" in line:
                            signal_line = line.strip()
                            signal_level = int(signal_line.split("Signal level=")[1].split(" ")[0])
                            # Clasificar la intensidad de la señal
                            if signal_level <= -80:
                                config.data.wifi.signal = 3  # Débil
                            elif -80 < signal_level <= -60:
                                config.data.wifi.signal = 4  # Moderada
                            elif -60 < signal_level <= -40:
                                config.data.wifi.signal = 5  # Buena
                            elif signal_level > -40:
                                config.data.wifi.signal = 6  # Excelente
                            break
                else:
                    config.data.wifi.signal = 2  # Desconectada
            else:
                config.data.wifi.signal = 2  # No manejado=Desconectado

            #logger.info("Wifi SIGNAL:" + str(config.data.wifi.signal))

            # ALMACENAR LISTADO DE APS DETECTADAS (se borrara en cada ciclo por el momento)
            command="iwlist wlan0 scan | awk '/Quality|ESSID|Channel|Encryption key|WPA|WEP|WPS|Address/ { print $0 }'"
            iwlist_result = run_command(command)
            
            networks=[]

            pattern = (
                r'Cell \d+ - Address:\s*([0-9A-Fa-f:]{17})\s*.*?'
                r'Channel:(\d+)\s*.*?'
                r'Quality=\d+/\d+\s+Signal level=-?\d+\s+dBm\s*.*?'
                r'Encryption key:(on|off)\s*.*?'
                r'ESSID:"([^"]*)"\s*.*?'
                r'(?:IE:\s*(WPA3|IEEE 802\.11i/WPA2 Version 1|WPA Version 1|WEP).*?)*'
            )

            # Buscar coincidencias en el resultado del escaneo
            matches = re.findall(pattern, iwlist_result, re.DOTALL)

            # Añadir cada red WiFi como ítem en el menú
            for match in matches:
                mac = match[0]
                channel = match[1]
                encryption = match[2]
                essid = match[3]

                # Determinar el estado de la seguridad
                security = "OPEN"
                if encryption == "on":
                    if "WEP" in match:
                        security = "WEP"
                    elif "WPA Version 1" in match:
                        security = "WPA"
                    elif "IEEE 802.11i/WPA2 Version 1" in match:
                        security = "WPA2"
                    elif "WPA3" in match:
                        security = "WPA3"

                networks.append((mac, essid, security, channel))

                config.data.wifi.networks=networks



        except Exception as e:
            # Registrar errores y continuar el bucle
            tb = traceback.format_exc()
            logger.error(f"Error en el background worker: {e} - {tb}")

        # Pausa antes del siguiente ciclo
        time.sleep(5)