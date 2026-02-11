# Feature Specification: Auction Catalog Manager

**Feature Branch**: `001-auction-catalog-manager`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "Build an application to manage auction catalogs. We will use https://catalog-api.abconnect.co/swagger/v1/swagger.json with a wrapper found at /usr/src/pkgs/ABConnectTools. There are Sellers → Events → Lots which we will review and set overrides for values."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Seller, Event, and Lot Hierarchy (Priority: P1)

As a catalog manager, I want to navigate the hierarchy of Sellers, Events, and Lots so that I can find specific auction items to review. The application presents a clear drill-down flow: I first see a list of sellers, then select a seller to view their events (auction catalogs), then select an event to see its lots.

**Why this priority**: Navigation is the foundation of the application. Without the ability to browse and locate items, no other functionality is usable.

**Independent Test**: Can be fully tested by logging in, viewing the seller list, selecting a seller to see their events, and selecting an event to see its lots. Delivers the core value of organized catalog browsing.

**Acceptance Scenarios**:

1. **Given** I am logged in, **When** I open the application, **Then** I see a list of sellers with their name, display ID, and active status.
2. **Given** I am viewing the seller list, **When** I select a seller, **Then** I see that seller's events with title, agent, start/end dates, and completion status.
3. **Given** I am viewing an event, **When** I select it, **Then** I see all lots belonging to that event with their lot number, item ID, and description.
4. **Given** I am viewing any list, **When** there are more results than fit on one page, **Then** I can paginate through the results.
5. **Given** I am viewing sellers, **When** I filter by name or active status, **Then** the list updates to show only matching sellers.
6. **Given** I am viewing events, **When** I filter by title, date range, agent, or completion status, **Then** the list updates to show only matching events.

---

### User Story 2 - Review Lot Details (Priority: P2)

As a catalog manager, I want to view the full details of a lot so that I can assess its current data before deciding whether overrides are needed. I can see the lot's initial data (dimensions, weight, quantity, value, description, condition notes) alongside any existing overrides and associated images.

**Why this priority**: Reviewing lot data is the prerequisite to making informed override decisions. Users need to see what they are working with before making changes.

**Independent Test**: Can be tested by navigating to any lot and verifying that all initial data fields, existing overrides, and images are displayed clearly.

**Acceptance Scenarios**:

1. **Given** I am viewing a lot list, **When** I select a lot, **Then** I see the lot's initial data including quantity, dimensions (L/W/H), weight, value, description, case/pack info, condition notes, and handling flags.
2. **Given** a lot has existing overrides, **When** I view the lot detail, **Then** I see the overrides displayed alongside or compared against the initial data so differences are apparent.
3. **Given** a lot has associated images, **When** I view the lot detail, **Then** I see the images displayed with the lot information.
4. **Given** I am viewing lot details, **When** the lot has special handling flags (force crate, do not tip), **Then** these are clearly indicated.

---

### User Story 3 - Set and Edit Lot Overrides (Priority: P3)

As a catalog manager, I want to set overrides on specific lot values so that I can correct or adjust data that differs from the initial catalog entry. I can override individual fields (dimensions, weight, quantity, value, description, condition, commodity, handling flags) without altering the original data.

**Why this priority**: Override management is the core business action of the application — the reason the tool exists. It is P3 only because it depends on P1 (navigation) and P2 (review) being in place first.

**Independent Test**: Can be tested by navigating to a lot, setting an override on one or more fields, saving, and confirming the override appears in the lot detail view.

**Acceptance Scenarios**:

1. **Given** I am viewing a lot's details, **When** I choose to add an override, **Then** I see an editable form pre-populated with the lot's current values.
2. **Given** I am editing an override, **When** I change one or more fields and save, **Then** the override is persisted and the lot detail view reflects the new override.
3. **Given** a lot already has an override, **When** I choose to edit it, **Then** the form is pre-populated with the existing override values.
4. **Given** I am editing an override, **When** I cancel without saving, **Then** no changes are persisted.
5. **Given** I have saved an override, **When** I return to the lot detail, **Then** I can clearly see which values differ from the initial data.

