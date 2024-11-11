import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_dir="logs", log_level=logging.INFO, max_size=5 * 1024 * 1024, backup_count=5, to_console=True):
    """
    Configura un logger con rotación de archivos.
    
    Args:
        name (str): Nombre del logger, generalmente el nombre del módulo o archivo.
        log_dir (str): Directorio donde se almacenan los archivos de log.
        log_level (int): Nivel de logging (e.g., logging.INFO, logging.DEBUG).
        max_size (int): Tamaño máximo del archivo de log antes de que ocurra la rotación.
        backup_count (int): Número de archivos de respaldo a mantener después de la rotación.

    Returns:
        logger (logging.Logger): Instancia configurada de un logger.
    """
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{name}.log")

    # Configuración básica del logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Evitar duplicar handlers si se llama varias veces
    if not logger.hasHandlers():
        # Formato de los logs
        formatter = logging.Formatter(' %(levelname)s - %(name)s - %(message)s')
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #formatter= logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s')

        # Crear manejador con rotación de logs
        handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count)
        handler.setFormatter(formatter)

        # Agregar el handler al logger
        logger.addHandler(handler)

        console_handler = logging.StreamHandler()  # Handler para imprimir en la consola
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
