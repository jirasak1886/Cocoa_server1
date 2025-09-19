import smtplib, os, logging
from email.mime.text import MIMEText
from email.header import Header

logger = logging.getLogger(__name__)

def _smtp_settings():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587") or "587")
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    from_addr = os.getenv("FROM_ADDR", user)
    return host, port, user, pwd, from_addr

def send_email(to_addresses, subject, body, html=False):
    host, port, user, pwd, from_addr = _smtp_settings()
    msg = MIMEText(body, "html" if html else "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = from_addr
    msg["To"] = ", ".join([to_addresses] if isinstance(to_addresses, str) else to_addresses)

    try:
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo()
            s.starttls()
            s.login(user, pwd)
            s.sendmail(from_addr, [to_addresses], msg.as_string())
        logger.info(f"📧 Email sent to {to_addresses}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False

