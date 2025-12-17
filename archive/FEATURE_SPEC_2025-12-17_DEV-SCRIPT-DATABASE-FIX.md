# Feature Specification: dev.sh Database Initialization Fix

**Date:** 2025-12-17
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Pattern Scan Results](#3-pattern-scan-results)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)

---

## 1. Problem Statement

Developers cannot successfully run `./scripts/dev.sh` to set up a local development environment because the database seeding fails with "no such table: users" error, even though migrations appear to run successfully.

---

## 2. Executive Summary

### Scope
This analysis covers the dev.sh script's database initialization and seeding process, specifically investigating why the `users` table is not found after migrations run.

### What Works
| Feature | Status |
|---------|--------|
| Virtual environment creation | Production Ready |
| Dependency installation | Production Ready |
| .env file creation from template | Production Ready |
| Alembic migrations execution (command runs) | Partial |
| Directory creation (`mkdir -p data`) | Production Ready |

### What's Broken
| Issue | Type | Location |
|-------|------|----------|
| DATABASE_URL override in .env | BUG | .env:10-13 |
| Dev script doesn't validate database path | GAP | scripts/dev.sh:58 |
| Misleading echo messages | GAP | scripts/dev.sh:61 vs seed_db.py:57 |

### Key Business Rules Defined
- **BR-DEV-001:** Local development must use relative database path `./data/battle_d.db`
- **BR-DEV-002:** Production must use absolute path `/data/battle_d.db` (Railway volume mount)
- **BR-DEV-003:** Developer should be able to run a single command to set up local environment

---

## 3. Pattern Scan Results

**Pattern searched:** Duplicate/conflicting DATABASE_URL definitions and .env file handling

**Search command:**
```bash
grep -rn "DATABASE_URL" .
grep -rn "\.env" scripts/
```

**Results:**
| File | Line | Description |
|------|------|-------------|
| .env | 10 | Local dev DATABASE_URL (correct) |
| .env | 13 | Production DATABASE_URL (SHOULD BE COMMENTED OUT) |
| .env.example | 9 | Local dev DATABASE_URL |
| .env.example | 12 | Production DATABASE_URL (correctly commented out) |

**Root Cause:**
The user's `.env` file has two `DATABASE_URL` lines, both uncommented:
```
DATABASE_URL=sqlite:///./data/battle_d.db    # Line 10 - LOCAL
DATABASE_URL=sqlite:////data/battle_d.db    # Line 13 - PRODUCTION (overwrites!)
```

The second line overwrites the first. Environment variables don't support multiple assignments - the last one wins. This causes:
1. Migrations run against `/data/battle_d.db` (absolute path, likely doesn't exist or requires sudo)
2. Seeding tries to use `/data/battle_d.db` which has no tables
3. Error: "no such table: users"

**Decision:**
- [x] Fix the immediate issue (comment out production DATABASE_URL in .env)
- [ ] Improve dev.sh script to prevent this issue in the future

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Local Development Setup

**Business Rule BR-DEV-001: Single Command Setup**
> A developer should be able to run `./scripts/dev.sh` and have a fully functional local development environment with test accounts ready to use.

**Acceptance Criteria:**
```gherkin
Feature: Local Development Setup
  As a developer
  I want to run a single command to set up my local environment
  So that I can start developing quickly without manual configuration

Scenario: Fresh setup on new machine
  Given the developer has uv installed
  And no .env file exists
  And no data/battle_d.db file exists
  When the developer runs ./scripts/dev.sh
  Then the virtual environment is created
  And dependencies are installed
  And .env is created from .env.example with correct local DATABASE_URL
  And database migrations are applied to ./data/battle_d.db
  And test accounts (admin, staff, mc) are seeded
  And the development server starts at http://localhost:8000

Scenario: Setup with existing .env containing production DATABASE_URL
  Given the developer has a .env file with production DATABASE_URL
  When the developer runs ./scripts/dev.sh
  Then the script should warn about incorrect DATABASE_URL
  Or the script should use the correct local path regardless of .env

Scenario: Setup after previous failed run
  Given a previous dev.sh run failed during seeding
  When the developer runs ./scripts/dev.sh again
  Then the script should recover gracefully
  And create/migrate the database if needed
  And seed only missing accounts
```

### 4.2 Database URL Configuration

**Business Rule BR-DEV-002: Environment-Specific Database Paths**
> Local development must use a relative path (`./data/battle_d.db`) while production uses an absolute path (`/data/battle_d.db` for Railway volume mount).

**Acceptance Criteria:**
```gherkin
Feature: Database URL Configuration
  As a developer
  I want clear separation between local and production database paths
  So that I don't accidentally affect production data

Scenario: .env.example provides correct template
  Given a developer copies .env.example to .env
  When they don't modify DATABASE_URL
  Then the application uses ./data/battle_d.db (relative path)

Scenario: Production URL must be explicitly enabled
  Given the .env.example file
  Then the production DATABASE_URL line is commented out by default
  And contains clear documentation about when to use it
```

---

## 5. Current State Analysis

### 5.1 dev.sh Script Flow

**Current Workflow:**
```
1. Check for uv
2. Create .venv if needed
3. Activate .venv
4. Install dependencies
5. Create .env from .env.example if not exists
6. Create data/ directory
7. Run alembic upgrade head  <-- Uses DATABASE_URL from .env
8. Run seed_db.py            <-- Uses DATABASE_URL from .env
9. Start uvicorn server
```

**Issue:** Steps 7 and 8 both read DATABASE_URL from `.env`. If `.env` has the production URL active, both will target `/data/battle_d.db` instead of `./data/battle_d.db`.

### 5.2 .env File Issue

**Evidence from .env (lines 9-14):**
```
# Database
# Local development (relative path)
DATABASE_URL=sqlite:///./data/battle_d.db

# Railway production (absolute path)
DATABASE_URL=sqlite:////data/battle_d.db    <-- THIS OVERWRITES ABOVE!
```

The user's `.env` file does NOT follow the `.env.example` pattern. In `.env.example`, line 12 is commented out:
```
# DATABASE_URL=sqlite:////data/battle_d.db
```

### 5.3 Script Output Analysis

**User's output shows:**
```
🗄️  Initializing database...
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
🌱 Seeding test accounts...
🌱 Seeding database...
```

**Critical observation:** Alembic reports "Will assume non-transactional DDL" but NO migration versions are shown being applied. This suggests:
1. Either all migrations were already applied (to `/data/battle_d.db`)
2. Or the database file doesn't exist and tables weren't created

Given the error "no such table: users", option 2 is confirmed - the migrations either failed silently or created tables at the wrong location.

---

## 6. Implementation Recommendations

### 6.1 Critical (Immediate Fix)

1. **Fix the .env file** - Comment out the production DATABASE_URL line:
   ```bash
   # In .env, change line 13 from:
   DATABASE_URL=sqlite:////data/battle_d.db
   # To:
   # DATABASE_URL=sqlite:////data/battle_d.db
   ```

### 6.2 Recommended (Prevent Recurrence)

1. **Add DATABASE_URL validation to dev.sh** - Check if DATABASE_URL points to an absolute path and warn the user:
   ```bash
   # After sourcing .env or creating it
   if grep -q "DATABASE_URL=sqlite:////data" .env 2>/dev/null; then
       echo "⚠️  Warning: .env contains production DATABASE_URL"
       echo "   For local development, comment out line: DATABASE_URL=sqlite:////data/battle_d.db"
   fi
   ```

2. **Force local DATABASE_URL in dev.sh** - Override the environment variable for local development:
   ```bash
   export DATABASE_URL="sqlite:///./data/battle_d.db"
   ```

3. **Add migration verification** - After running migrations, verify tables exist:
   ```bash
   # After alembic upgrade head
   if ! .venv/bin/python -c "import sqlite3; c=sqlite3.connect('./data/battle_d.db'); c.execute('SELECT 1 FROM users LIMIT 1')" 2>/dev/null; then
       echo "❌ Error: Database tables not created properly"
       echo "   Check your DATABASE_URL in .env"
       exit 1
   fi
   ```

4. **Consolidate echo messages** - Remove confusing duplicate "Seeding" messages:
   - Change `scripts/dev.sh:61` from "🌱 Seeding test accounts..." to "🌱 Initializing test data..."
   - Or remove the echo from `seed_db.py:57` since the script already announces it

### 6.3 Nice-to-Have (Future)

1. **Add a --reset flag** to dev.sh to completely wipe and recreate the database
2. **Add a --check flag** to verify the setup without making changes
3. **Create a separate scripts/reset-db.sh** for database-only operations

---

## Appendix: Quick Fix Command

For the user to immediately fix their issue:

```bash
# Option 1: Edit .env to comment out production DATABASE_URL
# Change line 13 from:
#   DATABASE_URL=sqlite:////data/battle_d.db
# To:
#   # DATABASE_URL=sqlite:////data/battle_d.db

# Option 2: Delete .env and let dev.sh recreate it
rm .env
rm -rf data/
./scripts/dev.sh
```
