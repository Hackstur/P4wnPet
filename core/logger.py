import logging
import os
from logging.handlers import RotatingFileHandler

class LoggerSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LoggerSingleton, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._loggers = {}

    def _setup_logger(self, name):
        log_dir = "logs"
        log_level = logging.INFO
        max_size = 5 * 1024 * 1024
        backup_count = 5
        to_console = True
        log_format = '%(levelname)-8s %(asctime)-6s %(name)-20s: %(message)s'
        datefmt = '%H:%M'

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, f"{name}.log")

        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        if not logger.hasHandlers():
            formatter = logging.Formatter(log_format, datefmt=datefmt)

            handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            if to_console:
                color_formatter = ColoredFormatter(log_format, datefmt=datefmt)
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(color_formatter)
                logger.addHandler(console_handler)

        return logger

    def get_logger(self, name):
        if name not in self._loggers:
            self._loggers[name] = self._setup_logger(name)
        return self._loggers[name]

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Azul
        'INFO': '\033[92m',     # Verde
        'WARNING': '\033[93m',  # Amarillo
        'ERROR': '\033[91m',    # Rojo
        'CRITICAL': '\033[1;91m' # Rojo brillante
    }
    RESET = '\033[0m'

    LEVELNAME_MAP = {
        'INFO': 'INFO ',
        'WARNING': 'WARN ',
        'ERROR': 'ERROR',
        'DEBUG': 'DEBUG',
        'CRITICAL': 'CRIT '
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        levelname = self.LEVELNAME_MAP.get(record.levelname, record.levelname)
        record.levelname = f"{log_color}{levelname}{self.RESET}"
        return super().format(record)
