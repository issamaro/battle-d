# Battle-D Documentation Index
**Level 0: Meta - Navigation & Reference** | Last Updated: 2025-11-25

**Purpose:** Central navigation hub for all project documentation

---

## Quick Reference

| Need to know... | Read |
|-----------------|------|
| Business rules & entities | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Validation constraints & limits | [VALIDATION_RULES.md](VALIDATION_RULES.md) |
| UI designs & wireframes | [UI_MOCKUPS.md](UI_MOCKUPS.md) |
| Development roadmap | [ROADMAP.md](ROADMAP.md) |
| Architecture patterns | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Deployment guide | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Testing strategies | [TESTING.md](TESTING.md) |
| Term definitions | [GLOSSARY.md](GLOSSARY.md) |
| How to change docs | [DOCUMENTATION_CHANGE_PROCEDURE.md](DOCUMENTATION_CHANGE_PROCEDURE.md) |

---

## Document Hierarchy

```
LEVEL 0: META (Navigation & Reference)
├── DOCUMENTATION_INDEX.md      ← You are here
├── GLOSSARY.md                 → Term definitions
└── CHANGELOG.md                → What changed when

LEVEL 1: SOURCE OF TRUTH (Authoritative - change these first)
├── DOMAIN_MODEL.md             → Business rules, entities, workflows
└── VALIDATION_RULES.md         → All constraints, limits, validations

LEVEL 2: DERIVED (References Level 1 - update after Level 1)
├── UI_MOCKUPS.md               → UI implementation designs
├── UI_PATTERNS.md              → Reusable UI patterns (future)
├── ROADMAP.md                  → Project roadmap, development phases
└── README.md                   → Project overview

LEVEL 3: OPERATIONAL (Procedures & Technical)
├── ARCHITECTURE.md             → Technical patterns, code examples
├── TESTING.md                  → Test strategies
├── DEPLOYMENT.md               → Infrastructure setup
└── DOCUMENTATION_CHANGE_PROCEDURE.md → How to modify docs

WORKBENCH: (Temporary, per-task tracking)
└── workbench/*.md              → Active work-in-progress files
```

---

## Decision Tree: Where Should I Document This?

```
                    ┌─────────────────────────────────┐
                    │ What type of information is it? │
                    └─────────────────────────────────┘
                                    │
        ┌───────────────┬───────────┴───────────┬────────────────┐
        ▼               ▼                       ▼                ▼
   Business Rule   Constraint/Limit      UI Behavior      Technical/How
   "What & Why"    "Boundaries"         "User sees"       "Implementation"
        │               │                       │                │
        ▼               ▼                       ▼                ▼
  DOMAIN_MODEL.md  VALIDATION_RULES.md   UI_MOCKUPS.md    ARCHITECTURE.md
        │               │                       │                │
        └───────────────┴───────────┬───────────┴────────────────┘
                                    ▼
                        Does it affect the roadmap?
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                         YES                  NO
                          │                   │
                          ▼                   │
                    ROADMAP.md                │
                          │                   │
                          └─────────┬─────────┘
                                    ▼
                          Is it a term/concept?
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                         YES                  NO
                          │                   │
                          ▼                   ▼
                    GLOSSARY.md             Done
```

---

## Cross-Reference Map

| Concept | Defined In | Referenced In |
|---------|-----------|---------------|
| Tournament entity | DOMAIN_MODEL.md §Tournament | VALIDATION_RULES.md, UI_MOCKUPS.md |
| Tournament phases | DOMAIN_MODEL.md §1 | VALIDATION_RULES.md §Phase Transitions |
| Minimum performers formula | VALIDATION_RULES.md §3 | DOMAIN_MODEL.md §2, UI_MOCKUPS.md §4 |
| Field length limits | VALIDATION_RULES.md §UI Field Validation | UI_MOCKUPS.md (referenced) |
| Magic link settings | VALIDATION_RULES.md §Magic Link Auth | UI_MOCKUPS.md §Login |
| Pool distribution | VALIDATION_RULES.md §Pool Size | DOMAIN_MODEL.md §4 |
| Tiebreak logic | DOMAIN_MODEL.md §5 | VALIDATION_RULES.md (summary) |
| Deletion rules | DOMAIN_MODEL.md §8 | VALIDATION_RULES.md §Deletion Rules |
| V1/V2 features | DOMAIN_MODEL.md §Judge | ROADMAP.md §Phase 5 |
| Judge workflow | DOMAIN_MODEL.md §Judge | UI_MOCKUPS.md §21 (V2 Only) |
| Battle generation | ROADMAP.md §2.1 | ARCHITECTURE.md (future) |
| Pool distribution | ROADMAP.md §2.2 | VALIDATION_RULES.md §Pool Size |
| Tiebreak battles | ROADMAP.md §2.3 | DOMAIN_MODEL.md §5 |

---

## V1 vs V2 Feature Summary

| Feature | V1 | V2 |
|---------|----|----|
| **Battle Scoring** | Staff/Admin encodes winner | Judges score independently |
| **Judge Accounts** | N/A | Temporary user accounts |
| **Scoring Interface** | Battle encoding UI | Judge scoring UI (blind) |
| **Score Aggregation** | N/A | Admin validates, aggregates |

**V2 Documentation:**
- DOMAIN_MODEL.md §Judge (V2 Only)
- UI_MOCKUPS.md §21.1 Judge Scoring Interface (V2 Only)
- ROADMAP.md Phase 5

---

## Document Ownership

| Document | Primary Owner | Review Frequency |
|----------|--------------|------------------|
| DOMAIN_MODEL.md | Product/Business | Per feature change |
| VALIDATION_RULES.md | Product/Dev | Per constraint change |
| UI_MOCKUPS.md | Design/Frontend | Per UI change |
| ROADMAP.md | Project Lead | Weekly |
| ARCHITECTURE.md | Tech Lead | Per pattern change |
| README.md | All | Per release |

---

## Related Resources

- **Code:** `app/models/` - SQLAlchemy models (technical schema source of truth)
- **Tests:** `tests/` - Test implementations
- **Archive:** `archive/` - Historical workbench files and progress tracking

---

## Getting Started

1. **New to the project?** Start with [README.md](README.md)
2. **Understanding the domain?** Read [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
3. **Building UI?** Reference [UI_MOCKUPS.md](UI_MOCKUPS.md)
4. **Adding validation?** Check [VALIDATION_RULES.md](VALIDATION_RULES.md)
5. **Changing documentation?** Follow [DOCUMENTATION_CHANGE_PROCEDURE.md](DOCUMENTATION_CHANGE_PROCEDURE.md)
