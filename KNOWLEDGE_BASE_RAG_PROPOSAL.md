# Knowledge-Augmented RCA: Uber Genie Approach for Causeway Platform

**From:** MSP Raja
**To:** Arpit Garg
**Re:** Adding Confluence + Slack + Jira as knowledge sources (Uber Genie approach)
**Date:** January 14, 2026

---

## TL;DR

**Yes, absolutely!** Adding RAG (Retrieval-Augmented Generation) with Confluence/Slack/Jira would significantly enhance our Ocean Debugging Agent. This combines our **structured decision tree** (for deterministic debugging) with **unstructured tribal knowledge** (for edge cases and historical solutions).

**Uber's Results:** 70,000 questions answered, 48.9% helpfulness, 13,000 hours saved
**Our Opportunity:** Even better - we have structured data + unstructured knowledge

---

## Current Architecture vs. Enhanced Architecture

### Current (Decision Tree Only)

```
Salesforce Ticket
  ↓
Extract Identifiers (LLM)
  ↓
Decision Tree + Data Sources
  ├─ Redshift (network relationships)
  ├─ ClickHouse (CFW logs)
  ├─ JustTransform (scraping history)
  ├─ Tracking API (load details)
  └─ Super API (configuration)
  ↓
Root Cause Determination
```

**Limitations:**
- Only handles cases in decision tree
- No access to tribal knowledge
- Can't learn from historical resolutions
- Misses edge cases documented in Confluence/Slack

---

### Enhanced (Decision Tree + Knowledge RAG)

```
Salesforce Ticket
  ↓
Extract Identifiers (LLM)
  ↓
Parallel Investigation:
  ├─ [Path 1] Decision Tree + Data Sources (structured)
  │    ├─ Redshift, ClickHouse, JT, APIs
  │    └─ Deterministic root cause logic
  │
  └─ [Path 2] Knowledge Base RAG (unstructured)
       ├─ Confluence wiki pages
       ├─ Slack thread history
       ├─ Jira ticket resolutions
       └─ Support team documentation
  ↓
Hybrid Decision:
  ├─ If decision tree confident (>0.7) → Use that
  ├─ If uncertain → Check knowledge base
  └─ If both found → Present both with citations
  ↓
Root Cause + Historical Context
```

**Advantages:**
- ✅ Handles both structured and unstructured scenarios
- ✅ Learns from historical resolutions
- ✅ Captures edge cases (like the Pepsi carrierless load)
- ✅ Leverages Surya/Prashant's documented procedures
- ✅ Provides citations (transparency)
- ✅ Continuously improves as docs/threads added

---

## Knowledge Sources to Ingest

### 1. Confluence Pages

**What to Include:**
```
FourKites Confluence
├── Support Documentation
│   ├── Carrier Files Processing Guide (Prashant's catalog)
│   ├── Ocean Troubleshooting Procedures
│   ├── Network Relationship Setup
│   ├── JustTransform Debugging Guide
│   └── Common Root Causes
│
├── Engineering Docs
│   ├── CFW Architecture
│   ├── Data Ingestion Flows
│   ├── API Documentation
│   └── Database Schema Reference
│
└── Runbooks
    ├── Load Not Tracking Runbook
    ├── ETA Discrepancy Runbook
    ├── Duplicate Events Runbook
    └── Integration Failure Runbook
```

**Why This Matters:**
- Prashant's data dictionary → Becomes searchable
- Support team runbooks → Directly applicable
- Architecture docs → Context for decisions

---

### 2. Slack Channels

**Channels to Index:**
```
Slack Channels
├── #support-team (ISBO)
│   └── Real ticket resolutions, Q&A with Surya/Prashant
│
├── #ocean-debugging (or equivalent)
│   └── Specific ocean issue discussions
│
├── #carrier-integrations
│   └── Carrier-specific issues, integration changes
│
├── #engineering-alerts
│   └── System issues, CFW errors, log anomalies
│
└── Your private group (Arpit + Surya + Prashant + Raja)
    └── Project discussions, edge cases discovered
```

**What to Extract:**
- Threaded conversations with resolutions
- Code snippets shared
- SQL queries that worked
- Links to related Jira tickets
- Carrier-specific quirks ("CR England always sends ref number")

**Example Use Case:**
```
Agent finds: "Load 9118452, no carrier, dispatcher API updates"
RAG retrieves: Slack thread where Prashant said
  "First time seeing this... definite outlier...
   system falls back to reference number"
Agent includes: Historical context + citation
```

