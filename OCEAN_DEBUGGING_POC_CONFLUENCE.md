# Ocean Debugging Agent POC

**Author:** MSP Raja, AI R&D Solutions Engineer
**Date:** January 13, 2026
**Status:** Architecture Approved, Implementation Ready

---

## Executive Summary

This document outlines the design and architecture for an **AI-powered Ocean Debugging Agent** that automates the investigation of ocean shipment tracking issues. The system transforms the current manual, random troubleshooting process into a structured, parallel investigation workflow.

### Key Metrics

| Metric | Current (Manual) | Target (Automated) | Improvement |
|--------|-----------------|-------------------|-------------|
| Resolution Time | 30-45 minutes | 10-15 minutes | 60% reduction |
| Data Gathering | 25-35 minutes | Automated | 80% reduction |
| Tools Accessed | 5-8 systems | 1 unified CLI | 75% reduction |
| Accuracy | Variable | 85%+ | Consistent |

---

## Problem Statement

### Current State

Support analysts (ISBO team) manually investigate ocean tracking issues by:

1. **Random tool hopping** - Checking 5-8 different systems without structure
2. **Manual data gathering** - Copy-pasting between Platform, JT Portal, SigNoz, Redshift
3. **Tribal knowledge dependent** - Resolution relies on individual expertise
4. **Time intensive** - 80% of time spent on data gathering, 20% on actual analysis

### Root Cause Distribution

Based on support team analysis:

| Root Cause | Frequency | Detection Method |
|------------|-----------|------------------|
| Network Relationship Missing | **7.7%** | Redshift query |
| JT Scraping Error | 15% | Compare crawled vs formatted |
| Carrier Portal Issue | 20% | JT shows correct scrape |
| Configuration Issue | 10% | Super API check |
| System Bug | 5% | All sources agree, platform wrong |

---

## Solution Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OCEAN DEBUGGING AGENT POC                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐ │
│  │  SALESFORCE  │────▶│              ROUTER AGENT                        │ │
│  │    TICKET    │     │  - Extract identifiers (LLM)                     │ │
│  │    (API)     │     │  - Classify issue type                           │ │
│  └──────────────┘     │  - Select skill: ocean_debugging                 │ │
│                       └──────────────────┬───────────────────────────────┘ │
│                                          │                                  │
│                                          ▼                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    STATE MACHINE (Investigation State)                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │ InvestigationState                                              │  │ │
│  │  │ ├── ticket_id, case_number                                      │  │ │
│  │  │ ├── identifiers: {load_id, carrier_id, shipper_id, ...}        │  │ │
│  │  │ ├── current_step: str                                           │  │ │
│  │  │ ├── completed_steps: List[StepResult]                           │  │ │
│  │  │ ├── evidence: List[Evidence]                                    │  │ │
│  │  │ ├── parallel_tasks: Dict[str, TaskStatus]                       │  │ │
│  │  │ ├── root_cause: Optional[str]                                   │  │ │
│  │  │ ├── confidence: float                                           │  │ │
│  │  │ └── needs_human: bool                                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                          │                                  │
│                                          ▼                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         AGENT LOOP                                     │ │
│  │                                                                        │ │
│  │  while not investigation.is_complete():                               │ │
│  │      1. Get next steps (respecting dependency graph)                  │ │
│  │      2. Execute independent steps in PARALLEL                         │ │
│  │      3. Save results to state + accumulate evidence                   │ │
│  │      4. Evaluate decision tree against evidence                       │ │
│  │      5. If stuck or low confidence → human_handoff()                  │ │
│  │      6. If root_cause found → generate_report()                       │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                          │                                  │
│                    ┌─────────────────────┼─────────────────────┐           │
│                    │                     │                     │           │
│                    ▼                     ▼                     ▼           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │   Redshift       │  │   ClickHouse     │  │   JT API         │         │
│  │   (Network,      │  │   (SigNoz Logs)  │  │   (Scraping      │         │
│  │    Files,Loads)  │  │                  │  │    History)      │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                    │                     │                     │           │
│                    └─────────────────────┼─────────────────────┘           │
│                                          │                                  │
│                                          ▼                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      DECISION ENGINE                                   │ │
│  │  - Evaluate decision_tree.yaml rules against evidence                 │ │
│  │  - Calculate confidence based on evidence types                       │ │
│  │  - Determine root cause or next investigation step                    │ │
│  │  - Handle all paths: network, JT, config, system bug                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                          │                                  │
│                           ┌──────────────┴──────────────┐                  │
│                           │                             │                  │
│                           ▼                             ▼                  │
│  ┌─────────────────────────────┐      ┌─────────────────────────────────┐ │
│  │      ROOT CAUSE FOUND       │      │       HUMAN HANDOFF            │ │
│  │  - Generate markdown report │      │  - Present evidence gathered   │ │
│  │  - Recommended actions      │      │  - Ask specific question       │ │
│  │  - Update Salesforce case   │      │  - Resume with human input     │ │
│  └─────────────────────────────┘      └─────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Investigation Workflow (Decision Tree)

