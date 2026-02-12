# Research: Pagination UX Improvements

**Feature**: 009-pagination-ux | **Date**: 2026-02-12

## R1: HTMX-Compatible Jump-to-Page Input

**Decision**: Use a click-to-edit pattern — the page number span becomes an `<input type="number">` on click, with Enter triggering an HTMX request via `htmx.ajax()`.

**Rationale**: HTMX's `hx-get` is attribute-driven and works well for static links but not for dynamic user-typed values. Using `htmx.ajax()` from a JS event handler allows building the URL with the typed page number at runtime while still leveraging HTMX's swap/target/indicator machinery.

**Alternatives considered**:
- **Hidden form with `hx-get`**: Would require a form with hidden inputs and dynamic URL construction in the template. More template complexity for no benefit.
- **Full JS fetch + innerHTML**: Bypasses HTMX entirely. Loses integration with HTMX indicators, events, and history.
- **`hx-vals` with JS**: Could use `hx-vals="js:{page: getPageInput()}"` but this requires the URL to not include page param, adding complexity to the template logic.

**Implementation pattern**:
```javascript
// On Enter key in page input
const input = e.target;
const page = Math.max(1, Math.min(parseInt(input.value), parseInt(input.max)));
const url = input.dataset.baseUrl + '?page=' + page + input.dataset.extraParams;
htmx.ajax('GET', url, {target: input.dataset.target, swap: 'innerHTML'});
```

## R2: Page Size Selector with HTMX

**Decision**: Use a `<select>` element with `hx-get` that includes `page_size` as a query parameter. On change, navigate to page 1 with the new page size.

**Rationale**: HTMX natively supports `hx-get` on `<select>` with `hx-trigger="change"`. The URL can be pre-built in the template with `page=1&page_size=X` for each option, or we can use `hx-vals` to include the selected value. Since the options are static (10, 25, 50, 100), building the URL per-option in the template is simpler.

**Alternatives considered**:
- **JS-driven select**: Unnecessary — HTMX handles this natively.
- **Separate API param**: The `page_size` param already exists in `_parse_page_params()`, just not exposed in the panel pagination UI.

**Implementation pattern**: A standalone `<select>` with `hx-get` and `hx-trigger="change"` that swaps the panel content. The `hx-get` URL uses the `base_url` with `page=1&page_size=<value>`. Since the select needs a dynamic URL per option, we use JS to build the URL on change:
```html
<select class="page-size-select" onchange="paginatePageSize(this)">
  <option value="10">10</option>
  <option value="25" selected>25</option>
  ...
</select>
```

## R3: Pagination Context Extension (start_item / end_item)

**Decision**: Compute `start_item` and `end_item` in the view and pass them in the `paginated` context dict.

**Rationale**: Computing range in the view keeps the template simple (just `{{ paginated.start_item }}–{{ paginated.end_item }} of {{ paginated.total_items }}`). The Django template language has limited math capabilities — computing `(page-1)*page_size+1` in a template requires custom filters or awkward `add` chains.

**Alternatives considered**:
- **Custom template filter**: Adds a new file and registration boilerplate for simple arithmetic.
- **Compute in template with `add`**: Django's `add` filter only does addition, not multiplication. Would need chained variables and `with` blocks — fragile and unreadable.

**Implementation**:
```python
# In _paginate_locally() and where Paginated objects are used:
start_item = (page - 1) * page_size + 1
end_item = min(page * page_size, total)
paginated["start_item"] = start_item
paginated["end_item"] = end_item
```

For API-backed pagination (sellers, events), the ABConnect `Paginated` object doesn't have these fields. We'll compute and attach them after receiving the API response:
```python
def _enrich_pagination(paginated, page, page_size):
    """Add start_item/end_item to a paginated object or dict."""
    total = paginated.total_items if hasattr(paginated, 'total_items') else paginated['total_items']
    pg = paginated.page_number if hasattr(paginated, 'page_number') else paginated['page_number']
    start = (pg - 1) * page_size + 1
    end = min(pg * page_size, total)
    if isinstance(paginated, dict):
        paginated['start_item'] = start
        paginated['end_item'] = end
    else:
        # Wrap API Paginated object in a dict for uniform template access
        return {
            'page_number': paginated.page_number,
            'total_pages': paginated.total_pages,
            'total_items': paginated.total_items,
            'has_previous_page': paginated.has_previous_page,
            'has_next_page': paginated.has_next_page,
            'start_item': start,
            'end_item': end,
        }
    return paginated
```

## R4: Scroll-to-Top on HTMX Swap

**Decision**: Add an `htmx:afterSwap` listener in `shell.html` that scrolls the target panel to top.

**Rationale**: HTMX fires `htmx:afterSwap` after content is swapped. The event's `detail.target` gives us the panel container, which we can `scrollTop = 0`. This is a single line of JS in the existing event listener block.

**Alternatives considered**:
- **`hx-on::after-swap` attribute on pagination links**: Would need to be on every link/button — DRY violation.
- **CSS `scroll-behavior: auto` with anchor**: Over-engineered for a simple scrollTop reset.

**Implementation**:
```javascript
// In existing htmx:afterSwap listener in shell.html
// After swap, scroll the target panel to top
const target = e.detail.target;
if (target && target.closest('.panel')) {
    target.closest('.panel').scrollTop = 0;
}
```

## R5: Page Size Param Preservation

**Decision**: Pass `page_size` through `extra_params` in the pagination template, and include it in all pagination HTMX requests.

**Rationale**: The `extra_params` dict already handles `selected`, `name`, `title` preservation. Adding `page_size` to this dict ensures it persists across prev/next navigation. When page size changes, the select handler builds a fresh URL with `page=1`.

**Alternatives considered**:
- **Session storage (server-side)**: Adds state management complexity, Django session writes on every page size change. Over-engineered for this use case.
- **localStorage (client-side)**: Would require JS on every page load to read and inject. Fragile and not server-aware.

**Implementation**: In each panel view, include `page_size` in `extra_params` when it differs from the default:
```python
extra_params = {}
if page_size != default_page_size:
    extra_params["page_size"] = page_size
```
