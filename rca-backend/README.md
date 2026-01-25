# Multi-Agent RCA Platform - Backend

**Comprehensive Root Cause Analysis powered by LangGraph multi-agent orchestration**

## Overview

This backend service implements a multi-agent AI system that performs automated root cause analysis for logistics/tracking issues. It uses LangGraph to orchestrate multiple specialized agents that work in parallel to investigate issues, form hypotheses, and determine root causes.

## Architecture

### Multi-Agent System

The system uses **LangGraph StateGraph** to orchestrate the following agents:

1. **Identifier Agent** - Extracts tracking IDs, load numbers, containers, etc. from issue text using LLM
2. **Data Collection Agents** (run in parallel):
   - **Tracking API Agent** - Fetches customer-facing load view
   - **JT Agent** - RPA scraping history (Ocean mode only)
   - **Super API Agent** - Internal tracking configuration
   - **Network Agent** - Carrier-shipper relationship validation
3. **Hypothesis Agent** - Forms hypotheses from collected evidence
4. **Synthesis Agent** - Determines final root cause or requests human input

### Workflow

```
Issue Text
    ↓
Identifier Agent (LLM extraction)
    ↓
Parallel Data Collection
  ├─ Tracking API Agent
  ├─ JT Agent (Ocean only)
  ├─ Super API Agent
  └─ Network Agent
    ↓
Hypothesis Agent (pattern matching + evidence scoring)
    ↓
Synthesis Agent (root cause determination or HITL)
    ↓
Root Cause + Recommended Actions
```

### State Management

Uses **LangGraph InvestigationState** with:
- **Accumulated data** from agents (using `operator.add` annotations)
- **Agent messages** for conversation UI
- **Timeline events** for visual flow
- **Executed queries** for data source panels
- **Hypotheses** with evidence for/against
- **Root cause** determination

## Project Structure

```
rca-backend/
├── app/
│   ├── agents/
│   │   ├── base.py                    # Base agent class
│   │   ├── identifier_agent.py        # LLM identifier extraction
│   │   ├── hypothesis_agent.py        # Hypothesis formation
│   │   ├── synthesis_agent.py         # Root cause determination
│   │   ├── workflow.py                # LangGraph workflow
│   │   └── data_agents/
│   │       ├── tracking_api_agent.py  # Tracking API data collection
│   │       ├── jt_agent.py            # Just Transform RPA history
│   │       ├── super_api_agent.py     # Super API config
│   │       └── network_agent.py       # Network relationship
│   ├── api/
│   │   └── rca.py                     # FastAPI SSE streaming endpoints
│   ├── models/
│   │   └── investigation.py           # State models, hypotheses, evidence
│   ├── services/
│   │   ├── jt_client.py               # NEW: Just Transform API client
│   │   ├── super_api_client.py        # NEW: Super API client
│   │   ├── confluence_client.py       # NEW: Confluence search
│   │   ├── slack_client.py            # NEW: Slack search
│   │   ├── tracking_api_client.py     # Reused from Rewind
│   │   ├── company_api_client.py      # Reused from Rewind
│   │   ├── redshift_client.py         # Reused from Rewind
│   │   ├── clickhouse_client.py       # Reused from Rewind
│   │   ├── athena_client.py           # Reused from Rewind
│   │   └── llm_client.py              # Reused from Rewind
│   ├── config.py                      # Configuration management
│   └── main.py                        # FastAPI application
├── .env                               # Environment variables
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## Setup

### Prerequisites

- Python 3.10+
- Access to FourKites APIs (credentials in `.env`)
- Access to data sources (Redshift, ClickHouse, Athena)
- LLM API keys (Anthropic Claude or Azure OpenAI)

### Installation

1. **Create virtual environment:**
   ```bash
   cd rca-backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - `.env` file is already configured with credentials from Rewind
   - Optionally add `SLACK_BOT_TOKEN` if using Slack integration

## Running the Backend

### Development Mode

```bash
cd rca-backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### POST /api/rca/investigate/stream

Start an investigation with Server-Sent Events (SSE) streaming.

**Request:**
```json
{
  "issue_text": "Load U110123982 is not tracking",
  "manual_identifiers": {  // Optional
    "tracking_id": "614258134",
    "mode": "OCEAN"
  }
}
```

**SSE Events Emitted:**
- `started` - Investigation started
- `agent_message` - Agent conversation updates
- `timeline_event` - Investigation timeline updates
- `hypothesis_update` - Hypotheses with confidence scores
- `query_executed` - Data source queries
- `root_cause` - Final root cause determination
- `needs_human` - Human-in-the-loop request
- `complete` - Investigation finished
- `error` - Error occurred

**Example Client (JavaScript):**
```javascript
const eventSource = new EventSource('/api/rca/investigate/stream', {
  method: 'POST',
  body: JSON.stringify({ issue_text: "Load not tracking" })
});

