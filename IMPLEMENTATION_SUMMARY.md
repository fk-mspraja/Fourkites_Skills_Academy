# Ops-Focused UI Improvements - Implementation Summary

## Overview

This document summarizes the enhanced UI components created for the Rewind RCA agent platform, specifically designed to make the system transparent and powerful for Operations and Support teams.

## ✅ What Has Been Created

### 1. **Multi-Agent Collaboration View** 🧠📊🤝🔍

**Files Created:**
- `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/AgentCollaborationView.jsx`
- `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/AgentCollaborationView.css`

**Features:**
- Visual "swim lane" display showing 4 specialized agents working in parallel:
  - **Hypothesis Agent**: Generates potential root causes with confidence scores
  - **Data Fetcher Agents**: Shows parallel queries across multiple data sources (Redshift, SigNoz, Athena, etc.)
  - **Consensus Agent**: Displays evidence collection and hypothesis evaluation
  - **Pattern Matcher**: Shows historical pattern matching and similar cases
- Real-time status updates via SSE (Server-Sent Events)
- Expandable/collapsible lanes with detailed progress
- Color-coded status badges (active=blue, complete=green, waiting=yellow, error=red)
- Query progress indicators with SQL preview
- Evidence matrix showing what supports/refutes each hypothesis

**How It Works:**
```jsx
import AgentCollaborationView from './components/AgentCollaborationView';

<AgentCollaborationView
  investigationId="INV-2026-001"
  onAgentClick={(agentType, agentData) => {
    // Handle agent detail view
  }}
/>
```

The component listens to SSE events:
- `agent_update`: Updates agent status and progress
- `reasoning_step`: Adds reasoning steps to history
- `consensus_update`: Updates consensus building progress

---

### 2. **AI-Powered Query Builder** ✨

**Files Created:**
- `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/AIQueryBuilder.jsx`
- `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/AIQueryBuilder.css`
- `/Users/msp.raja/rca-agent-project/rewind-app/backend/services/ai_query_generator.py`
- `/Users/msp.raja/rca-agent-project/rewind-app/backend/routes/ai_routes.py`

**Features:**
- Natural language to SQL/ClickHouse query conversion using Claude API
- Automatic data source selection (SigNoz, Redshift, Athena, Rewind ClickHouse)
- Query explanation in plain English
- Warnings about potential performance issues
- Example queries for common use cases
- One-click query execution
- Save queries as templates
- Copy, edit, and share generated queries

**How It Works:**

**Frontend:**
```jsx
import AIQueryBuilder from './components/AIQueryBuilder';

<AIQueryBuilder
  onExecuteQuery={(queryData) => {
    // Execute the generated query
    console.log(queryData.query, queryData.dataSource);
  }}
  onSaveTemplate={(template) => {
    // Save query as template
  }}
/>
```

**Backend API:**
```bash
POST /api/v1/ai/generate-query
Content-Type: application/json

{
  "natural_language": "Show me all ocean events for load ABC123 in the last 3 days",
  "context": {
    "available_sources": ["signoz", "redshift", "athena"],
    "preferred_source": "auto",
    "user_role": "ops"
  }
}
```

**Response:**
```json
{
  "query": "SELECT toDateTime64(timestamp / 1000000000, 3) as ts, body FROM signoz_logs.distributed_logs WHERE service_name = 'ocean' AND hasToken(body, 'ABC123') AND timestamp >= toUnixTimestamp64Nano(now() - INTERVAL 3 DAY) ORDER BY timestamp DESC LIMIT 200",
  "data_source": "signoz",
  "explanation": [
    "Using hasToken for 'ABC123' (word-level indexed search)",
    "Filtering last 3 days for performance",
    "Limited to 200 rows to prevent overwhelming results"
  ],
  "potential_issues": [
    "hasToken doesn't work with underscores - use LIKE if needed",
    "30-day retention limit on SigNoz"
  ],
  "estimated_rows": 150
}
```

---

### 3. **Comprehensive Documentation**

**Files Created:**
- `/Users/msp.raja/rca-agent-project/OPS_UI_IMPROVEMENTS.md` - Complete design specification with:
  - UI mockups (ASCII art)
  - Component architecture
  - Agent reasoning panel design
  - Query template library design
  - Investigation timeline design
  - Log context viewer design
  - Implementation roadmap
  - Success metrics

---

