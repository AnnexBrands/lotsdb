import tempfile
from pathlib import Path

from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from catalog import services
from catalog.importers import load_file, list_import_files, SUPPORTED_EXTENSIONS

FILES_DIR = Path(__file__).resolve().parent.parent / "FILES"


def import_list(request):
    files = list_import_files(FILES_DIR)
    file_info = []
    for f in files:
        size = f.stat().st_size
        if size >= 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        file_info.append({"name": f.name, "size": size_str})

    return render(request, "catalog/imports/list.html", {"files": file_info})


def import_file(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("import_list"))

    filename = request.POST.get("filename", "")
    if not filename:
        messages.error(request, "No filename specified.")
        return HttpResponseRedirect(reverse("import_list"))

    # Prevent path traversal
    safe_name = Path(filename).name
    file_path = FILES_DIR / safe_name
    if not file_path.is_file():
        messages.error(request, f"File not found: {safe_name}")
        return HttpResponseRedirect(reverse("import_list"))

    try:
        bulk_request, summary = load_file(file_path)
    except Exception as e:
        messages.error(request, f"Failed to read {safe_name}: {e}")
        return HttpResponseRedirect(reverse("import_list"))

    try:
        services.bulk_insert(request, bulk_request)
        messages.success(request, f"Imported {safe_name}\n{summary}")
    except Exception as e:
        messages.error(request, f"API error importing {safe_name}: {e}")

    return HttpResponseRedirect(reverse("import_list"))


@require_POST
def upload_catalog(request):
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)

    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return JsonResponse(
            {"success": False, "error": f"Unsupported file type: {suffix}. Accepted: {exts}"},
            status=400,
        )

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
            bulk_request, summary = load_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Failed to parse file: {e}"}, status=400)

    if not bulk_request.catalogs:
        return JsonResponse({"success": False, "error": "File contains no catalog data"}, status=400)

    customer_catalog_id = bulk_request.catalogs[0].customer_catalog_id

    # Check if catalog already exists — merge path (US2)
    existing_catalog_id = services.find_catalog_by_customer_id(request, customer_catalog_id)
    if existing_catalog_id:
        try:
            result = services.merge_catalog(request, bulk_request, existing_catalog_id)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Merge failed: {e}"},
                status=500,
            )
        response = {
            "success": True,
            "redirect": "/",
            "merge": {
                "added": result["added"],
                "updated": result["updated"],
                "unchanged": result["unchanged"],
                "failed": result["failed"],
            },
        }
        if result.get("errors"):
            response["warnings"] = result["errors"]
        return JsonResponse(response)

    # New catalog path — bulk insert
    try:
        services.bulk_insert(request, bulk_request)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Import failed: {e}"}, status=500)

    event_id = services.find_catalog_by_customer_id(request, customer_catalog_id)
    return JsonResponse({"success": True, "redirect": "/"})
