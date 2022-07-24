from email.mime.application import MIMEApplication


def gen_attachment(content: bytes | str, filename: str = '', content_disposition: str = '') -> MIMEApplication:
    attachment = MIMEApplication(content, Name=filename)
    if content_disposition:
        attachment['Content-Disposition'] = content_disposition
    else:
        attachment.add_header('Content-Disposition',
                              'attachment', filename=filename)
    return attachment
