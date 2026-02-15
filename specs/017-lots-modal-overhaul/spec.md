# Feature Specification: Lots Modal Overhaul

**Feature Branch**: `017-lots-modal-overhaul`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Improve the lots modal. Center both horiz and vert. Header with image gallery left; desc, notes, override form (same as lots table) right. Below that: recommendation engine with low, med, high suggestion with gallery of related examples below."
**Reference Mockup**: `/usr/src/BrandGuidelines/mockups/autoparser/modals/m6-full-composite.html`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Redesigned Modal Layout with Gallery and Override Form (Priority: P1)

A logistics operator clicks a lot thumbnail or description in the lots table. The lot detail modal opens, centered both horizontally and vertically on screen. The top section (hero area) displays an image gallery on the left side and the lot's description, notes, and inline override form on the right side. The override form contains the same fields as the lots table inline form (qty, L, W, H, weight, cpack, force crate, do not tip) and behaves identically — saving overrides back to the lot. The operator can browse lot images via thumbnail navigation while simultaneously editing override values, all without leaving the modal.

**Why this priority**: The core value of the modal overhaul. Without the redesigned layout, the other features (recommendation engine) have no context. This replaces the current two-step detail-then-edit flow with a unified view.

**Independent Test**: Can be fully tested by opening any lot modal and verifying the gallery + info + override form layout renders correctly, the form saves overrides, and the modal is centered on screen.

**Acceptance Scenarios**:

1. **Given** a lots table with loaded lots, **When** the operator clicks a lot thumbnail or description, **Then** the modal opens centered both horizontally and vertically on the viewport.
2. **Given** an open lot modal, **When** the modal renders, **Then** the left side displays the lot's image gallery with thumbnail navigation, and the right side displays description, notes, and the override form.
3. **Given** the override form in the modal, **When** the operator changes a dimension value and saves, **Then** the override is persisted and the lots table row updates to reflect the new value.
4. **Given** the image gallery, **When** the lot has multiple images, **Then** the operator can click thumbnails to switch the main displayed image.
5. **Given** the override form, **When** the operator changes the cpack dropdown, **Then** the dropdown visually reflects the selected severity level with the appropriate color badge (NF=green, LF=blue, F=amber, VF=red, PBO=purple).
6. **Given** the modal, **When** the viewport is narrow (mobile/tablet), **Then** the layout stacks vertically (gallery above, info below) instead of side-by-side.

---

### User Story 2 - Recommendation Engine with Low/Med/High Suggestions (Priority: P2)

Below the hero section, the modal displays a recommendation engine section. This section shows three sizing suggestions — low (Q25), median (Q50), and high (Q75) — presented as cards with box dimensions and pack type. One card is visually highlighted as the recommended option. This gives the operator quick reference sizing guidance for the lot based on its dimensions.

**Why this priority**: The recommendation engine is the key new capability that adds intelligence to the modal. However, it depends on the redesigned layout (P1) being in place first. Initially this section will display placeholder content (marked "Quoter Pending") since the actual quoter/sizing engine integration is a future concern.

**Independent Test**: Can be tested by opening a lot modal and verifying three suggestion cards appear below the hero section with low/median/high labels, one marked as recommended, each showing box dimensions and pack type.

**Acceptance Scenarios**:

1. **Given** an open lot modal, **When** the recommendation section renders, **Then** three sizing cards are displayed in a horizontal row labeled "Minimum", "Recommended", and "Oversize" (corresponding to low, median, high).
2. **Given** the three sizing cards, **When** displayed, **Then** the "Recommended" card is visually distinguished (highlighted border/background) from the other two.
3. **Given** each sizing card, **When** displayed, **Then** it shows box dimensions (L x W x H) and pack type.
4. **Given** the recommendation section, **When** the quoter engine is not yet integrated, **Then** a "Quoter Pending" badge is displayed to indicate placeholder status.

---

### User Story 3 - Related Lots Gallery with Card Stacks (Priority: P3)

Below the recommendation cards, the modal displays a "Related Lots" section with three columns of browsable card stacks aligned to the low/med/high categories. Each card shows a related lot's image, lot number, dimensions, weight, cpack level, and an "Accept" button. The operator can navigate through stacked cards in each column using up/down controls. Clicking "Accept" on a related lot copies that lot's dimensions and pack settings into the current lot's override form.

**Why this priority**: Provides the most advanced workflow — allowing operators to find similar lots and quickly apply their sizing. Depends on both the layout (P1) and recommendation section (P2) being in place. Initially displays placeholder data; actual similarity matching is a future integration.

**Independent Test**: Can be tested by opening a lot modal and verifying three columns of navigable card stacks appear, each card showing lot details, and the Accept button populates the override form above.

**Acceptance Scenarios**:

