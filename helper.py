import base64
import shutil
import time
from datetime import datetime, timedelta
import sounddevice as sd

import mss
from PIL import Image
import os
import ctypes
import sys
from logger import logger


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
                logger.info("发现一张图片，所以过滤 {}".format(data[i].get("content")))
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

def create_date_folder(base_dir):
    """
    创建一个按当前日期命名的文件夹。

    参数:
        base_dir (str): 基础目录，日期文件夹将创建在该目录下。

    返回:
        str: 创建的文件夹路径。
    """
    # 获取当前日期
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")  # 格式化为 YYYY-MM-DD

    # 创建日期文件夹
    date_folder = os.path.join(base_dir, date_str)
    os.makedirs(date_folder, exist_ok=True)

    return date_folder

def delete_old_folders(base_dir, days_to_keep=5):
    """
    删除超过指定天数的旧文件夹。

    参数:
        base_dir (str): 基础目录，检查该目录下的文件夹。
        days_to_keep (int): 保留文件夹的天数。
    """
    # 获取当前时间
    now = datetime.now()

    # 遍历基础目录下的所有文件夹
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.isdir(folder_path):
            try:
                # 解析文件夹名称中的日期
                folder_date = datetime.strptime(folder_name, "%Y-%m-%d")
                # 计算文件夹的年龄
                folder_age = now - folder_date
                # 如果文件夹超过指定天数，则删除
                if folder_age > timedelta(days=days_to_keep):
                    shutil.rmtree(folder_path)
                    print(f"已删除过期文件夹: {folder_path}")
            except ValueError:
                # 如果文件夹名称不是日期格式，则跳过
                continue

del_flag = 0

def capture_and_crop(region=None, save_path="screenshots"):
    """
    定期截图并裁剪。
    :param region: 截取区域 (left, top, width, height)，默认全屏
    :param interval: 截图间隔（秒）
    :param count: 截图次数
    :param save_path: 图片保存路径
    """
    save_path = create_date_folder(save_path)
    global del_flag
    if del_flag != datetime.now().hour:
        print("开始删除过期文件夹")
        delete_old_folders(save_path)
        del_flag = datetime.now().hour

    with mss.mss() as sct:
        monitor = sct.monitors[1] if region is None else {"left": region[0], "top": region[1], "width": region[2],
                                                          "height": region[3]}

        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        if region:
            img = img.crop((0, 0, region[2], region[3]))  # 裁剪

        now = datetime.now()
        # filename = os.path.join(save_path, "screenshot_{}.pdf".format(now.strftime("%Y%m%d_%H%M%S")))
        # img.save(filename, "PDF", resolution=100.0)
        filename = os.path.join(save_path, "screenshot_{}.png".format(now.strftime("%Y%m%d_%H%M%S")))

        img.save(filename)
        logger.info(f"Saved: {filename}")
        return filename
    return None


def corp_image(image_path, region, save_path="screenshots"):
    with Image.open(image_path) as img:
        img = img.crop((region[0], region[1], region[2], region[3]))  # 裁剪
        now = datetime.now()
        filename = os.path.join(save_path, "corp_{}.png".format(now.strftime("%Y%m%d_%H%M%S")))
        img.save(filename)
        logger.info(f"Saved: {filename}")
        return filename


def find_device_by_name(name, partial_match=True):
    """按名称查找设备"""
    for i, device in enumerate(sd.query_devices()):
        if (partial_match and name in device['name']) or \
                (not partial_match and name == device['name']):
            return {'index': i, 'device': device}
    return None
if __name__ == "__main__":
    capture_and_crop(None)
