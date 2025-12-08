# Feature Specification: Slash Command Methodology Improvement

**Date:** 2025-12-08
**Status:** Awaiting User Approval

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Deliverable 1: One-Command Local Dev Setup](#3-deliverable-1-one-command-local-dev-setup)
4. [Deliverable 2: Slash Command Improvements](#4-deliverable-2-slash-command-improvements)
5. [Business Rules & Acceptance Criteria](#5-business-rules--acceptance-criteria)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Evidence from Last 5 Features](#7-appendix-evidence-from-last-5-features)

---

## 1. Problem Statement

The current slash command methodology allows features to be marked complete without sufficient verification, leading to cascading bugs discovered in production. Analysis of the last 5 features shows that 3 out of 5 (60%) either triggered immediate follow-up bug fixes or required scope reduction mid-implementation.

Additionally, there is no easy way to test locally - all testing happens via pytest or in production on Railway.

---

## 2. Executive Summary

### Two Deliverables

| # | Deliverable | Purpose |
|---|-------------|---------|
| 1 | **One-Command Local Dev Setup** | Enable local browser testing with minimal friction |
| 2 | **Slash Command Improvements** | Close methodology gaps that allow bugs through |

### Evidence from Last 5 Features

| Feature | Issue | Root Cause |
|---------|-------|------------|
| UX Navigation Redesign | Created broken links found in production | No browser testing |
| Fix Broken Phases Links | Bug from prior feature | No pattern scan |
| Bug Fix POST Routes 404 | 10 routes had same issue | No pattern scan |
| E2E Testing Framework | Accepted at 69% not 85% | Technical constraint discovered mid-implementation |

### Key Principle

**"Trust but verify"** - Add verification evidence requirements at critical gates.

---

## 3. Deliverable 1: One-Command Local Dev Setup

### Goal

Developer can start the app locally with ONE command and immediately test in browser.

### Current State

README says:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Reality requires:
- uv (not pip)
- Virtual environment activation
- Database migration
- Seed data for test accounts
- Environment variables

### Proposed Solution

**Create `scripts/dev.sh`:**
```bash
#!/bin/bash
# One-command local development setup
# Usage: ./scripts/dev.sh

set -e

echo "Setting up Battle-D local development..."

# 1. Create/activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi
source .venv/bin/activate

# 2. Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# 3. Setup environment
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    # Set console email provider for dev
    sed -i '' 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env 2>/dev/null || \
    sed -i 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env
fi

# 4. Initialize database
echo "Initializing database..."
mkdir -p data
alembic upgrade head

# 5. Seed test accounts (if not exist)
echo "Seeding test accounts..."
python -c "
import asyncio
from app.database import async_session_maker
from app.models import User
from app.models.enums import UserRole

async def seed():
    async with async_session_maker() as session:
        # Check if admin exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == 'admin@battle-d.com'))
        if result.scalar_one_or_none():
            print('Test accounts already exist')
            return

        # Create test accounts
        users = [
            User(email='admin@battle-d.com', first_name='Admin', last_name='User', role=UserRole.ADMIN),
            User(email='staff@battle-d.com', first_name='Staff', last_name='User', role=UserRole.STAFF),
            User(email='mc@battle-d.com', first_name='MC', last_name='User', role=UserRole.MC),
        ]
        for user in users:
            session.add(user)
        await session.commit()
        print('Created test accounts: admin@battle-d.com, staff@battle-d.com, mc@battle-d.com')

asyncio.run(seed())
"

# 6. Start server
echo ""
echo "=========================================="
echo "Battle-D is running at: http://localhost:8000"
echo ""
echo "Test accounts:"
echo "  - admin@battle-d.com (Admin)"
echo "  - staff@battle-d.com (Staff)"
echo "  - mc@battle-d.com (MC)"
echo ""
echo "Magic links will print to console."
echo "=========================================="
echo ""

uvicorn app.main:app --reload
```

### Usage

```bash
# First time (or anytime)
./scripts/dev.sh

# That's it. Open http://localhost:8000
```

### Acceptance Criteria

```gherkin
Feature: One-Command Local Development
  As a developer
  I want to start local dev with one command
  So that I can test features in browser quickly

Scenario: First-time setup
  Given I have cloned the repository
  And I have uv installed
  When I run ./scripts/dev.sh
  Then virtual environment is created
  And dependencies are installed
  And database is initialized
  And test accounts are created
  And server starts at localhost:8000

Scenario: Subsequent runs
  Given I have run ./scripts/dev.sh before
  When I run ./scripts/dev.sh again
  Then it detects existing setup
  And server starts quickly
  And I can log in with test accounts

Scenario: Login with magic link
  Given the server is running
  When I enter admin@battle-d.com on login page
  Then magic link prints to console
  And I can copy/paste URL to log in
```

---

## 4. Deliverable 2: Slash Command Improvements

### 4.1 Pattern Scanning in `/analyze-feature`

**Gap:** No "scan for similar issues" step.
**Consequence:** Same bug exists in multiple places, only one is fixed.

**Add Step 1.4.5:**
```markdown
### Step 1.4.5: Pattern Scan

**For bug fixes - REQUIRED:**
Search codebase for similar patterns:

```bash
# Example: POST routes returning wrong status
grep -r "RedirectResponse.*303.*not found" app/routers/
grep -r "add_flash_message.*not found" app/routers/
```

**Document in feature-spec.md:**
| File | Line | Similar Issue |
|------|------|---------------|
| battles.py | 139 | Same pattern |
| admin.py | 45 | Same pattern |

**Decision:** Fix all now / Track separately

**For new features - RECOMMENDED:**
Search for similar existing implementations to follow.
```

**Quality Gate Addition:**
```markdown
- [ ] Pattern scan performed (grep for similar issues)
- [ ] All affected locations documented
- [ ] Decision documented: fix all now or track separately
```

### 4.2 Technical POC in `/plan-implementation`

**Gap:** No technical risk validation before full implementation.
**Consequence:** Constraints discovered mid-implementation (E2E at 69%).

**Add Step 3.5:**
```markdown
### Step 3.5: Technical Risk POC (If Applicable)

**When required:**
- New integration pattern (new test framework, external API)
- Significant architecture change
- Unfamiliar technology

**Process (1-2 hours max):**
1. Create minimal proof-of-concept
2. Test the risky assumption
3. Document findings
4. Decide: proceed / adjust / abandon

**Document in implementation-plan.md:**
```markdown
## Technical POC

**Risk:** Sync TestClient with async fixtures
**Hypothesis:** TestClient can see fixture-created data
**Result:** FAILED - Session isolation
**Decision:** Adjust target from 85% to 70%
```

**Skip if:** Standard CRUD, no new patterns, low complexity.
```

**Quality Gate Addition:**
```markdown
- [ ] Technical risks identified (or "none" documented)
- [ ] POC performed for high-risk items (if applicable)
- [ ] POC results documented with decision
```

### 4.3 Browser Smoke Test in `/verify-feature`

**Gap:** Browser testing optional, self-certified.
**Consequence:** URL/template bugs pass tests but fail in browser.

**Update Step 3 to MANDATORY:**
```markdown
### Step 3: Browser Smoke Test (MANDATORY for UI changes)

**Skip if:** Pure backend change with no UI.

**Required (with local dev running):**

1. **Open feature in browser:**
   - Navigate to http://localhost:8000
   - Log in with test account
   - Navigate to feature

2. **Test primary action:**
   - Click main button/submit form
   - Verify success

3. **Check console:**
   - Open DevTools > Console
   - Verify no errors

4. **Document:**
```markdown
## Browser Smoke Test

**Tested on:** localhost:8000
**Account used:** admin@battle-d.com

**Results:**
- [x] Feature page loads
- [x] Primary action works
- [x] No console errors
- [ ] Issue found: [describe if any]
```
```

**Quality Gate Addition:**
```markdown
**Browser Verification (MANDATORY for UI):**
- [ ] Local dev running (./scripts/dev.sh)
- [ ] Feature tested in browser
- [ ] Primary action verified
- [ ] No console errors
- [ ] Results documented
```

### 4.4 Cross-Feature Impact in `/close-feature`

**Gap:** No check that related features still work.
**Consequence:** Feature breaks related functionality (UX broke phases).

**Add Step 1.5:**
```markdown
### Step 1.5: Cross-Feature Impact Check

**Based on files modified, verify related features:**

| If You Modified | Test These |
|-----------------|------------|
| base.html | All sidebar links, all pages |
| Shared service | All routes using that service |
| Model | All services using that model |
| Router | Navigation to/from affected routes |

**Process:**
1. List files modified
2. Identify dependent features
3. Quick-test each (click through)
4. Document

**Example:**
```markdown
## Cross-Feature Impact

**Files modified:** base.html, dashboard_service.py

**Related features tested:**
| Feature | Test | Result |
|---------|------|--------|
| Sidebar nav | Click all links | All work |
| Phase management | Click "Manage Phases" | Works |
| Event mode | Navigate to /event | Works |
```
```

**Quality Gate Addition:**
```markdown
- [ ] Related features identified
- [ ] Each related feature quick-tested
- [ ] No regressions found
- [ ] Verification documented
```

---

## 5. Business Rules & Acceptance Criteria

### BR-METHOD-001: Pattern Scanning

```gherkin
Scenario: Bug fix includes pattern scan
  Given I am analyzing a bug
  When I complete /analyze-feature
  Then I have searched for similar patterns in codebase
  And documented all locations with same issue
  And decided: fix all now or track separately
```

### BR-METHOD-002: Technical POC

```gherkin
Scenario: High-risk implementation has POC
  Given implementation involves new pattern/technology
  When I complete /plan-implementation
  Then I have created minimal POC (1-2 hours)
  And documented whether assumption holds
  And adjusted plan if needed
```

### BR-METHOD-003: Browser Smoke Test

```gherkin
Scenario: UI feature verified in browser
  Given I completed a feature with UI changes
  When I complete /verify-feature
  Then I have tested feature in browser (localhost)
  And verified primary action works
  And checked for console errors
  And documented results
```

### BR-METHOD-004: Cross-Feature Impact

```gherkin
Scenario: Related features verified before closure
  Given I am closing a feature
  When I complete /close-feature
  Then I have identified related features
  And quick-tested each one
  And documented no regressions
```

---

## 6. Implementation Recommendations

### Priority Order

| # | Item | Type | Impact |
|---|------|------|--------|
| 1 | `scripts/dev.sh` | New file | Enables all browser testing |
| 2 | Update README Quick Start | Doc update | Points to new script |
| 3 | `/verify-feature` browser test | Command update | Catches URL/template bugs |
| 4 | `/analyze-feature` pattern scan | Command update | Catches systemic issues |
| 5 | `/close-feature` cross-feature | Command update | Prevents cascading bugs |
| 6 | `/plan-implementation` POC | Command update | Catches constraints early |

### Files to Modify

| File | Change |
|------|--------|
| `scripts/dev.sh` | **CREATE** - One-command setup |
| `README.md` | Update Quick Start section |
| `.claude/commands/analyze-feature.md` | Add pattern scan step |
| `.claude/commands/plan-implementation.md` | Add POC step |
| `.claude/commands/verify-feature.md` | Make browser test mandatory |
| `.claude/commands/close-feature.md` | Add cross-feature check |

---

## 7. Appendix: Evidence from Last 5 Features

### Feature 1: UX Navigation Redesign (2025-12-07)

**What happened:** Major feature marked complete without browser testing. Broken links discovered in production.

**From closure doc:**
> "Phase 3.3 was marked complete without browser testing. URL prefixes in templates didn't match router configuration. 404 errors discovered by user in production."

**Would have caught:** Browser smoke test requirement.

### Feature 2: Fix Broken Phases Links (2025-12-07)

**What happened:** Found 7 broken links across 6 templates - all had same pattern issue.

**Would have caught:** Pattern scan during analysis.

### Feature 3: Bug Fix POST Routes 404 (2025-12-08)

**What happened:** Found 10 routes across 3 files with identical bug.

**From bug report:**
> "Similar pattern may exist in other routers. A codebase-wide audit should be performed."

**Would have caught:** Pattern scan during analysis.

### Feature 4: E2E Testing Framework (2025-12-08)

**What happened:** Target was 85% coverage, accepted at 69% due to session isolation.

**From closure doc:**
> "Session isolation between sync TestClient and async fixtures limits testable scenarios."

**Would have caught:** Technical POC before full implementation.

### Feature 5: Integration Testing Methodology (2025-12-07)

**What happened:** Methodology update after production bugs.

**Root cause:** Mocked tests hiding real bugs - already addressed in methodology.

---

## 8. User Confirmation

- [ ] Approach approved: One-command dev setup + methodology improvements
- [ ] `scripts/dev.sh` approach acceptable
- [ ] Quality gate additions approved
- [ ] Ready for `/plan-implementation`
