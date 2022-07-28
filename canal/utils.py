import logging
from email.mime.application import MIMEApplication

import requests


def gen_attachment(content: bytes | str, filename: str = '', content_disposition: str = '') -> MIMEApplication:
    attachment = MIMEApplication(content, Name=filename)
    if content_disposition:
        attachment['Content-Disposition'] = content_disposition
    else:
        attachment.add_header('Content-Disposition',
                              'attachment', filename=filename)
    return attachment


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
                logging.error(f"Send feishu message failed: {r.status_code} {r.text}")
