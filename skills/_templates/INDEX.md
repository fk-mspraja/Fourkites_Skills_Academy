# RCA Skills Templates Index

**Location**: `/Users/msp.raja/rca-agent-project/skills/_templates/`

This directory contains the complete system for extracting support team mental models and converting them into automated RCA skills.

---

## Quick Navigation

### I'm a Support Analyst (SME)
Start here: [QUICK_START.md](QUICK_START.md)

This is your guide for the 2-day knowledge extraction process. You'll learn:
- What happens during the shadow session
- How to prepare
- What the extraction process involves
- What happens after

**Time commitment**: 8 hours total (4 hours shadowing + 4 hours review)

### I'm Extracting Knowledge (Documentation Team)
Start here: [README.md](README.md) then use [knowledge_extraction_template.yaml](knowledge_extraction_template.yaml)

This shows you how to:
- Plan the shadow session
- Use the extraction template
- Fill in each section
- Validate with the SME

**Time commitment**: 8 hours per domain (4 hours observation + 4 hours documentation)

**Output**: Completed `knowledge_extraction_template.yaml`

### I'm Validating an Extraction (Engineering Manager)
Start here: [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)

This ensures the extraction is complete and accurate:
- Completeness verification
- Accuracy validation
- Test case verification
- SME sign-off
- Readiness assessment

**Time commitment**: 4-8 hours per extraction

**Input**: Completed `knowledge_extraction_template.yaml`
**Output**: Signed-off, ready-to-convert extraction

### I'm Converting to a Skill (Engineering Team)
Start here: [EXTRACTION_TO_SKILL.md](EXTRACTION_TO_SKILL.md)

This guide walks through the technical conversion:
- Creating `skill_definition.yaml`
- Building `decision_tree.yaml`
- Generating pattern library
- Writing test cases
- Validation and deployment

**Time commitment**: 1-2 days per skill

**Input**: Validated `knowledge_extraction_template.yaml`
**Output**: Production-ready skill in `skills/[domain]-rca/`

---

## Files in This Directory

### Core Template

**`knowledge_extraction_template.yaml`**
- **Purpose**: Primary template for capturing SME mental models
- **Size**: ~800 lines with helpful comments
- **Used by**: Documentation teams during shadow sessions
- **Output**: Filled with analyst's knowledge during 2-day process
- **Format**: Structured YAML with 12 major sections
- **Key sections**:
  1. Observation Session - what you saw
  2. Mental Model - how they think
  3. Data Sources - systems they query
  4. Patterns - issue types they handle
  5. Decision Tree - machine-readable flowchart
  6. Test Cases - real examples
  7. Edge Cases - weird situations
  8. Metrics - performance baselines
  9. Dependencies - what they need
  10. Knowledge Sources - where they learned
  11. Assumptions - what they assume
  12. Next Steps - validation plan

### Supporting Guides

**`README.md`**
- Complete guide for using the extraction template
- How to conduct shadow sessions
- Explanation of each template section
- Tips for success
- Common mistakes to avoid
- Conversion process overview

**`QUICK_START.md`**
- Written for support analysts (SMEs)
- Friendly, non-technical language
- What to expect during shadow session
- What happens after
- FAQ for common concerns
- Example of extracted knowledge

**`VALIDATION_CHECKLIST.md`**
- Comprehensive checklist for validating extractions
- 11 sections covering all aspects
- Pass/fail criteria for each check
- Sign-off template
- Issue tracking (blocker/important/nice-to-have)
- Post-validation next steps

**`EXTRACTION_TO_SKILL.md`**
- Technical guide for converting extraction to skill
- Step-by-step instructions
- YAML templates for each output file
- How to structure pattern library
- Test running and validation
- Deployment checklist
- Common issues and solutions
- Reference implementation code

**`INDEX.md`** (this file)
- Navigation guide for all templates
- Quick reference for different roles
- Timeline summary
- File descriptions

---

## The Full Workflow

