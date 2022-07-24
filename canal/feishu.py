import logging

import requests


class Feishu:
    def __init__(self, webhook: str):
        self.webhook = webhook

    def send_msg(self, msg: str):
        logging.warning(f"Send msg: {msg}")
        if not self.webhook:
            return
        payload = {
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        with requests.post(self.webhook, json=payload, verify=False) as r:
            if r.status_code != 200:
                logging.error(f"Alert failed: {r.status_code} {r.text}")
