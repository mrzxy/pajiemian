import time
import paho.mqtt.client as mqtt
import json
import logging

# logging.basicConfig(level=logging.DEBUG)
# MQTT 服务器信息
BROKER = "f24a5dcf.ala.cn-hangzhou.emqxsl.cn"  # 替换为你的 MQTT 服务器地址
USERNAME = "dcaccount"  # MQTT 用户名（如果需要）
PASSWORD = "f24a5dcf123"  # MQTT 密码（如果需要）
def on_connect(client, userdata, flags, rc, e2):
    print("Connected to MQTT Broker!")
    print(client, userdata, flags, rc, e2)
# 消息发布成功回调（⚠️ 移除 properties 参数）
def on_publish(client, userdata, mid, a, b):
    print(client, mid, a, b)
    print(f"Message {mid} published successfully.")

def to_publish(topic: str, message: str):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set("./emqxsl-ca.crt")
    client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.on_publish = on_publish

    # client.enable_logger()
    client.connect(BROKER, 8883, 60)
    client.loop_start()
    result = client.publish(topic, message)
    result.wait_for_publish()
    client.loop_stop()
    client.disconnect()


def to_publish_role(target, msg):
    topic = ""
    content = {}

    target = target.lower()
    if target == "dp":
        topic = "lis-msg/dp"
        content = {
            "channel": "dp-alerts",
            "content": msg,
        }
    elif target == "rickman":
        topic = "lis-msg/rickmarch"
        content = {
            "channel": "rick-alerts",
            "content": msg,
        }
    elif target == "kira":
        topic = "lis-msg/kiraturner"
        content = {
            "channel": "kira-alerts",
            "content": msg,
        }
    if topic != "":
        return to_publish(topic, json.dumps(content))
    return False


if __name__ == "__main__":
    r = to_publish("lis-msg/roger",  json.dumps({
        "channel": "rogertest",
        "content": 'tou tong',
    }))
    print(r)

# 示例用法