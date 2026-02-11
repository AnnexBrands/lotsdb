from pathlib import Path

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from catalog import services
from catalog.importers import load_file, list_import_files

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
