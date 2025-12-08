# Change Log: Fix Command Center Missing Progress Variable

**Date:** 2025-12-08
**Feature:** FIX-COMMAND-CENTER-MISSING-PROGRESS
**Status:** In Progress

---

## Changes Made

### 1. app/routers/event.py

**Change:** Add `progress` and `queue` variables to `command_center()` route template context

**Before (lines 90-109):**
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

**After:**
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

**Reason:** The template `command_center.html` includes `_phase_progress.html` which expects a `progress` variable, and `_battle_queue.html` which expects a `queue` variable. These were missing from the route context, causing a 500 Server Error.

---

## Test Results

Pending...

---

## Notes

- Services already exist and work correctly in HTMX partial routes
- No template changes needed
- No database changes needed
