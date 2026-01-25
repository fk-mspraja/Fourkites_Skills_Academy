# Prashant Session Preparation - Carrier/OTR Operations
**Date:** Tomorrow (Jan 14, 2026)
**Purpose:** Document carrier/OTR debugging workflow for POC Use Case 2
**Format:** Shadow session - watch Prashant debug real tickets

---

## Session Goals

**Primary:**
1. Document Prashant's step-by-step debugging workflow
2. Identify the 3-4 key steps he ALWAYS does
3. Map which APIs/DBs he queries at each step
4. Understand decision points ("If X, then I check Y")

**Secondary:**
5. Find pain points (what takes longest?)
6. Understand where he gets stuck (human-in-the-loop opportunities)
7. Capture SQL queries/API calls he uses
8. Learn what makes him confident he found root cause

---

## Questions to Ask

### Workflow Questions

**1. What are the typical issues you debug?**
- [ ] Load not found?
- [ ] File processing errors?
- [ ] ETA calculation wrong?
- [ ] Carrier API failures?
- [ ] Other: _______

**2. When you get a ticket, what's your FIRST step?**
- Which tool do you open first?
- What do you look at?
- Why start there?

**3. Walk me through your last 3 tickets:**
- What was the issue?
- What steps did you take?
- How long did it take?
- What was root cause?

**4. What's your mental checklist?**
- "I ALWAYS check X, then Y, then Z"
- Can you draw a flowchart?

**5. Where do you get stuck?**
- What makes you say "I need help"?
- When do you escalate?
- When do you give up?

---

### Technical Questions

**6. Which systems do you use?**
- [ ] Platform UI
- [ ] Redshift
- [ ] SigNoz logs
- [ ] Trino (SPOG)
- [ ] APIs (which ones?)
- [ ] S3
- [ ] Confluence
- [ ] Custom tools
- [ ] Other: _______

**7. Show me your most-used SQL queries:**
- Can you share the top 5 queries you run?
- Which tables do you query most?
- Any joins you always do?

**8. Show me your Postman collections:**
- Which APIs do you call?
- What endpoints?
- What auth do they use?

**9. Any custom scripts or tools you built?**
- Like Surya's EDI parser
- Automation scripts?
- Helper tools?

**10. What's in Confluence that you reference?**
- Carrier list?
- Troubleshooting guides?
- SQL templates?
- Is it up to date?

---

### Decision Tree Questions

**11. "If I see X, I know to check Y next":**

Example:
- If carrier file count is zero → I check carrier API status
- If carrier API is working → I check file format
- If file format is correct → I check processing logs

**Your examples:**
- If _______ → I check _______
- If _______ → I check _______
- If _______ → I check _______

**12. How do you know you found root cause?**
- What evidence confirms it?
- Do you verify with multiple sources?
- What's your confidence threshold?

**13. What makes you decide to escalate?**
- Engineering issue vs carrier issue vs bug?
- Who do you escalate to?
- What info do you include in escalation?

---

### Pain Point Questions

**14. What takes the MOST time?**
- Data gathering?
- Waiting for API responses?
- Analyzing logs?
- Correlating findings?

**15. What's the most frustrating part?**
- Tool switching?
- Slow queries?
- Missing data?
- Unclear error messages?

**16. If you could automate ONE thing, what would it be?**
- Why that one?
- How much time would it save?

**17. What would make your job easier?**
- Better tools?
- Better documentation?
- Faster access to data?
- AI suggestions?

---

### Adoption/Usage Questions

**18. Do you know about the previous RCA bot?**
- Did you try it?
- Why didn't you keep using it?
- What was wrong with it?

**19. Would you use an AI agent to help debug?**
- What would make you trust it?
- What would make you NOT trust it?
- What's the bare minimum for you to try it?

**20. How do you want it to work?**
- Show all queries it runs?
- Let you override decisions?
- Integrate with Salesforce?
- Command-line or web UI?

---

## What to Observe (Shadow Session)

### Timing Each Step
Use stopwatch, record:
- [ ] 0:00 - Start: Read ticket
- [ ] _:__ - Open first tool
- [ ] _:__ - First query complete
- [ ] _:__ - Switch to second tool
- [ ] _:__ - Second query complete
- [ ] _:__ - Switch to third tool
- [ ] _:__ - Analysis phase starts
- [ ] _:__ - Decision made
- [ ] _:__ - Total time: _____

### Tool Switching
Count how many times he switches between:
- Salesforce
- Browser tabs
- Terminal/SQL client
- Postman
- Confluence
- Other

**Each switch = context switch = time lost**

### Copy-Paste Operations
Note when he:
- Copies data from one tool
- Pastes into another
- Formats data manually
- Correlates findings manually

**These are automation opportunities**

### Queries and API Calls
**Record EXACTLY:**
```sql
-- Example: First query he runs
SELECT ...
FROM ...
WHERE ...
```

```bash
# Example: API call
curl -X GET https://api.example.com/... \
  -H "Authorization: ..."
```

