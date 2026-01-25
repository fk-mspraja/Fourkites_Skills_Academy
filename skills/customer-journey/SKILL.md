---
name: customer-journey
description: "Standard Customer Success playbooks, charters, and engagement models. Use this skill for CS kickoffs, QBRs, success metrics, and customer engagement strategies. Solves the 'Stephen Dyke 2-hour search for CS content' problem."
version: 1.0.0
author: FourKites Customer Success Team
category: customer-success
tags: [cs, playbooks, qbr, kickoff, engagement, success-metrics]
status: pilot
---

# Customer Journey Skill

## Overview

**Problem Solved:** On Jan 5, 2026, Stephen Dyke spent 2+ hours searching for "standard CS Journey content" via Slack. Answer: "We have an old one that needs to be refreshed. Teams were changing so we stopped."

**With This Skill:** 30 seconds, self-service, always current.

This skill packages all Customer Success playbooks, charters, and engagement models into a single discoverable resource.

## Contents

### 1. CS Kickoff Framework

**Start_Your_Journey_CSOps Pitch** (Updated Feb '25)

**Purpose:**
- Communicate what CS does
- Set customer expectations
- Determine applicability to each customer
- Align on strategic objectives

**Key Components:**
- CS team introduction
- Value proposition (what we deliver)
- Engagement model (how we work together)
- Success metrics (how we measure impact)

**When to Use:**
- First engagement with new customer
- Post-implementation handoff from PS
- Account expansion kickoff
- Renewal discussions

**Template Location:** `templates/cs-kickoff-deck.pptx`

### 2. QBR (Quarterly Business Review) Framework

**Purpose:**
- Review usage and adoption metrics
- Celebrate wins and success stories
- Identify challenges and opportunities
- Align on next quarter priorities

**Standard Agenda:**
1. **Business Review** (15 min)
   - Shipment volume trends
   - Adoption by carrier/lane
   - Feature utilization

2. **Value Delivered** (15 min)
   - KPI improvements (e.g., on-time delivery %, exceptions reduced)
   - ROI demonstration
   - Customer testimonials

3. **Product Updates** (10 min)
   - Recent releases
   - Upcoming features
   - Beta opportunities

4. **Strategic Planning** (20 min)
   - Expansion opportunities
   - Integration roadmap
   - Training needs

**Template Location:** `templates/qbr-deck.pptx`

### 3. Success Metrics

**Standard KPIs by Customer Type:**

**Shipper Customers:**
- % shipments tracked
- Exception rate reduction
- On-time delivery improvement
- Time saved on manual tracking

**Carrier Customers:**
- API integration uptime
- Data submission accuracy
- Customer satisfaction scores
- Support ticket reduction

**3PL/Freight Forwarder:**
- Number of clients onboarded to FourKites
- Visibility coverage across client base
- Operational efficiency gains
- Customer retention improvement

### 4. Engagement Models

**High-Touch (Enterprise):**
- Weekly check-ins
- Monthly business reviews
- Quarterly strategic planning
- Dedicated CS manager
- 24/7 escalation path

**Tech-Touch (Mid-Market):**
- Bi-weekly check-ins
- Quarterly business reviews
- Email/Slack support
- Shared CS manager
- Business hours support

**Digital-Led (SMB):**
- Monthly automated reports
- Self-service help center
- Email support
- Pooled CS team
- Standard SLAs

### 5. Customer Health Scoring

**Red (At Risk):**
- Adoption < 50% of contracted volume
- No executive engagement in 90 days
- Open P0/P1 issues > 5 days
- Renewal at risk

**Yellow (Needs Attention):**
- Adoption 50-80%
- Executive engagement sporadic
- Open issues but manageable
- Expansion potential unclear

**Green (Healthy):**
- Adoption > 80%
- Regular executive engagement
- Proactive feature adoption
- Expansion identified

## Usage Examples

### Example 1: New Customer Kickoff

**Scenario:** PS just completed implementation for Acme Corp. CS needs to schedule kickoff.

**Query:** "What should I include in the kickoff for Acme Corp?"

**Skill Response:**
```
CS KICKOFF CHECKLIST for Acme Corp:

PREPARATION:
✓ Review implementation summary from PS
✓ Analyze first 30 days of usage data
✓ Identify key stakeholders and their roles
✓ Customize kickoff deck with Acme-specific data

AGENDA:
1. Introductions (5 min)
2. What CS Does - Value Proposition (10 min)
3. Engagement Model - How We Work Together (10 min)
4. Success Metrics - How We Measure Impact (10 min)
5. Q&A and Next Steps (5 min)

DELIVERABLES:
- Kickoff deck (template: templates/cs-kickoff-deck.pptx)
- Success metrics dashboard
- Engagement cadence (calendar invites)
- Escalation contacts

FOLLOW-UP:
- Weekly check-ins for first 90 days
- Monthly business reviews
- Quarterly strategic planning

TEMPLATE: [Link to CS Kickoff Deck]
```

### Example 2: Preparing for QBR

**Scenario:** Quarterly review coming up with Global Shipping Inc.

**Query:** "How do I prepare for Global Shipping Inc's QBR?"

**Skill Response:**
```
QBR PREPARATION for Global Shipping Inc:

DATA TO COLLECT (2 weeks before):
✓ Shipment volume trends (last 90 days)
✓ Carrier adoption rates by lane
✓ Exception rate comparison (vs previous quarter)
✓ Feature utilization metrics (ICT, Digital Workers, etc.)
✓ Support ticket summary (volume, P0/P1 count, resolution time)

SUCCESS STORIES:
✓ Identify 2-3 wins to highlight
✓ Quantify impact (e.g., "20% reduction in detention costs")
✓ Prepare customer quotes/testimonials

STRATEGIC DISCUSSION POINTS:
✓ Expansion opportunities (new carriers, lanes, features)
✓ Integration roadmap (TMS, WMS, etc.)
✓ Training needs assessment
✓ Renewal timing and terms

DECK STRUCTURE:
1. Business Review (shipment data, adoption)
2. Value Delivered (KPIs, ROI, success stories)
3. Product Updates (recent + upcoming)
4. Strategic Planning (expansion, roadmap)

TEMPLATE: [Link to QBR Deck]

ATTENDEES:
- Customer: VP Supply Chain, Director Logistics, Operations Manager
- FourKites: CS Manager, AE, Product Manager (optional)

OUTCOME:
- Renewed alignment on goals
- Expansion opportunity identified
- Action items with owners and dates
```

## Integration with Other Skills

**Related Skills:**
- `fourkites-products` - Product catalog for customer education
- `implementation-methodology` - Handoff context from PS to CS
- `troubleshooting-runbooks` - Support escalation procedures

## Success Metrics

**Problem Today:**
- Content search time: 2+ hours (Stephen Dyke example)
- Outdated templates: "We started updating but teams were changing"
- Inconsistent customer experience: No standard playbooks

**With This Skill:**
- Content search time: 30 seconds
- Always current: Version-controlled, single source of truth
- Consistent experience: Standard playbooks for all customers

## Future Enhancements

- Customer segmentation playbooks (by industry, size, etc.)
- Automated health scoring dashboards
- Customer journey analytics
- Proactive intervention triggers

---

**Status:** Pilot - Content being migrated from scattered docs
**Last Updated:** January 22, 2026
**Owner:** Customer Success Operations
**Contact:** Stephen Dyke, Anand Ravindran, Kayla Henry
