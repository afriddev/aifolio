from abc import ABC, abstractmethod
from typing import List, Tuple


class DocServicesImpl(ABC):

    @abstractmethod
    def ExtractTextAndImagesFromPdf(self, docPath: str) -> Tuple[str, List[str]]:
        pass

    @abstractmethod
    async def UploadImageToBucket(
        self, base64Str: str, folder: str, extension: str
    ) -> str:
        pass
