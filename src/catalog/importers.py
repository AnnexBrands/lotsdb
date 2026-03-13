"""Catalog file import logic.

Transforms flat spreadsheet rows into nested bulk insert dicts for the Catalog API.
"""

import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from catalog.services import scan_lot_images


# =============================================================================
# Configuration
# =============================================================================

CPACK_MAP = {"nf": "1", "lf": "2", "f": "3", "vf": "4", "pbo": "pbo"}
DEFAULT_CPACK = "3"
DEFAULT_AGENT = "DLC"

SUPPORTED_EXTENSIONS = {".xlsx", ".csv", ".json"}


# =============================================================================
# Converters
# =============================================================================


def parse_datetime(value) -> datetime:
    """Parse datetime from various formats."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M"]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    raise ValueError(f"Cannot parse datetime: {value}")


def ensure_future(dt: datetime) -> datetime:
    """Ensure datetime is in the future; substitute year 2099 if in the past."""
    if dt <= datetime.now():
        # Handle leap-day dates: Feb 29 doesn't exist in 2099
        if dt.month == 2 and dt.day == 29:
            return dt.replace(year=2099, day=28)
        return dt.replace(year=2099)
    return dt


def to_float(value, default: float = 0.0) -> float:
    """Safely convert to float."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_int(value, default: int = 1) -> int:
    """Safely convert to int."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def convert_dimensions(value: float, dim_type: str) -> float:
    """Convert dimensions to inches."""
    conversions = {"in": 1.0, "cm": 1 / 2.54, "mm": 1 / 25.4}
    return value * conversions.get(dim_type, 1.0)


def convert_weight(value: float, weight_type: str) -> float:
    """Convert weight to pounds."""
    conversions = {"lb": 1.0, "kg": 2.20462, "oz": 1 / 16}
    return value * conversions.get(weight_type, 1.0)


def convert_cpack(value: str) -> str:
    """Convert fragility code to cpack value."""
    if not value:
        return DEFAULT_CPACK
    return CPACK_MAP.get(value.lower().strip(), DEFAULT_CPACK)


# =============================================================================
# File Loading
# =============================================================================


def _load_xlsx(path: Path) -> list[dict]:
    """Load an XLSX file and return list of dicts (one per row)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    return [dict(zip(headers, row)) for row in rows[1:]]


def _load_csv(path: Path) -> list[dict]:
    """Load a CSV file and return list of dicts."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _load_json(path: Path) -> list[dict]:
    """Load a JSON file and return list of dicts."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def _load_data(path: Path) -> list[dict]:
    """Load data from a file based on its extension."""
    ext = path.suffix.lower()
    if ext == ".xlsx":
        return _load_xlsx(path)
    elif ext == ".csv":
        return _load_csv(path)
    elif ext == ".json":
        return _load_json(path)
    raise ValueError(f"Unsupported file type: {ext}")


# =============================================================================
# Data Builder
# =============================================================================


