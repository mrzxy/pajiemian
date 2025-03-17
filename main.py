
import re
import time
from datetime import datetime
from database import DB
from dc import Discord
from logger import logger
from helper import open_image_and_to_base64, deep_get, filter_nearest_less_equal, get_dpi_scale, \
    capture_and_crop

from ocr_client import detect_text, mock_detect_text

def match_result(resp):

    pattern = re.compile(
        r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
        r"(.*)"  # 匹配内容
    )

    result_list = []
    pic_offset_list = []
    for v in resp.get("QuestionInfo"):
        for v2 in v.get("ResultList"):
            figure = v2.get("Figure", [])
            if len(figure) > 0:
                for f in figure:
                    offset_y = deep_get(f, ["Coord", "LeftTop", "Y"], None)
                    if offset_y is None:
                        logger.info("图片坐标信息获取失败")
                        continue
                    pic_offset_list.append(offset_y)
            for question in v2.get("Question"):
                offset_y = deep_get(question, ["Coord", "LeftTop", "Y"], None)
                if offset_y is None:
                    logger.info("1.坐标信息获取失败")
                    return

                text = question.get("Text").strip()
                chunk_list = text.split("\n")
                for chunk in chunk_list:
                    matches = pattern.findall(chunk)
                    if len(matches) > 0:
                        result_list.append({"content": matches[0], "offset_y": offset_y})
                    else:
                        logger.info("1.正则匹配失败,原句：{}".format(chunk))

            for v3 in v2.get("Option"):
                offset_y = deep_get(v3, ["Coord", "LeftTop", "Y"], None)
                if offset_y is None:
                    logger.info("1.坐标信息获取失败")
                    return
                text = v3.get("Text").strip()
                matches = pattern.findall(text)
                if len(matches) > 0:
                    result_list.append({"content": matches[0], "offset_y": offset_y})
                else:
                    logger.info("2.正则匹配失败,原句：{}".format(text))

    logger.info(pic_offset_list)
    if len(result_list) == 0:
        logger.info("没有匹配到结果")
        return

    # 使用offset_y排序
    result_list = sorted(result_list, key=lambda x: x.get("offset_y"))
    result_list = filter_nearest_less_equal(result_list, pic_offset_list)

    for v in result_list:

        role, event, content = v.get("content")

        role = role.replace(" ", "", -1).strip()
        content = content.strip()
        event = event.strip()

        message_id = f"{role}|{event}|{content}".replace(" ", "", -1)

        if not db.is_sent(message_id):
            logger.info(f"{role} 发送:{content}")
            db.insert_send_history(message_id)
            # if discord.send_msg_by_webhook(role, content):
            #     db.insert_send_history(message_id)


def main():
    logger.info(datetime.now().strftime("%H:%M:%S") + "-开始截屏")
    # scale = NSScreen.mainScreen().backingScaleFactor()
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
    db = DB()
    discord = Discord()
    interval = 5
    # resp = detect_text(open_image_and_to_base64(img_file))
    # with open(os.path.join("case", "large_text.json"), "w") as f:
    #     f.write(resp.to_json_string())
    # capture_and_crop(region=(100, 100, 500, 400), interval=2, count=5)
    # capture_and_crop(region=None, interval=1, count=1)

    while True:
        try:
            main()
        except Exception as e:
            logger.error(e)
        finally:
            time.sleep(interval)

# capture_and_crop(region=scaled_region, interval=1, count=1)