---

### 3. Jira Tickets

**What to Index:**
```
Jira Projects
├── Support Tickets (Salesforce-synced)
│   ├── Resolution notes
│   ├── Root cause tags
│   └── Time to resolution
│
├── Engineering Bugs
│   ├── CFW issues
│   ├── Network relationship bugs
│   └── JT scraping failures
│
└── Feature Requests
    └── Requested improvements based on support pain points
```

**What to Extract:**
- Ticket description + resolution
- Root cause analysis in comments
- Workarounds documented
- Related tickets (pattern detection)
- Fix versions (when was issue resolved)

**Example Use Case:**
```
Agent investigating: Network relationship missing
RAG finds: 15 similar Jira tickets
          All resolved by Network Team
          Average resolution: 2 days
          Pattern: Same carrier, multiple shippers affected
Agent recommends: Create bulk network relationships
```

---

## RAG Architecture (Uber Genie Style)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE INGESTION                       │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  [Confluence]       [Slack API]        [Jira API]
   API Fetch        Thread Export      Ticket Export
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    Text Chunking
              (500 tokens, 100 overlap)
                           │
                           ▼
                    Embedding Model
                  (OpenAI text-embedding-3)
                           │
                           ▼
                   Vector Database
                  (Pinecone / Weaviate)
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
  Metadata Index                        Full Text Index
  - source_type                         - original_content
  - source_url                          - summary
  - author                              - keywords
  - date                                - related_tickets
  - category

┌─────────────────────────────────────────────────────────────┐
│                    QUERY TIME (AGENT USES RAG)               │
└─────────────────────────────────────────────────────────────┘

User Query: "Load 9118452, no carrier, dispatcher API"
        │
        ▼
Query Embedding (same model)
        │
        ▼
Vector Search (top 10 similar documents)
        │
        ▼
Rerank (by date, source authority, relevance)
        │
        ▼
Top 3 Retrieved Documents:
  1. Slack thread: Prashant on carrierless loads [0.92 similarity]
  2. Confluence: Dispatcher API troubleshooting [0.88]
  3. Jira: Similar ticket resolution [0.85]
        │
        ▼
Context Injection to LLM:
        │
        ▼
┌─────────────────────────────────────────────────┐
│  You are investigating load 9118452.           │
│                                                │
│  Retrieved Knowledge:                          │
│  1. [Slack] Prashant: "Carrierless loads..."  │
│  2. [Confluence] "Dispatcher API debugging..." │
│  3. [Jira] "Ticket #12345 similar issue..."   │
│                                                │
│  Based on decision tree AND knowledge base,    │
│  determine root cause. Cite sources.           │
└─────────────────────────────────────────────────┘
        │
        ▼
LLM Response with Citations:
  "Root Cause: System fallback to reference number
   (carrierless load exception case)

   Sources:
   - Slack: [Link to thread]
   - Confluence: [Link to page]
   - Similar ticket: JIRA-12345"
```

---

## Implementation Plan

### Phase 1: Data Ingestion Pipeline (Week 1-2)

**1.1 Confluence Ingestion**
```python
from atlassian import Confluence

class ConfluenceIngester:
    def __init__(self, url, username, api_token):
        self.confluence = Confluence(url, username, api_token)

    def ingest_space(self, space_key):
        pages = self.confluence.get_all_pages_from_space(space_key)

        for page in pages:
            content = self.confluence.get_page_by_id(
                page['id'],
                expand='body.storage'
            )

            # Extract text from HTML
            text = strip_html(content['body']['storage']['value'])

            # Chunk and embed
            chunks = chunk_text(text, chunk_size=500, overlap=100)

            for i, chunk in enumerate(chunks):
                yield {
                    'content': chunk,
                    'metadata': {
                        'source': 'confluence',
                        'page_id': page['id'],
                        'page_title': page['title'],
                        'url': f"{url}/pages/{page['id']}",
                        'space': space_key,
                        'chunk_index': i,
                        'last_modified': content['version']['when']
                    }
                }
```

**1.2 Slack Ingestion**
```python
from slack_sdk import WebClient

