# Implementation Plan: Fix Command Center Missing Progress Variable

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_FIX-COMMAND-CENTER-MISSING-PROGRESS.md

---

## 1. Summary

**Feature:** Fix 500 error on Event Command Center by adding missing `progress` and `queue` variables to template context
**Approach:** Add two service calls in `command_center()` route to fetch `progress` and `queue`, then pass them to the template

---

## 2. Affected Files

### Backend
**Models:**
- No changes needed

**Services:**
- No changes needed (services already exist and work correctly)

**Repositories:**
- No changes needed

**Routes:**
- `app/routers/event.py`: Add `progress` and `queue` to `command_center()` route context

**Validators:**
- No changes needed

**Utils:**
- No changes needed

### Frontend
**Templates:**
- No changes needed (templates already expect these variables)

**Components:**
- No changes needed

**CSS:**
- No changes needed

### Database
**Migrations:**
- No changes needed

### Tests
**New Test Files:**
- None needed

**Updated Test Files:**
- `tests/test_event_service_integration.py`: Add test to verify route passes all required context variables

### Documentation
**Level 1:**
- No changes needed

**Level 2:**
- No changes needed

**Level 3:**
- No changes needed

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**No database changes required.**

### 3.2 Service Layer Changes

**No service changes required.** The services already exist:
- `event_service.get_phase_progress(tournament_uuid)` - returns `PhaseProgress`
- `event_service.get_battle_queue(tournament_uuid, category_uuid)` - returns `List[QueueItem]`

### 3.3 Route Changes

**Router:** `app/routers/event.py`
**Method:** `command_center()` (lines 23-109)

**Current Code (lines 90-108):**
```python
# Get command center context
context = await event_service.get_command_center_context(
    tournament_uuid, category_uuid
)

# Get active tournament for template (same as current)
active_tournament = tournament

return templates.TemplateResponse(
    request=request,
    name="event/command_center.html",
    context={
        "current_user": user,
        "context": context,
        "tournament": tournament,
        "active_tournament": active_tournament,
        "category_filter": category_uuid,
        "flash_messages": flash_messages,
    },
)
```

**New Code:**
```python
# Get command center context
context = await event_service.get_command_center_context(
    tournament_uuid, category_uuid
)

# Get phase progress for progress bar
progress = await event_service.get_phase_progress(tournament_uuid)

# Get battle queue
queue = await event_service.get_battle_queue(tournament_uuid, category_uuid)

# Get active tournament for template (same as current)
active_tournament = tournament

return templates.TemplateResponse(
    request=request,
    name="event/command_center.html",
    context={
        "current_user": user,
        "context": context,
        "tournament": tournament,
        "active_tournament": active_tournament,
        "category_filter": category_uuid,
        "flash_messages": flash_messages,
        "progress": progress,
        "queue": queue,
    },
)
```

**Changes:**
1. Add call to `event_service.get_phase_progress(tournament_uuid)`
2. Add call to `event_service.get_battle_queue(tournament_uuid, category_uuid)`
3. Add `"progress": progress` to context
4. Add `"queue": queue` to context

---

## 4. Frontend Implementation Plan

**No frontend changes required.** The templates already expect these variables:
- `_phase_progress.html` expects `progress`
- `_battle_queue.html` expects `queue`

---

## 5. Documentation Update Plan

**No documentation changes required.** This is a bug fix, not a new feature.

---

## 6. Testing Plan

### Integration Test

**File:** `tests/test_event_service_integration.py`

**New Test:**
```python
@pytest.mark.asyncio
async def test_command_center_route_passes_all_context_variables():
    """Verify command_center() route passes all required template variables.

    This test verifies the fix for the 500 error caused by missing 'progress'
    and 'queue' variables in the template context.
    """
    # This would require creating a tournament in event phase via HTTP
    # and verifying the response contains all expected elements
    #
    # Note: Due to database session isolation between async fixtures and
    # TestClient, this test should use the service integration approach:
    # verify the route's context building logic separately
```

**Alternative Approach (Recommended):**
Since E2E tests have database session isolation issues, add a focused unit test that mocks the service and verifies the route calls all required methods.

### Manual Testing Checklist

- [ ] Start dev server: `./scripts/dev.sh`
- [ ] Create a tournament and advance to PRESELECTION phase
- [ ] Navigate to `/event/{tournament_id}`
- [ ] Verify page loads without 500 error
- [ ] Verify progress bar displays
- [ ] Verify battle queue displays
- [ ] Verify current battle section displays

---

## 7. Risk Analysis

### Risk 1: Performance Impact
**Concern:** Adding two more service calls per request
**Likelihood:** Low
**Impact:** Low (these are simple DB queries)
**Mitigation:**
- Both queries are already optimized
- Same queries run in HTMX partials without issues
- Total additional time: <50ms

### Risk 2: Breaking Existing HTMX Functionality
**Concern:** Adding variables might affect HTMX partial behavior
**Likelihood:** Very Low
**Impact:** Low
**Mitigation:**
- HTMX partials use their own routes (not affected)
- Variables are only added to main page load
- No template changes needed

---

## 8. Technical POC

**Status:** Not required
**Reason:** Simple bug fix - adding two service calls and passing results to template. Both services are already proven in HTMX partial routes.

---

## 9. Implementation Order

**Recommended sequence (~15 minutes total):**

1. **Fix Route** (~5 minutes)
   - Add two service calls in `command_center()`
   - Add variables to template context

2. **Manual Test** (~5 minutes)
   - Start dev server
   - Navigate to command center
   - Verify no 500 error
   - Verify all sections render

3. **Run Test Suite** (~5 minutes)
   - Run `pytest` to ensure no regressions
   - All 460+ tests should pass

4. **Commit and Deploy**

---

## 10. Open Questions

- [x] Should we add an E2E test? → Challenging due to database session isolation. Manual testing + existing service integration tests provide sufficient coverage.
- [x] Are there other routes with similar issues? → Pattern scan found no other affected routes.

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
