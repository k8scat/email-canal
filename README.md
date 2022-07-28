# email-canal

通过 POP3 协议同步邮件到 Kafka，支持上传附件到阿里云 OSS。

## 快速开始

### 运行 Kafka

```bash
docker network create kafka_net
docker compose -f deploy/kafka up -d
```

### 运行 email-canal

编辑 `settings.py` 文件，主要修改 `POP3`、`阿里云 OSS` 和 `飞书告警` 的配置，其他配置保持默认即可。

```bash
docker compose up -d
```

## Author

[K8sCat](https://github.com/k8scat)

## License

[MIT](https://github.com/k8scat/email-canal/blob/main/LICENSE)
