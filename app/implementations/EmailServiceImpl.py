from abc import ABC, abstractmethod
from app.enums import EmailServiceResponseEnum


class EmailServiceImpl(ABC):

    @abstractmethod
    def SendMail(
        self, toEmail: str, title: str, subject: str, body: str
    ) -> EmailServiceResponseEnum:
        pass

    @abstractmethod
    def GetMessageBody(self, toEmail: str, title: str, subject: str, body: str) -> str:
        pass
