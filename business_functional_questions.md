# Business & Functional Questions: Projection Interface

**Created:** 2025-11-30
**Purpose:** Business analysis to clarify Phase 4 requirements before documentation/implementation
**Perspective:** User Experience first (Steve Jobs thinking)

---

## Executive Summary

The **Projection Interface** is for **the audience** - dancers waiting their turn, spectators, supporters in the venue. This is not a staff tool. It's a **public-facing experience** that answers one question:

> **"What's happening right now, and what's coming next?"**

Current documentation has **critical gaps** in understanding the audience's needs and context. This document identifies what's missing from a UX perspective.

---

## Part 1: Terminology Clarification

### Problem: Technical Jargon Doesn't Serve Audiences

**Current Terms (from docs):**
- "Bracket" - GLOSSARY.md line 65-66: "elimination bracket for Finals phase"
- "Standing" - Found in code (ARCHITECTURE.md lines 592-610): pool rankings table
- "Projection" - Not defined anywhere

**What does the AUDIENCE understand?**
- ❌ "Bracket" - Sports term, not universal (user confirmed: "I don't know bracket")
- ❌ "Standing" - Passive, unclear ("Am I standing? Is someone standing?")
- ❌ "Projection screen" - Technical term staff use

**Steve Jobs Question:** *"If my mom walked into this venue, what would she call what she sees?"*

### Proposed Audience-Friendly Terms

**Instead of "Bracket" →**
- **Option A: "Championship Path"** - Shows the journey to champion
- **Option B: "Finals Tree"** - Visual metaphor everyone understands
- **Option C: "Road to Victory"** - Inspirational, clear goal
- **Recommendation:** **"Championship Path"** - Clear, aspirational, universal
**Response:** **"Finals Tree"** - I don't understand at first what Bracket means in the app so I don't know what term is most suitable as a replacement.

**Instead of "Standing" →**
- **Option A: "Rankings"** - Everyone knows what this means
- **Option B: "Leaderboard"** - Gaming/competition term, modern
- **Option C: "Scoreboard"** - Sports term, familiar
- **Recommendation:** **"Rankings"** - Simplest, most direct
**Response:** **"Can't choose"** - I don't understand at first what Standing means in the app so I don't know what term is most suitable as a replacement.


**Instead of "Projection" →**
- **Option A: "Live Display"** - Describes what it does
- **Option B: "Tournament Board"** - Like airport departure boards
- **Option C: "Big Screen"** - What audience calls it anyway
- **Recommendation:** **"Live Display"** - Functional, clear
**Response:** **"Live Display"** - I clearly understand that we are talking about the projection screen for the audience, and that it's live.

**User's Term: "Matchmaking"**
- User described it as: "a table consisting of finished, to come, active matches"
- **Excellent!** This is **battle queue** from audience perspective
- **Recommendation:** Use **"Match Schedule"** or **"Battle Schedule"**
  - Shows: What finished, what's active, what's coming
  - Like a train/flight departure board everyone understands
**Response:** **"Battle Schedule"** - I clearly understand that we are talking about the battle matchmaking consisting of all the battles for PRESELECTION, POOLS, and FINALS phases.

---

## Part 2: What Does the Audience Actually Need?

### The Audience Context

**Who is watching?**
1. **Dancers waiting** - Need to know when they battle
2. **Supporters** - Want to watch their friend/crew member
3. **General spectators** - Want to see exciting battles
4. **Tournament organizers** - Want smooth, professional presentation

**What's their mental model?**
- ❌ NOT: "I want to see pool standings with W-D-L calculations"
- ✅ YES: "Is my friend dancing now? When's their next battle?"

**What environment are they in?**
- Loud music playing
- People moving around
- Might glance at screen briefly (5-10 seconds)
- Can't read small text from 20 feet away
- Expect immediate clarity (like airport screens)

### Critical UX Questions (MISSING from docs)

#### Q1: What's the Primary Use Case?

