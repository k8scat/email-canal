import json
import sys
import time
import traceback

from kafka_producer import Producer
from pop3 import POP3
from storage.oss import AliyunOSS
from settings import *

handlers = [
    logging.StreamHandler(stream=sys.stdout),
]
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s: %(message)s",
                    handlers=handlers)

log = logging.getLogger(__name__)


def main():
    msg_count = pop3.count()
    log.info(f"Email count: {msg_count}")
    email_index = 1
    if os.path.isfile(POP3_INDEX_FILE):
        try:
            with open(POP3_INDEX_FILE) as f:
                email_index = int(f.read().strip())
        except Exception as e:
            log.warning(f"Read email index failed: {e}, use default index: {email_index}")

    try:
        while True:
            log.info(f"Retrieve email index: {email_index}")
            try:
                m = pop3.retr(email_index)
                if m is None:
                    log.error(f"Retrieve email failed, index: {email_index}")
                    break

                try:
                    msg = json.dumps(m.__dict__).encode()
                except Exception as e:
                    log.error(f"Serialize message failed: {e}, index: {email_index}")
                    break

                producer.send(msg)
                email_index += 1
            except Exception as e:
                if POP3.message_not_found(e):
                    log.info(f"Email not exists, index: {email_index}, sleep {POP3_RETR_INTERVAL} seconds...")
                    time.sleep(POP3_RETR_INTERVAL)
                    continue

                if POP3.message_already_deleted(e):
                    log.info(f"Email already deleted, index: {email_index}")
                    email_index += 1
                    continue

                log.error(f"Process failed: {e}, index: {email_index}, traceback:\n{traceback.format_exc()}")
                break
    finally:
        with open(POP3_INDEX_FILE, "w") as f:
            f.write(str(email_index))


if __name__ == "__main__":
    storage = None
    if ENABLE_ALIYUN_OSS:
        storage = AliyunOSS(ALIYUN_OSS_ACCESS_KEY_ID, ALIYUN_OSS_ACCESS_KEY_SECRET,
                            ALIYUN_OSS_ENDPOINT, ALIYUN_OSS_BUCKET_NAME)

    pop3 = POP3(host=POP3_HOST, user=POP3_USER, password=POP3_PASSWORD, local_attachment_dir=ATTACHMENTS_DIR,
                port=POP3_PORT, enable_ssl=POP3_ENABLE_SSL, storage=storage, debug_level=POP3_DEBUG_LEVEL)
    pop3.login()

    producer = Producer(broker=KAFKA_BROKER, topic=KAFKA_TOPIC)
    try:
        main()
    finally:
        producer.close()
        pop3.quit()
