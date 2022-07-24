import os

PROD = os.environ.get("PROD", "").lower()


def is_prod() -> bool:
    return PROD == "true"


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if is_prod():
    ROOT_DIR = "/email-canal/data"

KAFKA_BROKER = "localhost:9092"
if is_prod():
    KAFKA_BROKER = "kafka:9092"
KAFKA_TOPIC = "email"

# POP3
POP3_HOST = ""
POP3_PORT = 995
POP3_USER = ""
POP3_PASSWORD = ""
POP3_ENABLE_SSL = True
POP3_INDEX_FILE = os.path.join(ROOT_DIR, "pop3_index.txt")
POP3_RETR_INTERVAL = 60

# 阿里云 OSS
ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_ACCESS_KEY_SECRET = ""
ALIYUN_OSS_ENDPOINT = ""
ALIYUN_OSS_BUCKET_NAME = ""

ATTACHMENTS_DIR = os.path.join(ROOT_DIR, "attachments")
if not os.path.isdir(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# 飞书通知
FEISHU_WEBHOOK = ""
