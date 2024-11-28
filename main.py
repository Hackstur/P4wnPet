import os
import sys
import time
import signal
import threading
import traceback

from core.functions import run_command
from core.plugin_manager import plugin_manager, PluginManager
from core.menu_manager import menu_manager, Menu
from core.event_system import event_system
from core.menu import menu_creator
from core.background import background_worker

from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)

LOCK_FILE = "/tmp/p4wnpet.lock"

def create_lock_file():
    """Crea un archivo de bloqueo para asegurar una única instancia de la aplicación."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as lock_file:
                pid = int(lock_file.read().strip())
                logger.info(f"Matando proceso anterior con PID {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)  # Esperar 1 segundo para asegurarse de que el proceso anterior se haya terminado
        except Exception as e:
            logger.error(f"Error al intentar matar el proceso anterior: {e}")
    
    with open(LOCK_FILE, 'w') as lock_file:
        lock_file.write(str(os.getpid()))

def remove_lock_file():
    """Elimina el archivo de bloqueo."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def main():
    logger.info("Iniciando P4wnPet")

    create_lock_file()
    logger.info("Fichero lock creado")
    run_command("sudo rm -rf /root/P4wnPet/logs/bettercap.log")

    try:
        # Cargar plugins
        plugin_manager=PluginManager()

        # CONFIGURAMOS LOS MENUS DESPUES DE LOS PLUGINS PARA QUE SE SUBSCRIBAN
        main_menu = Menu("P4WNPET")
        menu_creator(main_menu)
        menu_manager.set_menu(main_menu)

        # BACKGROUND WORKER
        background_thread = threading.Thread(target=background_worker, daemon=True)
        background_thread.start()
        logger.info("Lanzando proceso en background")

        event_system.publish("p4wn_start")

    except Exception as e:
        logger.error(f"Error durante la ejecución de P4wnPet: {e}")
        logger.error(traceback.format_exc())

    finally:
        remove_lock_file()

if __name__ == "__main__":
    main()
