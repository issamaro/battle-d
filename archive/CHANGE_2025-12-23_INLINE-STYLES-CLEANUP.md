# Workbench: Inline Styles Cleanup (Frontend Rebuild Phase 2)

**Date:** 2025-12-23
**Author:** Claude
**Status:** Complete

---

## Purpose

Remove all ~121 inline `style=""` attributes from 18 templates and migrate them to the SCSS design system. This completes the frontend rebuild by ensuring all visual styling is centralized in SCSS files.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- N/A - No entity changes

**VALIDATION_RULES.md:**
- N/A - No validation rule changes

### Level 2: Derived
**ROADMAP.md:**
- N/A - This is a cleanup task, not a new feature phase

### Level 3: Operational
**ARCHITECTURE.md:**
- N/A - No backend pattern changes

**FRONTEND.md:**
- Section "Component Library": Add documentation for new SCSS partials:
  - `_error-pages.scss` - Error page layout classes
  - `_battles.scss` - Battle encode form classes
  - `_profile.scss` - Profile page layout classes
  - `_alerts.scss` - Alert/info box classes

---

## Verification

**Grep checks performed:**
```bash
grep -rn 'style="' app/templates/
```

**Result:** 0 matches - All inline styles removed!

**SCSS Compilation:** Successful with no errors

---

## Files Modified

**SCSS (New):**
- `app/static/scss/components/_error-pages.scss`
- `app/static/scss/components/_battles.scss`
- `app/static/scss/components/_profile.scss`
- `app/static/scss/components/_alerts.scss`

**SCSS (Updated):**
- `app/static/scss/components/_index.scss` - Added 4 new partials
- `app/static/scss/components/_cards.scss` - Added card-neutral, card-header-warning
- `app/static/scss/components/_loading.scss` - Added loading-indicator
- `app/static/scss/utilities/_display.scss` - Added d-none, d-block, d-flex utilities

**Templates Migrated (18 total):**
- `errors/401.html` - Error page with SCSS classes
- `errors/403.html` - Error page with SCSS classes
- `errors/404.html` - Error page with SCSS classes
- `errors/500.html` - Error page with SCSS classes
- `errors/tournament_config_error.html` - Error page with SCSS classes
- `battles/detail.html` - Battle card with SCSS classes
- `battles/encode_pool.html` - Encode form with SCSS classes
- `battles/encode_tiebreak.html` - Encode form with SCSS classes
- `dancers/profile.html` - Profile table with SCSS classes
- `tournaments/add_category.html` - Form with alert boxes
- `admin/fix_active_tournaments.html` - Admin form with alerts
- `pools/overview.html` - Pool standings with SCSS classes
- `registration/_dancer_search.html` - Search table with SCSS classes
- `registration/register.html` - Registration form
- `tournaments/create.html` - Create form with alert
- `tournaments/list.html` - Warning card header
- `dancers/edit.html` - Card-neutral background
- `admin/edit_user.html` - Card-neutral background

---

## New CSS Classes Created

### Error Pages
- `.error-page` - Centered container for error pages
- `.error-code` - Large error code (404, 500, etc.)
- `.error-code--muted` - Muted color variant
- `.error-code--danger` - Danger color variant
- `.error-code--warning` - Warning color variant
- `.error-message` - Error description text
- `.error-detail` - Technical detail (monospace)
- `.error-actions` - Button group

### Battles
- `.battle-card` - Battle detail wrapper
- `.battle-header` - Battle title and status
- `.battle-section` - Section spacing
- `.performer-grid` - Grid layout for performers
- `.performer-card` - Individual performer card
- `.performer-card--winner` - Winner highlight
- `.performer-option` - Radio card for selection
- `.performer-option-content` - Content inside radio option
- `.winner-badge` - Winner text badge
- `.battle-status` - Status badge variants
- `.battle-actions` - Action buttons footer
- `.draw-separator` - Draw option separator
- `.encode-footer` - Form footer
- `.battle-outcome-data` - Pre block for outcome
- `.performer-stats` - Small stats text
- `.standings-winner` - Winner row highlight
- `.status-success` - Green text
- `.status-danger` - Red text

### Profile
- `.profile-container` - Max-width container
- `.profile-table` - Definition table
- `.profile-row` - Table row with border
- `.profile-label` - Bold label cell
- `.profile-value` - Value cell
- `.profile-actions` - Buttons container
- `.profile-section` - Section with top border
- `.info-box` - Info placeholder box

### Alerts
- `.alert` - Base alert class
- `.alert-warning` - Yellow warning box
- `.alert-info` - Blue info box
- `.alert-danger` - Red danger box
- `.alert-success` - Green success box
- `.alert-titled` - Alert with heading
- `.alert-display` - Large display number
- `.alert-muted` - Small/muted text
- `.calculator-box` - Yellow calculator display
- `.calculator-value` - Large value in calculator
- `.calculator-formula` - Formula text
- `.howto-box` - Blue how-it-works box

### Utilities Added
- `.d-none` - display: none
- `.d-block` - display: block
- `.d-inline` - display: inline
- `.d-inline-block` - display: inline-block
- `.d-flex` - display: flex
- `.d-grid` - display: grid
- `.card-neutral` - Neutral background card
- `.card-header-warning` - Warning background header
- `.loading-indicator` - Centered loading text

---

## Notes

- All colors now use design tokens from `_variables.scss`
- All spacing uses `$space-*` scale
- All `var(--pico-*)` references have been removed
- JavaScript updated in register.html to use classList instead of style.display
