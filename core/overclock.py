

from core.logger import setup_logger
logger = setup_logger(__name__)


# Parámetros de overclock a verificar
overclock_keywords = [
    'arm_freq',
    'over_voltage',
    'core_freq',
    'sdram_freq',
    'over_voltage_sdram',
    'force_turbo',
    'boot_delay'
]

# Definir configuraciones de overclock (de menor a mayor)
overclock_profiles = {
    'no_overclock': None,  # Esto eliminará las configuraciones de overclock
    'LOWER': {
        'arm_freq': '900',
        'over_voltage': '2',
        'core_freq': '400',
        'sdram_freq': '400',
        'over_voltage_sdram': '1'
    },
    'MEDIUM': {
        'arm_freq': '1000',
        'over_voltage': '3',
        'core_freq': '450',
        'sdram_freq': '450',
        'over_voltage_sdram': '2'
    },
    'HIGH': {
        'arm_freq': '1100',
        'over_voltage': '5',
        'core_freq': '500',
        'sdram_freq': '500',
        'over_voltage_sdram': '2'
    },
    'MAXIMUM': {
        'arm_freq': '1100',
        'over_voltage': '8',
        'core_freq': '500',
        'sdram_freq': '500',
        'over_voltage_sdram': '2',
        'force_turbo': '1',
        'boot_delay': '1'
    }
}

def check_overclock(file_path='/boot/config.txt'):
    """
    Verifica y devuelve el tipo de configuración de overclock en el archivo config.txt.
    Si no coincide con ningún perfil definido, devuelve "CUSTOM".
    """
    try:
        with open(file_path, 'r') as file:
            config_lines = file.readlines()

        # Leer las configuraciones de overclock actuales
        current_config = {}
        for line in config_lines:
            line = line.strip()
            for keyword in overclock_keywords:
                if line.startswith(keyword):
                    key, value = line.split('=')
                    current_config[key.strip()] = value.strip()

        # Comparar con los perfiles definidos
        for profile, config in overclock_profiles.items():
            if config is None:
                # 'no_overclock' no tiene ninguna configuración, verificar si el archivo no tiene overclock
                if not current_config:
                    return 'NOT OVERCLOCK'
            elif current_config == config:
                return profile
        
        # Si no coincide con ningún perfil, es un "CUSTOM" overclock
        return 'CUSTOM'

    except FileNotFoundError:
        logger.error(f"Error: El archivo {file_path} no fue encontrado.")
        return None


def apply_overclock(file_path='/boot/config.txt', profile='no_overclock'):
    """
    Aplica una configuración de overclock al archivo config.txt.
    Si se selecciona 'no_overclock', elimina las configuraciones de overclock.
    """
    if profile not in overclock_profiles:
        logger.error(f"Error: El perfil de overclock '{profile}' no es válido.")
        return False

    config = overclock_profiles[profile]
    
    try:
        with open(file_path, 'r') as file:
            config_lines = file.readlines()

        if profile == 'no_overclock':
            # Si el perfil es 'no_overclock', eliminamos las configuraciones de overclock
            config_lines = [line for line in config_lines if not any(keyword in line for keyword in overclock_keywords)]
        else:
            # Si el perfil no es 'no_overclock', agregamos la configuración correspondiente
            # Primero, eliminamos las configuraciones previas (si existen)
            config_lines = [line for line in config_lines if not any(keyword in line for keyword in overclock_keywords)]
            # Luego, agregamos las nuevas configuraciones
            for key, value in config.items():
                config_lines.append(f"{key}={value}\n")
        
        # Escribimos las configuraciones actualizadas al archivo
        with open(file_path, 'w') as file:
            file.writelines(config_lines)
        
        logger.info(f"Configuración de overclock '{profile}' aplicada correctamente.")
        return True

    except FileNotFoundError:
        logger.error(f"Error: El archivo {file_path} no fue encontrado.")
        return False
