import os
import importlib
import json
import sys
import traceback

from core.logger import setup_logger
logger = setup_logger(__name__)

class PluginManager:
    def __init__(self):
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

    def load_configuration(self):
        """Carga el estado de activación de los plugins desde un archivo JSON."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.plugins_status = json.load(f)
            logger.info(f"Configuración de plugins cargada desde {self.config_file}")
        else:
            self.plugins_status = {}
            logger.info("No se encontró un archivo de configuración. Se inicializa una configuración vacía.")

    def save_configuration(self):
        """Guarda el estado de activación de los plugins en un archivo JSON."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.plugins_status, f)
            logger.info(f"Configuración de plugins guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"Error al guardar la configuración de plugins: {e}")

    def scan_plugins(self):
        """Escanea el directorio de plugins y los carga si tienen una clase con el mismo nombre que el archivo."""
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
                sys.path.insert(0, self.plugin_directory)  # Añadir el directorio de plugins al path
                
                try:
                    # Importamos el módulo del plugin
                    plugin_module = importlib.import_module(module_name)
                    self._load_plugin_class(plugin_module, module_name)
                except Exception as e:
                    logger.error(f"Error al importar el plugin {module_name}: {e}")
                    logger.error("Detalles del error:")
                    logger.error(traceback.format_exc())
                finally:
                    sys.path.pop(0)

        # Después de escanear todos los plugins, verificamos el estado y activamos los que estén activos en la configuración
        self.activate_plugins_from_config()
        
        self.save_configuration()
        logger.info("Escaneo de plugins completado")

    def _load_plugin_class(self, plugin_module, module_name):
        """Carga la clase principal del plugin, que tiene el mismo nombre que el archivo."""
        class_name = module_name  # El nombre de la clase es el nombre del archivo
        if hasattr(plugin_module, class_name):
            plugin_class = getattr(plugin_module, class_name)
            plugin_instance = plugin_class()  # Crear una instancia del plugin

            self.plugin_instances[module_name] = plugin_instance

            # Actualizar estado del plugin si no estaba registrado
            if module_name not in self.plugins_status:
                self.plugins_status[module_name] = False  # Inactivo por defecto

            logger.info(f"Plugin encontrado: {plugin_instance.name} por {plugin_instance.author}")
        else:
            logger.warning(f"No se encontró una clase {class_name} en {module_name}.py")

    def activate_plugins_from_config(self):
        """Verifica el estado de los plugins y los activa si están marcados como activados en la configuración."""
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

    def activate_plugin(self, plugin_name):
        """Activa un plugin y llama a su método `initialize`."""
        if plugin_name in self.plugin_instances:
            plugin_instance = self.plugin_instances[plugin_name]
            try:
                plugin_instance.initialize()
                logger.info(f"Plugin {plugin_instance.name} activado correctamente.")
            except Exception as e:
                logger.error(f"Error al activar el plugin {plugin_name}: {e}")
        else:
            logger.error(f"El plugin '{plugin_name}' no está cargado o no existe.")

    def deactivate_plugin(self, plugin_name):
        """Desactiva un plugin llamando a su método `stop` si está definido."""
        if plugin_name in self.plugin_instances:
            plugin_instance = self.plugin_instances[plugin_name]
            if hasattr(plugin_instance, 'stop'):
                try:
                    plugin_instance.stop()
                    logger.info(f"Plugin {plugin_instance.name} desactivado correctamente.")
                except Exception as e:
                    logger.error(f"Error al detener el plugin {plugin_name}: {e}")
        else:
            logger.error(f"El plugin '{plugin_name}' no está cargado o no existe.")

    def is_plugin_active(self, plugin_name):
        """Devuelve el estado de activación del plugin."""
        return self.plugins_status.get(plugin_name, False)

plugin_manager=PluginManager()