**Scenario 1: Someone walks up to the screen mid-tournament**
- What do they see first?
- Can they immediately understand: "What's happening NOW?"
- Can they find: "When does [dancer name] compete?"

**Current docs show:** 4 different views (battle, queue, rankings, championship path)

**UX Problem:** Which view is default? How do they switch? Do they even need to switch?

**Recommendation:**
- **Default view should answer: "What's happening RIGHT NOW?"**
- If battle ACTIVE → Show battle
- If NO active battle → Show upcoming battles (match schedule)
- Rankings/championship path should be **secondary** (not everyone cares)

**Response**
- The current UX is not optimized, don't take it into account.
- I want to see the battle schedule, with the current one highlighted in some way, what were the ones before, and what's the upcoming battles. This way I can know whether my battle: has already passed, is the current one, or is upcoming.

---

#### Q2: What Does "Match Schedule" (Your "Matchmaking") Actually Show?

**From audience perspective:**

```
UPCOMING BATTLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 NOW BATTLING
   B-Boy Storm vs Crazy Legs
   Pool A • Battle 5 of 12

⏰ UP NEXT
   Phoenix vs Thunder
   Pool A • Battle 6 of 12

📋 COMING SOON
   - B-Girl Fierce vs Lady Boom (Pool A, Battle 7)
   - Flex vs Twist (Pool B, Battle 3)
   - [more...]

✅ RECENTLY FINISHED
   - Breaker vs Spinner → Breaker won
   - Flash vs Boom → Flash won
```

**Questions:**
1. How many "coming soon" battles to show? (3? 5? 10?)
2. Show all categories mixed, or one category at a time?
3. When tournament has 50+ pending battles, what's relevant to show?
4. Should it auto-scroll if list is long?

**Recommendation:**
- Show **current + next 5-7 upcoming**
- Group by category if multiple (with category headers)
- Recently finished: Last 2-3 only (audience already saw them)

**Response**
- I would go this way (see example below), with the 3 previous battles, the current one (now battling), the battle to come, and the 3 coming soon.
- We don't group by category since the battle schedule mix all the battles up regardless of the category they belong to.
- In that sense, battle order is chronological (BAttle 1, then Battle 2, ...). See the example below.
- Side quest: in the glossary.md file, we should add examples with sentences contextualizing the terms.
```
UPCOMING BATTLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ RECENTLY FINISHED
   - Breaker vs Spinner → Breaker won
   - Flash vs Boom → Flash won

🔴 NOW BATTLING
   B-Boy Storm vs Crazy Legs
   Pool A • Battle 5 of 12

⏰ UP NEXT
   Phoenix vs Thunder
   Pool B • Battle 6 of 12

📋 COMING SOON
   - B-Girl Fierce vs Lady Boom (Pool A, Battle 7)
   - Flex vs Twist (Pool B, Battle 8)
   - [more...]
```

---

#### Q3: When Do People Actually Need "Rankings"?

**Business insight from DOMAIN_MODEL.md:**
- Pools phase: Round-robin, everyone battles everyone
- Rankings determine who advances to finals
- **Key moment:** End of pools, to see who qualified

**UX insight:**
- **During pools:** Rankings change after every battle → not very meaningful to show constantly
- **After pools complete:** Rankings = who advances → VERY important to show

**Questions:**
1. Should rankings show during pools? Or only when pools complete?
2. If showing during pools, how often to update? (Constantly changing)
3. What if someone is watching mid-pools? Do they care about current rankings?

**Recommendation:**
- **During pools:** Rankings are **secondary** info (not main screen)
- **After pools complete:** Rankings become **primary** (show advancement)
- **Visual distinction:** Highlight performers who qualified for finals

**Response**
- **During pools:** The current battle schedule is the most important, but next to it should be displayed the rankings so we keep track of who might be the winner. It rises tension. The issue here is that the rankings are category-wide, so the rankings should always be updated to show the category's ranking for the current battle.
- **After pools complete:** Show the rankings for all the categories.
- **Visual distinction:** Highlight performers who qualified (or might be qualified) for finals

---

