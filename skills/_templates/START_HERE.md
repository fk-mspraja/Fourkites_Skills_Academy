# START HERE

**Welcome to the RCA Skills Template System**

You've just accessed the complete system for extracting support team mental models into automated RCA skills.

This document will get you oriented in 2 minutes.

---

## What Is This?

This is a proven system for:
1. **Shadowing** support analysts (like Prashant for OTR, Surya for Ocean)
2. **Capturing** their decision-making process and knowledge
3. **Converting** that knowledge into automated diagnostic skills
4. **Deploying** those skills to help your entire support team

**Timeline**: 2 weeks from shadow session to production skill

---

## Who Are You?

### I'm a Support Analyst Being Shadowed
**You need**: [QUICK_START.md](QUICK_START.md) (10-minute read)

This explains what the process is, what to expect, and answers your questions.

### I'm Extracting Knowledge (Documentation/PM)
**You need**: [README.md](README.md) (15-minute read) + the [knowledge_extraction_template.yaml](knowledge_extraction_template.yaml)

This shows you how to conduct the 2-day shadow session and fill in the template.

### I'm Validating an Extraction (Engineering Manager)
**You need**: [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) (20-minute read)

This ensures the extraction is complete and accurate before conversion.

### I'm Converting to a Skill (Engineering Team)
**You need**: [EXTRACTION_TO_SKILL.md](EXTRACTION_TO_SKILL.md) (30-minute read)

This guides you through creating the production skill files.

### I'm Not Sure Where I Fit In
**You need**: [INDEX.md](INDEX.md) (10-minute read)

This shows you the full process and helps you find your role.

---

## Quick Timeline

```
WEEK 1-2: Extract Knowledge
├─ Day 1: Shadow analyst, observe 5-10 real tickets (4 hours)
└─ Day 2: Document and validate with analyst (4 hours)
   Output: knowledge_extraction_template.yaml (filled)

WEEK 3: Validate Quality
├─ Review extraction against checklist
├─ Fix any gaps
└─ Get SME sign-off
   Output: Validated extraction

WEEK 4-5: Convert to Skill
├─ Create skill definition files
├─ Build decision tree
├─ Organize pattern library
└─ Run tests
   Output: Production skill in skills/[domain]-rca/

WEEK 6-7: Deploy & Monitor
├─ Deploy to dev/beta
├─ Test against real cases
├─ Monitor accuracy
└─ Go to production
   Output: Live skill reducing support load
```

---

## The Files

| File | Read This If | Time |
|------|--------------|------|
| [START_HERE.md](START_HERE.md) | You just arrived | 2 min |
| [QUICK_START.md](QUICK_START.md) | You're a support analyst | 10 min |
| [README.md](README.md) | You're extracting knowledge | 15 min |
| [knowledge_extraction_template.yaml](knowledge_extraction_template.yaml) | You're ready to do the extraction | 30 min |
| [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) | You're validating an extraction | 20 min |
| [EXTRACTION_TO_SKILL.md](EXTRACTION_TO_SKILL.md) | You're converting to a skill | 30 min |
| [INDEX.md](INDEX.md) | You want the full map | 10 min |
| [SUMMARY.md](SUMMARY.md) | You want an overview | 10 min |
| [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) | You need verification it's complete | 10 min |

---

## What Problem Does This Solve?

**Before**: Support analysts manually troubleshoot every ticket. New analysts take weeks to learn. Knowledge is fragmented.

**After**: Routine issues are diagnosed automatically in seconds. Analysts handle complex cases. Knowledge is preserved and consistent.

---

## The Big Picture

```
SUPPORT ANALYST KNOWS
"Here's how I troubleshoot load not tracking..."
        ↓
KNOWLEDGE EXTRACTION
"Let me capture that systematically..."
        ↓
VALIDATED EXTRACTION
"This matches how you actually work"
        ↓
RCA SKILL CREATION
"Now we can automate this"
        ↓
PRODUCTION DEPLOYMENT
"Customers get instant answers"
        ↓
AUTOMATED RCA
"25% faster, 85%+ accurate"
```

---

## Getting Started Now

### Option 1: I Want to Learn What This Is
1. Read this file (you're doing it!)
2. Read [SUMMARY.md](SUMMARY.md) (5 minutes)
3. Read [INDEX.md](INDEX.md) (10 minutes)
4. You'll understand the system completely

### Option 2: I'm Ready to Start an Extraction
1. Read [README.md](README.md) (15 minutes)
2. Print or copy [knowledge_extraction_template.yaml](knowledge_extraction_template.yaml)
3. Schedule 2 days with a support analyst
4. Follow the README's step-by-step guide

### Option 3: I Need to Validate an Extraction
1. Read [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) (20 minutes)
2. Use the checklist against the completed extraction
3. Get SME sign-off
4. Ready for conversion

### Option 4: I'm Converting to a Skill
1. Read [EXTRACTION_TO_SKILL.md](EXTRACTION_TO_SKILL.md) (30 minutes)
2. Follow the step-by-step technical conversion process
3. Create all required files
4. Run tests
5. Deploy

---

## FAQ

**Q: How much time does this take?**
A: 8 hours total for extraction (4 shadowing + 4 documentation), then 1-2 days for conversion to a working skill.

**Q: Can I use this for my domain?**
A: Yes! The template works for any domain - OTR, Ocean, Drayage, Carrier Files, etc.

**Q: What if the analyst's process isn't "clean"?**
A: Perfect! We capture the real process, messy as it is. That's where the actual expertise is.

**Q: When can I start?**
A: Right now. Read the appropriate guide for your role and you're ready to go.

**Q: Who do I contact with questions?**
A: Each guide has a "Questions?" section with specific answers.

---

## Key Documents Quick Links

**Architecture Plan** (reference):
- `.omc/plans/rca-skills-platform-architecture.md` (Part 3.2 describes this system)

**Existing Skill Example** (reference):
- `skills/ocean_debugging/skill_definition.yaml` (what a finished skill looks like)

**This Template System** (use):
- `skills/_templates/` (all the guides and templates you need)

---

## Success Looks Like

After using this system, you'll have:

✓ **Captured Knowledge**: SME's decision process documented in machine-readable format
✓ **Validated Extraction**: All gaps filled, SME sign-off obtained
✓ **Production Skill**: Working automated diagnostic skill
✓ **Live Deployment**: Supporting your support team 24/7
✓ **Preserved Knowledge**: Even if analyst leaves, knowledge is preserved

---

## Next Step

Based on your role, go read:

- **Support Analyst?** → [QUICK_START.md](QUICK_START.md)
- **Documentation Team?** → [README.md](README.md)
- **Engineering Manager?** → [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)
- **Engineering Team?** → [EXTRACTION_TO_SKILL.md](EXTRACTION_TO_SKILL.md)
- **Not sure?** → [INDEX.md](INDEX.md)

---

**You're in the right place.**
**Welcome to the RCA Skills Platform.**

---

*Created 2026-01-26*
*Version 1.0.0*
*Status: Ready to use*
