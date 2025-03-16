import base64
from datetime import datetime

import mss
from PIL import Image
import os
import ctypes
import sys


def open_image_and_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return image_to_base64(img_file)


def image_to_base64(img_file):
    return base64.b64encode(img_file.read()).decode("utf-8")


def deep_get(d, keys, default=None):
    """ 使用递归方式获取嵌套字典中的值 """
    if not keys:
        return d
    if not isinstance(d, dict):
        return default
    return deep_get(d.get(keys[0], default), keys[1:], default)


def filter_nearest_less_equal(data, m):
    for offset in m:
        # 从后向前遍历
        for i in range(len(data) - 1, -1, -1):
            offset_y = data[i].get("offset_y", 0)
            if offset_y < offset:
                print("发现一张图片，所以过滤 {}".format(data[i].get("content")))
                data.pop(i)
                break
    return data


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
        filename = os.path.join(save_path, "screenshot_{}.pdf".format(now.strftime("%Y%m%d_%H%M%S")))
        img.save(filename, "PDF", resolution=100.0)
        print(f"Saved: {filename}")
        return filename
    return None


def corp_image(image_path, region, save_path="screenshots"):
    with Image.open(image_path) as img:
        img = img.crop((region[0], region[1], region[2], region[3]))  # 裁剪
        now = datetime.now()
        filename = os.path.join(save_path, "corp_{}.png".format(now.strftime("%Y%m%d_%H%M%S")))
        img.save(filename)
        print(f"Saved: {filename}")
        return filename
