# AI Agent Readiness Assessment Framework

**Before building agents, ensure Layers 1-4 are complete**

---

## Assessment Checklist

Use this framework to determine if your domain is ready for AI agent development. You must complete Layers 1-4 before building Layer 5 (Agents).

---

## Layer 1: Discovery & Shadowing ✅

**Status:** Complete if you can answer YES to all questions

- [ ] Have you shadowed SME/Support Ops for 2-4 hours?
- [ ] Did you observe 5-10 real tickets/issues?
- [ ] Did you document how analysts think through problems?
- [ ] Did you capture which data sources they check first?
- [ ] Did you identify decision points and branching logic?
- [ ] Did you note confidence indicators ("I'm 90% sure when...")?
- [ ] Did you document edge cases and failure modes?

**Deliverable:** Shadow session notes (50-100 bullet points minimum)

**If NO to any:** Schedule shadow session with SME before proceeding.

---

## Layer 2: Knowledge Extraction ✅

**Status:** Complete if you have a filled-out extraction template

- [ ] Have you used the 12-section knowledge extraction template?
- [ ] Did you capture investigation flow (step-by-step logic)?
- [ ] Did you document all data sources and queries used?
- [ ] Did you identify diagnostic patterns (5-10 patterns minimum)?
- [ ] Did you map decision tree logic with conditions?
- [ ] Did you create test scenarios from real tickets?
- [ ] Did you validate extraction with SME?

**Deliverable:** Completed `knowledge_extraction_{domain}.yaml` (500-800 lines)

**If NO to any:** Complete knowledge extraction using `skills/_templates/knowledge_extraction_template.yaml`

---

## Layer 3: Skills Library ✅

**Status:** Complete if you have structured skills in AI-friendly format

- [ ] Have you created `skills/{domain}/SKILL.yaml`?
- [ ] Does it define trigger keywords (10+ keywords)?
- [ ] Does it list investigation capabilities?
- [ ] Does it reference data sources?
- [ ] Have you created pattern YAML files (5+ patterns minimum)?
- [ ] Have you created playbook YAML files?
- [ ] Have you created test case YAML files (5+ test cases)?
- [ ] Is ownership defined in CODEOWNERS?
- [ ] Is skill versioned in Git?

**Deliverables:**
- `skills/{domain}/SKILL.yaml` (400-700 lines)
- `skills/{domain}/patterns/*.yaml` (5-10 files)
- `skills/{domain}/playbooks/*.yaml` (2-5 files)
- `skills/{domain}/test_cases/*.yaml` (5+ files)

**If NO to any:** Create skill structure using existing skills as template.

---

## Layer 4: Data Layer (AI-Understandable) ✅

**Status:** Complete if data sources have AI-friendly interfaces

### Data Source Inventory

Check which MCP servers or APIs your skill needs:

**Available MCP Servers:**
- [x] **Athena MCP Server** - Query AWS Athena tables
- [x] **Redshift MCP Server** - Query Redshift data warehouse
- [x] **Tracking API MCP Server** - Query FourKites Tracking API
- [x] **Network API MCP Server** - Query network relationships
- [x] **Company API MCP Server** - Query company configuration
- [x] **SigNoz MCP Server** - Query observability logs and metrics
- [x] **Neo4j MCP Server** - Query graph database for relationships
- [x] **DataHub Super API MCP Server** - Query unified data catalog
- [x] **Slack MCP Server** - Search historical conversations
- [x] **Confluence MCP Server** - Search documentation

### Assessment Questions

For each data source your skill needs:

- [ ] Does an MCP server exist for this data source? (Check list above)
- [ ] Can the MCP server execute the queries your skill needs?
- [ ] Does the MCP server return data in AI-friendly format?
- [ ] Is authentication/authorization configured?
- [ ] Have you tested MCP server with sample queries?

**If NO to any:**
- If MCP server doesn't exist: Create new MCP server (or use REST API as interim)
- If MCP server exists but incomplete: Extend existing MCP server
- Document data source gaps in `skills/{domain}/DATA_SOURCES.md`

---

## Layer 5: Agent Layer 🔨

**Status:** Only proceed if Layers 1-4 are COMPLETE

- [ ] Are Layers 1-4 100% complete?
- [ ] Have you validated test cases (90%+ accuracy)?
- [ ] Do you have 5+ patterns ready?
- [ ] Are all data sources accessible via MCP/API?

**If YES to all:** You are ready to build agents!

