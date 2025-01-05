from typing import Dict, Any, TypedDict, Sequence, Annotated
from fastapi import HTTPException
import PyPDF2
from neo4j import GraphDatabase
from datetime import datetime
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, Graph
from langgraph.graph.message import add_messages


# Define the state that will be passed between nodes
class ProcessingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    document_text: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]


class DocumentProcessor:
    def __init__(
        self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, gemini_api_key: str
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", temperature=0, google_api_key=gemini_api_key
        )
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> Graph:
        # Create the graph
        workflow = StateGraph(ProcessingState)

        # Add nodes for each processing step
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("store", self._store_node)

        # Define the edges
        workflow.add_edge("extract", "analyze")
        workflow.add_edge("analyze", "store")

        # Set the entry and exit points
        workflow.set_entry_point("extract")
        workflow.set_finish_point("store")

        return workflow.compile()

    async def _extract_node(self, state: ProcessingState) -> ProcessingState:
        """Node for text extraction"""
        text = self._extract_text(state["messages"][-1].content)
        return {
            "messages": state["messages"],
            "document_text": text,
            "metadata": state["metadata"],
        }

    async def _analyze_node(self, state: ProcessingState) -> ProcessingState:
        """Node for document analysis"""
        prompt = HumanMessage(
            content=f"""
        Analyze the following document text and provide a structured analysis with:
        1. A brief summary
        2. Key entities (people, organizations, locations, dates, etc.) with their context
        3. Main topics discussed
        4. Key relationships between entities

        Document text:
        {state["document_text"][:10000]}
        """
        )

        response = await self.model.ainvoke([prompt])
        analysis = json.loads(response.content)

        return {**state, "analysis": analysis}

    async def _store_node(self, state: ProcessingState) -> ProcessingState:
        """Node for storing in Neo4j"""
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
                    "doc_id": state["metadata"]["document_id"],
                    "name": state["metadata"]["name"],
                    "type": state["metadata"]["type"],
                    "created_date": datetime.now().isoformat(),
                    "content": state["document_text"],
                    "summary": state["analysis"]["summary"],
                },
            )

            # Store entities and relationships
            for entity in state["analysis"]["entities"]:
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
                        "doc_id": state["metadata"]["document_id"],
                        "text": entity["text"],
                        "type": entity["type"],
                        "context": entity["context"],
                        "confidence": entity.get("confidence", 1.0),
                    },
                )

        return state

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF"""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    async def process_document(self, file_path: str, metadata: Dict[str, Any]):
        """Process document using the LangGraph workflow"""
        try:
            initial_state = {
                "messages": [HumanMessage(content=file_path)],
                "metadata": metadata,
                "document_text": "",
                "analysis": {},
            }

            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "status": "success",
                "analysis": final_state["analysis"],
                "document_id": metadata["document_id"],
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to process document: {str(e)}"
            )

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
