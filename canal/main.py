import json
import poplib
import sys
import time
import traceback

from canal.storage.local import LocalStorage
from kafka_producer import Producer
from pop3 import POP3
from settings import *
from canal.storage.oss import AliyunOSS

handlers = [
    logging.StreamHandler(stream=sys.stdout),
]
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s: %(message)s",
                    handlers=handlers)

log = logging.getLogger(__name__)


def main():
    pop3 = POP3(host=POP3_HOST, user=POP3_USER, password=POP3_PASSWORD,
                port=POP3_PORT, enable_ssl=POP3_ENABLE_SSL, debug_level=POP3_DEBUG_LEVEL,
                storages=storages)
    pop3_has_reset = False

    count = pop3.count()
    log.info(f"Email count: {count}")
    email_index = 1
    if os.path.isfile(POP3_INDEX_FILE):
        try:
            with open(POP3_INDEX_FILE) as f:
                email_index = int(f.read().strip())
        except Exception as e:
            log.warning(f"Read email index failed: {e}, use default index: {email_index}")
            with open(POP3_INDEX_FILE, "w") as f:
                f.write(str(email_index))

    try:
        while True:
            try:
                m = pop3.retr(email_index)
                if m is None:
                    log.error(f"Retrieve email failed, index: {email_index}")
                    break

                if pop3_has_reset:
                    pop3_has_reset = False
                try:
                    msg = json.dumps(m).encode()
                except Exception as e:
                    log.error(f"Serialize message failed: {e}, index: {email_index}")
                    break

                producer.send(msg)
                email_index += 1
            except Exception as e:
                if isinstance(e, poplib.error_proto) and not pop3_has_reset:
                    pop3.reset()
                    pop3_has_reset = True
                    continue

                if POP3.is_not_found(e):
                    log.info(f"Email not exists, index: {email_index}, sleep {POP3_RETR_INTERVAL} seconds...")
                    time.sleep(POP3_RETR_INTERVAL)
                    continue

                if POP3.is_deleted(e):
                    log.info(f"Email already deleted, index: {email_index}")
                    email_index += 1
                    continue

                log.error(f"Process failed: {e}, index: {email_index}, traceback:\n{traceback.format_exc()}")
                break
    finally:
        with open(POP3_INDEX_FILE, "w") as f:
            log.info(f"Write email index: {email_index}")
            f.write(str(email_index))
        pop3.quit()


if __name__ == "__main__":
    storages = []
    if ENABLE_LOCAL_STORAGE:
        storages.append(LocalStorage(ATTACHMENTS_DIR))
    if ENABLE_ALIYUN_OSS:
        oss = AliyunOSS(ALIYUN_OSS_ACCESS_KEY_ID, ALIYUN_OSS_ACCESS_KEY_SECRET,
                        ALIYUN_OSS_ENDPOINT, ALIYUN_OSS_BUCKET_NAME)
        storages.append(oss)

    producer = Producer(broker=KAFKA_BROKER, topic=KAFKA_TOPIC)
    try:
        while True:
            main()
    finally:
        producer.close()
