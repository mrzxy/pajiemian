import io
import re
import time
from helper import open_image_and_to_base64, deep_get, filter_nearest_less_equal
from logger import logger
from database import db
from dc import discord
from trie import replace_keywords

pattern = re.compile(
    r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
    r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
    r"(.*)"  # 匹配内容
)


def to_lines(resp):
    pat = re.compile(
        r"(\w{1,25})\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间

    )
    chars = resp.get("data").get("chars")
    line_data = []
    for charLine in chars:
        buffer = io.StringIO()
        for char in charLine:
            buffer.write(char.get("char"))

        new_y = charLine[0].get("y")
        new_x = charLine[0].get("x")
        # print("x:{}, {}".format(new_x, buffer.getvalue()))

        append = False
        test = False
        if len(line_data) > 0:
            last = line_data[len(line_data) - 1]
            if new_y - last["y"] > 8:
                append = True
            else:
                # ocr 可能 发送人 在后面
                # x > 500 可能是 日期提示(Mar 17, 2025)
                if new_x < 500:
                    new_char = buffer.getvalue()
                    last['buffer']. append({"x": new_x, "char": new_char})
        else:
            append = True

        if append:
            line_data.append({
                "y": charLine[0].get("y"),
                "buffer": [
                    {
                        "x": new_x,
                        "char": buffer.getvalue(),
                    }
                ],
            })

    pattern2 = re.compile(
        r"(\w{1,25})\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
        r"(.*)"  # 匹配内容
    )

    collated_data = []
    for k, v in enumerate(line_data):
        sorted_arr = sorted(v["buffer"], key=lambda item: item["x"])
        buffer = io.StringIO()
        for c in sorted_arr:
            buffer.write(c.get("char"))


        content = buffer.getvalue()

        matchers = pattern2.findall(content)
        if len(matchers) < 1:
            pre_idx = k- 1
            if pre_idx < 0 or len(collated_data) < 1:
                logger.info("孤儿语句{}".format(content))
                continue
            prev = collated_data[len(collated_data) - 1]
            prev.get("buff").write(content)
        else:
            collated_data.append({
                "buff": buffer,
            })

    result_list = []
    for v in collated_data:
        content = v.get("buff").getvalue()
        matches = pattern.findall(content)
        if len(matches) < 1:
            logger.error("Opt.正则匹配失败,原句：{}".format(content))
            continue

        result_list.append(matches[0])
    return result_list


def match_result(collated_data, debug=False):
    if collated_data is None or len(collated_data) == 0:
        return True
    for v in collated_data:
        role, event, content = v
        content = replace_keywords(content)

        role = role.replace(" ", "", -1).strip()
        content = content.strip()
        event = event.strip()

        message_id = f"{role}|{event}|{content}".replace(" ", "", -1)

        if debug:
            logger.info(f"{role} 发送:{content}")
        else:
            if not db.is_sent(message_id):
                logger.info(f"{role} 发送:{content}")
                if discord.send_msg_by_webhook(role, content):
                    db.insert_send_history(message_id)
                    time.sleep(1)

    return True
