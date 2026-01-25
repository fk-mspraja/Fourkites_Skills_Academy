# Auto-RCA Architecture: How Sub-Agents Reach Consensus

## 🎯 Core Innovation: Hypothesis-Driven Investigation

Instead of following fixed steps, the system uses **parallel hypothesis testing** with autonomous sub-agents that adapt based on evidence.

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│                     Load ID: 618171104                           │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               PHASE 1: Identifier Extraction                     │
│                                                                  │
│  • Extract load_id from ticket/input                            │
│  • Fetch initial tracking data (Platform API)                   │
│  • Enrich: carrier_id, shipper_id, container_number, etc.       │
│                                                                  │
│  Output: {load_id, carrier_id, shipper_id, ...}                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: Hypothesis Formation (LLM)                 │
│                                                                  │
│  LLM Prompt:                                                    │
│  "Given this load with status 'Awaiting Tracking Info',         │
│   what are the most likely root causes?"                        │
│                                                                  │
│  LLM Returns 5 Hypotheses:                                      │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ H1: "Network relationship missing" (conf=0.25)       │        │
│  │ H2: "JT scraping failed" (conf=0.25)                 │        │
│  │ H3: "Carrier portal down" (conf=0.20)                │        │
│  │ H4: "Subscription inactive" (conf=0.15)              │        │
│  │ H5: "Identifier mismatch" (conf=0.15)                │        │
│  └─────────────────────────────────────────────────────┘        │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 3: Parallel Sub-Agent Investigation             │
│                                                                  │
│  Spawn 5 Sub-Agents (one per hypothesis)                        │
│  Each runs independently with max 5 iterations                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ SubAgent-H1  │  │ SubAgent-H2  │  │ SubAgent-H3  │  ...     │
│  │ (Network)    │  │ (JT Check)   │  │ (Carrier)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         │    EACH AGENT LOOP (max 5 iterations):                │
│         │    ┌──────────────────────────────────┐               │
│         │    │ 1. LLM: "What should I query?"   │               │
│         │    │    → Decides data source & method│               │
│         │    │                                   │               │
│         │    │ 2. Execute query (API/DB)        │               │
│         │    │    → Get evidence                 │               │
│         │    │                                   │               │
│         │    │ 3. LLM: "Does this support H1?"  │               │
│         │    │    → Update confidence            │               │
│         │    │                                   │               │
│         │    │ 4. If confidence > 0.9: CONFIRMED │               │
│         │    │    If confidence < 0.1: ELIMINATED│               │
│         │    │    Else: Continue investigating   │               │
│         │    └──────────────────────────────────┘               │
│         │                                                         │
│         ▼                                                         │
│    Evidence collected & confidence updated in real-time         │
│                                                                  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                PHASE 4: Consensus Synthesis (LLM)                │
│                                                                  │
│  Input to LLM:                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ ALL Hypotheses + Final Confidence:                   │       │
│  │ • H1: 0.85 (Network relationship inactive)           │       │
│  │ • H2: 0.10 (JT scraping - eliminated)                │       │
│  │ • H3: 0.05 (Carrier portal - eliminated)             │       │
│  │ • H4: 0.05 (Subscription - eliminated)               │       │
│  │ • H5: 0.50 (Identifier mismatch - possible)          │       │
│  │                                                       │       │
│  │ ALL Evidence (15 pieces):                            │       │
│  │ • company_api: "Relationship exists but INACTIVE"    │       │
│  │ • tracking_api: "Load in awaiting state"             │       │
│  │ • super_api: "Subscription is active"                │       │
│  │ • ... (all other evidence)                           │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  LLM Synthesis Prompt:                                          │
│  "Given all hypotheses and evidence, determine:                 │
│   1. Most likely root cause                                     │
│   2. Confidence level (0.0-1.0)                                 │
│   3. Recommended actions                                        │
│   4. Remaining uncertainties"                                   │
│                                                                  │
│  LLM Response (CONSENSUS):                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Root Cause: "network_relationship_inactive"          │       │
│  │ Confidence: 0.85                                      │       │
│  │ Explanation: "H1 has highest confidence with strong  │       │
│  │              evidence from company_api showing        │       │
│  │              relationship is INACTIVE since Dec 2025. │       │
│  │              H2-H4 were eliminated. H5 is possible    │       │
│  │              but less likely than H1."                │       │
│  │ Action: "Reactivate shipper-carrier relationship     │       │
│  │          in FourKites Network Admin"                  │       │
│  └──────────────────────────────────────────────────────┘       │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FINAL RESULT RETURNED                        │
│                                                                  │
│  InvestigationResult {                                          │
│    root_cause: "network_relationship_inactive",                 │
│    confidence: 0.85,                                            │
│    category: "CONFIGURATION_ISSUE",                             │
│    evidence: [15 pieces],                                       │
│    recommended_action: "Reactivate relationship...",            │
│    investigation_time: 45.2s                                    │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Sub-Agent Behavior

### Example: SubAgent-H1 (Network Checker)

**Hypothesis**: "Network relationship between shipper and carrier is missing" (initial confidence: 0.25)

**Iteration 1:**
```
LLM Decision:
  "To test if relationship exists, query company_api"

Action: query_data_source
  source: company_api
  method: get_company_relationship
  params: {} (auto-filled: shipper_id, carrier_id)

Execute Query → Response:
  { "exists": true, "status": "INACTIVE", "deactivated_date": "2025-12-15" }

Convert to Evidence:
  finding: "Relationship exists but status is INACTIVE"
  source: company_api

LLM Evaluation:
  "This SUPPORTS the hypothesis - relationship exists but inactive is similar to missing"

Update Confidence: 0.25 → 0.60
```

**Iteration 2:**
```
LLM Decision:
  "High confidence! Need more evidence to confirm. Check if similar loads affected."

Action: query_data_source
  source: redshift
  method: find_similar_stuck_loads
  params: {} (auto-filled: carrier_id)

Execute Query → Response:
  { "affected_loads": 12, "all_same_shipper": true }

Evidence:
  finding: "12 similar loads affected, all same shipper-carrier pair"

LLM Evaluation:
  "This STRONGLY SUPPORTS - pattern confirms relationship issue"

Update Confidence: 0.60 → 0.85
```

**Iteration 3:**
```
LLM Decision:
  "Confidence is 0.85 (>0.9 threshold not quite reached). Conclude investigation."

Action: conclude
  reason: "Strong evidence collected, relationship inactive confirmed"

SubAgent-H1 COMPLETE:
  status: active (not quite confirmed, but very likely)
  confidence: 0.85
  evidence: 2 pieces
  iterations: 3
```

---

## 🤝 How Consensus is Reached

### Step-by-Step Consensus Process

1. **All Sub-Agents Complete**
   - Each returns: hypothesis + confidence + evidence
   - Example:
     ```
     H1: 0.85 (2 evidence pieces)
     H2: 0.10 (0 evidence - eliminated)
     H3: 0.05 (1 contradicting evidence)
     H4: 0.05 (1 contradicting evidence)
     H5: 0.50 (3 evidence pieces)
     ```

2. **Collect All Evidence**
   - Aggregate all evidence from all agents
   - Remove duplicates
   - Total: 7 unique evidence pieces

3. **LLM Synthesis**
   - Sends ALL hypotheses + ALL evidence to GPT-4o
   - Prompt:
     ```
     "You are analyzing an RCA investigation. 5 parallel hypotheses were tested:

     H1: Network relationship inactive (0.85 confidence)
       Evidence:
       - company_api: "Relationship INACTIVE since Dec 2025"
       - redshift: "12 similar loads affected with same carrier"

     H2: JT scraping error (0.10 confidence)
       Evidence: None

     H3: Carrier portal down (0.05 confidence)
       Evidence:
       - tracking_api: "Portal is active" (contradicts)

     ...

     Determine the CONSENSUS root cause. Weigh evidence strength and confidence."
     ```

4. **LLM Reasoning** (Internal)
   ```
   "H1 has the highest confidence (0.85) and strongest evidence.
    The company_api directly confirms the relationship is INACTIVE.
    The redshift query shows this affects multiple loads, confirming a pattern.

    H2 was eliminated - no evidence of JT errors.
    H3 was contradicted - portal is active.
    H4 was contradicted - subscription is active.
    H5 has moderate confidence but less evidence than H1.

    CONCLUSION: H1 is the most likely root cause."
   ```

5. **Final Output**
   ```json
   {
     "root_cause": "network_relationship_inactive",
     "confidence": 0.85,
     "explanation": "The shipper-carrier relationship exists but is INACTIVE...",
     "recommended_actions": [
       "Reactivate relationship in Network Admin",
       "Contact shipper to confirm they want tracking for this carrier"
     ],
     "remaining_uncertainties": [
       "Why was the relationship deactivated?"
     ]
   }
   ```

---

## 🎬 Real-World Example

### Input
```
Load ID: 618171104
Initial Status: "Awaiting Tracking Info"
```

### Phase 1: Identifiers
```
{
  "load_id": "618171104",
  "carrier_id": "ABC_CARRIER",
  "shipper_id": "XYZ_SHIPPER",
  "container_number": "CONT123",
  "status": "Awaiting Tracking Info"
}
```

### Phase 2: Hypotheses Formed
```
1. Network relationship missing (0.25)
2. JT scraping failed (0.25)
3. Carrier portal down (0.20)
4. Subscription inactive (0.15)
5. Identifier mismatch (0.15)
```

### Phase 3: Parallel Investigation (30 seconds)

**SubAgent-H1 (Network):**
- Iter 1: Query company_api → "Relationship INACTIVE" → confidence: 0.60
- Iter 2: Query redshift → "12 similar loads" → confidence: 0.85
- Iter 3: Conclude

**SubAgent-H2 (JT):**
- Iter 1: Query justtransform → Client not configured → confidence: 0.25
- Iter 2: Repeat → No data → confidence: 0.10
- Eliminated

**SubAgent-H3 (Carrier):**
- Iter 1: Query tracking_api → "Portal active" → confidence: 0.05
- Eliminated

**SubAgent-H4 (Subscription):**
- Iter 1: Query super_api → "Subscription active" → confidence: 0.05
- Eliminated

**SubAgent-H5 (Identifier):**
- Iter 1: Query tracking_api → "Container not found" → confidence: 0.50
- Iter 2: Revisit tracking_api → "Booking exists" → confidence: 0.40
- Iter 3: Conclude

### Phase 4: Synthesis (5 seconds)

**LLM Input:**
```
Hypotheses:
- H1: 0.85 (Network inactive)
- H2: 0.10 (Eliminated)
- H3: 0.05 (Eliminated)
- H4: 0.05 (Eliminated)
- H5: 0.40 (Identifier mismatch possible)

Evidence (7 pieces):
1. company_api: "Relationship INACTIVE since 2025-12-15"
2. redshift: "12 similar loads affected"
3. tracking_api: "Portal active"
4. super_api: "Subscription active"
5. tracking_api: "Container not found"
6. tracking_api: "Booking exists"
```

**LLM Consensus:**
```json
{
  "root_cause": "network_relationship_inactive",
  "confidence": 0.85,
  "explanation": "H1 has strongest evidence with company_api confirming INACTIVE relationship. Pattern confirmed by redshift showing 12 similar loads. H5 is possible but less likely.",
  "recommended_action": "Reactivate shipper-carrier relationship in Network Admin"
}
```

---

## 🎯 Key Advantages

### vs Linear RCA
| Aspect | Linear (Old) | Hypothesis-Driven (New) |
|--------|-------------|------------------------|
| Path | Fixed steps (1→2→5) | Adaptive based on evidence |
| Parallelism | Sequential | 5 agents run concurrently |
| Decisions | Hardcoded rules | LLM reasoning per iteration |
| Confidence | Binary (yes/no) | Probabilistic (0.0-1.0) |
| Revisiting | Not possible | Can revisit APIs with new params |
| Time | ~60s (sequential) | ~30s (parallel) |

### Real Innovation
1. **Adaptive**: LLM decides what to query next based on findings
2. **Parallel**: 5 hypotheses tested simultaneously
3. **Self-correcting**: Can adjust strategy mid-investigation
4. **Evidence-based**: Confidence updates with each finding
5. **Consensus**: Final determination weighs all evidence

---

## 📊 Streaming Architecture

### SSE Events Flow
```
Frontend                  Backend                    Sub-Agents
   │                         │                            │
   │──POST /investigate─────>│                            │
   │                         │──Form hypotheses──────────>│
   │<───event: hypothesis────│                            │
   │<───event: hypothesis────│                            │
   │                         │──Spawn agents─────────────>│
   │<───event: agent_action──│<───Query company_api───────│
   │<───event: evidence──────│<───Return evidence─────────│
   │<───event: confidence────│<───Updated to 0.85─────────│
   │                         │                            │
   │<───event: result────────│<───Synthesis complete──────│
   │<───event: complete──────│                            │
```

---

## 🎨 UI Visualization

The React Next.js frontend visualizes:
1. **Progress Stepper**: 4 phases with real-time updates
2. **Hypothesis Cards**: Live confidence bars (0-100%)
3. **Sub-Agent Actions**: What each agent is doing
4. **Evidence Timeline**: As it's collected
5. **Final Consensus**: Beautiful result card with metrics

---

## 🔧 Technical Stack

### Backend
- **FastAPI**: SSE streaming endpoint
- **Azure GPT-4o**: Hypothesis formation, action decisions, synthesis
- **AsyncIO**: Parallel sub-agent execution
- **Python 3.11**: Core engine

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: FourKites branding
- **Lucide Icons**: Modern icon set
- **SSE Client**: Real-time streaming

---

## 📝 Summary

**Consensus = LLM-powered evidence synthesis**

Instead of hardcoded rules, the system:
1. Forms multiple theories (hypotheses)
2. Tests them in parallel with autonomous agents
3. Collects evidence and updates confidence
4. Uses LLM to synthesize all findings into a final determination

This mimics how experienced support engineers think - testing multiple theories simultaneously and reaching a conclusion based on all available evidence.
