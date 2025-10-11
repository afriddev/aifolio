from abc import ABC, abstractmethod
from typing import List, Tuple


class DocServicesImpl(ABC):

    @abstractmethod
    def ExtractTextAndImagesFromPdf(self, docPath: str,images:bool) -> Tuple[str, List[str]]:
        pass

    @abstractmethod
    def UploadImageToFileServer(
        self, base64Str: str,name: str
    ) -> str | None:
        pass
