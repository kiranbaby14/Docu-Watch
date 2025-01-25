import os
from typing import List, Dict, Any
import PyPDF2
from pdf2image import convert_from_path
from neo4j import GraphDatabase
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from PIL import Image
import io
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import base64

# Load environment variables from .env file
load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")


class ContractProcessor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        # Since Gemini 1.5 Pro handles both text and vision, we only need one model instance
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, temperature=0.1
        )

        # Common prefixes to remove during name normalization
        self.prefixes = {
            "mr",
            "mr.",
            "mrs",
            "mrs.",
            "ms",
            "ms.",
            "dr",
            "dr.",
            "prof",
            "prof.",
            "sir",
            "madam",
        }

    def normalize_name(self, name: str) -> str:
        """Simply remove prefixes from names"""
        if not name:
            return "Unknown Party"

        # Remove leading/trailing whitespace and convert to title case
        name = name.strip()

        # Check if the name starts with any prefix
        lower_name = name.lower()
        for prefix in self.prefixes:
            if lower_name.startswith(prefix + " "):
                name = name[len(prefix) :].strip()
                break

        return name if name else "Unknown Party"

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF using both text extraction and visual analysis
        Returns both extracted text and images for complex pages
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # Convert PDF pages to images
        # try:
        #     images = convert_from_path(pdf_path)
        #     logger.info(f"Successfully converted {len(images)} pages to images")
        # except Exception as e:
        #     logger.error(f"Error converting PDF to images: {e}")
        #     return None

        # Standard text extraction
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            page_data = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                full_text += text

                # If page contains tables (simple heuristic check)
                if self._likely_contains_table(text):
                    page_data.append(
                        {
                            "page_num": i,
                            "text": text,
                            # 'image': images[i],
                            "has_table": True,
                        }
                    )
                else:
                    page_data.append({"page_num": i, "text": text, "has_table": False})

        return {"full_text": full_text, "page_data": page_data}

    def _likely_contains_table(self, text: str) -> bool:
        """Simple heuristic to detect if text likely contains tables"""
        # Check for common table indicators
        table_indicators = [
            text.count("|") > 5,
            text.count("\t") > 5,
            text.count("  ") > 10,  # Multiple spaces
            any(line.count(",") > 3 for line in text.split("\n")),
        ]
        return any(table_indicators)

    def extract_contract_info(self, pdf_data: Dict) -> Dict:
        """Enhanced contract information extraction with dynamic field detection"""
        # Base contract info structure
        contract_info = {
            "type": None,
            "expiry_date": None,
            "parties": [],
            "key_terms": [],
            "value": None,
            "renewal_terms": None,
            "table_data": [],
            "additional_fields": {},  # For document-specific fields
        }

        # First pass: Extract standard fields
        text_prompt = """
        Extract the following standard information from the contract text. 
        If a field is not found, return null for that field:
        1. Contract Type
        2. Expiry Date (in YYYY-MM-DD format)
        3. Parties Involved
        4. Key Terms
        5. Contract Value
        6. Renewal Terms

        Format as JSON with these fields:
        {
            "type": string or null,
            "expiry_date": "YYYY-MM-DD" or null,
            "parties": [string array],
            "key_terms": [string array],
            "value": string or null,
            "renewal_terms": string or null
        }
        """

        try:
            text_response = self.llm.invoke(
                text_prompt + "\n\nContract Text:\n" + pdf_data["full_text"]
            )
            response_text = text_response.content.strip()
            if not response_text.startswith("{"):
                import re

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            base_info = json.loads(response_text)
            contract_info.update(base_info)
        except Exception as e:
            logger.error(f"Error processing standard fields: {e}")

        # Second pass: Identify and extract document-specific fields
        analysis_prompt = """
        Analyze this contract and identify any important fields specific to this type of document 
        that weren't covered in the standard extraction. Consider:

        IMPORTANT: ALL field names must be in snake_case format (lowercase words separated by underscores).
        Examples of correct field naming:
        - "annual_salary" (not "annualSalary" or "annualsalary")
        - "employee_notice_period" (not "employeeNoticePeriod" or "employeenoticeperiod")

        Consider extracting these types of fields (using snake_case names):
        1. Industry-specific terms
        2. Special conditions or requirements
        3. Performance metrics or SLAs
        4. Compliance requirements
        5. Specific deliverables
        6. Payment terms or schedules
        7. Territory or jurisdiction details
        8. Special rights or privileges
        9. Termination conditions
        10. Insurance requirements

        Format response as JSON with field name and value pairs:
        {
            "field_name": "extracted_value",
            ...
        }

        Only include fields that are actually present in the document and important.
        """

        try:
            analysis_response = self.llm.invoke(
                analysis_prompt + "\n\nContract Text:\n" + pdf_data["full_text"]
            )
            response_text = analysis_response.content.strip()
            if not response_text.startswith("{"):
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            additional_fields = json.loads(response_text)
            contract_info["additional_fields"] = additional_fields
        except Exception as e:
            logger.error(f"Error processing additional fields: {e}")

        # Process pages with tables (existing code)
        # for page in pdf_data['page_data']:
        #     if page.get('has_table') and page.get('image'):
        #         self._process_table_page(page, contract_info)

        return contract_info

    def _process_table_page(self, page: Dict, contract_info: Dict):
        """Process a page containing tables with enhanced table type detection"""
        vision_prompt = """
        Analyze this contract page image and extract any tabular data. 
        Identify the specific type of information in the table and pay special attention to:
        - Payment schedules and terms
        - Service level agreements (SLAs)
        - Pricing details
        - Delivery schedules
        - Performance metrics
        - Compliance requirements
        - Resource allocations
        - Milestone schedules
        
        Return a valid JSON object with this format:
        {
            "table_type": string describing the specific type of information,
            "headers": ["column1", "column2", ...],
            "rows": [
                {"column1": "value1", "column2": "value2", ...}
            ]
        }
        """

        try:
            img_byte_arr = io.BytesIO()
            page["image"].save(img_byte_arr, format="PNG")
            img_bytes = img_byte_arr.getvalue()

            parts = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "data": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
                            },
                        },
                    ],
                }
            ]

            vision_response = self.llm.invoke(parts)
            response_text = vision_response.content.strip()

            if not response_text.startswith("{"):
                import re

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)

            table_data = json.loads(response_text)
            contract_info["table_data"].append(
                {"page": page["page_num"], "data": table_data}
            )

        except Exception as e:
            logger.error(f"Error processing table on page {page['page_num']}: {e}")

    def create_graph_schema(self):
        """Create Neo4j schema for contracts"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.contract_id IS UNIQUE",
                "CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT table_id IF NOT EXISTS FOR (t:Table) REQUIRE t.table_id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.error(f"Error creating constraint: {e}")

    def store_contract_in_neo4j(
        self, contract_info: Dict, account_id: str, envelope_id: str
    ):
        """Enhanced storage with additional fields support"""
        with self.driver.session() as session:
            try:
                # Prepare base contract properties
                contract_props = {
                    "contract_id": envelope_id,
                    "account_id": account_id,
                    "type": contract_info.get("type") or "Unknown",
                    "expiry_date": contract_info.get("expiry_date"),
                    "value": contract_info.get("value"),
                    "renewal_terms": contract_info.get("renewal_terms"),
                }

                # Add additional fields to properties
                for field, value in contract_info.get("additional_fields", {}).items():
                    # Convert field name to valid property name
                    field_name = field.lower().replace(" ", "_")
                    contract_props[field_name] = value

                # Remove None values
                contract_props = {
                    k: v for k, v in contract_props.items() if v is not None
                }

                # Normalize party names
                parties = contract_info.get("parties", []) or ["Unknown Party"]
                normalized_parties = [
                    self.normalize_name(party)
                    for party in parties
                    if isinstance(party, str)
                ]

                # Create contract node with all properties
                result = session.run(
                    """
                    MERGE (c:Contract {contract_id: $contract_id})
                    SET c += $props
                    SET c.display_name = c.contract_id
                    WITH c
                    UNWIND $parties as party
                    MERGE (p:Party {name: party})
                    MERGE (p)-[:INVOLVED_IN]->(c)
                    RETURN c
                    """,
                    contract_id=envelope_id,
                    props=contract_props,
                    parties=normalized_parties,
                )

                # Store table data
                self._store_table_data(session, contract_info, envelope_id)

                logger.info(
                    f"Successfully stored enhanced contract {envelope_id} in Neo4j"
                )
            except Exception as e:
                logger.error(f"Error storing contract in Neo4j: {e}")
                logger.debug(f"Contract info: {json.dumps(contract_info, indent=2)}")

    def _store_table_data(self, session, contract_info: Dict, envelope_id: str):
        """Helper method to store table data"""
        for table in contract_info.get("table_data", []):
            if not table.get("data"):
                continue

            table_id = f"{envelope_id}_page_{table['page']}"
            session.run(
                """
                MATCH (c:Contract {contract_id: $contract_id})
                MERGE (t:Table {table_id: $table_id})
                SET t += $table_props
                MERGE (t)-[:BELONGS_TO]->(c)
                WITH t
                UNWIND $rows as row
                CREATE (r:TableRow {data: row})
                CREATE (r)-[:PART_OF]->(t)
                """,
                contract_id=envelope_id,
                table_id=table_id,
                table_props={
                    "page_number": table["page"],
                    "table_type": table["data"].get("table_type", "unknown"),
                    "headers": table["data"].get("headers", []),
                },
                rows=table["data"].get("rows", []),
            )


from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END


# Define the state schema as a TypedDict
class GraphState(TypedDict):
    question: str
    result: str
    response: Optional[str]


class ContractGraphRAG:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, temperature=0.1
        )

        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def setup_graph(self):
        """Set up LangGraph for contract querying"""

        def query_neo4j(state: GraphState) -> GraphState:
            """Query Neo4j based on the user's question"""
            question = state["question"]

            # Generate Cypher query using LLM
            cypher_prompt = f"""
            Generate a Cypher query to answer this question: {question}
            The graph schema has:
            - Nodes: Contract (contract_id, account_id, type, expiry_date, value, renewal_terms)
            - Nodes: Party (name)
            - Nodes: Table (table_id, page_number, table_type, headers)
            - Nodes: TableRow (data)
            - Relationships: 
                (Party)-[:INVOLVED_IN]->(Contract)
                (Table)-[:BELONGS_TO]->(Contract)
                (TableRow)-[:PART_OF]->(Table)
            
            Return only the raw Cypher query with no markdown formatting or explanation.
            The query should not be wrapped in ```cypher``` tags.
            Example format:
            MATCH (n:Node) RETURN n
            """

            try:
                cypher_response = self.llm.invoke(cypher_prompt)
                # Clean the response to remove any markdown formatting
                cypher_query = cypher_response.content.strip()

                # Remove markdown code block if present
                if cypher_query.startswith("```"):
                    cypher_query = cypher_query.split("\n", 1)[1]  # Remove first line
                if cypher_query.endswith("```"):
                    cypher_query = cypher_query.rsplit("\n", 1)[0]  # Remove last line
                cypher_query = (
                    cypher_query.replace("```cypher", "").replace("```", "").strip()
                )

                # Execute query
                with self.driver.session() as session:
                    result = session.run(cypher_query)
                    result_data = str(result.data())
                    return {
                        "question": question,
                        "result": result_data,
                        "response": None,
                    }
            except Exception as e:
                logger.error(f"Error in query_neo4j: {e}")
                logger.error(
                    f"Attempted query: {cypher_query if 'cypher_query' in locals() else 'No query generated'}"
                )
                return {"question": question, "result": "[]", "response": None}

        def generate_response(state: GraphState) -> GraphState:
            """Generate natural language response using LLM"""
            question = state["question"]
            neo4j_result = state["result"]

            response_prompt = f"""
            Question: {question}
            Data from database: {neo4j_result}
            
            Generate a natural language response to the question using the data.
            Be concise but informative. If the data is empty, indicate that no 
            relevant information was found.
            """

            try:
                response = self.llm.invoke(response_prompt)
                return {
                    "question": question,
                    "result": neo4j_result,
                    "response": response.content,
                }
            except Exception as e:
                logger.error(f"Error in generate_response: {e}")
                return {
                    "question": question,
                    "result": neo4j_result,
                    "response": "I apologize, but I encountered an error processing your question.",
                }

        # Create LangGraph with proper typing
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("query_database", query_neo4j)
        workflow.add_node("generate_response", generate_response)

        # Add edges - simplified edge definition
        workflow.add_edge("query_database", "generate_response")

        # Set entry and finish points
        workflow.set_entry_point("query_database")
        workflow.set_finish_point("generate_response")

        return workflow.compile()