The agent follows a structured 6-step investigation workflow based on the support team's mental model:

### Step 1: Platform Check (Customer View)
- **What**: Check load status in FourKites platform
- **Why**: See what customer sees
- **Decision Points**:
  - Load not found → Configuration issue
  - Status = "Awaiting Tracking Info" → Continue to Step 2

### Step 2: Get Tracking Configuration
- **What**: Query Super API for tracking setup
- **Why**: Understand how load is being tracked
- **Key Data**:
  - Primary identifier (booking number > bill of lading > container)
  - Subscription ID
  - Tracking source (RPA, API, EDI)

### Step 3: Check Just Transform (JT)
- **What**: Query JT portal for scraping history
- **Why**: See what carrier portal data was captured
- **Decision Points**:
  - No JT events → Carrier portal not sending data
  - JT has events → Compare crawled vs formatted

### Step 4: SigNoz Logs Analysis
- **What**: Query PROCESS_OCEAN_UPDATE logs
- **Why**: See how data was processed internally
- **Query Pattern**:
```sql
SELECT body, timestamp, trace_id,
       JSONExtractString(body, 'event_code') as event_code,
       JSONExtractString(body, 'data_source') as data_source
FROM signoz_logs.distributed_logs
WHERE service_name = 'multimodel_carrier_updates_worker'
  AND body LIKE '%PROCESS_OCEAN_UPDATE%'
  AND body LIKE '%{container_number}%'
  AND timestamp >= now() - INTERVAL 30 DAY
```

### Step 5: Network Relationship Check (Critical)
- **What**: Query Redshift for carrier-shipper relationship
- **Why**: #1 cause of stuck loads (7.7%)
- **Query**:
```sql
SELECT relationship_id, status, is_active
FROM company_relationships
WHERE shipper_id = '{shipper_id}'
  AND carrier_id = '{carrier_id}'
```

### Step 6: Correlate & Determine Root Cause
- **What**: Compare all findings
- **Output**: Root cause + confidence + recommended action

---

## Data Sources Integration

| Source | Purpose | Access Method | Latency |
|--------|---------|---------------|---------|
| **Salesforce** | Get ticket details | REST API | ~2s |
| **Tracking API** | Load status, milestones | REST API | ~1s |
| **Super API** | Tracking configuration | REST API | ~1s |
| **JT API** | Scraping history | REST API | ~5s |
| **SigNoz** | Processing logs | ClickHouse | ~10s |
| **Redshift** | Network relationships, files | SQL | ~5s |

### Parallel Execution Strategy

```
         Time →

Step 1:  ████████████  Platform Check
Step 2:  ████████████  Tracking Config

         ↓ (after identifiers extracted)

Step 3:  ████████████████  JT History
Step 4:  ████████████████  SigNoz Logs     ← PARALLEL
Step 5:  ████████████████  Network Check   ← PARALLEL

         ↓ (after all complete)

Step 6:  ████████  Decision Engine
```

