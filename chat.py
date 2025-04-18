import re
import requests
from config import conf
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT


def send_chat_request(content):
    try:
        api_key = conf['TAOBAO_CHAT_KEY']
        anthropic = Anthropic(api_key=api_key)

        message = f"""
        You are a professional stock trader tasked with analyzing and translating financial text content. Your job is to identify financial and stock-related information, recognize professional terminology, detect spelling errors, identify stock price and index point errors, and then translate the corrected content into fluent Chinese.
Here is the text content you need to analyze:
<text_content>
{content}
</text_content>
Follow these steps to complete your task:
1. Carefully read through the text content and identify any financial or stock-related information. This may include company names, stock symbols, stock prices, market indices, or other relevant financial data.
2. Recognize and note any professional financial or stock market terminology used in the text.
3. Detect any spelling errors in the text, particularly in company names, stock symbols, or financial terms. Make a mental note of these errors for later correction.
4. Identify any stock price or index point errors by checking if the mentioned values seem reasonable or if they contradict other information in the text.
5. Based on your analysis, create a corrected version of the text, fixing any spelling errors and adjusting any incorrect stock prices or index points. Use your expertise to make educated guesses for corrections when necessary.
6. Translate the corrected English text into fluent, accurate Chinese, ensuring that all financial terms and concepts are correctly conveyed.
7. Prepare your final output in the following format:
<analysis>
List the key financial information, professional terminology, and any errors you identified in the original text.
</analysis>
<corrections>
Provide a brief summary of the corrections you made to the original text.
</corrections>
<translation>
Present your Chinese translation of the corrected text.
</translation>
Your final output should only include the content within the <analysis>, <corrections>, and <translation> tags. Do not include any of your thought processes or intermediate steps in the final output.
"""

        response = anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            messages=[{"role": "user", "content": message}],
            max_tokens=20000,
            stream=False
        )
        text = response.content[0].text
        # 使用正则表达式提取translation内容
        pattern = r'<translation>(.*?)</translation>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            translation = match.group(1).strip()
            return translation
        return None

    except Exception as e:
        print(f"excpetion 请求失败: {e}")
        return None


def send_chat_request_old(content):
    api_key = conf['CHAT_API_KEY']
    api_url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'  # 替换为实际的 API 地址

    tpl = "请你扮演一个专业的股票交易员，我会给你英文内容，你要能识别出文字里关于金融，股票的相关信息，股票代码等专业术语，能识别出文字里的拼写错误，识别出股票价格错误，点位错误等。比如识别完并纠正完后，结合上下文把我给你的英文内容翻译成地道正确的中文。补充一个要求，不要把你纠正和识别的思考过程发出来，只需要直接给我成品就行. 内容为:{}.".format(
        content)
    # 请求参数
    payload = {
        "model": "doubao-1-5-pro-32k-250115",  # 模型 ID
        "messages": [
            {
                "role": "user",
                "content": tpl,
            }
        ],
        "response_format": {
            "type": "json_object"
        }
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
    content = """I'll put my charts up in a second, but I wanted to comment on what Mao just posted. Yes, Netflix is up, but they're up because they said they see a $1 trillion market cap in the next few years. That's where the strength came from. Uh, we'll see the earnings tomorrow, right? That's Thursday. And uh here's the thing, I was looking for an inexpensive way to get into a call spread for next week. What I want to do is I want to sell, sell a call spread or sell a put spread for this week, collect some income from that and then use that income to buy
[08:07]As much as I love you, I think I hate you. So as soon as I come up with the structure that I think will be worth the risk reward, I'll let you know. And if I don't find one, we don't find one."""
    result = send_chat_request(content)
    print(result)
