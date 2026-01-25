# Skills Router - Quick Start Guide

**5-Minute Integration Guide**

---

## 1. Import the Router

```python
from building_blocks.skills_router import SkillsRouter

router = SkillsRouter()
```

---

## 2. Route a Ticket

```python
decision = router.route({
    "description": "Load U123 not tracking",
    "mode": "ground",           # Optional
    "shipper": "walmart",        # Optional
    "carrier": "crst-logistics"  # Optional
})
```

---

## 3. Check the Decision

```python
print(f"Skill: {decision.skill_id}")          # "otr-rca"
print(f"Confidence: {decision.confidence}")   # 0.85
print(f"Level: {decision.confidence_level}")  # "HIGH"
```

---

## 4. Auto-Route or Review

```python
if decision.should_auto_route():
    # High confidence (≥85%) - execute automatically
    skill = router.get_skill(decision.skill_id)
    result = skill.investigate(context)
else:
    # Low confidence (<85%) - send to human review
    escalate_to_human(context)
```

---

## 5. Register Your Skills (Optional)

```python
from skills.otr_rca import OTRRCASkill

router.register_skill("otr-rca", OTRRCASkill())
router.register_skill("ocean-tracking", OceanTrackingSkill())

# Now you can retrieve skills
skill = router.get_skill("otr-rca")
```

---

## Common Patterns

### Validate Input

```python
is_valid, error = router.validate_context(context)
if not is_valid:
    return f"Error: {error}"
```

### Get Explanation

```python
explanation = router.explain_routing(context)
print(explanation)
# Shows full classification chain
```

### Handle Unknown Routes

```python
decision = router.route(context)

if decision.skill_id == "unknown":
    print(f"Could not route: {decision.reasoning}")
    escalate_to_human(context)
```

---

## Context Format

**Required:**
- `description` (str) - Problem description

**Optional:**
- `mode` (str) - "ground", "ocean", "air", "drayage"
- `load_number` (str)
- `shipper` (str)
- `carrier` (str)

---

## Confidence Thresholds

| Level | Range | Action |
|-------|-------|--------|
| HIGH | ≥85% | Auto-route |
| MEDIUM | 60-84% | Review recommended |
| LOW | <60% | Human required |

---

## Skill IDs

| Skill ID | Domain | Use Case |
|----------|--------|----------|
| `otr-rca` | Ground | OTR tracking issues |
| `ocean-tracking` | Ocean | Container tracking |
| `drayage-rca` | Drayage | Drayage operations |
| `air-tracking` | Air | Air freight |
| `unknown` | N/A | Could not classify |

---

## Testing

```bash
# Run built-in tests
python building_blocks/skills_router.py

# Quick validation
python -c "
from building_blocks.skills_router import SkillsRouter
router = SkillsRouter()
decision = router.route({'description': 'Load not tracking'})
print(f'Routed to: {decision.skill_id}')
"
```

---

## Full Documentation

- **README:** `building_blocks/SKILLS_ROUTER_README.md`
- **Implementation:** `building_blocks/IMPLEMENTATION_SUMMARY.md`
- **Source:** `building_blocks/skills_router.py`

---

## Need Help?

1. Check pattern matching: `decision.matched_patterns`
2. Review reasoning: `decision.reasoning`
3. Get explanation: `router.explain_routing(context)`
4. See examples in README

---

**That's it!** You're ready to route support tickets.