def process_directory(base_dir: str):
    """Process all PDFs in the directory structure: data/docusign_downloads/<account_dir>/<envelope_dir>"""
    contract_processor = ContractProcessor()
    contract_processor.create_graph_schema()

    base_path = Path(base_dir)
    docusign_path = base_path / "docusign_downloads"

    if not docusign_path.exists():
        logger.error(f"Directory not found: {docusign_path}")
        return

    # Process each account directory
    for account_dir in docusign_path.iterdir():
        if account_dir.is_dir():
            logger.info(f"Processing account directory: {account_dir}")

            # Process each envelope directory
            for envelope_dir in account_dir.iterdir():
                if envelope_dir.is_dir():
                    logger.info(f"Processing envelope directory: {envelope_dir}")

                    # Find main contract PDF (not summary.pdf)
                    contract_pdfs = [f for f in envelope_dir.glob("*.pdf")]
                    # contract_pdfs = [f for f in envelope_dir.glob('*.pdf')
                    #                if f.name != 'summary.pdf']

                    if contract_pdfs:
                        pdf_path = contract_pdfs[0]
                        try:
                            # Process contract
                            pdf_data = contract_processor.process_pdf(str(pdf_path))
                            if pdf_data:
                                contract_info = (
                                    contract_processor.extract_contract_info(pdf_data)
                                )
                                contract_processor.store_contract_in_neo4j(
                                    contract_info, account_dir.name, envelope_dir.name
                                )
                        except Exception as e:
                            logger.error(f"Error processing {pdf_path}: {e}")


