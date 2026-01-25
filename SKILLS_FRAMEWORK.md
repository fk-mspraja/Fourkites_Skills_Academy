# Skills-Based Agent Framework - Architecture Design

**Purpose:** Reusable, composable agent architecture for RCA investigations
**Date:** January 13, 2026
**Status:** POC Design Phase

---

## Core Concept

**Instead of:** One monolithic RCA bot that tries to handle everything
**Build:** Router + specialized skills, each an expert in one domain

**Benefits:**
- ✅ **Maintainable:** Each skill is independent, can be updated without breaking others
- ✅ **Testable:** Test each skill in isolation
- ✅ **Scalable:** Add new skills without rewriting existing ones
- ✅ **Transferable:** Same framework works for HR, IT, Finance, etc.

---

## Architecture Patterns

### Pattern 1: Router + Skills

```
                  ┌─────────────┐
                  │   Router    │ ← Single entry point
                  │   Agent     │ ← Routes to skills
                  └──────┬──────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ↓                ↓                ↓
   ┌────────┐      ┌────────┐      ┌────────┐
   │ Skill  │      │ Skill  │      │ Skill  │
   │   A    │      │   B    │      │   C    │
   └────────┘      └────────┘      └────────┘
    Ocean          Carrier/OTR     DY Ops
```

**Router responsibilities:**
- Classify incoming question
- Select appropriate skill
- Pass context to skill
- Aggregate results if multiple skills needed

**Skill responsibilities:**
- Execute domain-specific investigation
- Maintain state within investigation
- Return structured results
- Trigger human handoff when stuck

### Pattern 2: State Machine per Skill

Each skill has a decision tree that's executed as a state machine:

```
┌─────────────────────────────────────────────┐
│ Skill: Ocean Debugging                      │
│                                              │
│  State: INIT                                 │
│    ↓                                         │
│  State: CHECK_NETWORK                        │
│    ├─ Result: NO_RELATIONSHIP → END          │
│    ├─ Result: INACTIVE → END                 │
│    └─ Result: OK → CHECK_FILES               │
│                                              │
│  State: CHECK_FILES                          │
│    ├─ Result: NO_FILES → END                 │
│    └─ Result: FILES_EXIST → CHECK_MATCHING   │
│                                              │
│  State: CHECK_MATCHING                       │
│    ├─ Result: NO_MATCHES → END               │
│    ├─ Result: FAILED → END                   │
│    └─ Result: SUCCESS → ESCALATE             │
│                                              │
│  State: END                                  │
│    └─ Return: Root cause + evidence          │
└─────────────────────────────────────────────┘
```

### Pattern 3: Human-in-the-Loop

```
Agent investigating...
    ↓
Confidence drops OR stuck
    ↓
┌────────────────────────────┐
│ Handoff to Human           │
│                            │
│ "I found:                  │
│  - Network: Active         │
│  - Files: Received         │
│  - Matching: Zero matches  │
│                            │
│ What should I check next?" │
│                            │
│ [Option A] [Option B] [C]  │
└────────────────────────────┘
    ↓
Human selects Option A
    ↓
Agent resumes with guidance
```

**Key:** Agent doesn't fail, it asks for help

---

## Skill Anatomy

### Complete Skill Structure

```
skills/ocean_debugging/
├── skill_definition.yaml     ← What this skill does, when to use it
├── decision_tree.yaml        ← Step-by-step investigation flow
├── api_mappings.yaml         ← Which APIs/DBs to query at each step
├── knowledge_base.md         ← Domain knowledge (Confluence, tribal knowledge)
├── test_cases/               ← Real tickets for validation
│   ├── case_network_missing.yaml
│   ├── case_no_files.yaml
│   └── case_identifier_mismatch.yaml
└── prompts/                  ← LLM prompts for this skill
    ├── classify.txt
    ├── analyze_results.txt
    └── generate_hypothesis.txt
```

### skill_definition.yaml

