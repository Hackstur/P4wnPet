
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

from core.logger import setup_logger
logger = setup_logger(__name__)

def save_config():
    from core.config import config
    try:
        config.save_to_file("config/p4wnpet.json")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")

def run_p4wnp1_template(flag, name):
        logger.info("Ejecutando P4wnP1 template: "+name)
        run_command("P4wnP1_cli template deploy "+flag+ " "+name)
        event_system.publish("p4wn_alert", f"Template {name} deployed!", ok_callback=True)

def run_p4wnp1_hidscript(path):
    run_command(f"P4wnP1_cli hid run -c \"layout('{config.data.hid.keymap}'); typingSpeed({config.data.hid.type_speed});\"") 
    path=path.replace("/usr/local/P4wnP1/HIDScripts/","")
    hid_cmd = ['P4wnP1_cli', 'hid', 'run', '-n', path]
    process_manager.add_process(hid_cmd, name=f"HID-{os.path.basename(path)}")


def run_p4wnp1_ums(path):
    run_command(f"P4wnP1_cli usb set --rndis --hid-keyboard --hid-mouse --ums --ums-file {path}")


def mount_local_ums(path):
    name=os.path.splitext(os.path.basename(path))[0]
    run_command(f"sydi mkdir /mnt/{name}")
    run_command(f"sudo mount -o loop,rw {path} /mnt/{name}")


def sync_local_ums(path):
    a=1


def restart_p4wnpet():
    """
    Reinicia la aplicación 'P4wnPet' de forma segura, liberando el archivo PID
    y lanzando una nueva instancia de 'main.py'.
    """
    # Obtén el directorio base del proyecto desde la ubicación de este archivo
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Construye la ruta completa de 'main.py'
    main_script = os.path.join(base_dir, "main.py")

    # Ejecuta una nueva instancia de 'main.py' usando el mismo intérprete de Python
    subprocess.Popen([sys.executable, main_script])

    # Termina el proceso actual para finalizar la instancia anterior
    sys.exit()


def run_command(command, timeout=None):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar el comando: {command}\nSalida: {e.stdout.decode('utf-8')}\nError: {e.stderr.decode('utf-8')}")
    except subprocess.TimeoutExpired:
        logger.warning(f"El comando ha superado el límite de tiempo: {command}")
    return ""


def toggle_dwc2_mode():
    try:
        # Leer el archivo de configuración
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        # Comprobar si la línea "dtoverlay=dwc2" está presente
        dwc2_active = "dtoverlay=dwc2" in ''.join(lines)

        # Si está activado, desactivamos el modo
        if dwc2_active:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "dtoverlay=dwc2" not in line:
                        file.write(line)
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\ndtoverlay=dwc2\n")

        # Ejecutar el comando para reiniciar el sistema
        run_command("sudo reboot")

    except Exception as e:
        logger.error(f"Error al alternar el modo dwc2: {e}")


def is_dwc2_enabled():
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        # Verificar si la línea "dtoverlay=dwc2" está presente en el archivo
        if "dtoverlay=dwc2" in ''.join(lines):
            return True
        else:
            return False
    except Exception as e:
        return False


def is_hdmi_enabled():
    """
    Verifica si el HDMI está activado en el archivo config.txt.
    :return: True si está activado, False si no lo está.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        if "hdmi_blanking=0" in ''.join(lines):
            print("HDMI está activado.")
            return True
        else:
            print("HDMI no está activado.")
            return False
    except Exception as e:
        print(f"Error al verificar el estado del HDMI: {e}")
        return False
    

def toggle_hdmi_mode():
    """
    Alterna el estado del HDMI en el archivo config.txt.
    Si está activado, lo desactiva. Si está desactivado, lo activa.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        # Verificar si está habilitado `hdmi_blanking=1`
        hdmi_enabled = "hdmi_blanking=0" in ''.join(lines)

        if hdmi_enabled:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "hdmi_blanking=0" not in line:
                        file.write(line)
            print("HDMI desactivado correctamente.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\nhdmi_blanking=0\n")
            print("HDMI activado correctamente.")

        # Reiniciar para aplicar cambios
        print("Reiniciando el sistema...")
        run_command("sudo reboot")

    except Exception as e:
        print(f"Error al alternar el modo HDMI: {e}")

        

def toggle_audio_mode():
    """
    Alterna el estado del audio en el archivo config.txt.
    Si está activado, lo desactiva. Si está desactivado, lo activa.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        # Verificar si `dtparam=audio=on` está presente
        audio_enabled = "dtparam=audio=on" in ''.join(lines)

        if audio_enabled:
            with open("/boot/config.txt", 'w') as file:
                for line in lines:
                    if "dtparam=audio=on" not in line:
                        file.write(line)
            print("Audio desactivado correctamente.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\ndtparam=audio=on\n")
            print("Audio activado correctamente.")

        # Reiniciar para aplicar cambios
        print("Reiniciando el sistema...")
        run_command("sudo reboot")

    except Exception as e:
        print(f"Error al alternar el modo de audio: {e}")


def is_audio_enabled():
    """
    Verifica si el audio está activado en el archivo config.txt.
    :return: True si está activado, False si no lo está.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        if "dtparam=audio=on" in ''.join(lines):
            print("Audio está activado.")
            return True
        else:
            print("Audio no está activado.")
            return False
    except Exception as e:
        print(f"Error al verificar el estado del audio: {e}")
        return False