#### Q4: What's "Finals tree" (Finals) For?

**Business insight from DOMAIN_MODEL.md:**
- Finals: Pool winners compete in elimination format
- 2 pools → 1 finals battle (A winner vs B winner)
- More than 2 pools → "bracket system (not yet defined)" (line 462).

**Current system:** Supports 2 pools only (DOMAIN_MODEL says >2 pools "not yet defined")

**UX questions:**
1. With 2 pools only, is "championship path" just... showing 1 battle? -> YES, 1 battle per category.
2. What does audience see during finals phase?
   - Before finals battle → "Finals coming soon, pool winners are X and Y"?
   - During finals battle → Same as regular battle view?
   - After finals → Champion announcement?
**Response:** finals phase should show the battle schedule consisting of all the final battles since there will be one final per category. Order is randomized.

**Recommendation:**
- **For 2-pool scenario (V1):**
  - No complex visualization needed -> OK
  - Show: "FINALS: [Winner A] vs [Winner B]" with their pool origins -> No need of the pool origin, just specify the category.
  - If already battled → Show champion with celebration -> OK
- **Championship Path view only useful if >2 pools** (deferred to later phase)

---

#### Q5: What About Multi-Category Tournaments?

**Business insight from DOMAIN_MODEL.md:**
- Tournament can have multiple categories (Hip Hop 1v1, Krump 2v2, etc.)
- Each category has own battles, pools, schedule

**Real-world scenario:**
```
Tournament: "Summer Battle 2024"
Categories:
  - Hip Hop 1v1 (16 dancers)
  - Breaking 2v2 (8 crews = 16 dancers)
  - Krump Open (12 dancers)
```

**UX Problem:**
- All 3 categories run in **same venue**, **same day**
- Battles happen **sequentially** (one at a time - DOMAIN_MODEL constraint line 489)
- Audience member might care about 1 category, or all 3

**Questions:**
1. Should live display show ALL categories mixed together? -> YES, see battle schedule builder (all battles from all categories are randomly mixed up)
2. Or show one category at a time and cycle through? -> NO
3. How does audience know which category the current battle is from? -> as Q3's response says:
   - "- **During pools:** The current battle schedule is the most important, but next to it should be displayed the rankings so we keep track of who might be the winner. It rises tension. The issue here is that the rankings are category-wide, so the rankings should always be updated to show the category's ranking for the current battle."
   - Beware: if it's the preselection, rankings should not be displayed, but category of the active battle should.
   - To make it general, for every battle, the category should be communicated as a real part of the battle's data that is displayed, not regardless of whether the battle's status.
4. What if someone only cares about Krump - do they have to watch Hip Hop battles scroll by? -> YES

**Current docs:** Completely silent on this

**Recommendation:**
**Option A: Category Tabs/Filter** (like airline departure board filtered by terminal)
- Show all by default
- Allow filtering by category (via URL parameter or physical tablet next to screen)
- Each battle clearly labeled with category

**Option B: Auto-Show Active Category Only**
- If current battle is Hip Hop → show Hip Hop schedule
- If current battle is Krump → show Krump schedule
- Automatically switches based on what's happening

**Option C: Split Screen (if venue has wide screen)**
- Left: Current battle
- Right: Full schedule across all categories

**Steve Jobs choice:** **Option B** - "The computer should do the thinking, not the user"

---

## Part 3: Empty States - What's Actually Possible?

### Business Rules Constraints (from DOMAIN_MODEL.md + code)

**Constraint 1:** Only ONE battle can be ACTIVE at a time (line 489)
**Constraint 2:** Only ONE tournament can be ACTIVE at a time (VALIDATION_RULES.md line 34)
**Constraint 3:** Tournament phases progress sequentially (line 500-503)

### State Analysis

#### State 1: No ACTIVE Tournament
**When:** No tournament set to ACTIVE status
**Projection should show:**
```
WELCOME TO BATTLE-D
════════════════════
No tournament currently running

Check back soon for upcoming events!
```
**UX Note:** This is like an airport screen when no flights scheduled

