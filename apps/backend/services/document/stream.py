from fastapi import HTTPException
from typing import Dict, Any, Union
from io import BytesIO
import hashlib


class DocumentService:
    @staticmethod
    def create_document_stream(content: Union[str, bytes, BytesIO]) -> BytesIO:
        """Create a BytesIO stream from document content"""
        try:
            if isinstance(content, BytesIO):
                # If it's already a BytesIO, return it after seeking to start
                content.seek(0)
                return content
            elif isinstance(content, bytes):
                # If it's bytes, create new BytesIO
                return BytesIO(content)
            elif isinstance(content, str):
                # If it's a string, encode to bytes
                return BytesIO(content.encode("utf-8"))
            elif hasattr(content, "read"):
                # If it's a file-like object, read it
                return BytesIO(content.read())
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create document stream: {str(e)}"
            )

    @staticmethod
    def validate_document_type(doc_type: str, filename: str) -> tuple[str, str]:
        """Validate and determine document content type and filename"""
        if doc_type in ["content", "summary"]:
            content_type = "application/pdf"
            if not filename.lower().endswith(".pdf"):
                filename = f"{filename}.pdf"
        elif doc_type == "zip":
            content_type = "application/zip"
            if not filename.lower().endswith(".zip"):
                filename = f"{filename}.zip"
        else:
            content_type = "application/octet-stream"

        return content_type, filename

    @staticmethod
    def calculate_document_hash(content: Union[str, bytes]) -> str:
        """Calculate SHA-256 hash of document content"""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def format_document_metadata(
        doc_info: Dict[str, Any], envelope_id: str
    ) -> Dict[str, Any]:
        """Format document metadata for API response"""
        return {
            "document_id": doc_info["document_id"],
            "name": doc_info["name"],
            "type": doc_info["type"],
            "uri": f"/api/documents/{envelope_id}/{doc_info['document_id']}/download",
            "size": doc_info.get("size"),
            "page_count": doc_info.get("page_count"),
            "file_extension": doc_info.get("file_extension"),
        }
