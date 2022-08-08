import logging
import os.path
import poplib
import time
import uuid
from email.header import decode_header
from email.message import Message
from email.parser import Parser
from email.utils import parseaddr
from typing import Tuple, List

from canal.storage.local import LocalStorage
from canal.storage.oss import AliyunOSS
from canal.storage.storage import Storage
from canal.utils import sha256

log = logging.getLogger(__name__)


class Email:
    def __init__(self, subject: str, from_addr: Tuple[str, str], to_addr: Tuple[str, str],
                 plain_content: str = "", html_content: str = "", attachments: List[dict] | None = None,
                 size: int | None = None, raw: bytes | None = None, index: int | None = None,
                 date: float | None = None):
        self.subject = subject
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.plain_content = plain_content
        self.html_content = html_content
        self.attachments = attachments
        self.size = size
        self.raw = raw
        self.index = index
        self.date = date


class POP3:
    poplib._MAXLINE = 1024 * 1024

    status_ok = b'+OK'

    def __init__(self, host: str, user: str, password: str, port: int | None = None,
                 enable_ssl: bool = True, debug_level: int = 0,
                 storages: list[Storage] | None = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.debug_level = debug_level
        self.enable_ssl = enable_ssl
        self.storages = storages

        if self.port is None:
            if self.enable_ssl:
                self.port = poplib.POP3_PORT
            else:
                self.port = poplib.POP3_SSL_PORT

        if self.enable_ssl:
            self.client = poplib.POP3_SSL(host=self.host, port=self.port)
        else:
            self.client = poplib.POP3(host=self.host, port=self.port)
        self.client.set_debuglevel(self.debug_level)
        self.login()

    def login(self, retry: int = 3, interval: int = 3):
        self.client.user(self.user)

        # pop3_server login retry: poplib.error_proto: b'-ERR login fail, please try again later'
        for count in range(retry):
            try:
                self.client.pass_(self.password)
                break
            except Exception as e:
                if count == retry - 1:
                    raise Exception(f'POP3 login failed: {e}')
                log.warning(f'POP3 login failed: {e}')
                time.sleep(interval)

    def reset(self):
        if self.enable_ssl:
            self.client = poplib.POP3_SSL(host=self.host, port=self.port)
        else:
            self.client = poplib.POP3(host=self.host, port=self.port)
        self.client.set_debuglevel(self.debug_level)
        self.login()

    def quit(self):
        self.client.quit()

    @staticmethod
    def get_email_header(msg: Message, header: str) -> Tuple[str, str]:
        header = header.lower()
        if header not in ["subject", "from", "to", "date"]:
            log.warning(f"Invalid header: {header}")
            return "", ""

        value = msg.get(header, None)
        if not value:
            return "", ""
        if header in ["subject", "date"]:
            return POP3.decode_header_value(value), ''

        name, email = parseaddr(value)
        name = POP3.decode_header_value(name)
        return name, email

    @staticmethod
    def get_subject(msg: Message) -> str:
        return POP3.get_email_header(msg, "subject")[0]

    @staticmethod
    def get_content(msg: Message) -> str:
        content = msg.get_payload(decode=True)
        charset = msg.get_content_charset(failobj="utf-8")
        if charset:
            content = content.decode(charset, errors="ignore")
        return content

    @staticmethod
    def get_payloads(msg: Message) -> list[Message]:
        payloads = []
        if msg.is_multipart():
            for payload in msg.get_payload():
                payloads.extend(POP3.get_payloads(payload))
        else:
            payloads.append(msg)
        return payloads

    def parse_email(self, msg: Message) -> dict:
        headers = []
        for k, v in msg.items():
            v = POP3.decode_header_value(v)
            headers.append((k, v))
            if k.lower() == "subject":
                log.info(f"Email subject: {v}")
        email = {
            "headers": headers,
        }

        raw_payloads = POP3.get_payloads(msg)
        payloads = []
        attachments = []
        for payload in raw_payloads:
            content_disposition = payload.get_content_disposition()
            headers = []
            for k, v in payload.items():
                v = POP3.decode_header_value(v)
                headers.append((k, v))
            p = {
                "headers": headers,
                "payload": payload.get_payload(),
            }
            payloads.append(p)

            if content_disposition == "attachment":
                p = payload.get_payload(decode=True)
                if not isinstance(p, bytes):
                    logging.warning(f"Payload is not bytes: {type(p)}")
                    continue

                filename = payload.get_filename()
                if not filename:
                    logging.warning(f"Filename not found in attachment payload")
                    continue
                logging.info(f"Raw filename: {filename}")
                filename = POP3.decode_header_value(filename)
                if not filename:
                    logging.warning(f"Decoded filename is empty")
                    continue
                logging.info(f"Decoded filename: {filename}")
                att = self.save_attachment(filename=filename, content=p)
                if att:
                    attachments.append(att)

        if len(payloads) > 0:
            email["payloads"] = payloads
        if len(attachments) > 0:
            email["attachments"] = attachments
        return email

    def save_attachment(self, filename: str, content: bytes) -> dict:
        data = {
            "name": filename,
            "hash": sha256(content),
            "size": len(content),
        }
        if len(self.storages) == 0:
            return data

        ext = os.path.splitext(filename)[1]
        key = f"{str(uuid.uuid4())}{ext}"
        data["key"] = key
        for s in self.storages:
            if isinstance(s, LocalStorage):
                logging.info(f"Saving attachment to local storage: {key}")
                s.upload(key=key, content=content)
            elif isinstance(s, AliyunOSS):
                logging.info(f"Saving attachment to aliyun oss: {key}")
                s.upload(key=key, content=content)
        return data

    def count(self) -> int:
        count, _ = self.client.stat()
        return count

    def retr(self, index: int) -> dict | None:
        log.info(f"Retrieve email index: {index}")
        resp, lines, octets = self.client.retr(index)
        if not resp.startswith(self.status_ok):
            log.error(f"Retrieve email failed: {resp}")
            return None
        log.info(f"Email size: {octets}")

        msg_content_bytes = b"\r\n".join(lines)
        try:
            msg_content = msg_content_bytes.decode("utf-8")
        except Exception as e:
            log.warning(f"Decode message with utf-8 failed: {e}")
            log.info("Try to find message charset...")
            charset = ""
            for line in lines:
                if b"Content-Type: " in line:
                    line = line.decode("utf-8").lower()
                    for part in line.split(";"):
                        if "charset" in part:
                            pos = part.find("charset=")
                            charset = part[pos + 8:].strip()
                            break
                if charset:
                    break
            if charset == "":
                log.warning("Message charset not found and use utf-8")
                charset = "utf-8"
            else:
                log.info(f"Found message charset: {charset}")

            try:
                msg_content = msg_content_bytes.decode(charset, errors="ignore")
            except Exception as e:
                log.error(f"Decode message failed: {e}")
                return None

        msg = Parser().parsestr(msg_content)
        email = self.parse_email(msg)
        email["index"] = index
        return email

    @staticmethod
    def decode_header_value(value) -> str:
        # return u''.join(
        #     word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        #     for word, encoding in decode_header(value))

        result = []
        for part, charset in decode_header(value):
            s = part
            if isinstance(part, bytes):
                charsets = []
                if charset:
                    charsets.append(charset)
                if charset not in ['utf-8', 'utf8']:
                    charsets.append('utf-8')
                charsets.append('gbk')

                decode_ok = False
                for encoding in charsets:
                    try:
                        log.info(f"Try to decode header value with {encoding}")
                        s = part.decode(encoding)
                        decode_ok = True
                        break
                    except UnicodeDecodeError:
                        log.warning(f"Decode header value with {encoding} failed: {part}")

                if not decode_ok:
                    encoding = charsets[0]
                    log.info(f"Try to decode header value with {encoding} and ignore errors")
                    s = part.decode(encoding, errors="ignore")

            result.append(s)
        return u''.join(result)

    @staticmethod
    def is_not_found(e: Exception) -> bool:
        return len(e.args) == 1 and e.args[0] == b'-ERR Message not exists'

    @staticmethod
    def is_deleted(e: Exception) -> bool:
        return len(e.args) == 1 and e.args[0] == b'-ERR Message already deleted'
