import time
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
        int(674 * scale * scale_factor)  # height
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


if __name__ == "__main__":
    interval = 5
    # img_file = "/Users/zxy/Project/xianyu/capture/screenshots/5-1.png"
    # resp = mock_detect_text("debug7.json")
    # match_result(resp)
    # main()
    while True:
        try:
            main()
        except Exception as e:
            logger.error(e)
        finally:
            time.sleep(interval)

# capture_and_crop(region=scaled_region, interval=1, count=1)
