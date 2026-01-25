# What is a Skill? (Skills ≠ Prompts)

## TL;DR for Matt

**Skills are NOT prompts.** They're structured intelligence packages containing **logic + data + procedures + context** that create compounding organizational learning.

Think of it this way:
- **Prompt:** "Ask AI to analyze why this lane is delayed"
- **Skill:** Encoded logic that knows how to detect delays, query carrier patterns, assess ETA drift, and generate actionable outreach—the same way every time

---

## The Core Difference

### ❌ What Skills Are NOT (Just Prompts)

**Prompts are text instructions:**
```
"Analyze this FedEx tracking issue and tell me why the ETA keeps slipping"
```

**Problem:**
- 10 people ask → 10 different AI responses
- Each person restarts from zero
- No consistency, no compounding
- Nothing becomes institutional knowledge

### ✅ What Skills ARE (Structured Intelligence)

**Skills are executable knowledge packages:**

```yaml
# skills/fedex-tracking-workflow/SKILL.md

name: fedex-tracking-workflow
description: "Diagnose FedEx tracking gaps, ETA drift, timestamp issues"
owner: stephen.dyke@fourkites.com

## INPUTS (Data Required)
- load_data: load_number, carrier, pickup_time, delivery_appt
- eta_signals: current_eta, original_eta, eta_drift
- stop_history: timestamps, locations, gaps
- carrier_patterns: reliability_score, avg_delay, common_issues

## LOGIC (What to Do)
1. DETECT missing timestamps
   → Check stop_history for gaps > 2 hours
   → Compare against expected check-in frequency

2. CHECK ETA drift
   → current_eta - original_eta
   → Compare vs delivery appointment window
   → Calculate risk score (0-100)

3. ASSESS carrier reliability
   → Query carrier_patterns database
   → Historical on-time %
   → Pattern: Does this carrier always run late on this lane?

4. GENERATE outreach
   → If drift > 2hrs AND appointment at risk: HIGH priority
   → If timestamps missing > 4hrs: Send carrier query
   → If carrier risk score > 70: Escalate to manager

## OUTPUTS (What You Get)
action: "Contact carrier - HIGH priority"
reason: "ETA drift 4hrs, missing 3 timestamps, carrier risk score 72"
template: "FedEx delay outreach v2.1"
next_steps:
  - Send carrier query using template
  - Alert customer with revised ETA
  - Monitor position updates every 30min
  - Escalate if no response in 2hrs
```

**Result:**
- 1 skill created once
- ∞ teams use it (PS, CS, Support, Ops)
- 100% consistency
- Gets better over time as we refine the logic

---

## How This Solves Stephen's Problem

### Today (Without Skills)

**Stephen's FedEx/BRP workflow pain:**

Each team (PS, CS, Support, Ops) diagnoses tracking gaps their own way:
- Some check timestamps first, others check ETA
- Different people query different data sources
- No standard process for carrier outreach
- Everyone has their own templates
- **Nothing compounds across the org**

**Impact:**
- Same analysis repeated 10+ times per week
- Inconsistent customer communication
- New hires take weeks to learn "the Stephen way"
- When Stephen leaves, knowledge walks out the door

### With Skills

**One skill encodes Stephen's best process:**

```
fedex-tracking-workflow skill contains:
→ Exact data to check (load_data, eta_signals, stop_history)
→ Decision tree logic (timestamp gap > 2hrs? ETA drift > threshold?)
→ Carrier reliability patterns from historical data
→ Standard outreach templates by issue type
→ Escalation rules (when to involve manager)
```

**Now:**
- PS, CS, Support, Ops all use the same logic
- AI agents execute the workflow automatically
- New hires productive in days (just use the skill)
- Stephen's expertise becomes institutional knowledge
- **Every use makes the org smarter (we refine the skill based on feedback)**

---

## The Definition You Outlined

From our conversation, you said:

> "Define the end-to-end process—by process I mean specifically AI-assisted process—and define standard prompts that teams can use to create materials, making sure prompts are designed to take on the knowledge from previous teams' work."