---

#### State 2: Tournament ACTIVE, Phase = REGISTRATION
**When:** Tournament setup, dancers still signing up
**Projection should show:**
```
SUMMER BATTLE 2024
══════════════════
Registration In Progress

Categories:
  • Hip Hop 1v1 — 12 dancers registered
  • Breaking 2v2 — 6 crews registered

Battles start soon!
```
**UX Note:** Builds anticipation, shows progress

---

#### State 3: Tournament ACTIVE, Phase = PRESELECTION/POOLS/FINALS, No Battles Created Yet
**When:** Admin advanced phase but hasn't generated battles
**Projection should show:**
```
PRESELECTION STARTING SOON
═══════════════════════════
Battles are being prepared...

Stay tuned!
```
**UX Note:** Transitional state, rare

---

#### State 4: Battles Exist, All PENDING (None Active)
**When:** Between battles, waiting for next to start
**Projection should show:**
```
NEXT UP
═══════
B-Boy Storm vs Crazy Legs
Pool A • Starting Soon

UPCOMING
─────────
[Schedule of next 5-7 battles]
```
**UX Note:** This is the "matchmaking/schedule" view - MOST COMMON STATE

---

#### State 5: One Battle ACTIVE
**When:** Battle happening right now
**Projection should show:**
```
NOW BATTLING
════════════
[Full battle display - two performers, scores when complete]
```
**UX Note:** This is the MOST IMPORTANT STATE - the action

---

#### State 6: All Battles in Phase COMPLETED, Waiting for Next Phase
**When:** All preselection/pool battles done, admin hasn't advanced yet
**Projection should show:**

For Preselection complete:
```
PRESELECTION RESULTS
════════════════════
Qualified for Pools:
  1. B-Boy Storm (9.2)
  2. Crazy Legs (8.8)
  [...]

Pool battles starting soon!
```

For Pools complete:
```
POOL RESULTS
════════════
Pool A Winner: B-Boy Storm (12 points)
Pool B Winner: Crazy Legs (9 points)

Finals coming up!
```

**UX Note:** Celebration + anticipation for next phase

---

#### State 7: Tournament Phase = COMPLETED
**When:** All battles finished, champion declared
**Projection should show:**
```
TOURNAMENT COMPLETE
═══════════════════
🏆 CHAMPIONS 🏆

Hip Hop 1v1: B-Boy Storm
Breaking 2v2: Crazy Legs & Phoenix
Krump Open: B-Girl Fierce

Thank you for watching!
```
**UX Note:** Final celebration screen

---

### States That DON'T Exist (System Constraints)

❌ **"Multiple battles active"** - Impossible (line 489 constraint)
❌ **"Tournament in undefined phase"** - Phases are enum, must be one of 5
❌ **"Battle stuck in limbo"** - Status is enum: PENDING, ACTIVE, or COMPLETED

---

## Part 4: The One Screen vs Multiple Views Dilemma

### Current Documentation Assumption
UI_MOCKUPS.md Section 13 shows **4 separate views:**
1. Battle View (13.1)
2. Rankings/Standings (13.2)
3. Battle Queue (13.3)
4. Championship Path/Bracket (13.4)

### UX Problem: Why 4 views?

**Steve Jobs question:** *"Why should the user think about which view to see?"*

**Analysis:**
- **Battle view:** Shows what's happening NOW (when battle active)
- **Queue view:** Shows what's happening NEXT (when no battle active)
- **Rankings:** Shows who's WINNING (only relevant end of pools or during finals)
- **Championship path:** Shows the JOURNEY (only relevant during/after finals with >2 pools)

**These aren't equal choices - they're context-dependent!**

### Recommendation: Intelligent Single View

**The computer decides what to show based on tournament state:**

