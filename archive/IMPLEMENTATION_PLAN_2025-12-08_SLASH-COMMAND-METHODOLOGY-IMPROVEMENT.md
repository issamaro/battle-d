# Implementation Plan: Slash Command Methodology Improvement

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_SLASH-COMMAND-METHODOLOGY-IMPROVEMENT.md

---

## 1. Summary

**Feature:** One-command local dev setup + slash command methodology improvements to catch bugs before production.

**Approach:**
1. Create `scripts/dev.sh` that leverages existing `seed_db.py`
2. Update README Quick Start section
3. Add pattern scan, POC, browser test, and cross-feature check steps to slash commands

---

## 2. Affected Files

### New Files
| File | Purpose |
|------|---------|
| `scripts/dev.sh` | One-command local dev setup script |

### Documentation Updates
| File | Change |
|------|--------|
| `README.md` | Update Quick Start section to use `./scripts/dev.sh` |
| `.claude/commands/analyze-feature.md` | Add Step 1.4.5: Pattern Scan |
| `.claude/commands/plan-implementation.md` | Add Step 3.5: Technical POC |
| `.claude/commands/verify-feature.md` | Update Step 3: Browser Smoke Test (MANDATORY) |
| `.claude/commands/close-feature.md` | Add Step 1.5: Cross-Feature Impact Check |

### No Changes Needed
| Item | Reason |
|------|--------|
| Models | No data model changes |
| Services | No service changes |
| Repositories | No repository changes |
| Routes | No route changes |
| Database | No schema changes |
| Tests | Methodology changes only |

---

## 3. Implementation Plan

### 3.1 Deliverable 1: One-Command Local Dev Setup

#### scripts/dev.sh

**Leverages existing infrastructure:**
- `seed_db.py` - Already exists, creates test accounts
- `.env.example` - Already exists with all required variables
- `alembic` - Already configured for migrations
- `.venv` - Standard Python virtual environment

**Script Design:**
```bash
#!/bin/bash
# One-command local development setup
# Usage: ./scripts/dev.sh

set -e  # Exit on any error

echo "🚀 Setting up Battle-D local development..."
echo ""

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed."
    echo "   Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 2. Create/activate virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# Activate venv
source .venv/bin/activate

# 3. Install dependencies
echo "📦 Installing dependencies..."
uv pip install -r requirements.txt --quiet

# 4. Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from .env.example..."
    cp .env.example .env
    # Set console email provider for dev (macOS and Linux compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env
    else
        sed -i 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env
    fi
fi

# 5. Initialize database
echo "🗄️  Initializing database..."
mkdir -p data

# Run migrations
.venv/bin/alembic upgrade head

# 6. Seed test accounts
echo "🌱 Seeding test accounts..."
.venv/bin/python seed_db.py

# 7. Start server
echo ""
echo "=========================================="
echo "✅ Battle-D is running at: http://localhost:8000"
echo ""
echo "📧 Test accounts:"
echo "   • admin@battle-d.com (Admin)"
echo "   • staff@battle-d.com (Staff)"
echo "   • mc@battle-d.com (MC)"
echo ""
echo "🔗 Magic links will print to console."
echo "=========================================="
echo ""

.venv/bin/uvicorn app.main:app --reload
```

**Key Design Decisions:**
1. Uses existing `seed_db.py` instead of inline Python
2. Uses `.venv/bin/` prefix to ensure correct Python is used
3. Cross-platform `sed` for macOS and Linux
4. Clear emoji feedback for progress
5. Idempotent - safe to run multiple times

---

### 3.2 Deliverable 2: Slash Command Improvements

#### 3.2.1 `/analyze-feature` - Add Pattern Scan

**Location:** `.claude/commands/analyze-feature.md`
**Insert after:** Step 1.4 (Create User Story with BDD-Style Acceptance Criteria)
**Insert before:** Step 1.5 (As-Is Analysis)

**New Step 1.4.5:**
```markdown
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
```

**Quality Gate Addition:**
```markdown
**Pattern Scan (Bug Fixes):**
- [ ] Pattern scan performed (grep for similar issues)
- [ ] All affected locations documented
- [ ] Decision documented: fix all now or track separately
```

---

#### 3.2.2 `/plan-implementation` - Add Technical POC

**Location:** `.claude/commands/plan-implementation.md`
**Insert after:** Step 3 (Choose Architectural Patterns)
**Insert before:** Step 4 (Plan Database Changes)

