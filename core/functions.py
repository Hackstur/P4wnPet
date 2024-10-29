
import os
import re
import asyncio

import subprocess
import time

from core.process_manager import process_manager

from core.logger import setup_logger
logger = setup_logger(__name__)



import re
import subprocess



def verify_handshake(handshake_dir, bssid, check_only=False):
    """
    Verifica si hay handshakes en el archivo de captura.
    
    Args:
        handshake_dir (str): Ruta del directorio donde se almacenan los handshakes.
        bssid (str): BSSID de la red WiFi.
        check_only (bool): Si es True, solo comprueba si hay handshakes y no detiene procesos.
    
    Returns:
        bool: True si hay handshakes, False en caso contrario.
    """
    capture_file = os.path.join(handshake_dir, 'capture-01.cap')  # Cambia esto si tu archivo tiene un nombre diferente

    while True:
        # Comprobar el handshake usando aircrack-ng
        try:
            result = subprocess.run(['aircrack-ng', capture_file], capture_output=True, text=True)
            output = result.stdout
            logger.info(output)

            # Buscar el número de handshakes en la salida
            match = re.search(r'(\d+) handshakes?', output.lower())
            if match:
                num_handshakes = int(match.group(1))  # Convertir el número a entero
                logger.info(f"Se detectaron {num_handshakes} handshakes.")

                if num_handshakes > 0:  # Verificar si hay más de 0 handshakes
                    if check_only:
                        return True
                    
                    logger.info("Handshake detectado. Deteniendo captura y desautenticaciones.")
                    process_manager.stop_process(name=f"HandshakeCapture-{bssid}")

                    # Detener procesos de desautenticación
                    for client in get_connected_clients(bssid):
                        process_manager.stop_process(name=f"DeauthClient-{client}")

                    break  # Salir del bucle de verificación
            else:
                logger.info("No se detectaron handshakes en el archivo de captura.")

            if check_only:
                return False

        except Exception as e:
            logger.error(f"Error al verificar handshake: {e}")

        time.sleep(5)  # Esperar 5 segundos antes de volver a verificar

               


