import smtplib
from email.message import EmailMessage

from utils.config import get_settings


class EmailConfigurationError(RuntimeError):
    pass


class GmailEmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_password_reset_otp(self, recipient: str, otp: str) -> None:
        if not self.settings.gmail_user or not self.settings.gmail_app_password:
            raise EmailConfigurationError("Gmail OTP delivery is not configured.")

        message = EmailMessage()
        message["Subject"] = "Your CodeReviewAI password reset OTP"
        message["From"] = self.settings.gmail_user
        message["To"] = recipient
        message.set_content(
            f"Your CodeReviewAI password reset OTP is {otp}.\n\n"
            "This OTP expires in 10 minutes. If you did not request it, you can ignore this email."
        )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(self.settings.gmail_user, self.settings.gmail_app_password)
            smtp.send_message(message)
