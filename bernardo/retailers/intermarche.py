import re
import json

NAME = "intermarche"

def extract_store_id(flow, rule):
    m = re.search(r"/pdvs/(\d+)/", flow.request.path)
    return m.group(1) if m else "unknown"

def extract_category_id(flow, rule):
    try:
        body = json.loads(flow.request.get_text())
        return body.get("category", "unknown")
    except Exception:
        return "unknown"

def extract_page(flow, rule):
    try:
        body = json.loads(flow.request.get_text())
        return body.get("page", "unknown")
    except Exception:
        return "unknown"

EXTRACTORS = {
    "store_id": extract_store_id,
    "category_id": extract_category_id,
    "page": extract_page,
}

__all__ = [
    "EXTRACTORS",
]
