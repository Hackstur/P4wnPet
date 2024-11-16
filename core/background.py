import subprocess
import time
import pywifi
from pywifi import const
from core.config import config

# Configurar el logger
from core.logger import setup_logger
logger = setup_logger(__name__)

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
            # Verificar si la interfaz WiFi está activa y obtener detalles
            iwconfig_result = subprocess.run(['iwconfig', 'wlan0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            iwconfig_output = iwconfig_result.stdout
            # Verificar el modo
            if "Mode:Monitor" in iwconfig_output:
                config.data.wifi_signal = 0  # No relevante en modo monitor
            elif "Mode:Master" in iwconfig_output:
                config.data.wifi_signal = 1  # No relevante en modo AP
            elif "Mode:Managed" in iwconfig_output:
                config.data.wifi_signal = 2  # No relevante en modo AP
                # Verificar si está conectado
                if "Access Point: Not-Associated" not in iwconfig_output:
                    # Aquí tiene sentido analizar la intensidad de la señal
                    config.data.wifi_signal = 3  # No relevante en modo AP
                    for line in iwconfig_output.splitlines():
                        if "Signal level" in line:
                            signal_line = line.strip()
                            signal_level = int(signal_line.split("Signal level=")[1].split(" ")[0])
                            # Clasificar la intensidad de la señal
                            if signal_level <= -80:
                                config.data.wifi_signal = 3  # Débil
                            elif -80 < signal_level <= -60:
                                config.data.wifi_signal = 4  # Moderada
                            elif -60 < signal_level <= -40:
                                config.data.wifi_signal = 5  # Buena
                            elif signal_level > -40:
                                config.data.wifi_signal = 6  # Excelente
                            break
                else:
                    config.data.wifi_signal = 2  # Desconectada
            else:
                config.data.wifi_signal = 2 # No manejado=Desconectado  



        except Exception as e:
            # Registrar errores y continuar el bucle
            logger.error(f"Error en el background worker: {e}")

        # Pausa antes del siguiente ciclo
        time.sleep(5)