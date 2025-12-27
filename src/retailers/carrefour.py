import re
import json
from mitmproxy import http, ctx
from urllib.parse import urlencode

NAME = "carrefour"

def safe_header(flow, name, default):
    return flow.request.headers.get(name, default)


def replay_with_page(flow: http.HTTPFlow, page: int):
    if flow.metadata.get("replayed"):
        return

    replay_flow = flow.copy()
    replay_flow.metadata["replayed"] = True

    query = dict(replay_flow.request.query)
    query["page"] = str(page)
    replay_flow.request.query = query

    replay_flow.request.headers["Accept"] = "application/json, text/plain, */*"
    replay_flow.request.headers["X-Requested-With"] = "XMLHttpRequest"
    replay_flow.request.headers["Referer"] = replay_flow.request.url

    ctx.master.commands.call("replay.client", [replay_flow])

def extract_page(flow, rule):
    return flow.request.query.get("page", "1")

def extract_category_id(flow, rule):
    m = re.search(r"^/r/(?P<category>[^?]+)", flow.request.path)
    return m.group("category") if m else "unknown"

def extract_store_id(flow, rule):
    cookies = flow.request.cookies
    store_id = cookies.get("FRONTAL_STORE")
    if store_id is None:
        rule["save"] = False
    return store_id

def replay(flow, rule):
    page = extract_page(flow, rule)
    replay_with_page(flow, page)

EXTRACTORS = {
    "store_id": extract_store_id,
    "category": extract_category_id,
    "page": extract_page,
}

__all__ = [
    "EXTRACTORS",
]