class CatalogDataBuilder:
    """Builds bulk insert dict from spreadsheet rows."""

    def __init__(self, agent: str = DEFAULT_AGENT):
        self.agent = agent
        self.catalogs_data: dict[int, dict] = {}
        self.catalog_sellers: dict[int, dict[int, dict]] = defaultdict(dict)
        self.catalog_lots: dict[int, list] = defaultdict(list)

    def add_row(self, row: dict) -> None:
        """Process a single spreadsheet row."""
        catalog_id = to_int(row["Catalog ID"])
        seller_id = to_int(row["House ID"])

        self._add_catalog(catalog_id, row)
        self._add_seller(catalog_id, seller_id, row)
        self._add_lot(catalog_id, seller_id, row)

    def _add_catalog(self, catalog_id: int, row: dict) -> None:
        if catalog_id in self.catalogs_data:
            return

        start_date = ensure_future(parse_datetime(row["Catalog Start Date"]))
        end_date = start_date + timedelta(hours=1)

        self.catalogs_data[catalog_id] = {
            "customer_catalog_id": str(catalog_id),
            "title": row.get("Catalog Title", ""),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "agent": row.get("Agent", self.agent),
        }

    def _add_seller(self, catalog_id: int, seller_id: int, row: dict) -> None:
        if seller_id in self.catalog_sellers[catalog_id]:
            return

        self.catalog_sellers[catalog_id][seller_id] = {
            "customer_display_id": seller_id,
            "name": row.get("House Name"),
            "is_active": True,
        }

    def _add_lot(self, catalog_id: int, seller_id: int, row: dict) -> None:
        lot_id = to_int(row["Lot ID"])
        lot_number = str(row.get("Lot Num", "")).strip()
        lot_title = row.get("Lot Title", "")
        lot_description = row.get("Lot Description", "")

        dim_type = row.get("Shipping Dimension Type", "in")
        weight_type = row.get("Shipping Weight Type", "lb")

        h = convert_dimensions(to_float(row.get("Shipping Height")), dim_type)
        w = convert_dimensions(to_float(row.get("Shipping Width")), dim_type)
        depth = convert_dimensions(to_float(row.get("Shipping Depth")), dim_type)
        wgt = convert_weight(to_float(row.get("Shipping Weight")), weight_type)
        qty = to_int(row.get("Shipping Quantity"), 1)

        fragility = row.get("Fragility", "f")
        cpack = convert_cpack(fragility)
        force_crate = str(row.get("Crate", "")).lower() == "ct"

        description = f"{lot_number} {lot_title}".strip()

        initial_data = {
            "qty": qty, "h": h, "w": w, "l": depth, "wgt": wgt,
            "cpack": cpack, "description": description,
            "notes": lot_description, "force_crate": force_crate,
        }

        image_links = scan_lot_images(seller_id, catalog_id, lot_id)

        lot = {
            "customer_item_id": str(lot_id),
            "lot_number": lot_number,
            "initial_data": initial_data,
            "overriden_data": [],
            "image_links": image_links,
        }

        self.catalog_lots[catalog_id].append(lot)

    def build(self) -> dict:
        """Build final bulk insert request dict."""
        catalogs = []

        for catalog_id, cat_data in self.catalogs_data.items():
            sellers = list(self.catalog_sellers[catalog_id].values())

            catalog = {
                "customer_catalog_id": cat_data["customer_catalog_id"],
                "title": cat_data["title"],
                "start_date": cat_data["start_date"],
                "end_date": cat_data["end_date"],
                "agent": cat_data["agent"],
                "sellers": sellers,
                "lots": self.catalog_lots[catalog_id],
            }
            catalogs.append(catalog)

        return {"catalogs": catalogs}

    def summary(self) -> str:
        """Return summary of built data."""
        lines = [f"Catalogs: {len(self.catalogs_data)}"]
        for catalog_id, cat_data in self.catalogs_data.items():
            sellers = len(self.catalog_sellers[catalog_id])
            lots = len(self.catalog_lots[catalog_id])
            lines.append(f"  {catalog_id}: {cat_data['title'][:40]}")
            lines.append(f"    Sellers: {sellers}, Lots: {lots}")
        return "\n".join(lines)


# =============================================================================
# Public API
# =============================================================================


def load_file(path: str | Path, agent: str = DEFAULT_AGENT) -> tuple[dict, str]:
    """Load a spreadsheet and return (bulk_insert_dict, summary_string).

    Args:
        path: Path to spreadsheet (xlsx, csv, json)
        agent: Default agent code for catalogs

    Returns:
        Tuple of (bulk insert dict, human-readable summary)
    """
    path = Path(path)
    data = _load_data(path)

    builder = CatalogDataBuilder(agent=agent)
    for row in data:
        builder.add_row(row)

    request = builder.build()
    summary = f"File: {path.name} ({len(data)} rows)\n{builder.summary()}"
    return request, summary


def list_import_files(directory: str | Path) -> list[Path]:
    """List importable files in a directory."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
