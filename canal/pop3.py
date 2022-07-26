import logging
import os.path
import poplib
import time
import uuid
from email.header import decode_header
from email.message import Message
from email.mime.application import MIMEApplication
from email.parser import Parser
from email.utils import parseaddr, parsedate
from typing import Tuple, List

from canal.storage import AliyunOSS
from canal.utils import gen_attachment


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
    pop3 = None

    def __init__(self, host: str, user: str, password: str, local_attachment_dir: str,
                 port: int | None = None, enable_ssl: bool = True,
                 oss: AliyunOSS | None = None, debug_level: int = 0):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.debug_level = debug_level
        if self.port is None:
            if enable_ssl:
                self.port = poplib.POP3_PORT
            else:
                self.port = poplib.POP3_SSL_PORT

        if enable_ssl:
            self.pop3 = poplib.POP3_SSL(host=self.host, port=self.port)
        else:
            self.pop3 = poplib.POP3(host=self.host, port=self.port)
        self.pop3.set_debuglevel(self.debug_level)

        self.local_attachment_dir = local_attachment_dir
        self.oss = oss

    def login(self, retry: int = 3, interval: int = 3):
        # self.pop3.set_debuglevel(1)
        self.pop3.user(self.user)

        # pop3_server login retry: poplib.error_proto: b'-ERR login fail, please try again later'
        for count in range(retry):
            try:
                self.pop3.pass_(self.password)
                break
            except Exception as e:
                if count == retry - 1:
                    raise Exception(f'pop3 server login failed: {e}')
                logging.warning(f'pop3 server login failed: {e}')
                time.sleep(interval)

    @staticmethod
    def guess_charset(msg: Message) -> str:
        charset = msg.get_charset()
        if charset is None:
            # text/plain; charset="utf-8"
            # text/plain; charset="utf-8"; format=flowed
            # text/plain; charset = "gbk"
            content_type = msg.get('Content-Type', '').lower().replace(' ', '')
            for part in content_type.split(';'):
                if 'charset' in part:
                    pos = part.find('charset=')
                    charset = part[pos + 8:].strip()
                    break

            if charset is None:
                charset = 'utf-8'
        return charset

    @staticmethod
    def parse_email_header(msg: Message, header: str) -> Tuple[str, str]:
        header = header.lower()
        if header not in ['subject', 'from', 'to', 'date']:
            logging.warning(f'Invalid header: {header}')
            return '', ''

        value = msg.get(header, '')
        if not value:
            return '', ''
        if header in ['subject', 'date']:
            return POP3.decode_header_value(value), ''

        name, email = parseaddr(value)
        name = POP3.decode_header_value(name)
        return name, email

    @staticmethod
    def parse_subject(msg: Message) -> str:
        return POP3.parse_email_header(msg, 'Subject')[0]

    @staticmethod
    def parse_date(msg: Message) -> float | None:
        date = POP3.parse_email_header(msg, 'Date')[0]
        d = parsedate(date)
        if d is None:
            return None
        return time.mktime(d)

    @staticmethod
    def parse_email_content(msg: Message) -> str:
        content = msg.get_payload(decode=True)
        charset = POP3.guess_charset(msg)
        if charset:
            content = content.decode(charset, errors='ignore')
        return content

    def parse_email(self, msg: Message) -> Email:
        subject = POP3.parse_subject(msg)
        from_addr = POP3.parse_email_header(msg, 'From')
        to_addr = POP3.parse_email_header(msg, 'To')
        date = POP3.parse_date(msg)
        email = Email(subject=subject, from_addr=from_addr, to_addr=to_addr, date=date)

        logging.info(f'Parsing email: {subject}')

        parts = [msg]
        if msg.is_multipart():
            parts = msg.get_payload()

        attachments = []
        for part in parts:
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                email.plain_content = POP3.parse_email_content(part)
            elif content_type == 'text/html':
                email.html_content = POP3.parse_email_content(part)
            else:
                logging.info(f'Found content_type: {content_type}')
                content_disposition = part.get('Content-Disposition', '').strip()
                content_disposition = POP3.decode_header_value(content_disposition)
                if content_disposition.startswith('attachment;'):
                    logging.info(f'Found attachment: {content_disposition}')
                    content = part.get_payload(decode=True)
                    if content is None:
                        logging.warning(f'Attachment content is empty')
                        continue
                    attachment = gen_attachment(part.get_payload(decode=True), content_disposition=content_disposition)
                    att = self.save_attachment(attachment)
                    attachments.append(att)
                else:
                    logging.debug(f'Ignored content_type: {content_type}')
        if len(attachments) > 0:
            email.attachments = attachments
        return email

    def save_attachment(self, attachment: MIMEApplication) -> dict | None:
        filename = attachment.get_filename()
        if not filename:
            logging.warning('Attachment has no filename')
            return None

        ext = os.path.splitext(filename)[1]
        key = f'{str(uuid.uuid4())}{ext}'
        local_file = os.path.join(self.local_attachment_dir, key)
        with open(local_file, 'wb') as f:
            f.write(attachment.get_payload(decode=True))
        if self.oss:
            logging.info(f'Uploading attachment: {filename}, local_file: {local_file}, key: {key}')
            self.oss.upload(local_file, key)
        return {'oss_key': key, 'local_file': local_file, 'filename': filename, 'size': os.path.getsize(local_file)}

    def stat(self) -> Tuple[int, int]:
        msg_count, mailbox_size = self.pop3.stat()
        return msg_count, mailbox_size

    def count(self) -> int:
        count, _ = self.stat()
        return count

    def list(self) -> List:
        # emails: [b'1 82923', b'2 2184', ...]
        resp, emails, _ = self.pop3.list()
        if not resp.startswith(self.status_ok):
            raise Exception('List failed', str(resp))
        return emails

    def retr(self, index: int) -> Email | None:
        resp, lines, octets = self.pop3.retr(index)

        if not resp.startswith(self.status_ok):
            logging.error(f'Invalid resp: {resp}')
            return None
        logging.info(f'Email size: {octets}')

        try:
            msg_content = b'\r\n'.join(lines).decode('utf-8')
        except Exception as e:
            logging.warning(f'Decode message with utf-8 failed: {e}')
            logging.info('Try to find message charset...')
            charset = ''
            for line in lines:
                if b'Content-Type: ' in line:
                    line = line.decode('utf-8').lower()
                    for part in line.split(';'):
                        if 'charset' in part:
                            pos = part.find('charset=')
                            charset = part[pos + 8:].strip()
                            break
                if charset:
                    break
            if charset == '':
                logging.warning('Message charset not found and use utf-8')
                charset = 'utf-8'
            else:
                logging.info(f'Found message charset: {charset}')

            try:
                msg_content = b'\r\n'.join(lines).decode(charset, errors='ignore')
            except Exception as e:
                logging.error(f'Decode message failed: {e}')
                return None

        msg = Parser().parsestr(msg_content)
        email = self.parse_email(msg)
        email.size = octets
        email.raw = msg_content
        email.index = index
        return email

    @staticmethod
    def decode_header_value(value) -> str:
        # return u''.join(
        #     word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        #     for word, encoding in decode_header(value))

        result = []
        for s, charset in decode_header(value):
            if isinstance(s, bytes):
                encoding = charset
                try:
                    s = s.decode(encoding)
                except UnicodeDecodeError:
                    logging.warning(f"Decode header value with {encoding} failed: {s}")
                    try:
                        encoding = "utf-8"
                        logging.info(f"Try to decode header value with {encoding}")
                        s = s.decode(encoding)
                    except UnicodeDecodeError:
                        logging.warning(f"Decode header value with {encoding} failed: {s}")
                        try:
                            encoding = "gbk"
                            logging.info(f"Try to decode header value with {encoding}")
                            s = s.decode(encoding)
                        except UnicodeDecodeError:
                            logging.warning(f"Decode header value with gbk failed: {s}")
                            s = s.decode(charset, errors="ignore")

            result.append(s)
        return u''.join(result)
