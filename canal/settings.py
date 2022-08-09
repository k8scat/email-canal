import logging
import os

DATA_DIR = "/email-canal/data"
if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

LOGS_DIR = "/email-canal/logs"
if not os.path.isdir(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

KAFKA_BROKER = "kafka:9092"
KAFKA_TOPIC = "email"
KAFKA_PRODUCER_MAX_REQUEST_SIZE = 104857600

# POP3
POP3_HOST = ""
POP3_PORT = 995
POP3_USER = ""
POP3_PASSWORD = ""
POP3_ENABLE_SSL = True
POP3_RETR_INTERVAL = 60
# 支持 0, 1, 2，数字越大，打印的日志越详细
POP3_DEBUG_LEVEL = 0

# 阿里云 OSS
ENABLE_ALIYUN_OSS = False
ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_ACCESS_KEY_SECRET = ""
ALIYUN_OSS_ENDPOINT = ""
ALIYUN_OSS_BUCKET_NAME = ""

ENABLE_LOCAL_STORAGE = True
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
if not os.path.isdir(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

LOG_LEVEL = logging.INFO
LOG_FILE = os.path.join(LOGS_DIR, "email-canal.log")

REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
