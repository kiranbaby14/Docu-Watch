from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.chat_history import ChatHistory
from services.ai import ContractPlugin, ContractSearchService
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()


class ChatService:
    def __init__(self):
        self._openai_api_key = os.getenv("OPENAI_API_KEY")
        self._neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self._neo4j_password = os.getenv("NEO4J_PASSWORD")
        self._chat_histories: Dict[str, ChatHistory] = {}

    def get_or_create_history(self, user_id: str) -> ChatHistory:
        """Get existing chat history or create new one for user"""
        if user_id not in self._chat_histories:
            self._chat_histories[user_id] = ChatHistory()
        return self._chat_histories[user_id]

    def clear_history(self, user_id: str) -> None:
        """Clear chat history for a user"""
        if user_id in self._chat_histories:
            del self._chat_histories[user_id]

    async def initialize_kernel(self, account_id: str):
        """Initialize and configure the semantic kernel"""
        kernel = Kernel()

        # Initialize ContractSearchService
        contract_search_neo4j = ContractSearchService(
            uri=self._neo4j_uri,
            user=self._neo4j_user,
            pwd=self._neo4j_password,
            account_id=account_id,
        )

        # Add ContractPlugin to kernel
        kernel.add_plugin(
            ContractPlugin(contract_search_service=contract_search_neo4j),
            plugin_name="contract_search",
        )

        # Add OpenAI chat completion service
        kernel.add_service(
            OpenAIChatCompletion(
                ai_model_id="gpt-4o",
                api_key=self._openai_api_key,
                service_id="contract_search",
            )
        )

        # Configure function calling settings
        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id="contract_search"
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"included_plugins": ["contract_search"]}
        )

        return kernel, settings

    async def get_chat_response(self, message: str, user_id: str) -> str:
        """Process a chat message and return the response"""
        # Get or create chat history
        history = self.get_or_create_history(user_id)

        # Initialize kernel
        kernel, settings = await self.initialize_kernel(user_id)

        # Add user message to history
        history.add_user_message(message)

        # Get chat completion service
        chat_completion: OpenAIChatCompletion = kernel.get_service(
            type=ChatCompletionClientBase
        )

        # Get AI response
        result = (
            await chat_completion.get_chat_message_contents(
                chat_history=history,
                settings=settings,
                kernel=kernel,
                arguments=KernelArguments(),
            )
        )[0]

        # Add assistant's response to history
        history.add_message(result)

        return str(result)