```
IF battle is ACTIVE
  → Show Battle View

ELSE IF phase = PRESELECTION or POOLS
  IF any battles PENDING
    → Show Match Schedule (queue)
  ELSE (all battles in phase complete)
    → Show Rankings (who advanced/qualified)

ELSE IF phase = FINALS
  IF finals battle PENDING or ACTIVE
    → Show Finals Battle (with pool origins context)
  ELSE (finals complete)
    → Show Champion

ELSE IF phase = REGISTRATION
  → Show Registration Progress

ELSE IF phase = COMPLETED
  → Show Final Results + Champions

ELSE (no active tournament)
  → Show Welcome/Standby screen
```

**The audience never chooses - they always see what's most relevant.**

**Staff override:** Via URL parameter (`?view=rankings`) for testing or special display needs

---

## Part 5: What's Missing from Documentation

### Missing Business Logic

1. **Battle Duration Expectations**
   - How long does a battle last? (Impacts refresh rates, schedule predictions)
   - Not documented anywhere

2. **Tournament Timeline**
   - How long is registration phase? Hours? Days?
   - How long is preselection? (All battles same day? Multiple days?)
   - Impacts what "coming soon" means

3. **Category Execution Order**
   - Do all categories run in parallel? (NO - battles are sequential)
   - What order do battles happen across categories?
   - Who decides order? (MC? Auto-generated?)

4. **Performer Name Display**
   - Show real name or blaze? (GLOSSARY says dancers have both)
   - Current templates show "Performer 1" / "Performer 2" (encode forms)
   - Audience needs to see blazes (stage names)

5. **2v2 Battle Display**
   - Duo partners battle together (DOMAIN_MODEL line 510)
   - How to show on screen? "Storm & Thunder vs Boom & Flash"?
   - Needs different layout than 1v1

### Missing UX Specifications

1. **Font Sizes for Distance Viewing**
   - Audience 20-50 feet from screen
   - Current UI_MOCKUPS shows font-size: 1.5rem, 2rem (too small!)
   - Recommendation: Minimum 4rem (64px) for names, 6rem+ for scores

2. **Color Accessibility**
   - Venue lighting varies (bright stage lights, dark audience)
   - High contrast essential
   - Current mockups show gradients - might not work in real venue

3. **Animation/Transitions**
   - Does screen "pop" to new content? Or smooth transitions?
   - Do scores count up? Or appear instantly?
   - Does "NOW BATTLING" pulse/animate?

4. **Sound/Audio Integration**
   - Does projection sync with MC announcements?
   - Visual-only? Or complementary to audio?

5. **Branding**
   - Tournament logo/branding display?
   - Sponsor logos (user said remove, but what about tournament organizer branding)?

---

## Part 6: Critical Questions for User Decision

### Question Group 1: Terminology (USER MUST APPROVE)

**Q1.1:** Replace "bracket" with what term?
- [ ] "Championship Path"
- [ ] "Finals Tree"
- [ ] "Road to Victory"
- [ ] Other: ___________

**Q1.2:** Replace "standing" with what term?
- [ ] "Rankings"
- [ ] "Leaderboard"
- [ ] "Scoreboard"
- [ ] Other: ___________

