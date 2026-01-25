# Analysis 09: Gap Analysis - Current State vs Requirements

**Date:** 2026-01-05
**Based On:** All previous analyses + original conversation requirements

---

## Executive Summary

Based on the conversation between Msp Raja and Arpit Garg, the vision was to create a **unified RCA system** that:
1. Helps support teams think faster (not just new tools)
2. Auto-narrows scope (first-focus routing)
3. Encodes human analyst playbook
4. Consolidates scattered data into one view
5. Works with existing habits (logs-first mindset)

**Current Reality:** We have excellent **components** but significant **integration gaps**:
- ✅ Data consolidated (load_replay, rewind-app)
- ✅ Sophisticated RCA pipeline (rca-bot-2.0)
- ⚠️ But: 3 separate systems, no unified interface
- ⚠️ But: No first-focus routing logic
- ⚠️ But: Not MCP-based (massive duplication)
- ⚠️ But: Support SQL catalog (Notion) not integrated

---

## Gap Analysis by Requirement

### Requirement 1: "Help them think, not just give tools"

**Vision (from conversation):**
> "the real unlock is how we help them think… not what tool we give"
>
> "instead of asking support to change habits, system shd quietly do the thinking for them… take an issue, auto narrow scope, rank likely flows / services, and then hand them a smaller log world to play in"

