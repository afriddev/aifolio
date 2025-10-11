import fitz
import os
import base64
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
import requests

from implementations import DocServicesImpl


load_dotenv()


class DocServices(DocServicesImpl):
    def __init__(self):
        self.fileUrl = os.getenv("FILE_SERVER_URL", "")

    def ExtractTextAndImagesFromPdf(
        self, docPath: str, images: bool = False
    ) -> Tuple[str, List[str]]:
        pdfBytes = base64.b64decode(docPath)
        doc: Any = fitz.open(stream=pdfBytes, filetype="pdf")
        # doc: Any = fitz.open(docPath)
        imagesB64: List[str] = []
        imageCounter: int = 1
        finalTextParts: List[str] = []

        for _, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            pageItems: List[Tuple[str, float, str]] = []

            for block in blocks:
                if block["type"] == 0:
                    for line in block.get("lines", []):
                        y0 = line["bbox"][1]
                        lineText = " ".join(
                            span.get("text", "")
                            for span in line.get("spans", [])
                            if "text" in span
                        ).strip()
                        if lineText:
                            pageItems.append(("text", y0, lineText))
                elif block["type"] == 1:
                    y0 = block["bbox"][1]
                    imgId = f"image-{imageCounter}"
                    placeholder = f"<<{imgId}>>"

                    xref: Optional[int] = block.get("image") or block.get("number")
                    baseImage = None
                    if isinstance(xref, int) and xref > 0:
                        try:
                            baseImage = doc.extract_image(xref)
                        except Exception:
                            baseImage = None

                    if baseImage and baseImage.get("image"):
                        data = baseImage["image"]
                    else:
                        try:
                            rect = fitz.Rect(block["bbox"])
                            pix = page.get_pixmap(
                                matrix=fitz.Matrix(2, 2), clip=rect, alpha=False
                            )
                            data = pix.tobytes("png")
                        except Exception:
                            data = b""

                    b64Str = base64.b64encode(data).decode("utf-8") if data else ""
                    imagesB64.append(b64Str)
                    pageItems.append(("image", y0, placeholder if (images) else ""))
                    imageCounter += 1

            pageItems.sort(key=lambda x: x[1])
            for itemType, _, content in pageItems:
                if itemType == "text":
                    finalTextParts.append(content)
                else:
                    finalTextParts.append(f"\n{content}\n")

        return "\n".join(finalTextParts), imagesB64

    def UploadImageToFileServer(self, base64Str: str, name: str) -> str | None:
        try:
            url = f"{self.fileUrl}/save/{name}"
            response = requests.post(url, json={"data": base64Str})
            response.raise_for_status()
            tempServerResponse = response.json()
            if tempServerResponse.get("data") == "SUCCESS":
                return f"{self.fileUrl}/{tempServerResponse.get("name")}"
            else:
                return None
        except requests.RequestException as e:
            print(f"Error during request to file server: {e}")
            return None
