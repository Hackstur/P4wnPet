import os
import subprocess
import sys
import time
import psutil
from core.menu_manager import Menu, MenuItem, menu_manager
from core.process_manager import process_manager
from core.constants import constants
from core.event_system import event_system
from core.config import config

from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)

def save_config():
    """Guarda la configuración actual en un archivo JSON."""
    from core.config import config
    try:
        config.save_to_file("config/p4wnpet.json")
        logger.info("Configuración guardada correctamente.")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")

def run_p4wnp1_template(flag, name):
    """Ejecuta un template de P4wnP1."""
    logger.info(f"Ejecutando P4wnP1 template: {name}")
    run_command(f"P4wnP1_cli template deploy {flag} {name}")
    event_system.publish("p4wn_alert", f"Template {name} deployed!", ok_callback=True)

def run_p4wnp1_hidscript(path):
    """Ejecuta un script HID de P4wnP1."""
    run_command(f"P4wnP1_cli hid run -c \"layout('{config.data.hid.keymap}'); typingSpeed({config.data.hid.type_speed});\"")
    path = path.replace("/usr/local/P4wnP1/HIDScripts/", "")
    hid_cmd = ['P4wnP1_cli', 'hid', 'run', '-n', path]
    process_manager.add_process(hid_cmd, name=f"HID-{os.path.basename(path)}")

def run_p4wnp1_ums(path):
    """Configura P4wnP1 en modo UMS."""
    run_command(f"P4wnP1_cli usb set --rndis --hid-keyboard --hid-mouse --ums --ums-file {path}")

def mount_local_ums(path):
    """Monta una imagen UMS localmente."""
    name = os.path.splitext(os.path.basename(path))[0]
    run_command(f"sudo mkdir -p /mnt/{name}")
    run_command(f"sudo mount -o loop,rw {path} /mnt/{name}")
    logger.info(f"Imagen UMS montada en /mnt/{name}")

def sync_local_ums(path):
    """Sincroniza una imagen UMS localmente."""
    # Implementar la lógica de sincronización aquí
    logger.info(f"Sincronizando imagen UMS: {path}")

def restart_p4wnpet():
    """
    Reinicia la aplicación 'P4wnPet' de forma segura, liberando el archivo PID
    y lanzando una nueva instancia de 'main.py'.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    main_script = os.path.join(base_dir, "main.py")
    logger.info("Reiniciando P4wnPet...")
    subprocess.Popen([sys.executable, main_script])
    sys.exit()

def run_command(command, timeout=None):
    """Ejecuta un comando en la terminal y retorna su salida."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        logger.info(f"Comando ejecutado: {command}")
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar el comando: {command}\nSalida: {e.stdout.decode('utf-8')}\nError: {e.stderr.decode('utf-8')}")
    except subprocess.TimeoutExpired:
        logger.warning(f"El comando ha superado el límite de tiempo: {command}")
    return ""

def toggle_dwc2_mode():
    """Alterna el modo DWC2 en el archivo de configuración."""
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        dwc2_active = "dtoverlay=dwc2" in ''.join(lines)

        if dwc2_active:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "dtoverlay=dwc2" not in line:
                        file.write(line)
            logger.info("Modo DWC2 desactivado.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\ndtoverlay=dwc2\n")
            logger.info("Modo DWC2 activado.")

        run_command("sudo reboot")

    except Exception as e:
        logger.error(f"Error al alternar el modo dwc2: {e}")

def is_dwc2_enabled():
    """Verifica si el modo DWC2 está activado en el archivo de configuración."""
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        if "dtoverlay=dwc2" in ''.join(lines):
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error al verificar el modo DWC2: {e}")
        return False

def is_hdmi_enabled():
    """Verifica si el HDMI está activado en el archivo de configuración."""
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        if "hdmi_blanking=0" in ''.join(lines):
            logger.info("HDMI está activado.")
            return True
        else:
            logger.info("HDMI no está activado.")
            return False
    except Exception as e:
        logger.error(f"Error al verificar el estado del HDMI: {e}")
        return False

def toggle_hdmi_mode():
    """
    Alterna el estado del HDMI en el archivo config.txt.
    Si está activado, lo desactiva. Si está desactivado, lo activa.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        hdmi_enabled = "hdmi_blanking=0" in ''.join(lines)

        if hdmi_enabled:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "hdmi_blanking=0" not in line:
                        file.write(line)
            logger.info("HDMI desactivado correctamente.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\nhdmi_blanking=0\n")
            logger.info("HDMI activado correctamente.")

        logger.info("Reiniciando el sistema...")
        run_command("sudo reboot")

    except Exception as e:
        logger.error(f"Error al alternar el modo HDMI: {e}")

def toggle_audio_mode():
    """
    Alterna el estado del audio en el archivo config.txt.
    Si está activado, lo desactiva. Si está desactivado, lo activa.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        audio_enabled = "dtparam=audio=on" in ''.join(lines)

        if audio_enabled:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "dtparam=audio=on" not in line:
                        file.write(line)
            logger.info("Audio desactivado correctamente.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\ndtparam=audio=on\n")
            logger.info("Audio activado correctamente.")

        logger.info("Reiniciando el sistema...")
        run_command("sudo reboot")

    except Exception as e:
        logger.error(f"Error al alternar el modo audio: {e}")

def is_audio_enabled():
    """
    Verifica si el audio está activado en el archivo config.txt.
    :return: True si está activado, False si no lo está.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        if "dtparam=audio=on" in ''.join(lines):
            logger.info("Audio está activado.")
            return True
        else:
            logger.info("Audio no está activado.")
            return False
    except Exception as e:
        logger.error(f"Error al verificar el estado del audio: {e}")
        return False
