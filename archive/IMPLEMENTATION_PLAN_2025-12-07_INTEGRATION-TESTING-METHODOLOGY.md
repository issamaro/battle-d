# Implementation Plan: Integration Testing Methodology Improvement

**Date:** 2025-12-07
**Phase:** 3.4 (Methodology Improvement)
**Status:** Ready for Implementation

---

## Summary

Update the development methodology to prescribe service integration tests as the primary testing pattern for services, replacing the current over-mocked unit test pattern.

---

## Files to Modify

### 1. `.claude/commands/implement-feature.md`

**Location:** Step 13 (Writing Tests)

**Changes:**
1. Replace Step 13.1 "Unit Tests (Service Layer)" with "Service Integration Tests (Primary)"
2. Add Step 13.2 "Unit Tests (Optional - Isolated Logic Only)"
3. Update Quality Gate to require integration tests

**Before (Step 13.1):**
```python
@pytest.mark.asyncio
async def test_filter_battles_by_encoding_status_pending(battle_service, battle_repo):
    # Setup - MOCK THE REPO
    battle_repo.get_by_filters.return_value = [mock_battle_1, mock_battle_2]
    ...
```

**After (Step 13.1):**
```python
@pytest.mark.asyncio
async def test_filter_battles_integration(async_session_maker):
    """Integration test: filter battles with real DB."""
    async with async_session_maker() as session:
        # Real repositories
        battle_repo = BattleRepository(session)
        service = BattleService(battle_repo)

        # Create REAL test data
        battle = Battle(status=BattleStatus.PENDING, ...)
        await battle_repo.create(battle)

        # Test against REAL DB
        result = await service.filter_battles(...)
        assert len(result) == expected
```

**Quality Gate Addition:**
```markdown
- [ ] Service integration tests written (real repos, real DB)
- [ ] Integration tests verify database state after operations
```

---

### 2. `.claude/commands/verify-feature.md`

**Location:** Quality Gate section

**Changes:**
Add new "Integration Testing" section to quality gate.

**Addition after "Automated Testing:":**
```markdown
**Integration Testing (Services):**
- [ ] Service integration tests exist for new service methods
- [ ] Integration tests use real repositories (not mocks)
- [ ] Integration tests create real test data in DB
- [ ] Integration tests verify actual database state
```

---

### 3. `TESTING.md`

**Location:** After "Unit Tests (Current - Phase 0)" section

**Changes:**
Add new "Service Integration Tests" section with:
- Explanation of why integration tests are primary
- Pattern/template for service integration tests
- Example test code
- When to use mocked unit tests vs integration tests

**New Section:**
```markdown
### Service Integration Tests (Primary for Services)

Service integration tests are the **primary test type** for service methods.
Unlike unit tests with mocked repositories, integration tests catch bugs like:
- Invalid enum references (e.g., BattleStatus.IN_PROGRESS doesn't exist)
- Repository method signature mismatches
- Lazy loading and relationship issues
- Transaction/session management bugs

**Why Integration Tests First:**
Mocked unit tests only verify that code *calls* dependencies correctly.
Integration tests verify that code *works* with real dependencies.

**Pattern:**
```python
@pytest.mark.asyncio
async def test_service_method_integration(async_session_maker):
    """Integration test description."""
    async with async_session_maker() as session:
        # 1. Create real repositories
        repo = SomeRepository(session)
        service = SomeService(repo)

        # 2. Create real test data with real enum values
        entity = Entity(status=EntityStatus.PENDING)  # Real enum!
        await repo.create(entity)

        # 3. Execute service method
        result = await service.some_method(entity.id)

        # 4. Verify actual behavior and DB state
        assert result.success
        updated = await repo.get_by_id(entity.id)
        assert updated.status == EntityStatus.COMPLETED
```

**When to Use Mocked Unit Tests:**
- Pure calculation functions (no DB)
- Complex branching logic worth isolating
- External API calls (mock the API, not the repo)
```

---

### 4. `.claude/README.md`

**Location:** Test Structure Templates section (around line 2492)

**Changes:**
1. Rename "Unit Test Template (Service Layer)" to "Service Integration Test Template (Primary)"
2. Add "Unit Test Template (Optional - Isolated Logic)" as secondary
3. Update examples to show integration pattern first

**Replace current template with:**
```python
### Service Integration Test Template (Primary)

"""Service integration tests use real repositories and database."""

@pytest.mark.asyncio
async def test_create_example_integration(async_session_maker):
    """Integration test for example creation."""
    async with async_session_maker() as session:
        # Real repository
        repo = ExampleRepository(session)
        service = ExampleService(repo)

        # Execute with real DB
        result = await service.create_example(name="Test", value=10)

        # Verify actual state
        assert result.success
        assert result.data.id is not None

        # Verify DB state
        saved = await repo.get_by_id(result.data.id)
        assert saved.name == "Test"


### Unit Test Template (Optional - Isolated Logic Only)

"""Use mocked unit tests ONLY for pure logic without DB interaction."""

def test_calculate_minimum_performers():
    """Unit test for pure calculation (no DB)."""
    result = calculate_minimum_performers(groups_ideal=3)
    assert result == 7  # (3 * 2) + 1
```

---

## Testing Approach

Since this is a documentation-only change:
- No code tests required
- Verify grep consistency after changes
- Manual review of updated documentation

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Existing tests may need updates | This change is methodology only; existing tests continue to work |
| Developers may resist pattern change | Clear explanation of WHY in TESTING.md |

---

## Success Criteria

1. `/implement-feature` shows integration test example first
2. `/verify-feature` has integration test quality gate
3. `TESTING.md` has "Service Integration Tests" section
4. `README.md` templates show integration tests as primary

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Update implement-feature.md | 15 min |
| Update verify-feature.md | 10 min |
| Update TESTING.md | 20 min |
| Update README.md | 15 min |
| **Total** | ~1 hour |