class SlackIngester:
    def __init__(self, token):
        self.client = WebClient(token=token)

    def ingest_channel(self, channel_id, days_back=365):
        # Get channel history
        result = self.client.conversations_history(
            channel=channel_id,
            oldest=timestamp_days_ago(days_back)
        )

        # Get threads
        for message in result['messages']:
            if message.get('thread_ts'):
                thread = self.client.conversations_replies(
                    channel=channel_id,
                    ts=message['thread_ts']
                )

                # Combine thread into single document
                thread_text = self._format_thread(thread['messages'])

                yield {
                    'content': thread_text,
                    'metadata': {
                        'source': 'slack',
                        'channel_id': channel_id,
                        'thread_ts': message['thread_ts'],
                        'url': self._get_thread_url(channel_id, message['thread_ts']),
                        'participants': extract_users(thread['messages']),
                        'date': message['ts'],
                        'has_resolution': self._detect_resolution(thread_text)
                    }
                }
```

**1.3 Jira Ingestion**
```python
from jira import JIRA

class JiraIngester:
    def __init__(self, server, username, api_token):
        self.jira = JIRA(server, basic_auth=(username, api_token))

    def ingest_project(self, project_key, issue_types=['Support']):
        jql = f"project = {project_key} AND issuetype in ({','.join(issue_types)})"
        issues = self.jira.search_issues(jql, maxResults=10000)

        for issue in issues:
            # Combine description + comments + resolution
            full_text = f"""
            Title: {issue.fields.summary}
            Description: {issue.fields.description}

            Resolution Notes:
            {self._get_resolution_notes(issue)}

            Root Cause:
            {self._extract_root_cause(issue)}
            """

            yield {
                'content': full_text,
                'metadata': {
                    'source': 'jira',
                    'issue_key': issue.key,
                    'url': f"{server}/browse/{issue.key}",
                    'issue_type': issue.fields.issuetype.name,
                    'status': issue.fields.status.name,
                    'created': issue.fields.created,
                    'resolved': issue.fields.resolutiondate,
                    'assignee': issue.fields.assignee.name if issue.fields.assignee else None,
                    'labels': issue.fields.labels
                }
            }
```

---

### Phase 2: Vector Database Setup (Week 2)

**2.1 Technology Choice**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Pinecone** | Managed, fast, easy | Cost ($70/mo+) | ✅ **Best for MVP** |
| **Weaviate** | Open source, powerful | Self-hosted | For production |
| **Chroma** | Simple, local | Not scalable | For testing |

**2.2 Embedding Model**

```python
from openai import OpenAI

class EmbeddingService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # $0.02/1M tokens

    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Batch for efficiency
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

**2.3 Pinecone Setup**

```python
import pinecone

pinecone.init(api_key="your-key", environment="us-west1-gcp")

# Create index
index_name = "causeway-knowledge-base"
pinecone.create_index(
    name=index_name,
    dimension=1536,  # text-embedding-3-small dimension
    metric="cosine"
)

index = pinecone.Index(index_name)

# Upsert vectors
def upsert_document(doc_id, embedding, metadata):
    index.upsert(vectors=[{
        'id': doc_id,
        'values': embedding,
        'metadata': metadata
    }])
```

---

### Phase 3: RAG Integration into Agent (Week 3-4)

**3.1 Knowledge Base Module**

```python
class KnowledgeBase:
    def __init__(self, pinecone_index, embedding_service):
        self.index = pinecone_index
        self.embedder = embedding_service

    def search(self, query: str, top_k: int = 5, filters: dict = None):
        """
        Search knowledge base for relevant documents.

        Args:
            query: User query or investigation context
            top_k: Number of results to return
            filters: Metadata filters (source_type, date_range, etc.)

        Returns:
            List of relevant documents with scores
        """
        # Embed query
        query_embedding = self.embedder.embed(query)

        # Search vector database
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filters
        )

        # Rerank by date (recent first) and source authority
        reranked = self._rerank(results.matches)

        return reranked

    def _rerank(self, matches):
        """Rerank results by recency and source authority"""
        source_weights = {
            'confluence': 1.0,  # Official docs highest
            'slack': 0.8,       # Recent discussions
            'jira': 0.9         # Proven resolutions
        }

        for match in matches:
            source = match.metadata['source']
            date_score = self._date_recency_score(match.metadata.get('date'))

            match.adjusted_score = (
                match.score * source_weights.get(source, 0.5) * date_score
            )

        return sorted(matches, key=lambda x: x.adjusted_score, reverse=True)
```

**3.2 Hybrid Decision Engine**

