
import os
import re

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




import re
import subprocess

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


# 
def run_p4wnp1_ums(path):
    #ums_cmd=['P4wnP1_cli', 'usb', 'set',  '--rndis', '--hid-keyboard', '--hid-mouse', '--ums', '--ums-file', path]
    #process_manager.add_process(ums_cmd,"UMS: "+path)

    run_command(f"P4wnP1_cli usb set --rndis --hid-keyboard --hid-mouse --ums --ums-file {path}")

    

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



