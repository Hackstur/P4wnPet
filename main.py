import os
import sys
import fcntl
import signal
import traceback
import asyncio
from core.pet import Pet
from core.logger import setup_logger

# Configuración del logger para este módulo
logger = setup_logger(__name__)

class SingletonApp:
    """
    Clase que asegura que solo una instancia de la aplicación se ejecute al mismo tiempo,
    utilizando un archivo de PID para gestionar la instancia única.
    
    Attributes:
        pid_file (str): Ruta al archivo que almacena el PID de la aplicación.
        pid_file_handle (file object): Referencia al archivo de PID abierto para bloqueo.
    """
    
    def __init__(self, pid_file):
        """
        Inicializa la clase SingletonApp con la ruta al archivo de PID.
        
        Args:
            pid_file (str): Ruta al archivo donde se almacenará el PID.
        """
        self.pid_file = pid_file
        self.pid_file_handle = None
        logger.info(f"Inicializando SingletonApp con archivo PID en {self.pid_file}")
    
    def ensure_single_instance(self):
        """
        Asegura que solo una instancia de la aplicación se esté ejecutando.
        Si se encuentra una instancia anterior, intenta detenerla antes de iniciar una nueva.
        """
        try:
            # Si existe un archivo PID, intentaremos eliminar el proceso anterior
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Verificar si el proceso sigue activo
                try:
                    os.kill(old_pid, 0)
                except ProcessLookupError:
                    # El proceso no existe, podemos continuar sin problemas
                    logger.info("No se encontró un proceso activo con el PID almacenado.")
                else:
                    # Proceso activo encontrado, intentamos detenerlo
                    logger.info(f"Terminando el proceso existente con PID {old_pid}")
                    os.kill(old_pid, signal.SIGTERM)  # Señal para terminar el proceso
                    logger.info(f"Proceso {old_pid} terminado")

            # Abrimos el archivo de PID para escritura y bloqueamos
            self.pid_file_handle = open(self.pid_file, 'w')
            fcntl.lockf(self.pid_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Escribimos el nuevo PID
            self.pid_file_handle.write(str(os.getpid()))
            self.pid_file_handle.flush()
            logger.info(f"Instancia única asegurada, PID {os.getpid()} escrito en {self.pid_file}")
        
        except IOError:
            logger.error("Error al intentar asegurar la instancia única")
            sys.exit(1)

    def cleanup(self):
        """
        Limpia el archivo de PID y libera el bloqueo.
        
        Se llama típicamente al final de la ejecución de la aplicación para
        liberar los recursos y eliminar el archivo PID.
        """
        try:
            if self.pid_file_handle:
                fcntl.lockf(self.pid_file_handle, fcntl.LOCK_UN)
                self.pid_file_handle.close()
            os.remove(self.pid_file)
            logger.info(f"Archivo PID {self.pid_file} eliminado correctamente")
        except Exception as e:
            logger.error(f"Error al limpiar el archivo PID: {e}")


def main():
    """
    Función principal de la aplicación. Configura la instancia única y maneja la ejecución principal.
    """
    logger.info("Iniciando P4wnPet")
    
    # Crear una instancia de SingletonApp para asegurar ejecución única
    logger.info("Asegurando instancia única de P4wnPet")
    singleton = SingletonApp("/tmp/p4wnpet.pid")  # Ruta donde se almacena el archivo de PID
    singleton.ensure_single_instance()

    try:
        # Aquí se incluye la lógica principal de la aplicación

        logger.info("Configurando clase Pet")
        p4wnpet = Pet()  # Crear instancia de la clase principal de la aplicación

        # Ejecutar 
        p4wnpet.start()  # Iniciar la lógica del tamagotchi

    except Exception as e:
        logger.error(f"Error durante la ejecución de P4wnPet: {e}")
        logger.error(traceback.format_exc())

    finally:
        # Limpieza del archivo PID al finalizar la ejecución
        logger.info("Finalizando P4wnPet y realizando limpieza")
        singleton.cleanup()

if __name__ == "__main__":
    main()
