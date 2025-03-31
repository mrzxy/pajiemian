import asyncio
import logging
import sys
import threading
import time
import os
from datetime import datetime
from config import conf
from database import db
from google_ocr import extract_text_from_image
from image_hash import calculate_image_hash
from logger import logger
from helper import get_dpi_scale, capture_and_crop, open_image_and_to_base64
from matcher import match_result, to_lines
from ocr_client import  mock_detect_text, detect_text
from collections import defaultdict

from sound import monitor_audio

daily_counter = defaultdict(int)

def task():
    event_date = datetime.now().strftime("%Y-%m-%d")
    logger.info("开始截屏, 累计调用OCR次数: {}".format(daily_counter.get(event_date)))
    scale = 1
    scale_factor = get_dpi_scale()
    scaled_region = (
        int(0 * scale_factor),  # left
        int(172 * scale_factor),  # top
        int(1102 * scale * scale_factor),  # width
        int(857 * scale * scale_factor)  # height
    )
    img_file = capture_and_crop(region=scaled_region)
    if img_file is None:
        logger.info("截图失败")
        return

    file_hash = calculate_image_hash(img_file)
    if db.is_processed_image(file_hash):
        print("图片已处理过")
        return

    daily_counter[event_date] += 1

    resp = match_result(extract_text_from_image(img_file))
    # resp = detect_text(open_image_and_to_base64(img_file))
    # resp = mock_detect_text("debug1.json")
    if resp is None:
        logger.info("OCR failed")
        return
    if resp:
        db.insert_processed_image(file_hash)

def debug():
    r1 = calculate_image_hash("screenshots/r1.png")
    print(f"r1: {r1}")
    r2 = calculate_image_hash("screenshots/r2.png")
    print(f"r1: {r2}")
    r3 = calculate_image_hash("screenshots/r3.png")
    print(f"r1: {r3}")
    logger.setLevel(logging.DEBUG)
    for root, dirs, files in os.walk("case/debug"):
        for file in files:
            if file == "debug8.json":
                resp = mock_detect_text(file)
                if resp.get("code") != 10000:
                    logger.error("接口返回Code:{}, Message:{}".format(resp.get("code"), resp.get("message")))
                    return False

                collated_data = to_lines(resp)
                match_result(collated_data, True)

def main():
    print("开始抓取")
    while True:
        try:
            task()
        except Exception as e:
            logger.error(e)
        finally:
            time.sleep(conf["interval"])

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) > 1 and argv[1] == "debug":
        debug()
    else:
        thread1 = None
        if len(argv) > 1 and argv[1] == "sound":
            thread1 = threading.Thread(target=asyncio.run, args=(monitor_audio(),))
            thread1.start()
        thread2 = threading.Thread(target=main)
        thread2.start()

        thread2.join()
        if thread1 is not None:
            thread1.join()
        print("程序 end")

