import logging
import sys
import time
import os
from sympy.strategies.core import switch

from config import conf
from logger import logger
from helper import get_dpi_scale, capture_and_crop, open_image_and_to_base64
from matcher import match_result
from ocr_client import  mock_detect_text, detect_text


def main():
    logger.info("开始截屏")
    scale = 1
    scale_factor = get_dpi_scale()
    scaled_region = (
        int(0 * scale_factor),  # left
        int(172 * scale_factor),  # top
        int(1075 * scale * scale_factor),  # width
        int(857 * scale * scale_factor)  # height
    )
    img_file = capture_and_crop(region=scaled_region)
    if img_file is None:
        logger.info("截图失败")
        return


    resp = detect_text(open_image_and_to_base64(img_file))
    # resp = mock_detect_text("debug1.json")
    if resp is None:
        logger.info("OCR failed")
        return
    match_result(resp)

def debug():
    logger.setLevel(logging.DEBUG)
    for root, dirs, files in os.walk("case/debug"):
        for file in files:
            if file == "debug8.json":
                resp = mock_detect_text(file)
                match_result(resp)

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) > 1 and argv[1] == "debug":
        debug()
    else:
        while True:
            try:
                main()
            except Exception as e:
                logger.error(e)
            finally:
                time.sleep(conf["interval"])