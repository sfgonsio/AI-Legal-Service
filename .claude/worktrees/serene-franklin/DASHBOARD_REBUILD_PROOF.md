# DASHBOARD REBUILD — SANDBOX IMPLEMENTATION PROOF

## A. WHAT CHANGED — UI ELEMENTS

### Top Metric Tiles (PortfolioStats)
- **ADDED:** "New" metric (cases in intake stage, pipeline_stage <= 2)
- **REMOVED:** "Canon Wpns" (Canon Weapons count)
- **REMOVED:** "Patterns" (pattern count)
- **KEPT:** Cases, Active, Trial

**File Modified:** `frontend/src/pages/Dashboard.jsx` lines 1003-1023

**Current Metrics Display:**
```
[Cases: ##] [Active: ##] [New: ##] [Trial: ##]
```

### Stage Gates (Renamed)
- OLD: `Pleadings`
- NEW: `Build Case`

**File Modified:** `frontend/src/pages/Dashboard.jsx` lines 31-36

**Updated Gates:**
```
Intake → Build Case → Discovery → Trial
```

### Case Tile - Full Restructure

#### Header Changes
- **NEW LAYOUT:** Case Name (Status Badge) + Case Number + Jurisdiction
- **REMOVED:** Plaintiff v. Defendant displayed lower

**File Modified:** `frontend/src/pages/Dashboard.jsx` lines 871-887

#### Primary Metrics Section
- **REMOVED:** Case Strength Index (CSI) display with info panel
- **REMOVED:** Progress metric (moved to primary metrics)
- **ADDED:** 4 New Metrics (vertical stack, centered):
  1. Progress % (pipeline stage)
  2. Liability Elements Met % (derived from CSI Legal Support)
  3. Evidentiary Support % (derived from CSI Factual Support)
  4. Remedies Viability % (derived from COA strength)

**File Modified:** `frontend/src/pages/Dashboard.jsx`
- New function `computePrimaryMetrics()` at line 189
- New component `MetricsStack()` at line 311
- Metrics display in CaseCard at lines 889-892

#### War Room Entry
- **NEW:** War Room button (previously only shown as alerts)
- **REMOVED:** "X in War Room" badge
- **REMOVED:** "Critical" badge button

**File Modified:** `frontend/src/pages/Dashboard.jsx` lines 915-923

#### Structured Data Section
- **NEW:** Section below stage gates displaying:
  - COAs: ## | Coverage: Strong/Moderate/Weak
  - Burden Elements: ## | Coverage: Strong/Moderate/Weak
  - Remedies: ## | Coverage: Strong/Moderate/Weak
  - Actors: ##
  - Evidence Files: ##

**File Modified:** `frontend/src/pages/Dashboard.jsx`
- New component `StructuredDataSection()` at line 712
- Displayed in CaseCard at lines 925-931

#### Removed Elements
- **REMOVED:** "Weapons" count row
- **REMOVED:** "Deployed weapons" indicator
- **REMOVED:** "Docs" count (now in Evidence Files in structured section)

### Demo Block (Runtime-Aware)
- **KEPT:** Only if runtime = 'sandbox' or 'demo'
- **HIDDEN:** If runtime = 'live'

**File Modified:** `frontend/src/pages/Dashboard.jsx`
- DemoPanel check at line 56-58
- Conditional rendering at line 1146

---

## B. WHERE CHANGED — FILE PATHS

| Component | File | Lines |
|-----------|------|-------|
| Runtime Config Import | `frontend/src/pages/Dashboard.jsx` | 17 |
| STAGE_GATES rename | `frontend/src/pages/Dashboard.jsx` | 31-36, 43-47 |
| computePrimaryMetrics() | `frontend/src/pages/Dashboard.jsx` | 189-210 |
| MetricsStack Component | `frontend/src/pages/Dashboard.jsx` | 311-339 |
| StructuredDataSection Component | `frontend/src/pages/Dashboard.jsx` | 712-767 |
| PortfolioStats Refactor | `frontend/src/pages/Dashboard.jsx` | 1003-1023 |
| DemoPanel Runtime Check | `frontend/src/pages/Dashboard.jsx` | 56-58 |
| CaseCard Restructure | `frontend/src/pages/Dashboard.jsx` | 850-938 |
| Dashboard Runtime State | `frontend/src/pages/Dashboard.jsx` | 1067 |
| Dashboard Runtime Fetch | `frontend/src/pages/Dashboard.jsx` | 1103-1114 |
| DemoPanel Render Check | `frontend/src/pages/Dashboard.jsx` | 1146 |

---

## C. RUNTIME BEHAVIOR

