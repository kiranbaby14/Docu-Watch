import os
import json
from pathlib import Path
import logging
from openai import OpenAI
from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch,
)
from dotenv import load_dotenv
from typing import Optional

from utils import read_text_file, save_json_string_to_file, extract_json_from_string
from ..neo4j.neo4j_indexer import Neo4jIndexer
from ...notification import WebhookService
from ...tracking import ProgressTracker, BatchProgressTracker
from schemas.webhook import ProcessingPhase, TerminateMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, webhook_service: Optional[WebhookService] = None):
        load_dotenv()

        self.webhook_service = webhook_service
        self.progress_tracker = ProgressTracker(
            webhook_service, phase=ProcessingPhase.PDF_TO_JSON
        )
        self.batch_tracker = None  # Will be initialized when we know total files

        # Initialize OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)

        # Load prompts
        # Get the directory where the current script is located
        current_dir = Path(__file__).parent
        # Navigate to prompts directory (adjust the path as needed)
        prompts_dir = current_dir.parent / "prompts"
        self.system_instruction = read_text_file(prompts_dir / "system_prompt.txt")
        self.extraction_prompt = read_text_file(
            prompts_dir / "contract_extraction_prompt.txt"
        )

        # Configure assistant
        self.pdf_assistant = self.client.beta.assistants.create(
            model="gpt-4o-mini",
            description="An assistant to extract the information from contracts in PDF format.",
            tools=[{"type": "file_search"}],
            name="PDF assistant",
            instructions=self.system_instruction,
        )

        # Initialize Neo4j indexer
        self.neo4j_indexer = Neo4jIndexer(webhook_service)

    async def process_pdf(self, envelope_id: str, pdf_path: str | Path) -> str | None:
        """Process a single PDF file and return the extracted content"""
        logger.info(f"Processing {pdf_path}...")

        try:
            # Create thread
            thread = self.client.beta.threads.create()

            # Upload PDF file
            file = self.client.files.create(
                file=open(pdf_path, "rb"), purpose="assistants"
            )

            # Update progress before starting
            await self.progress_tracker.update_document_progress(
                envelope_id, str(pdf_path)
            )

            # Create assistant message with attachment
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                attachments=[
                    Attachment(
                        file_id=file.id,
                        tools=[AttachmentToolFileSearch(type="file_search")],
                    )
                ],
                content=self.extraction_prompt,
            )

            # Run thread
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=self.pdf_assistant.id, timeout=1000
            )

            if run.status != "completed":
                await self.progress_tracker.mark_envelope_failed(
                    envelope_id, f"Run failed: {run.status}"
                )
                raise Exception("Run failed:", run.status)

            # Retrieve messages
            messages = list(self.client.beta.threads.messages.list(thread_id=thread.id))
            result = messages[0].content[0].text.value

            # Update batch progress
            if self.batch_tracker:
                await self.batch_tracker.update_envelope_progress(
                    envelope_id, str(pdf_path)
                )

            return result

        except Exception as e:
            await self.progress_tracker.mark_envelope_failed(envelope_id, str(e))
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None

    async def process_directory(self, base_dir: str | Path, account_id: str) -> bool:
        """Process PDFs in the specific account directory matching account_id"""
        base_path = Path(base_dir)
        docusign_path = base_path / "docusign_downloads"

        if not docusign_path.exists():
            logger.error(f"Directory not found: {docusign_path}")
            return False

        # Create output directories
        output_base = base_path / "output"
        debug_base = base_path / "debug"
        output_base.mkdir(exist_ok=True)
        debug_base.mkdir(exist_ok=True)

        json_files_created = False

        # Look for the specific account directory
        account_dir = docusign_path / account_id
        if not account_dir.exists() or not account_dir.is_dir():
            logger.error(f"Account directory not found for account_id: {account_id}")
            return False

        # Count total PDFs for batch tracking
        total_pdfs = sum(1 for _ in docusign_path.rglob("*.pdf"))
        self.batch_tracker = BatchProgressTracker(
            total_pdfs, self.webhook_service, phase=ProcessingPhase.PDF_TO_JSON
        )

        logger.info(f"Processing account directory: {account_dir}")

        # Create account directories
        account_output = output_base / account_dir.name
        account_debug = debug_base / account_dir.name
        account_output.mkdir(exist_ok=True)
        account_debug.mkdir(exist_ok=True)

        # Process envelopes in this account
        created = await self._process_account_envelopes(
            account_dir, account_output, account_debug
        )
        json_files_created |= created

        return json_files_created

    async def _process_account_envelopes(
        self,
        account_dir: Path,
        account_output: Path,
        account_debug: Path,
    ) -> bool:
        """Process all envelopes in an account directory"""
        json_files_created = False

        for envelope_dir in account_dir.iterdir():
            if not envelope_dir.is_dir():
                continue

            # Get envelope_id from directory name
            envelope_id = envelope_dir.name
            logger.info(f"Processing envelope directory: {envelope_dir}")

            # Create envelope directories
            envelope_output = account_output / envelope_dir.name
            envelope_debug = account_debug / envelope_dir.name
            envelope_output.mkdir(exist_ok=True)
            envelope_debug.mkdir(exist_ok=True)

            # Get PDF files once
            contract_pdfs = list(envelope_dir.glob("*.pdf"))
            total_pdfs_in_envelope = len(contract_pdfs)

            await self.progress_tracker.start_envelope(
                envelope_id, total_pdfs_in_envelope
            )
            await self.batch_tracker.register_envelope(
                envelope_id, total_pdfs_in_envelope
            )

            if contract_pdfs:
                created = await self._process_envelope_pdf(
                    envelope_id, contract_pdfs[0], envelope_output, envelope_debug
                )
                json_files_created |= created

                # Mark envelope complete
                await self.batch_tracker.complete_envelope(envelope_id)
                await self.progress_tracker.complete_envelope(
                    envelope_id, [str(p) for p in envelope_output.rglob("*.json")]
                )
        return json_files_created

    async def _process_envelope_pdf(
        self,
        envelope_id: str,
        pdf_path: Path,
        envelope_output: Path,
        envelope_debug: Path,
    ) -> bool:
        """Process a single PDF in an envelope directory"""
        try:
            complete_response = await self.process_pdf(envelope_id, pdf_path)
            if not complete_response:
                return False

            # Save debug response
            debug_file = envelope_debug / f"complete_response_{pdf_path.name}.json"
            save_json_string_to_file(complete_response, str(debug_file))

            # Process and save JSON
            contract_json = extract_json_from_string(complete_response)
            if not contract_json:
                logger.error(
                    f"Failed to extract valid JSON from response for {pdf_path}"
                )
                return False
            contract_json["agreement"]["email_subject"] = pdf_path.name.rstrip(".pdf")
            contract_json["agreement"]["envelope_id"] = envelope_id
            json_string = json.dumps(contract_json, indent=4)
            output_file = envelope_output / f"{pdf_path.name}.json"
            save_json_string_to_file(json_string, str(output_file))

            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for {pdf_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")

        return False

    async def run(self, account_id: str):
        """Main execution method"""
        try:
            # Process PDFs to JSON
            json_files_created = await self.process_directory("./data", account_id)

            # Index to Neo4j if files were created
            if json_files_created:
                logger.info(
                    "JSON files created successfully. Starting Neo4j indexing..."
                )
                try:
                    await self.neo4j_indexer.index_documents(
                        base_dir="./data", account_id=account_id
                    )
                    logger.info("Neo4j indexing completed successfully")
                except Exception as e:
                    logger.error(f"Error during Neo4j indexing: {e}")
            else:
                logger.warning("No JSON files were created. Skipping Neo4j indexing.")

        except Exception as e:
            logger.error(f"Application error: {e}")
            raise

    async def process_background(self, account_id: str):
        """Process PDFs asynchronously with webhook notifications"""
        try:
            await self.run(account_id)
            if self.webhook_service:
                webhook_termination_message = TerminateMessage(terminate=True)
                await self.webhook_service.send_notification(
                    webhook_termination_message.model_dump()
                )
        except Exception as e:
            error_msg = f"Error processing PDFs: {e}"
            logger.error(error_msg)
            # if self.webhook_service:
            #     await self.webhook_service.send_notification(
            #         {"status": "error", "message": error_msg}
            #     )
            raise


def main():
    processor = PDFProcessor()
    processor.run()


if __name__ == "__main__":
    main()