```
WEEK 1-2: Knowledge Extraction
├── Day 1: Shadow Session (4 hours)
│   ├── Watch analyst handle 5-10 real tickets
│   ├── Fill sections 1-4 of extraction template
│   └── Document tools, decisions, data sources
│
├── Day 2: Documentation (4 hours)
│   ├── Fill sections 5-12 of extraction template
│   ├── Create decision tree flowchart
│   ├── Add test cases from observed tickets
│   └── Validate with SME
│
└── Result: knowledge_extraction_template.yaml (completed)

WEEK 3: Validation
├── Completeness review
├── Accuracy verification
├── Test case validation
├── Data source testing
├── SME sign-off
└── Result: Signed-off extraction ready for conversion

WEEK 4-5: Skill Conversion
├── Create skill_definition.yaml
├── Create decision_tree.yaml
├── Generate pattern library (patterns/*.yaml)
├── Create API mappings
├── Write test cases
├── Create documentation
├── Validate all components
└── Result: Production-ready skill in skills/[domain]-rca/

WEEK 6-7: Testing & Deployment
├── Dev environment testing
├── Run against historical cases
├── Beta deployment
├── Monitor accuracy
├── Gather feedback
├── Fine-tune confidence thresholds
└── Production deployment
```

---

## Timeline Summary

| Phase | Who | Time | Output |
|-------|-----|------|--------|
| **Extraction** | SME + Doc Team | 8 hours | knowledge_extraction_template.yaml |
| **Validation** | Engineering Lead | 4-8 hours | Validated extraction |
| **Conversion** | Engineering Team | 1-2 days | Production skill files |
| **Testing** | QA + SME | 1-2 weeks | Deployed skill |
| **Maintenance** | Engineering Team | Ongoing | Updated patterns/extraction |

**Total per domain**: 2-3 weeks from shadow session to production

---

## Key Documents by Phase

### Phase 1: Extraction (Day 1-2)
- **Read**: `README.md` (planning) + `QUICK_START.md` (for SME)
- **Use**: `knowledge_extraction_template.yaml` (during session and afterwards)
- **Output**: Completed template with all 12 sections filled

### Phase 2: Validation (Day 3-5)
- **Use**: `VALIDATION_CHECKLIST.md`
- **Verify**: All checks pass, SME signs off
- **Output**: Validated extraction ready to convert

