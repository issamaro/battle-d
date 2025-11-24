# Battle-D Glossary
**Level 0: Meta - Navigation & Reference** | Last Updated: 2025-11-24

**Purpose:** Definitions of key terms used throughout the project documentation

---

## Tournament Structure

### Tournament
A competition event containing one or more categories. A tournament progresses through 5 phases in sequence: Registration → Preselection → Pools → Finals → Completed.

### Category
A competition division within a tournament, defined by dance style and format (e.g., "Hip Hop 1v1", "Breaking Duo 2v2"). Each category has its own set of performers, pools, and battles.

### Phase
A stage in the tournament lifecycle. Phases progress sequentially and cannot be skipped:
1. **Registration** - Dancers sign up for categories
2. **Preselection** - Initial elimination round to qualify for pools
3. **Pools** - Group stage with round-robin battles
4. **Finals** - Bracket elimination to determine champion
5. **Completed** - Tournament finished, results locked

---

## People

### User
A system account with login credentials (via magic link). Users have roles: Admin, Staff, MC, or Judge.

### Dancer
A real person who competes in battles. Dancers do NOT have system accounts - they are registered by Staff. A dancer has a "blaze" (stage name) and real name.

### Performer
A dancer registered in a specific tournament category. The same dancer becomes a new "performer" each time they register for a category. Performers have tournament-specific stats (preselection score, pool points).

### Blaze
A dancer's stage name or artist name (e.g., "B-Boy Storm", "Crazy Legs"). Must be unique across all dancers.

### Judge (V2 Only)
A temporary user account for scoring battles. In V1, Staff/Admin encodes results instead.

### MC (Master of Ceremonies)
A user role responsible for running battles during events - starting battles, managing flow.

---

## Competition Mechanics

### Preselection
The mandatory elimination phase after registration. All registered performers compete; lowest-scoring performers are eliminated. Top performers advance to pools.

### Pool
A group of performers who compete against each other in round-robin format during the Pools phase. Each category has multiple pools (minimum 2, maximum 10).

### Pool Points
Points accumulated by a performer during pool battles. Used to rank performers within their pool and determine who advances to finals.

### Tiebreak Battle
A special battle to resolve ties. Used when performers have equal scores at critical cutoff points (preselection qualification, pool winners).

### Round-Robin
A format where every performer in a pool battles every other performer exactly once.

### Finals Bracket
The elimination bracket for the Finals phase. Pool winners from each pool compete in single-elimination format until a champion is determined.

---

## Scoring

### Preselection Score
A score assigned to each performer during preselection (1-10 scale). Determines who advances to pools.

### Battle Outcome
The result of a battle: which performer won, and the score (e.g., 3-2 means winner won 3 rounds to 2).

### Encode (V1)
The act of Staff/Admin manually entering the winner of a battle. Used in V1 before Judge scoring interface exists.

---

## Technical Terms

### Magic Link
A passwordless authentication method. Users receive an email with a unique link that logs them in. Links expire after 5 minutes.

### Groups Ideal
The target number of pools for a category. Set when creating the category. Affects minimum performer requirements.

### Minimum Performers Formula
`(groups_ideal × 2) + 1` - The minimum number of performers required to run a category. Ensures at least 2 performers per pool plus 1 for elimination.

### Duo Partner
In 2v2 categories, each performer has a `duo_partner_id` linking them to their teammate.

---

## Status Values

### Tournament Status
- **CREATED** - Tournament is being set up, not yet active
- **ACTIVE** - Tournament is running (only one can be active)
- **COMPLETED** - Tournament finished, results locked

### Battle Status
- **PENDING** - Battle not yet started
- **IN_PROGRESS** - Battle currently happening
- **COMPLETED** - Battle finished, winner recorded

---

## V1 vs V2

### V1 (Current)
The initial version without judge accounts. Staff/Admin encodes battle results manually.

### V2 (Future)
The enhanced version with judge accounts. Judges score battles independently via their own interface (blind scoring).

---

## Related Documents

- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Full entity definitions and business rules
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - Constraints and validation logic
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Document navigation