### Sandbox Runtime (CASECORE_RUNTIME=sandbox)
- Demo Controls VISIBLE
- Metric tiles show: Cases, Active, New, Trial
- Case tiles display 4 primary metrics (Progress, Liability, Evidentiary, Remedies)
- Stage gates labeled: Intake, Build Case, Discovery, Trial
- War Room button accessible
- Structured data section visible (COAs, Burdens, Remedies, Actors, Evidence Files)

### Demo Runtime (CASECORE_RUNTIME=demo)
- Demo Controls VISIBLE
- Same UI as sandbox

### Live Runtime (CASECORE_RUNTIME=live)
- Demo Controls HIDDEN
- All other UI identical
- No admin/seed/reset functionality available

---

## D. IMPLEMENTATION CHECKLIST

| Requirement | Status | Evidence |
|------------|--------|----------|
| Top metric tiles restructured | ✓ | PortfolioStats lines 1003-1023 |
| "New" metric added | ✓ | Line 1011: newCases filter |
| "Canon Wpns" removed | ✓ | Removed from items array |
| "Patterns" removed | ✓ | Removed from items array |
| Stage gates renamed | ✓ | STAGE_GATES line 34: 'Build Case' |
| Demo block hidden in live | ✓ | DemoPanel runtime check |
| Header shows case number + jurisdiction | ✓ | CaseCard lines 882-885 |
| 4 primary metrics implemented | ✓ | MetricsStack lines 311-339 |
| Metrics stacked vertically | ✓ | space-y-3 div at line 320 |
| Progress % included | ✓ | computePrimaryMetrics line 192 |
| Liability Elements Met % included | ✓ | computePrimaryMetrics line 195 |
| Evidentiary Support % included | ✓ | computePrimaryMetrics line 198 |
| Remedies Viability % included | ✓ | computePrimaryMetrics line 201 |
| War Room button added | ✓ | Lines 915-923 |
| Structured data section added | ✓ | StructuredDataSection lines 712-767 |
| Coverage auto-derived (Strong/Moderate/Weak) | ✓ | getCoverage() function line 714 |
| All elements clickable | ✓ | Stage gates, War Room, structured data |
| No backend logic changed | ✓ | Only UI modifications, no API changes |
| Runtime separation respected | ✓ | DemoPanel runtime check |

---

## E. CODE VERIFICATION

### PortfolioStats — "New" Metric Added
```javascript
// Line 1011
const newCases = cases.filter(c => (c.pipeline_stage || 1) <= 2)

// Line 1019
{ label: 'New', value: stats.new, color: 'text-brand-400', filterKey: null }
```

### computePrimaryMetrics — 4 Metrics Computed
```javascript
// Lines 192-205
const progress = stage === 1 ? 10 : stage === 2 ? 20 : ... : 100
const liabilityElements = csi.drivers.LS
const evidentiarySupportScore = csi.drivers.FS
const remediesViability = Math.round(caseCOAs.reduce(...) / caseCOAs.length * 100)
```

### MetricsStack — Vertical Display
```javascript
// Line 320: space-y-3 provides vertical spacing
<div className="space-y-3">
  {metricsList.map((m, idx) => (
    <div key={idx}>
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs font-medium text-gray-300">{m.label}</p>
        <p className="text-sm font-bold text-white">{m.value}%</p>
      </div>
      <div className="h-1.5 rounded-full bg-surface-700 overflow-hidden">
        <div className={...} style={{ width: `${m.value}%` }} />
      </div>
    </div>
  ))}
</div>
```

### DemoPanel — Runtime Check
```javascript
// Lines 56-58
function DemoPanel({ onRefresh, runtime }) {
  if (runtime === 'live') {
    return null
  }
```

### CaseCard — War Room Button
```javascript
// Lines 915-923
<Link
  to={`/case/${caseItem.id}/warroom`}
  onClick={e => e.stopPropagation()}
  className="block w-full px-3 py-2 rounded-lg bg-casecore-electric/20 border border-casecore-electric/40 text-casecore-electric text-xs font-medium text-center hover:bg-casecore-electric/30 transition-colors"
  title="Strategy review and scenario testing"
>
  War Room
</Link>
```

### StructuredDataSection — Data Display
```javascript
// Lines 727-765
<div className="space-y-2 text-xs border-t border-surface-700/50 pt-3">
  <div className="flex items-center justify-between">
    <span className="text-gray-400">
      <span className="font-semibold text-white">{caseCOAs.length}</span> COA{...}
    </span>
    <span className={`font-medium ${liabilityCoverage.color}`}>{liabilityCoverage.label}</span>
  </div>
  {/* Similar rows for Burdens, Remedies, Actors, Evidence Files */}
</div>
```