## 🔧 Integration Guide

### Step 1: Backend Setup

**1. Install Dependencies:**
```bash
cd /Users/msp.raja/rca-agent-project/rewind-app/backend
pip install anthropic
```

**2. Set Environment Variable:**
```bash
export ANTHROPIC_API_KEY="your-claude-api-key"
```

**3. Register AI Routes in FastAPI:**

Edit `/Users/msp.raja/rca-agent-project/rewind-app/backend/main.py`:

```python
from routes.ai_routes import router as ai_router

# Add to your FastAPI app
app.include_router(ai_router)
```

**4. Update SSE Event Emission:**

Modify your investigation orchestrator to emit new agent events:

```python
# In your investigation handler
async def run_investigation(investigation_id: str):
    # Emit agent status updates
    await emit_sse_event("agent_update", {
        "agent_type": "hypothesis",
        "status": "active",
        "current_task": "Analyzing error patterns",
        "hypotheses": [
            {
                "name": "Network relationship missing",
                "confidence": 0.95,
                "reasoning": "Company API returned NO_RELATIONSHIP"
            }
        ]
    })

    # Emit reasoning steps
    await emit_sse_event("reasoning_step", {
        "agent_type": "hypothesis",
        "timestamp": "2026-01-19T12:30:47Z",
        "inputs": ["error_message", "retry_count"],
        "decision": "Query company API for relationship",
        "reasoning": "Error indicates connection refused, suggesting network issue"
    })

    # Emit consensus updates
    await emit_sse_event("consensus_update", {
        "hypothesis_id": "H1",
        "confidence_before": 0.85,
        "confidence_after": 0.98,
        "evidence_added": "Company API returned NO_RELATIONSHIP",
        "impact": "HIGH"
    })
```

---

### Step 2: Frontend Integration

**1. Import Components:**

Edit `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/App.jsx`:

```jsx
import AgentCollaborationView from './components/AgentCollaborationView';
import AIQueryBuilder from './components/AIQueryBuilder';

function App() {
  const [investigationId, setInvestigationId] = useState(null);
  const [viewMode, setViewMode] = useState('timeline'); // 'timeline', 'auto-rca', 'log-search', 'agent-collab'

  return (
    <div className="App">
      {/* View Mode Selector */}
      <div className="view-mode-selector">
        <button onClick={() => setViewMode('timeline')}>Timeline</button>
        <button onClick={() => setViewMode('auto-rca')}>Auto RCA</button>
        <button onClick={() => setViewMode('log-search')}>Log Search</button>
        <button onClick={() => setViewMode('agent-collab')}>Agent Collaboration</button>
      </div>

      {/* Agent Collaboration View */}
      {viewMode === 'agent-collab' && (
        <AgentCollaborationView
          investigationId={investigationId}
          onAgentClick={(agentType, data) => {
            console.log(`Clicked ${agentType}:`, data);
            // Show detailed agent reasoning panel
          }}
        />
      )}

      {/* AI Query Builder in Log Search View */}
      {viewMode === 'log-search' && (
        <div>
          <AIQueryBuilder
            onExecuteQuery={(queryData) => {
              // Execute query against selected data source
              executeQuery(queryData.query, queryData.dataSource);
            }}
            onSaveTemplate={(template) => {
              // Save to template library
              saveTemplate(template);
            }}
          />
        </div>
      )}
    </div>
  );
}
```

**2. Add to Auto RCA View:**

You can also embed the Agent Collaboration View in the existing Auto RCA view:

```jsx
// In AutoRCAView.jsx
import AgentCollaborationView from './AgentCollaborationView';

<div className="auto-rca-view">
  {/* Existing investigation form */}

  {investigationStarted && (
    <>
      {/* Show agent collaboration view above results */}
      <AgentCollaborationView investigationId={investigationId} />

      {/* Existing investigation plan and results */}
      <div className="investigation-results">
        {/* ... existing code ... */}
      </div>
    </>
  )}
</div>
```

---

## 📊 Key Features Explained

### Multi-Agent Transparency

**Before:**
```
Investigation started...
Querying data sources...
Analysis complete.

Root Cause: Network relationship missing
Confidence: 98%
```