```yaml
skill:
  id: "ocean_debugging"
  name: "Ocean Shipment Debugging"
  version: "1.0.0"
  owner: "Surya (Support Team)"
  status: "poc"

  description: |
    Debug ocean shipment tracking issues including:
    - Load not tracking (Awaiting Tracking Info)
    - Wrong vessel departure dates
    - Missing milestones
    - ETA discrepancies

  triggers:
    # When router sees these, invoke this skill
    keywords:
      - "not tracking"
      - "awaiting tracking info"
      - "vessel departure"
      - "ocean"
      - "container"
      - "booking"

    issue_categories:
      - "load_not_tracking"
      - "eta_issues"
      - "milestone_wrong"

    conditions:
      - "load.mode == 'OCEAN'"

  capabilities:
    # What can this skill do?
    - id: "check_network_relationship"
      description: "Verify carrier-shipper relationship exists"
      confidence: "high"

    - id: "check_carrier_files"
      description: "Verify carrier sending files"
      confidence: "high"

    - id: "check_file_matching"
      description: "Verify files matching to loads"
      confidence: "medium"

    - id: "analyze_signoz_logs"
      description: "Deep dive into processing logs"
      confidence: "medium"

  data_sources:
    redshift:
      tables:
        - "company_relationships"
        - "fact_carrier_file_logs"
        - "fact_carrier_record_logs"
        - "load_validation_data_mart"
      credentials: "aws_iam"

    clickhouse:
      service: "signoz"
      logs:
        - "multimodel_carrier_updates_worker"
      credentials: "env:SIGNOZ_TOKEN"

    apis:
      justtransform:
        endpoint: "https://jt-api.internal/v1"
        auth: "basic"
        credentials: "env:JT_USERNAME,JT_PASSWORD"

      super_api:
        endpoint: "https://api.fourkites.internal/super"
        auth: "api_key"
        credentials: "env:SUPER_API_KEY"

  decision_tree:
    path: "decision_tree.yaml"
    entry_point: "step_1_network_relationship"

  human_handoff:
    # When to ask for human help
    triggers:
      low_confidence:
        threshold: 0.7
        action: "Ask human to verify results"

      stuck_after_steps:
        max_steps: 5
        action: "Present findings and ask for guidance"

      contradictory_data:
        action: "Ask human to resolve contradiction"

      critical_decision:
        actions:
          - "create_relationship"
          - "escalate_to_engineering"
        action: "Get human approval before proceeding"

  output_format:
    # Structured result format
    type: "investigation_result"
    fields:
      - "root_cause"
      - "evidence"
      - "confidence_score"
      - "recommended_action"
      - "time_to_investigate"
      - "steps_completed"

  metrics:
    # Track effectiveness
    target_time: "20 minutes"
    baseline_time: "40 minutes"
    expected_accuracy: "85%"
```

### decision_tree.yaml

```yaml
# Ocean Debugging Decision Tree
# Based on: Surya's documented workflow (SUPPORT-TEAM-MENTAL-MODEL.md)

entry_point: "step_1_network_relationship"

steps:

  step_1_network_relationship:
    name: "Check Network Relationship"
    description: "Verify carrier-shipper relationship exists and is active"

    pre_conditions:
      - "load.carrier_id is not null"
      - "load.shipper_id is not null"

    action:
      type: "query"
      source: "redshift"
      query_template: |
        SELECT
          relationship_id,
          status,
          is_active,
          created_date
        FROM company_relationships
        WHERE shipper_id = '{load.shipper_id}'
          AND carrier_id = '{load.carrier_id}'

    decisions:

      no_relationship:
        condition: "result.count == 0"
        confidence: 0.95
        conclusion:
          root_cause: "Network relationship missing"
          explanation: |
            Carrier-shipper relationship does not exist in system.
            This is the #1 cause of 'Awaiting Tracking Info' (7.7% of loads).
          impact: "critical"
          recommended_action:
            action: "create_relationship"
            priority: "immediate"
            human_approval_required: true
        next_step: null  # Investigation complete

      relationship_inactive:
        condition: "result.is_active == false"
        confidence: 0.90
        conclusion:
          root_cause: "Network relationship inactive"
          explanation: "Relationship exists but is not active"
          recommended_action:
            action: "activate_relationship"
            human_approval_required: true
        next_step: null  # Investigation complete

      relationship_active:
        condition: "result.is_active == true"
        confidence: 0.85
        conclusion:
          partial_finding: "Network relationship is active"
          explanation: "Relationship OK, issue is elsewhere"
        next_step: "step_2_carrier_files"

  step_2_carrier_files:
    name: "Check Carrier File Reception"
    # ... (similar structure)

  step_3_file_matching:
    name: "Check File Matching"
    # ... (similar structure)

# Parallel investigation paths
parallel_checks:
  - "step_signoz_logs"
  - "step_justtransform_history"

# Can run these in parallel with main decision tree
# Results merged at end
```

