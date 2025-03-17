import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    log_file = "app.log"

    # 配置 TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=15  # 每天轮转，保留 7 天日志
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # 配置日志
    logger = logging.getLogger("my_app")
    logger.setLevel(logging.INFO)
    log_file = "app.log"

    logger.addHandler(handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()