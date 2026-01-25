"""Parallel task executor for investigation steps"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.models.state import InvestigationState, StepResult, TaskStatus, TaskStatusEnum
from core.models.evidence import Evidence, EvidenceSource, EvidenceType
from core.utils.logging import get_logger

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Type of investigation task"""
    PLATFORM_CHECK = "platform_check"
    TRACKING_CONFIG = "tracking_config"
    JT_HISTORY = "jt_history"
    SIGNOZ_LOGS = "signoz_logs"
    NETWORK_CHECK = "network_check"
    CARRIER_FILES = "carrier_files"
    SIMILAR_LOADS = "similar_loads"


@dataclass
class Task:
    """A single investigation task to execute"""
    id: str
    task_type: TaskType
    client_name: str
    method_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    depends_on: List[str] = field(default_factory=list)
    evidence_source: EvidenceSource = EvidenceSource.PLATFORM


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    task_type: TaskType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0


class ParallelTaskExecutor:
    """
    Execute multiple investigation tasks in parallel.

    Respects task dependencies and manages concurrent execution.
    """

    def __init__(
        self,
        clients: Dict[str, Any],
        max_parallel: int = 5,
        default_timeout: float = 60.0
    ):
        self.clients = clients
        self.max_parallel = max_parallel
        self.default_timeout = default_timeout

    async def execute_single(self, task: Task) -> TaskResult:
        """Execute a single task"""
        start_time = time.time()

        try:
            # Get the client
            client = self.clients.get(task.client_name)
            if not client:
                return TaskResult(
                    task_id=task.id,
                    task_type=task.task_type,
                    success=False,
                    error=f"Client '{task.client_name}' not found"
                )

            # Get the method
            method = getattr(client, task.method_name, None)
            if not method:
                return TaskResult(
                    task_id=task.id,
                    task_type=task.task_type,
                    success=False,
                    error=f"Method '{task.method_name}' not found on {task.client_name}"
                )

            # Execute with timeout (handle both sync and async methods)
            timeout = task.timeout or self.default_timeout

            # Check if method is async or sync
            import inspect
            if inspect.iscoroutinefunction(method):
                # Async method - await directly
                result = await asyncio.wait_for(
                    method(**task.params),
                    timeout=timeout
                )
            else:
                # Sync method - run in thread pool
                result = await asyncio.wait_for(
                    asyncio.to_thread(method, **task.params),
                    timeout=timeout
                )

            # Transform the result based on task type
            transformed_result = self._transform_result(task, result)

            execution_time = time.time() - start_time

            logger.info(
                f"Task {task.id} completed in {execution_time:.2f}s"
            )

            return TaskResult(
                task_id=task.id,
                task_type=task.task_type,
                success=True,
                data=transformed_result,
                execution_time=execution_time
            )

        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task.id,
                task_type=task.task_type,
                success=False,
                error=f"Task timed out after {task.timeout or self.default_timeout}s",
                execution_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            return TaskResult(
                task_id=task.id,
                task_type=task.task_type,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _transform_result(self, task: Task, result: Any) -> Dict[str, Any]:
        """
        Transform raw API/DB results into normalized format for decision engine.

        Handles different response structures from various data sources and normalizes
        them to a consistent format that the decision engine expects.
        """
        if result is None:
            return {"exists": False, "error": "No data returned"}

        # Handle PLATFORM_CHECK (Tracking API)
        if task.task_type == TaskType.PLATFORM_CHECK:
            # Tracking API returns {"load": {...}} or {"loads": [{...}]}
            load_data = None

            if isinstance(result, dict):
                if "load" in result:
                    load_data = result["load"]
                elif "loads" in result and result["loads"]:
                    load_data = result["loads"][0]  # Take first load

            if not load_data:
                return {
                    "exists": False,
                    "load_exists": False,
                    "error": "Load not found in API response"
                }

            # Extract and normalize fields
            mode_raw = load_data.get("loadMode", "UNKNOWN")
            return {
                "exists": True,
                "load_exists": True,
                "mode": mode_raw.upper() if isinstance(mode_raw, str) else mode_raw,  # Uppercase for decision tree
                "actual_mode": load_data.get("actualLoadMode"),
                "current_state": load_data.get("status", "UNKNOWN"),  # Map status -> current_state
                "status": load_data.get("status"),
                "mappable_status": load_data.get("mappableStatus"),
                "tracking_id": load_data.get("id"),
                "load_number": load_data.get("loadNumber"),

                # Carrier and shipper (handle both nested and flat formats)
                "carrier": self._extract_entity(load_data, "carrier"),
                "shipper": self._extract_entity(load_data, "shipper"),
                "managing_carrier": self._extract_entity(load_data, "managingCarrier"),
                "operating_carrier": self._extract_entity(load_data, "operatingCarrier"),

                # Timestamps
                "created_at": load_data.get("createdAt"),
                "updated_at": load_data.get("updatedAt"),
                "delivered_at": load_data.get("deliveredAt"),

                # Tracking details
                "tracking_method": load_data.get("trackingMethod"),
                "tracking_number": load_data.get("trackingNumber"),
                "container_number": load_data.get("containerNumber"),
                "stops": load_data.get("stops", []),

                # Keep raw data for deeper analysis
                "_raw": load_data
            }

        # Other task types return data as-is (already normalized)
        return result if isinstance(result, dict) else {"data": result}

    def _extract_entity(self, load_data: Dict, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract entity (carrier/shipper) from load data.
        Handles both nested objects and flat fields.
        """
        # Try nested format first (GET /tracking/{id})
        if entity_type in load_data and isinstance(load_data.get(entity_type), dict):
            entity = load_data[entity_type]
            return {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "permalink": entity.get("permalink"),
                "_raw": entity
            }

        # Try flat format (POST /tracking/search)
        id_field = f"{entity_type}Id"
        name_field = f"{entity_type}Name"

        if id_field in load_data or name_field in load_data:
            return {
                "id": load_data.get(id_field),
                "name": load_data.get(name_field)
            }

        return None

    async def execute_parallel(
        self,
        tasks: List[Task],
        state: InvestigationState
    ) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of tasks to execute
            state: Current investigation state

        Returns:
            List of task results
        """
        if not tasks:
            return []

        # Filter to only executable tasks (dependencies met)
        executable = self._get_executable_tasks(tasks, state)

        if not executable:
            logger.warning("No executable tasks (dependencies not met)")
            return []

        # Limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(task: Task) -> TaskResult:
            async with semaphore:
                # Update state to show task is running
                state.parallel_tasks[task.id] = TaskStatus(
                    task_id=task.id,
                    status=TaskStatusEnum.RUNNING
                )
                return await self.execute_single(task)

        # Execute all tasks concurrently
        logger.info(f"Executing {len(executable)} tasks in parallel")
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in executable],
            return_exceptions=True
        )

        # Process results
        processed_results = []
        for task, result in zip(executable, results):
            if isinstance(result, Exception):
                result = TaskResult(
                    task_id=task.id,
                    task_type=task.task_type,
                    success=False,
                    error=str(result)
                )

            # Update state
            state.parallel_tasks[task.id] = TaskStatus(
                task_id=task.id,
                status=TaskStatusEnum.COMPLETED if result.success else TaskStatusEnum.FAILED
            )

            processed_results.append(result)

        return processed_results

    def _get_executable_tasks(
        self,
        tasks: List[Task],
        state: InvestigationState
    ) -> List[Task]:
        """Get tasks whose dependencies are satisfied"""
        completed_ids = {s.step_id for s in state.completed_steps}

        executable = []
        for task in tasks:
            # Check if already executed
            if task.id in completed_ids:
                logger.debug(f"Task {task.id} already completed, skipping")
                continue

            # Check dependencies
            deps_met = all(
                dep in completed_ids
                for dep in task.depends_on
            )

            if deps_met:
                logger.info(f"✅ Task {task.id} is executable (deps: {task.depends_on})")
                executable.append(task)
            else:
                logger.debug(f"Task {task.id} not executable - missing deps: {set(task.depends_on) - completed_ids}")

        return executable

    def build_investigation_tasks(
        self,
        state: InvestigationState
    ) -> List[Task]:
        """
        Build task list based on current investigation state.

        Args:
            state: Current investigation state

        Returns:
            List of tasks to execute
        """
        tasks = []
        identifiers = state.identifiers

        # Step 1: Platform check (always first)
        if identifiers.get("load_id"):
            tasks.append(Task(
                id="step_1_platform_check",
                task_type=TaskType.PLATFORM_CHECK,
                client_name="tracking_api",
                method_name="get_tracking_by_id",
                params={"tracking_id": int(identifiers["load_id"])},
                evidence_source=EvidenceSource.TRACKING_API
            ))

        # Step 2: Tracking config
        if identifiers.get("load_id"):
            tasks.append(Task(
                id="step_2_get_tracking_config",
                task_type=TaskType.TRACKING_CONFIG,
                client_name="super_api",
                method_name="get_tracking_config",
                params={"load_id": identifiers["load_id"]},
                depends_on=["step_1_platform_check"],
                evidence_source=EvidenceSource.SUPER_API
            ))

        # Steps 3-5 can run in parallel after step 2
        # Step 3: JT History
        subscription_id = identifiers.get("subscription_id")
        if subscription_id:
            tasks.append(Task(
                id="step_3_jt_history",
                task_type=TaskType.JT_HISTORY,
                client_name="justtransform",
                method_name="get_subscription_history",
                params={"subscription_id": subscription_id},
                depends_on=["step_2_get_tracking_config"],
                timeout=60.0,
                evidence_source=EvidenceSource.JUSTTRANSFORM
            ))

        # Step 4: SigNoz logs
        container = identifiers.get("container_number")
        booking = identifiers.get("booking_number")
        if container or booking:
            tasks.append(Task(
                id="step_4_signoz_logs",
                task_type=TaskType.SIGNOZ_LOGS,
                client_name="clickhouse",
                method_name="get_ocean_processing_logs",
                params={
                    "container_number": container,
                    "booking_number": booking,
                    "days_back": 30
                },
                depends_on=["step_2_get_tracking_config"],
                timeout=120.0,
                evidence_source=EvidenceSource.SIGNOZ
            ))

        # Step 5: Network relationship check (critical)
        shipper_id = identifiers.get("shipper_id")
        carrier_id = identifiers.get("carrier_id")
        logger.info(f"Building step_5: shipper_id={shipper_id}, carrier_id={carrier_id}, all_identifiers={list(identifiers.keys())}")
        if shipper_id and carrier_id:
            tasks.append(Task(
                id="step_5_network_check",
                task_type=TaskType.NETWORK_CHECK,
                client_name="company_api",
                method_name="get_company_relationship",
                params={
                    "company_permalink": shipper_id,
                    "related_company_id": carrier_id
                },
                depends_on=["step_1_platform_check"],
                evidence_source=EvidenceSource.COMPANY_API
            ))

        # Additional: Find similar stuck loads
        if carrier_id:
            tasks.append(Task(
                id="step_6_similar_loads",
                task_type=TaskType.SIMILAR_LOADS,
                client_name="redshift",
                method_name="find_similar_stuck_loads",
                params={"carrier_id": carrier_id},
                depends_on=["step_5_network_check"],
                evidence_source=EvidenceSource.REDSHIFT
            ))

        return tasks

    def result_to_evidence(
        self,
        task: Task,
        result: TaskResult
    ) -> Optional[Evidence]:
        """Convert a task result to evidence"""
        if not result.success:
            return None

        # Generate finding summary based on task type
        finding = self._summarize_finding(task.task_type, result.data)

        return Evidence(
            type=EvidenceType.API if "api" in task.client_name else EvidenceType.DATABASE,
            source=task.evidence_source,
            step_id=task.id,
            finding=finding,
            raw_data=result.data,
            query_time_ms=result.execution_time * 1000
        )

    def _summarize_finding(
        self,
        task_type: TaskType,
        data: Dict[str, Any]
    ) -> str:
        """Generate human-readable finding summary"""
        if task_type == TaskType.PLATFORM_CHECK:
            if data.get("exists"):
                return f"Load exists, status = {data.get('status', 'unknown')}"
            return "Load not found in platform"

        if task_type == TaskType.TRACKING_CONFIG:
            if data.get("exists"):
                source = data.get("tracking_source", "unknown")
                identifier = data.get("primary_identifier", "unknown")
                return f"Tracking via {source} using {identifier}"
            return "No tracking configuration found"

        if task_type == TaskType.JT_HISTORY:
            count = data.get("events_count", 0)
            has_disc = data.get("has_discrepancies", False)
            if count == 0:
                return "No JT scraping history found"
            if has_disc:
                return f"Found {count} JT events with discrepancies"
            return f"Found {count} JT events, no discrepancies"

        if task_type == TaskType.SIGNOZ_LOGS:
            count = data.get("count", 0)
            if count == 0:
                return "No PROCESS_OCEAN_UPDATE logs found"
            sources = data.get("data_sources", {})
            return f"Found {count} log entries from sources: {list(sources.keys())}"

        if task_type == TaskType.NETWORK_CHECK:
            if data.get("exists"):
                status = data.get("relationships", [{}])[0].get("status", "unknown")
                return f"Network relationship exists, status = {status}"
            return "No carrier-shipper relationship found"

        if task_type == TaskType.SIMILAR_LOADS:
            affected = data.get("affected_loads", 0)
            return f"{affected} similar loads also stuck"

        return "Finding recorded"