### api_mappings.yaml

```yaml
# API Mappings - Which API calls correspond to which investigation steps

mappings:

  check_network_relationship:
    api: "redshift"
    query: "company_relationships_query"
    params:
      required:
        - "shipper_id"
        - "carrier_id"
    response_schema:
      type: "object"
      fields:
        - name: "relationship_id"
          type: "string"
        - name: "is_active"
          type: "boolean"
    cache_ttl: 3600  # Cache for 1 hour

  check_carrier_files:
    api: "redshift"
    query: "fact_carrier_file_logs_query"
    params:
      required:
        - "carrier_id"
        - "date_range"
    response_schema:
      type: "array"
      item_type: "file_record"

  get_signoz_logs:
    api: "clickhouse"
    query_builder: "signoz_query_builder"
    params:
      service: "multimodel_carrier_updates_worker"
      keyword: "PROCESS_OCEAN_UPDATE"
      time_range: "last_30_days"
    response_parser: "signoz_log_parser"
    cache_ttl: 300  # 5 minutes
```

---

## Implementation Patterns

### Router Agent Implementation

```python
# router_agent.py

class RouterAgent:
    """
    Supervisor agent that routes questions to specialized skills
    """

    def __init__(self, skills_directory: str):
        self.skills = self._load_skills(skills_directory)
        self.llm = LLMClient()

    def route(self, question: str, context: dict) -> InvestigationResult:
        """
        Main entry point
        """
        # Step 1: Classify question
        skill_name = self._classify_question(question, context)

        # Step 2: Get skill
        skill = self.skills[skill_name]

        # Step 3: Execute skill
        result = skill.investigate(context)

        return result

    def _classify_question(self, question: str, context: dict) -> str:
        """
        Determine which skill to use
        """
        # Try pattern matching first (fast)
        for skill in self.skills.values():
            if self._matches_patterns(question, skill.triggers):
                return skill.id

        # Fall back to LLM classification (slower but smarter)
        prompt = f"""
        Question: {question}
        Context: {context}
        Available skills: {[s.name for s in self.skills.values()]}

        Which skill should handle this question?
        """
        return self.llm.classify(prompt)
```

### Skill Base Class

```python
# skill_base.py

class Skill(ABC):
    """
    Base class for all skills
    """

    def __init__(self, skill_dir: str):
        self.definition = self._load_yaml(f"{skill_dir}/skill_definition.yaml")
        self.decision_tree = self._load_yaml(f"{skill_dir}/decision_tree.yaml")
        self.api_mappings = self._load_yaml(f"{skill_dir}/api_mappings.yaml")
        self.state_machine = StateMachine(self.decision_tree)

    @abstractmethod
    def investigate(self, context: dict) -> InvestigationResult:
        """
        Execute investigation following decision tree
        """
        pass

    def execute_step(self, step_name: str, context: dict) -> StepResult:
        """
        Execute one step of decision tree
        """
        step = self.decision_tree['steps'][step_name]

        # Execute query/action
        data = self._execute_action(step['action'], context)

        # Evaluate decision logic
        decision = self._evaluate_decisions(step['decisions'], data)

        # Update state
        self.state_machine.transition(decision)

        # Check if need human input
        if decision.confidence < 0.7:
            return self._handoff_to_human(step_name, data, decision)

        # Continue or end
        if decision.next_step:
            return self.execute_step(decision.next_step, context)
        else:
            return self._format_result(decision)
```

### State Machine

```python
# state_machine.py

class StateMachine:
    """
    Manages investigation state
    """

    def __init__(self, decision_tree: dict):
        self.tree = decision_tree
        self.current_state = decision_tree['entry_point']
        self.history = []
        self.evidence = []

    def transition(self, decision: Decision):
        """
        Move to next state based on decision
        """
        self.history.append({
            'from_state': self.current_state,
            'decision': decision.name,
            'confidence': decision.confidence,
            'timestamp': datetime.now()
        })

        self.current_state = decision.next_step
        self.evidence.append(decision.evidence)

    def get_state(self) -> dict:
        """
        Serialize current state for human handoff or resume
        """
        return {
            'current_state': self.current_state,
            'history': self.history,
            'evidence': self.evidence,
            'can_resume': True
        }

    def restore_state(self, saved_state: dict):
        """
        Resume from saved state
        """
        self.current_state = saved_state['current_state']
        self.history = saved_state['history']
        self.evidence = saved_state['evidence']
```