---

### User Story 4 - Search and Filter Lots Across Events (Priority: P4)

As a catalog manager, I want to search for lots by item ID or lot number so that I can quickly locate specific items without navigating the full hierarchy.

**Why this priority**: Improves efficiency for users who already know which lot they need, but not strictly required for the core review-and-override workflow.

**Independent Test**: Can be tested by entering a known item ID or lot number in the search and verifying the correct lot is returned.

**Acceptance Scenarios**:

1. **Given** I am on any screen, **When** I search by customer item ID, **Then** I see matching lots with their parent event and seller context.
2. **Given** I am on any screen, **When** I search by lot number, **Then** I see matching lots with their parent event and seller context.
3. **Given** my search returns results, **When** I select a lot from the results, **Then** I am taken to the full lot detail view.

---

### Edge Cases

- What happens when a lot has no initial data for certain fields (e.g., missing dimensions)? Empty fields display as blank/not set rather than zero.
- How does the system handle a seller with no events, or an event with no lots? Display an empty state with a clear message.
- What happens when an override is set with identical values to the initial data? The override is saved as-is; no validation prevents identical values.
- How does the system behave when a lot belongs to multiple catalogs? The lot is shown under each associated catalog; overrides apply to the lot globally.
- What happens when an event is marked as completed? Overrides remain editable; completed status does not lock editing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a navigable hierarchy of Sellers, Events, and Lots.
- **FR-002**: System MUST support paginated listing for sellers, events, and lots.
- **FR-003**: System MUST allow filtering sellers by name, display ID, and active status.
- **FR-004**: System MUST allow filtering events by title, agent, date range, and completion status.
- **FR-005**: System MUST allow filtering lots by customer item ID and lot number.
- **FR-006**: System MUST display full lot detail including all initial data fields, existing overrides, and associated images.
- **FR-007**: System MUST visually distinguish override values from initial data values when both are present.
- **FR-008**: System MUST allow users to create new overrides for a lot, specifying values for any combination of: quantity, dimensions (L/W/H), weight, value, description, case/pack, condition notes, commodity, force crate flag, and do not tip flag.
- **FR-009**: System MUST allow users to edit existing overrides.
- **FR-010**: System MUST provide a search capability to find lots by customer item ID or lot number across all events.
- **FR-011**: System MUST show breadcrumb-style context (Seller > Event > Lot) so users always know their position in the hierarchy.
- **FR-012**: System MUST authenticate users before allowing access to catalog data.
- **FR-013**: System MUST display empty states with meaningful messages when a seller has no events or an event has no lots.

### Key Entities

- **Seller**: An auction house or consignor who provides items for sale. Identified by name and a customer-facing display ID. May be active or inactive.
- **Event (Catalog)**: A specific auction or sale event organized by one or more sellers. Has a title, managing agent, date range, and completion status. Contains lots.
- **Lot**: An individual item or group of items offered in an auction event. Has initial data (dimensions, weight, quantity, value, description, condition, handling requirements) and may have one or more overrides that adjust specific values. May include product images.
- **Override**: A set of adjusted values for a lot that takes precedence over the initial data. Tracks which fields have been changed from the original.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate from the seller list to a specific lot's detail view in under 4 clicks.
- **SC-002**: Users can create or edit a lot override and save it in under 2 minutes.
- **SC-003**: Users can locate a specific lot by search in under 30 seconds.
- **SC-004**: All list views load and display results within 3 seconds under normal conditions.
- **SC-005**: 90% of users can complete the review-and-override workflow on first attempt without assistance.
- **SC-006**: Override changes are immediately reflected in the lot detail view after saving.

## Assumptions

- Users will authenticate with existing credentials managed by the ABConnect identity system.
- The application will be used by internal staff (catalog managers) who are familiar with auction terminology.
- The "Events" terminology used in the user-facing application maps to "Catalogs" in the underlying system.
- Lot overrides are additive — the original initial data is always preserved and viewable.
- Overrides remain editable regardless of event completion status. Managers may need to correct data after an auction closes.
- The application is a web application, accessible via a standard browser.
