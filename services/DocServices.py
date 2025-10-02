import fitz
import boto3
from botocore.exceptions import ClientError
import os
import base64
from typing import Any, List, Optional, Tuple, cast
from uuid import uuid4


from dotenv import load_dotenv


from implementations import DocServicesImpl


load_dotenv()


class DocServices(DocServicesImpl):
    def ExtractTextAndImagesFromPdf(self, docPath: str) -> Tuple[str, List[str]]:
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
                    pageItems.append(("image", y0, placeholder))
                    imageCounter += 1

            pageItems.sort(key=lambda x: x[1])
            for itemType, _, content in pageItems:
                if itemType == "text":
                    finalTextParts.append(content)
                else:
                    finalTextParts.append(f"\n{content}\n")

        return "\n".join(finalTextParts), imagesB64

    async def UploadImageToBucket(
        self, base64Str: str, folder: str, extension: str
    ) -> str:
        try:
            contentType = (
                "image/png"
                if extension.lower() == "png"
                else (
                    "application/pdf"
                    if (extension.lower() == "pdf")
                    else "text/csv" if (extension.lower() == "csv") else "image/jpeg"
                )
            )

            fileBytes: bytes = base64.b64decode(base64Str)
            ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
            SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
            REGION = os.getenv("AWS_REGION", "ap-south-1")
            BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "")

            s3 = cast(Any, boto3).client(
                "s3",
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY,
                region_name=REGION,
            )

            fileName: str = f"{folder}/{uuid4()}.{extension}"
            key = f"{folder}/{fileName}"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=fileBytes,
                ACL="public-read",
                ContentType=contentType,
            )
            publicUrl = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{key}"

            return publicUrl
        except ClientError as e:
            print("Error uploading to S3:", e)
            return ""
