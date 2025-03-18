import requests

webhooks = {
    "dp": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-",
    "rickman": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-",
    "kira": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-"
}
class Discord:
    def __init__(self):
        pass

    def send_msg_by_webhook(self, user, msg):
        key = user.lower()
        if key not in webhooks:
            print("Webhook not found for user: " + user)
            return
        webhook = webhooks[key]

        payload = {"content": msg}
        response = requests.post(webhook, json=payload)

        if response.status_code == 204:
            print("消息发送成功！")
            return True
        else:
            print(f"发送失败: {response.status_code}, {response.text}")
            return False

discord = Discord()