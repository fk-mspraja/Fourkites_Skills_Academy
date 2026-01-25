# Ops-Focused UI Improvements for Rewind RCA Agent
## Executive Summary

This document outlines comprehensive UI enhancements to make the Rewind RCA agent transparent, powerful, and intuitive for Operations and Support teams. The improvements focus on **visibility into agent reasoning**, **enhanced log querying capabilities**, and **AI-assisted troubleshooting**.

**Key Improvements:**
1. **Multi-Agent Collaboration View** - See subagents working in parallel on hypotheses
2. **Agent Reasoning Panel** - Transparent decision-making and consensus building
3. **AI-Powered Query Builder** - Natural language to SQL/ClickHouse queries
4. **Query Templates & Saved Queries** - Reusable investigation patterns
5. **Real-Time Investigation Timeline** - Visual agent communication flow
6. **Log Context Viewer** - See surrounding logs with one click

---

## 1. Multi-Agent Collaboration View

### Problem
Currently, the Auto RCA view shows investigation steps sequentially, but hides the parallel work happening between multiple specialized agents (Hypothesis Agent, Data Fetcher, Consensus Agent, Pattern Matcher).

### Solution: Agent Swim Lane View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Investigation: Load #ABC123 - Callback Webhook Failure             │
│  Started: 2026-01-19 12:30:45 | Duration: 45s | Status: In Progress │
└─────────────────────────────────────────────────────────────────────┘

┌─ Hypothesis Agent ────────────────────────────────────────────────┐
│ 🧠 Generating hypotheses...                                  [ACTIVE]│
│ ✅ H1: Network relationship missing (confidence: 0.85)       [12:30:47]│
│ ✅ H2: Webhook endpoint unreachable (confidence: 0.72)       [12:30:48]│
│ ✅ H3: Authentication failure (confidence: 0.45)             [12:30:49]│
│ ⏱️  Waiting for consensus...                                 [12:30:50]│
└────────────────────────────────────────────────────────────────────┘

┌─ Data Fetcher Agents ─────────────────────────────────────────────┐
│ 📊 Parallel queries in progress (3/4 complete)              [ACTIVE]│
│                                                                      │
│ ├─ Redshift Query ✅                                       [12:30:46]│
│ │  SELECT * FROM companies WHERE permalink = 'xyz'                 │
│ │  Result: No active relationship found                            │
│ │  Rows: 0 | Duration: 1.2s                                        │
│ │                                                                   │
│ ├─ Callbacks Query 🔄                                      [12:30:47]│
│ │  SELECT * FROM callbacks_v2 WHERE load_number = 'ABC123'        │
│ │  Scanning: 450 rows | Progress: 89%                              │
│ │                                                                   │
│ ├─ Tracking API Call ✅                                    [12:30:45]│
│ │  GET /api/v1/loads/ABC123                                        │
│ │  Result: Found metadata | Response: 245ms                        │
│ │                                                                   │
│ └─ SigNoz Logs ⏳                                          [Queued] │
│    Query will start after callbacks complete                        │
└────────────────────────────────────────────────────────────────────┘

┌─ Consensus Agent ─────────────────────────────────────────────────┐
│ 🤝 Building consensus...                                    [PENDING]│
│ Waiting for: Callbacks query, SigNoz logs                          │
│                                                                      │
│ Evidence collected so far:                                          │
│ • Network relationship: MISSING ✅                                  │
│ • Load metadata: FOUND ✅                                           │
│ • Callback history: IN_PROGRESS 🔄                                 │
└────────────────────────────────────────────────────────────────────┘

┌─ Pattern Matcher ─────────────────────────────────────────────────┐
│ 🔍 Analyzing error patterns...                              [IDLE]  │
│ Will activate after consensus is reached                            │
└────────────────────────────────────────────────────────────────────┘
```

### Component Structure

**New Component: `AgentCollaborationView.jsx`**

```jsx
// Location: /Users/msp.raja/rca-agent-project/rewind-app/frontend/src/components/AgentCollaborationView.jsx

import React, { useState, useEffect } from 'react';
import './AgentCollaborationView.css';

