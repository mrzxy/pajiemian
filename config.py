import json

def init_config():
    with open("config.json") as f:
        config = json.load(f)
        return config

conf = init_config()