**Agent Development Checklist:**
- [ ] Define agent architecture (single vs multi-agent)
- [ ] Build identifier agent (extracts IDs from input)
- [ ] Build data collection agents (one per MCP server)
- [ ] Build hypothesis agent (pattern matching)
- [ ] Build synthesis agent (generates resolution)
- [ ] Implement orchestration logic
- [ ] Test end-to-end with real tickets
- [ ] Measure accuracy and time savings
- [ ] Deploy to test environment

**If NO:** Complete missing layers before building agents. Building agents without foundation = 87% failure rate.

---

## Current Status Dashboard

### Domains Status Matrix

| Domain | Layer 1 | Layer 2 | Layer 3 | Layer 4 | Layer 5 | Ready? |
|--------|---------|---------|---------|---------|---------|--------|
| **OTR RCA** | ✅ Complete | ✅ Complete | ✅ 12 patterns | ✅ All MCP ready | 🔨 In Progress | ✅ YES |
| **Ocean Tracking** | 🟡 Partial | 🟡 Partial | 🟡 Definition only | ✅ MCP ready | ❌ Not started | ❌ NO - Complete L1-L3 |
| **Drayage** | ❌ Not started | ❌ Not started | ❌ Not started | 🟡 Some MCP ready | ❌ Not started | ❌ NO - Start at L1 |
| **Air** | ❌ Not started | ❌ Not started | ❌ Not started | 🟡 Some MCP ready | ❌ Not started | ❌ NO - Start at L1 |
| **Implementation** | ❌ Not started | ❌ Not started | ❌ Not started | ✅ All MCP ready | ❌ Not started | ❌ NO - Start at L1 |

---

## MCP Server Coverage Analysis

### What We Have ✅

| MCP Server | Status | Coverage | Use Cases |
|-----------|--------|----------|-----------|
| **Athena** | ✅ Production | 100% | Callbacks, events, raw data |
| **Redshift** | ✅ Production | 100% | Load validation, data marts, analytics |
| **Tracking API** | ✅ Production | 100% | Load search, status, tracking data |
| **Network API** | ✅ Production | 100% | Relationships, configuration |
| **Company API** | ✅ Production | 100% | Company settings, features |
| **SigNoz** | ✅ Production | 100% | Logs, metrics, traces |
| **Neo4j** | ✅ Production | 100% | Graph relationships, connections |
| **DataHub Super API** | ✅ Production | 100% | Unified data catalog |
| **Slack** | ✅ Production | 100% | Historical conversations |
| **Confluence** | ✅ Production | 100% | Documentation search |

**Total:** 10 MCP servers covering all major data sources

### What We Need (Gaps) 🔨

| Data Source | MCP Status | Priority | Workaround |
|-------------|-----------|----------|------------|
| JT Scraping API | ❌ Missing | High (Ocean) | Use REST API directly |
| Carrier Files API | ❌ Missing | Medium | Use REST API directly |
| Billing Systems | ❌ Missing | Low | Manual queries |
| Email Archives | ❌ Missing | Low | Use Slack as proxy |

---

## How to Use This Assessment

### For Domain Owners (Support Ops, SMEs)

**Step 1: Self-Assessment**
```bash
# Read this document
# Check boxes for your domain
# Identify which layer is incomplete
```

**Step 2: Gap Analysis**
```bash
# For incomplete layers, identify specific gaps:
# - Layer 1: Need shadow session with {SME name}
# - Layer 2: Need to complete extraction template
# - Layer 3: Need to create 5+ pattern files
# - Layer 4: Need MCP server for {data source}
```

**Step 3: Create Action Plan**
```bash
# Timeline to complete missing layers:
# - Layer 1: 2-4 hours (1 shadow session)
# - Layer 2: 2-4 days (extraction + validation)
# - Layer 3: 2-3 days (pattern files)
# - Layer 4: Verify MCP servers (1 day)
# Total: 5-8 days to readiness
```

### For AI/Engineering Teams

**Before Starting Agent Development:**

1. **Check readiness:** Is this domain ready? (All Layers 1-4 complete?)
2. **If NO:** Work with domain owner to complete missing layers
3. **If YES:** Proceed with agent development
4. **Validate:** Run test cases from Layer 3 to validate accuracy

---

## Red Flags 🚨

### Do NOT Build Agents If:

- ❌ **No knowledge extraction:** "We'll figure out patterns as we build"
  - **Why bad:** 87% of AI projects fail without domain knowledge foundation
  - **Fix:** Complete Layer 2 first

- ❌ **No test cases:** "We'll test with production traffic"
  - **Why bad:** Can't measure accuracy, can't validate improvements
  - **Fix:** Create 5+ test cases with expected outcomes

