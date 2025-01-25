from docusign_esign import ApiClient, EnvelopesApi
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple


class EnvelopeService:
    def __init__(self, token: str, account_id: str, base_uri: str):
        self.token = token
        self.account_id = account_id
        self.base_uri = base_uri
        self.api_client = self._create_api_client()

    def _create_api_client(self):
        api_client = ApiClient()
        api_client.host = f"{self.base_uri}/restapi"
        api_client.set_default_header("Authorization", f"Bearer {self.token}")
        return api_client

    async def get_completed_envelopes(self) -> List[Dict[str, Any]]:
        """Get all completed envelopes"""
        try:
            envelope_api = EnvelopesApi(self.api_client)
            from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

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
                    if doc.type != "summary"  # Filter out summary documents
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
                    if doc.document_id == document_id and doc.type != "summary"
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
