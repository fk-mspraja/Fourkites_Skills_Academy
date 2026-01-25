# Knowledge Extraction: Quick Start Guide

**For**: Support analysts being shadowed (Prashant, Surya, etc.)
**Time**: 2 days total (4 hours/day)
**Goal**: Turn your expertise into an automated RCA skill

## What is This?

You know how to solve support issues fast. We want to capture that knowledge so we can automate it. This guide walks you through a simple 2-day process.

## Day 1: The Shadow Session (4 hours)

Someone will shadow you while you handle real support tickets. They'll be taking notes and asking questions like:

**"What are you checking right now?"**
- You: "I'm verifying the load exists in the system"
- Them: "Got it - I'll write that down"

**"Why that first?"**
- You: "Because 98% of the time, if the load doesn't exist, that's the answer"
- Them: "Makes sense - that helps me understand your thinking"

**"What if it exists?"**
- You: "Then I check the network relationship"
- Them: "And if that's missing?"
- You: "That's usually the problem - we need to create the relationship"

### What They're Documenting

They're capturing:

1. **Your workflow** - Step by step, what you check and in what order
2. **Your decision points** - If X then Y, else check Z
3. **Your tools** - Which systems you use for each step
4. **Your shortcuts** - The heuristics that make you fast
5. **Your edge cases** - The weird situations you've learned to handle

### During the Session

Just work normally. They'll:
- Watch you handle 5-10 tickets
- Ask clarifying questions
- Take screenshots and notes
- Maybe record your screen (we'll ask first)

**It's OK to say:**
- "I'm not sure about this one"
- "This is unusual"
- "Let me check with the team"
- "This sometimes fails for weird reasons"

That's valuable information too.

## Day 2: Review & Validation (4 hours)

We'll show you what we extracted and ask you to review it:

**We'll ask:**
- "Is this right?" - Yes/no/clarify
- "Did we miss anything?" - Tribal knowledge, edge cases, etc.
- "What's the confidence level?" - How certain are you at each step?
- "What assumptions are you making?" - What do you assume is always true?

**Your job:**
- Read through the extraction (takes ~30 minutes)
- Mark what's accurate and what needs fixing
- Add anything we missed
- Sign off when it's right

## The Template (High Level)

You don't need to fill it out - we do that. But here's what we're capturing:

```
WHAT WE CAPTURE:

1. Your tools and how you use them
   "You open Platform first, then call Tracking API, then check SigNoz"

2. Your workflow
   "If load doesn't exist → tell customer to verify load number
    If load exists → check network relationship
    If relationship missing → escalate to operations"

3. Your mental model
   "Always check the simplest thing first - existence
    Most issues are network-related
    ELD issues are second-most common"

4. Your confident shortcuts
   "CR England always sends reference number, not load ID"
   "First check network - solves 40% of cases immediately"

5. Your edge cases
   "Pepsi sometimes has carrierless loads (dispatcher API)"
   "Some older loads don't have proper metadata"

6. Real examples
   We'll use tickets you showed us as test cases
```

## What Happens After

Once we validate the extraction:

1. **We build a skill** - Automated RCA using your knowledge
2. **We test it** - Against the tickets you showed us
3. **You help us tune it** - "This confidence is too high" / "You forgot this edge case"
4. **It goes to production** - Helping support team 24/7

## FAQ

**Q: Will this replace me?**
A: No. This automates the easy 20% of cases. You handle the complex 80%. You'll spend less time on routine issues, more time on interesting problems.

**Q: What if I'm wrong about something?**
A: That's fine. We'll test it against real cases and fix it. This is iterative.

**Q: Why does this matter?**
A: Right now:
- New analysts take weeks to learn your mental model
- Support team is manual and slow
- Customers wait for answers
- With automation: Instant answers for routine issues, faster escalation for hard ones

**Q: How much time?**
A: 4 hours shadowing + 4 hours review. That's it. The rest is our work.

**Q: What if my process isn't "clean"?**
A: Perfect. Reality is messy. We want the real process, not a theoretical ideal.

## During the Session: Be Yourself

- Talk out loud as you work ("Now I'm checking...")
- Share your thinking ("This usually means...")
- Point out patterns ("I see this pattern a lot")
- Mention shortcuts ("Quickest way to check is...")
- Call out uncertainty ("I'm not entirely sure about this")

## After the Session: Be a Reviewer

- Review the extraction (30 minutes of reading)
- Correct any misunderstandings
- Fill in gaps
- Confirm it's accurate

That's it. We handle the rest.

## Example

Here's what a simple "Network Relationship Missing" diagnosis looks like when extracted:

```
SYMPTOM: "Load not tracking" / "Awaiting Tracking Info"

WORKFLOW:
1. Check load exists (Tracking API)
   Result: Found ✓ → Go to step 2
   Result: Not found → STOP: Load not in system

2. Check network relationship (Company API)
   Result: Exists & Active ✓ → Go to step 3
   Result: Missing → STOP: NETWORK_RELATIONSHIP_MISSING (95% confident)
   Result: Inactive → STOP: NETWORK_RELATIONSHIP_INACTIVE (90% confident)

3. Check ELD config (Company API)
   Result: Enabled ✓ → Check carrier devices
   Result: Disabled → STOP: ELD_NOT_ENABLED (92% confident)

CONFIDENCE = How certain are we?
- Load exists = 98% (almost always right)
- Network missing = 95% (very clear indicator)
- ELD disabled = 92% (pretty clear)

RESOLUTION:
- Network missing → Create relationship in Connect (human approval)
- ELD disabled → Enable ELD in Connect (human approval)
```

## Questions Before Day 1?

Ask these questions:

1. **"What will happen to my notes?"** - They become internal documentation, used to build and improve the skill
2. **"Is this confidential?"** - Yes, we keep all cases private. We only use sanitized patterns
3. **"Do I get to review before it's public?"** - Yes, completely. You sign off on the final extraction
4. **"What if I have new learnings?"** - We update the skill. This is iterative and ongoing

## Success Criteria

After 2 days, we should be able to answer:

- [ ] What's your typical 5-step workflow?
- [ ] What's step 1 and why?
- [ ] What decision points do you encounter?
- [ ] How confident are you at each point?
- [ ] What's your #1 rule of thumb?
- [ ] What edge cases break the rules?
- [ ] Which data source is most reliable?
- [ ] When do you escalate?

If we can answer all of those, the extraction is complete.

## Timeline

```
Day 1 (Monday 2-6pm):      Shadow session - you work, we observe
Day 2 (Tuesday 10am-2pm):  Review & validation - you review our notes
Post-validation:           We build the skill (your work is done)
2-3 weeks later:           Skill in production
```

## Your Benefit

- **Recognition**: Your knowledge becomes documented institutional knowledge
- **Faster team**: New analysts learn from your patterns faster
- **Less manual work**: You handle the interesting cases, not the routine ones
- **Better service**: Customers get faster answers

## Still Have Questions?

This is collaborative. We're learning FROM you, not testing you. If something doesn't make sense, ask us to clarify.

---

**Ready to go?** Let's schedule your shadow session.

**Need details?** Read the full template: `knowledge_extraction_template.yaml`