eventSource.addEventListener('agent_message', (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.agent}: ${data.message}`);
});

eventSource.addEventListener('root_cause', (event) => {
  const rootCause = JSON.parse(event.data);
  console.log('Root Cause:', rootCause.description);
});
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "rca-backend",
  "llm_provider": "azure_openai"
}
```

## Configuration

Key environment variables (from `.env`):

```bash
# LLM Provider
LLM_PROVIDER=azure_openai  # or "anthropic"

# API Base URLs
TRACKING_API_BASE_URL=https://tracking-api-rr.fourkites.com
COMPANY_API_BASE_URL=https://company-api.fourkites.com
DATAHUB_API_BASE_URL=https://ocean-support-datahub-staging.fourkites.com
JT_API_BASE_URL=https://just-transform.fourkites.com

# FourKites API Auth
FK_API_USER=msp.raja@fourkites.com
FK_API_PASSWORD=Forever@1998

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Agent Customization

### Adding a New Data Collection Agent

1. **Create agent file:**
   ```python
   # app/agents/data_agents/my_agent.py
   from app.agents.base import BaseAgent
   from app.models import InvestigationState

   class MyAgent(BaseAgent):
       def __init__(self):
           super().__init__("My Agent")

       async def execute(self, state: InvestigationState):
           # Fetch data
           data = await self.fetch_data(state)

           # Log query
           query_log = self.log_query(
               state,
               "My Data Source",
               "GET /api/my_endpoint",
               result_count=len(data)
           )

           return {
               "my_data": data,
               **query_log,
               "_message": "My data fetched successfully"
           }
   ```

2. **Register in workflow:**
   ```python
   # app/agents/workflow.py
   from app.agents.data_agents.my_agent import MyAgent

   class RCAWorkflow:
       def __init__(self):
           # ...
           self.my_agent = MyAgent()

       async def _parallel_data_collection_node(self, state):
           tasks = [
               # ...
               self.my_agent.run(state)
           ]
   ```

### Adding a New Hypothesis Pattern

Edit `app/agents/hypothesis_agent.py`:

```python
async def execute(self, state):
    hypotheses = []

    # ...existing patterns...

    # New pattern
    my_data = state.get("my_data", {})
    if my_data.get("some_condition"):
        hypotheses.append(self._create_hypothesis(
            "H_NEW",
            "Description of new hypothesis",
            RootCauseCategory.CUSTOM_CATEGORY,
            0.8,  # Confidence
            [Evidence(
                source="My Data Source",
                finding="Finding that supports this hypothesis",
                supports_hypothesis=True,
                weight=0.8
            )]
        ))
```

## Testing

### Manual Testing

1. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Test with curl:**
   ```bash
   curl -N -X POST http://localhost:8000/api/rca/investigate/stream \
     -H "Content-Type: application/json" \
     -d '{"issue_text": "Load U110123982 is not tracking"}'
   ```

3. **Expected output:**
   ```
   event: started
   data: {"investigation_id": "abc123...", "timestamp": "2025-01-20T..."}

   event: agent_message
   data: {"agent": "Identifier Agent", "message": "Extracted tracking_id=614258134"}

   event: agent_message
   data: {"agent": "Tracking API Agent", "message": "Load found..."}

   ...

   event: root_cause
   data: {"category": "network_relationship", "description": "Carrier-shipper..."}

   event: complete
   data: {"investigation_id": "abc123..."}
   ```

## Troubleshooting

### LLM Client Errors

If you see `Failed to create LLM client`:
- Check `LLM_PROVIDER` in `.env` (should be `azure_openai` or `anthropic`)
- Verify API keys are set (`AZURE_OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)

### API Connection Errors

If agents fail to fetch data:
- Verify API credentials in `.env` (`FK_API_USER`, `FK_API_PASSWORD`)
- Check network connectivity to FourKites APIs
- Test individual API clients in Python REPL

### Missing Dependencies

If you get import errors:
```bash
pip install -r requirements.txt
```

## Next Steps

### Frontend Integration

The frontend (Next.js) will:
1. Call `POST /api/rca/investigate/stream`
2. Listen for SSE events
3. Display real-time agent conversation
4. Visualize investigation timeline
5. Show hypothesis tracker with evidence
6. Display data source panels with queries

### Additional Features (Not Yet Implemented)

- **RAG System** - Vector search for Confluence/Slack/JIRA
- **Redshift Agent** - Query load validation errors
- **SigNoz Agent** - Recent log analysis
- **Athena Agent** - Historical callback/API logs
- **Analysis Agents** - Callback patterns, validation errors, ocean events
- **Session Persistence** - Save investigations to database
- **HITL UI** - Frontend modal for human input

## Contributing

When adding new agents or features:
1. Follow the BaseAgent pattern for consistency
2. Use proper logging (`self.logger.info()`)
3. Return state updates via dictionaries
4. Add timeline events and agent messages for UX
5. Log all queries for data source panels

## License

Internal FourKites project
