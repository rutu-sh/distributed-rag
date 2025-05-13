# default libraries
import logging.config
import os 
import logging 

# installed libraries
import structlog

# custom libraries
import common.config as config


StreamHandler = logging.StreamHandler(stream=os.sys.stdout)
# FileHandler = logging.FileHandler(config.LOG_FILE_PATH)

def get_logger(name: str, bind_params: dict = None, handlers: list = None) -> structlog.BoundLogger:
    """
    Configures and returns a structlog logger. 
    :param name: Name of the logger
    :param bind_params: Extra parameters to bind to the logger. Example: {"param1": "value1", "param2": "value2"}. Default: None
    :param handlers: List of handlers to add to the logger. Example: [logging.StreamHandler(), logging.FileHandler("log.txt")]. Default: StreamHandler
    """
    if not handlers:
        handlers = [logging.StreamHandler(stream=os.sys.stdout)]
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt=config.LOG_TIME_FORMAT),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        
    )
    logger = structlog.get_logger(name)
    logger.setLevel(config.LOG_LEVEL)
    if bind_params:
        logger = logger.bind(**bind_params)
    for handler in handlers:
        logger.addHandler(handler)
    return logger