---

## Skills Framework

The ocean debugging capability is encapsulated as a "skill" that can be loaded by the router agent:

### Skill Definition (`skill_definition.yaml`)

```yaml
skill:
  id: "ocean_debugging"
  name: "Ocean Shipment Debugging"
  version: "1.0.0"

  triggers:
    keywords:
      - "not tracking"
      - "awaiting tracking info"
      - "vessel departure wrong"
      - "eta incorrect"
    issue_categories:
      - "load_not_tracking"
      - "eta_issues"
      - "milestone_wrong"
      - "duplicate_events"

  capabilities:
    - id: "platform_check"
      name: "Check Platform Status"

    - id: "get_tracking_config"
      name: "Get Tracking Configuration"

    - id: "check_justtransform"
      name: "Check JT Scraping History"

    - id: "analyze_signoz_logs"
      name: "Analyze Processing Logs"

    - id: "check_network_relationship"
      name: "Verify Carrier-Shipper Relationship"

  human_handoff:
    triggers:
      - low_confidence: { threshold: 0.7 }
      - stuck_after_steps: { max_steps: 5 }
      - contradictory_data: true
```

---

## Implementation Directory Structure

```
skills/ocean_debugging/
├── skill_definition.yaml       ✅ Created
├── decision_tree.yaml          ✅ Created
├── api_mappings.yaml           ✅ Created
├── knowledge_base.md           ✅ Created
├── test_cases/                 ✅ Created
├── prompts/                    ✅ Created
│
├── src/                        📝 To Implement
│   ├── __init__.py
│   │
│   ├── agent.py                # Main OceanDebuggingAgent class
│   ├── state.py                # InvestigationState management
│   ├── task_executor.py        # Parallel task execution
│   ├── decision_engine.py      # Decision tree evaluator
│   │
│   ├── clients/                # Data source clients
│   │   ├── base_client.py      # Thread-local + retry pattern
│   │   ├── salesforce_client.py
│   │   ├── redshift_client.py
│   │   ├── clickhouse_client.py
│   │   ├── jt_client.py
│   │   ├── tracking_api_client.py
│   │   └── super_api_client.py
│   │
│   ├── models/                 # Pydantic models
│   │   ├── state.py
│   │   ├── evidence.py
│   │   ├── ticket.py
│   │   └── result.py
│   │
│   └── utils/
│       ├── config.py
│       ├── llm_client.py
│       └── logging.py
│
├── main.py                     # CLI entry point
├── requirements.txt
└── .env.example
```

---

## Key Code Patterns

### 1. Investigation State Model

```python
class InvestigationState(BaseModel):
    ticket_id: str
    case_number: str
    identifiers: Dict[str, Any]
    current_step: str = "init"
    completed_steps: List[StepResult] = []
    evidence: List[Evidence] = []
    parallel_tasks: Dict[str, TaskStatus] = {}
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    confidence: float = 0.0
    needs_human: bool = False
    human_question: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2. Agent Loop Pattern

```python
async def investigate(self, case_number: str) -> InvestigationResult:
    # 1. Get ticket from Salesforce
    ticket = await self.clients['salesforce'].get_ticket(case_number)

    # 2. Extract identifiers using LLM
    identifiers = await self._extract_identifiers(ticket)

    # 3. Initialize state
    state = InvestigationState(
        ticket_id=ticket.id,
        case_number=ticket.case_number,
        identifiers=identifiers,
        current_step="step_1_platform_check"
    )

    # 4. Main investigation loop
    while not self._is_complete(state):
        # Get executable steps (respect dependencies)
        executable_steps = self._get_executable_steps(state)

        # Build tasks for parallel execution
        tasks = [self._build_task(step, state) for step in executable_steps]

        # Execute in parallel
        results = await self.executor.execute_parallel(tasks, state)

        # Process results and update state
        for task, result in zip(tasks, results):
            self._process_result(state, task, result)

        # Evaluate decisions
        decision = self.decision_engine.evaluate(state)

        if decision.root_cause:
            state.root_cause = decision.root_cause
            state.confidence = decision.confidence
        elif decision.needs_human:
            state.needs_human = True
            state.human_question = decision.question
        elif decision.next_step:
            state.current_step = decision.next_step

    # 5. Generate result
    return self._generate_result(state)