---

## Adding New Skills

### Process to Add a New Skill:

1. **Document workflow** (shadow support analyst)
2. **Create skill directory** (`skills/new_skill/`)
3. **Define skill** (`skill_definition.yaml`)
4. **Create decision tree** (`decision_tree.yaml`)
5. **Map APIs** (`api_mappings.yaml`)
6. **Write prompts** (`prompts/`)
7. **Create test cases** (`test_cases/`)
8. **Implement skill class** (inherit from `Skill` base)
9. **Test in isolation** (unit tests)
10. **Register with router** (add to skills directory)

**Time estimate:** 2-3 days per skill

---

## Testing Strategy

### Unit Tests: Each Skill Independently

```python
def test_ocean_debugging_network_missing():
    """
    Test: Network relationship missing case
    """
    skill = OceanDebuggingSkill()

    context = {
        'load': {
            'id': 'U123',
            'carrier_id': 'CARR123',
            'shipper_id': 'SHIP456'
        }
    }

    # Mock database response: No relationship
    mock_db_return = []

    result = skill.investigate(context)

    assert result.root_cause == "Network relationship missing"
    assert result.confidence > 0.9
    assert result.recommended_action == "create_relationship"
```

### Integration Tests: Router + Skill

```python
def test_router_selects_correct_skill():
    """
    Test: Router routes to ocean debugging
    """
    router = RouterAgent('skills/')

    question = "Why is load U123 not tracking?"
    context = {'load': {'mode': 'OCEAN'}}

    result = router.route(question, context)

    assert result.skill_used == "ocean_debugging"
```

### End-to-End Tests: Real Tickets

```python
def test_real_ticket_network_missing():
    """
    Test: Known ticket from last week
    """
    router = RouterAgent('skills/')

    # Real ticket data
    ticket = load_ticket('SF-12345')

    result = router.route(ticket.description, ticket.context)

    # Compare to known root cause
    assert result.root_cause == ticket.actual_root_cause
```

---

## Deployment Considerations

### POC Phase (Week 1):
- **Platform:** Local Python script
- **LLM:** Claude API (via Anthropic SDK)
- **State:** In-memory (no persistence)
- **UI:** Command-line interface

### Demo Phase (Week 2):
- **Platform:** Docker container
- **LLM:** Same
- **State:** Redis (for handoff resume)
- **UI:** Simple web interface (FastAPI + React)

### Production Phase (Future):
- **Platform:** Kubernetes
- **LLM:** Multi-model support (Claude primary, GPT fallback)
- **State:** PostgreSQL + Redis
- **UI:** Salesforce integration
- **Monitoring:** OpenTelemetry → SignOz
- **Secrets:** AWS Secrets Manager

---

## Open Architecture Questions

### For Discussion:

1. **Should skills be stateless or stateful?**
   - Stateless: Easier to scale, but harder to resume
   - Stateful: Better UX, but more complex

2. **Should router use LLM or rules?**
   - LLM: Flexible, handles novel questions
   - Rules: Fast, predictable, cheaper

3. **Should skills communicate with each other?**
   - Yes: Could combine insights (ocean skill → carrier skill)
   - No: Keeps them independent, simpler

4. **How to version skills?**
   - Git branches per skill?
   - Semantic versioning (1.0.0)?
   - Router can select skill version?

5. **How to handle conflicting skills?**
   - Multiple skills claim to handle same question
   - Router picks highest confidence?
   - Ask human to choose?

---

## Success Metrics

### Track These for Each Skill:

**Performance:**
- Time to complete investigation
- Number of steps executed
- API calls made

**Accuracy:**
- Correct root cause identified
- False positive rate
- Human handoff frequency

**Adoption:**
- Number of investigations run
- Repeat usage rate
- User satisfaction score

**Cost:**
- LLM tokens used
- API call costs
- Infrastructure costs

---

**Status:** ✅ Framework design complete
**Next:** Build POC with ocean_debugging skill
**Owner:** MSP Raja
**Last Updated:** 2026-01-13
