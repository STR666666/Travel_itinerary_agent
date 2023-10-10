from loguru import logger

DEBUG = True
def log_info(info, debug=DEBUG):
    if debug:
        logger.debug(info)