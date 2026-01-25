"""Main Ocean Debugging Agent implementation"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.models.state import InvestigationState, StepResult
from core.models.evidence import Evidence, EvidenceType, EvidenceSource
from core.models.ticket import SalesforceTicket, TicketIdentifiers
from core.models.result import InvestigationResult, RootCauseCategory

from core.clients.salesforce_client import SalesforceClient
from core.clients.redshift_client import RedshiftClient
from core.clients.clickhouse_client import ClickHouseClient
from modes.ocean.clients.jt_client import JustTransformClient
from core.clients.tracking_api_client import TrackingAPIClient
from core.clients.super_api_client import SuperApiClient
from core.clients.company_api_client import CompanyAPIClient

from core.engine.task_executor import ParallelTaskExecutor, Task
from core.engine.decision_engine import DecisionEngine
from core.engine.hypothesis_engine import HypothesisEngine
from core.engine.hypothesis_orchestrator import HypothesisOrchestrator

from core.utils.config import Config
from core.utils.llm_client import LLMClient
from core.utils.logging import get_logger, setup_logging

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

    def __init__(self, config: Optional[Config] = None, use_hypothesis_mode: bool = True):
        self.config = config or Config()
        self.use_hypothesis_mode = use_hypothesis_mode  # NEW: Toggle between hypothesis and legacy mode
        self._clients: Optional[Dict[str, Any]] = None
        self._executor: Optional[ParallelTaskExecutor] = None
        self._decision_engine: Optional[DecisionEngine] = None
        self._llm_client: Optional[LLMClient] = None
        self._hypothesis_engine: Optional[HypothesisEngine] = None
        self._orchestrator: Optional[HypothesisOrchestrator] = None

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
            self._llm_client = LLMClient()
        return self._llm_client

    @property
    def hypothesis_engine(self) -> HypothesisEngine:
        """Lazy initialization of hypothesis engine"""
        if self._hypothesis_engine is None:
            self._hypothesis_engine = HypothesisEngine(self.llm_client)
        return self._hypothesis_engine

    @property
    def orchestrator(self) -> HypothesisOrchestrator:
        """Lazy initialization of hypothesis orchestrator"""
        if self._orchestrator is None:
            self._orchestrator = HypothesisOrchestrator(
                clients=self.clients,
                llm_client=self.llm_client,
                hypothesis_engine=self.hypothesis_engine
            )
        return self._orchestrator

    def _init_clients(self) -> Dict[str, Any]:
        """Initialize all data source clients"""
        clients = {}

        # Salesforce
        if self.config.salesforce.is_configured():
            clients["salesforce"] = SalesforceClient(self.config.salesforce)
        else:
            logger.warning("Salesforce not configured")

        # Redshift - reads from global config
        if self.config.redshift.is_configured():
            clients["redshift"] = RedshiftClient()
        else:
            logger.warning("Redshift not configured")

        # ClickHouse - reads from global config
        if self.config.clickhouse.is_configured():
            clients["clickhouse"] = ClickHouseClient()
        else:
            logger.warning("ClickHouse not configured")

        # Just Transform - reads from global config
        if self.config.justtransform.is_configured():
            clients["justtransform"] = JustTransformClient()
        else:
            logger.warning("Just Transform not configured")

        # Tracking API - reads from global config
        if self.config.tracking_api.is_configured():
            clients["tracking_api"] = TrackingAPIClient()
        else:
            logger.warning("Tracking API not configured")

        # Super API
        if self.config.super_api.is_configured():
            clients["super_api"] = SuperApiClient(self.config.super_api)
        else:
            logger.warning("Super API not configured")

        # Company API (for network relationships)
        clients["company_api"] = CompanyAPIClient()

        return clients

    async def investigate(
        self,
        case_number: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    ) -> InvestigationResult:
        """
        Run a full investigation for a Salesforce case.

        Uses hypothesis-driven mode by default (adaptive, parallel sub-agents).
        Set use_hypothesis_mode=False in constructor for legacy linear mode.

        Args:
            case_number: Salesforce case number
            progress_callback: Optional callback for progress updates (0-100)
            event_callback: Optional async callback for detailed events (type, data)

        Returns:
            InvestigationResult with root cause and recommendations
        """
        if self.use_hypothesis_mode:
            return await self._investigate_hypothesis_mode(case_number, progress_callback, event_callback)
        else:
            return await self._investigate_legacy_mode(case_number, progress_callback)

    async def _investigate_hypothesis_mode(
        self,
        case_number: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    ) -> InvestigationResult:
        """
        Hypothesis-driven investigation with parallel sub-agents.

        This mode:
        1. Forms hypotheses about possible root causes
        2. Spawns sub-agents to test each hypothesis in parallel
        3. Uses LLM reasoning to decide what to query
        4. Synthesizes findings into final root cause
        """
        start_time = datetime.utcnow()

        def update_progress(pct: int):
            if progress_callback:
                progress_callback(pct)

        async def emit_event(event_type: str, data: Dict[str, Any]):
            if event_callback:
                await event_callback(event_type, data)

        try:
            # Step 1: Get ticket and extract identifiers (20%)
            logger.info(f"[HYPOTHESIS MODE] Starting investigation for case: {case_number}")
            await emit_event("log", {"message": "Starting hypothesis-driven investigation", "phase": "init"})
            update_progress(5)

            ticket = await self._get_ticket(case_number)
            await emit_event("log", {"message": f"Retrieved ticket: {ticket.case_number}", "phase": "ticket"})
            update_progress(10)

            identifiers = await self._extract_identifiers(ticket)
            await emit_event("log", {"message": f"Extracted identifiers: {list(identifiers.keys())}", "phase": "identifiers"})
            await emit_event("identifiers", identifiers)
            update_progress(20)

            # Validate identifiers
            ticket_ids = TicketIdentifiers(**identifiers)
            if not ticket_ids.has_minimum_identifiers():
                await emit_event("error", {"message": "Could not extract minimum identifiers from ticket"})
                return self._create_error_result(
                    ticket,
                    "Could not extract minimum identifiers from ticket",
                    start_time
                )

            # Step 2: Gather initial evidence (30%)
            logger.info("Gathering initial evidence for hypothesis formation...")
            await emit_event("log", {"message": "Gathering initial evidence for hypothesis formation", "phase": "evidence"})
            initial_evidence = await self._gather_initial_evidence(identifiers)

            for ev in initial_evidence:
                await emit_event("evidence", {
                    "finding": ev.finding,
                    "source": ev.source.value if hasattr(ev.source, 'value') else str(ev.source),
                    "type": ev.type.value if hasattr(ev.type, 'value') else str(ev.type)
                })

            update_progress(30)

            # Update identifiers from initial evidence
            identifiers = self._enrich_identifiers(identifiers, initial_evidence)

            # Step 3: Run hypothesis-driven investigation (30-90%)
            logger.info("Running hypothesis-driven investigation...")
            await emit_event("log", {"message": "Forming hypotheses and spawning sub-agents", "phase": "hypotheses"})

            result = await self.orchestrator.investigate(
                identifiers=identifiers,
                initial_evidence=initial_evidence,
                event_callback=event_callback
            )
            update_progress(90)

            # Step 4: Set ticket info and finalize
            result.ticket_id = ticket.id
            result.case_number = ticket.case_number
            result.load_id = identifiers.get("load_id")
            update_progress(100)

            await emit_event("log", {
                "message": f"Investigation complete: {result.root_cause_category}",
                "phase": "complete"
            })

            logger.info(
                f"[HYPOTHESIS MODE] Investigation complete: "
                f"root_cause={result.root_cause_category}, "
                f"confidence={result.confidence:.0%}"
            )

            return result

        except Exception as e:
            logger.error(f"[HYPOTHESIS MODE] Investigation failed: {e}", exc_info=True)
            await emit_event("error", {"message": str(e), "phase": "failed"})
            return InvestigationResult(
                ticket_id="",
                case_number=case_number,
                needs_human=True,
                human_question=f"Investigation failed with error: {e}",
                investigation_time=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )

    async def _gather_initial_evidence(
        self,
        identifiers: Dict[str, Any]
    ) -> List[Evidence]:
        """
        Gather initial evidence to help form hypotheses.

        Always runs platform check to get basic load info.
        """
        evidence = []
        load_id = identifiers.get("load_id")

        if not load_id:
            logger.warning("No load_id for initial evidence gathering")
            return evidence

        # Platform check - get basic load info
        tracking_client = self.clients.get("tracking_api")
        if tracking_client:
            try:
                # Run sync method in thread pool to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: tracking_client.get_tracking_by_id(int(load_id))
                )
                if result:
                    # Create evidence from result
                    ev = Evidence(
                        type=EvidenceType.API,
                        source=EvidenceSource.TRACKING_API,
                        step_id="initial_platform_check",
                        finding=self._summarize_platform_result(result),
                        raw_data=result
                    )
                    evidence.append(ev)
                    logger.info(f"Initial evidence: {ev.finding}")
            except Exception as e:
                logger.warning(f"Initial platform check failed: {e}")

        return evidence

    def _summarize_platform_result(self, result: Dict[str, Any]) -> str:
        """Summarize platform check result for hypothesis formation"""
        if not result:
            return "Platform check returned no data"

        load_data = result.get("load") or result.get("loads", [{}])[0] if result.get("loads") else result

        status = load_data.get("status") or load_data.get("mappableStatus", "unknown")
        carrier = load_data.get("carrier", {})
        carrier_name = carrier.get("name", "unknown") if isinstance(carrier, dict) else str(carrier)

        return f"Load status={status}, carrier={carrier_name}"

    def _enrich_identifiers(
        self,
        identifiers: Dict[str, Any],
        initial_evidence: List[Evidence]
    ) -> Dict[str, Any]:
        """Enrich identifiers from initial evidence"""
        enriched = identifiers.copy()

        for ev in initial_evidence:
            if ev.step_id == "initial_platform_check":
                data = ev.raw_data
                load_data = data.get("load") or data.get("loads", [{}])[0] if data.get("loads") else data

                # Debug: log what we found
                logger.info(f"Enriching from load_data keys: {list(load_data.keys()) if isinstance(load_data, dict) else type(load_data)}")

                # Extract carrier/shipper
                carrier = load_data.get("carrier", {})
                shipper = load_data.get("shipper", {})

                logger.info(f"Found carrier: {carrier}, shipper: {shipper}")

                if isinstance(carrier, dict) and carrier.get("id"):
                    enriched["carrier_id"] = carrier["id"]
                    enriched["carrier_name"] = carrier.get("name")

                if isinstance(shipper, dict) and shipper.get("id"):
                    enriched["shipper_id"] = shipper["id"]
                    enriched["shipper_name"] = shipper.get("name")

                # Extract container/booking
                if load_data.get("containerNumber"):
                    enriched["container_number"] = load_data["containerNumber"]
                if load_data.get("bookingNumber"):
                    enriched["booking_number"] = load_data["bookingNumber"]

        logger.info(f"Enriched identifiers: {enriched}")
        return enriched

    async def _investigate_legacy_mode(
        self,
        case_number: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> InvestigationResult:
        """
        Legacy linear investigation mode (step-by-step).

        Use --legacy flag or set use_hypothesis_mode=False to use this mode.
        """
        start_time = datetime.utcnow()

        def update_progress(pct: int):
            if progress_callback:
                progress_callback(pct)

        try:
            # Step 1: Get ticket from Salesforce (10%)
            logger.info(f"[LEGACY MODE] Starting investigation for case: {case_number}")
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
                f"[LEGACY MODE] Investigation complete: root_cause={result.root_cause}, "
                f"confidence={result.confidence:.0%}"
            )

            return result

        except Exception as e:
            logger.error(f"[LEGACY MODE] Investigation failed: {e}")
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
        """Get ticket from Salesforce or create synthetic ticket for manual input"""
        sf_client = self.clients.get("salesforce")

        # If no Salesforce configured, create synthetic ticket for manual investigations
        if not sf_client:
            logger.info("Salesforce not configured, creating synthetic ticket for manual investigation")
            return SalesforceTicket(
                id=case_number,
                case_number=case_number,
                subject=f"Manual Investigation: {case_number}",
                description=f"Direct investigation requested for {case_number}",
                status="Open",
                priority="Medium",
                created_date=datetime.utcnow()
            )

        return await sf_client.get_ticket(case_number)

    async def _extract_identifiers(self, ticket: SalesforceTicket) -> Dict[str, Any]:
        """Extract identifiers from ticket using LLM or from synthetic case number"""
        identifiers = {}

        # First check if ticket has load_id in custom field
        if ticket.load_id:
            identifiers["load_id"] = ticket.load_id

        # Check if case_number is synthetic (contains load_id or load_number)
        if ticket.case_number.startswith("LOAD_"):
            # Extract load_id from synthetic case number
            load_id = ticket.case_number.replace("LOAD_", "")
            if load_id.isdigit():
                identifiers["load_id"] = load_id
                logger.info(f"Extracted load_id from synthetic case: {load_id}")
                return identifiers

        if ticket.case_number.startswith("LOADNUM_"):
            # Extract load_number from synthetic case number
            load_number = ticket.case_number.replace("LOADNUM_", "")
            identifiers["load_number"] = load_number
            logger.info(f"Extracted load_number from synthetic case: {load_number}")
            return identifiers

        # Use LLM to extract additional identifiers if not synthetic
        if ticket.description and ticket.description != f"Direct investigation requested for {ticket.case_number}":
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
                # Log task result
                if result.success:
                    logger.info(f"✅ Task {task.id} succeeded")
                else:
                    logger.error(f"❌ Task {task.id} failed: {result.error}")

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
        if task.id == "step_2_get_tracking_config":
            if data.get("subscription_id"):
                state.identifiers["subscription_id"] = data["subscription_id"]
            if data.get("tracking_source"):
                state.identifiers["tracking_source"] = data["tracking_source"]

        # Extract carrier/shipper from platform check
        if task.id == "step_1_platform_check":
            carrier = data.get("carrier", {})
            shipper = data.get("shipper", {})
            logger.info(f"Extracting identifiers from step_1: carrier={carrier.get('id')}, shipper={shipper.get('id')}")
            if carrier.get("id"):
                state.identifiers["carrier_id"] = carrier["id"]
                state.identifiers["carrier_name"] = carrier.get("name")
                logger.info(f"✅ Set carrier_id={carrier['id']}")
            if shipper.get("id"):
                state.identifiers["shipper_id"] = shipper["id"]
                state.identifiers["shipper_name"] = shipper.get("name")
                logger.info(f"✅ Set shipper_id={shipper['id']}")

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
