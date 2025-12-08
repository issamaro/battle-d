# Analyze Feature - Business Analysis + Requirements Definition

**Phases:** 1 (Business Analysis) + 2 (Requirements Definition)

**Purpose:** Understand WHAT to build and WHY, without any technical thinking yet.

---

## Instructions for Claude

You are starting a new feature. Follow these steps in order:

### Step 1: Business Analysis Phase (Methodology §1)

**1.1 Extract User Request Intent**
- What did the user ask for? (exact words)
- What problem are they trying to solve? (infer, then confirm)
- What triggered this request? (bug report, user feedback, new requirement)

**1.2 Identify the "Five Whys"**
- **Who** is affected? (users, staff, admins, stakeholders)
- **What** is the current pain point? (what's broken or missing)
- **When** does this problem occur? (workflow, frequency)
- **Where** in the user journey does this happen? (specific screens, processes)
- **Why** does this matter to the business? (impact: efficiency, revenue, satisfaction)

**1.3 Define Success Criteria (Business Perspective)**
- How will we know this solved the problem?
- What would make users say "this is better"?
- What metrics would improve? (time saved, errors reduced, satisfaction score)

**1.4 Create User Story with BDD-Style Acceptance Criteria**

Use Gherkin format:
```gherkin
Feature: [Feature name]
  As a [type of user]
  I want [capability]
  So that [business value]

Scenario: [Scenario name]
  Given [initial context/state]
  When [action taken]
  Then [expected outcome]
  And [additional expected outcome]
```

Create 2-4 scenarios covering different aspects of the feature.

**1.4.5 Pattern Scan (For Bug Fixes - REQUIRED)**

Before analyzing the specific bug, search for similar issues across the codebase:

**Process:**
1. Identify the problematic pattern in the reported bug
2. Search codebase for similar patterns:
   ```bash
   # Example searches:
   grep -rn "pattern_from_bug" app/
   grep -rn "similar_anti_pattern" app/
   ```
3. Document all occurrences found
4. Decide: Fix all now or track separately

**Document in feature-spec.md:**
```markdown
## Pattern Scan Results

**Pattern searched:** [describe the problematic pattern]

**Search command:**
`grep -rn "..." app/`

**Results:**
| File | Line | Description |
|------|------|-------------|
| file1.py | 123 | Same issue |
| file2.py | 456 | Same issue |

**Decision:**
- [ ] Fix all in this feature
- [ ] Fix reported bug only, track others in backlog
```

**For new features:** Search for similar existing implementations to follow as patterns.

**Skip if:** Pure documentation change or methodology update with no code patterns to scan.

**1.5 As-Is Analysis (Business Lens Only)**

Read documentation and code to understand current state:

**a) Business Entities (Read DOMAIN_MODEL.md):**
- Which entities are involved?
- What can users currently do?
- What are current limitations?
- What workflows exist?

**b) Business Rules (Read VALIDATION_RULES.md):**
- What validation rules exist?
- What constraints apply?
- Why do these rules exist? (business reason)
- What gaps exist in current rules?

**c) Current User Experience:**
- Read FRONTEND.md for existing components
- Read templates (app/templates/**/*.html) for current workflow
- Document step-by-step current user journey
- Identify pain points
- Focus on WHAT users experience, not HOW it's implemented