import traceback
import sys


def main():
    # Set the base directory directly instead of using command line arguments
    base_dir = "./data"

    try:
        # Process all contracts
        process_directory(base_dir)

        # Initialize GraphRAG
        rag = ContractGraphRAG()
        graph = rag.setup_graph()

        # Interactive query loop
        while True:
            try:
                question = input("\nEnter your question (or 'quit' to exit): ")
                if question.lower() in ["quit", "exit"]:
                    break

                # Initialize the state with the question
                initial_state = {"question": question, "result": "", "response": None}

                # Run the graph
                final_state = graph.invoke(initial_state)

                # Print the response
                if final_state and "response" in final_state:
                    print("\nResponse:", final_state["response"])
                else:
                    print("\nNo response generated.")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                print("\nError details:", str(e))
                print("\nFull traceback:")
                traceback.print_exc(file=sys.stdout)
                print("\nTrying to continue...\n")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print("\nCritical error occurred:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    finally:
        # Clean up Neo4j connection
        try:
            if "contract_processor" in locals():
                contract_processor = ContractProcessor()
                contract_processor.driver.close()
                print("\nCleaned up Neo4j connection.")
        except Exception as cleanup_error:
            print(f"\nError during cleanup: {str(cleanup_error)}")


if __name__ == "__main__":
    main()
