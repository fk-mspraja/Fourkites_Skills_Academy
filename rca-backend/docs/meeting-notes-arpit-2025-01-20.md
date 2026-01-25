# RCA Syncup Meeting Notes - January 20, 2025

**Attendees:** MSP Raja, Arpit

## Current RCA Process Issues (Validated)

- Manual investigation process lacking systematic approach
- Missing data sources and evidence correlation
- Knowledge silos and context switching problems
- Random support ticket investigations with no structured methodology

## Multi-Agent Architecture Solution (Approved)

- Collaborative multi-agent system mimicking expert analyst team workflow
- Specialized agents for different skills (planning, investigation, state management)
- Backend with LangGraph orchestrator and investigation state graph
- Modular data collection agents for:
  - Tracking API ✅
  - Redshift ✅
  - Athena ✅
  - Future extensible sources

## Agent Collaboration Workflow (Working)

- Agent coordination and hypothesis formation working in parallel
- State management tracking investigation progress (30%, 40% completion)
- Human-in-the-loop when confidence is low or multiple issues found
- Evidence-based decision making with transparent logging
- State flow: extract identifiers → coordinate → review → collect proposals → routing decisions

## Current Implementation Status

| Component | Status |
|-----------|--------|
| LangGraph Orchestration | ✅ Working |
| Tracking API Agent | ✅ Working |
| Redshift Agent | ✅ Working (needs VPN) |
| Athena Agent | ✅ Working |
| UI Prototype | ✅ Showing conversational steps |
| Sample Scenario (load 603) | ✅ Tested |
| SSE Real-time Updates | ⚠️ Needs improvement |
| Heartbeat Updates | ❌ Not implemented |
| Clickable Investigation Cards | ❌ Not implemented |

## Action Items

### MSP Raja
- [ ] Implement SSE heartbeat updates for real-time progress
- [ ] Add clickable investigation cards in UI
- [ ] Focus on 2-3 primary data sources for POC
- [ ] Handle ocean-related use cases

### Arpit
- [ ] Provide MD documents with specific use cases and skill examples
- [ ] Handle non-ocean cases
- [ ] Define deployment strategy (auto-RCA option vs "Ops Agent" menu)

## Deployment Options

1. **Option A:** Integrate with existing auto-RCA option
2. **Option B:** Create new "Ops Agent" menu item (preferred)

## Next Steps

1. Arpit to provide use case documentation
2. Focus on 2-3 primary data sources for proof of concept
3. Parallel development track:
   - MSP: Ocean cases + core infrastructure
   - Arpit: Non-ocean cases
4. Improve UI with heartbeat updates
5. Make investigation cards clickable for drill-down

## Technical Decisions

- **Orchestration:** LangGraph StateGraph (confirmed)
- **Primary Data Sources for POC:** Tracking API, Redshift, Athena
- **UI Updates:** SSE with heartbeat for real-time feedback
- **Transparency:** All steps logged and queryable for ops team

---

*Meeting transcript: https://notes.granola.ai/t/a33fb026-f22b-4fe8-b5b8-ca274ac31011*
