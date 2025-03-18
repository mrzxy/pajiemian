import io
import re
import time
from helper import open_image_and_to_base64, deep_get, filter_nearest_less_equal
from logger import logger
from database import db
from dc import discord

pattern = re.compile(
    r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
    r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
    r"(.*)"  # 匹配内容
)


def to_lines(resp):
    pat = re.compile(
        r"(\w{1,25})\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
    )
    chars = resp.get("data").get("chars")
    line_data = []
    for charLine in chars:
        buffer = io.StringIO()
        for char in charLine:
            buffer.write(char.get("char"))

        new_y = charLine[0].get("y")

        append = False
        if len(line_data) > 0:
            last = line_data[len(line_data) - 1]
            if new_y - last["y"] > 8:
                append = True
            else:
                # ocr 可能 发送人 在后面
                new_char = buffer.getvalue()
                matches = pat.findall(new_char)
                if len(matches) > 0:
                    buffer.write(" ")
                    buffer.write(last["buff"].getvalue())
                    last["buff"] = buffer
                else:
                    last["buff"].write(" ")
                    last["buff"].write(new_char)
        else:
            append = True

        if append:
            line_data.append({
                "y": charLine[0].get("y"),
                "buff": buffer,
            })

    pattern2 = re.compile(
        r"(\w{1,25})\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
        r"(.*)"  # 匹配内容
    )

    collated_data = []
    for k, v in enumerate(line_data):
        content = v.get("buff").getvalue()
        matchers = pattern2.findall(content)
        if len(matchers) < 1:
            pre_idx = k- 1
            if pre_idx < 0 or len(collated_data) < 1:
                logger.info("孤儿语句{}".format(content))
                continue
            prev = collated_data[len(collated_data) - 1]
            prev.get("buff").write(content)
        else:
            collated_data.append(v)

    result_list = []
    for v in collated_data:
        matches = pattern.findall(v.get("buff").getvalue())
        print(v.get("y"), v.get("buff").getvalue())
        if len(matches) <= 0:
            logger.info("Opt.正则匹配失败,原句：{}".format(content))
            continue

        result_list.append(matches[0])
    return result_list


def match_result(resp):
    if resp.get("code") != 10000:
        logger.error("接口返回Code:{}, Message:{}".format(resp.get("code"), resp.get("message")))
        return

    collated_data = to_lines(resp)

    for v in collated_data:
        role, event, content = v

        role = role.replace(" ", "", -1).strip()
        content = content.strip()
        event = event.strip()

        message_id = f"{role}|{event}|{content}".replace(" ", "", -1)

        if not db.is_sent(message_id):
            logger.info(f"{role} 发送:{content}")
            # db.insert_send_history(message_id)
            # if discord.send_msg_by_webhook(role, content):
            #     db.in



def match_result2( resp):
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
                    logger.info("Q.坐标信息获取失败")
                    return

                text = question.get("Text").strip()
                chunk_list = text.split("\n")
                for chunk in chunk_list:
                    matches = pattern.findall(chunk)
                    if len(matches) > 0:
                        result_list.append({"content": matches[0], "offset_y": offset_y})
                    else:
                        logger.info("Q.正则匹配失败,原句：{}".format(chunk))

            for v3 in v2.get("Option"):
                offset_y = deep_get(v3, ["Coord", "LeftTop", "Y"], None)
                if offset_y is None:
                    logger.info("Opt.坐标信息获取失败")
                    return
                text = v3.get("Text").strip()
                matches = pattern.findall(text)
                if len(matches) > 0:
                    result_list.append({"content": matches[0], "offset_y": offset_y})
                else:
                    logger.info("Opt.正则匹配失败,原句：{}".format(text))

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
            # db.insert_send_history(message_id)
            # if discord.send_msg_by_webhook(role, content):
            #     db.insert_send_history(message_id)