**Skills are the implementation of that vision:**

### 1. "End-to-End AI-Assisted Process"

Skills encode the full workflow:
```
INPUT → LOGIC → OUTPUT
(What data)  (How to analyze)  (What action)
```

Example: FedEx tracking skill
- **INPUT:** Load data, ETA, timestamps, carrier history
- **LOGIC:** Detect gaps, assess risk, generate outreach
- **OUTPUT:** Recommended action with reasoning + template

### 2. "Standard Prompts Taking on Previous Work"

Skills ARE standardized prompts + logic + data:
```
Instead of: "Figure out why FedEx is late" (vague, no context)

We have: A skill that knows:
  → Check these 4 data sources in this order
  → Apply these 6 decision rules
  → Use template v2.1 for this issue type
  → Historical pattern: FedEx lane X is always 3hrs late on Fridays
```

The skill "takes on previous work" because:
- It captures what worked before
- It improves based on new learnings
- Version 1.0 → 1.1 → 2.0 as we get smarter

### 3. "Knowledge Compounds"

**Without Skills (Prompts Only):**
```
Week 1: Person A asks AI about lane delays → Gets answer A
Week 2: Person B asks same question → Gets different answer B
Week 3: Person C asks again → Gets answer C
→ No compounding. Everyone restarts from zero.
```

**With Skills:**
```
Week 1: Create lane-delay-analysis skill based on best process
Week 2: Person B uses skill → Gets consistent result
Week 3: Person C uses skill → Gets same reliable answer
Week 10: Skill updated with new patterns (now version 1.1)
Week 20: Everyone benefits from accumulated improvements
→ Compounding intelligence. Org gets sharper over time.
```

---

## Real-World Analogy

### Prompts = Asking Directions

"Hey, how do I get to the airport?"
- You get an answer
- Next person asks → Gets different route
- Nothing is saved
- Everyone restarts from scratch

### Skills = GPS Navigation

- Knows the routes (logic)
- Has real-time traffic data (data)
- Suggests optimal path (procedure)
- Learns from millions of trips (compounding)
- Same reliable navigation for everyone
- Gets better over time with new data

---

## How to Create a Skill (4 Steps)

### Step 1: Identify Repeated Work

**Look for:**
- Same questions asked repeatedly ("Why is this lane delayed?")
- Common troubleshooting ("Load not tracking")
- Manual analysis that could be automated
- Tribal knowledge ("Ask Sarah, she knows how")

**Examples at FourKites:**
- Stephen's FedEx workflow
- "How do I run a QBR?"
- "What's our implementation process?"
- "Why is load not tracking?" (85+ patterns)

### Step 2: Document the Best Process

**Work with domain expert to capture:**

| Component | Questions to Ask |
|-----------|------------------|
| **Inputs** | What data do you look at first? |
| **Logic** | How do you diagnose the issue? |
| **Rules** | What thresholds trigger different actions? |
| **Outputs** | What actions do you recommend? |
| **Edge Cases** | What are the tricky scenarios? |

**Example Session with Stephen:**
```
Q: "When FedEx load shows late ETA, what do you check first?"
A: "I look at stop history for missing timestamps, then compare
    current ETA vs appointment window."

Q: "What's your threshold for escalation?"
A: "If ETA drift is more than 2 hours AND we're within 6 hours
    of delivery appointment, I escalate immediately."

Q: "Do different lanes have different patterns?"
A: "Yes, Lane SF→LA with FedEx is always 3hrs late on Fridays
    due to Bay Bridge traffic. I factor that in."
```

### Step 3: Structure as Skill

**Package into skill format:**

