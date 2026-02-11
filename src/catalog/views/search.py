from django.shortcuts import render

from catalog import services


def search_lots_view(request):
    query = request.GET.get("q", "").strip()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))

    lots = None
    if query:
        lots = services.search_lots(request, query=query, page=page, page_size=page_size)

    return render(request, "catalog/search/results.html", {
        "query": query,
        "lots": lots.items if lots else [],
        "paginated": lots,
        "preserved_params": {"q": query} if query else {},
    })
