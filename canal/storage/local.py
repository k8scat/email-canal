import os

from canal.storage.storage import Storage


class LocalStorage(Storage):
    def __init__(self, folder: str):
        self.folder = folder
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder, exist_ok=True)

    def upload(self, *args, **kwargs):
        key = kwargs.get("key", "")
        if key == "":
            raise ValueError("key is required")
        filepath = os.path.join(self.folder, key)

        content = kwargs.get("content", None)
        if content is None:
            raise ValueError("content is required")

        if isinstance(content, bytes):
            with open(filepath, "wb") as f:
                f.write(content)
        else:
            raise TypeError("content must be bytes")



