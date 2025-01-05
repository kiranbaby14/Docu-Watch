from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentBaseSchema(BaseModel):
    """Base document model with common fields"""

    document_id: str = Field(..., description="Unique identifier of the document")
    name: str = Field(..., description="Name of the document")
    type: str = Field(
        ..., description="Type of document (e.g., 'content', 'summary', 'zip')"
    )


class DocumentInfoSchema(DocumentBaseSchema):
    """Extended document information including URI and optional metadata"""

    uri: str = Field(..., description="URI to download the document")
    pages: Optional[int] = Field(None, description="Number of pages in the document")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")
    file_extension: Optional[str] = Field(None, description="File extension")


class EnvelopeDocumentsSchema(BaseModel):
    """Collection of documents within an envelope"""

    envelope_id: str = Field(
        ..., description="ID of the envelope containing the documents"
    )
    documents: List[DocumentInfoSchema] = Field(
        ..., description="List of documents in the envelope"
    )
    created_date: datetime = Field(
        ..., description="Date when the envelope was created"
    )
    status: str = Field(..., description="Current status of the envelope")

    class Config:
        """Pydantic config"""

        from_attributes = True  # Allows conversion from ORM objects
        json_encoders = {datetime: lambda v: v.isoformat()}