**New Step 3.5:**
```markdown
### Step 3.5: Technical Risk POC (If Applicable)

**When required:**
- New integration pattern (new test framework, external API, unfamiliar library)
- Significant architecture change (new service layer, caching, async patterns)
- Technology you haven't used in this codebase before

**When to skip:**
- Standard CRUD operations following existing patterns
- Simple template changes
- Documentation-only changes
- Bug fixes with clear solutions

**POC Process (1-2 hours maximum):**
1. Identify the riskiest technical assumption
2. Create minimal proof-of-concept (separate file or test)
3. Test whether the assumption holds
4. Document findings
5. Decide: proceed as planned / adjust approach / abandon

**Document in implementation-plan.md:**
```markdown
## Technical POC

**Risk identified:** [e.g., "Sync TestClient with async fixtures"]
**Hypothesis:** [e.g., "TestClient can see data created by async fixtures"]

**POC code:**
```python
# Minimal test to validate assumption
...
```

**Result:** ✅ PASSED / ❌ FAILED
**Findings:** [what you learned]
**Decision:** [proceed / adjust target from X to Y / abandon approach]
```

**If no POC needed, document:**
```markdown
## Technical POC

**Status:** Not required
**Reason:** Standard CRUD following existing patterns
```
```

**Quality Gate Addition:**
```markdown
**Technical Risk Validation:**
- [ ] Technical risks identified (or "none - standard patterns" documented)
- [ ] POC performed for high-risk items (if applicable)
- [ ] POC results documented with decision
```

---

#### 3.2.3 `/verify-feature` - Make Browser Test MANDATORY

**Location:** `.claude/commands/verify-feature.md`
**Update:** Step 3 (Manual Testing Checklist)

**Replace Step 3 with:**
```markdown
### Step 3: Browser Smoke Test (MANDATORY for UI changes)

**Skip condition:** ONLY skip if feature has ZERO UI changes (pure backend/tests).

**Prerequisites:**
- Local dev running: `./scripts/dev.sh`
- Browser open at http://localhost:8000
- Logged in with test account

**Required Tests:**

**3.1 Feature Page Loads:**
- Navigate to the feature's primary page
- Verify page renders without errors
- Check: No 404, no 500, content displays

**3.2 Primary Action Works:**
- Perform the main action (click button, submit form, etc.)
- Verify expected result occurs
- Check: Success message, data saved, redirect works

**3.3 Console Check:**
- Open browser DevTools (F12) > Console tab
- Verify: No red errors
- Note any warnings (optional to fix)

**3.4 Navigation Links (if templates modified):**
- Click all navigation links on the page
- Verify: No 404 errors
- Check: All links lead to correct pages

**Document in test-results.md:**
```markdown
## Browser Smoke Test

**Tested on:** localhost:8000
**Account used:** admin@battle-d.com

**Results:**
| Test | Status | Notes |
|------|--------|-------|
| Feature page loads | ✅ | Renders correctly |
| Primary action works | ✅ | Form submits, success message shows |
| Console errors | ✅ | No errors |
| Navigation links | ✅ | All sidebar links work |

**Issues found:** None / [describe if any]
```
```

**Quality Gate Update:**
```markdown
**Browser Verification (MANDATORY for UI changes):**
- [ ] Local dev running (`./scripts/dev.sh`)
- [ ] Feature page loads without errors
- [ ] Primary action works correctly
- [ ] No console errors in browser DevTools
- [ ] Navigation links work (if templates modified)
- [ ] Results documented in test-results.md
```

---

#### 3.2.4 `/close-feature` - Add Cross-Feature Impact Check

**Location:** `.claude/commands/close-feature.md`
**Insert after:** Step 1 (Pre-Closure Checklist)
**Insert before:** Step 2 (Update CHANGELOG.md)

