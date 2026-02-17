# Quickstart: Import Hardening (020)

**Date**: 2026-02-17
**Prerequisites**: Dev server running, authenticated session, Redis running

## Setup

```bash
cd /usr/src/lotsdb
.venv/bin/python src/manage.py runserver 0.0.0.0:8000
```

Ensure Redis is running (used for recovery cache):
```bash
redis-cli ping  # should return PONG
```

## Test Plan

### US1: Merge Recovery Dashboard

**Happy path — recovery after merge failure:**
1. Import a catalog file with a known existing catalog ID (triggers merge)
2. If all lots succeed, no recovery link appears — to test recovery, temporarily modify `merge_catalog` to raise an exception for one lot
3. After merge with failures: verify the response includes `recovery_url`
4. Navigate to `/imports/recovery/`
5. Verify the table shows failed lots with customer item ID, lot number, error message
6. Click "Check Server" on a failed lot — verify server state is displayed
7. Click "Retry" — verify success (row turns green) or error (row turns red with detail)
8. After all lots resolved, verify "All items recovered" message

**Edge case — Redis unavailable:**
1. Stop Redis
2. Import a file that triggers a merge failure
3. Verify merge still completes (best-effort) but no recovery link (warning logged)
4. Restart Redis

### US2: Search by Customer Item ID

**Happy path:**
1. Note a customer item ID from an existing lot in the lots table (e.g., `2100000000`)
2. Type it into the navbar search input and press Enter
3. Verify redirect to `/?seller=1874&event=400160&item=2100000000` (actual IDs vary)
4. Verify: seller panel highlights the correct seller, events panel highlights the correct event, lots table shows the correct page, and the lot row has a highlighted/active style

**Not found:**
1. Type a non-existent item ID (e.g., `9999999999`)
2. Press Enter
3. Verify "Item not found" toast appears and page is unchanged

**Pagination:**
1. Find a lot that is NOT on page 1 of a large event
2. Search for its customer item ID
3. Verify the lots table shows the correct page with the lot highlighted

### US3: Upload UX Polish

**Deep-link redirect:**
1. Drop a valid `.xlsx` file (new catalog) on the dropzone
2. Verify redirect goes to `/?seller=X&event=Y` (not bare `/`)

**Toast persistence:**
1. Drop a valid file for an existing catalog (merge path)
2. Verify the merge summary toast appears on the destination page (after redirect)
3. Toast should be visible for at least 3 seconds

**100% failure:**
1. (Requires test setup) Trigger a merge where all lots fail
2. Verify the response is treated as an error (error toast, not success)
3. Verify recovery link is shown

**File size limit:**
1. Create a file larger than 1 MB (e.g., `dd if=/dev/zero of=big.xlsx bs=1M count=2`)
2. Drop it on the dropzone
3. Verify "File too large" error toast appears immediately (client-side check)

**Dropzone animation:**
1. Drag a file over the dropzone (don't drop)
2. Verify the dropzone grows/animates
3. Drop the file
4. Verify upload-in-progress animation appears

### US4: Lots Table Bug Fixes

**Inline save persistence:**
1. Select a seller → event → see lots table
2. Change a dimension value (e.g., qty) inline
3. Click save
4. Refresh the page (F5)
5. Verify the new value is still there

**Cpack override indicator:**
1. Find a lot with an overridden cpack value
2. Verify the orange "original value" indicator appears next to cpack (inline and modal)

**Events panel after save:**
1. Select a seller with past and future events
2. Verify both appear in the events panel
3. Save a lot override (inline or modal)
4. Verify the events panel still shows both past and future events

## Run Tests

```bash
.venv/bin/python -m pytest tests/ -v
```
