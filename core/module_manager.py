import pkgutil
import importlib
import json
import os
import asyncio

from core.logger import setup_logger
logger = setup_logger(__name__)

class ModuleManager:
    """
    Gestor de módulos que permite la carga dinámica, activación y desactivación de módulos en el sistema.
    
    Attributes:
        modules (list): Lista de instancias de módulos cargados.
        event_system (EventSystem): Sistema de eventos que se pasa a los módulos al inicializarlos.
        modules_status (dict): Estado de los módulos (True = activado, False = desactivado).
        config_file (str): Ruta al archivo JSON que almacena la configuración de los módulos.
        module_instances (dict): Diccionario que almacena las instancias de los módulos cargados por nombre.
    """
    
    def __init__(self, event_system):
        logger.info("Iniciando el sistema de gestión de módulos")
        self.modules = []  # Lista para almacenar instancias de módulos cargados
        self.event_system = event_system  # Sistema de eventos
        self.modules_status = {}  # Estado de los módulos (activado/desactivado)
        self.config_file = 'config/modules_config.json'  # Archivo de configuración para guardar el estado de los módulos
        self.module_instances = {}  # Almacenar instancias de los módulos
        self.load_configuration()  # Cargar la configuración al iniciar
        logger.info("Gestor de módulos inicializado correctamente")

    def load_configuration(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.modules_status = json.load(f)
            logger.info(f"Configuración de módulos cargada desde {self.config_file}")
        else:
            self.modules_status = {}
            logger.info("No se encontró un archivo de configuración. Se inicializa una configuración vacía.")

    def save_configuration(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.modules_status, f)
        logger.info(f"Configuración de módulos guardada en {self.config_file}")

    def scan_modules(self):
        logger.info("Escaneando el directorio de módulos...")
        module_path = 'modules'
        available_modules = {module_name: False for _, module_name, _ in pkgutil.iter_modules([module_path])}

        for module_name in available_modules:
            if module_name not in self.modules_status:
                logger.info(f"Nuevo módulo encontrado: {module_name}")
                self.modules_status[module_name] = False  # Por defecto, los módulos están desactivados

        self.save_configuration()  # Guardar la configuración actualizada
        logger.info("Escaneo de módulos completado")

    def toggle_module(self, module_name):
        if module_name in self.modules_status:
            self.modules_status[module_name] = not self.modules_status[module_name]
            self.save_configuration()  # Guardar cambios en configuración
            logger.info(f"Módulo {module_name} {'activado' if self.modules_status[module_name] else 'desactivado'}")

            if self.modules_status[module_name]:
                self.load_module(module_name)
            else:
                self.unload_module(module_name)
        else:
            logger.error(f"El módulo {module_name} no existe en la configuración")

    def load_module(self, module_name):
        try:
            logger.info(f"Cargando módulo {module_name}...")
            module = importlib.import_module(f'modules.{module_name}')
            class_found = False
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, 'initialize'):
                    module_instance = attr()  # Crear instancia de la clase
                    module_instance.initialize(self.event_system)  # Inicializar el módulo con el sistema de eventos
                    
                    self.modules.append(module_instance)
                    self.module_instances[module_name] = module_instance  # Guardar instancia
                    class_found = True
                    
                    logger.info(f"Módulo {module_name} cargado y activado correctamente.")
                    return module_instance
            
            if not class_found:
                logger.warning(f"El módulo {module_name} no tiene una clase de inicialización.")
                return None

        except Exception as e:
            logger.error(f"Error al cargar el módulo {module_name}: {e}")
            return None

    async def unload_module(self, module_name):
        if module_name in self.module_instances:
            module_instance = self.module_instances.pop(module_name)
            
            if hasattr(module_instance, 'stop'):
                await module_instance.stop()
                logger.info(f"Método stop llamado en el módulo {module_name}.")
                
            try:
                self.modules.remove(module_instance)
                logger.info(f"Módulo {module_name} descargado correctamente.")
            except ValueError:
                logger.error(f"Advertencia: El módulo {module_name} no se encontró en la lista de módulos activos.")
        else:
            logger.error(f"Advertencia: El módulo {module_name} no está cargado en las instancias.")

    
    
    def is_module_active(self, module_name):
        """
        Verifica si un módulo está activado.

        Args:
            module_name (str): Nombre del módulo a verificar.

        Returns:
            bool: True si el módulo está activado, False si está desactivado o no existe.
        """
        if module_name in self.modules_status:
            return self.modules_status[module_name]
        else:
            logger.warning(f"El módulo {module_name} no existe en la configuración.")
            return False  # O puedes lanzar una excepción si prefieres manejarlo de otra manera.


# Ejemplo de uso del ModuleManager con el sistema de eventos:
# event_system = EventSystem()
# module_manager = ModuleManager(event_system)
# asyncio.run(module_manager.scan_modules())  # Escanear módulos asincrónicamente
