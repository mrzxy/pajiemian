import json
import logging

from logger import logger
import re
import os
from google.cloud import vision
from google.cloud.vision_v1 import types


def extract_text_from_image(image_path, debug=""):
    """
    使用 Google Vision API 从图片中提取文字
    :param image_path: 图片文件路径
    :return: 识别出的文本
    """
    # 设置 Google Cloud 认证 JSON 文件路径
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gkey.json'

    # 初始化客户端
    client = vision.ImageAnnotatorClient()

    # 读取图片文件
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # 调用 API 进行文本检测
    response = client.text_detection(image=image)

    if response.error.message:
        print(f'API Error: {response.error.message}')
        return None

    if not response.text_annotations:
        print("未检测到文本")
        return None

    # 将结果保存到 JSON 文件
    if debug != "":
        response_json = vision.AnnotateImageResponse.to_json(response)
        with open("case/" + debug + ".json", 'w', encoding='utf-8') as json_file:
            json.dump(json.loads(response_json), json_file, ensure_ascii=False, indent=4)

    return match_text(response)


pattern2 = re.compile(
    r"(\w{1,25})\s?"  # 匹配角色名（兼容空格）
    r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
    r"(.*)"  # 匹配内容
)

date_pattern = r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*,?\s*\d{4}$"

def match_text(response):
    full_text_annotation = response.full_text_annotation
    pages = full_text_annotation.pages

    for page in pages:
        block_words = []
        # 遍历每一页的块
        for block in page.blocks:
            words_line_text = ""
            for paragraph in block.paragraphs:
                word_text_list = []
                is_break = False
                is_break_first = False
                is_app = False
                special_block = []
                # print(paragraph.bounding_box)
                for kkk in range(len(paragraph.words)):
                    word = paragraph.words[kkk]
                    text_block = ""
                    for symbol in word.symbols:
                        if is_break:
                            if is_app:
                                special_block[len(special_block) - 1]['text'] += symbol.text
                                if hasattr(symbol, "property") and hasattr(symbol.property, "detected_break"):
                                    break_type = symbol.property.detected_break.type_
                                    if break_type == vision.TextAnnotation.DetectedBreak.BreakType.SPACE:
                                        special_block[len(special_block) - 1]['text'] += " "
                                    elif break_type in (
                                            vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE,
                                            vision.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK
                                    ):
                                        is_break = True
                                        is_break_first = True
                                        is_app = False
                                continue
                            elif is_break_first:
                                is_break_first = False
                                tmp = symbol.bounding_box.vertices[0]
                                tmp2 = paragraph.words[0].symbols[0].bounding_box.vertices[0]
                                # 说明可能截取错误，需要重新修正
                                if abs(tmp.x - tmp2.x) < 3:
                                    special_block.append({
                                        'text': symbol.text,
                                        'x': tmp.x,
                                        'y': tmp.y,
                                    })
                                    is_app = True
                                    continue

                        text_block += symbol.text
                        # 处理空格或换行
                        if hasattr(symbol, "property") and hasattr(symbol.property, "detected_break"):
                            break_type = symbol.property.detected_break.type_
                            if break_type == vision.TextAnnotation.DetectedBreak.BreakType.SPACE:
                                text_block += " "
                            elif break_type in (
                                    vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE,
                                    vision.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK
                            ):
                                is_break = True
                                is_break_first = True
                    inner_x = word.symbols[0].bounding_box.vertices[0].x
                    inner_y = word.symbols[0].bounding_box.vertices[0].y

                    word_text_list.append({
                        'text': text_block,
                        'x': inner_x,
                        'y': inner_y,
                    })
                word_text = "".join([w['text'] for w in word_text_list])
                word_text = strip_text(word_text)
                if re.fullmatch(date_pattern, word_text,  re.IGNORECASE):
                    logger.debug(f"忽略了{word_text}")
                    continue
                bbox = paragraph.words[0].bounding_box.vertices
                block_words.append({"text": word_text, 'x': bbox[0].x, 'y': bbox[0].y, 'rx': paragraph.bounding_box.vertices[1].x})
                block_words.extend(special_block)

        block_words.sort(key=lambda e: e.get('y'))

    # 抹平y
    prev = None
    processed_block_words = []
    for item in block_words:
        if prev is None:
            processed_block_words.append([item])
            prev = item
            continue

        if abs(item.get('y') - prev.get('y')) >= 40:
            processed_block_words.append([item])
        else:
            last = processed_block_words[-1][-1]

            if last.get('x') <= item.get('x'):
                if pattern2.findall(item.get('text')):
                    processed_block_words.append([item])
                else:
                    item['text'] = " "+item['text']
                    processed_block_words[-1].append(item)
            else:
                if pattern2.findall(last.get('text')):
                    # bug05.png 换行情况
                    if pattern2.findall(item.get('text')):
                        processed_block_words.append([item])
                    else:
                        item['text'] = " " + item['text']
                        processed_block_words[-1].append(item)
                else:
                    if pattern2.findall(item.get('text')):
                        processed_block_words.append([item])
                    else:
                        insert_pos = len(processed_block_words[-1]) - 1
                        item['text'] = " " + item['text']
                        processed_block_words[-1].insert(insert_pos,item)
        prev = item


    temp_group = []
    for line_item in processed_block_words:
        # line_item.sort(key=lambda e: e.get('x'))
        if len(line_item) > 2:
            if line_item[1]['text'].strip() == "0":
                del line_item[1]

        temp_group.append("".join([w['text'] for w in line_item]))

    pattern = re.compile(
        r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
        r"(.*)"  # 匹配内容
    )

    result_list = []
    for v in temp_group:
        content = v
        matches = pattern.findall(content)
        if len(matches) < 1:
            logger.error("Opt.正则匹配失败,原句：{}".format(content))
            continue

        result_list.append(matches[0])

    # for x in temp_group:
    #     print("{} x:{} y:{}".format(x.get('text'), x.get('x'), x.get('y')))
    return result_list


def strip_text(text):
    chars = ["⚫", "•", "◉"]
    for char in chars:
        text = text.replace(char, "").replace(f"{char} ", "")
    return text


if __name__ == "__main__":
    code = "bug01"
    image_path = f"screenshots/{code}.png"
    # extracted_text = extract_text_from_image(image_path,  code)
    # print("提取的文本:", extracted_text)
    logger.setLevel(logging.DEBUG)
    with open(f"case/{code}.json", 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        response = types.AnnotateImageResponse.from_json(json.dumps(data))
        result = match_text(response)
        for x in result:
            print(f"行:{x}")
