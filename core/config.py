import json
import os
# Configurar el logger
from core.logger import setup_logger
logger = setup_logger(__name__)

class ConfigCategory:

    def __init__(self, **kwargs):
        
        """Inicializa dinámicamente los atributos a partir de los valores pasados."""
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigCategory(**value))
            #elif isinstance(value, Network):
            #    setattr(self, key, value)  
            else:
                setattr(self, key, value)

    def to_dict(self):

        """Convierte la categoría de configuración en un diccionario."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConfigCategory):
                result[key] = value.to_dict()
            #elif isinstance(value, Network):
            #    result[key] = value.to_dict() 
            else:
                result[key] = value
        return result

class AppConfig:
    def __init__(self, config_file=None):
        """Inicializa con configuraciones genéricas."""
        logger.info("Inicializando AppConfig con configuraciones predeterminadas.")
        self.data = ConfigCategory(
           
            hid={
                'type_speed'    : "(100,50)",
                'keymap'        : 'ES',
                'vid'           : 'vidcode',
                'pid'           : 'pid',
                'mouse_steps'   : 100,
            }
        )

        # Cargar configuración desde archivo, si se proporciona
        if config_file:
            logger.info(f"Cargando configuración desde {config_file}.")
            self.load_from_file(config_file)

    def load_from_file(self, file_path):
        """Cargar la configuración desde un archivo JSON."""
        if not os.path.exists(file_path):
            logger.warning(f"El archivo {file_path} no existe.")
            return

        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Actualiza dinámicamente la configuración
        self._update_from_dict(self.data, data)
        logger.info("Configuración cargada y actualizada desde el archivo.")

    def save_to_file(self, file_path):
        """Guardar la configuración actual en un archivo JSON."""
        with open(file_path, "w") as f:
            json.dump(self.data.to_dict(), f, indent=4)
        logger.info(f"Configuración guardada en {file_path}.")

    def _update_from_dict(self, obj, data):
        """Actualiza dinámicamente un objeto de configuración a partir de un diccionario."""
        for key, value in data.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                if isinstance(attr, ConfigCategory) and isinstance(value, dict):
                    self._update_from_dict(attr, value)
                else:
                    setattr(obj, key, value)
                    logger.info(f"Configuración actualizada: {key} = {value}")

    def __repr__(self):
        return json.dumps(self.data.to_dict(), indent=4)

    def update_config(self, **kwargs):
        """Permite actualizar la configuración programáticamente."""
        logger.info("Actualizando configuración programáticamente.")
        self._update_from_dict(self.data, kwargs)

config=AppConfig("config/p4wnpet.json")

"""
# Ejemplo de uso
if __name__ == "__main__":
    config = AppConfig()

    # Acceder a los valores de configuración de subcategorías
    logger.info(f"Configuración inicial de WiFi: {config.data.wifi.target}")  # None
    logger.info(f"Configuración inicial de la base de datos: {config.data.database.url}")  # localhost:5432

    # Actualizar un valor de una subcategoría
    config.data.wifi.target = "00:11:22:33:44:55"
    config.data.database.url = "localhost:3306"

    # Guardar la configuración en un archivo
    config.save_to_file("config.json")

    # Cargar la configuración desde un archivo
    config.load_from_file("config.json")

    # Ver la configuración actual
    logger.info(f"Configuración actual: {config}")
"""