**Current State:**
- ✅ **load_replay.py** + **rewind-app**: Consolidate data into one view
- ✅ Shows: Load metadata, files, callbacks, network status, errors
- ✅ Progressive loading (don't wait for everything)

**Gap:**
- ❌ **No "auto-narrow scope" logic**
  - System shows ALL data, user still decides what to look at
  - No guidance: "For this issue type, start here"
  - No priority ranking: "This is most likely cause"

**What's Needed:**
- First-focus routing decision trees
- "Next Steps" recommendations based on data patterns
- Example: "Load stuck → Network issue detected → Recommendation: Create carrier relationship"

**Score:** ⚠️ **Partial (40%)** - Data consolidated, but no intelligence layer

---

### Requirement 2: "Encode heuristics: for this issue → start here → go deeper only if needed"

**Vision (from conversation):**
> "once that logic is explicit + repeatable, it can plug anywhere… ui, cli, jira intake, agents, etc"

**Current State:**
- ✅ **issue_mappings.yaml**: Documents service dependencies and message flows
- ✅ **domain_rules.yaml**: Known error patterns
- ✅ **data_catalog.yaml**: Documents data sources

**Gap:**
- ❌ **Configuration exists but NOT USED as routing logic**
  - `issue_mappings.yaml` has `dependent_services` but not fully utilized
  - No decision trees: "If category X, check service Y first, then Z"
  - No failure mode logic: "If X fails, likely cause is Y, check Z"

**Example of What's Missing:**
```yaml
# NOT IN CURRENT CONFIG (should be added)
issue_routing:
  awaiting_tracking_info:
    step1:
      check: company_relationships table
      question: "Does relationship exist and is active?"
      if_no: "Create relationship" (action)
      if_yes: proceed to step2
    step2:
      check: fact_carrier_file_logs
      question: "Are carrier files being received?"
      if_no: "Contact carrier to send files" (action)
      if_yes: proceed to step3
    step3:
      check: fact_carrier_record_logs
      question: "Are files matching to loads?"
      if_no: "Check load identifiers in file vs database" (action)
```

**What's Needed:**
- Decision tree YAML format
- Router module that reads decision trees
- Integration with UI/CLI to guide users

**Score:** ⚠️ **Partial (30%)** - Config exists, routing logic doesn't

---

### Requirement 3: "Human analyst playbook: Load Search → Files → Callbacks → Metrics → Logs"

**Vision (from conversation):**
> "support and ops has this mental playbook via LOGS - and we have tried around 2-3 wide spread projects which lasted for 3 -6 months - where team build some consolited API or CLI tools for them to use - but they just cant come out of logs"

**Current State:**
- ✅ **load_replay.py** implements this exact playbook:
  1. Load Search ✅ (get_load_metadata)
  2. Files ✅ (get_carrier_file_stats, get_shipper_file_stats)
  3. Callbacks ✅ (get_callbacks - partial)
  4. Metrics ✅ (get_error_stats)
  5. Logs ✅ (integrated with ClickHouse)

- ✅ **rewind-app** implements same with web UI

**Gap:**
- ⚠️ **Playbook is implicit in code, not explicit**
  - Code shows WHAT to query, not WHY
  - No documentation of analyst decision process
  - No explanation: "We check files first because..."

- ⚠️ **No visual workflow**
  - Could show: "You are here: Step 2 of 5 (Files)"
  - Could show: "Next: Check callbacks if files are clean"

**What's Needed:**
- Document analyst decision process
- Add workflow visualization to UI
- Add "Why am I seeing this?" explanations

**Score:** ✅ **Good (80%)** - Playbook implemented, needs documentation

---

### Requirement 4: "Support SQL Catalog (Notion) integration"

**Vision (from conversation):**
> "Also I am planning to integrate support SQL catalog (they are buidlign a repo/catalog in Notion which would contain usecases and the search query,SQL for that ccase for signoz, SPOG (Trino DB))"

**Current State:**
- ❌ **NOT INTEGRATED**
- Support team maintains SQL queries in Notion
- These queries are **human-validated** for specific use cases

**Gap:**
- ❌ No Notion API client
- ❌ No integration with RCA bot or rewind-app
- ❌ Duplicate effort: Support team builds queries in Notion, engineers build queries in code

**What's Needed:**
- Notion API integration
- Query catalog sync (Notion → data_catalog.yaml or separate catalog)
- "Similar Issue" matching: Query Notion catalog for issues like current one
- Use proven queries instead of generating new ones

**Score:** ❌ **Missing (0%)** - Critical gap, mentioned but not implemented

---

### Requirement 5: "Common agent framework (audit, security, standards)"

**Vision (from conversation):**
> "this may be more focusedon HR side.. but my thought is we shoudl have some common practices, concepts, frameworks used along the agents - like basic audit, security etc. today i dont think we hvae it in place anywhere"

**Current State:**
- ⚠️ **12 MCP servers, each team did their own thing**
- ⚠️ No common auth pattern (some HMAC, some Basic, some PAT)
- ⚠️ No common logging standard
- ⚠️ No common error handling
- ⚠️ No audit trail (who queried what, when)
- ⚠️ No security review process

**Gap:**
- ❌ No governance framework
- ❌ No mandatory standards
- ❌ No security baseline
- ❌ No audit logging

**What's Needed:**
- MCP Server Standards Document
- Mandatory security review
- Centralized audit logging (OpenTelemetry)
- Secret management (AWS Secrets Manager)
- Access control (who can use which MCP server)

**Score:** ❌ **Missing (10%)** - Critical organizational gap

---

### Requirement 6: "MCP-based architecture (not monolithic clients)"

**Vision:** Implied from conversation about consolidation and reuse

**Current State:**
- ✅ **12 MCP servers exist**
- ❌ **RCA Bot and rewind-app don't use them**
  - Both implement own clients
  - 70% duplication rate
  - 6+ clients duplicated 2-4 times

**Gap:**
- ❌ RCA Bot still uses direct clients (ClickHouseClient, RedshiftClient, etc.)
- ❌ rewind-app still uses direct clients
- ❌ load_replay.py still uses direct clients
- ❌ No unified MCP orchestration layer

**What's Needed:**
- Convert all clients → MCP calls
- Create missing MCP servers (GitHub, Trino, Confluence, Company API)
- Unified MCP gateway/router
- Retire direct client implementations

**Score:** ⚠️ **Partial (30%)** - MCP servers exist, not used by main systems

---

### Requirement 7: "Multi-agent orchestration (parallel evidence collection)"

**Vision:** From TECHNICAL_DESIGN.md (Phase 2)

**Current State:**
- ✅ **load_replay.py**: Uses ThreadPoolExecutor for parallel queries
- ✅ **rewind-app**: Stage 3 sections run in parallel
- ❌ **rca_bot.py**: Sequential 10-step pipeline (not parallel)

**Gap:**
- ❌ No LangGraph or multi-agent framework
- ❌ No independent agents (logs agent, code agent, metrics agent)
- ❌ No parallel evidence collection with coordination
- ❌ Single orchestrator, not multi-agent

**What's Needed:**
- LangGraph implementation
- Define agent types: LogsAgent, CodeAgent, MetricsAgent, DocsAgent
- Coordinator agent merges results
- Agents run independently, report back

**Score:** ⚠️ **Partial (20%)** - Parallel queries exist, not true multi-agent

---

### Requirement 8: "Visual timeline generation (Mermaid diagrams)"

**Vision:** From Phase 4 roadmap

**Current State:**
- ❌ **NOT IMPLEMENTED**
- Text-only reports and tables
- No visual execution flow
- No sequence diagrams

**Gap:**
- ❌ No Mermaid diagram generation
- ❌ No visual timeline
- ❌ No execution flow visualization

**What's Needed:**
- Generate Mermaid sequence diagrams from correlation IDs
- Show: Service A → Service B → Service C with timestamps
- Embed diagrams in reports (GitHub/Confluence/Jira render Mermaid)

**Score:** ❌ **Missing (0%)** - Future feature

---

### Requirement 9: "Feedback loop / continuous learning"

**Vision:** From success metrics and Phase 3

**Current State:**
- ❌ **NO FEEDBACK TRACKING**
- No metrics: Was RCA helpful?
- No tracking: Was classification correct?
- No measurement: Did fix work?

**Gap:**
- ❌ No user feedback mechanism
- ❌ No outcome tracking
- ❌ No learning from results
- ❌ No metrics dashboard

**What's Needed:**
- Add feedback buttons: "Was this helpful?" (Yes/No)
- Track: Classification accuracy (manual review)
- Track: Fix success rate (automated testing)
- Dashboard: RCA metrics, accuracy trends
- Use data to improve: Retrain classifiers, adjust confidence thresholds

**Score:** ❌ **Missing (0%)** - Critical for improvement

---

### Requirement 10: "Consolidation (not fragmentation)"

**Vision (from conversation):**
> "so in short - what i am seeing is that we are all over places with agents, mcpserver - each team BU is alreayd moved ahead with what they want.. but I am trying to give it a thought of first understanding what we have, what cata log we have etc.."

**Current State:**
- ⚠️ **High fragmentation:**
  - 3 implementations of Load Replay (CLI, web UI in POC, rewind-app)
  - 12 MCP servers built independently
  - 2 implementations of RCA (basic in rewind-app, advanced in rca-bot-2.0)
  - Duplicate clients everywhere (70% duplication)

**Gap:**
- ❌ No central registry of agents/servers
- ❌ No coordination between teams
- ❌ No review process before building new server
- ❌ Multiple tools instead of one unified system

**What's Needed:**
- **Immediate:** Retire duplicate implementations
  - Keep: rewind-app (web UI)
  - Migrate: rca-bot-2.0 capabilities → rewind-app
  - Retire: load_replay.py CLI, web_ui POC
- **Medium-term:** MCP server registry
- **Long-term:** Governance to prevent future duplication

**Score:** ❌ **Poor (20%)** - High duplication, no coordination

---

## Architecture Gaps

### Gap 1: No Unified Interface

**Current:**
```
User
  ├─ rewind-app (web) → Load Replay
  ├─ rca-bot-2.0 (CLI) → Advanced RCA
  └─ Cassey agent (?) → Basic triage
```

**Should Be:**
```
User → rewind-app (unified web UI)
          ├─ Load Replay (existing)
          ├─ Advanced RCA (from rca-bot-2.0)
          └─ Quick Triage (Cassey logic)
```

**Impact:** Users need multiple tools, confusion

---

### Gap 2: No MCP Layer

**Current:**
```
Tool → Direct Client → Database/API
```

**Should Be:**
```
Tool → MCP Client → MCP Server → Database/API
```

**Impact:** 70% duplication, inconsistent implementations

---

### Gap 3: No Routing Intelligence

**Current:**
```
User describes issue → System queries ALL data → User decides what to look at
```

**Should Be:**
```
User describes issue → System classifies → Routing logic determines priority
→ System queries relevant data FIRST → Presents narrowed view → User investigates
```

**Impact:** Cognitive overload, slow triage

---

### Gap 4: No Catalog-Driven Code

**Current:**
```
Code has hard-coded SQL queries
Config YAMLs exist but not used by code
```

**Should Be:**
```
Code reads queries from data_catalog.yaml
Code reads routing logic from issue_routing.yaml
Code reads domain patterns from domain_rules.yaml
```

**Impact:** Config files not living documents, require code changes

---

## Summary by Category

### Data Access & Integration

| Requirement | Status | Score | Priority |
|-------------|--------|-------|----------|
| Data consolidation | ✅ Good | 80% | Low (done) |
| MCP architecture | ⚠️ Partial | 30% | **HIGH** |
| Duplicate elimination | ❌ Poor | 20% | **HIGH** |
| Support SQL catalog | ❌ Missing | 0% | **MEDIUM** |

### Intelligence & Routing

| Requirement | Status | Score | Priority |
|-------------|--------|-------|----------|
| First-focus routing | ❌ Missing | 0% | **CRITICAL** |
| Auto-narrow scope | ⚠️ Partial | 40% | **HIGH** |
| Heuristic encoding | ⚠️ Partial | 30% | **HIGH** |
| Visual timeline | ❌ Missing | 0% | LOW |

### Architecture & Governance

| Requirement | Status | Score | Priority |
|-------------|--------|-------|----------|
| Common framework | ❌ Missing | 10% | **HIGH** |
| Multi-agent | ⚠️ Partial | 20% | MEDIUM |
| Feedback loop | ❌ Missing | 0% | **HIGH** |
| Consolidation | ❌ Poor | 20% | **CRITICAL** |

### Analyst Experience

| Requirement | Status | Score | Priority |
|-------------|--------|-------|----------|
| Playbook implementation | ✅ Good | 80% | Low (done) |
| "Next Steps" guidance | ⚠️ Partial | 40% | **HIGH** |
| Works with habits | ✅ Good | 85% | Low (done) |
| One unified tool | ❌ Poor | 30% | **CRITICAL** |

---

## Critical Gaps (Top 5)

### 1. ❌ No First-Focus Routing Logic (CRITICAL)

**Impact:** Support teams get ALL data, still decide where to start
**Solution:** Implement decision tree routing with `issue_routing.yaml`
**Effort:** Medium (2-3 weeks)

### 2. ❌ Three Separate Systems, No Consolidation (CRITICAL)

**Impact:** User confusion, duplicate maintenance
**Solution:** Migrate rca-bot-2.0 → rewind-app, retire duplicates
**Effort:** High (1-2 months)

### 3. ⚠️ No MCP Architecture, 70% Duplication (HIGH)

**Impact:** Massive code duplication, inconsistent implementations
**Solution:** Create missing MCP servers, convert clients → MCP calls
**Effort:** High (2-3 months)

### 4. ❌ No Common Framework/Governance (HIGH)

**Impact:** Teams build without coordination, proliferation continues
**Solution:** Establish standards, review process, mandatory patterns
**Effort:** Medium (coordination, not code)

### 5. ❌ Support SQL Catalog Not Integrated (MEDIUM)

**Impact:** Missing human-validated knowledge, duplicate query effort
**Solution:** Notion API integration, query sync
**Effort:** Low (1-2 weeks)

---

## What's Working Well (Don't Break)

### Strengths to Preserve

1. ✅ **Drain3 → LLM Pipeline**
   - Proven, optimal approach
   - 95% token savings
   - Don't change this

2. ✅ **Data Consolidation**
   - load_replay and rewind-app work well
   - One-screen view is valuable
   - Keep this UX

3. ✅ **Configuration YAMLs**
   - Encode institutional knowledge
   - Easy to extend
   - Preserve and enhance

4. ✅ **Parallel Query Execution**
   - 54% faster than sequential
   - Good user experience
   - Keep this pattern

5. ✅ **Code Flow Analysis**
   - Neo4j validation is unique
   - Increases confidence
   - Expand this

---

## Recommendations Priority

### P0 (Critical - Do First)

1. **Consolidate Systems**
   - Migrate rca-bot-2.0 RCA → rewind-app backend
   - Retire: load_replay CLI, web_ui POC
   - Single web UI for all capabilities

2. **Implement First-Focus Routing**
   - Create `issue_routing.yaml` with decision trees
   - Add Router module
   - Integrate with UI

### P1 (High - Do Next)

3. **Convert to MCP Architecture**
   - Create missing MCP servers (GitHub, Trino, Confluence, Company API)
   - Migrate rewind-app clients → MCP calls
   - Retire direct client implementations

4. **Establish Governance**
   - Document MCP server standards
   - Mandatory security review
   - Central server registry

5. **Add "Next Steps" Guidance**
   - Based on data patterns, recommend actions
   - Example: "Network issue detected → Create relationship"

### P2 (Medium - Can Wait)

6. **Integrate Support SQL Catalog**
   - Notion API integration
   - Query sync
   - Similar issue matching

7. **Add Feedback Loop**
   - User feedback buttons
   - Outcome tracking
   - Metrics dashboard

### P3 (Low - Future)

8. **Multi-Agent Orchestration**
   - LangGraph implementation
   - Independent agents

9. **Visual Timeline Generation**
   - Mermaid diagrams
   - Execution flow visualization

---

## Success Metrics (How to Measure Progress)

### Phase 1: Consolidation (3 months)
- ✅ Single web UI (rewind-app) with all capabilities
- ✅ Duplicate implementations retired
- ✅ First-focus routing implemented
- **Metric:** Time to RCA reduced by 30% (measured by time from ticket → resolution)

### Phase 2: MCP Architecture (6 months)
- ✅ All direct clients replaced with MCP calls
- ✅ 70% duplication eliminated
- ✅ Common standards established
- **Metric:** Code lines reduced by 50%, maintenance effort reduced

### Phase 3: Intelligence (9 months)
- ✅ Support SQL catalog integrated
- ✅ Feedback loop operational
- ✅ "Next Steps" guidance live
- **Metric:** 90% of issues have actionable next step, user satisfaction >4.0/5.0

### Phase 4: Automation (12 months)
- ✅ Multi-agent orchestration
- ✅ Visual timelines
- ✅ 60% automation rate (no human input needed)
- **Metric:** 60% of issues auto-resolved, human intervention only for complex cases

---

**Status:** ✅ Gap Analysis Complete
**Next:** Create consolidated analysis report with recommendations