**d) Current Business Logic (if relevant):**
- Read services (app/services/*.py) for WHAT happens automatically
- What requires manual intervention?
- What business rules are enforced?
- Focus on business operations, not technical implementation

**1.6 Create Gap Analysis**
```
Current State (As-Is):
- [What exists today]

Desired State (To-Be):
- [What's needed per user story]

Gap (What's Missing):
- [What's missing/broken]

Business Impact:
- [Time/cost/satisfaction impact]
```

**1.7 Create User Flow Diagram**

Create an ASCII flow diagram showing the complete user journey:
- All phases/steps in the workflow
- Decision points and branches
- Where issues/gaps exist (mark with ⚠️ warnings)
- Validation checks at each transition
- Worst-case scenarios and corner cases

Format example (one phase transition):
```
═══════════════════════════════════════════════════════════════
 PHASE 1: [NAME]                                [Status: STATE]
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  ACTIONS:                                                │
  │  • Action 1                                              │
  │  • Action 2                                              │
  └──────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │  VALIDATION CHECK ([Phase] → [Next Phase]):              │
  │  ✅ Rule 1 passes                                        │
  │  ✅ Rule 2 passes                                        │
  │  ⚠️ Edge case: [description of issue]                   │
  └──────────────────────────────────────────────────────────┘

  [USER ACTION] ─────────────────────────────────────────────►

═══════════════════════════════════════════════════════════════
 PHASE 2: [NEXT NAME]
═══════════════════════════════════════════════════════════════
```

> **Note:** Required for workflow features. Can be simplified or omitted for isolated utilities.

**1.8 Validate Understanding with User**

Use **AskUserQuestion** to:
- Confirm problem statement
- Validate BDD scenarios match their vision
- Clarify ambiguous terms
- Confirm scope

**MANDATORY:** Cannot proceed until user confirms understanding.

---

### Step 2: Requirements Definition Phase (Methodology §2)

**2.1 Define Functional Requirements**

From BDD scenarios, derive concrete requirements:

**Must Have:**
- [ ] Requirement 1 (derived from scenario)
- [ ] Requirement 2
- [ ] Requirement 3

**Should Have (nice-to-have if time permits):**
- [ ] Enhancement 1
- [ ] Enhancement 2

**Won't Have (explicitly out of scope):**
- Excluded item 1
- Excluded item 2

**2.2 Define Non-Functional Requirements**

- Performance constraints (response time, load capacity)
- Scalability needs (how many users/records)
- Security requirements (authentication, authorization, data protection)
- Accessibility requirements (WCAG 2.1 AA per FRONTEND.md)
- Responsive behavior (mobile-first per FRONTEND.md)

**2.3 Define Validation Rules**

- What business constraints need validation?
- What data validation is required?
- Will these go in VALIDATION_RULES.md? (if domain rules, yes)

**2.4 Define UI Specifications (if user-facing)**

Read **FRONTEND.md Component Library** to identify:

**Components to Reuse:**
- [ ] Component 1 (exists in FRONTEND.md)
- [ ] Component 2 (exists)

**Components Missing:**
- [ ] Component 3 (need design discussion)

**HTMX Patterns Needed:**
- Pattern 1 (from FRONTEND.md HTMX Patterns section)
- Pattern 2

**Accessibility Considerations:**
- Keyboard navigation requirements
- Screen reader support
- ARIA attributes needed
- Color contrast requirements

**Responsive Behavior:**
- Mobile (320px-768px): [specific requirements]
- Tablet (769px-1024px): [specific requirements]
- Desktop (1025px+): [specific requirements]

**If components missing:**
- Use **AskUserQuestion** to discuss design approach
- Propose options aligned with FRONTEND.md principles
- Get user preference

**2.5 Create Acceptance Criteria**

From requirements and BDD scenarios:
- How will we know it's done?
- What tests must pass?
- What UI/UX criteria must be met?

---

## Deliverable: Create feature-spec.md

Create a file named: `workbench/FEATURE_SPEC_YYYY-MM-DD_[FEATURE-NAME].md`

> **Template Flexibility:** Not all sections are required for every feature.
> - **New features:** Focus on sections 1, 3, 4, 6
> - **Validation tasks:** Focus on sections 1, 2, 3, 4, 5
> - **Simple changes:** Sections 1, 4, 6 may suffice

Use this format:

```markdown
# Feature Specification: [Feature Name]

**Date:** YYYY-MM-DD
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement
[1-2 sentences describing the problem from business perspective]

---

## 2. Executive Summary

### Scope
[Brief description of what this analysis covers]

### What Works ✅
| Feature | Status |
|---------|--------|
| Feature 1 | Production Ready / Partial / Not Implemented |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| Issue 1 | BUG/GAP | file:line |

### Key Business Rules Defined
- **BR-XXX-001:** [Rule summary]

> **Note:** Omit Executive Summary for simple features. Include for validation tasks or complex analysis.

---

## 3. User Flow Diagram
[ASCII diagram showing complete workflow - see methodology 1.7]

> **Note:** Required for workflow features. Can be omitted for isolated utilities.
> For validation tasks, include issues (bugs/gaps) directly in the diagram using 🚨 boxes.

---

## 4. Business Rules & Acceptance Criteria

### 4.x [Rule/Feature Name]

**Business Rule BR-XXX-NNN: [Rule Name]**
> [Rule statement in business terms]

**Acceptance Criteria:**
```gherkin
Feature: [Feature name]
  Scenario: [Scenario name]
    Given [context]
    When [action]
    Then [outcome]
```

> **Note:** Use Gherkin for complex rules. Simple features can use checkbox list:
> - [ ] Acceptance criterion 1
> - [ ] Acceptance criterion 2

---

## 5. Current State Analysis

### 5.x [Analysis Area]
**Business Rule:** [What should happen]
**Implementation Status:** ✅/⚠️/❌ [Status]
**Evidence:** [Code references]
**Test Coverage:** [What's tested]

> **Note:** Detailed technical analysis. Can be abbreviated for new features.

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)
1. [Critical item]

### 6.2 Recommended
1. [Recommended item]

### 6.3 Nice-to-Have (Future)
1. [Future item]

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers
- **Q:** [Question]
  - **A:** [Answer or status]

### 7.2 Formulas/Calculations
[Any relevant formulas or reference data]

### 7.3 User Confirmation
- [x] User confirmed problem statement
- [x] User validated scenarios
- [x] User approved requirements
```

---

## Quality Gate (BLOCKING)

**Before marking this command complete, verify:**

**Problem Understanding:**
- [ ] Problem statement written in business terms (not technical)
- [ ] BDD scenarios written with Given/When/Then format (2-4 scenarios)

**Pattern Scan (Bug Fixes):**
- [ ] Pattern scan performed (grep for similar issues)
- [ ] All affected locations documented
- [ ] Decision documented: fix all now or track separately
- [ ] (Skip if: new feature, documentation-only, or methodology update)

**Flow & Structure:**
- [ ] User flow diagram created (if workflow feature)
- [ ] Executive summary provides quick overview (if complex analysis)
- [ ] Issues clearly separated from recommendations

**Analysis Complete:**
- [ ] Affected business entities identified (from DOMAIN_MODEL.md)
- [ ] Current business rules documented (from VALIDATION_RULES.md)
- [ ] Gap analysis completed (current vs desired with business impact)

**Requirements Defined:**
- [ ] Business rules defined with Gherkin acceptance criteria
- [ ] Implementation recommendations prioritized (Critical/Recommended/Nice-to-Have)
- [ ] All ambiguities resolved via AskUserQuestion

**User Validation:**
- [ ] User confirmed understanding of problem
- [ ] User validated scenarios match their vision
- [ ] User approved requirements

**Deliverable:**
- [ ] feature-spec.md file created in workbench/
- [ ] Relevant sections completed (per template flexibility guidelines)
- [ ] File follows template format

**If any checkbox is empty, STOP and complete that step.**

---

## Common Mistakes to Avoid

❌ **Don't jump to technical details:**
- BAD: "We'll add a filter_by_status() method"
- GOOD: "Staff need to see only unencoded battles"

❌ **Don't skip as-is analysis:**
- BAD: Proposing changes without understanding current workflow
- GOOD: Document current workflow → identify pain points → propose solution

❌ **Don't write vague acceptance criteria:**
- BAD: "System should be faster"
- GOOD: "Staff can find any battle within 5 seconds"

❌ **Don't mix business and technical language:**
- BAD: "Add hx-get endpoint for filtering"
- GOOD: "Staff can filter battles by status with one click"

❌ **Don't skip user validation:**
- Must use AskUserQuestion to confirm understanding
- Must validate BDD scenarios with user
- Cannot proceed without user approval

---

## Next Steps

After this command completes and user approves the feature-spec.md:
1. User reviews feature-spec.md
2. User provides feedback/approval
3. Run `/plan-implementation feature-spec.md` to start technical design

---

**Remember:** This phase is about understanding WHAT to build and WHY. No technical decisions yet. Stay in business language. Focus on user needs and business value.