export const AgentCollaborationView = ({ investigationId, sseStream }) => {
  const [agents, setAgents] = useState({
    hypothesis: { status: 'idle', hypotheses: [], activeTask: null },
    dataFetchers: { status: 'idle', queries: [], results: {} },
    consensus: { status: 'idle', evidence: [], conclusion: null },
    patternMatcher: { status: 'idle', patterns: [] }
  });

  // Listen to SSE stream for agent updates
  useEffect(() => {
    if (!sseStream) return;

    const handleAgentEvent = (event) => {
      const { agent_type, action, data, timestamp } = event;

      setAgents(prev => ({
        ...prev,
        [agent_type]: {
          ...prev[agent_type],
          ...data,
          lastUpdate: timestamp
        }
      }));
    };

    sseStream.addEventListener('agent_update', handleAgentEvent);
    return () => sseStream.removeEventListener('agent_update', handleAgentEvent);
  }, [sseStream]);

  return (
    <div className="agent-collaboration-view">
      <InvestigationHeader {...investigationMeta} />

      <div className="agent-swim-lanes">
        <AgentLane
          name="Hypothesis Agent"
          icon="🧠"
          agent={agents.hypothesis}
          renderContent={<HypothesisContent {...agents.hypothesis} />}
        />

        <AgentLane
          name="Data Fetcher Agents"
          icon="📊"
          agent={agents.dataFetchers}
          renderContent={<DataFetcherContent {...agents.dataFetchers} />}
        />

        <AgentLane
          name="Consensus Agent"
          icon="🤝"
          agent={agents.consensus}
          renderContent={<ConsensusContent {...agents.consensus} />}
        />

        <AgentLane
          name="Pattern Matcher"
          icon="🔍"
          agent={agents.patternMatcher}
          renderContent={<PatternMatcherContent {...agents.patternMatcher} />}
        />
      </div>
    </div>
  );
};
```

**Key Features:**
- Real-time status updates via SSE
- Expandable/collapsible lanes
- Color-coded by status (active=blue, complete=green, waiting=yellow, error=red)
- Progress indicators for long-running queries
- Click to expand query details (full SQL, explain plan)

---

## 2. Agent Reasoning Panel

### Problem
Users can't see WHY agents made certain decisions or how they arrived at consensus.

### Solution: Transparent Reasoning Display

```
┌─ Agent Reasoning ─────────────────────────────────────────────────┐
│                                                                     │
│ 💭 Hypothesis Agent Thinking (12:30:47)                            │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Analyzing callback failure for load #ABC123...                  ││
│ │                                                                  ││
│ │ Input signals:                                                   ││
│ │ • Error message: "Connection refused to webhook endpoint"       ││
│ │ • HTTP status: null (no response received)                      ││
│ │ • Retry count: 5 (max retries exhausted)                        ││
│ │ • Carrier: XYZ Logistics                                        ││
│ │                                                                  ││
│ │ Decision tree reasoning:                                         ││
│ │ 1. Check network relationship status                            ││
│ │    → Querying company API for XYZ Logistics...                  ││
│ │    → Result: NO_RELATIONSHIP found                              ││
│ │    → Confidence: HIGH (0.95) - definitive database check        ││
│ │                                                                  ││
│ │ 2. Generate hypothesis                                           ││
│ │    → H1: Network relationship missing                           ││
│ │    → Supporting evidence: Company API returned NO_RELATIONSHIP  ││
│ │    → Confidence score: 0.95                                     ││
│ │    → Expected fix: Add carrier relationship in admin panel      ││
│ │                                                                  ││
│ │ Alternative hypotheses considered but rejected:                 ││
│ │ • Webhook endpoint down (0.15) - would show timeout, not refuse ││
│ │ • Auth failure (0.05) - would show 401/403, not connection fail ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ 🤝 Consensus Agent Thinking (12:30:52)                             │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Evaluating 3 hypotheses against collected evidence...           ││
│ │                                                                  ││
│ │ Evidence matrix:                                                 ││
│ │                                                                  ││
│ │ Hypothesis 1: Network relationship missing (0.95)               ││
│ │ ✅ Company API: NO_RELATIONSHIP confirmed                       ││
│ │ ✅ Callbacks: All attempts failed with "connection refused"     ││
│ │ ✅ Load metadata: Carrier = XYZ Logistics                       ││
│ │ ✅ Historical pattern: 47 similar cases in last 30 days         ││
│ │ → Final confidence: 0.98 (VERY HIGH)                            ││
│ │                                                                  ││
│ │ Hypothesis 2: Webhook endpoint unreachable (0.72)               ││
│ │ ❌ Network ping: Endpoint is reachable                          ││
│ │ ❌ SSL cert: Valid and not expired                              ││
│ │ ⚠️  Callbacks: Connection refused (contradicts reachability)    ││
│ │ → Final confidence: 0.12 (LOW) - rejected                       ││
│ │                                                                  ││
│ │ Hypothesis 3: Authentication failure (0.45)                     ││
│ │ ❌ Error pattern: No 401/403 codes found                        ││
│ │ ❌ Connection level failure (before auth)                       ││
│ │ → Final confidence: 0.05 (VERY LOW) - rejected                  ││
│ │                                                                  ││
│ │ 🎯 CONSENSUS REACHED                                             ││
│ │ Root Cause: Network relationship missing                        ││
│ │ Confidence: 98%                                                  ││
│ │ Recommended Action: Create carrier relationship in admin panel  ││
│ └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘

