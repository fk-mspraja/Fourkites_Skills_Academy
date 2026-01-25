# FourKites Skills Academy 🎓

**Eliminating the Internal Coordination Tax Through Reusable Organizational Knowledge**

> *"The companies that win in autonomous operations won't be the ones with the best technology. They'll be the ones that operate with the speed and precision that AI enables."* — Matt Elenjickal, CEO

---

## 🎯 Vision

FourKites Skills Academy packages our institutional knowledge into **discoverable, reusable skills** that work for both **humans and AI agents**. No more scattered docs, tribal knowledge, or 2-hour Slack searches.

### The Problem We're Solving

**Common scenario across teams:**
- Employee needs standard content or process documentation
- Asks in Slack, gets multiple outdated responses
- "We had something but it needs updating..."
- "We started refreshing it but teams changed..."

**Result:** Hours wasted, scattered knowledge, no clear answer.

**With Skills Academy:** 30 seconds, self-service, always current.

---

## 🏗️ What Are Agent Skills?

Agent Skills are the **industry standard** (created by Anthropic) for packaging organizational knowledge:

- **For Humans:** Single source of truth, instantly searchable
- **For AI Agents:** Structured context that makes them 10x more accurate
- **For Organizations:** Version-controlled knowledge that survives team changes

### Technical Foundation

Built on [Anthropic's Agent Skills framework](https://agentskills.io):
- Open standard, not proprietary
- Portable across all AI tools
- Proven by the creators of Claude
- Designed specifically to eliminate coordination tax

---

## 📚 Current Skills Catalog

### ✅ Production Skills (Live)

#### `rca-support-agent`
**Root Cause Analysis for Support Cases**

Comprehensive RCA workflow for diagnosing logistics/tracking issues:
- Load not tracking patterns (85+ subcategories)
- ELD troubleshooting procedures
- Data source integration guides
- Multi-agent orchestration patterns

**Impact:** Automates 60% of L1 support investigations

---

### 🚧 Pilot Skills (In Development)

These address the **exact gaps** found in our coordination tax audit:

#### `fourkites-products`
**Complete Product Catalog & Capabilities**

*Solves:* "Sales cannot confidently articulate our full platform value"
- ICT components and features
- Digital Workers catalog
- Integration capabilities
- Competitive positioning

#### `customer-journey`
**Standard CS Playbooks & Charters**

*Solves:* Long searches for customer success content and playbooks
- Kickoff templates
- QBR frameworks
- Success metrics
- Engagement models

#### `implementation-methodology`
**ICT + Digital Workforce Implementation Framework**

*Solves:* Missing standardized implementation content for customer-facing teams
- Standard implementation phases
- CIE processing workflows
- Integration patterns
- Best practices

#### `troubleshooting-runbooks`
**P0/P1 Incident Response Procedures**

*Solves:* "12+ hour P0 with multiple Slack threads"
- Automated escalation paths
- Pre-approved communication templates
- Diagnostic decision trees
- On-call runbooks

---

## 🎯 Pilot Results (Target Metrics)

| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| **Content Search Time** | 2+ hours | 30 seconds | **95% reduction** |
| **Onboarding Duration** | 4-6 weeks | 1-2 weeks | **60% faster** |
| **AI Agent Accuracy** | ~60% useful | ~95% useful | **58% improvement** |
| **Knowledge Decay** | High (teams change) | Zero (version-controlled) | **Permanent** |

---

## 🚀 Quick Start

### For Humans

**Browse Skills:**
```bash
open web/index.html
```

**Search for Knowledge:**
```
"How do I troubleshoot ELD issues?" → rca-support-agent skill
"What's our CS kickoff process?" → customer-journey skill
"What products do we offer?" → fourkites-products skill
```

### For AI Agents

Skills are automatically discoverable by Claude and other compatible AI tools:

```python
# Example: Agent using rca-support-agent skill
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4.5",
    skills=["rca-support-agent"],
    messages=[{
        "role": "user",
        "content": "Load U110123982 not tracking, ELD enabled but no updates"
    }]
)
# Agent automatically accesses ELD troubleshooting patterns
```

---

## 📖 Documentation

- [Vision & Strategy](docs/VISION.md) - Why Skills Academy matters
- [Pilot Plan](docs/PILOT_PLAN.md) - 2-week validation approach
- [ROI Analysis](docs/ROI_ANALYSIS.md) - Business impact projections
- [Contributing Guide](docs/CONTRIBUTING.md) - How to create skills

---

## 🎬 Demo for Leadership

**Show the problem:**
1. Explain common scenario: hours spent searching for standard content
2. Demonstrate coordination tax impact across teams

**Show the solution:**
1. Open Skills Academy web interface
2. Search for "CS Journey" → Instant results
3. Show AI agent using the skill → Accurate response
4. Demonstrate version control → Knowledge never decays

**Show the vision:**
- 50+ skills covering all FourKites domains
- Every employee has instant access
- Every AI agent has perfect context
- We operate at AI-age velocity

---

## 🏆 Success Criteria

**Phase 1 (Weeks 1-2): Pilot Validation**
- ✅ Build 3 skills from missing content
- ✅ Test with 10 Sales/CS users
- ✅ Achieve 95% reduction in search time

**Phase 2 (Weeks 3-6): Core Catalog**
- Build 15 essential skills across domains
- Train skill creators in each department
- Integrate with Claude Desktop

**Phase 3 (Weeks 7-12): Full Rollout**
- 50+ skills covering all domains
- Company-wide adoption
- AI agents using skills in production

---

## 🤝 Contributing

Every department contributes skills in their domain:

**Sales:** Product positioning, competitive battlecards
**CS:** Playbooks, success metrics, engagement models
**Professional Services:** Implementation frameworks, integration patterns
**Support:** Troubleshooting runbooks, diagnostic procedures
**R&D:** Architecture patterns, API documentation
**Product:** Feature specs, roadmap context

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for skill creation guide.

---

## 📊 Alignment with Strategic Initiatives

Skills Academy is the **foundation** for Matt's 45-day coordination tax elimination:

| Initiative | How Skills Academy Enables It |
|------------|------------------------------|
| **Standardized Repeatability** | Skills = standardized packages & playbooks |
| **Eliminate Manual Handoffs** | Knowledge flows automatically, not via Slack |
| **Close Feedback Loops** | Skills capture learnings, prevent repeated issues |
| **AI-Age Velocity** | Agents operate with institutional knowledge |

---

## 🔗 Resources

- [Agent Skills Standard](https://agentskills.io) - Official framework
- [Anthropic Documentation](https://docs.anthropic.com/skills) - Technical details
- [FourKites Skills Catalog](web/index.html) - Browse all skills

---

## 👥 Team

**Creator:** MSP Raja (AI R&D Solutions Engineer)
**Executive Sponsor:** Matt Elenjickal (CEO)
**Pilot Participants:** Sales, CS, Professional Services teams

---

## 📅 Timeline

- **Phase 1 (Weeks 1-2):** Pilot validation with 3 skills
- **Phase 2 (Weeks 3-6):** Core catalog development
- **Phase 3 (Weeks 7-12):** Full rollout across organization

---

**Let's eliminate coordination tax and operate at AI-age velocity.**
