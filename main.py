import json
import time
import mss
from PIL import Image
import os
import ctypes
import sys
from AppKit import NSScreen
import re
from datetime import datetime
from database import DB
from dc import Discord
from helper import image_to_base64, open_image_and_to_base64, deep_get, filter_nearest_less_equal

from ocr_client import detect_text, mock_detect_text

from glom import glom


def get_dpi_scale():
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # 让 Python 进程感知 DPI
        dpi = user32.GetDpiForSystem()
        return dpi / 96.0  # 标准 DPI 为 96
    else:
        return 1.0


def capture_and_crop(region=None, save_path="screenshots"):
    """
    定期截图并裁剪。
    :param region: 截取区域 (left, top, width, height)，默认全屏
    :param interval: 截图间隔（秒）
    :param count: 截图次数
    :param save_path: 图片保存路径
    """
    os.makedirs(save_path, exist_ok=True)

    with mss.mss() as sct:
        monitor = sct.monitors[1] if region is None else {"left": region[0], "top": region[1], "width": region[2],
                                                          "height": region[3]}

        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        if region:
            img = img.crop((0, 0, region[2], region[3]))  # 裁剪

        now = datetime.now()
        filename = os.path.join(save_path, "screenshot_{}.png".format(now.strftime("%Y%m%d_%H%M%S")))
        img.save(filename)
        print(f"Saved: {filename}")
        return filename
    return None


def match_result(resp):
    pattern = re.compile(
        r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}:\d{2}\s?[AP]M)\s"  # 匹配事件时间
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
                        print("图片坐标信息获取失败")
                        continue
                    pic_offset_list.append(offset_y)
            for question in v2.get("Question"):
                offset_y = deep_get(question, ["Coord", "LeftTop", "Y"], None)
                if offset_y is None:
                    print("1.坐标信息获取失败")
                    return

                text = question.get("Text").strip()
                chunk_list = text.split("\n")
                for chunk in chunk_list:
                    matches = pattern.findall(chunk)
                    if len(matches) > 0:
                        result_list.append({"content": matches[0], "offset_y": offset_y})
                    else:
                        print("1.正则匹配失败,原句：{}".format(chunk))

            for v3 in v2.get("Option"):
                offset_y = deep_get(v3, ["Coord", "LeftTop", "Y"], None)
                if offset_y is None:
                    print("1.坐标信息获取失败")
                    return
                text = v3.get("Text").strip()
                matches = pattern.findall(text)
                if len(matches) > 0:
                    result_list.append({"content": matches[0], "offset_y": offset_y})
                else:
                    print("2.正则匹配失败,原句：{}".format(text))

    print(pic_offset_list)
    if len(result_list) == 0:
        print("没有匹配到结果")
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

        print(f"{role} 发送:{content}")
        if not db.is_sent(message_id):
            if discord.send_msg_by_webhook(role, content):
                db.insert_send_history(message_id)


def main():
    scale = NSScreen.mainScreen().backingScaleFactor()
    scale_factor = get_dpi_scale()
    scaled_region = (
        int(314 * scale_factor),  # left
        int(158 * scale_factor),  # top
        int(1150 * scale * scale_factor),  # width
        int(680 * scale * scale_factor)  # height
    )
    scaled_region = None
    img_file = capture_and_crop(region=scaled_region)
    if img_file is None:
        print("截图失败")
        return

    return

    # resp = detect_text(open_image_and_to_base64(img_file))
    resp = mock_detect_text("simplty.json")
    if resp is None:
        print("OCR failed")
        return
    match_result(resp)


if __name__ == "__main__":
    db = DB()
    discord = Discord()
    interval = 1
    # img_file = "/Users/zxy/Project/xianyu/capture/screenshots/large_text.png"
    # resp = detect_text(open_image_and_to_base64(img_file))
    # with open(os.path.join("case", "large_text.json"), "w") as f:
    #     f.write(resp.to_json_string())
    # capture_and_crop(region=(100, 100, 500, 400), interval=2, count=5)
    # capture_and_crop(region=None, interval=1, count=1)

# while True:
#     try:
#         main()
#     except Exception as e:
#         print(e)
#     finally:
#         time.sleep(interval)
    main()

# capture_and_crop(region=scaled_region, interval=1, count=1)
