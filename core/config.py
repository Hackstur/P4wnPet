import json
import os
# Configurar el logger
from core.logger import LoggerSingleton
logger = LoggerSingleton().get_logger(__name__)

class ConfigCategory:

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigCategory(**value))
            #elif isinstance(value, Network):
            #    setattr(self, key, value)  
            else:
                setattr(self, key, value)

    def to_dict(self):
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
        logger.info("Inicializando AppConfig con configuraciones predeterminadas.")
        self.data = ConfigCategory(
            
            hid={
                'type_speed'    : (50,20),
                'keymap'        : 'es',
                'vid'           : 'vidcode',
                'pid'           : 'pid',
                'mouse_steps'   : 100,
            },
            wifi={
                'nic'           : 'wlan0',
                'target_essid'  : None,
                'target_bssid'  : None,
                'signal'        : 0

            }
        )

        # Cargar configuración desde archivo, si se proporciona
        if config_file:
            logger.info(f"Cargando configuración desde {config_file}.")
            self.load_from_file(config_file)

    def load_from_file(self, file_path):
        if not os.path.exists(file_path):
            logger.warning(f"El archivo {file_path} no existe.")
            return

        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Actualiza dinámicamente la configuración
        self._update_from_dict(self.data, data)
        logger.info("Configuración cargada y actualizada desde el archivo.")

    def save_to_file(self, file_path):
        with open(file_path, "w") as f:
            json.dump(self.data.to_dict(), f, indent=4)
        logger.info(f"Configuración guardada en {file_path}.")

    def _update_from_dict(self, obj, data):
        for key, value in data.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                if isinstance(attr, ConfigCategory) and isinstance(value, dict):
                    self._update_from_dict(attr, value)
                else:
                    # Convertir listas a tuplas si es necesario
                    if isinstance(value, list) and isinstance(attr, tuple):
                        value = tuple(value)
                    setattr(obj, key, value)
                    logger.info(f"Configuración actualizada: {key} = {value}")

    def __repr__(self):
        return json.dumps(self.data.to_dict(), indent=4)

    def update_config(self, **kwargs):
        self._update_from_dict(self.data, kwargs)

config=AppConfig("config/p4wnpet.json")
