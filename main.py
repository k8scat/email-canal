import json
import logging
import time
import traceback

from canal.feishu import Feishu
from canal.message import Producer
from canal.pop3 import POP3
from canal.storage import AliyunOSS
from settings import *


def main():
    msg_count = pop3.count()
    logging.info(f"Email count: {msg_count}")
    email_index = 1
    if os.path.isfile(POP3_INDEX_FILE):
        try:
            with open(POP3_INDEX_FILE) as f:
                email_index = int(f.read().strip())
        except Exception as e:
            logging.warning(f"Read email index failed: {e}, use default index: {email_index}")

    try:
        while True:
            logging.info(f"Retrieve email index: {email_index}")
            try:
                m = pop3.retr(email_index)
                if m is None:
                    feishu.send_msg(f"Retrieve email failed, index: {i}")
                    break

                try:
                    msg = json.dumps(m.__dict__).encode()
                except Exception as e:
                    feishu.send_msg(f"Serialize message failed: {e}, index: {i}")
                    break

                producer.send(msg)
                email_index += 1

            except Exception as e:
                if email_not_found(e):
                    logging.info(f"Email not exists, index: {email_index}, sleep {POP3_RETR_INTERVAL} seconds...")
                    time.sleep(POP3_RETR_INTERVAL)
                    continue

                logging.error(e)
                logging.error(traceback.format_exc())
                email_index -= 1
                break
    finally:
        with open(POP3_INDEX_FILE, "w") as f:
            f.write(str(email_index))


def email_not_found(e: Exception) -> bool:
    return len(e.args) == 1 and e.args[0] == b'-ERR Message not exists'


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    feishu = Feishu(FEISHU_WEBHOOK)

    if ALIYUN_OSS_ACCESS_KEY_ID == "" or \
            ALIYUN_OSS_ACCESS_KEY_SECRET == "" or \
            ALIYUN_OSS_BUCKET_NAME == "" or \
            ALIYUN_OSS_ENDPOINT == "":
        oss = None
    else:
        oss = AliyunOSS(ALIYUN_OSS_ACCESS_KEY_ID, ALIYUN_OSS_ACCESS_KEY_SECRET,
                        ALIYUN_OSS_ENDPOINT, ALIYUN_OSS_BUCKET_NAME)

    pop3 = POP3(host=POP3_HOST, user=POP3_USER, password=POP3_PASSWORD, local_attachment_dir=ATTACHMENTS_DIR,
                port=POP3_PORT, enable_ssl=POP3_ENABLE_SSL, oss=oss, debug_level=POP3_DEBUG_LEVEL)
    pop3.login()

    producer = Producer(KAFKA_BROKER, KAFKA_TOPIC)

    try:
        main()
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
    finally:
        producer.close()