**After (with Agent Collaboration View):**
```
┌─ Hypothesis Agent ────────────────────────────────┐
│ 🧠 ACTIVE                                         │
│ Generated 3 hypotheses:                           │
│ • H1: Network relationship missing (95%)          │
│ • H2: Webhook endpoint unreachable (72%)          │
│ • H3: Authentication failure (45%)                │
└───────────────────────────────────────────────────┘

┌─ Data Fetcher Agents ─────────────────────────────┐
│ 📊 3/4 COMPLETE                                   │
│ ├─ Redshift Query ✅ (1.2s) - No relationship found│
│ ├─ Tracking API ✅ (245ms) - Load metadata found  │
│ ├─ Callbacks Query 🔄 89% - Scanning 450 rows    │
│ └─ SigNoz Logs ⏳ Queued                          │
└───────────────────────────────────────────────────┘

┌─ Consensus Agent ─────────────────────────────────┐
│ 🤝 WAITING FOR: Callbacks query                   │
│ Evidence collected:                               │
│ • Network relationship: MISSING ✅                │
│ • Load metadata: FOUND ✅                         │
│ • Callback history: IN_PROGRESS 🔄               │
└───────────────────────────────────────────────────┘
```

**Benefits:**
- Ops can see **why** the AI thinks what it thinks
- Can identify **which data sources** contributed to conclusion
- Can **interrupt** if they see the investigation going wrong
- **Trust** is built through transparency

---

### Natural Language Querying

**Before (Manual Log Search):**
Ops team member needs to:
1. Know ClickHouse syntax
2. Remember table names and column names
3. Understand timestamp conversion (`toDateTime64(timestamp / 1000000000, 3)`)
4. Know when to use `hasToken()` vs `LIKE`
5. Remember to add LIMIT clauses

**After (AI Query Builder):**
```
Input: "Show me ocean events with retries in the last 3 days"

Output:
✨ Generated Query:
SELECT toDateTime64(timestamp / 1000000000, 3) as ts, body
FROM signoz_logs.distributed_logs
WHERE service_name = 'ocean'
  AND body LIKE '%retry%'
  AND timestamp >= toUnixTimestamp64Nano(now() - INTERVAL 3 DAY)
ORDER BY timestamp DESC
LIMIT 200

🧠 Explanation:
• Using SigNoz for recent logs (30-day retention)
• Filtering service 'ocean' for ocean-specific events
• Using LIKE for 'retry' (substring match)
• Limited to 200 rows for performance

⚠️ Potential Issues:
• Consider using hasToken if 'retry' is a complete word
• 3-day range should be fast, but narrow if needed
```

**Benefits:**
- **Lower barrier to entry** - new team members can query immediately
- **Faster investigations** - no syntax lookup required
- **Educational** - explanations teach proper query patterns
- **Error prevention** - warnings about common pitfalls

---

## 🚀 Next Steps

### Immediate (Required for Production)

1. **Add Authentication to AI Endpoints:**
   ```python
   from fastapi import Depends
   from auth import get_current_user

   @router.post("/generate-query")
   async def generate_query(request: QueryGenerationRequest, user=Depends(get_current_user)):
       # Only authenticated users can use AI features
   ```

2. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @router.post("/generate-query")
   @limiter.limit("10/minute")  # Max 10 queries per minute
   async def generate_query(...):
   ```

3. **Cost Monitoring:**
   - Track Claude API usage per user
   - Set spending limits
   - Log all AI queries for audit

4. **Error Handling:**
   - Add retry logic for Claude API failures
   - Graceful degradation if AI is unavailable
   - Fallback to manual query builder

---

### Phase 2 Features (From OPS_UI_IMPROVEMENTS.md)

1. **Query Template Library:**
   - Database schema for storing templates
   - CRUD API endpoints
   - Template sharing between team members
   - Usage analytics

2. **Agent Reasoning Panel:**
   - Detailed view of agent "thinking"
   - Decision tree visualization
   - Hypothesis evaluation matrix
   - Alternative hypotheses considered

3. **Investigation Timeline:**
   - Visual timeline of all agent events
   - Click to expand event details
   - Export timeline as PDF/JSON
   - Replay investigation feature

4. **Log Context Viewer:**
   - One-click "show surrounding logs"
   - ±N logs before/after selected entry
   - Pattern extraction from logs
   - Jump to related logs by correlation ID

---

## 📈 Success Metrics

Track these KPIs to measure impact:

### Quantitative
- **Investigation Time**: Target <3 min (down from 30-45 min)
- **Query Success Rate**: 85%+ find answer on first query
- **AI Query Usage**: 60%+ of queries use AI builder after 30 days
- **Agent View Engagement**: 70%+ expand reasoning panel
- **Template Adoption**: 50%+ use templates within 30 days

### Qualitative
- **User Feedback**: NPS score >40
- **Confidence**: Survey "I trust the AI conclusions" >80% agree
- **Knowledge Sharing**: Templates created and shared between team members
- **Onboarding**: New ops members productive within 1 week (vs 2-3 weeks)

---

## 🔐 Security Considerations

### AI Query Generation

**Risks:**
- SQL injection via natural language input
- Unauthorized data access
- Expensive queries causing DoS

**Mitigations:**
1. **Input Validation:**
   ```python
   # Block malicious patterns
   BLOCKED_PATTERNS = [
       r'DROP\s+TABLE',
       r'DELETE\s+FROM',
       r'TRUNCATE',
       r'ALTER\s+TABLE',
       # ... more destructive operations
   ]

   for pattern in BLOCKED_PATTERNS:
       if re.search(pattern, generated_query, re.IGNORECASE):
           raise SecurityException("Query contains blocked operations")
   ```

2. **Read-Only Database User:**
   ```python
   # All query execution uses read-only credentials
   REDSHIFT_USER = 'rewind_readonly'  # GRANT SELECT only
   ```

3. **Query Timeout:**
   ```python
   # Prevent long-running queries
   QUERY_TIMEOUT = 30  # seconds
   ```

4. **Audit Logging:**
   ```python
   # Log all AI-generated queries
   await log_ai_query(
       user_id=user.id,
       natural_language=request.natural_language,
       generated_query=result.query,
       data_source=result.data_source,
       executed_at=datetime.now()
   )
   ```

---

## 🧪 Testing

### Unit Tests

**Backend:**
```python
# tests/test_ai_query_generator.py
import pytest
from services.ai_query_generator import AIQueryGenerator

@pytest.mark.asyncio
async def test_generate_simple_query():
    generator = AIQueryGenerator()
    result = await generator.generate(
        nl_input="Show me ocean events for load ABC123",
        context={"available_sources": ["signoz"]}
    )

    assert "SELECT" in result.query
    assert "distributed_logs" in result.query
    assert result.data_source == "signoz"
    assert len(result.explanation_points) > 0
```

**Frontend:**
```javascript
// components/__tests__/AIQueryBuilder.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import AIQueryBuilder from '../AIQueryBuilder';

test('generates query on button click', async () => {
  const mockExecute = jest.fn();
  render(<AIQueryBuilder onExecuteQuery={mockExecute} />);

  const input = screen.getByPlaceholderText(/describe what you want/i);
  fireEvent.change(input, { target: { value: 'Show me ocean events' } });

  const generateBtn = screen.getByText(/generate query/i);
  fireEvent.click(generateBtn);

  // Wait for query to generate
  await screen.findByText(/AI Generated Query/i);

  expect(screen.getByText(/SELECT/i)).toBeInTheDocument();
});
```

### Integration Tests

```python
# tests/test_ai_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_generate_query_endpoint():
    response = client.post("/api/v1/ai/generate-query", json={
        "natural_language": "Show me failed callbacks",
        "context": {"available_sources": ["athena"]}
    })

    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "data_source" in data
    assert "explanation" in data
```

---

## 📚 Additional Resources

- **Full Design Spec**: See `/Users/msp.raja/rca-agent-project/OPS_UI_IMPROVEMENTS.md`
- **Component Source**: `/Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/`
- **Backend Services**: `/Users/msp.raja/rca-agent-project/rewind-app/backend/services/`
- **API Routes**: `/Users/msp.raja/rca-agent-project/rewind-app/backend/routes/`

---

## 🎉 Summary

You now have:

✅ **Multi-Agent Collaboration View** - See what agents are thinking in real-time
✅ **AI Query Builder** - Convert natural language to SQL/ClickHouse queries
✅ **Backend AI Service** - Claude-powered query generation with explanations
✅ **API Endpoints** - RESTful endpoints for AI features
✅ **Comprehensive Documentation** - Design specs, integration guide, and roadmap

**Next:** Integrate these components into your Auto RCA and Log Search views, add query templates, and implement the investigation timeline for complete transparency!
