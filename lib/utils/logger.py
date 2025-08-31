import logging
import sys
import os

from typing import Union, Literal


LogLevel = Union[Literal[10, 20, 30, 40, 50], int]

def enable_default_logger(
    level: LogLevel = logging.INFO,
    directory: str = None,
    name: str = None,
    reinit: bool = True
):
    """Set the default logger handler for the package.

    Will set the root handlers to empty list, prevent duplicate handlers added
    by other packages causing duplicate logging messages.
    """
    logger = logging.getLogger(name or __name__)
    
    if any(not isinstance(handler, logging.NullHandler)
           for handler in logger.handlers):
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)5s] %(message)s',
                                  datefmt='%H:%M:%S')

    if directory:
        if os.path.exists(directory) and reinit:
            os.rmdir(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_handler = logging.FileHandler(os.path.join(directory, 'logging.log'), encoding='utf8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


class LogWithCacheWrapper:
    def __init__(self, logger):
        self.logger = logger
        self.cache = []

    def _cache_message(self, level, message):
        self.cache.append({'level':level, 'details':message})

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
        self._cache_message('INFO', message)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
        self._cache_message('ERROR', message)

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)
        self._cache_message('WARNING', message)

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
        self._cache_message('DEBUG', message)

    def get_cached_logs(self):
        return self.cache
 