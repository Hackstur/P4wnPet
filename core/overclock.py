

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
    try:
        with open(file_path, 'r') as file:
            config_lines = file.readlines()

        current_config = {}
        for line in config_lines:
            line = line.strip()
            for keyword in overclock_keywords:
                if line.startswith(keyword):
                    key, value = line.split('=')
                    current_config[key.strip()] = value.strip()

        for index, (profile, config) in enumerate(overclock_profiles.items()):
            if config is None:
                if not current_config:
                    return index  # Retorna el índice de 'no_overclock'
            elif current_config == config:
                return index  # Retorna el índice del perfil correspondiente
        return 0  # Indica que es un perfil 'CUSTOM' o no reconocido

    except FileNotFoundError:
        logger.error(f"Error: El archivo {file_path} no fue encontrado.")
        return None


def apply_overclock(file_path='/boot/config.txt', profile='no_overclock'):
    if profile not in overclock_profiles:
        logger.error(f"Error: El perfil de overclock '{profile}' no es válido.")
        return False

    config = overclock_profiles[profile]
    
    try:
        with open(file_path, 'r') as file:
            config_lines = file.readlines()

        if profile == 'no_overclock':
            config_lines = [line for line in config_lines if not any(keyword in line for keyword in overclock_keywords)]
        else:
            config_lines = [line for line in config_lines if not any(keyword in line for keyword in overclock_keywords)]
            for key, value in config.items():
                config_lines.append(f"{key}={value}\n")
        
        with open(file_path, 'w') as file:
            file.writelines(config_lines)
        
        logger.info(f"Configuración de overclock '{profile}' aplicada correctamente.")
        return True

    except FileNotFoundError:
        logger.error(f"Error: El archivo {file_path} no fue encontrado.")
        return False