def get_connected_clients(bssid, interface="wlan0mon"):
    """
    Obtiene una lista de clientes conectados a una red WiFi específica.

    Args:
        bssid (str): BSSID de la red WiFi.
        interface (str): Interfaz de red en modo monitor. Por defecto, 'wlan0mon'.
    
    Returns:
        list: Lista de direcciones MAC de los clientes conectados.
    """
    try:
        # Comando para capturar los clientes conectados con airodump-ng
        cmd = ['sudo', 'airodump-ng', '--bssid', bssid, '--write-interval', '1', '-w', '/dev/null', interface]

        # Ejecutar el comando y capturar su salida
        logger.info(f"Ejecutando airodump-ng para obtener clientes conectados a la red {bssid}...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)

        if result.returncode != 0:
            logger.error(f"Error ejecutando airodump-ng: {result.stderr}")
            return []

        # Procesar la salida de airodump-ng
        output = result.stdout
        clients = []

        # Expresión regular para capturar las direcciones MAC de los clientes conectados
        client_mac_pattern = re.compile(r'((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})\s+-\d+.*\d+.\d+.\d+.\d+')  # Patrón de MAC del cliente

        for line in output.splitlines():
            match = client_mac_pattern.search(line)
            if match:
                client_mac = match.group(1).strip()
                clients.append(client_mac)

        if clients:
            logger.info(f"Clientes conectados encontrados para {bssid}: {clients}")
        else:
            logger.info(f"No se encontraron clientes conectados para {bssid}.")
        
        return clients

    except subprocess.TimeoutExpired:
        logger.error("El proceso de airodump-ng ha expirado.")
        return []
    except Exception as e:
        logger.error(f"Error al obtener clientes conectados: {str(e)}")
        return []


class Network:
    def __init__(self, essid=None, bssid=None, security=None, channel=None):
        self.essid = essid
        self.bssid = bssid
        self.security = security
        self.channel = channel

    def __repr__(self):
        return f"Network(ESSID={self.essid}, BSSID={self.bssid}, Security={self.security}, Channel={self.channel})"

    def to_dict(self):
            """Convierte la instancia en un diccionario."""
            return {
                "essid": self.essid,
                "bssid": self.bssid,
                "security": self.security,
                "channel": self.channel
            }





def run_command(command, timeout=None):
    """Ejecuta un comando y devuelve la salida, con un timeout opcional."""
    logger.info(f"Ejecutando comando: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        logger.info(f"Comando ejecutado exitosamente: {command}")
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar el comando: {command}\nSalida: {e.stdout.decode('utf-8')}\nError: {e.stderr.decode('utf-8')}")
    except subprocess.TimeoutExpired:
        logger.warning(f"El comando ha superado el límite de tiempo: {command}")
    return ""


def is_monitor_mode(interface="wlan0"):
    """Comprueba si una interfaz de red está en modo monitor."""
    return 'type monitor' in run_command(f"iw dev {interface}mon info")

def enable_monitor_mode(interface="wlan0"):
    """Activa el modo monitor en una interfaz de red, asegurándose de que no haya procesos que interfieran."""
    try:
        # Ejecutar airmon-ng check kill para matar procesos que puedan interferir
        run_command("airmon-ng check kill")
        
        # Activar el modo monitor con airmon-ng
        run_command(f"airmon-ng start {interface}")
        
        logger.info(f"Módulo monitor activado en la interfaz: {interface}")
        return True
    except Exception as e:
        logger.error(f"Error al activar el modo monitor en {interface}: {e}")
        return False
    

def disable_monitor_mode(interface="wlan0"):
    """Desactiva el modo monitor en una interfaz de red y la levanta de nuevo."""
    try:
        # Detener la interfaz en modo monitor
        run_command(f"airmon-ng stop {interface}mon")  # 'interface' + 'mon' para la interfaz en modo monitor
        
        # Levantar la interfaz original
        run_command(f"ip link set {interface} up")
        
        logger.info(f"Módulo monitor desactivado y la interfaz restaurada: {interface}")
        return True
    except Exception as e:
        logger.error(f"Error al desactivar el modo monitor en {interface}: {e}")
        return False
    


def scan_wifi_with_iwlist(interface="wlan0"):
    """
    Escanea las redes WiFi disponibles utilizando iwlist (modo normal), extrayendo solo el ESSID y BSSID (MAC).
    
    Args:
        interface (str): La interfaz WiFi a escanear (por defecto "wlan0").
        
    Returns:
        list: Lista de redes encontradas, cada una representada como una tupla (BSSID, ESSID).
    """
    try:

        """
        # Ejecutar el comando iwlist
        result = run_command(f"iwlist {interface} scanning")
        
        # Ver la salida de iwlist para depuración
        logger.info("Resultado del comando iwlist:")
        logger.info(result)

        
        # Expresión regular para extraer el BSSID y ESSID           # ESTO FUNCIONA DPM
        pattern = (
            r'Cell \d+ - Address: ([0-9A-Fa-f:]{17})\s+.*?'  # BSSID
            r'ESSID:"([^"]*)"'  # ESSID
        )

        # Buscar coincidencias en el resultado del escaneo
        matches = re.findall(pattern, result, re.DOTALL)
        networks = []

        # Procesar las coincidencias y construir la lista de redes
        for match in matches:
            bssid, essid = match
            essid = essid if essid else "HIDDEN"  # Mostrar como oculto si no hay ESSID
            networks.append((bssid, essid))  # Solo BSSID y ESSID
        """

        # Ejecutar el comando para escanear las redes WiFi
        result = run_command("iwlist wlan0 scan | awk '/Quality|ESSID|Channel|Encryption key|WPA|WEP|WPS|Address/ { print $0 }'")
        logger.info("resultado comando iwlist wlan0 scanning ->"+result)

        networks=[]

        """ ESTO TAMBIEN FUNCIONA
       # Expresión regular para extraer la dirección, ESSID y estado de la clave
        pattern = r'Cell \d+ - Address:\s*([0-9A-Fa-f:]{17}).*?Quality=\d+/\d+\s+Signal level=-?\d+\s+dBm\s+Encryption key:(on|off)\s+ESSID:"([^"]*)".*?(?:IE: (?:IEEE 802\.11i/WPA2 Version 1|WPA Version 1|WEP).*?)?'
        
        # Buscar coincidencias en el resultado del escaneo
        matches = re.findall(pattern, result, re.DOTALL)
        
        # Añadir cada red WiFi como ítem en el menú
        for match in matches:
            logger.info("REGULAR EXPRESION MATCHED!:" + match[0])
            mac = match[0]
            encryption = match[1]
            essid = match[2]
            security = "WPA2" if encryption == "on" else "OPEN"

            networks.append((mac, essid, security))
    
            
            #ESTO TAMBIEN FUNCIONA BIEN
        pattern = (
            r'Cell \d+ - Address:\s*([0-9A-Fa-f:]{17}).*?Quality=\d+/\d+\s+Signal level=-?\d+\s+dBm\s+'
            r'Encryption key:(on|off)\s+ESSID:"([^"]*)".*?'
            r'(?:IE:\s*(WPA3|IEEE 802\.11i/WPA2 Version 1|WPA Version 1|WEP).*?)*'
        )

        # Buscar coincidencias en el resultado del escaneo
        matches = re.findall(pattern, result, re.DOTALL)

        # Añadir cada red WiFi como ítem en el menú
        for match in matches:
            logger.info("REGULAR EXPRESION MATCHED!:" + match[0])
            mac = match[0]
            encryption = match[1]
            essid = match[2]

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

            networks.append((mac, essid, security))
        """
        pattern = (
            r'Cell \d+ - Address:\s*([0-9A-Fa-f:]{17})\s*.*?'
            r'Channel:(\d+)\s*.*?'
            r'Quality=\d+/\d+\s+Signal level=-?\d+\s+dBm\s*.*?'
            r'Encryption key:(on|off)\s*.*?'
            r'ESSID:"([^"]*)"\s*.*?'
            r'(?:IE:\s*(WPA3|IEEE 802\.11i/WPA2 Version 1|WPA Version 1|WEP).*?)*'
        )

        # Buscar coincidencias en el resultado del escaneo
        matches = re.findall(pattern, result, re.DOTALL)

        # Añadir cada red WiFi como ítem en el menú
        for match in matches:
            logger.info("REGULAR EXPRESION MATCHED!:" + match[0])
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



        logger.info(f"Redes encontradas: {networks}")
        return networks

    except Exception as e:
        logger.error(f"Error al escanear con iwlist: {e}")
        return []
    


def scan_wifi_with_airodump(interface="wlan0"):
    """
    Escanea las redes WiFi disponibles utilizando airodump-ng (modo monitor), incluyendo el canal de cada red.
    """
    try:
        # Ejecutar airodump-ng para escanear las redes
        command = f"airodump-ng {interface} --write-interval 1 --output-format csv -w /tmp/scan_results"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        
        # Leer los resultados CSV de airodump-ng
        with open("/tmp/scan_results-01.csv", "r") as file:
            lines = file.readlines()

        networks = []
        parsing_networks = False

        # Procesar el archivo CSV para obtener las redes
        for line in lines:
            line = line.strip()
            if line.startswith("BSSID"):  # La tabla de redes empieza aquí
                parsing_networks = True
                continue

            if parsing_networks:
                if line == "":  # Fin de la sección de redes
                    break

                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 14:
                    bssid = parts[0]  # BSSID de la red
                    channel = parts[3]  # Canal de la red
                    essid = parts[13] if parts[13] != "" else "HIDDEN"  # Nombre de la red (ESSID)
                    encryption = "WPA2" if "WPA2" in parts[5] else ("WEP" if "WEP" in parts[5] else "OPEN")  # Tipo de cifrado
                    networks.append((bssid, essid, encryption, channel))  # Incluir canal en la tupla

        return networks

    except Exception as e:
        print(f"Error al escanear con airodump-ng: {e}")
        return []



def getNICnames():
    """ Extract network device names from /proc/net/dev.

        Returns list of device names.  Returns empty list if no network
        devices are present.

        >>> getNICnames()
        ['lo', 'eth0']

    """
    device = re.compile('[a-z]{2,}[0-9]*:')
    ifnames = []

    fp = open('/proc/net/dev', 'r')
    for line in fp:
        try:
            # append matching pattern, without the trailing colon
            ifnames.append(device.search(line).group()[:-1])
        except AttributeError:
            pass
    return ifnames


def getWNICnames():
    """ Extract wireless device names from /proc/net/wireless.

        Returns empty list if no devices are present.

        >>> getWNICnames()
        ['eth1', 'wifi0']

    """
    device = re.compile('[a-z]{2,}[0-9]*:')
    ifnames = []

    fp = open('/proc/net/wireless', 'r')
    for line in fp:
        try:
            # append matching pattern, without the trailing colon
            ifnames.append(device.search(line).group()[:-1])
        except AttributeError:
            pass
    # if we couldn't lookup the devices, try to ask the kernel
    if ifnames == []:
        #ifnames = getConfiguredWNICnames()
        pass

    return ifnames

