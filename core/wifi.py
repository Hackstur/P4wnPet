import subprocess
import threading
import time
from core.functions import run_command
from core.config import config
from core.bettercap import *
from core.process_manager import process_manager

from core.logger import setup_logger
logger = setup_logger(__name__)

# POC de modulo de control total para wifi (si me gusta la idea hare mas similares...)

class NIC:
    def __init__(self):
        self.selected="wlan0"

    def set(self, nic):
        config.data.wifi.nic=nic
        return self

    def get(self):
        return config.data.wifi.nic

    def list(self):
        try:
            # Comando para listar interfaces inalámbricas
            command = "iw dev | awk '/Interface/ { print $2 }'"
            result = run_command(command)
            logger.info("WIFI NICs: " + result)
            
            # Parsear la salida y extraer solo los nombres de las interfaces
            interfaces = result.strip().split("\n")
            
            # Si no hay interfaces, retornar None
            return interfaces if interfaces else None

        except Exception as e:
            logger.error(f"Error al listar NICs: {e}")
            return None
    

class Wifi:
    def __init__(self):
        self.nic=NIC()
        self.bettercap=None
        self.bettercap_thread=None
        self.bettercap_thread_flag=threading.Event()

    def is_monitormode(self):  # comprobar si el modo monitor está activado en el NIC seleccionado
        try:
            result = run_command("iw dev")
            
            # Verificamos si la salida contiene 'type monitor' para la interfaz indicada
            if result:
                if f"Interface {wifi.nic.get()}mon" in result:
                    # Si la interfaz está en 'type monitor', devolvemos True
                    logger.info(result)
                    if "type monitor" in result.split(f"Interface {wifi.nic.get()}mon")[1]:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    

    def toggle_monitormode(self):
        try:
            interface = wifi.nic.get()
            
            if self.is_monitormode():
                # Salir del modo monitor
                logger.info(f"Desactivando modo monitor en {interface}mon.")
                run_command(f"sudo airmon-ng stop {interface}mon")
                
                # Reinicia el módulo del controlador para evitar problemas
                logger.info("Reiniciando módulo del controlador WiFi.")
                run_command("sudo modprobe -r brcmfmac")
                run_command("sudo modprobe brcmfmac")
                
                # Reactiva la interfaz original
                logger.info(f"Levantando la interfaz {interface}.")
                run_command(f"sudo ip link set {interface} up")
                logger.info(f"Modo gestionado habilitado en {interface}.")

                # configuramos un fallback (por defecto y por el momento el startup de p4wnp1)
                run_command("P4wnP1_cli template deploy -w startup")
            else:
                # Detener servicios que interfieren y habilitar modo monitor
                logger.info("Habilitando modo monitor.")
                run_command("sudo airmon-ng check kill")
                run_command(f"sudo airmon-ng start {interface}")
                logger.info(f"Modo monitor habilitado en {interface}mon.")
    
        except Exception as e:
            logger.error(f"Error al cambiar el modo de la interfaz {interface}: {e}")

    def networks(self): # lista los AP cercanos (escaneados en background)
        if hasattr(config.data.wifi, 'networks'):
            networks = config.data.wifi.networks
            return networks if networks else None
        return None

    def toggle_bettercap(self):
        if self.is_bettercap_running():
            stop_process = subprocess.run(["sudo", "pkill", "-f", "bettercap"], capture_output=True, text=True)
            if stop_process.returncode == 0:
                logger.info("Bettercap detenido correctamente.")
            else:
                logger.info(f"Error al intentar detener Bettercap: {stop_process.stderr}")
        else:

            self.bettercap = Client()
            time.sleep(1)
            
            while self.bettercap.successful==False:
                logger.info("waiting bettercap API REST")
                time.sleep(2)

            time.sleep(2)
            logger.info("Bettercap API rest DETECTED!! launch background worker")
            self.bettercap.clearWifi()
            self.bettercap.recon()



    def is_bettercap_running(self):
        check_process = subprocess.run(["pgrep", "-f", "bettercap"], capture_output=True, text=True)
        if check_process.returncode==0:
            return True
        else:
            return False


wifi=Wifi()