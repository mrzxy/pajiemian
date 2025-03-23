import requests

from emqx import to_publish_role
from logger import logger

webhooks = {
    "dp": "https://discord.com/api/webhooks/1351026063521611786/ocZvPs3Sj94Nye_bWOMlXfxv5XedwxQ_7yScMlvmarGI1-x5CzbTLbTNZUurm8NV5xmP",
    "rickman": "https://discord.com/api/webhooks/1351026161542627348/TrbGb9vI6DpglWEibiSCcDs49G7e7pNQBod1lulbsnwMes9thHB4hUHPRcsc5J2yCNNx",
    "kira": "https://discord.com/api/webhooks/1351026232753524858/cgHpgZ5CacN3fxb_Uxsz1RKmxWSnH7tlLwmP_BLA-fOsPTO1bpAU4mvRrbiOU3ik9VQY"
}
# webhooks = {
#     "dp": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-",
#     "rickman": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-",
#     "kira": "https://discord.com/api/webhooks/1350049241501929542/whfC8x3c_NlUOyKwrayTFPs0NJRbDLJy_jtnkJU4zxSbh9UYmc-7fNCMUD5-2O3pclX-"
# }
class Discord:
    def __init__(self):
        pass

    def send_msg_by_webhook(self, user, msg):

        key = user.lower()
        logger.info("发送 emqx {}".format(to_publish_role(key, msg)))

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