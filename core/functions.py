
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

def measure_write_speed(path, size_mb=100, sample_factor=0.1):
    """
    Mide la velocidad de escritura en MB/s en la ruta especificada, usando un bloque reducido y extrapolando el resultado.

    :param path: Ruta donde se creará el archivo temporal (debe estar en la tarjeta SD o dispositivo a probar).
    :param size_mb: Tamaño del archivo de prueba en megabytes (por defecto, 100 MB).
    :param sample_factor: Porción de 1 MB a escribir en cada ciclo, se usa para extrapolar el resultado (por defecto, 0.1 MB).
    :return: Velocidad de escritura en MB/s (redondeada a 2 decimales).
    """
    test_file = os.path.join(path, "write_speed_test.tmp")
    sample_size = int(1024 * 1024 * sample_factor)  # Bloque de prueba en bytes
    data = b'0' * sample_size
    iterations = int(size_mb / sample_factor)  # Número de veces que escribiremos el bloque reducido

    try:
        start = time.time()
        with open(test_file, 'wb') as file:
            for _ in range(iterations):
                file.write(data)
        end = time.time()

        total_time = end - start
        write_speed = size_mb / total_time if total_time > 0 else 0
    finally:
        # Eliminar el archivo de prueba después de la prueba
        if os.path.exists(test_file):
            os.remove(test_file)

    return round(write_speed, 2)

def measure_read_speed(path, size_mb=100, sample_factor=0.1):
    """
    Mide la velocidad de lectura en MB/s desde un archivo en la ruta especificada, usando un bloque reducido y extrapolando el resultado.

    :param path: Ruta donde se leerá el archivo temporal (debe estar en la tarjeta SD o dispositivo a probar).
    :param size_mb: Tamaño del archivo de prueba en megabytes (por defecto, 100 MB).
    :param sample_factor: Porción de 1 MB a leer en cada ciclo, se usa para extrapolar el resultado (por defecto, 0.1 MB).
    :return: Velocidad de lectura en MB/s (redondeada a 2 decimales).
    """
    test_file = os.path.join(path, "read_speed_test.tmp")
    sample_size = int(1024 * 1024 * sample_factor)  # Bloque de prueba en bytes
    data = b'0' * sample_size
    iterations = int(size_mb / sample_factor)  # Número de veces que leeremos el bloque reducido

    # Crear el archivo de prueba para medir la velocidad de lectura
    with open(test_file, 'wb') as file:
        for _ in range(iterations):
            file.write(data)

    try:
        start = time.time()
        with open(test_file, 'rb') as file:
            for _ in range(iterations):
                file.read(sample_size)
        end = time.time()

        total_time = end - start
        read_speed = size_mb / total_time if total_time > 0 else 0
    finally:
        # Eliminar el archivo de prueba después de la prueba
        if os.path.exists(test_file):
            os.remove(test_file)

    return round(read_speed, 2)

def toggle_dwc2_mode():
    """
    Alterna el estado del controlador dwc2 en el archivo config.txt.
    Si está activado, lo desactiva. Si está desactivado, lo activa.
    """
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
            print("Modo dwc2 desactivado correctamente.")
        else:
            with open("/boot/config.txt", 'a') as file:
                file.write("\ndtoverlay=dwc2\n")
            print("Modo dwc2 activado correctamente.")

        # Ejecutar el comando para reiniciar el sistema
        print("Reiniciando el sistema...")
        run_command("sudo reboot")

    except Exception as e:
        print(f"Error al alternar el modo dwc2: {e}")


def is_dwc2_enabled():
    """
    Verifica si el modo dwc2 está activado en el archivo config.txt.
    :return: True si está activado, False si no lo está.
    """
    try:
        with open("/boot/config.txt", 'r') as file:
            lines = file.readlines()

        # Verificar si la línea "dtoverlay=dwc2" está presente en el archivo
        if "dtoverlay=dwc2" in ''.join(lines):
            print("El modo dwc2 está activado.")
            return True
        else:
            print("El modo dwc2 no está activado.")
            return False
    except Exception as e:
        print(f"Error al verificar el modo dwc2: {e}")
        return False
