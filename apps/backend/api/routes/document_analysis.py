from fastapi import APIRouter, Depends, BackgroundTasks
from services.envelope import EnvelopeService
from processors.document import DocumentProcessor
from core.oauth2 import oauth2_scheme
from apps.backend.core.settings import Settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{envelope_id}/{document_id}/process")
async def process_document(
    envelope_id: str,
    document_id: str,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(Settings),
):
    """Process document and store in graph database"""
    # Get document from DocuSign
    docusign_service = EnvelopeService(token)
    temp_file_path, content_type, filename = await docusign_service.get_document(
        envelope_id, document_id
    )

    # Initialize document processor
    processor = DocumentProcessor(
        settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD
    )

    # Process document in background
    background_tasks.add_task(
        processor.process_document,
        temp_file_path,
        {
            "document_id": document_id,
            "name": filename,
            "type": content_type,
            "envelope_id": envelope_id,
        },
    )

    return {"status": "processing", "document_id": document_id}


@router.get("/graph/{document_id}")
async def get_document_graph(
    document_id: str,
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(Settings),
):
    """Get document graph data"""
    with GraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    ) as driver:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(e:Entity)
                RETURN d, collect(e) as entities
            """,
                {"doc_id": document_id},
            )

            data = result.single()
            return {
                "document": dict(data["d"]),
                "entities": [dict(e) for e in data["entities"]],
            }