- ❌ **No skills library:** "We'll hardcode logic in agent"
  - **Why bad:** Not reusable, can't be updated by domain experts
  - **Fix:** Create skill YAML files in Layer 3

- ❌ **No MCP servers:** "Agent will query databases directly"
  - **Why bad:** No AI-friendly interface, hard to maintain, security issues
  - **Fix:** Use existing MCP servers or create new ones

- ❌ **Skipping discovery:** "We know the domain, don't need to shadow"
  - **Why bad:** Miss edge cases, nuances, actual mental models
  - **Fix:** Shadow session is mandatory - no shortcuts

---

## Green Flags ✅

### Ready to Build Agents When:

- ✅ **Complete extraction:** 500-800 line YAML with 12 sections filled
- ✅ **5+ patterns identified:** Each with evidence rules and test cases
- ✅ **MCP servers available:** All data sources have AI-friendly interfaces
- ✅ **Test cases validated:** 90%+ accuracy on pattern matching
- ✅ **SME sign-off:** Domain expert reviewed and approved extraction
- ✅ **Ownership defined:** Clear who maintains skills and patterns
- ✅ **Version controlled:** All artifacts in Git with CODEOWNERS

---

## Example: Ocean Tracking Readiness

**Current Status:**
```
Layer 1: 🟡 Partial (need 2-hour session with Surya)
Layer 2: 🟡 Partial (template started but not complete)
Layer 3: 🟡 Definition only (need to create pattern files)
Layer 4: ✅ Complete (JT API MCP, Super API MCP ready)
Layer 5: ❌ Not ready yet
```

**Gap Analysis:**
- **Missing:** Complete shadow session (2-4 hours)
- **Missing:** Finish extraction template (2 days)
- **Missing:** Create 8 pattern YAML files (2 days)
- **Missing:** Create test cases (1 day)

**Timeline to Readiness:** 5-6 days

**Action Plan:**
1. Week 1: Schedule 2-hour shadow session with Surya
2. Week 1: Complete knowledge extraction template (Surya + MSP Raja)
3. Week 2: Create 8 Ocean pattern files from extraction
4. Week 2: Create 5+ test cases from real Ocean tickets
5. Week 2: Validate patterns with Surya (90%+ accuracy)
6. **Week 3:** START agent development (not before)

---

## Example: OTR RCA Readiness

**Current Status:**
```
Layer 1: ✅ Complete (shadowed Prashant, documented flows)
Layer 2: ✅ Complete (extraction template filled, 12 sections)
Layer 3: ✅ Complete (12 patterns, 2 playbooks, test cases)
Layer 4: ✅ Complete (Athena, Redshift, Tracking API MCP servers)
Layer 5: 🔨 In Progress (multi-agent investigator being built)
```

**Status:** ✅ **READY FOR AGENT DEVELOPMENT**

All prerequisites met. Agent development in progress.

---

## Quick Readiness Check

**Answer these 4 questions:**

1. **Do you have a completed knowledge extraction?** (500-800 line YAML)
   - YES → Continue
   - NO → Stop. Complete Layer 2 first.

2. **Do you have 5+ pattern files with test cases?**
   - YES → Continue
   - NO → Stop. Complete Layer 3 first.

3. **Are all your data sources accessible via MCP servers?**
   - YES → Continue
   - NO → Stop. Complete Layer 4 first.

4. **Have you validated test cases with 90%+ accuracy?**
   - YES → ✅ **START BUILDING AGENTS!**
   - NO → Stop. Refine patterns until accuracy is 90%+.

---

## Contact for Help

**For Readiness Assessment:**
- MSP Raja (AI R&D Solutions Engineer)

**For Knowledge Extraction Sessions:**
- Schedule via [calendar link]

**For MCP Server Questions:**
- Check `mcp-servers/` repository
- Engineering team: #mcp-servers Slack channel

**For Skills Library Questions:**
- GitHub: Fourkites_Skills_Academy
- Slack: #ai-skills-library

---

## Summary

**Golden Rule:**

> **Do NOT build agents (Layer 5) until Layers 1-4 are 100% complete.**
>
> **Building without foundation = 87% failure rate.**

**Process:**
1. ✅ Shadow & Discover (Layer 1)
2. ✅ Extract Knowledge (Layer 2)
3. ✅ Create Skills (Layer 3)
4. ✅ Verify Data Access (Layer 4)
5. 🚀 Build Agents (Layer 5)

**Each layer depends on the previous one. No shortcuts.**

---

**Last Updated:** January 27, 2026
**Author:** MSP Raja, AI R&D Solutions Engineer
