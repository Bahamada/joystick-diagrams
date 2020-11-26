import os
import typing
import webbrowser
from time import time

import config
import version
import logging

# Logging Init
logDir = './logs/'
logFile = 'jv.log'
logger = logging.getLogger('jv')
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(config.chrome_path))


def create_directory(directory: str) -> bool:
    if not os.path.exists(directory):
        os.makedirs(directory)
        return True
    else:
        log("Failed to create directory: {}".format(directory), 'error')
        return False


def log(text: str, level: str = 'info') -> None:
    # Accepted Levels
    # info, warning, error
    if config.debug:
        if level == 'info':
            logger.info(text)
        elif level == 'warning':
            logger.warning(text)
        elif level == 'error':
            logger.error(text)
        else:
            logger.debug(text)


def print_timing(func: typing.Callable) -> typing.Callable:
    def wrapped(*args, **kwargs):
        time_start = time()
        result = func(*args, **kwargs)
        time_end = time()
        print(f"{func.__name__}  {(time_end - time_start) * 1000} ms")
        return result

    return wrapped


def get_version() -> str:
    return "Version: " + version.VERSION


if not os.path.exists(logDir):
    dir_created = create_directory(logDir)
    assert dir_created
handler = logging.FileHandler(logDir + logFile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
if config.debugLevel == 1:
    logger.setLevel(logging.WARNING)
elif config.debugLevel == 2:
    logger.setLevel(logging.ERROR)
elif config.debugLevel == 3:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)