### Phase 3: Conversion (Day 6-8)
- **Read**: `EXTRACTION_TO_SKILL.md`
- **Create**: skill_definition.yaml, decision_tree.yaml, patterns/*, test_cases/*
- **Validate**: Test runner passes, all references correct
- **Output**: Production-ready skill directory

### Phase 4: Testing (Week 2)
- **Test**: Against 30-50 historical cases
- **Deploy**: Dev → Beta → Production
- **Monitor**: Accuracy metrics, false positives/negatives
- **Output**: Live skill with monitoring

---

## Template Sections Map

How the extraction template sections map to skill outputs:

| Extraction Section | Skill Output Files | Purpose |
|---|---|---|
| 1. Observation Session | README.md | Document how skill was built |
| 2. Mental Model | decision_tree.yaml | Flowchart of thinking process |
| 3. Data Sources | skill_definition.yaml | API/system configuration |
| 4. Patterns | patterns/*.yaml | Pattern library with detection |
| 5. Decision Tree | decision_tree.yaml | Machine-readable flowchart |
| 6. Test Cases | test_cases/*.yaml | Validation test suite |
| 7. Edge Cases | decision_tree.yaml | Branching and escalation paths |
| 8. Metrics | skill_definition.yaml | Performance targets |
| 9. Dependencies | decision_tree.yaml | Escalation and handoff triggers |
| 10. Knowledge Sources | README.md | References and documentation |
| 11. Assumptions | README.md | Limitations section |
| 12. Next Steps | VALIDATION_CHECKLIST.md | Conversion steps |

---

## Template Statistics

| File | Size | Sections | Purpose |
|------|------|----------|---------|
| knowledge_extraction_template.yaml | ~800 lines | 12 | Primary extraction template |
| README.md | ~400 lines | 8 | Guide for extraction process |
| QUICK_START.md | ~250 lines | 8 | Quick guide for SMEs |
| VALIDATION_CHECKLIST.md | ~500 lines | 11 | Validation framework |
| EXTRACTION_TO_SKILL.md | ~600 lines | 9 | Technical conversion guide |
| INDEX.md | ~300 lines | 6 | Navigation guide (this file) |

**Total**: ~2,850 lines of documentation and templates

---

## Usage Examples

### Example 1: OTR "Load Not Tracking" Skill

**Timeline**: 2 weeks
**SME**: Prashant (OTR Support Lead)
**Pattern Count**: 25+ patterns
**Test Cases**: 8 real examples
**Result**: Handles 25% of support tickets automatically

**Files created**:
- `skills/otr-rca/skill_definition.yaml`
- `skills/otr-rca/decision_tree.yaml`
- `skills/otr-rca/patterns/` (25+ files)
- `skills/otr-rca/test_cases/` (8+ files)
- `skills/otr-rca/knowledge_base/prashant_workflow.yaml`

### Example 2: OCEAN Shipment Debugging Skill

**Timeline**: 2 weeks
**SME**: Surya (ISBO Analyst)
**Pattern Count**: 35+ patterns
**Test Cases**: 10 real examples
**Result**: Handles 35% of ocean tracking issues automatically

**Files created**:
- `skills/ocean-rca/skill_definition.yaml`
- `skills/ocean-rca/decision_tree.yaml`
- `skills/ocean-rca/patterns/` (35+ files)
- `skills/ocean-rca/test_cases/` (10+ files)
- `skills/ocean-rca/knowledge_base/surya_workflow.yaml`

---

## Getting Started

### For a New Extraction

1. **Schedule with SME**
   - Pick 2 consecutive days
   - Block 4 hours each day
   - Set up screen recording if possible
   - Prepare 5-10 real support tickets to analyze

2. **Read the guides**
   - SME reads `QUICK_START.md`
   - Documentation team reads `README.md`
   - Both review `knowledge_extraction_template.yaml`

3. **Day 1: Shadow Session**
   - Observe analyst work
   - Fill sections 1-4 of template
   - Take detailed notes

4. **Day 2: Documentation**
   - Write sections 5-12 of template
   - Create decision tree flowchart
   - Add test cases
   - Review with SME

5. **Validation**
   - Use `VALIDATION_CHECKLIST.md`
   - Get SME sign-off
   - Fix any gaps or errors

6. **Conversion**
   - Follow `EXTRACTION_TO_SKILL.md`
   - Create skill files
   - Run test cases
   - Deploy to production

---

## FAQ

**Q: How long does extraction take?**
A: 8 hours total (4 hours observation + 4 hours documentation)

**Q: Can I extract multiple analysts for the same domain?**
A: Yes! Document each analyst's approach separately, then merge into a skill that represents both perspectives.

**Q: What if the analyst doesn't follow a clear process?**
A: That's OK. Document the actual process, messy as it is. Real expertise is often intuitive. We'll work with the analyst to extract the rules they follow instinctively.

**Q: How do I validate confidence scores?**
A: Run test cases. If actual results don't match expected confidence, re-calibrate.

**Q: What happens to tribal knowledge?**
A: It becomes documented! We extract it into Section 7, which becomes part of the decision tree and patterns.

**Q: How often should we update the extraction?**
A: Annually, or when the analyst's approach changes significantly.

---

## Contact & Support

**Questions about extraction?** Read `README.md` and `QUICK_START.md`

**Questions about validation?** Read `VALIDATION_CHECKLIST.md`

**Questions about conversion?** Read `EXTRACTION_TO_SKILL.md`

**Questions about process?** See `.omc/plans/rca-skills-platform-architecture.md` Part 3

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-26 | Initial template and guides created |

---

## Next Steps

1. Schedule first extraction with an SME
2. Copy `knowledge_extraction_template.yaml` to start the process
3. Follow the timeline in `README.md`
4. Use `VALIDATION_CHECKLIST.md` to ensure quality
5. Convert to skill using `EXTRACTION_TO_SKILL.md`

**Goal**: Build 10-12 domain-specific skills covering the full range of support issues.

---

**Last Updated**: 2026-01-26
**Template Framework Version**: 1.0.0
**Purpose**: Guide knowledge extraction for RCA skills platform
