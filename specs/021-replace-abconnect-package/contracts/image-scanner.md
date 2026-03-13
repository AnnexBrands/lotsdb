# Image Scanner Contract

**Date**: 2026-03-13

## Function: scan_lot_images

Probes CDN URLs for a single lot to discover available images.

### Input

```
house_id: int       — Seller/house identifier
catalog_id: int     — Catalog identifier
lot_id: int         — Lot identifier
```

### Output

```
List[str]           — List of verified image URLs (may be empty)
```

### Behavior

1. Construct URL: `https://s3.amazonaws.com/static2.liveauctioneers.com/{house_id}/{catalog_id}/{lot_id}_{n}_m.jpg`
2. Start at n=1
3. Send HTTP HEAD request to URL
4. If 2xx: add URL to result list, reset consecutive failure counter, increment n
5. If non-2xx (4xx, 5xx, network error): increment consecutive failure counter, increment n
6. If consecutive failures >= 3: stop
7. If n > 200: stop (safety bound)
8. Return collected URLs

### Error Handling

- Network timeouts: count as non-2xx failure
- 5xx server errors: count as non-2xx failure (no retry per clarification)
- Connection errors: count as non-2xx failure, log warning

### Constraints

- Maximum 200 probes per lot
- HTTP HEAD method (minimal bandwidth)
- Timeout per probe: 5 seconds (reasonable for CDN)

## Function: scan_images_for_catalog

Scans images for all lots in a catalog import, parallelized across lots.

### Input

```
lots: List[LotInfo]     — List of (house_id, catalog_id, lot_id) tuples
max_workers: int = 10   — Thread pool size (matches LOT_FETCH_MAX_WORKERS)
```

### Output

```
Dict[int, List[str]]    — Mapping of lot_id → list of verified image URLs
```

### Behavior

1. Create ThreadPoolExecutor with max_workers
2. Submit scan_lot_images for each lot in parallel
3. Collect results, mapping lot_id to URL list
4. Log summary: total lots scanned, total images found, total probes made

### Usage Points

- `importers.py` CatalogDataBuilder._add_lot(): replaces `build_image_url()` static template
- `services.py` merge_catalog(): replaces `file_lot.image_links` passthrough
