# Quickstart: Lots Panel Skeleton Loading

## Prerequisites

- Python 3.14, Django dev server running
- At least one seller with multiple events containing lots

## Run Tests

```bash
cd src && python -m pytest ../tests/ -v
```

## Manual Verification

### 1. Skeleton loading on event click (FR-001 through FR-005, FR-007)

1. Open the app and select a seller
2. Click an event — observe the lots panel immediately shows skeleton rows:
   - 4 rows with animated pulse placeholders
   - Thumbnail placeholder (56x56 rounded rect) in column 1
   - Description bars (title + notes) in column 2
   - Dimension bar cluster in column 3
   - Small placeholders for CPack, Crate, DNT columns
3. After data loads, skeleton is fully replaced by real lots table
4. Verify no layout shift — columns align between skeleton and real data

### 2. No skeleton on seller click (FR-006)

1. While viewing lots for an event, click a different seller
2. Verify the lots panel shows "Select an event to view lots" empty state
3. Verify skeleton rows do NOT appear in the lots panel

### 3. Stable event sort order (FR-008)

1. Select a seller with multiple events
2. Note the event order (should be most recent first by start date)
3. Click an event to load its lots
4. Verify the events list maintains the same order — only the active highlight changes
5. Click a different event — verify order stays stable

### 4. Edge cases

- Select an event with zero lots: skeleton appears briefly, then empty/no-lots state shows
- Rapid-click multiple events: each click replaces the skeleton, no stacking or glitches
