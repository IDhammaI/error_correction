"""SMTP 发信（注册验证码等）。"""

import logging
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_smtp_email(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    mail_from: str,
    use_tls: bool,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    if not host or not mail_from:
        raise ValueError("SMTP 未配置：需要 smtp_host 与 smtp_from")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = to_addr

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(mail_from, [to_addr], msg.as_string())

    logger.info("已发送邮件至 %s", to_addr)
