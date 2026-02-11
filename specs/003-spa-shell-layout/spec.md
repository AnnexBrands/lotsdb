# Feature Specification: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "FR 3 - Convert Seller/Events screens to an SPA shell with a three-region layout: Left1=Sellers, Left2=Events, Main=Lots. This feature establishes the UI foundation and style guide baseline for the application. The outcome must reflect professional product design quality, not developer-placeholder UI. Assume this UI will be used daily by internal operators and eventually external customers. Use static/catalog/lotsdb_logo.svg for brand logo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Sellers, Events, and Lots in a Three-Panel Layout (Priority: P1)

As a catalog operator, I want to see Sellers, Events, and Lots in a persistent three-column layout so that I can navigate between sellers and their events without losing context or waiting for full page reloads. Clicking a seller loads its events in the middle panel; clicking an event loads its lots in the main panel. All three panels are visible simultaneously.

**Why this priority**: This is the foundational interaction model. Every subsequent feature builds on this layout. Without it, operators must navigate back and forth between full-page views, losing context on each transition.

**Independent Test**: Navigate to the home page after login. The three-panel layout is visible. Click a seller in Left1 — events appear in Left2 without a full page reload. Click an event in Left2 — lots appear in Main without a full page reload. The previously selected seller remains highlighted in Left1.

**Acceptance Scenarios**:

1. **Given** I am authenticated and on the home page, **When** the page loads, **Then** I see a three-column layout with Sellers in the left panel, an empty/placeholder Events panel in the middle, and an empty/placeholder Lots panel on the right.
2. **Given** the Sellers panel is visible, **When** I click a seller, **Then** the Events panel loads that seller's events via HTMX (no full page reload) and the selected seller is visually highlighted.
3. **Given** events are loaded for a seller, **When** I click an event, **Then** the Lots panel loads that event's lots via HTMX (no full page reload) and the selected event is visually highlighted.
4. **Given** I have a seller and event selected, **When** I click a different seller, **Then** the Events panel updates to the new seller's events and the Lots panel clears or shows a placeholder.
5. **Given** the three-panel layout is displayed, **When** I view the page, **Then** the LotsDB brand logo is visible in the top navigation bar.

---

### User Story 2 - Professional Visual Design and Style Guide Baseline (Priority: P1)

As a product stakeholder, I want the application to present a polished, professional visual design that reflects production-quality product standards — not a developer prototype — so that it is suitable for daily use by internal operators and eventually external customers.

**Why this priority**: Co-equal with Story 1 because the user explicitly requires production-quality design as a non-negotiable outcome. The layout and the visual design ship together.

**Independent Test**: Load the application and visually confirm: consistent typography, refined color palette, appropriate spacing, clear visual hierarchy, branded header with logo, smooth transitions, and professional empty states. The design should feel like a shipped product, not a wireframe.

**Acceptance Scenarios**:

1. **Given** I am on the home page, **When** I view the interface, **Then** the top bar displays the LotsDB logo (from `static/catalog/lotsdb_logo.svg`), a search input, the catalog dropzone, and user controls — all consistently styled.
2. **Given** I view any panel, **When** content is loading, **Then** I see a subtle loading indicator (not a blank flash).
3. **Given** I view the three-panel layout, **When** no event or seller is selected, **Then** empty panels show professional placeholder states (icon + message), not blank space.
4. **Given** I interact with clickable items (sellers, events, lots), **When** I hover over them, **Then** I see appropriate hover states with smooth transitions.
5. **Given** any panel has more items than fit on screen, **When** I scroll, **Then** only that panel scrolls independently; the other panels and header remain fixed.

---

### User Story 3 - Scrollable Panels with Pagination (Priority: P2)

As an operator working with large catalogs, I want each panel to handle long lists gracefully — with independent scrolling and pagination controls — so that I can work with sellers, events, and lots without performance degradation.

**Why this priority**: Large datasets are common in production use. Without pagination, the UI becomes unusable. However, the layout and design foundation (P1) must exist first.

**Independent Test**: Load a seller with many events. Confirm the Events panel scrolls independently and shows pagination controls. Repeat for the Lots panel with a large event.

**Acceptance Scenarios**:

1. **Given** there are more sellers than fit in the Sellers panel, **When** I view the panel, **Then** the panel scrolls independently and shows pagination controls (next/previous).
2. **Given** a seller has many events, **When** I click that seller, **Then** the Events panel shows paginated results with navigation.
3. **Given** an event has many lots, **When** I click that event, **Then** the Lots panel shows paginated results with navigation.
4. **Given** I navigate to page 2 of events, **When** I click a different seller, **Then** the Events panel resets to page 1 of the new seller's events.

---

### User Story 4 - Preserved Navigation to Detail Views (Priority: P2)

As an operator, I want to click on a lot in the Main panel to navigate to the existing lot detail page, so that I retain access to the full lot detail, override, search, and import workflows that already exist.

**Why this priority**: Existing functionality must remain accessible. The SPA shell augments navigation but must not break existing deep-link views.

**Independent Test**: From the three-panel layout, click a lot row. Verify the lot detail page opens. Verify the back button returns to the SPA layout. Verify search, import, and override flows still work.

**Acceptance Scenarios**:

1. **Given** lots are displayed in the Main panel, **When** I click a lot row, **Then** I navigate to the existing lot detail page (`/lots/<id>/`).
2. **Given** I am on a lot detail page, **When** I click the browser back button or the Home breadcrumb, **Then** I return to the SPA shell layout.
3. **Given** I use the search bar from the SPA shell, **When** I submit a search, **Then** the existing search results page loads.
4. **Given** I access `/imports/`, `/lots/<id>/override/`, or any other existing URL directly, **When** the page loads, **Then** it renders correctly using the existing templates.

---

### Edge Cases

- What happens when a seller has zero events? The Events panel shows an empty state message: "No events for this seller."
- What happens when an event has zero lots? The Lots panel shows an empty state message: "No lots in this event."
- What happens when the API is unreachable? The panel that triggered the request shows an error state with a retry option.
- What happens on narrow viewports (< 768px)? The three-panel layout collapses to a stacked single-column layout with navigation between panels.
- What happens when clicking quickly between sellers? The latest request wins; earlier in-flight requests are superseded by HTMX's request cancellation behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render a three-region SPA shell layout on the home page: Left1 (Sellers), Left2 (Events), Main (Lots).
- **FR-002**: System MUST load seller events into Left2 via HTMX when a seller is clicked, without a full page reload.
- **FR-003**: System MUST load event lots into Main via HTMX when an event is clicked, without a full page reload.
- **FR-004**: System MUST visually highlight the currently selected seller in Left1 and the currently selected event in Left2.
- **FR-005**: System MUST clear the downstream panel(s) when a new upstream selection is made (new seller clears Events + Lots; new event clears Lots).
- **FR-006**: System MUST display the LotsDB brand logo (`static/catalog/lotsdb_logo.svg`) in the top navigation bar.
- **FR-007**: System MUST provide independent scrolling for each of the three panels.
- **FR-008**: System MUST provide pagination controls within each panel for large datasets.
- **FR-009**: System MUST show professional empty-state placeholders when no selection has been made or when a panel has no data.
- **FR-010**: System MUST show a loading indicator within a panel while an HTMX request is in flight.
- **FR-011**: System MUST preserve existing navigation to lot detail, override, search, and import pages.
- **FR-012**: System MUST maintain the existing catalog dropzone, search, and user controls in the top navigation bar.
- **FR-013**: System MUST serve HTMX partial responses (HTML fragments) for seller-events and event-lots endpoints.

### Key Entities

- **Seller**: Loaded from ABConnect API. Displayed in Left1 with name and customer display ID on a single row.
- **Event (Catalog)**: Loaded from ABConnect API. Displayed in Left2 with title and `customer_catalog_id | start_date` meta.
- **Lot**: Loaded from ABConnect API. Displayed in Main as cards with thumbnail image, lot number + description (bold), and truncated notes. Links to existing lot detail page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can navigate from seller → event → lots in under 3 clicks with no full page reloads.
- **SC-002**: Panel transitions (HTMX swaps) complete in under 500ms for typical datasets (< 100 items).
- **SC-003**: The layout is usable at viewport widths from 1024px to 2560px without horizontal scrolling.
- **SC-004**: All existing pages (lot detail, override, search, import) remain accessible and functional.
- **SC-005**: The visual design meets professional product standards — consistent typography, spacing, color, and branding throughout.
