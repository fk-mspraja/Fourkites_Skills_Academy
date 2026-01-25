---
name: implementation-methodology
description: "Standard implementation framework for ICT + Digital Workforce deployments. Use this for PS engagements, customer onboarding, integration planning, and CIE processing. Solves the 'we don't have external master content' problem."
version: 1.0.0
author: FourKites Professional Services Team
category: implementation
tags: [implementation, ps, ict, digital-workers, integration, onboarding]
status: pilot
---

# Implementation Methodology Skill

## Overview

**Problem Solved:** On Jan 6, 2026, Chris Young asked: "Do you have any current external master content for Integration, Digital Workforce CIE processing?" Answer: "We don't currently, Stephen" / "unfortunately"

**With This Skill:** Standard methodology, always accessible, version-controlled.

## Standard Implementation Framework

### Phase Structure

**4-Phase Approach:**
1. **Discovery & Planning** (2-4 weeks)
2. **Configuration & Integration** (4-6 weeks)
3. **Testing & Validation** (2-3 weeks)
4. **Go-Live & Handoff** (1 week)

**Total Timeline:** 9-14 weeks (standard)

### Accelerated Implementation (Optional)

**Fast-Track:** 6-8 weeks for customers with:
- Simple carrier base (<50 carriers)
- Standard TMS integration
- No custom requirements

---

## Phase 1: Discovery & Planning

### Objectives

- Understand customer's logistics operations
- Document carrier ecosystem
- Define success metrics
- Create project plan

### Activities

#### Week 1-2: Discovery Workshops

**Workshop 1: Business Requirements**
- Attendees: Customer stakeholders (VP Supply Chain, Director Logistics, IT)
- Topics:
  - Current state assessment
  - Pain points and goals
  - Success criteria definition
  - Scope confirmation

**Workshop 2: Technical Discovery**
- Attendees: IT team, TMS admin, API developers
- Topics:
  - TMS integration requirements
  - Data mapping (fields, formats, timing)
  - Security/authentication requirements
  - Environment setup (sandbox, prod)

**Workshop 3: Carrier Mapping**
- Attendees: Logistics coordinators, carrier managers
- Topics:
  - Carrier prioritization (by volume)
  - Existing tracking methods (API, EDI, manual)
  - Contract/relationship review
  - Onboarding sequence

#### Week 3-4: Planning & Design

**Deliverables:**
- **Project Plan:** Detailed timeline with milestones
- **Integration Design Doc:** TMS connector specs, data flows
- **Carrier Onboarding Plan:** Phased rollout by carrier
- **Success Metrics Dashboard:** KPIs to track

**Review Meeting:**
- Present deliverables to customer stakeholders
- Get sign-off on approach
- Confirm resources and timing

### Exit Criteria

✓ Project plan approved by customer
✓ Integration design signed off
✓ Sandbox environment provisioned
✓ Carrier onboarding list prioritized (top 20 carriers = 80% volume)

---

## Phase 2: Configuration & Integration

### Objectives

- Build and test TMS integration
- Configure FourKites ICT platform
- Onboard priority carriers
- Enable Digital Workers

### Activities

#### Week 5-6: TMS Integration Build

**Technical Implementation:**

```python
# Example: TMS Integration Flow
1. Customer TMS sends load create event
   → FourKites API receives load data
   → Load created in FourKites system

2. FourKites queries carrier for tracking data
   → Position updates received (ELD, API, etc.)
   → Updates sent back to TMS via webhook

3. Exception detected (delay, missed appointment)
   → Alert sent to TMS
   → Workflow triggered in TMS
```

**Data Mapping:**
- Customer TMS fields → FourKites load model
- Required fields: load_number, carrier, shipper, consignee, pickup_location, delivery_location, appointment_time
- Optional fields: BOL, PO, SKUs, weight, etc.

**Testing:**
- Unit tests: Field mapping validation
- Integration tests: End-to-end load lifecycle
- Error handling: Missing data, invalid formats

#### Week 7-8: ICT Configuration

**Platform Setup:**
- User roles and permissions
- Alert configurations (email, SMS, Slack)
- Dashboard customization
- Reporting templates

