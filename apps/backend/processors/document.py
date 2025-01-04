from fastapi import HTTPException
from typing import Dict, Any
import PyPDF2
from neo4j import GraphDatabase
import google.generativeai as genai
from datetime import datetime
import json


class DocumentProcessor:
    def __init__(
        self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, gemini_api_key: str
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    async def process_document(self, file_path: str, metadata: Dict[str, Any]):
        """Process document using Gemini and store in graph database"""
        try:
            # Extract text from PDF
            text = self._extract_text(file_path)

            # Use Gemini to analyze the document
            analysis = await self._analyze_with_gemini(text)

            # Store in Neo4j
            with self.driver.session() as session:
                # Create document node
                session.run(
                    """
                    CREATE (d:Document {
                        id: $doc_id,
                        name: $name,
                        type: $type,
                        created_date: $created_date,
                        content: $content,
                        summary: $summary
                    })
                """,
                    {
                        "doc_id": metadata["document_id"],
                        "name": metadata["name"],
                        "type": metadata["type"],
                        "created_date": datetime.now().isoformat(),
                        "content": text,
                        "summary": analysis["summary"],
                    },
                )

                # Create entity nodes and relationships
                for entity in analysis["entities"]:
                    session.run(
                        """
                        MATCH (d:Document {id: $doc_id})
                        MERGE (e:Entity {
                            text: $text,
                            type: $type,
                            context: $context
                        })
                        CREATE (d)-[:CONTAINS {confidence: $confidence}]->(e)
                    """,
                        {
                            "doc_id": metadata["document_id"],
                            "text": entity["text"],
                            "type": entity["type"],
                            "context": entity["context"],
                            "confidence": entity.get("confidence", 1.0),
                        },
                    )

                # Create topic nodes
                for topic in analysis["topics"]:
                    session.run(
                        """
                        MATCH (d:Document {id: $doc_id})
                        MERGE (t:Topic {name: $name})
                        CREATE (d)-[:ABOUT]->(t)
                    """,
                        {"doc_id": metadata["document_id"], "name": topic},
                    )

            return {
                "status": "success",
                "analysis": analysis,
                "document_id": metadata["document_id"],
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to process document: {str(e)}"
            )

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF"""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    async def _analyze_with_gemini(self, text: str) -> Dict:
        """Analyze document content using Gemini"""

        # Prompt for comprehensive document analysis
        prompt = f"""
        Analyze the following document text and provide a structured analysis with:
        1. A brief summary
        2. Key entities (people, organizations, locations, dates, etc.) with their context
        3. Main topics discussed
        4. Key relationships between entities
        
        Return the analysis in the following JSON format:
        {{
            "summary": "brief summary",
            "entities": [
                {{
                    "text": "entity text",
                    "type": "entity type",
                    "context": "brief context",
                    "confidence": confidence_score
                }}
            ],
            "topics": ["topic1", "topic2"],
            "relationships": [
                {{
                    "source": "entity1",
                    "target": "entity2",
                    "relationship": "relationship type",
                    "context": "relationship context"
                }}
            ]
        }}

        Document text:
        {text[:10000]}  # Limiting text length for API constraints
        """

        response = await self.model.generate_content(prompt)
        return json.loads(response.text)

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