### Mental Model
Note when he says:
- "I'm checking X because..."
- "This tells me..."
- "Now I know..."
- "Next I need to verify..."

**These reveal his decision logic**

---

## What to Capture in Documentation

### 1. Issue Type Definition
```yaml
issue_type:
  name: "[from Prashant]"
  description: "[from Prashant]"
  frequency: "% of tickets"
  typical_time: "minutes"
```

### 2. Step-by-Step Workflow
```yaml
steps:
  step_1:
    name: "[from Prashant]"
    description: "[from Prashant]"
    tool: "[from observation]"
    query: "[copy exact SQL/API call]"
    expected_time: "[from timing]"

  step_2:
    name: "[from Prashant]"
    # ...
```

### 3. Decision Points
```yaml
decision_points:
  after_step_1:
    if: "[condition]"
    then: "go to step_2"
    else: "go to step_3"
    confidence: "[how sure is he?]"
```

### 4. Pain Points
```yaml
pain_points:
  - step: "[which step]"
    issue: "[what's painful]"
    time_lost: "[minutes]"
    automation_potential: "high/medium/low"
```

### 5. Success Criteria
```yaml
success_criteria:
  root_cause_found:
    evidence_required:
      - "[what evidence]"
      - "[what evidence]"
    confidence: "[how confident]"
```

---

## Questions About Integration

**21. How do you currently access:**
- Redshift? (SQL client? Which one?)
- SigNoz? (Web UI? API?)
- Carrier APIs? (Postman? cURL? Other?)

**22. Authentication:**
- Personal credentials or shared?
- Stored where?
- Rotated how often?

**23. Salesforce:**
- Do you update tickets manually?
- Copy-paste findings?
- Use any automation?

---

## Output from Session

**Create these documents:**

1. **`skills/carrier_otr_operations/skill_definition.yaml`**
   - Based on template from SKILLS_FRAMEWORK.md
   - Filled with Prashant's workflow

2. **`skills/carrier_otr_operations/decision_tree.yaml`**
   - Step-by-step investigation flow
   - Decision points and conditions

3. **`skills/carrier_otr_operations/api_mappings.yaml`**
   - Which queries at which steps
   - Exact SQL/API calls

4. **`skills/carrier_otr_operations/knowledge_base.md`**
   - Tribal knowledge
   - Common patterns
   - Known issues

5. **`PRASHANT_SESSION_NOTES.md`**
   - Raw notes from session
   - Timing data
   - Pain points
   - Quotes

---

## Session Format

### Part 1: Interview (15 minutes)
- Ask questions 1-20
- Get high-level understanding
- Map mental model

### Part 2: Live Debugging (30-45 minutes)
- Prashant debugs 2-3 real tickets
- You observe and time each step
- Record queries and decisions
- Ask clarifying questions

### Part 3: Review (15 minutes)
- Confirm understanding
- "Is this your workflow?"
- "Did I capture it correctly?"
- Get his feedback on what agent should do

---

## Key Success Criteria for Tomorrow

**You'll know session was successful if you can answer:**

1. ✅ What's Prashant's step 1, 2, 3 for typical issue?
2. ✅ What SQL queries does he run at each step?
3. ✅ What decision logic does he use?
4. ✅ Where does he get stuck / need help?
5. ✅ Would he use an agent? What would it need to do?

**If you can't answer these → schedule follow-up**

---

## Red Flags to Watch For

**🚩 If Prashant says:**
- "Every ticket is different, there's no pattern" → Dig deeper, there IS a pattern
- "I just know from experience" → That's the pattern, make it explicit
- "It depends" → On what? That's your decision logic
- "This rarely happens" → Then don't build for it in POC

**🚩 If workflow is:**
- >10 steps → Too complex for POC, pick subset
- Highly manual → Good! Automation opportunity
- Requires intuition → Human-in-the-loop opportunity
- Escalates often → May not be automatable

---

## After Session: Validation

**Before building anything, validate with Prashant:**

1. Show him the decision tree you documented
2. Ask: "Is this your process?"
3. Test: Give him a hypothetical ticket, see if he follows the tree
4. Iterate until he says "Yes, that's exactly it"

**Then you can build with confidence**

---

## Equipment Needed

- [ ] Laptop with note-taking app
- [ ] Screen recording permission (if allowed)
- [ ] Stopwatch/timer
- [ ] Access to same tools Prashant uses (request access if needed)
- [ ] This preparation doc printed/open

---

## Follow-Up After Session

**Immediately after:**
1. Write up raw notes while fresh
2. Create skill definition YAML
3. Sketch decision tree
4. List open questions
5. Share with Prashant for review

**Within 24 hours:**
1. Complete all documentation
2. Share with Arpit for feedback
3. Identify which use case to build first (Surya's or Prashant's)
4. Start building router + selected skill

---

**Status:** ✅ Prepared for Prashant session
**Next:** Attend session tomorrow, take detailed notes
**Owner:** MSP Raja
**Last Updated:** 2026-01-13
