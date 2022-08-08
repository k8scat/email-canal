import oss2

ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_ACCESS_KEY_SECRET = ""
ALIYUN_OSS_ENDPOINT = ""
ALIYUN_OSS_BUCKET_NAME = ""


def main():
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth(ALIYUN_OSS_ACCESS_KEY_ID,
                     ALIYUN_OSS_ACCESS_KEY_SECRET)
    # Endpoint以杭州为例，其它Region请按实际情况填写。
    bucket = oss2.Bucket(auth, ALIYUN_OSS_ENDPOINT,
                         ALIYUN_OSS_BUCKET_NAME)

    while True:
        resp = bucket.list_objects()
        if len(resp.object_list) == 0:
            break

        keys = [obj.key for obj in resp.object_list]
        result = bucket.batch_delete_objects(keys)
        if result.status != 200:
            print(result)
            break

        print(f"Cleaned objects: {keys}")
        if len(resp.object_list) < 100:
            break


if __name__ == "__main__":
    main()
