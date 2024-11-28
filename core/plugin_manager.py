import os
import importlib
import json
import sys
import traceback

from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)

class PluginManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("Iniciando el sistema de gestión de plugins")
        
        # Atributos
        self.plugin_directory = 'plugins'  # Directorio donde se encuentran los plugins
        self.plugins_status = {}           # Diccionario para el estado de cada plugin
        self.plugin_instances = {}         # Instancias de plugins cargados
        self.config_file = "config/plugins_config.json"  # Archivo de configuración

        # Cargar configuración de plugins o iniciar vacía
        self.load_configuration()

        # Escanear el directorio de plugins
        self.scan_plugins()

        # Activar plugins según la configuración
        self.activate_plugins_from_config()

    def load_configuration(self):
        """Carga la configuración de los plugins desde un archivo JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.plugins_status = json.load(f)
                logger.info(f"Configuración de plugins cargada desde {self.config_file}")
            except Exception as e:
                logger.error(f"Error al cargar la configuración de plugins: {e}")
        else:
            self.plugins_status = {}
            logger.info("No se encontró un archivo de configuración. Se inicializa una configuración vacía.")

    def save_configuration(self):
        """Guarda la configuración de los plugins en un archivo JSON."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.plugins_status, f)
            logger.info(f"Configuración de plugins guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"Error al guardar la configuración de plugins: {e}")

    def scan_plugins(self):
        """Escanea el directorio de plugins y carga los plugins disponibles."""
        logger.info("Escaneando el directorio de plugins...")
        
        # Confirmar que el directorio de plugins existe
        if not os.path.exists(self.plugin_directory):
            logger.error(f"El directorio de plugins '{self.plugin_directory}' no existe.")
            return
        
        for file_name in os.listdir(self.plugin_directory):
            file_path = os.path.join(self.plugin_directory, file_name)
            
            # Verificar si es un archivo Python (.py) y no es __init__.py
            if file_name.endswith('.py') and not file_name.startswith('__'):
                module_name = file_name[:-3]  # Quitar el '.py' del nombre del archivo
                try:
                    module = importlib.import_module(f"{self.plugin_directory}.{module_name}")
                    plugin_class = getattr(module, module_name, None)
                    if plugin_class:
                        plugin_instance = plugin_class()
                        self.load_plugin(module_name, plugin_instance)
                        logger.info(f"Plugin {module_name} cargado desde {module_name}.py")
                    else:
                        logger.warning(f"No se encontró una clase {module_name} en {module_name}.py")
                except Exception as e:
                    logger.error(f"Error al cargar el plugin {module_name}: {e}")
                    logger.error(traceback.format_exc())

    def load_plugin(self, plugin_name, plugin_instance):
        """Carga un plugin en el sistema."""
        self.plugin_instances[plugin_name] = plugin_instance
        # No sobrescribir el estado del plugin si ya está en la configuración
        if plugin_name not in self.plugins_status:
            self.plugins_status[plugin_name] = False
        logger.info(f"Plugin {plugin_name} cargado correctamente.")

    def unload_plugin(self, plugin_name):
        """Descarga un plugin del sistema."""
        if plugin_name in self.plugin_instances:
            self.deactivate_plugin(plugin_name)
            del self.plugin_instances[plugin_name]
            del self.plugins_status[plugin_name]
            logger.info(f"Plugin {plugin_name} descargado correctamente.")
        else:
            logger.error(f"El plugin '{plugin_name}' no existe en la configuración")

    def activate_plugin(self, plugin_name):
        """Activa un plugin."""
        if plugin_name in self.plugin_instances:
            plugin_instance = self.plugin_instances[plugin_name]
            try:
                if hasattr(plugin_instance, 'initialize'):
                    plugin_instance.initialize()
                    self.plugins_status[plugin_name] = True
                    logger.info(f"Plugin {plugin_instance.name} activado correctamente.")
                else:
                    logger.error(f"El plugin {plugin_name} no tiene un método 'initialize'.")
            except Exception as e:
                logger.error(f"Error al activar el plugin {plugin_name}: {e}")
        else:
            logger.error(f"El plugin '{plugin_name}' no está cargado o no existe.")

    def deactivate_plugin(self, plugin_name):
        """Desactiva un plugin."""
        if plugin_name in self.plugin_instances:
            plugin_instance = self.plugin_instances[plugin_name]
            if hasattr(plugin_instance, 'stop'):
                try:
                    plugin_instance.stop()
                    self.plugins_status[plugin_name] = False
                    logger.info(f"Plugin {plugin_instance.name} desactivado correctamente.")
                except Exception as e:
                    logger.error(f"Error al detener el plugin {plugin_name}: {e}")
            else:
                logger.error(f"El plugin {plugin_name} no tiene un método 'stop'.")
        else:
            logger.error(f"El plugin '{plugin_name}' no está cargado o no existe.")

    def is_plugin_active(self, plugin_name):
        """Verifica si un plugin está activo."""
        return self.plugins_status.get(plugin_name, False)

    def activate_plugins_from_config(self):
        """Activa los plugins según la configuración guardada."""
        for plugin_name, is_active in self.plugins_status.items():
            if is_active:
                self.activate_plugin(plugin_name)

    def toggle_plugin(self, plugin_name):
        """Activa o desactiva un plugin según su estado actual."""
        if plugin_name in self.plugins_status:
            new_status = not self.plugins_status[plugin_name]
            self.plugins_status[plugin_name] = new_status
            self.save_configuration()

            logger.info(f"Plugin {plugin_name} {'activado' if new_status else 'desactivado'}")
            if new_status:
                self.activate_plugin(plugin_name)
            else:
                self.deactivate_plugin(plugin_name)
        else:
            logger.error(f"El plugin '{plugin_name}' no existe en la configuración")


plugin_manager=None