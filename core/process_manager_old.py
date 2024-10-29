import subprocess
import os
import signal
import psutil
from core.logger import setup_logger

# Configurar el logger
logger = setup_logger(__name__)

class ProcessManager:
    """
    Process Manager que permite agregar y gestionar múltiples procesos de manera concurrente.
    """

    def __init__(self):
        """
        Inicializa el Process Manager con una lista vacía de procesos.
        """
        self.processes = []

    def add_process(self, command, name=None):
        """
        Agrega un nuevo proceso al manager y lo ejecuta.
        
        Args:
            command (list): Comando y argumentos para ejecutar el proceso.
            name (str): Nombre opcional del proceso para identificarlo.
        """
        try:
            logger.info(f"Iniciando proceso: {command}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process_info = {
                'name': name or f"Process-{process.pid}",
                'process': process,
                'pid': process.pid
            }
            self.processes.append(process_info)
            logger.info(f"Proceso {process_info['name']} con PID {process_info['pid']} iniciado.")
            return process_info['pid']
        except Exception as e:
            logger.error(f"Error al iniciar proceso: {str(e)}")
            return None

    def stop_process(self, pid=None, name=None):
        """
        Detiene un proceso específico por su PID o nombre, junto con sus subprocesos.
        
        Args:
            pid (int): PID del proceso a detener.
            name (str): Nombre del proceso a detener.
        """
        try:
            process_info = None

            # Buscar el proceso por nombre o PID
            if name:
                process_info = self.get_process_by_name(name)
            elif pid:
                process_info = self.get_process_by_pid(pid)

            if process_info:
                pid = process_info['pid']
                logger.info(f"Deteniendo proceso {process_info['name']} con PID {pid}...")

                # Obtener el proceso principal y todos sus hijos
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)

                # Primero intentar terminar todos los subprocesos
                for child in children:
                    try:
                        logger.info(f"Terminando subproceso con PID {child.pid}...")
                        child.terminate()
                    except psutil.NoSuchProcess:
                        logger.warning(f"El subproceso con PID {child.pid} ya no existe.")

                # Terminar el proceso principal
                parent.terminate()
                logger.info(f"Proceso {process_info['name']} con PID {pid} detenido.")

                # Esperar a que todos los procesos terminen
                _, still_alive = psutil.wait_procs(children + [parent], timeout=2)
                
                # Si aún están vivos, forzar la terminación
                for p in still_alive:
                    logger.warning(f"El proceso con PID {p.pid} no se detuvo a tiempo, forzando terminación...")
                    p.kill()

                logger.info(f"Todos los subprocesos y el proceso principal con PID {pid} han sido detenidos.")
                self.remove_process(pid)
            else:
                logger.warning(f"No se encontró un proceso con nombre '{name}' o PID {pid}.")
        except psutil.NoSuchProcess:
            logger.error(f"El proceso con PID {pid} no existe.")
        except Exception as e:
            logger.error(f"Error al detener el proceso: {str(e)}")

    def remove_process(self, pid):
        """
        Elimina un proceso de la lista de procesos gestionados por su PID.

        Args:
            pid (int): PID del proceso a eliminar.
        """
        self.processes = [p for p in self.processes if p['pid'] != pid]

    def get_process_by_name(self, name):
        """
        Obtiene la información de un proceso por su nombre.
        
        Args:
            name (str): Nombre del proceso a buscar.
        
        Returns:
            dict: Información del proceso, si se encuentra, o None.
        """
        for process_info in self.processes:
            if process_info['name'] == name:
                return process_info
        return None

    def get_process_by_pid(self, pid):
        """
        Obtiene la información de un proceso por su PID.
        
        Args:
            pid (int): PID del proceso a buscar.
        
        Returns:
            dict: Información del proceso, si se encuentra, o None.
        """
        for process_info in self.processes:
            if process_info['pid'] == pid:
                return process_info
        return None

    def list_processes(self):
        """
        Lista todos los procesos gestionados actualmente.
        
        Returns:
            list: Una lista de diccionarios con la información de los procesos gestionados.
        """
        logger.info("Listado de procesos en ejecución:")
        process_list = []
        for process_info in self.processes:
            process = process_info['process']
            status = "corriendo" if process.poll() is None else "terminado"
            process_data = {
                'name': process_info['name'],
                'pid': process_info['pid'],
                'status': status
            }
            process_list.append(process_data)
            logger.info(f"{process_data['name']} (PID {process_data['pid']}): {process_data['status']}")
        return process_list

    def stop_all(self):
        """
        Detiene todos los procesos gestionados por el Process Manager.
        """
        logger.info("Deteniendo todos los procesos...")
        for process_info in self.processes:
            self.stop_process(process_info['pid'])

    def process_exists(self, pid=None, name=None):
        """
        Verifica si un proceso existe por su PID o nombre.

        Args:
            pid (int, optional): PID del proceso a verificar.
            name (str, optional): Nombre del proceso a verificar.

        Returns:
            bool: True si el proceso existe, False en caso contrario.
        """
        try:
            if pid:
                return psutil.pid_exists(pid)

            if name:
                process_info = self.get_process_by_name(name)
                if process_info:
                    return psutil.pid_exists(process_info['pid'])
            return False
        except Exception as e:
            logger.error(f"Error al verificar el proceso: {str(e)}")
            return False


process_manager=ProcessManager()