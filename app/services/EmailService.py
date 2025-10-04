import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.implementations import EmailServiceImpl
from app.enums import EmailServiceResponseEnum
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService(EmailServiceImpl):
    def __init__(self):
        self.fromEmail = os.getenv("FROM_EMAIL_ADDRESS", "")
        self.fromEmailPasskey = os.getenv("FROM_EMAIL_PASSKEY", "")
        self.smtpGmail = "smtp.gmail.com"
        self.smtpPort = 465

    def GetMessageBody(self, toEmail: str, title: str, subject: str, body: str) -> str:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{title} <{self.fromEmail}>"
        msg["To"] = toEmail
        plainBody = (
            body.replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("<strong>", "")
            .replace("</strong>", "")
        )
        msg.attach(MIMEText(plainBody, "plain"))
        msg.attach(MIMEText(body, "html"))

        return msg.as_string()

    def SendMail(
        self, toEmail: str, title: str, subject: str, body: str
    ) -> EmailServiceResponseEnum:
        try:
            tempMessage = self.GetMessageBody(
                toEmail=toEmail, title=title, subject=subject, body=body
            )
            email_server = smtplib.SMTP_SSL(self.smtpGmail, self.smtpPort)
            try:
                email_server.login(self.fromEmail, self.fromEmailPasskey)
                email_server.sendmail(self.fromEmail, toEmail, tempMessage)

                return EmailServiceResponseEnum.SUCCESS
            except:
                return EmailServiceResponseEnum.UNAUTHORIZED

        except Exception as error:
            print(error)
            return EmailServiceResponseEnum.ERROR
