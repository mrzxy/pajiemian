import json
from logger import logger
import re
import os
from google.cloud import vision
from google.cloud.vision_v1 import types

def extract_text_from_image(image_path):
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
    response_json = vision.AnnotateImageResponse.to_json(response)
    with open("response.json", 'w', encoding='utf-8') as json_file:
        json.dump(json.loads(response_json), json_file, ensure_ascii=False, indent=4)

    return match_text(response)


def match_text(response):
    full_text_annotation = response.full_text_annotation
    pages = full_text_annotation.pages

    for page in pages:
        block_words = []
        # 遍历每一页的块
        for block in page.blocks:
            words_line_text = ""
            for paragraph in block.paragraphs:
                word_text = ""
                for word in paragraph.words:
                    for symbol in word.symbols:
                        word_text += symbol.text
                        # 处理空格或换行
                        if hasattr(symbol, "property") and hasattr(symbol.property, "detected_break"):
                            break_type = symbol.property.detected_break.type_
                            if break_type == vision.TextAnnotation.DetectedBreak.BreakType.SPACE:
                                word_text += " "
                            elif break_type in (
                                    vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE,
                                    vision.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK
                            ):
                                word_text += ""

                words_line_text += word_text

                bbox = block.paragraphs[0].words[0].bounding_box.vertices
                x_min = min(v.x for v in bbox)
                y_avg = sum(v.y for v in bbox) / 4  # 计算 y 坐标平均值，防止倾斜影响
                block_words.append({"text": words_line_text, 'x':x_min, 'y':y_avg})

        block_words.sort(key=lambda e: e.get('y'))

    temp_group = []
    for item in block_words:
        if len(temp_group) == 0:
            temp_group.append(item)
            continue

        last = temp_group[len(temp_group) - 1]
        if item.get('y') - last.get('y')  >= 4:
            temp_group.append(item)
        else:
            if last.get('x') < item.get('x'):
                last['text'] = last.get('text') + ' ' + item.get('text')
            else:
                last['text'] = item.get('text') + ' ' + last.get('text')

    pattern = re.compile(
        r"(D\s?P|Rickman|Kira)\s?"  # 匹配角色名（兼容空格）
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s?\d{1,2}(?::\d{1,2})?:\d{2}\s?[AP]M)\s?"  # 匹配事件时间
        r"(.*)"  # 匹配内容
    )

    result_list = []
    for v in temp_group:
        content = v['text']
        matches = pattern.findall(content)
        if len(matches) < 1:
            logger.error("Opt.正则匹配失败,原句：{}".format(content))
            continue
        result_list.append(matches[0])

    # for x in temp_group:
    #     print("{} x:{} y:{}".format(x.get('text'), x.get('x'), x.get('y')))
    return result_list

if __name__ == "__main__":
    image_path = "screenshots/7.png"  # 替换为你的图片路径
    # extracted_text = extract_text_from_image(image_path)
    # print("提取的文本:", extracted_text)
    with open("response.json", 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        response = types.AnnotateImageResponse.from_json(json.dumps(data))
        result = match_text(response)
        for x in result:
            print(f"行:{x}")