**Q1.3:** What to call the queue/schedule view?
- [ ] "Match Schedule"
- [ ] "Battle Schedule"
- [ ] "Upcoming Battles"
- [ ] "Matchmaking" (user's term)
- [ ] Other: ___________

---

### Question Group 2: Multi-Category Handling (USER MUST DECIDE)

**Q2.1:** How to handle tournaments with multiple categories?
- [ ] Option A: Category tabs/filters (manual switching)
- [ ] Option B: Auto-show active category only (intelligent switching)
- [ ] Option C: Show all categories mixed together (single view)
- [ ] Option D: Split screen (if wide display available)

**Q2.2:** Should category be visually prominent?
- [ ] Yes - large category label on every screen
- [ ] Moderate - small header showing category
- [ ] Minimal - only show if multiple categories exist

---

### Question Group 3: Rankings Display Strategy (USER MUST DECIDE)

**Q3.1:** When should rankings be shown?
- [ ] Always visible (constantly updating)
- [ ] Only when pools phase complete (final standings)
- [ ] Smart: Show after each battle briefly, then return to schedule
- [ ] Manual: Only if staff chooses to display

**Q3.2:** What rankings data to show?
- [ ] Full table: All performers, W-D-L, points, rank
- [ ] Top 3 only: Podium style
- [ ] Qualified performers only: Who's advancing
- [ ] Adaptive: Full during pools, qualified-only after

---

### Question Group 4: Battle Display Detail (USER MUST DECIDE)

**Q4.1:** What to show during ACTIVE battle (in V1 without judges/rounds)?
- [ ] Just names + "Battle in Progress" message
- [ ] Names + timer showing elapsed time
- [ ] Names + scores (updated when staff encodes result)
- [ ] Names + category + pool context

**Q4.2:** What to show when battle COMPLETED?
- [ ] Winner name + "WINS!" message (5 seconds, then next battle)
- [ ] Both performers + winner highlighted (10 seconds)
- [ ] Full outcome details + score (if applicable)
- [ ] Auto-advance to rankings update

---

### Question Group 5: URL Structure & Access (USER MUST DECIDE)

**Q5.1:** How should projection be accessed?
- [ ] `/projection` - Auto-selects ACTIVE tournament
- [ ] `/projection/{tournament_id}` - Explicit tournament required
- [ ] `/projection` with optional `?tournament_id=` override
- [ ] `/live` or `/display` (different name than "projection")

**Q5.2:** Should projection URL be publicly accessible?
- [ ] Yes - No authentication, anyone with URL can view
- [ ] Yes - But rate-limited to prevent abuse
- [ ] Partial - Requires special token generated by staff
- [ ] No - Staff-only, must be logged in

---

### Question Group 6: Intelligent Display vs Manual Control (CRITICAL)

**Q6.1:** Who controls what the audience sees?
- [ ] Fully automatic - System decides based on tournament state (recommended)
- [ ] Staff-controlled - Admin panel to switch views
- [ ] Hybrid - Auto mode with staff override option
- [ ] Pre-programmed - Staff sets schedule of what shows when

**Q6.2:** If automatic, what's the fallback when no clear "best view"?
- [ ] Default to schedule/queue
- [ ] Default to rankings
- [ ] Show tournament info + branding
- [ ] Rotate between views every 15 seconds

---

## Part 7: Recommendations Summary (Steve Jobs Perspective)

### Principle 1: Simplicity Over Options
**Don't make the audience think. Make the computer think.**

- ❌ NO: 4 different views to choose from
- ✅ YES: One intelligent view that adapts

### Principle 2: Context Is Everything
**Show what matters NOW, not everything possible.**

- During battle → Show battle
- Between battles → Show what's next
- End of phase → Show who advanced
- Tournament done → Celebrate winners

### Principle 3: Audience-First Language
**Use words normal people use, not technical jargon.**

- ❌ "Standings", "Bracket", "Projection"
- ✅ "Rankings", "Championship Path", "Live Display"

### Principle 4: Design for the Back Row
**If you can't read it from 50 feet away, it's too small.**

- Font sizes: Minimum 4rem (64px)
- High contrast: White on dark, no subtle grays
- Animations: Smooth but obvious

### Principle 5: Zero Configuration
**It should just work. No setup, no choices, no confusion.**

- URL: `/projection` (simple, memorable)
- Access: Public, no login needed
- Display: Automatic, no staff intervention required
- Updates: Real-time via HTMX polling

---

## Next Steps

1. **User reviews this document**
2. **User answers the 6 question groups** (decisions needed)
3. **Create terminology glossary** with approved terms
4. **Update DOMAIN_MODEL.md** with projection business rules
5. **Revise UI_MOCKUPS.md** Section 13 with:
   - Approved terminology
   - Simplified intelligent view approach
   - All empty states defined
   - V1-compatible (no judges/rounds)
6. **Update ROADMAP.md** with finalized Phase 4 scope

**Only THEN proceed to implementation.**

---

**Status:** ⏸️ **AWAITING USER INPUT** - Need answers to question groups before proceeding