**Carrier Onboarding (Top 20):**

**Per-Carrier Process:**
1. Identify tracking method (ELD, API, EDI, etc.)
2. Configure in FourKites
3. Test with sample loads
4. Validate tracking accuracy
5. Go live

**Common Tracking Methods:**
- **ELD:** Samsara, Geotab, Omnitracs, etc.
  - Configuration: Enable ELD in network relationship
  - Validation: GPS pings every 5-15 min

- **Carrier API:** FedEx, UPS, XPO, etc.
  - Configuration: API credentials, endpoint setup
  - Validation: Status milestones received

- **EDI (214):** Traditional carriers
  - Configuration: EDI translator, partner ID
  - Validation: Milestone events parsed correctly

#### Week 9-10: Digital Workers Enablement

**Worker 1: Appointment Scheduler**
- Connect to facility dock scheduling system
- Map dock doors and time slots
- Configure business rules (hours, constraints)
- Test auto-scheduling workflow

**Worker 2: Track & Trace Agent**
- Define customer notification templates
- Configure trigger rules (milestones, exceptions)
- Set up email/SMS channels
- Test notification delivery

**Worker 3: Exception Handler**
- Define exception types to auto-handle
- Configure resolution workflows
- Set escalation thresholds
- Test end-to-end scenarios

### Exit Criteria

✓ TMS integration complete and tested
✓ Top 20 carriers onboarded (80% volume covered)
✓ Digital Workers configured and tested
✓ User training completed

---

## Phase 3: Testing & Validation

### Objectives

- Validate end-to-end workflows
- Ensure data accuracy
- Confirm performance meets SLAs
- User acceptance testing (UAT)

### Activities

#### Week 11: Integration Testing

**Test Scenarios:**
1. **Load Creation:** TMS → FourKites
2. **Tracking Updates:** Carrier → FourKites → TMS
3. **Exception Handling:** Delay detected → Alert sent → Workflow triggered
4. **Reporting:** Data available in dashboards and reports

**Success Criteria:**
- 100% of test loads created successfully
- 95%+ tracking accuracy
- Alerts delivered within 5 minutes
- Zero data loss

#### Week 12: User Acceptance Testing (UAT)

**UAT Participants:** 5-10 end users (logistics coordinators, managers)

**UAT Scenarios:**
- Search for load and view tracking
- Respond to exception alert
- Generate carrier performance report
- Configure custom alert rules

**Feedback Collection:**
- Usability issues
- Feature requests
- Training gaps

**UAT Sign-Off:** Customer formally accepts system

#### Week 13: Performance Validation

**Metrics to Validate:**
- Visibility coverage: Target 95%+ of loads tracked
- Update frequency: GPS every 5-15 min, carrier API every 1-4 hours
- Alert latency: < 5 minutes from event to notification
- System uptime: 99.9% availability

### Exit Criteria

✓ All integration tests passed
✓ UAT sign-off received
✓ Performance metrics meet SLAs
✓ Training materials finalized

---

## Phase 4: Go-Live & Handoff

### Objectives

- Production cutover
- Monitor initial performance
- Handoff to Customer Success
- Retrospective and optimization

### Activities

#### Week 14: Go-Live

**Go-Live Checklist:**
- [ ] Production environment configured (mirrors sandbox)
- [ ] TMS integration switched from sandbox to prod
- [ ] All users provisioned with accounts
- [ ] Monitoring/alerting enabled
- [ ] Support escalation path confirmed

**Go-Live Execution:**
1. **T-1 day:** Final smoke tests in prod
2. **T-0 (Go-Live Day):**
   - 8 AM: Enable TMS integration
   - 9 AM: First loads begin flowing
   - Throughout day: Monitor load creation, tracking, alerts
   - 5 PM: Review metrics, address issues
3. **T+1:** Stabilization, additional monitoring

**War Room:**
- PS team, customer IT, FourKites support on standby
- Slack channel for real-time communication
- Escalation hotline for critical issues

#### Handoff to Customer Success

