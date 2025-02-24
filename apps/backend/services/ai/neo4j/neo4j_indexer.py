from neo4j import GraphDatabase
import json
import os
from pathlib import Path
import logging
from dotenv import load_dotenv
from typing import Optional


from schemas.webhook import ProcessingPhase
from ...notification import WebhookService
from ...tracking import ProgressTracker, BatchProgressTracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jIndexer:
    # Cypher
    CREATE_GRAPH_STATEMENT = """
    WITH $data AS data
    WITH data.agreement as a

    // Account node
    MERGE (account:Account {account_id: a.account_id})

    // Agreement node
    MERGE (agreement:Agreement {envelope_id: a.envelope_id})
    ON CREATE SET 
    agreement.name = a.agreement_name,
    agreement.effective_date = a.effective_date,
    agreement.expiration_date = a.expiration_date,
    agreement.agreement_type = a.agreement_type,
    agreement.renewal_term = a.renewal_term,
    agreement.most_favored_country = a.governing_law.most_favored_country

    // Create relationship between Account and Agreement
    MERGE (account)-[:HAS_AGREEMENT]->(agreement)

    // Governing law
    MERGE (gl_country:Country {name: a.governing_law.country})
    MERGE (agreement)-[gbl:GOVERNED_BY_LAW]->(gl_country)
    SET gbl.state = a.governing_law.state

    // Parties
    WITH a, agreement
    FOREACH (party IN a.parties |
    MERGE (p:Organization {name: party.name})
    MERGE (p)-[ipt:IS_PARTY_TO]->(agreement)
    SET ipt.role = party.role
    MERGE (country_of_incorporation:Country {name: party.incorporation_country})
    MERGE (p)-[incorporated:INCORPORATED_IN]->(country_of_incorporation)
    SET incorporated.state = party.incorporation_state
    )

    // Clauses and excerpts
    WITH a, agreement, [clause IN a.clauses WHERE clause.exists = true] AS valid_clauses
    FOREACH (clause IN valid_clauses |
    CREATE (cl:ContractClause {type: clause.clause_type})
    MERGE (agreement)-[clt:HAS_CLAUSE]->(cl)
    SET clt.type = clause.clause_type
    FOREACH (excerpt IN clause.excerpts |
        MERGE (cl)-[:HAS_EXCERPT]->(e:Excerpt {text: excerpt})
    )
    MERGE (clType:ClauseType{name: clause.clause_type})
    MERGE (cl)-[:HAS_TYPE]->(clType)
    )

    // Risks
    WITH a, agreement
    FOREACH (risk IN CASE WHEN a.risks IS NOT NULL THEN a.risks ELSE [] END |
    CREATE (r:Risk {
        risk_type: risk.risk_type,
        description: risk.description,
        level: risk.level,
        impact: risk.impact
    })
    MERGE (agreement)-[:HAS_RISK]->(r)
    )

    // Obligations
    WITH a, agreement
    FOREACH (obligation IN CASE WHEN a.obligations IS NOT NULL THEN a.obligations ELSE [] END |
    CREATE (o:Obligation {
        description: obligation.description,
        due_date: obligation.due_date,
        recurring: obligation.recurring,
        recurrence_pattern: obligation.recurrence_pattern,
        status: obligation.status,
        reminder_days: obligation.reminder_days
    })
    MERGE (agreement)-[:HAS_OBLIGATION]->(o)
    )
    """

    CREATE_VECTOR_INDEX_STATEMENT = """
    CREATE VECTOR INDEX excerpt_embedding IF NOT EXISTS 
        FOR (e:Excerpt) ON (e.embedding) 
        OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`:'cosine'}} 
    """

    CREATE_FULL_TEXT_INDICES = [
        (
            "excerptTextIndex",
            "CREATE FULLTEXT INDEX excerptTextIndex IF NOT EXISTS FOR (e:Excerpt) ON EACH [e.text]",
        ),
        (
            "agreementTypeTextIndex",
            "CREATE FULLTEXT INDEX agreementTypeTextIndex IF NOT EXISTS FOR (a:Agreement) ON EACH [a.agreement_type]",
        ),
        (
            "clauseTypeNameTextIndex",
            "CREATE FULLTEXT INDEX clauseTypeNameTextIndex IF NOT EXISTS FOR (ct:ClauseType) ON EACH [ct.name]",
        ),
        (
            "clauseNameTextIndex",
            "CREATE FULLTEXT INDEX contractClauseTypeTextIndex IF NOT EXISTS FOR (c:ContractClause) ON EACH [c.type]",
        ),
        (
            "organizationNameTextIndex",
            "CREATE FULLTEXT INDEX organizationNameTextIndex IF NOT EXISTS FOR (o:Organization) ON EACH [o.name]",
        ),
        (
            "contractIdIndex",
            "CREATE INDEX agreementContractId IF NOT EXISTS FOR (a:Agreement) ON (a.envelope_id)",
        ),
        (
            "riskTypeIndex",
            "CREATE INDEX riskTypeIndex IF NOT EXISTS FOR (r:Risk) ON (r.risk_type)",
        ),
        (
            "riskLevelIndex",
            "CREATE INDEX riskLevelIndex IF NOT EXISTS FOR (r:Risk) ON (r.level)",
        ),
        (
            "obligationStatusIndex",
            "CREATE INDEX obligationStatusIndex IF NOT EXISTS FOR (o:Obligation) ON (o.status)",
        ),
        (
            "obligationDueDateIndex",
            "CREATE INDEX obligationDueDateIndex IF NOT EXISTS FOR (o:Obligation) ON (o.due_date)",
        ),
    ]

    EMBEDDINGS_STATEMENT = """
    MATCH (e:Excerpt) 
    WHERE e.text is not null and e.embedding is null
    SET e.embedding = genai.vector.encode(e.text, "OpenAI", { 
                        token: $token, model: "text-embedding-3-small", dimensions: 1536
                    })
    """

    def __init__(self, webhook_service: Optional[WebhookService] = None):
        load_dotenv()

        self.webhook_service = webhook_service
        self.progress_tracker = ProgressTracker(
            webhook_service, phase=ProcessingPhase.JSON_TO_GRAPH
        )
        self.batch_tracker = None

        # Initialize connection parameters
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Initialize driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def _index_exists(self, index_name: str) -> bool:
        """Check if an index exists in Neo4j"""
        check_index_query = "SHOW INDEXES WHERE name = $index_name"
        result = self.driver.execute_query(
            check_index_query, {"index_name": index_name}
        )
        return len(result.records) > 0

    async def create_indices(self):
        """Create all necessary indices in Neo4j"""
        try:
            # Create full-text indices
            for index_name, create_query in self.CREATE_FULL_TEXT_INDICES:
                try:
                    if not self._index_exists(index_name):
                        logger.info(f"Creating index: {index_name}")
                        self.driver.execute_query(create_query)
                    else:
                        logger.info(f"Index {index_name} already exists.")
                except Exception as e:
                    logger.error(f"Error creating index {index_name}: {e}")

            # Create vector index
            self.driver.execute_query(self.CREATE_VECTOR_INDEX_STATEMENT)

        except Exception as e:
            logger.error(f"Error creating indices: {e}")
            raise

    async def process_json_files(self, base_dir: str | Path, account_id: str):
        """Process JSON files from directory structure and load into Neo4j"""
        base_path = Path(base_dir)
        output_path = base_path / "output"

        if not output_path.exists():
            logger.error(f"Output directory not found: {output_path}")
            return

        # Look for the specific account directory
        account_dir = output_path / account_id
        if not account_dir.exists() or not account_dir.is_dir():
            logger.error(f"Account directory not found for account_id: {account_id}")
            return

        # Count total JSON files
        total_files = sum(1 for _ in output_path.rglob("*.json"))
        self.batch_tracker = BatchProgressTracker(
            total_files, self.webhook_service, phase=ProcessingPhase.JSON_TO_GRAPH
        )

        # Process each account directory
        for envelope_dir in account_dir.iterdir():
            if envelope_dir.is_dir():
                # Register envelope with trackers
                envelope_id = envelope_dir.name
                total_jsons = len(list(envelope_dir.rglob("*.json")))
                await self.progress_tracker.start_envelope(envelope_id, total_jsons)
                await self.batch_tracker.register_envelope(envelope_id, total_jsons)

                if envelope_dir.is_dir():
                    await self._process_envelope_directory(envelope_id, envelope_dir)

                # Mark envelope complete
                await self.batch_tracker.complete_envelope(envelope_id)
                await self.progress_tracker.complete_envelope(
                    envelope_id, [str(p) for p in account_dir.rglob("*.json")]
                )

    async def _process_envelope_directory(self, envelope_id: str, envelope_dir: Path):
        """Process all JSON files in an envelope directory"""
        logger.info(f"Processing envelope directory: {envelope_dir}")

        json_files = list(envelope_dir.glob("*.json"))
        for json_file in json_files:
            try:
                await self._process_json_file(envelope_id, json_file)
            except Exception as e:
                await self.progress_tracker.mark_envelope_failed(
                    envelope_id, f"Error processing {json_file}: {str(e)}"
                )
                logger.error(f"Error processing {json_file}: {e}")

    async def _process_json_file(self, envelope_id: str, json_file: Path):
        """Process a single JSON file and load it into Neo4j"""
        try:
            # Update progress
            await self.progress_tracker.update_document_progress(
                envelope_id, str(json_file)
            )

            with open(json_file, "r") as file:
                json_string = file.read()
                json_data = json.loads(json_string)

                # Get the account_id from the directory structure
                # json_file.parent is envelope dir, json_file.parent.parent is account dir
                account_id = json_file.parent.parent.name

                # Add envelope_id to the agreement
                agreement = json_data["agreement"]
                agreement["envelope_id"] = envelope_id
                agreement["account_id"] = account_id

                # Execute Neo4j statement
                self.driver.execute_query(self.CREATE_GRAPH_STATEMENT, data=json_data)
                logger.info(f"Processed {json_file}")

            # Update batch progress
            if self.batch_tracker:
                await self.batch_tracker.update_envelope_progress(
                    envelope_id, str(json_file)
                )

        except Exception as e:
            await self.progress_tracker.mark_envelope_failed(envelope_id, str(e))
            raise

    async def generate_embeddings(self):
        """Generate embeddings for contract excerpts"""
        logger.info("Generating Embeddings for Contract Excerpts...")
        try:
            self.driver.execute_query(
                self.EMBEDDINGS_STATEMENT, token=self.openai_api_key
            )
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def index_documents(
        self, base_dir: str | Path = "./data", account_id: str = None
    ):
        """Main method to process documents and create indices"""
        try:
            # Process all JSON files
            await self.process_json_files(base_dir, account_id)

            # Create indices
            await self.create_indices()

            # Generate embeddings
            await self.generate_embeddings()

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise

    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()


def main():
    indexer = Neo4jIndexer()
    try:
        indexer.index_documents()
    finally:
        indexer.close()


if __name__ == "__main__":
    main()
