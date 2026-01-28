# Team Sync Questions - Cassie Agent Architecture & Vision

**Meeting Goal:** Understand strategic vision, architectural boundaries, and expectations before finalizing gap analysis

**Attendees:** Goutham, Ashish, Sudhanshu, Arpit

---

## Section 1: Strategic Vision & Scope

**1.1 What is Cassie's intended scope?**
- Classification/routing only?
- Investigation orchestration?
- End-to-end case resolution?

**1.2 What does "success" look like for Phase 1?**
- Auto-resolution target percentage?
- Time to resolution improvement?
- Accuracy requirements?
- Customer satisfaction goals?

**1.3 Which use cases are in scope for Phase 1?**
- Load Not Tracking only?
- Specific sub-categories (OTR, Ocean, Intermodal)?
- Other case types?

---

## Section 2: Architecture & Components

**2.1 Who owns what in the architecture?**
- Cassie team: classification + routing?
- React Agent + specialized prompts: who maintains these?
- MCP servers: who builds/enhances these?

**2.2 What is the intended role of MCP servers?**
- Pure data access layer?
- Diagnostic logic embedded in MCPs?
- Hybrid approach?

**2.3 Where should diagnostic intelligence live?**
- In Cassie's classification logic?
- In specialized prompts that guide React Agent?
- In MCPs as intelligent services?
- Distributed across layers?

**2.4 What is React Agent's role?**
- Generic executor following prompt guidance?
- Intelligent investigator with its own logic?
- Something else?

---

## Section 3: Diagnostic Patterns & Automation

**3.1 Category Sheet (100+ patterns):**
- Is this the source of truth for automation patterns?
- Are bot feasibility ratings (HIGH/MEDIUM/LOW) accurate?
- Which patterns should be prioritized first?

**3.2 How should patterns be encoded?**
- As specialized prompts?
- As MCP-side logic?
- As a separate pattern library?
- Configuration-driven vs code-driven?

**3.3 Auto-resolution criteria:**
- What confidence threshold triggers auto-response?
- What cases should always escalate to human?
- How do we handle edge cases and ambiguity?

---

## Section 4: Data & Integration

**4.1 MCP Coverage:**
- Do current MCPs have all needed data for top 20 patterns?
- What data is missing (logs, configs, metrics)?
- Are there plans to build additional MCPs?

**4.2 Log Access:**
- GPS provider API logs - available via which MCP?
- Outlier detection logs - accessible?
- Status processing logs - queryable?
- Configuration change logs - tracked?

**4.3 Real-time vs Historical:**
- Which diagnostics need real-time API calls?
- Which can work with data warehouse queries?
- Performance/latency requirements?

---

## Section 5: Implementation Plan

**5.1 Current 11-week timeline:**
- What are the key milestones?
- What's planned for Weeks 1-2 (quick wins)?
- What dependencies exist between phases?

**5.2 Team structure:**
- Who works on what components?
- Where can I contribute most effectively?
- Are there parallel workstreams?

**5.3 Decision-making:**
- Who approves architectural decisions?
- How are priorities set?
- What's the process for proposing changes?

---

## Section 6: My Gap Analysis Document

**6.1 What did I get right?**
- Findings that align with your understanding
- Gaps you were already aware of
- Recommendations that make sense

**6.2 What did I miss or misunderstand?**
- Architectural context I lacked
- Planned improvements not reflected
- Strategic decisions I wasn't aware of

**6.3 What's most useful from the analysis?**
- Production case failures investigation?
- Pattern taxonomy analysis?
- Technical architecture review?
- Something else?

---

## Section 7: Next Steps

**7.1 How should I refine this analysis?**
- Focus areas to expand
- Sections to remove or deprioritize
- Additional research needed

**7.2 What deliverables would be most valuable?**
- Revised gap analysis with your context
- Pattern-to-implementation mapping
- MCP requirement specifications
- Technical design proposals
- Something else?

**7.3 Timeline for refinement:**
- When do you need the revised version?
- Iterative feedback cycles vs single pass?

---

## Pre-Meeting Homework

**For me:**
- Review any existing architecture docs they share
- Study the current 11-week plan in detail
- Prepare to take notes and ask clarifying questions

**For them:**
- Quick review of the gap analysis PDF (optional - can discuss without reading)
- Share any existing design docs or ADRs
- Share current phase breakdown and responsibilities

---

## Meeting Agenda (Suggested 60 min)

**0-10 min:** Context setting - current state and vision
**10-25 min:** Architecture & ownership clarification
**25-40 min:** Pattern automation strategy
**40-50 min:** Feedback on gap analysis
**50-60 min:** Next steps and action items

---
