import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "email"

# POP3
POP3_HOST = ""
POP3_PORT = 995
POP3_USER = ""
POP3_PASSWORD = ""
POP3_ENABLE_SSL = True
POP3_INDEX_FILE = os.path.join(DATA_DIR, "pop3_index.txt")
POP3_RETR_INTERVAL = 60
# 支持 0, 1, 2，数字越大，打印的日志越详细
POP3_DEBUG_LEVEL = 0

# 阿里云 OSS
ENABLE_ALIYUN_OSS = False
ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_ACCESS_KEY_SECRET = ""
ALIYUN_OSS_ENDPOINT = ""
ALIYUN_OSS_BUCKET_NAME = ""

ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
if not os.path.isdir(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# 飞书通知
FEISHU_WEBHOOK = ""
