from abc import ABC, abstractmethod
from typing import List, Tuple
from models import QaCsvChunksResponseModel, YtVideoChunksResponseModel


class DocServicesImpl(ABC):

    @abstractmethod
    def ExtractTextAndImagesFromPdf(
        self, docPath: str, images: bool
    ) -> Tuple[str, List[str]]:
        pass

    @abstractmethod
    def UploadImageToFileServer(self, base64Str: str, name: str) -> str | None:
        pass

    @abstractmethod
    def ExtractQaFromText(self, text: str) -> QaCsvChunksResponseModel:
        pass

    @abstractmethod
    def ExtractChunksFromYtVideo(
        self, videoId: str, chunkSec: int = 30
    ) -> list[YtVideoChunksResponseModel]:
        pass
