from kafka import KafkaProducer


class Producer:
    def __init__(self, **kwargs):
        self.broker = kwargs.get("broker", None)
        self.topic = kwargs.get("topic", None)
        if not self.broker or not self.topic:
            raise Exception(f"Invalid producer args: {kwargs}")

        self.producer = KafkaProducer(bootstrap_servers=self.broker, max_request_size=10485760)

    def send(self, message: bytes):
        res = self.producer.send(self.topic, message)
        if res.failed():
            raise Exception(f"Send message failed: {res.exception}")

    def close(self):
        self.producer.close()
