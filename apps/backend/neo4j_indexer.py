from neo4j import GraphDatabase
import json
import os
from pathlib import Path
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

CREATE_GRAPH_STATEMENT = """
WITH $data AS data
WITH data.agreement as a

// Agreement node
MERGE (agreement:Agreement {contract_id: a.contract_id})
ON CREATE SET 
  agreement.name = a.agreement_name,
  agreement.effective_date = a.effective_date,
  agreement.expiration_date = a.expiration_date,
  agreement.agreement_type = a.agreement_type,
  agreement.renewal_term = a.renewal_term,
  agreement.most_favored_country = a.governing_law.most_favored_country

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
        "CREATE INDEX agreementContractId IF NOT EXISTS FOR (a:Agreement) ON (a.contract_id)",
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


def index_exists(driver, index_name):
    check_index_query = "SHOW INDEXES WHERE name = $index_name"
    result = driver.execute_query(check_index_query, {"index_name": index_name})
    return len(result.records) > 0


def create_full_text_indices(driver):
    for index_name, create_query in CREATE_FULL_TEXT_INDICES:
        try:
            if not index_exists(driver, index_name):
                logger.info(f"Creating index: {index_name}")
                driver.execute_query(create_query)
            else:
                logger.info(f"Index {index_name} already exists.")
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")


def process_json_files(base_dir: str, driver: GraphDatabase.driver):
    """Process JSON files from the new directory structure and load into Neo4j"""
    base_path = Path(base_dir)
    output_path = base_path / "output"

    if not output_path.exists():
        logger.error(f"Output directory not found: {output_path}")
        return

    contract_id = 1

    # Process each account directory
    for account_dir in output_path.iterdir():
        if account_dir.is_dir():
            logger.info(f"Processing account directory: {account_dir}")

            # Process each envelope directory
            for envelope_dir in account_dir.iterdir():
                if envelope_dir.is_dir():
                    logger.info(f"Processing envelope directory: {envelope_dir}")

                    # Process all JSON files in the envelope directory
                    json_files = list(envelope_dir.glob("*.json"))

                    for json_file in json_files:
                        try:
                            with open(json_file, "r") as file:
                                json_string = file.read()
                                json_data = json.loads(json_string)

                                # Add contract_id to the agreement
                                agreement = json_data["agreement"]
                                agreement["contract_id"] = contract_id

                                # Execute Neo4j statement
                                driver.execute_query(
                                    CREATE_GRAPH_STATEMENT, data=json_data
                                )
                                contract_id += 1
                                logger.info(f"Processed {json_file}")

                        except Exception as e:
                            logger.error(f"Error processing {json_file}: {e}")


def main():
    # Neo4j connection setup
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        # Process all JSON files
        process_json_files("./data", driver)

        # Create indices
        create_full_text_indices(driver)
        driver.execute_query(CREATE_VECTOR_INDEX_STATEMENT)

        # Generate embeddings
        logger.info("Generating Embeddings for Contract Excerpts...")
        driver.execute_query(EMBEDDINGS_STATEMENT, token=openai_api_key)

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
