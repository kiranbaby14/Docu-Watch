from docusign_esign import ApiClient, EnvelopesApi
from fastapi import HTTPException
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from core.config import CONFIG


class DocuSignService:
    def __init__(self, token: str):
        self.token = token
        self.api_client = None
        self.account_id = None
        self.base_uri = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize DocuSign client and get account information"""
        try:
            # Get user info
            headers = {"Authorization": f"Bearer {self.token}"}
            user_info = requests.get(
                f"{CONFIG['authorization_server']}/oauth/userinfo", headers=headers
            ).json()

            if not user_info.get("accounts"):
                raise HTTPException(
                    status_code=400, detail="No DocuSign accounts found for this user"
                )

            self.account_id = user_info["accounts"][0]["account_id"]
            self.base_uri = user_info["accounts"][0]["base_uri"]

            # Initialize API client
            self.api_client = ApiClient()
            self.api_client.host = f"{self.base_uri}/restapi"
            self.api_client.set_default_header("Authorization", f"Bearer {self.token}")

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize DocuSign client: {str(e)}",
            )

    async def get_completed_envelopes(self) -> List[Dict[str, Any]]:
        """Get all completed envelopes"""
        try:
            envelope_api = EnvelopesApi(self.api_client)
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

            response = envelope_api.list_status_changes(
                account_id=self.account_id,
                from_date=from_date,
                from_to_status="completed",
                status="completed",
            )

            return [
                {
                    "envelope_id": envelope.envelope_id,
                    "status": envelope.status,
                    "subject": envelope.email_subject or "",
                    "sent_date": envelope.sent_date_time or "",
                    "last_modified": envelope.last_modified_date_time or "",
                }
                for envelope in (response.envelopes or [])
            ]

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get envelopes: {str(e)}"
            )

    async def get_envelope_documents(self, envelope_id: str) -> Dict[str, Any]:
        """Get list of documents in an envelope"""
        try:
            envelope_api = EnvelopesApi(self.api_client)

            # Get documents list
            docs_list = envelope_api.list_documents(
                account_id=self.account_id, envelope_id=envelope_id
            )

            # Get envelope info
            envelope = envelope_api.get_envelope(
                account_id=self.account_id, envelope_id=envelope_id
            )

            return {
                "envelope_id": envelope_id,
                "documents": [
                    {
                        "document_id": doc.document_id,
                        "name": doc.name,
                        "type": doc.type,
                        "uri": f"/api/envelopes/{envelope_id}/documents/{doc.document_id}/download",
                    }
                    for doc in docs_list.envelope_documents
                ],
                "created_date": envelope.created_date_time,
                "status": envelope.status,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get envelope documents: {str(e)}"
            )

    async def get_document(
        self, envelope_id: str, document_id: str
    ) -> Tuple[str, str, str]:
        """
        Get document content and metadata
        Returns:
            Tuple containing:
            - temp file path
            - content type
            - filename
        """
        try:
            envelope_api = EnvelopesApi(self.api_client)

            # Get document info first
            docs_list = envelope_api.list_documents(
                account_id=self.account_id, envelope_id=envelope_id
            )

            doc_info = next(
                (
                    doc
                    for doc in docs_list.envelope_documents
                    if doc.document_id == document_id
                ),
                None,
            )

            if not doc_info:
                raise HTTPException(status_code=404, detail="Document not found")

            # Get the temp file path from DocuSign
            temp_file_path = envelope_api.get_document(
                account_id=self.account_id,
                envelope_id=envelope_id,
                document_id=document_id,
            )

            # Determine content type and filename
            doc_name = doc_info.name
            has_pdf_suffix = doc_name.lower().endswith(".pdf")

            if doc_info.type == "content" or doc_info.type == "summary":
                content_type = "application/pdf"
                if not has_pdf_suffix:
                    doc_name += ".pdf"
            elif doc_info.type == "zip":
                content_type = "application/zip"
                if not doc_name.lower().endswith(".zip"):
                    doc_name += ".zip"
            else:
                content_type = "application/octet-stream"

            return temp_file_path, content_type, doc_name

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get document: {str(e)}"
            )