```

### 3. Thread-Local Client Pattern

```python
class BaseClient:
    """Thread-local connection pattern with retry logic"""

    def __init__(self, max_retries: int = 3):
        self._thread_local = threading.local()
        self.max_retries = max_retries

    def _get_connection(self):
        if not hasattr(self._thread_local, 'conn'):
            self._thread_local.conn = self._create_connection()
        return self._thread_local.conn

    async def execute_with_retry(self, operation, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                else:
                    raise
```

---

## Human Handoff Protocol

The system escalates to human when:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Low Confidence | < 0.7 | Present evidence, ask for guidance |
| Stuck | > 5 steps without progress | Show findings, request direction |
| Contradictory Data | Sources disagree | Highlight contradiction, ask resolution |
| Critical Decision | Affects many loads | Require approval before action |

### Handoff Response Format

```
INVESTIGATION STUCK

Case: SF-12345
Load: U110123982

Evidence Gathered:
- [Platform] Load exists, status = AWAITING_TRACKING_INFO
- [JT] No scraping history found
- [SigNoz] No PROCESS_OCEAN_UPDATE logs

Question for Human:
No data found from JT or SigNoz. Should I:
1. Expand time window search (currently 30 days)
2. Check alternative identifiers
3. Escalate as potential system issue

Please respond with option number or custom instruction.
```

---

## Implementation Phases

| Phase | Description | Deliverables |
|-------|-------------|--------------|
| **Phase 1** | Foundation | Models, Config, Utils |
| **Phase 2** | Data Clients | All 7 client implementations |
| **Phase 3** | Agent Core | Agent, Executor, Decision Engine |
| **Phase 4** | Integration | CLI, Testing, Documentation |

---

## Success Criteria

### Functional
- [ ] Read tickets from Salesforce API
- [ ] Query all 6 data sources successfully
- [ ] Execute steps in parallel where possible
- [ ] Correctly identify root cause for test cases
- [ ] Human handoff works when confidence low

### Performance
- [ ] End-to-end investigation < 5 minutes
- [ ] 85%+ accuracy on known test cases
- [ ] Parallel queries reduce latency by 50%

### Quality
- [ ] Unit tests for decision engine
- [ ] Integration tests with mock data
- [ ] Structured logging for debugging

---

## Dependencies

```
# Core
pydantic>=2.5.0
python-dotenv>=1.0.0

# Async
asyncio
aiohttp>=3.9.0

# Data Clients
psycopg2-binary>=2.9.9          # Redshift
clickhouse-driver>=0.2.7        # ClickHouse
simple-salesforce>=1.12.0       # Salesforce

# LLM
anthropic>=0.40.0               # Claude

# CLI
rich>=13.0.0
click>=8.1.0

# YAML
pyyaml>=6.0
```

---

## Next Steps

1. **Immediate**: Create directory structure and implement Phase 1 (models)
2. **Short-term**: Implement data clients and test connectivity
3. **Medium-term**: Build agent core with decision engine
4. **Validation**: Test against real Salesforce cases

---

## References

- `skills/ocean_debugging/skill_definition.yaml` - Skill definition
- `skills/ocean_debugging/decision_tree.yaml` - Investigation workflow
- `skills/ocean_debugging/api_mappings.yaml` - API configurations
- `skills/ocean_debugging/knowledge_base.md` - Domain knowledge
- `SUPPORT-TEAM-MENTAL-MODEL.md` - Source analysis
- `SUPPORT-SKILLS-AND-TOOLS-CATALOG.md` - Tools catalog

---

*Last Updated: January 13, 2026*
