import logging
from logging.handlers import TimedRotatingFileHandler
import time
import os


def setup_logger():
    log_dir = "logs"
    log_file = "app.log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    days_to_keep = 15
    log_path = os.path.join(log_dir, log_file)
    # 配置 TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
        log_path, when="midnight", encoding="utf-8", interval=1, backupCount=15  # 每天轮转，保留 7 天日志
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

    clean_old_logs(log_dir, days_to_keep)

    return logger


def clean_old_logs(log_dir, days_to_keep):
    """
    删除超过指定天数的日志文件。

    参数:
        log_dir (str): 日志文件存储目录。
        days_to_keep (int): 保留日志文件的天数。
    """
    now = time.time()
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > days_to_keep * 86400:  # 86400 秒 = 1 天
                os.remove(file_path)
                print(f"已删除过期日志文件: {file_path}")


logger = setup_logger()