```python
class HybridDecisionEngine:
    def __init__(self, decision_tree_engine, knowledge_base, llm_client):
        self.tree = decision_tree_engine
        self.kb = knowledge_base
        self.llm = llm_client

    def evaluate(self, state: InvestigationState) -> Decision:
        """
        Evaluate using both decision tree AND knowledge base.
        """
        # Path 1: Decision tree (structured)
        tree_decision = self.tree.evaluate(state)

        # Path 2: Knowledge base (unstructured)
        kb_context = self._get_knowledge_context(state)

        # Combine
        if tree_decision.confidence >= 0.7:
            # High confidence from decision tree - use it
            # But enrich with knowledge base for context
            return self._enrich_decision(tree_decision, kb_context)

        else:
            # Low confidence - consult knowledge base
            return self._llm_analysis_with_context(state, kb_context)

    def _get_knowledge_context(self, state: InvestigationState):
        """Query knowledge base for relevant context"""
        # Build search query from state
        query = f"""
        Load: {state.identifiers.get('load_id')}
        Carrier: {state.identifiers.get('carrier_id')}
        Issue: Load not tracking
        Evidence: {self._summarize_evidence(state.evidence)}
        """

        # Search knowledge base
        results = self.kb.search(query, top_k=3)

        return results

    def _llm_analysis_with_context(self, state, kb_context):
        """Use LLM to analyze with retrieved context"""
        prompt = f"""
        Investigation State:
        {state.to_dict()}

        Retrieved Knowledge:
        {self._format_kb_results(kb_context)}

        Based on the evidence AND historical knowledge, determine:
        1. Root cause
        2. Confidence (0-1)
        3. Explanation
        4. Citations
        """

        response = self.llm.analyze(prompt)

        return Decision(
            root_cause=response['root_cause'],
            confidence=response['confidence'],
            explanation=response['explanation'],
            citations=self._extract_citations(kb_context)
        )
```

---

### Phase 4: Citation & Transparency (Week 4)

**4.1 Citation Format**

```python
class Citation:
    def __init__(self, source_type, title, url, relevance_score):
        self.source_type = source_type  # confluence, slack, jira
        self.title = title
        self.url = url
        self.relevance_score = relevance_score

    def to_markdown(self):
        emoji = {
            'confluence': '📄',
            'slack': '💬',
            'jira': '🎫'
        }

        return f"{emoji[self.source_type]} [{self.title}]({self.url}) (relevance: {self.relevance_score:.0%})"
```

**4.2 Investigation Report with Citations**

```markdown
# Investigation Report: Load 9118452

## Root Cause
**Network relationship missing** (7.7% of stuck ocean loads)

## Confidence: 85%

## Explanation
No carrier-shipper relationship exists in company_relationships table.
This is a known pattern affecting loads from this carrier.

## Evidence
- [Redshift] Network query returned 0 results
- [CFW Logs] DataMonitoringUtils shows skipped_messages
- [Similar Loads] Found 12 other stuck loads from same carrier

## Historical Context
This issue has been documented and resolved multiple times:

📄 [Confluence: Network Relationship Setup Guide](https://confluence.fourkites.com/...)
   - Explains how to create relationships
   - References: relevance 92%

💬 [Slack Thread: Similar Issue Discussion](https://fourkites.slack.com/archives/...)
   - Prashant: "Always check network first for stuck loads"
   - Date: 2025-12-10
   - Relevance: 88%

🎫 [JIRA-8234: Bulk Network Relationship Creation](https://jira.fourkites.com/...)
   - Resolution: Created 15 relationships for same carrier
   - Impact: Fixed 45 stuck loads
   - Resolved: 2025-11-20
   - Relevance: 85%

## Recommended Action
Create network relationship between:
- Shipper: Smithfield Foods
- Carrier: CR England

Expected impact: 12+ loads will start tracking within 5 minutes.

## Pattern Alert
This carrier has recurring network relationship issues.
Consider: Bulk relationship creation audit.
```

---

## Cost Analysis

### Uber's Scale
- 154 Slack channels
- 70,000 questions answered
- 48.9% helpfulness
- 13,000 hours saved

### Our Estimated Scale (First 6 Months)

| Component | Volume | Cost |
|-----------|--------|------|
| **Confluence Pages** | 500 pages | Embedding: $0.50 |
| **Slack Threads** | 10,000 threads | Embedding: $2.00 |
| **Jira Tickets** | 5,000 tickets | Embedding: $1.00 |
| **Storage (Pinecone)** | 50k vectors | $70/month |
| **Query Cost** | 1000 queries/day | OpenAI: $10/month |
| **Re-indexing** | Weekly refresh | $5/month |
| **Total** | | **$88/month** |

