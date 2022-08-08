# email-canal

通过 POP3 协议同步邮件到 Kafka，支持附件本地或 OSS 存储。

## 快速开始

复制 [canal/settings.py](./canal/settings.py) 文件到项目根目录，主要修改 `POP3` 的配置，其他配置保持默认即可。

```bash
# 启动
docker compose up -d
```

## Author

[K8sCat](https://github.com/k8scat)

## License

[MIT](https://github.com/k8scat/email-canal/blob/main/LICENSE)