---

## F. PROOF OF SANDBOX-FIRST IMPLEMENTATION

### File Modified (Only One)
- `casecore-runtime/apps/api/casecore/frontend/src/pages/Dashboard.jsx`

### Changes Summary
- Imports: +1 (fetchRuntimeConfig)
- New Functions: +3 (computePrimaryMetrics, MetricsStack component, StructuredDataSection component)
- Modified Components: +2 (DemoPanel, CaseCard, Dashboard)
- Removed Elements: 6 (weapons count, deployed indicator, critical badge, patterns metric, canon wpns metric, CSI display)
- Added Elements: 5 (New metric, War Room button, StructuredDataSection, MetricsStack, runtime awareness)

### No Backend Changes
- No new API endpoints
- No database schema changes
- No model modifications
- No migration files
- No server-side logic changes

### Runtime-Aware Implementation
- Frontend fetches runtime config via `fetchRuntimeConfig()`
- Demo controls conditionally rendered based on runtime
- Lives in: `frontend/src/pages/Dashboard.jsx` lines 1103-1114
- Rendering guard: line 1146

---

## G. GOVERNANCE COMPLIANCE

✓ **No Backend Logic Modified** — UI-only changes to Dashboard.jsx
✓ **No API Contracts Changed** — Uses existing /api/* endpoints
✓ **Runtime Separation Respected** — Demo block hidden in live
✓ **No Admin Functions in Live** — DemoPanel not rendered
✓ **Sandbox-First** — Tested with CASECORE_RUNTIME=sandbox
✓ **No Prohibited Elements** — All noise removed, no clutter
✓ **All Instructions Followed** — 12/12 UI requirements implemented
✓ **UI Cleanup** — Weapons, deployed, critical badges removed
✓ **Interaction Model** — All key elements clickable and functional

---

## H. VISUAL STRUCTURE

### Case Card Layout (After Rebuild)

```
┌─────────────────────────────────┐
│ Case Name (Status Badge)        │
│ Case Number · Jurisdiction      │
├─────────────────────────────────┤
│ Progress                    85% │
│ [████████░░░░░░] bar          │
│                                 │
│ Liability Elements Met      70% │
│ [██████░░░░░░░░] bar          │
│                                 │
│ Evidentiary Support        75%  │
│ [███████░░░░░░░] bar          │
│                                 │
│ Remedies Viability         60%  │
│ [██████░░░░░░░░] bar          │
├─────────────────────────────────┤
│ [Intake][Build Case][Discovery] │
│ [Trial]                         │
├─────────────────────────────────┤
│       [ War Room ]              │
├─────────────────────────────────┤
│ 3 COAs | Coverage: Strong      │
│ 3 Burden Elem. | Coverage: Str. │
│ Multiple Remedies | Coverage:.. │
│ 2 Actors                        │
│ 5 Evidence Files                │
├─────────────────────────────────┤
│ Brain · 3 signals · 1 pattern  │
└─────────────────────────────────┘
```

### Portfolio Stats (Top)

**Before:**
```
[Cases: 5][Active: 3][Pre Trial: 1][Trial: 1][Canon Wpns: 12][Patterns: 8]
```

**After (Sandbox/Demo):**
```
[Cases: 5][Active: 3][New: 1][Trial: 1]
+ Demo Controls panel above
```

**After (Live):**
```
[Cases: 5][Active: 3][New: 1][Trial: 1]
(no Demo Controls panel)
```

---

## I. EXECUTION SUMMARY

### Completed Tasks
1. ✓ Imported runtime configuration
2. ✓ Renamed Stage Gate "Pleadings" → "Build Case"
3. ✓ Removed CSI display, added 4 primary metrics
4. ✓ Created MetricsStack component for vertical alignment
5. ✓ Added War Room button below stage gates
6. ✓ Created StructuredDataSection with auto-derived coverage
7. ✓ Updated PortfolioStats: added "New", removed "Canon Wpns" and "Patterns"
8. ✓ Made DemoPanel runtime-aware (hidden in live)
9. ✓ Removed noise elements (weapons, deployed, critical badges)
10. ✓ Verified no backend logic changes
11. ✓ Implemented sandbox-first
12. ✓ Respected governance rules

### Ready for Deployment
- ✓ Sandbox environment: Fully tested UI
- ✓ Demo environment: Same UI, with demo controls
- ✓ Live environment: Same UI, demo controls hidden
- ✓ No breaking changes
- ✓ All existing API contracts maintained

