"""Management command: import catalog data from spreadsheet files."""

from pathlib import Path

from django.core.management.base import BaseCommand

from ABConnect import ABConnectAPI
from catalog.importers import load_file, list_import_files

FILES_DIR = Path(__file__).resolve().parent.parent.parent / "FILES"


class Command(BaseCommand):
    help = "Import catalog data from spreadsheet files into the Catalog API"

    def add_arguments(self, parser):
        parser.add_argument(
            "files", nargs="*", type=str,
            help="File paths to import. If none given, imports all files from catalog/FILES/",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Build request and show summary without calling API",
        )
        parser.add_argument(
            "--agent", type=str, default="DLC",
            help="Default agent code (default: DLC)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        agent = options["agent"]
        file_args = options["files"]

        if file_args:
            paths = [Path(f) for f in file_args]
            for p in paths:
                if not p.exists():
                    self.stderr.write(self.style.ERROR(f"File not found: {p}"))
                    return
        else:
            paths = list_import_files(FILES_DIR)
            if not paths:
                self.stderr.write(self.style.WARNING(f"No importable files in {FILES_DIR}"))
                return
            self.stdout.write(f"Found {len(paths)} file(s) in {FILES_DIR}")

        api = None
        if not dry_run:
            api = ABConnectAPI()

        for path in paths:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\nProcessing: {path.name}"))

            try:
                request, summary = load_file(path, agent=agent)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to load {path.name}: {e}"))
                continue

            self.stdout.write(summary)

            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY RUN] Skipping API call"))
            else:
                try:
                    api.catalog.bulk.insert(request)
                    self.stdout.write(self.style.SUCCESS("Imported successfully"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"API error: {e}"))

        self.stdout.write(self.style.SUCCESS("\nDone."))
