from typing import List, Annotated, Tuple
from schemas import Agreement, ClauseType, Risk, Obligation, ContractClause
from semantic_kernel.functions import kernel_function
from .contract_service import ContractSearchService


class ContractPlugin:

    def __init__(self, contract_search_service: ContractSearchService):
        self.contract_search_service = contract_search_service

    @kernel_function
    async def get_contract(
        self, envelope_id: int
    ) -> Annotated[Agreement, "A contract"]:
        """Gets details about a contract with the given id."""
        return await self.contract_search_service.get_contract(envelope_id)

    @kernel_function
    async def get_contracts(
        self, organization_name: str
    ) -> Annotated[List[Agreement], "A list of contracts"]:
        """Gets basic details about all contracts where one of the parties has a name similar to the given organization name."""
        return await self.contract_search_service.get_contracts(organization_name)

    @kernel_function
    async def get_contracts_without_clause(
        self, clause_type: ClauseType
    ) -> Annotated[List[Agreement], "A list of contracts"]:
        """Gets basic details from contracts without a clause of the given type."""
        return await self.contract_search_service.get_contracts_without_clause(
            clause_type=clause_type
        )

    @kernel_function
    async def get_contracts_with_clause_type(
        self, clause_type: ClauseType
    ) -> Annotated[List[Agreement], "A list of contracts"]:
        """Gets basic details from contracts with a clause of the given type."""
        return await self.contract_search_service.get_contracts_with_clause_type(
            clause_type=clause_type
        )

    @kernel_function
    async def get_contracts_similar_text(
        self, clause_text: str
    ) -> Annotated[
        List[Agreement], "A list of contracts with similar text in one of their clauses"
    ]:
        """Gets basic details from contracts having semantically similar text in one of their clauses to the to the 'clause_text' provided."""
        return await self.contract_search_service.get_contracts_similar_text(
            clause_text=clause_text
        )

    @kernel_function
    async def answer_aggregation_question(
        self, user_question: str
    ) -> Annotated[str, "An answer to user_question"]:
        """Answer obtained by turning user_question into a CYPHER query"""
        return await self.contract_search_service.answer_aggregation_question(
            user_question=user_question
        )

    @kernel_function
    async def get_contract_excerpts(
        self, envelope_id: int
    ) -> Annotated[Agreement, "A contract"]:
        """Gets basic contract details and its excerpts."""
        return await self.contract_search_service.get_contract_excerpts(
            envelope_id=envelope_id
        )

    @kernel_function
    async def get_high_risk_clauses(
        self,
    ) -> Annotated[
        List[Tuple[ContractClause, Risk]], "High risk clauses across all contracts"
    ]:
        """Gets all contract clauses that have been marked as high risk."""
        return await self.contract_search_service.get_high_risk_clauses()

    @kernel_function
    async def get_contract_risks(
        self, envelope_id: int
    ) -> Annotated[List[Risk], "Risks for a specific contract"]:
        """Gets all risks associated with a specific contract."""
        return await self.contract_search_service.get_contract_risks(envelope_id)

    @kernel_function
    async def compare_contracts_by_party(
        self, party_name: str
    ) -> Annotated[dict, "Analysis of contracts by party"]:
        """Analyzes patterns in clauses across all contracts with a specific party."""
        return await self.contract_search_service.compare_contracts_by_party(party_name)

    @kernel_function
    async def analyze_industry_patterns(
        self, industry: str
    ) -> Annotated[dict, "Analysis of contracts by industry"]:
        """Analyzes common clause patterns within an industry."""
        return await self.contract_search_service.analyze_industry_patterns(industry)

    @kernel_function
    async def get_upcoming_obligations(
        self, days_ahead: int = 30
    ) -> Annotated[List[Obligation], "Upcoming obligations"]:
        """Gets all obligations due within the specified number of days."""
        return await self.contract_search_service.get_upcoming_obligations(days_ahead)

    @kernel_function
    async def track_recurring_obligations(
        self,
    ) -> Annotated[List[Obligation], "Recurring obligations"]:
        """Gets all recurring obligations."""
        return await self.contract_search_service.track_recurring_obligations()
