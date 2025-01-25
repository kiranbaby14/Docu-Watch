import os
import json
from pathlib import Path
import logging
from openai import OpenAI
from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch,
)
from utils import read_text_file, save_json_string_to_file, extract_json_from_string
import re
from dotenv import load_dotenv
from neo4j_indexer import main as index_to_neo4j

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuring the OpenAI library with your API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Load the system instruction and extraction prompt
system_instruction = read_text_file("./prompts/system_prompt.txt")
extraction_prompt = read_text_file("./prompts/contract_extraction_prompt.txt")

# Configure the assistant
pdf_assistant = client.beta.assistants.create(
    model="gpt-4o-mini",
    description="An assistant to extract the information from contracts in PDF format.",
    tools=[{"type": "file_search"}],
    name="PDF assistant",
    instructions=system_instruction,
)


def process_pdf(pdf_path):
    """Process a single PDF file and return the extracted content"""
    logger.info(f"Processing {pdf_path}...")

    # Create thread
    thread = client.beta.threads.create()

    # Upload PDF file
    try:
        file = client.files.create(file=open(pdf_path, "rb"), purpose="assistants")
    except Exception as e:
        logger.error(f"Error uploading file {pdf_path}: {e}")
        return None

    # Create assistant message with attachment and extraction_prompt
    try:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            attachments=[
                Attachment(
                    file_id=file.id,
                    tools=[AttachmentToolFileSearch(type="file_search")],
                )
            ],
            content=extraction_prompt,
        )

        # Run thread
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=pdf_assistant.id, timeout=1000
        )

        if run.status != "completed":
            raise Exception("Run failed:", run.status)

        # Retrieve messages
        messages_cursor = client.beta.threads.messages.list(thread_id=thread.id)
        messages = [message for message in messages_cursor]

        # Return extracted content
        return messages[0].content[0].text.value

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return None


def process_directory(base_dir: str):
    """Process all PDFs in the directory structure: data/docusign_downloads/<account_dir>/<envelope_dir>"""
    base_path = Path(base_dir)
    docusign_path = base_path / "docusign_downloads"

    if not docusign_path.exists():
        logger.error(f"Directory not found: {docusign_path}")
        return

    # Create output directories if they don't exist
    output_base = base_path / "output"
    debug_base = base_path / "debug"
    output_base.mkdir(exist_ok=True)
    debug_base.mkdir(exist_ok=True)

    json_files_created = False

    # Process each account directory
    for account_dir in docusign_path.iterdir():
        if account_dir.is_dir():
            logger.info(f"Processing account directory: {account_dir}")

            # Create account-specific output directories
            account_output = output_base / account_dir.name
            account_debug = debug_base / account_dir.name
            account_output.mkdir(exist_ok=True)
            account_debug.mkdir(exist_ok=True)

            # Process each envelope directory
            for envelope_dir in account_dir.iterdir():
                if envelope_dir.is_dir():
                    logger.info(f"Processing envelope directory: {envelope_dir}")

                    # Create envelope-specific output directories
                    envelope_output = account_output / envelope_dir.name
                    envelope_debug = account_debug / envelope_dir.name
                    envelope_output.mkdir(exist_ok=True)
                    envelope_debug.mkdir(exist_ok=True)

                    # Find main contract PDF (not summary.pdf)
                    contract_pdfs = [f for f in envelope_dir.glob("*.pdf")]

                    if contract_pdfs:
                        pdf_path = contract_pdfs[0]
                        try:
                            # Extract content from PDF using the assistant
                            complete_response = process_pdf(pdf_path)

                            if complete_response:
                                # Log the complete response for debugging
                                debug_file = (
                                    envelope_debug
                                    / f"complete_response_{pdf_path.name}.json"
                                )
                                save_json_string_to_file(
                                    complete_response, str(debug_file)
                                )

                                # Try to load the response as valid JSON
                                try:
                                    contract_json = extract_json_from_string(
                                        complete_response
                                    )
                                    if contract_json:
                                        # Store as valid JSON
                                        json_string = json.dumps(
                                            contract_json, indent=4
                                        )
                                        output_file = (
                                            envelope_output / f"{pdf_path.name}.json"
                                        )
                                        save_json_string_to_file(
                                            json_string, str(output_file)
                                        )
                                        json_files_created = True
                                    else:
                                        logger.error(
                                            f"Failed to extract valid JSON from response for {pdf_path}"
                                        )
                                except json.JSONDecodeError as e:
                                    logger.error(
                                        f"Failed to decode JSON for {pdf_path}: {e}"
                                    )

                        except Exception as e:
                            logger.error(f"Error processing {pdf_path}: {e}")

    return json_files_created


def main():
    try:
        # Process all PDFs to JSON
        json_files_created = process_directory("./data")

        # If JSON files were created successfully, index them to Neo4j
        if json_files_created:
            logger.info("JSON files created successfully. Starting Neo4j indexing...")
            try:
                index_to_neo4j()
                logger.info("Neo4j indexing completed successfully")
            except Exception as e:
                logger.error(f"Error during Neo4j indexing: {e}")
        else:
            logger.warning("No JSON files were created. Skipping Neo4j indexing.")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