**ROI:**
- If saves 10 hours/week for support team (conservative)
- 10 hours × $50/hour = $500/week = $2,000/month
- **ROI: 23x** (2000/88)

---

## Success Metrics (Uber-inspired)

### Quantitative
- **Question Volume:** Track how many times agent uses KB vs decision tree
- **Helpfulness Rate:** "Was this context useful?" feedback
- **Time Saved:** Compare with/without KB enhancement
- **Citation Accuracy:** Are sources actually relevant?

### Qualitative
- **Edge Case Coverage:** Can now handle outliers (like Pepsi carrierless load)
- **Knowledge Discovery:** Surfacing forgotten solutions
- **Team Learning:** New analysts learn from experienced ones

### Target Goals (6 months)
- 50%+ of investigations use KB
- 60%+ helpfulness rate (beats Uber's 48.9%)
- 20 hours/week saved (support team)
- 90%+ citation relevance

---

## Comparison: Decision Tree vs RAG vs Hybrid

| Scenario | Decision Tree Only | RAG Only | Hybrid (Recommended) |
|----------|-------------------|----------|---------------------|
| **Standard network missing** | ✅ Fast, accurate | ⚠️ Slower, may work | ✅ Best of both |
| **Pepsi carrierless load** | ❌ Not in tree | ✅ Found in Slack | ✅ RAG provides context |
| **New carrier integration** | ❌ Unknown pattern | ✅ Similar docs found | ✅ RAG + human handoff |
| **CFW parsing error** | ✅ Checks logs | ⚠️ May miss specifics | ✅ Logs + historical solutions |
| **Speed** | ⚡ 10-15 sec | 🐌 30-45 sec | ⚡ 15-20 sec (parallel) |
| **Explainability** | ✅ Clear logic | ⚠️ Black box | ✅ Logic + citations |
| **Maintenance** | 🔧 Update tree manually | 🔄 Auto-learns | 🔄 Best of both |

---

## Implementation Timeline

```
Week 1-2: Data Ingestion Pipeline
  ├─ Confluence API integration
  ├─ Slack export automation
  ├─ Jira ticket indexing
  └─ Initial embedding generation

Week 3: Vector Database Setup
  ├─ Pinecone account + index
  ├─ Upload embeddings
  └─ Test search quality

Week 4: Agent Integration
  ├─ Knowledge base module
  ├─ Hybrid decision engine
  ├─ Citation formatting
  └─ Testing with real cases

Week 5: Refinement
  ├─ Tune relevance thresholds
  ├─ Optimize reranking
  ├─ Add feedback loop
  └─ Performance optimization

Week 6: Deployment
  ├─ Internal demo (Surya + Prashant)
  ├─ Gather feedback
  ├─ Iterate
  └─ Production rollout
```

---

## Answer to Arpit's Question

> "Could we not have something like this as one of the source for our auto RCA .. like confluence wiki + slack channel responses (history of these )+possible jira?"

**YES! This is exactly what we should do.**

**Why it's perfect for us:**
1. ✅ We already have structured data approach (decision tree + APIs)
2. ✅ RAG adds unstructured tribal knowledge layer
3. ✅ Covers edge cases that decision tree misses
4. ✅ Learns from historical resolutions automatically
5. ✅ Provides transparency via citations
6. ✅ Low cost, high ROI
7. ✅ Complements existing work rather than replacing it

**Recommendation:**
- Add RAG as **Phase 6** of Ocean Debugging Agent (after Phase 5 deployment)
- Or run as **parallel track** while you (Raja) finish core agent
- Arpit could own RAG pipeline, Raja focuses on decision engine integration

**Next Steps:**
1. Get Confluence/Slack/Jira API access
2. Set up Pinecone account (free tier for testing)
3. Start with small pilot: Index 50 Confluence pages + 100 Slack threads
4. Test retrieval quality before full ingestion
5. Integrate into agent incrementally

---

**This would make Causeway Platform truly unique:**
- **Uber's Genie:** RAG only (unstructured knowledge)
- **Causeway:** RAG + Decision Trees + Real-time Data Queries (structured + unstructured)

**We'd have the best of all worlds.**

---

**Want me to create a detailed implementation spec or prototype the ingestion pipeline?**

---

**Sources:**
- [Uber Genie Blog Post](https://www.uber.com/en-IN/blog/genie-ubers-gen-ai-on-call-copilot/)
