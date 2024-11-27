import subprocess
import psutil
import threading
import queue

# Configurar el logger
from core.logger import setup_logger
logger = setup_logger(__name__)

class ProcessManager:

    def __init__(self):
        self.processes = []
        self.output_queue = queue.Queue()  # Cola para capturar la salida sin bloqueo

    def _enqueue_output(self, stream, queue, name, pipe_name, output_mode=None, filepath=None):
        """
        Captura la salida del proceso y la dirige según el modo configurado.
        """
        try:
            if filepath:
                with open(filepath, "a") as log_file:
                    for line in iter(stream.readline, ''):
                        if line:
                            formatted_line = f"[{name}] {pipe_name}: {line.strip()}"
                            if output_mode == "console":
                                print(formatted_line)
                            if output_mode in ("file", "both"):
                                log_file.write(formatted_line + "\n")
                                log_file.flush()
                            if output_mode in ("console", "both"):
                                queue.put(formatted_line)
            else:
                for line in iter(stream.readline, ''):
                    if line:
                        formatted_line = f"[{name}] {pipe_name}: {line.strip()}"
                        if output_mode == "console":
                            print(formatted_line)
                        if output_mode in ("console", "both"):
                            queue.put(formatted_line)
        except Exception as e:
            logger.error(f"Error leyendo la salida del proceso {name}: {str(e)}")

    def add_process(self, command, name=None, output_mode=None, filepath=None):
        """
        Inicia un proceso y configura cómo se gestionará su salida.
        """
        try:
            # Limpiar el archivo si se proporcionó un filepath
            if filepath and output_mode in ("file", "both"):
                with open(filepath, 'w') as f:
                    pass  # Crear/vaciar el archivo

            logger.info(f"Iniciando proceso: {command}")

            # Crear el proceso usando Popen y capturar stdout/stderr
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            process_info = {
                'name': name or f"Process-{process.pid}",
                'process': process,
                'pid': process.pid,
                'log_file': filepath  # Guardar el filepath (si existe) en la información del proceso
            }

            # Añadir el proceso a la lista de procesos gestionados
            self.processes.append(process_info)

            logger.info(f"Proceso {process_info['name']} con PID {process_info['pid']} iniciado.")

            # Iniciar hilos para capturar la salida sin bloquear
            threading.Thread(
                target=self._enqueue_output, 
                args=(process.stdout, self.output_queue, process_info['name'], 'stdout', output_mode, filepath),
                daemon=True
            ).start()
            threading.Thread(
                target=self._enqueue_output, 
                args=(process.stderr, self.output_queue, process_info['name'], 'stderr', output_mode, filepath),
                daemon=True
            ).start()

            return process_info['pid']
        except Exception as e:
            logger.error(f"Error al iniciar proceso: {str(e)}")
            return None

    def remove_terminated_processes(self):
        self.processes = [p for p in self.processes if p['process'].poll() is None]

    def list_processes(self):
        self.remove_terminated_processes()
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

    def stop_process(self, pid=None, name=None):
        try:
            process_info = None

            if name:
                process_info = self.get_process_by_name(name)
            elif pid:
                process_info = self.get_process_by_pid(pid)

            if process_info:
                pid = process_info['pid']
                logger.info(f"Deteniendo proceso {process_info['name']} con PID {pid}...")

                parent = psutil.Process(pid)
                children = parent.children(recursive=True)

                for child in children:
                    try:
                        logger.info(f"Terminando subproceso con PID {child.pid}...")
                        child.terminate()
                    except psutil.NoSuchProcess:
                        logger.warning(f"El subproceso con PID {child.pid} ya no existe.")

                parent.terminate()
                logger.info(f"Proceso {process_info['name']} con PID {pid} detenido.")

                _, still_alive = psutil.wait_procs(children + [parent], timeout=2)
                
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
        self.processes = [p for p in self.processes if p['pid'] != pid]

    def get_process_by_name(self, name):
        for process_info in self.processes:
            if process_info['name'] == name:
                return process_info
        return None

    def get_process_by_pid(self, pid):
        for process_info in self.processes:
            if process_info['pid'] == pid:
                return process_info
        return None

    def stop_all(self):
        logger.info("Deteniendo todos los procesos...")
        for process_info in self.processes:
            self.stop_process(process_info['pid'])

    def process_exists(self, pid=None, name=None):
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

    def monitor_output(self):
        """
        Muestra la salida de la cola en tiempo real.
        """
        while True:
            try:
                output = self.output_queue.get(timeout=1)
                if output is not None:
                    logger.info(output)
            except queue.Empty:
                continue



process_manager=ProcessManager()