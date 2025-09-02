import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("customlogger")
logger.setLevel(logging.INFO)
logger.propagate = True
