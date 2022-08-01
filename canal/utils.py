import hashlib


def sha256(data: bytes):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
