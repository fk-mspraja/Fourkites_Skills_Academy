"""Main Ocean Debugging Agent implementation"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .models.state import InvestigationState, StepResult
from .models.evidence import Evidence
from .models.ticket import SalesforceTicket, TicketIdentifiers
from .models.result import InvestigationResult, RootCauseCategory

from .clients.salesforce_client import SalesforceClient
from .clients.redshift_client import RedshiftClient
from .clients.clickhouse_client import ClickHouseClient
from .clients.jt_client import JustTransformClient
from .clients.tracking_api_client import TrackingAPIClient
from .clients.super_api_client import SuperApiClient

from .task_executor import ParallelTaskExecutor, Task
from .decision_engine import DecisionEngine

from .utils.config import Config
from .utils.llm_client import LLMClient
from .utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class OceanDebuggingAgent:
    """
    Main agent for investigating ocean shipment tracking issues.

    Implements the investigation loop:
    1. Get ticket from Salesforce
    2. Extract identifiers using LLM
    3. Initialize investigation state
    4. Execute investigation steps in parallel
    5. Evaluate decisions against collected evidence
    6. Determine root cause or request human input
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._clients: Optional[Dict[str, Any]] = None
        self._executor: Optional[ParallelTaskExecutor] = None
        self._decision_engine: Optional[DecisionEngine] = None
        self._llm_client: Optional[LLMClient] = None

    @property
    def clients(self) -> Dict[str, Any]:
        """Lazy initialization of data clients"""
        if self._clients is None:
            self._clients = self._init_clients()
        return self._clients

    @property
    def executor(self) -> ParallelTaskExecutor:
        """Lazy initialization of task executor"""
        if self._executor is None:
            self._executor = ParallelTaskExecutor(
                clients=self.clients,
                max_parallel=self.config.max_parallel_tasks,
                default_timeout=self.config.default_timeout
            )
        return self._executor

    @property
    def decision_engine(self) -> DecisionEngine:
        """Lazy initialization of decision engine"""
        if self._decision_engine is None:
            self._decision_engine = DecisionEngine()
        return self._decision_engine

    @property
    def llm_client(self) -> LLMClient:
        """Lazy initialization of LLM client"""
        if self._llm_client is None:
            self._llm_client = LLMClient(self.config.llm)
        return self._llm_client

    def _init_clients(self) -> Dict[str, Any]:
        """Initialize all data source clients"""
        clients = {}

        # Salesforce
        if self.config.salesforce.is_configured():
            clients["salesforce"] = SalesforceClient(self.config.salesforce)
        else:
            logger.warning("Salesforce not configured")

        # Redshift
        if self.config.redshift.is_configured():
            clients["redshift"] = RedshiftClient(self.config.redshift)
        else:
            logger.warning("Redshift not configured")

        # ClickHouse
        if self.config.clickhouse.is_configured():
            clients["clickhouse"] = ClickHouseClient(self.config.clickhouse)
        else:
            logger.warning("ClickHouse not configured")

        # Just Transform
        if self.config.justtransform.is_configured():
            clients["justtransform"] = JustTransformClient(self.config.justtransform)
        else:
            logger.warning("Just Transform not configured")

        # Tracking API
        if self.config.tracking_api.is_configured():
            clients["tracking_api"] = TrackingAPIClient(self.config.tracking_api)
        else:
            logger.warning("Tracking API not configured")

        # Super API
        if self.config.super_api.is_configured():
            clients["super_api"] = SuperApiClient(self.config.super_api)
        else:
            logger.warning("Super API not configured")

        return clients

    async def investigate(
        self,
        case_number: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> InvestigationResult:
        """
        Run a full investigation for a Salesforce case.

        Args:
            case_number: Salesforce case number
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            InvestigationResult with root cause and recommendations
        """
        start_time = datetime.utcnow()

        def update_progress(pct: int):
            if progress_callback:
                progress_callback(pct)

        try:
            # Step 1: Get ticket from Salesforce (10%)
            logger.info(f"Starting investigation for case: {case_number}")
            update_progress(5)

            ticket = await self._get_ticket(case_number)
            update_progress(10)

            # Step 2: Extract identifiers using LLM (20%)
            logger.info("Extracting identifiers from ticket")
            identifiers = await self._extract_identifiers(ticket)
            update_progress(20)

            # Validate we have minimum identifiers
            ticket_ids = TicketIdentifiers(**identifiers)
            if not ticket_ids.has_minimum_identifiers():
                return self._create_error_result(
                    ticket,
                    "Could not extract minimum identifiers from ticket",
                    start_time
                )

            # Step 3: Initialize state
            state = InvestigationState(
                ticket_id=ticket.id,
                case_number=ticket.case_number,
                identifiers=identifiers,
                current_step="step_1_platform_check"
            )

            # Step 4: Run investigation loop (20-90%)
            state = await self._investigation_loop(state, update_progress)

            # Step 5: Generate result (90-100%)
            update_progress(90)
            result = self._generate_result(state, ticket, start_time)
            update_progress(100)

            logger.info(
                f"Investigation complete: root_cause={result.root_cause}, "
                f"confidence={result.confidence:.0%}"
            )

            return result

        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            return InvestigationResult(
                ticket_id="",
                case_number=case_number,
                needs_human=True,
                human_question=f"Investigation failed with error: {e}",
                investigation_time=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )

    async def _get_ticket(self, case_number: str) -> SalesforceTicket:
        """Get ticket from Salesforce"""
        sf_client = self.clients.get("salesforce")
        if not sf_client:
            raise ValueError("Salesforce client not configured")

        return await sf_client.get_ticket(case_number)

    async def _extract_identifiers(self, ticket: SalesforceTicket) -> Dict[str, Any]:
        """Extract identifiers from ticket using LLM"""
        # First check if ticket has load_id in custom field
        identifiers = {}
        if ticket.load_id:
            identifiers["load_id"] = ticket.load_id

        # Use LLM to extract additional identifiers
        llm_extracted = await self.llm_client.extract_identifiers(
            subject=ticket.subject,
            description=ticket.description or ""
        )

        # Merge with priority to explicit fields
        for key, value in llm_extracted.items():
            if value and key not in identifiers:
                identifiers[key] = value

        return identifiers

    async def _investigation_loop(
        self,
        state: InvestigationState,
        progress_callback: Callable[[int], None]
    ) -> InvestigationState:
        """
        Main investigation loop.

        Repeatedly:
        1. Build executable tasks
        2. Execute in parallel
        3. Process results
        4. Evaluate decisions
        5. Continue or terminate
        """
        base_progress = 20
        progress_per_iteration = 70 // state.max_iterations

        while not state.is_complete():
            state.increment_iteration()

            # Update progress
            progress = base_progress + (state.iteration_count * progress_per_iteration)
            progress_callback(min(90, progress))

            logger.info(
                f"Iteration {state.iteration_count}/{state.max_iterations}, "
                f"current_step={state.current_step}"
            )

            # Build tasks based on current state
            tasks = self.executor.build_investigation_tasks(state)

            # Filter to only executable tasks
            executable = [
                t for t in tasks
                if not state.has_completed_step(t.id)
            ]

            if not executable:
                # No more tasks to execute
                logger.info("No more executable tasks")
                break

            # Execute tasks in parallel
            results = await self.executor.execute_parallel(executable, state)

            # Process results
            for task, result in zip(executable, results):
                # Add step result to state
                step_result = StepResult(
                    step_id=task.id,
                    step_name=task.task_type.value,
                    success=result.success,
                    data=result.data,
                    execution_time=result.execution_time,
                    error=result.error
                )
                state.add_step_result(step_result)

                # Convert to evidence
                evidence = self.executor.result_to_evidence(task, result)
                if evidence:
                    state.evidence.append(evidence)

                # Update identifiers from results
                self._update_identifiers_from_result(state, task, result)

            # Evaluate decisions
            if state.current_step in [t.id for t in executable]:
                # Current step just completed - evaluate
                decision = self.decision_engine.evaluate(state)

                if decision.root_cause:
                    state.set_root_cause(
                        root_cause=decision.root_cause,
                        category=decision.root_cause_category.value if decision.root_cause_category else "unknown",
                        confidence=decision.confidence,
                        explanation=decision.explanation or ""
                    )
                elif decision.needs_human:
                    state.set_human_handoff(decision.question or "Human input needed")
                elif decision.next_step:
                    state.current_step = decision.next_step

        # Final evaluation if no root cause determined
        if not state.root_cause and not state.needs_human:
            final_decision = self.decision_engine.evaluate_all_evidence(state)
            if final_decision.root_cause:
                state.set_root_cause(
                    root_cause=final_decision.root_cause,
                    category=final_decision.root_cause_category.value if final_decision.root_cause_category else "unknown",
                    confidence=final_decision.confidence,
                    explanation=final_decision.explanation or ""
                )
            elif final_decision.needs_human:
                state.set_human_handoff(final_decision.question or "Could not determine root cause")

        return state

    def _update_identifiers_from_result(
        self,
        state: InvestigationState,
        task: Task,
        result: Any
    ) -> None:
        """Update state identifiers from task results"""
        if not result.success:
            return

        data = result.data

        # Extract subscription_id from tracking config
        if task.id == "step_2_tracking_config":
            if data.get("subscription_id"):
                state.identifiers["subscription_id"] = data["subscription_id"]
            if data.get("tracking_source"):
                state.identifiers["tracking_source"] = data["tracking_source"]

        # Extract carrier/shipper from platform check
        if task.id == "step_1_platform_check":
            carrier = data.get("carrier", {})
            shipper = data.get("shipper", {})
            if carrier.get("id"):
                state.identifiers["carrier_id"] = carrier["id"]
                state.identifiers["carrier_name"] = carrier.get("name")
            if shipper.get("id"):
                state.identifiers["shipper_id"] = shipper["id"]
                state.identifiers["shipper_name"] = shipper.get("name")

    def _generate_result(
        self,
        state: InvestigationState,
        ticket: SalesforceTicket,
        start_time: datetime
    ) -> InvestigationResult:
        """Generate final investigation result"""
        end_time = datetime.utcnow()
        investigation_time = (end_time - start_time).total_seconds()

        # Count similar affected loads
        similar_loads = 0
        for ev in state.evidence:
            if ev.step_id == "step_6_similar_loads":
                similar_loads = ev.raw_data.get("affected_loads", 0)
                break

        # Map category
        category = None
        if state.root_cause_category:
            category_map = {
                "carrier_issue": RootCauseCategory.CARRIER_ISSUE,
                "jt_issue": RootCauseCategory.JT_ISSUE,
                "configuration_issue": RootCauseCategory.CONFIGURATION_ISSUE,
                "system_bug": RootCauseCategory.SYSTEM_BUG,
            }
            category = category_map.get(state.root_cause_category, RootCauseCategory.UNKNOWN)

        return InvestigationResult(
            ticket_id=ticket.id,
            case_number=ticket.case_number,
            load_id=state.identifiers.get("load_id"),
            root_cause=state.root_cause,
            root_cause_category=category,
            confidence=state.confidence,
            explanation=state.explanation or "",
            evidence=state.evidence,
            needs_human=state.needs_human,
            human_question=state.human_question,
            investigation_time=investigation_time,
            steps_executed=len(state.completed_steps),
            queries_executed=len(state.completed_steps),
            started_at=start_time,
            completed_at=end_time,
            similar_loads_affected=similar_loads,
            pattern_detected=similar_loads > 10
        )

    def _create_error_result(
        self,
        ticket: SalesforceTicket,
        error: str,
        start_time: datetime
    ) -> InvestigationResult:
        """Create an error result"""
        return InvestigationResult(
            ticket_id=ticket.id,
            case_number=ticket.case_number,
            needs_human=True,
            human_question=error,
            investigation_time=(datetime.utcnow() - start_time).total_seconds(),
            started_at=start_time,
            completed_at=datetime.utcnow()
        )

    async def update_salesforce(
        self,
        case_number: str,
        result: InvestigationResult
    ) -> None:
        """Update Salesforce case with investigation results"""
        sf_client = self.clients.get("salesforce")
        if not sf_client:
            logger.warning("Salesforce client not configured, cannot update case")
            return

        if not result.root_cause:
            logger.warning("No root cause to update")
            return

        await sf_client.update_case_with_rca(
            case_id=result.ticket_id,
            root_cause=result.root_cause,
            category=result.root_cause_category.value if result.root_cause_category else "unknown",
            confidence=result.confidence,
            explanation=result.explanation
        )

    def close(self) -> None:
        """Close all client connections"""
        for name, client in self.clients.items():
            try:
                if hasattr(client, "close"):
                    client.close()
            except Exception as e:
                logger.warning(f"Error closing {name} client: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