1. **Given** an open lot modal, **When** the related lots section renders, **Then** three columns are displayed, labeled "Q25 Low", "Q50 Median", and "Q75 High".
2. **Given** a column of related lot cards, **When** displayed, **Then** the top card is fully visible and subsequent cards appear stacked behind with decreasing opacity.
3. **Given** a card stack column, **When** the operator clicks the down navigation arrow, **Then** the next card cycles to the front position.
4. **Given** a related lot card, **When** displayed, **Then** it shows: lot image, lot number/title, dimensions, weight, cpack badge, and an "Accept" button.
5. **Given** a related lot card, **When** the operator clicks "Accept", **Then** that lot's dimensions, weight, and cpack values are copied into the override form in the hero section above.
6. **Given** the related lots section, **When** the similarity matching engine is not yet integrated, **Then** a "Similarity Matching" badge is displayed to indicate future functionality.

---

### Edge Cases

- What happens when a lot has no images? The gallery area displays a placeholder/empty state rather than collapsing.
- What happens when a lot has only one image? The thumbnail strip is hidden or shows a single non-interactive thumbnail.
- What happens when the related lots section has no matching lots for a column? The column displays an empty state message.
- How does the modal behave when the viewport is very small? The layout gracefully stacks all sections vertically.
- What happens when the operator modifies the override form and then clicks "Accept" on a related lot? The Accept action overwrites the current override field values (unsaved changes are replaced).
- What happens when the modal is opened while another save is in progress? The modal waits for the pending save to complete before allowing new saves.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The modal MUST be centered both horizontally and vertically on the viewport when opened.
- **FR-002**: The modal hero section MUST display a two-column layout: image gallery on the left, lot information on the right.
- **FR-003**: The image gallery MUST support a main image display area and a thumbnail navigation strip below it.
- **FR-004**: The right side of the hero section MUST display the lot title/description, notes, and an inline override form.
- **FR-005**: The inline override form MUST contain the same fields as the lots table row form: qty, L, W, H, weight, cpack (dropdown), force crate (checkbox), and do not tip (checkbox).
- **FR-006**: The override form MUST include a Save button that persists changes and updates the corresponding lots table row.
- **FR-007**: Each override field MUST show the initial (parsed) value as a reference below the input, with changed values highlighted in a distinct color.
- **FR-008**: The recommendation section MUST display three sizing suggestion cards in a horizontal row (minimum, recommended, oversize).
- **FR-009**: The recommended card MUST be visually distinguished from the other two cards.
- **FR-010**: The related lots section MUST display three columns of browsable card stacks corresponding to low (Q25), median (Q50), and high (Q75) categories.
- **FR-011**: Each related lot card MUST display: image thumbnail, lot number/title, dimensions, weight, cpack badge, and an "Accept" action.
- **FR-012**: Card stacks MUST support navigation (previous/next) with a counter showing current position out of total.
- **FR-013**: The "Accept" action on a related lot card MUST copy that lot's dimension, weight, and cpack values into the current lot's override form fields.
- **FR-014**: The modal layout MUST be responsive, stacking sections vertically on narrow viewports.
- **FR-015**: The modal MUST retain its current HTMX-driven open/close behavior (triggered from lots table row clicks, loaded dynamically).

### Key Entities

- **Lot Hero**: The top section of the modal combining image gallery and lot information with override form. Represents the primary interaction area.
- **Sizing Suggestion**: A recommended box size (L x W x H) with associated pack type. Three tiers: minimum, recommended, oversize.
- **Related Lot Card**: A reference to another lot with similar characteristics, displaying its image, dimensions, weight, and pack classification. Browsable in stacked card format.

## Assumptions

- The override form in the modal reuses the same backend endpoint and validation logic as the existing lots table inline form — no new backend endpoints needed for saving overrides.
- The recommendation engine (box sizing suggestions) will initially show placeholder/static content. Actual quoter integration is out of scope for this feature and will be handled by a future feature.
- The related lots section will initially show placeholder data. Actual similarity matching is out of scope and will be handled by a future feature.
- The modal's max width increases from the current 700px to approximately 840px to accommodate the two-column hero layout per the mockup.
- Gallery thumbnail navigation uses the existing image URLs from the lot data (no new image processing needed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The lot detail modal opens visually centered on screen (both axes) on all standard viewport sizes (desktop, tablet, mobile).
- **SC-002**: Operators can view lot images and edit override values simultaneously in a single modal view, eliminating the previous two-step detail-then-edit workflow.
- **SC-003**: Override changes saved from the modal correctly update the corresponding lots table row without requiring a page refresh.
- **SC-004**: 100% of lots table inline form fields (qty, L, W, H, weight, cpack, force crate, do not tip) are available and functional in the modal override form.
- **SC-005**: The recommendation section displays three sizing suggestion cards with clear visual distinction for the recommended option.
- **SC-006**: The related lots section displays three navigable card stack columns, with each card showing lot details and an Accept action.
- **SC-007**: The modal layout gracefully adapts to narrow viewports by stacking sections vertically without horizontal overflow.
