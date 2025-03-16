import base64

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