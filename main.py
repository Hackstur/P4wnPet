import os
import sys
import fcntl
import signal
import threading
import traceback
from core.logger import setup_logger

from core.plugin_manager import plugin_manager
from core.menu_manager import menu_manager, Menu
from core.event_system import event_system
from core.menu import menu_creator
from core.background import background_worker

# Configuración del logger para este módulo
logger = setup_logger(__name__)

class SingletonApp:
    
    def __init__(self, pid_file):
        self.pid_file = pid_file
        self.pid_file_handle = None
        logger.info(f"Inicializando SingletonApp con archivo PID en {self.pid_file}")
    
    def ensure_single_instance(self):

        try:
            # Verificar si el archivo PID existe
            if os.path.exists(self.pid_file):
                logger.info(f"Archivo PID encontrado en {self.pid_file}, intentando procesarlo")
                
                # Leer el contenido del archivo PID
                with open(self.pid_file, 'r') as f:
                    pid_content = f.read().strip()
                
                # Verificar si el contenido del PID es válido
                if pid_content.isdigit():
                    old_pid = int(pid_content)
                    
                    # Intentar matar el proceso si está activo
                    try:
                        os.kill(old_pid, 0)  # Verifica si el proceso aún existe
                        logger.info(f"Proceso activo con PID {old_pid} encontrado. Terminando el proceso.")
                        os.kill(old_pid, signal.SIGTERM)  # Envía señal de terminación
                    except ProcessLookupError:
                        logger.info("No se encontró un proceso activo con el PID almacenado.")
                    except PermissionError:
                        logger.error(f"No se tienen permisos para finalizar el proceso con PID {old_pid}")
                        sys.exit(1)
                else:
                    logger.warning(f"El archivo PID contiene un valor inválido: '{pid_content}'")

                # Eliminar el archivo PID en cualquier caso
                logger.info(f"Eliminando archivo PID {self.pid_file}")
                os.remove(self.pid_file)

            # Abrir el archivo de PID para escritura y bloquearlo
            self.pid_file_handle = open(self.pid_file, 'w')
            fcntl.lockf(self.pid_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Escribir el nuevo PID en el archivo PID
            self.pid_file_handle.write(str(os.getpid()))
            self.pid_file_handle.flush()
            logger.info(f"Instancia única asegurada, PID {os.getpid()} escrito en {self.pid_file}")
        
        except IOError:
            logger.error("Error al intentar asegurar la instancia única. Otro proceso está bloqueando el archivo PID.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error inesperado al asegurar instancia única: {e}")
            sys.exit(1)

    def cleanup(self):

        try:
            if self.pid_file_handle:
                fcntl.lockf(self.pid_file_handle, fcntl.LOCK_UN)
                self.pid_file_handle.close()
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                logger.info(f"Archivo PID {self.pid_file} eliminado correctamente")
        except Exception as e:
            logger.error(f"Error al limpiar el archivo PID: {e}")


def main():

    logger.info("Iniciando P4wnPet")
    
    # Crear una instancia de SingletonApp para asegurar ejecución única
    logger.info("Asegurando instancia única de P4wnPet")
    singleton = SingletonApp("/tmp/p4wnpet.pid")  # Ruta donde se almacena el archivo de PID
    singleton.ensure_single_instance()

    try:


        # CONFIGURAMOS LOS MENUS DESPUES DE LOS PLUGINS PARA QUE SE SUBSCRIBAN
        main_menu=Menu("P4WNPET")
        menu_creator(main_menu)
        menu_manager.set_menu(main_menu)

        # BACKGROUND WORKER
        background_thread=threading.Thread(target=background_worker, daemon=True)
        background_thread.start()
        logger.info("Lanzando proceso en background")

        event_system.publish(("p4wn_start"))

    except Exception as e:
        logger.error(f"Error durante la ejecución de P4wnPet: {e}")
        logger.error(traceback.format_exc())

    finally:
        # Limpieza del archivo PID al finalizar la ejecución
        logger.info("Finalizando P4wnPet y realizando limpieza")
        singleton.cleanup()

if __name__ == "__main__":
    main()
