import requests

def send_chat_request(content):
    api_key = ''  # 替换为你的 API 密钥
    api_url = 'https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions'  # 替换为实际的 API 地址

    # 请求参数
    payload = {
        "model": "bot-20250304111409-p8dh8",  # 模型 ID
        "messages": [
            {
                "role": "user",
                "content": """翻译以下内容:{}.要求: 直接返回翻译结果，不要返回不相关信息。""".format(content),
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
        print(f"请求失败: {e}")
        return None

# 示例用法
if __name__ == "__main__":
    content = "Please analyze the recent stock price fluctuations of Apple Inc."
    result = send_chat_request(content)