**New Step 1.5:**
```markdown
### Step 1.5: Cross-Feature Impact Check

**Purpose:** Verify that changes didn't break related features.

**Based on files modified, test related features:**

| If You Modified | Quick-Test These |
|-----------------|------------------|
| `base.html` | All sidebar links, all major pages |
| `app/templates/*.html` | Pages including modified template |
| Shared service (`*_service.py`) | All routes using that service |
| Model (`app/models/*.py`) | All services using that model |
| Router (`app/routers/*.py`) | Navigation to/from affected routes |
| CSS files | Visual check on pages using those styles |

**Process:**
1. List all files modified in this feature
2. For each file type, identify dependent features (use table above)
3. Quick-test each dependent feature (navigate, click primary action)
4. Document results

**Document:**
```markdown
## Cross-Feature Impact Check

**Files modified in this feature:**
- [list files]

**Related features tested:**
| Feature | What I Tested | Result |
|---------|---------------|--------|
| Dashboard | Page loads, quick actions work | ✅ |
| Phase management | "Manage Phases" button works | ✅ |
| Event mode | Navigate to /event | ✅ |

**Regressions found:** None / [describe if any]
```

**If regression found:**
- STOP closure process
- Fix the regression
- Re-run /verify-feature
- Then continue with closure
```

**Quality Gate Addition:**
```markdown
**Cross-Feature Validation:**
- [ ] Files modified listed
- [ ] Related features identified (using table)
- [ ] Each related feature quick-tested
- [ ] No regressions found (or fixed before proceeding)
- [ ] Results documented
```

---

### 3.3 README Update

**Location:** `README.md`
**Section:** Quick Start (Local Development)

**Replace existing Quick Start section with:**
```markdown
## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

### One-Command Setup

```bash
# Clone and enter directory
cd web-app

# Run setup (creates venv, installs deps, seeds DB, starts server)
./scripts/dev.sh
```

**That's it!** Open http://localhost:8000

### Test Accounts
- `admin@battle-d.com` (Admin)
- `staff@battle-d.com` (Staff)
- `mc@battle-d.com` (MC)

Magic links print to console - copy/paste the URL to log in.

### Manual Setup (if preferred)

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed test accounts
python seed_db.py

# Start server
uvicorn app.main:app --reload
```
```

---

## 4. Testing Plan

### 4.1 Test scripts/dev.sh

**Manual testing checklist:**
- [ ] Fresh clone: Script creates venv, installs deps, runs migrations, seeds DB, starts server
- [ ] Second run: Script detects existing setup, starts server quickly
- [ ] Login flow: Magic link prints to console, can copy/paste to log in
- [ ] All test accounts work: admin, staff, mc

### 4.2 Test Slash Command Updates

**Verification (visual inspection):**
- [ ] Pattern scan section appears in /analyze-feature
- [ ] POC section appears in /plan-implementation
- [ ] Browser test is marked MANDATORY in /verify-feature
- [ ] Cross-feature check appears in /close-feature
- [ ] Quality gates include new checkboxes

---

## 5. Risk Analysis

### Risk 1: Script Fails on Different OS
**Concern:** `sed` command differs between macOS and Linux
**Likelihood:** Medium
**Mitigation:** Script includes OS detection with platform-specific sed syntax

### Risk 2: uv Not Installed
**Concern:** Developer doesn't have uv installed
**Likelihood:** Medium
**Mitigation:** Script checks for uv and provides install instructions

### Risk 3: Port 8000 Already in Use
**Concern:** Another process using port 8000
**Likelihood:** Low
**Impact:** Server fails to start with clear error message
**Mitigation:** Error message from uvicorn is self-explanatory

### Risk 4: Database Migration Fails
**Concern:** Alembic migration might fail on fresh setup
**Likelihood:** Low (migrations are tested)
**Mitigation:** Error will be visible in terminal output

---

## 6. Implementation Order

| # | Task | Complexity | Depends On |
|---|------|------------|------------|
| 1 | Create `scripts/dev.sh` | Low | Nothing |
| 2 | Test dev.sh on fresh setup | Low | Task 1 |
| 3 | Update README Quick Start | Low | Task 2 |
| 4 | Update `/analyze-feature.md` | Low | Nothing |
| 5 | Update `/plan-implementation.md` | Low | Nothing |
| 6 | Update `/verify-feature.md` | Low | Task 1 |
| 7 | Update `/close-feature.md` | Low | Nothing |

**Recommended sequence:**
1. Create and test dev.sh first (enables browser testing)
2. Update README to point to new script
3. Update slash commands (order doesn't matter)

---

## 7. Deliverables Checklist

### Deliverable 1: Local Dev Setup
- [ ] `scripts/dev.sh` created and executable
- [ ] Script tested on fresh setup
- [ ] README Quick Start updated

### Deliverable 2: Slash Command Updates
- [ ] `/analyze-feature.md` - Pattern Scan step added
- [ ] `/plan-implementation.md` - Technical POC step added
- [ ] `/verify-feature.md` - Browser test made MANDATORY
- [ ] `/close-feature.md` - Cross-feature check added

---

## 8. User Approval

- [ ] Implementation approach approved
- [ ] dev.sh script design approved
- [ ] Slash command changes approved
- [ ] Ready for /implement-feature
