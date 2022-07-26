import io
import logging

import oss2
from oss2 import Bucket, SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

from canal.storage.storage import Storage

log = logging.getLogger(__name__)


class AliyunOSS(Storage):
    preferred_size = 1000 * 1024

    def __init__(self, access_key_id: str, access_key_secret: str, endpoint: str, bucket_name: str):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.bucket = self._get_bucket()

    def _get_bucket(self) -> Bucket:
        # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        # Endpoint以杭州为例，其它Region请按实际情况填写。
        return oss2.Bucket(auth, self.endpoint, self.bucket_name)

    def upload(self, *args, **kwargs):
        """
        分片上传

        参考：https://help.aliyun.com/document_detail/88434.html?spm=a2c4g.11186623.6.849.de955fffeknceQ
        """
        key = kwargs.get("key", "")
        content = kwargs.get("content", None)
        if content is None:
            raise ValueError("content is required")
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")

        # 初始化分片。
        # 如果需要在初始化分片时设置文件存储类型，请在init_multipart_upload中设置相关headers，参考如下。
        # headers = dict()
        # headers["x-oss-storage-class"] = "Standard"
        # upload_id = bucket.init_multipart_upload(key, headers=headers).upload_id
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        total_size = len(content)
        # determine_part_size方法用来确定分片大小。1000KB
        part_size = determine_part_size(total_size, preferred_size=self.preferred_size)

        # 逐个上传分片。
        parts = []
        with io.BytesIO(content) as f:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                # SizedFileAdapter(f, size)方法会生成一个新的文件对象，重新计算起始追加位置。
                result = self.bucket.upload_part(key, upload_id, part_number, SizedFileAdapter(f, num_to_upload))
                parts.append(PartInfo(part_number, result.etag))
                offset += num_to_upload
                part_number += 1
                log.debug(f"Upload progress: {offset / total_size * 100}%")

            # 完成分片上传。
            # 如果需要在完成分片上传时设置文件访问权限ACL，请在complete_multipart_upload函数中设置相关headers，参考如下。
            # headers = dict()
            # headers["x-oss-object-acl"] = oss2.OBJECT_ACL_PRIVATE
            # bucket.complete_multipart_upload(key, upload_id, parts, headers=headers)
            self.bucket.complete_multipart_upload(key, upload_id, parts)
