# Feature Specification: Dimensions Input UX

**Feature Branch**: `012-dims-input-ux`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "improve UX for entering dims. fields should be LTR with clear style (muted 400?) for non-input (x, @, in, lbs) and floating headers. inputs should never cut off display of value."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read and Edit Dimensions Inline (Priority: P1)

A staff user viewing the lots table sees a compact, left-to-right dimensions row for each lot: Qty @ L x W x H in, Wgt lbs. The non-input separator tokens ("@", "x", "in", "lbs") are rendered in a muted, lighter weight (font-weight 400, subdued color) so they recede visually and the editable numeric values stand out. Each input field auto-sizes or is wide enough to never truncate the displayed value — even large numbers like 10000.5 are fully visible without scrolling inside the field.

**Why this priority**: This is the core of the feature — the entire point is to make dimensions readable and editable without visual confusion or clipped values.

**Independent Test**: Can be tested by loading any event with lots and verifying the dims row renders LTR with muted separators and fully visible values.

**Acceptance Scenarios**:

1. **Given** a lot with dimensions (qty=12, L=48.5, W=36, H=24, wgt=150), **When** the lots table renders, **Then** the dims cell displays inputs left-to-right as: `[12] @ [48.5] x [36] x [24] in, [150] lbs` with separators in muted style.
2. **Given** a lot with a large dimension value (e.g., L=10000.5), **When** the lots table renders, **Then** the input field is wide enough to display the full value without truncation or horizontal scrolling.
3. **Given** a lot row, **When** a user focuses a dimension input, **Then** the input visually indicates focus and the full value remains visible.

---

### User Story 2 - Floating Column Headers for Dimensions (Priority: P1)

Each sub-field within the dimensions cell has a floating label (e.g., "Qty", "L", "W", "H", "Wgt") positioned above the input so the user always knows which field they are editing. These labels are unobtrusive — styled consistently with the muted separator tokens — and do not consume extra vertical space that would bloat the row height.

**Why this priority**: Without labels, users cannot tell which number maps to length vs. width vs. height, making data entry error-prone. This is essential alongside the LTR layout.

**Independent Test**: Can be tested by loading the lots table and confirming each dimension input has a visible label identifying it.

**Acceptance Scenarios**:

1. **Given** a lot row in the lots table, **When** it renders, **Then** each dimension input has a floating header label ("Qty", "L", "W", "H", "Wgt") visible above the input.
2. **Given** the floating labels, **When** viewing the table, **Then** the labels are styled in the same muted/subdued treatment as the separator tokens (lighter weight, subdued color) so they don't compete with the input values.
3. **Given** the floating labels, **When** comparing row heights before and after this feature, **Then** row height increase is minimal (labels should be compact, not add a full extra line of height).

---

### Edge Cases

- What happens when a dimension value is empty or zero? The input should display the value as-is (empty or "0") without collapsing width.
- What happens when a user enters a very long decimal (e.g., 99999.999)? The input must be sized to accommodate without truncation.
- What happens on narrow browser widths? The dims cell should remain left-to-right and not wrap to multiple lines; horizontal scroll on the table is acceptable.
- What happens with overridden values (orange left-border indicator)? The override styling must still be visible alongside the new layout and labels.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dimension inputs MUST render in a single left-to-right horizontal row in the order: Qty @ L x W x H in, Wgt lbs.
- **FR-002**: Non-input separator tokens ("@", "x", "in", ",", "lbs") MUST be styled with muted/subdued appearance — lighter font-weight (400) and a subdued text color — so they visually recede behind the input values.
- **FR-003**: Each dimension input MUST have a floating header label ("Qty", "L", "W", "H", "Wgt") that identifies the field.
- **FR-004**: Floating labels MUST be styled consistently with the muted separator tokens (same subdued color and weight).
- **FR-005**: Dimension input fields MUST be wide enough to display their full value without truncation or horizontal scrolling inside the input. This applies to both the initial render and after user edits.
- **FR-006**: The existing override indicator (orange left-border on changed fields) MUST continue to work correctly with the new layout.
- **FR-007**: Auto-save behavior on dimension inputs MUST be preserved — no regression in save-on-change functionality.
- **FR-008**: The "Dimensions" column header in the table thead MUST remain as a single column header (the floating labels are per-input, not additional table columns).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All dimension values, including numbers up to 5 digits with one decimal place (e.g., 99999.9), are fully visible in their input fields without truncation on standard screen widths (1280px+).
- **SC-002**: Users can identify which dimension field is which (L vs. W vs. H) without needing to count position — floating labels are always visible.
- **SC-003**: Separator tokens ("@", "x", "in", "lbs") are visually distinct from editable values — a user can instantly distinguish what is editable from what is decoration.
- **SC-004**: No regression in existing lot editing workflows — override indicators, auto-save, and focus behavior all continue to work.

## Assumptions

- "Floating headers" means small labels positioned above each input within the same table cell, not a separate header row or tooltip.
- "Muted 400" refers to font-weight 400 with a subdued/muted color (e.g., slate-400 / #94a3b8), consistent with the existing separator styling direction.
- Input width is achieved via CSS min-width or ch-based sizing rather than JavaScript auto-resize, keeping the solution simple and performant.
- The "in" unit label appears after the H dimension to indicate inches for the L x W x H group.
