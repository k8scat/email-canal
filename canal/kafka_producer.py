from kafka import KafkaProducer


class Producer:
    batch_size = 0  # 禁用批处理
    compression_type = "lz4"

    def __init__(self, **kwargs):
        self.broker = kwargs.get("broker", None)
        self.topic = kwargs.get("topic", None)
        self.max_request_size = kwargs.get("max_request_size", 104857600)
        if not self.broker or not self.topic:
            raise Exception(f"Invalid producer args: {kwargs}")

        self.producer = KafkaProducer(bootstrap_servers=self.broker,
                                      max_request_size=self.max_request_size,
                                      compression_type=self.compression_type,
                                      batch_size=self.batch_size)

    def send(self, message: bytes):
        res = self.producer.send(self.topic, message)
        if res.failed():
            raise Exception(f"Send message failed: {res.exception}")

    def close(self):
        self.producer.close()
