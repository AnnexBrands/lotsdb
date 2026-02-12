# Spec: Lots Table UX Polish

**Feature**: 008-lots-table-ux-polish | **Status**: Draft | **Date**: 2026-02-11

## Overview

Refine the lots table editing UX to feel more like a spreadsheet: cleaner inputs, smarter save behavior, better visual feedback, and improved content discoverability.

## User Stories

### US1: Cleaner Input Appearance (P1)
As an operator, I want table inputs to look minimal and clean so the data is easy to scan.

**Acceptance:**
- Description and notes are combined into a single `<td>` with a single `<textarea>` (description on first line, notes below — separated by display, not separate inputs)
- Inputs for qty, l, w, h, wgt, cpack have no visible border — only the `<td>` cell has a subtle box border
- cpack field is a `<select>` dropdown with options: 1, 2, 3, 4, PBO (navigable with arrow keys)

### US2: Smart Save with Visual Feedback (P1)
As an operator, I want the save icon to indicate whether I have unsaved changes and when a save succeeds, without having to click a button every time.

**Acceptance:**
- Save icon has no border (just the icon)
- Save icon turns **red** when any field in the row has been modified (dirty state)
- Save icon turns **green** after a successful save
- Auto-save triggers after a long debounce (~2 seconds) when the row loses focus (user moves to another row or clicks elsewhere)
- Clicking the save icon still works as an immediate save
- Row does NOT flash yellow on click and never shows sticky yellow highlight from clicking

### US3: Photo Hover Preview (P2)
As an operator, I want to see a larger version of the lot photo when I hover over the thumbnail so I can quickly inspect items without opening the modal.

**Acceptance:**
- Hovering over the thumbnail shows a larger preview image (e.g., 300px) in a tooltip/popover
- Preview disappears when the mouse leaves the thumbnail
- If no image exists (placeholder), no preview appears

### US4: Notes "More" Link (P2)
As an operator, I want to see truncated notes in the table with a "more" link that opens the full detail in the lot detail modal.

**Acceptance:**
- Notes text is displayed as read-only truncated text below the description textarea
- A "more" link/button appears when notes exist, opening the lot detail modal
- The notes are not editable inline in the table (only editable via the detail modal)

## Non-Functional Requirements

- No new dependencies — vanilla JS + CSS only
- Changes confined to: lots_table_row.html, styles.css, shell.html (JS), panels.py
- Must not break existing lot detail modal or override save flows

## Out of Scope

- Changes to the detail modal layout
- Changes to the OverrideForm (modal edit form)
- New API endpoints
