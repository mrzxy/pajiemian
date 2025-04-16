import re
import requests
from config import conf

# def send_chat_request_v2(content):
#     api_key = conf['TAOBAO_CHAT_KEY']
#     url = "https://dpapi.cn/v1/chat/completions"
#     tpl = """
#     将以下英文内容翻译成中文: {} . 要求:要能识别出文字里关于金融，股票的相关信息，股票代码等专业术语，能识别出文字里的拼写错误, 直接返回翻译结果，不要新增任何不相关信息和注。
#     """.format(content)
#     print(tpl)
#     return
#
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#         "Accept": "text/event-stream",
#     }
#     data = {
#         "model": "claude-3-7-sonnet-thinking",
#         "messages": [{"role": "user",
#                       "content": tpl}],
#     }
#
#     try:
#         response = requests.post(url, headers=headers, json=data)
#         if response.status_code != 200:
#             print(f"1.请求失败: {response.status_code}", response.text)
#             return None
#
#         json_data = response.json()
#         reply_content = json_data["choices"][0]["message"]["content"]
#
#         reply_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
#         if reply_content:
#             return reply_content.strip()
#         return ""
#
#     except Exception as e:
#         print(f"excpetion 请求失败: {e}")
#         return None
#
def send_chat_request(content):
    api_key = conf['CHAT_API_KEY']
    api_url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'  # 替换为实际的 API 地址

    tpl = "请你扮演一个专业的股票交易员，我会给你英文内容，你要能识别出文字里关于金融，股票的相关信息，股票代码等专业术语，能识别出文字里的拼写错误，识别出股票价格错误，点位错误等。比如识别完并纠正完后，结合上下文把我给你的英文内容翻译成地道正确的中文。补充一个要求，不要把你纠正和识别的思考过程发出来，只需要直接给我成品就行，不要返回原文注解. 内容为:{}.".format(content)
    # 请求参数
    payload = {
        "model": "doubao-1-5-pro-32k-250115",  # 模型 ID
        "messages": [
            {
                "role": "user",
                "content": tpl,
            }
        ]
    }

    # 请求头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        json_response = response.json()  # 返回 JSON 响应
        return json_response['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(response.text)
        print(f"请求失败: {e}")
        return None


# 示例用法
if __name__ == "__main__":
    content = """Good morning, everybody. Let's go through the charts real quick as you can see here, the spy broke above the AVO, the 8 and 10. Now you've got a resistance of 54633, but we're trading at 5:36, so we're right back down. I don't think we're going anywhere 538 is the middle of the range. AVA 536, and the 8 and 10 or 5:31 and 5:23. Retail sales tomorrow and Powell speaks at lunch. """
    result = send_chat_request(content)
    print(result)