[Show Full Reasoning] [Export Reasoning] [Flag for Review]
```

**New Component: `AgentReasoningPanel.jsx`**

```jsx
export const AgentReasoningPanel = ({ reasoningSteps }) => {
  const [expandedSteps, setExpandedSteps] = useState({});

  return (
    <div className="reasoning-panel">
      {reasoningSteps.map((step, idx) => (
        <div key={idx} className="reasoning-step">
          <div className="reasoning-header" onClick={() => toggleExpand(idx)}>
            <span className="agent-icon">{step.agentIcon}</span>
            <span className="agent-name">{step.agentName} Thinking</span>
            <span className="timestamp">{step.timestamp}</span>
            <span className="expand-icon">{expandedSteps[idx] ? '▼' : '▶'}</span>
          </div>

          {expandedSteps[idx] && (
            <div className="reasoning-content">
              <div className="input-signals">
                <h4>Input signals:</h4>
                <ul>
                  {step.inputs.map(input => <li key={input.key}>• {input.text}</li>)}
                </ul>
              </div>

              <div className="decision-tree">
                <h4>Decision tree reasoning:</h4>
                {step.decisions.map((decision, dIdx) => (
                  <div key={dIdx} className="decision-node">
                    <div className="decision-step">{dIdx + 1}. {decision.action}</div>
                    {decision.substeps.map((sub, sIdx) => (
                      <div key={sIdx} className="decision-substep">
                        → {sub.text}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {step.alternatives && (
                <div className="alternatives-considered">
                  <h4>Alternative hypotheses considered but rejected:</h4>
                  <ul>
                    {step.alternatives.map(alt => (
                      <li key={alt.name}>
                        • {alt.name} ({alt.confidence}) - {alt.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {step.consensus && (
                <div className="consensus-result">
                  <div className="consensus-badge">🎯 CONSENSUS REACHED</div>
                  <div>Root Cause: <strong>{step.consensus.rootCause}</strong></div>
                  <div>Confidence: <strong>{step.consensus.confidence}%</strong></div>
                  <div>Recommended Action: <strong>{step.consensus.action}</strong></div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## 3. AI-Powered Query Builder

### Problem
Ops folks know what they want to find but not always how to write complex ClickHouse/SQL queries. Manual Log Search requires knowledge of schema, operators, and syntax.

### Solution: Natural Language Query Assistant

```
┌─ AI Query Builder ────────────────────────────────────────────────┐
│                                                                     │
│ 💬 Describe what you want to find:                                 │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Show me all ocean events for load ABC123 in the last 3 days    ││
│ │ where the correlation ID contains "retry"                       ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ [Generate Query] [Use Template ▼]                                  │
│                                                                     │
│ ✨ AI Generated Query:                                             │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ SELECT                                                           ││
│ │   toDateTime64(timestamp / 1000000000, 3) as ts,                ││
│ │   body                                                           ││
│ │ FROM signoz_logs.distributed_logs                               ││
│ │ WHERE 1=1                                                        ││
│ │   AND service_name = 'ocean'                                    ││
│ │   AND hasToken(body, 'ABC123')                                  ││
│ │   AND body LIKE '%retry%'                                       ││
│ │   AND timestamp >= toUnixTimestamp64Nano(now() - INTERVAL 3 DAY)││
│ │ ORDER BY timestamp DESC                                          ││
│ │ LIMIT 200                                                        ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ 🧠 AI Explanation:                                                 │
│ • Using hasToken for 'ABC123' (word-level indexed search)          │
│ • Using LIKE for 'retry' (substring match)                         │
│ • Timestamp converted to nanoseconds for ClickHouse                │
│ • Limited to 200 rows for performance                              │
│                                                                     │
│ ⚠️  Potential Issues:                                               │
│ • hasToken doesn't work with underscores - use LIKE if needed      │
│ • 3-day range may return many rows - consider narrowing            │
│                                                                     │
│ [Execute Query] [Edit Query] [Save as Template] [Explain More]     │
└─────────────────────────────────────────────────────────────────────┘
```

**New Component: `AIQueryBuilder.jsx`**

```jsx
import React, { useState } from 'react';
import './AIQueryBuilder.css';

export const AIQueryBuilder = ({ onExecuteQuery }) => {
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [generatedQuery, setGeneratedQuery] = useState(null);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateQuery = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch('/api/v1/ai/generate-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          natural_language: naturalLanguageInput,
          context: {
            available_sources: ['signoz', 'redshift', 'athena'],
            user_role: 'ops'
          }
        })
      });

      const data = await response.json();
      setGeneratedQuery(data.query);
      setAiExplanation(data.explanation);
      setPotentialIssues(data.potential_issues);
    } catch (error) {
      console.error('Failed to generate query:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="ai-query-builder">
      <div className="nl-input-section">
        <label>💬 Describe what you want to find:</label>
        <textarea
          value={naturalLanguageInput}
          onChange={(e) => setNaturalLanguageInput(e.target.value)}
          placeholder="Example: Show me all failed callbacks for shipper ABC Corp in the last week"
          rows={3}
        />
        <div className="builder-actions">
          <button
            onClick={generateQuery}
            disabled={!naturalLanguageInput || isGenerating}
          >
            {isGenerating ? '⏳ Generating...' : '✨ Generate Query'}
          </button>
          <QueryTemplateDropdown onSelectTemplate={loadTemplate} />
        </div>
      </div>

      {generatedQuery && (
        <>
          <div className="generated-query-section">
            <label>✨ AI Generated Query:</label>
            <pre className="sql-preview">{generatedQuery}</pre>
          </div>

          <div className="ai-explanation-section">
            <label>🧠 AI Explanation:</label>
            <ul>
              {aiExplanation.map((point, idx) => (
                <li key={idx}>• {point}</li>
              ))}
            </ul>
          </div>

          {potentialIssues.length > 0 && (
            <div className="potential-issues-section">
              <label>⚠️ Potential Issues:</label>
              <ul>
                {potentialIssues.map((issue, idx) => (
                  <li key={idx}>• {issue}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="query-actions">
            <button onClick={() => onExecuteQuery(generatedQuery)}>
              ▶️ Execute Query
            </button>
            <button onClick={() => openQueryEditor(generatedQuery)}>
              ✏️ Edit Query
            </button>
            <button onClick={() => saveAsTemplate(generatedQuery)}>
              💾 Save as Template
            </button>
            <button onClick={explainMore}>
              ❓ Explain More
            </button>
          </div>
        </>
      )}
    </div>
  );
};
```

**Backend Endpoint: `/api/v1/ai/generate-query`**

```python
# Location: /Users/msp.raja/rca-agent-project/rewind-app/backend/routes/ai_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_query_generator import AIQueryGenerator

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class QueryGenerationRequest(BaseModel):
    natural_language: str
    context: dict = {}

@router.post("/generate-query")
async def generate_query(request: QueryGenerationRequest):
    """
    Converts natural language to SQL/ClickHouse query using Claude API.

    Example input:
    {
        "natural_language": "Show me ocean events with retries in last 3 days",
        "context": {
            "available_sources": ["signoz", "redshift"],
            "user_role": "ops"
        }
    }
    """
    generator = AIQueryGenerator()

    result = await generator.generate(
        nl_input=request.natural_language,
        context=request.context
    )

    return {
        "query": result.sql,
        "explanation": result.explanation_points,
        "potential_issues": result.warnings,
        "data_source": result.recommended_source,
        "estimated_rows": result.estimated_result_size
    }
```

---

## 4. Query Templates & Saved Queries

### Problem
Ops teams run the same queries repeatedly for common issues. No way to save and share investigation patterns.

### Solution: Template Library + Personal Saved Queries

```
┌─ Query Templates ─────────────────────────────────────────────────┐
│                                                                     │
│ 📚 Template Library          🔍 Search: [____________]    [+ New]  │
│                                                                     │
│ ┌─ Common Issues ────────────────────────────────────────────────┐ │
│ │                                                                 │ │
│ │ 🔥 Most Used (Last 7 Days)                                     │ │
│ │ ├─ Callback Failures by Carrier                      [127 uses]│ │
│ │ ├─ Load Creation Errors                               [89 uses]│ │
│ │ ├─ Ocean Events Timeline                              [76 uses]│ │
│ │ └─ Carrier File Processing Flow                       [54 uses]│ │
│ │                                                                 │ │
│ │ 📋 By Category                                                  │ │
│ │ ├─ Network Issues (12 templates)                               │ │
│ │ ├─ Callback Webhooks (8 templates)                             │ │
│ │ ├─ Load Creation (15 templates)                                │ │
│ │ ├─ Carrier Files (6 templates)                                 │ │
│ │ └─ Ocean Events (10 templates)                                 │ │
│ │                                                                 │ │
│ │ 👤 My Saved Queries (5)                                        │ │
│ │ ├─ ABC Corp Recurring Issue                          [Jan 15]  │ │
│ │ ├─ Weekend Callback Spikes                           [Jan 12]  │ │
│ │ └─ XYZ Carrier Timeouts                              [Jan 08]  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Template: Callback Failures by Carrier                             │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Description:                                                    ││
│ │ Find all failed callback attempts for a specific carrier in     ││
│ │ the last N days, grouped by error pattern. Shows retry counts   ││
│ │ and affected load numbers.                                      ││
│ │                                                                  ││
│ │ Parameters:                                                      ││
│ │ • Carrier Name: [_______________] (required)                    ││
│ │ • Days to Search: [7__] (default: 7)                            ││
│ │ • Include Retries: [✓] Yes  [ ] No                             ││
│ │                                                                  ││
│ │ Data Source: AWS Athena (callbacks_v2)                          ││
│ │ Avg Duration: ~12 seconds                                       ││
│ │ Avg Rows Returned: ~150                                         ││
│ │                                                                  ││
│ │ Created by: Platform Team                                       ││
│ │ Last updated: Jan 10, 2026                                      ││
│ │ Used 127 times in last 7 days                                   ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ [Use Template] [Edit] [Clone] [Share] [Delete]                     │
└─────────────────────────────────────────────────────────────────────┘
```

**New Component: `QueryTemplateLibrary.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import './QueryTemplateLibrary.css';

export const QueryTemplateLibrary = ({ onUseTemplate }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch('/api/v1/query-templates')
      .then(res => res.json())
      .then(data => setTemplates(data.templates));
  }, []);

  const filteredTemplates = templates.filter(t => {
    const matchesCategory = selectedCategory === 'all' || t.category === selectedCategory;
    const matchesSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          t.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="query-template-library">
      <div className="library-header">
        <h2>📚 Query Templates</h2>
        <input
          type="text"
          placeholder="🔍 Search templates..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button onClick={createNewTemplate}>+ New Template</button>
      </div>

      <div className="library-sidebar">
        <div className="category-section">
          <h3>🔥 Most Used (Last 7 Days)</h3>
          <ul>
            {templates.slice(0, 4).map(t => (
              <li key={t.id}>
                <TemplateListItem template={t} showUsageCount />
              </li>
            ))}
          </ul>
        </div>

        <div className="category-section">
          <h3>📋 By Category</h3>
          <ul>
            <li onClick={() => setSelectedCategory('network')}>
              Network Issues ({templates.filter(t => t.category === 'network').length})
            </li>
            <li onClick={() => setSelectedCategory('callbacks')}>
              Callback Webhooks ({templates.filter(t => t.category === 'callbacks').length})
            </li>
            {/* More categories */}
          </ul>
        </div>

        <div className="category-section">
          <h3>👤 My Saved Queries</h3>
          <ul>
            {templates.filter(t => t.owner === 'current_user').map(t => (
              <li key={t.id}>
                <TemplateListItem template={t} showDate />
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="library-main">
        {selectedTemplate && (
          <TemplateDetailView
            template={selectedTemplate}
            onUse={onUseTemplate}
          />
        )}
      </div>
    </div>
  );
};

const TemplateDetailView = ({ template, onUse }) => {
  const [params, setParams] = useState(template.default_params || {});

  const handleUseTemplate = () => {
    const filledQuery = fillTemplateParams(template.query, params);
    onUse(filledQuery);
  };

  return (
    <div className="template-detail">
      <h2>{template.name}</h2>
      <p className="template-description">{template.description}</p>

      <div className="template-params">
        <h3>Parameters:</h3>
        {template.parameters.map(param => (
          <div key={param.name} className="param-input">
            <label>{param.label}:</label>
            {param.type === 'text' && (
              <input
                type="text"
                value={params[param.name] || ''}
                onChange={(e) => setParams({...params, [param.name]: e.target.value})}
                placeholder={param.placeholder}
                required={param.required}
              />
            )}
            {param.type === 'number' && (
              <input
                type="number"
                value={params[param.name] || param.default}
                onChange={(e) => setParams({...params, [param.name]: e.target.value})}
              />
            )}
            {param.type === 'checkbox' && (
              <input
                type="checkbox"
                checked={params[param.name] || false}
                onChange={(e) => setParams({...params, [param.name]: e.target.checked})}
              />
            )}
          </div>
        ))}
      </div>

      <div className="template-metadata">
        <div>Data Source: <strong>{template.data_source}</strong></div>
        <div>Avg Duration: <strong>{template.avg_duration}</strong></div>
        <div>Avg Rows: <strong>{template.avg_rows}</strong></div>
        <div>Created by: <strong>{template.created_by}</strong></div>
        <div>Used {template.usage_count} times in last 7 days</div>
      </div>

      <div className="template-actions">
        <button className="primary" onClick={handleUseTemplate}>Use Template</button>
        <button onClick={() => editTemplate(template)}>Edit</button>
        <button onClick={() => cloneTemplate(template)}>Clone</button>
        <button onClick={() => shareTemplate(template)}>Share</button>
      </div>
    </div>
  );
};
```

---

## 5. Real-Time Investigation Timeline

### Problem
Hard to understand the sequence of events and agent interactions over time.

### Solution: Interactive Timeline with Agent Communication

```
Timeline View: Investigation #INV-2026-001
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│ 12:30:45 ──┬─ 🔍 Investigation Started                              │
│            │   Load: ABC123 | Issue: Callback Failure                │
│            │                                                          │
│ 12:30:46 ──┼─ 🧠 Hypothesis Agent: Generating hypotheses             │
│            │   ├─ Analyzing error patterns...                        │
│            │   └─ Generated 3 hypotheses                             │
│            │                                                          │
│            ├─ 📊 Data Fetcher: Started 4 parallel queries            │
│            │                                                          │
│ 12:30:47 ──┼─ ✅ Tracking API: Completed (245ms)                     │
│            │   └─ Found load metadata                                │
│            │                                                          │
│ 12:30:48 ──┼─ ✅ Redshift: Completed (1.2s)                          │
│            │   └─ No active relationship found ⚠️                    │
│            │                                                          │
│            ├─ 🤝 Consensus Agent: Received network data              │
│            │   └─ Evidence: NO_RELATIONSHIP confirmed                │
│            │                                                          │
│ 12:30:50 ──┼─ ✅ Callbacks Query: Completed (3.8s)                   │
│            │   └─ Found 5 failed attempts                            │
│            │                                                          │
│ 12:30:52 ──┼─ 🤝 Consensus Agent: Building consensus                 │
│            │   ├─ Evaluating H1: Network relationship missing (0.95) │
│            │   ├─ Evaluating H2: Endpoint unreachable (0.72)         │
│            │   └─ Evaluating H3: Auth failure (0.45)                 │
│            │                                                          │
│ 12:30:54 ──┼─ 🎯 Consensus Agent: CONSENSUS REACHED                  │
│            │   └─ Root Cause: Network relationship missing (98%)     │
│            │                                                          │
│            ├─ 🔍 Pattern Matcher: Analyzing historical patterns      │
│            │                                                          │
│ 12:30:56 ──┼─ ✅ Pattern Matcher: Found 47 similar cases             │
│            │   └─ Common pattern: NO_RELATIONSHIP → callback fail    │
│            │                                                          │
│ 12:30:58 ──┴─ ✅ Investigation Complete                              │
│                Final Report Generated                                │
│                                                                       │
│ [Show Agent Communication] [Export Timeline] [Replay Investigation]  │
└─────────────────────────────────────────────────────────────────────┘
```

**New Component: `InvestigationTimeline.jsx`**

```jsx
import React, { useState, useEffect, useRef } from 'react';
import './InvestigationTimeline.css';

export const InvestigationTimeline = ({ investigationId, events }) => {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const timelineEndRef = useRef(null);

  useEffect(() => {
    if (autoScroll && timelineEndRef.current) {
      timelineEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, autoScroll]);

  const getEventIcon = (event) => {
    const icons = {
      'investigation_start': '🔍',
      'hypothesis_generated': '🧠',
      'data_fetch_start': '📊',
      'data_fetch_complete': '✅',
      'consensus_building': '🤝',
      'consensus_reached': '🎯',
      'pattern_match': '🔍',
      'investigation_complete': '✅',
      'error': '❌'
    };
    return icons[event.type] || '•';
  };

  const getEventColor = (event) => {
    if (event.type.includes('complete') || event.type.includes('reached')) return 'green';
    if (event.type.includes('error')) return 'red';
    if (event.type.includes('start') || event.type.includes('building')) return 'blue';
    return 'gray';
  };

  return (
    <div className="investigation-timeline">
      <div className="timeline-header">
        <h2>Timeline View: Investigation #{investigationId}</h2>
        <div className="timeline-controls">
          <label>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
          <button onClick={exportTimeline}>Export Timeline</button>
          <button onClick={replayInvestigation}>Replay Investigation</button>
        </div>
      </div>

      <div className="timeline-container">
        <div className="timeline-line"></div>
        <div className="timeline-events">
          {events.map((event, idx) => (
            <div
              key={idx}
              className={`timeline-event ${getEventColor(event)}`}
              onClick={() => setSelectedEvent(event)}
            >
              <div className="event-time">{formatTime(event.timestamp)}</div>
              <div className="event-marker">
                <span className="event-icon">{getEventIcon(event)}</span>
              </div>
              <div className="event-content">
                <div className="event-title">{event.title}</div>
                {event.details && (
                  <ul className="event-details">
                    {event.details.map((detail, dIdx) => (
                      <li key={dIdx}>{detail}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
          <div ref={timelineEndRef} />
        </div>
      </div>

      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
};
```

---

## 6. Log Context Viewer

### Problem
When viewing a specific log entry, ops teams often need to see surrounding logs for context. Currently requires manual queries.

### Solution: One-Click Context Expansion

```
┌─ Log Search Results ──────────────────────────────────────────────┐
│                                                                     │
│ Found 15 results for: hasToken(body, 'ABC123')                     │
│                                                                     │
│ ┌─ Result #3 ────────────────────────────────────────────────────┐ │
│ │ 2026-01-19 12:35:42.156                                         │ │
│ │ Service: ocean | Level: ERROR                                   │ │
│ │ Correlation ID: abc-123-def-456                                 │ │
│ │                                                                  │ │
│ │ {                                                                │ │
│ │   "message": "Failed to process MMCUW event",                   │ │
│ │   "load_number": "ABC123",                                      │ │
│ │   "error": "Connection refused",                                │ │
│ │   "retry_count": 3                                              │ │
│ │ }                                                                │ │
│ │                                                                  │ │
│ │ [📋 Copy] [🔗 Share] [⭐ Bookmark] [🔍 Show Context]            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ▼ Showing 5 logs before and after (click to collapse)              │
│                                                                     │
│ ┌─ Context: 5 logs before ──────────────────────────────────────┐  │
│ │ 12:35:40.123  INFO   Processing load ABC123                    │ │
│ │ 12:35:41.045  DEBUG  Fetching carrier configuration            │ │
│ │ 12:35:41.234  INFO   Carrier: XYZ Logistics                    │ │
│ │ 12:35:41.890  WARN   Retry attempt 1/5                         │ │
│ │ 12:35:42.012  WARN   Retry attempt 2/5                         │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ SELECTED LOG ────────────────────────────────────────────────┐  │
│ │ 12:35:42.156  ERROR  Failed to process MMCUW event             │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Context: 5 logs after ───────────────────────────────────────┐  │
│ │ 12:35:42.234  ERROR  Max retries exhausted                     │ │
│ │ 12:35:42.345  INFO   Marking load as failed                    │ │
│ │ 12:35:42.456  INFO   Sending alert to ops team                 │ │
│ │ 12:35:42.567  DEBUG  Alert sent successfully                   │ │
│ │ 12:35:42.678  INFO   Processing complete                       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [Expand More] (Show ±10 logs) | [Query This Pattern]               │
└─────────────────────────────────────────────────────────────────────┘
```

**New Component: `LogContextViewer.jsx`**

```jsx
import React, { useState } from 'react';
import './LogContextViewer.css';

export const LogContextViewer = ({ logEntry, onQueryPattern }) => {
  const [contextBefore, setContextBefore] = useState([]);
  const [contextAfter, setContextAfter] = useState([]);
  const [showingContext, setShowingContext] = useState(false);
  const [contextRange, setContextRange] = useState(5);

  const fetchContext = async () => {
    const response = await fetch('/api/v1/logs/context', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        timestamp: logEntry.timestamp,
        service_name: logEntry.service_name,
        range_before: contextRange,
        range_after: contextRange
      })
    });

    const data = await response.json();
    setContextBefore(data.before);
    setContextAfter(data.after);
    setShowingContext(true);
  };

  const expandContext = async (newRange) => {
    setContextRange(newRange);
    await fetchContext();
  };

  return (
    <div className="log-context-viewer">
      <div className="selected-log">
        <div className="log-header">
          <span className="log-timestamp">{formatTimestamp(logEntry.timestamp)}</span>
          <span className="log-service">Service: {logEntry.service_name}</span>
          <span className={`log-level level-${logEntry.level}`}>{logEntry.level}</span>
          {logEntry.correlation_id && (
            <span className="log-correlation">Correlation ID: {logEntry.correlation_id}</span>
          )}
        </div>

        <pre className="log-body">{JSON.stringify(JSON.parse(logEntry.body), null, 2)}</pre>

        <div className="log-actions">
          <button onClick={() => copyToClipboard(logEntry)}>📋 Copy</button>
          <button onClick={() => shareLog(logEntry)}>🔗 Share</button>
          <button onClick={() => bookmarkLog(logEntry)}>⭐ Bookmark</button>
          <button onClick={fetchContext}>🔍 Show Context</button>
        </div>
      </div>

      {showingContext && (
        <>
          <div className="context-section context-before">
            <h4>▼ Context: {contextRange} logs before</h4>
            <div className="context-logs">
              {contextBefore.map((log, idx) => (
                <LogEntryCompact key={idx} log={log} />
              ))}
            </div>
          </div>

          <div className="selected-log-highlight">
            <h4>┌─ SELECTED LOG ────────────────────┐</h4>
            <LogEntryCompact log={logEntry} highlight />
          </div>

          <div className="context-section context-after">
            <h4>▼ Context: {contextRange} logs after</h4>
            <div className="context-logs">
              {contextAfter.map((log, idx) => (
                <LogEntryCompact key={idx} log={log} />
              ))}
            </div>
          </div>

          <div className="context-actions">
            <button onClick={() => expandContext(10)}>
              Expand More (Show ±10 logs)
            </button>
            <button onClick={() => expandContext(20)}>
              Show ±20 logs
            </button>
            <button onClick={() => onQueryPattern(extractPattern(logEntry))}>
              Query This Pattern
            </button>
          </div>
        </>
      )}
    </div>
  );
};

const LogEntryCompact = ({ log, highlight }) => (
  <div className={`log-entry-compact ${highlight ? 'highlight' : ''}`}>
    <span className="compact-time">{formatTime(log.timestamp)}</span>
    <span className={`compact-level level-${log.level}`}>{log.level}</span>
    <span className="compact-message">{extractMessage(log.body)}</span>
  </div>
);
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure for agent transparency

1. **Backend SSE Events for Agent Updates**
   - Add new SSE event types: `agent_update`, `reasoning_step`, `consensus_update`
   - Modify investigation orchestrator to emit agent state changes
   - Create reasoning step logger

2. **Agent State Models**
   ```python
   # models/agent_state.py
   class AgentState(BaseModel):
       agent_type: str  # 'hypothesis', 'data_fetcher', 'consensus', 'pattern_matcher'
       status: str      # 'idle', 'active', 'waiting', 'complete', 'error'
       current_task: Optional[str]
       progress: float  # 0.0 to 1.0
       last_update: datetime

   class ReasoningStep(BaseModel):
       agent_name: str
       timestamp: datetime
       inputs: List[str]
       decisions: List[DecisionNode]
       alternatives: List[Alternative]
       conclusion: Optional[str]
   ```

3. **Base UI Components**
   - `AgentCollaborationView.jsx` (basic structure)
   - `AgentReasoningPanel.jsx` (collapsible steps)
   - Shared CSS for agent status colors

**Deliverables:**
- ✅ Backend emitting agent state via SSE
- ✅ Frontend displaying agent swim lanes
- ✅ Basic reasoning step display

---

### Phase 2: AI Query Builder (Week 3-4)
**Goal:** Natural language to SQL/ClickHouse queries

1. **AI Query Generation Service**
   ```python
   # services/ai_query_generator.py
   class AIQueryGenerator:
       async def generate(self, nl_input: str, context: dict) -> QueryResult:
           # Use Claude API to convert NL to SQL
           # Validate generated query
           # Provide explanations and warnings
   ```

2. **Query Template System**
   - Database schema for templates
   - CRUD API endpoints
   - Template parameter substitution

3. **Frontend Components**
   - `AIQueryBuilder.jsx`
   - `QueryTemplateLibrary.jsx`
   - Template parameter forms

**Deliverables:**
- ✅ Natural language query generation working
- ✅ Template library with 10+ common queries
- ✅ Save/share functionality

---

### Phase 3: Timeline & Context (Week 5-6)
**Goal:** Better visualization of investigation flow

1. **Investigation Timeline**
   - Store all events in investigation
   - Timeline rendering component
   - Event detail modals

2. **Log Context API**
   ```python
   @router.post("/api/v1/logs/context")
   async def get_log_context(request: LogContextRequest):
       # Query ±N logs around target timestamp
       # Maintain same service/correlation_id
       # Return before/after arrays
   ```

3. **Frontend Components**
   - `InvestigationTimeline.jsx`
   - `LogContextViewer.jsx`
   - Auto-scroll and replay features

**Deliverables:**
- ✅ Full investigation timeline
- ✅ One-click log context viewing
- ✅ Timeline export/replay

---

### Phase 4: Polish & Ops Feedback (Week 7-8)
**Goal:** Refine based on real ops usage

1. **Performance Optimization**
   - Lazy load timeline events
   - Virtual scrolling for large result sets
   - Query caching

2. **User Feedback Integration**
   - A/B test with ops team
   - Collect pain points
   - Iterate on UX

3. **Documentation**
   - User guide for ops team
   - Video tutorials
   - Query template cookbook

**Deliverables:**
- ✅ Production-ready UI
- ✅ Ops team trained
- ✅ Full documentation

---

## 8. Backend API Changes Required

### New Endpoints

```python
# routes/ai_routes.py
POST /api/v1/ai/generate-query          # NL to SQL conversion
POST /api/v1/ai/explain-query           # Explain existing query
POST /api/v1/ai/optimize-query          # Suggest optimizations

# routes/template_routes.py
GET    /api/v1/query-templates          # List all templates
POST   /api/v1/query-templates          # Create template
GET    /api/v1/query-templates/:id      # Get template details
PUT    /api/v1/query-templates/:id      # Update template
DELETE /api/v1/query-templates/:id      # Delete template
POST   /api/v1/query-templates/:id/use  # Execute with params

# routes/log_routes.py
POST /api/v1/logs/context               # Get surrounding logs
POST /api/v1/logs/pattern               # Find similar patterns

# routes/investigation_routes.py
GET  /api/v1/investigations/:id/timeline    # Full timeline
GET  /api/v1/investigations/:id/reasoning   # All reasoning steps
POST /api/v1/investigations/:id/replay      # Replay investigation
```

### Modified SSE Events

```python
# Existing events remain:
# - event: log
# - event: data
# - event: error
# - event: complete

# New agent-specific events:
event: agent_update
data: {
  "agent_type": "hypothesis",
  "status": "active",
  "current_task": "Analyzing error patterns",
  "progress": 0.45
}

event: reasoning_step
data: {
  "agent_name": "Hypothesis Agent",
  "timestamp": "2026-01-19T12:30:47Z",
  "step_type": "decision",
  "inputs": ["error_message", "retry_count"],
  "decision": "Query company API for relationship",
  "reasoning": "Error indicates connection refused, suggesting network issue"
}

event: consensus_update
data: {
  "hypothesis_id": "H1",
  "confidence_before": 0.85,
  "confidence_after": 0.98,
  "evidence_added": "Company API returned NO_RELATIONSHIP",
  "impact": "HIGH"
}

event: query_start
data: {
  "query_id": "Q123",
  "data_source": "redshift",
  "query": "SELECT * FROM companies...",
  "estimated_duration": "1.5s"
}

event: query_complete
data: {
  "query_id": "Q123",
  "duration": "1.2s",
  "rows_returned": 0,
  "result_summary": "No active relationship found"
}
```

---

## 9. Database Schema for Templates

```sql
-- New table for query templates
CREATE TABLE query_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    query_template TEXT NOT NULL,  -- SQL with {{param}} placeholders
    parameters JSONB,  -- Array of parameter definitions
    data_source VARCHAR(50),  -- 'signoz', 'redshift', 'athena'
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_public BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,
    avg_rows_returned INTEGER
);

-- Index for fast category/name searches
CREATE INDEX idx_templates_category ON query_templates(category);
CREATE INDEX idx_templates_created_by ON query_templates(created_by);
CREATE INDEX idx_templates_usage ON query_templates(usage_count DESC);

-- User saved queries (personal)
CREATE TABLE saved_queries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    data_source VARCHAR(50),
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0
);

-- Template usage tracking
CREATE TABLE template_usage_log (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES query_templates(id),
    user_id VARCHAR(100),
    parameters_used JSONB,
    duration_ms INTEGER,
    rows_returned INTEGER,
    executed_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. Example: Full Investigation Flow with New UI

### Scenario: Ops engineer investigates callback failure

1. **User opens Rewind, goes to Auto RCA view**
   - Enters JIRA ticket number or load ID
   - Clicks "Start Investigation"

2. **Multi-Agent Collaboration View appears**
   ```
   ┌─ Hypothesis Agent ─┐  ┌─ Data Fetchers ────┐  ┌─ Consensus Agent ─┐
   │ 🧠 ACTIVE           │  │ 📊 3/4 COMPLETE    │  │ 🤝 WAITING        │
   │ Generated 3 hyp...  │  │ Redshift: ✅       │  │ Needs 1 more...   │
   └─────────────────────┘  │ Tracking: ✅       │  └───────────────────┘
                            │ Callbacks: 🔄      │
                            └────────────────────┘
   ```

3. **Ops clicks "Show Reasoning" on Hypothesis Agent**
   - Sees full decision tree
   - Understands why H1 has 0.95 confidence
   - Can hover over any decision to see data sources used

4. **Ops notices Callbacks query is slow**
   - Clicks on "Callbacks: 🔄" in Data Fetchers lane
   - Sees actual SQL being executed
   - Sees progress: "Scanning 450 rows | 89% complete"
   - Can click "Explain Query" to understand why it's slow

5. **Consensus reached, but ops wants to verify**
   - Clicks "Query This Pattern" next to root cause
   - AI Query Builder opens with pre-filled template
   - Modifies date range, clicks "Execute"
   - Sees 47 similar cases in last 30 days

6. **Ops wants to save this for future use**
   - Clicks "Save as Template"
   - Names it "XYZ Carrier Relationship Issues"
   - Next time, can use template with one click

7. **Ops wants to see what happened to the load**
   - Switches to Timeline View
   - Enters load number ABC123
   - Sees full timeline with all data sources
   - Clicks on ocean event with error
   - Clicks "Show Context"
   - Sees ±5 logs before/after to understand sequence

8. **Ops closes ticket with RCA report**
   - Exports full timeline as PDF
   - Copies root cause summary
   - Pastes into JIRA with confidence
   - Total time: 3 minutes (vs 30-45 manual)

---

## 11. Success Metrics

### Quantitative
- **Investigation Time**: Reduce from 30-45 min to under 3 min (target: 90% faster)
- **Query Success Rate**: First query finds answer 85%+ of the time
- **Template Usage**: 60%+ of queries use templates after 30 days
- **Agent Visibility**: 70%+ of users expand reasoning panel
- **User Satisfaction**: NPS score >40

### Qualitative
- Ops team feels confident in AI conclusions
- Reduced "I don't know how to query this" support requests
- Increased trust in automated RCA (fewer manual overrides)
- Better knowledge sharing via saved templates
- Faster onboarding for new ops team members

---

## 12. Open Questions & Future Enhancements

### Open Questions
1. Should we support multi-load investigations (batch mode)?
2. How to handle conflicting hypotheses (no clear consensus)?
3. Should we add user feedback loop (thumbs up/down on root causes)?
4. How to display investigations that take >5 minutes?

### Future Enhancements
1. **Slack Integration**: Post RCA summaries to Slack channels
2. **Automated Remediation**: Suggest fixes (e.g., "Create relationship" button)
3. **Pattern Learning**: AI learns from ops corrections over time
4. **Mobile View**: Simplified view for on-call engineers
5. **Voice Commands**: "Show me callbacks for load ABC123"
6. **Collaborative Investigations**: Multiple ops can work on same case

---

## Summary

These UI improvements transform Rewind from a "black box AI tool" into a **transparent, powerful, and intuitive investigation platform** that ops teams will love. By showing agent reasoning, providing AI-assisted querying, and making logs/queries first-class citizens, we empower ops engineers to:

✅ **Understand WHY** the AI reached its conclusion
✅ **Trust the results** with full transparency
✅ **Move faster** with saved templates and AI query generation
✅ **Share knowledge** through template library
✅ **Debug deeper** with one-click log context

This positions Rewind as the go-to tool for all incident investigations, not just automated RCA.
