import smtplib
from decouple import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_SERVER = config("SMTP_SERVER")
SMTP_PORT = config("SMTP_PORT")
EMAIL_ADDRESS = config("EMAIL_ADDRESS")
EMAIL_PASSWORD = config("EMAIL_PASSWORD")


def send(to: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to, message.as_string())
            print("sended")
    except Exception as e:
        print("Error", e)