**Handoff Meeting:**
- Attendees: PS lead, CS manager, customer stakeholders
- Topics:
  - Implementation summary (what was built)
  - Known issues and workarounds
  - Optimization opportunities
  - Next steps (expansion, additional carriers)

**Handoff Deliverables:**
- Implementation summary doc
- Training recordings
- Configuration documentation
- Support escalation guide

#### Retrospective

**Internal Retrospective:**
- What went well?
- What could be improved?
- Lessons learned for future implementations

**Continuous Improvement:**
- Update this skill with new learnings
- Refine templates and processes
- Share best practices across PS team

### Exit Criteria

✓ Production system live and stable
✓ Handoff to CS completed
✓ Customer satisfaction survey > 4/5
✓ Retrospective completed

---

## CIE (Carrier Initiated Event) Processing

**CIE Definition:** Tracking events sent by carrier to FourKites (vs. FourKites polling carrier)

### Common CIE Types

**EDI 214:**
- Standard format for transportation status updates
- Milestones: Pickup, In-Transit, Delivery, etc.
- Processing: Parse EDI → Map to FourKites event model → Update load status

**Carrier API Webhooks:**
- Real-time push notifications from carrier
- Formats: JSON, XML
- Processing: Validate payload → Extract event data → Trigger workflows

**Email-Based Updates:**
- POD via email
- Exception notifications
- Processing: Extract attachments → OCR/parse → Update load

### CIE Processing Workflow

```
1. Carrier sends CIE (EDI, API, Email)
   ↓
2. FourKites ingestion layer receives event
   ↓
3. Validation: Format, required fields, duplicate check
   ↓
4. Enrichment: Geocode addresses, estimate ETA
   ↓
5. Update load status in FourKites
   ↓
6. Trigger downstream actions:
   - Send to TMS (if bi-directional integration)
   - Send alert (if exception)
   - Log event for analytics
```

### CIE Troubleshooting

**Common Issues:**
1. **Missing required fields:** Contact carrier to fix data format
2. **Duplicate events:** Dedupe logic (event ID, timestamp)
3. **Delayed delivery:** Check carrier API SLA, network issues
4. **Incorrect geocoding:** Validate address format, use fallback

---

## Implementation Best Practices

### Critical Success Factors

1. **Executive Sponsorship:** VP/Director-level champion
2. **Dedicated Resources:** Customer PM + IT lead assigned full-time
3. **Phased Carrier Onboarding:** Don't boil the ocean, start with top 20 carriers
4. **Change Management:** Train users early and often
5. **Continuous Communication:** Weekly status updates to stakeholders

### Common Pitfalls to Avoid

1. **Scope Creep:** Stick to agreed scope, defer "nice-to-haves" to post-launch
2. **Poor Data Quality:** Validate TMS data before integration (addresses, carrier names)
3. **Insufficient Testing:** Don't skip UAT, it catches critical issues
4. **Lack of User Buy-In:** Involve end users early, address concerns proactively
5. **Over-Customization:** Use standard configs where possible, custom only when necessary

---

## Templates & Resources

**Available Templates:**
- **Project Plan Template:** Gantt chart with standard phases
- **Integration Design Doc Template:** TMS connector specifications
- **Carrier Onboarding Tracker:** Spreadsheet for tracking carrier progress
- **UAT Test Plan Template:** Test scenarios and acceptance criteria
- **Go-Live Checklist:** Comprehensive pre-launch validation

**Location:** `/templates/implementation/`

---

## Success Metrics

**Implementation Quality:**
- On-time delivery: 90%+ implementations completed within agreed timeline
- Customer satisfaction: 4.5+/5 average rating
- Post-launch issues: < 5 critical bugs per implementation

**Business Impact:**
- Visibility coverage: 95%+ of loads tracked within 30 days
- User adoption: 80%+ of users actively using platform within 60 days
- ROI achievement: Customers achieve positive ROI within 6 months

---

**Status:** Pilot - Standardizing scattered implementation docs
**Last Updated:** January 22, 2026
**Maintained By:** Professional Services Team
**Contact:** Ali Fruland, Nick R., Andrew Buck
