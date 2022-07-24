from kafka import KafkaProducer


class Producer:
    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=self.broker)

    def send(self, message: bytes):
        self.producer.send(self.topic, message)

    def close(self):
        self.producer.close()

