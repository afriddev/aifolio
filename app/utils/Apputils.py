from app.implementations import AppUtilsImpl
import tiktoken


class AppUtils(AppUtilsImpl):

    def CountTokens(self, text: str) -> int:
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
