import logging

import redis

log = logging.getLogger(__name__)


class IndexManager:
    def put(self, idx: int):
        raise NotImplementedError()

    def get(self, default: int) -> int:
        raise NotImplementedError()


class RedisIndexManager(IndexManager):
    def __init__(self, index_key: str, host: str = "localhost", port: int = 6379, db: int = 0):
        super().__init__()
        self.index_key = index_key
        self.host = host
        self.port = port
        self.db = db
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)

    def put(self, idx: int):
        self.redis.set(self.index_key, idx)

    def get(self, default: int = 1) -> int:
        idx = self.redis.get(self.index_key)
        if idx is not None:
            assert isinstance(idx, bytes)
            return int(idx)
        self.put(default)
        return default

    def close(self):
        self.redis.close()