```yaml
# skills/fedex-tracking-workflow/SKILL.md

name: fedex-tracking-workflow
version: 1.0.0
owner: stephen.dyke@fourkites.com
description: "Diagnose FedEx tracking issues: gaps, ETA drift, carrier patterns"

## Inputs
- load_data (Tracking API)
- eta_signals (ETA service)
- stop_history (position updates)
- carrier_patterns (analytics DB)

## Logic
1. Missing timestamps
   IF gap > 2hrs THEN flag as MISSING_DATA

2. ETA drift assessment
   drift = current_eta - original_eta
   IF drift > 2hrs AND time_to_appt < 6hrs THEN priority = HIGH

3. Carrier pattern matching
   IF lane = "SF→LA" AND carrier = "FedEx" AND day = "Friday"
   THEN expected_delay = 3hrs (known pattern)

4. Outreach generation
   BASED ON priority level:
     HIGH → Template "FedEx urgent delay v2.1"
     MEDIUM → Template "FedEx standard follow-up v1.3"
     LOW → Automated monitoring only

## Outputs
- action: "Contact carrier" | "Alert customer" | "Monitor"
- priority: HIGH | MEDIUM | LOW
- reason: Detailed explanation with data points
- template: Which communication template to use
- next_steps: Checklist of follow-up actions

## Success Metrics
- Accuracy: 95%+ correct diagnosis
- Time savings: 15min → 2min per case
- Consistency: 100% same logic every time
```

### Step 4: Deploy & Improve

**Make Available:**
- Add to Skills Academy catalog
- Enable for AI agents (Claude, RCA bot, etc.)
- Train teams on usage
- Monitor adoption metrics

**Continuous Improvement:**
```
Version 1.0: Initial skill based on Stephen's process
  ↓
Week 4: Sarah finds edge case (weekend delays different)
  ↓
Version 1.1: Add weekend pattern logic
  ↓
Month 3: Data shows new FedEx pattern on holiday weeks
  ↓
Version 2.0: Enhanced with holiday pattern detection
```

**Everyone benefits from improvements automatically.**

---

## Why This Creates a Moat

### Competitive Advantage

**Other companies:**
- Scattered knowledge
- Each person reinvents the wheel
- No compounding learning
- Slow to improve

**FourKites with Skills Academy:**
- Centralized expertise in skills
- Everyone uses best practices instantly
- Learning compounds across org
- Gets faster and smarter every day

**Example:**
```
Project44 analyst: Spends 20min analyzing FedEx delay (every time)
FourKites analyst: Uses skill, gets answer in 2min

Over 1 year:
- Project44: Same 20min per case (250 cases = 83 hours)
- FourKites: 2min per case (250 cases = 8 hours)

FourKites saves: 75 hours per analyst per year
With 100 analysts: 7,500 hours saved = $450K value
```

**Plus:** FourKites keeps getting faster. Project44 stays the same.

---

## Summary: Skills vs Prompts

| Aspect | Prompts | Skills |
|--------|---------|--------|
| **What it is** | Text instructions | Structured logic + data + procedures |
| **Consistency** | Different every time | Same reliable pattern |
| **Compounding** | No (restart each time) | Yes (improves over time) |
| **Organizational Learning** | None | Becomes institutional knowledge |
| **AI Integration** | Unreliable results | Precise, context-aware execution |
| **Maintenance** | N/A (ephemeral) | Version-controlled, owned |
| **Example** | "Why is lane delayed?" | FedEx tracking workflow skill |

---

## Next Steps

1. **Pilot Skills (Already Built):**
   - `rca-support-agent` - 60% L1 automation
   - `customer-journey` - Solves Stephen's CS content search
   - `implementation-methodology` - Standard PS framework

2. **High-Impact Skills to Build Next:**
   - `fedex-tracking-workflow` (Stephen's pain point)
   - `carrier-delay-analysis` (lane-specific patterns)
   - `qbr-preparation` (CS playbook)

3. **Measurement:**
   - Time reduction: 95% target
   - Consistency: 100% same logic
   - Adoption: 10 users in pilot
   - Improvement: Skills updated based on feedback

---

**Skills are how we turn "scattered usage into compounding intelligence across the org."**

— MSP Raja
January 22, 2026
