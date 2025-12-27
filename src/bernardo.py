import json
import re

from datetime import datetime
from mitmproxy import http
from network import get_strategy, post_collect
from retailers import get_retailer

RULES = [
    {
        "retailer": "intermarche",
        "type": "category",
        "name": "category",
        "signature_suffix": "{store_id}_{category_id}_{page}",
        "host": "www.intermarche.com",
        "method": "POST",
        "path": re.compile(
            r"^/api/service/produits/v4/pdvs/\d+/products/byKeywordAndCategory$"
        ),
        "content_type": "application/json",
        "enabled": True,
        "save": True,
        "replay": False,
    },
    {
        "retailer": "carrefour",
        "name": "category-no-page",
        "type": "category",
        "signature_suffix": "{store_id}_{category}",
        "host": "www.carrefour.fr",
        "method": "GET",
        "path": re.compile(
            r"^/r/[^?]+"
        ),
        "content_type": "text/html",
        "enabled": False,
        "save": False,
        "replay": True,
    },
    {
        "retailer": "carrefour",
        "name": "category",
        "type": "category",
        "signature_suffix": "{store_id}_{category}_{page}",
        "host": "www.carrefour.fr",
        "method": "GET",
        "path": re.compile(
            r"^/r/[^?]+"
        ),
        "content_type": "application/json",
        "enabled": True,
        "save": True,
        "replay": False,
    }
]

def match_rule(flow):
    for r in RULES:
        path = r["path"]
        host = r["host"]
        method = r["method"]
        content_type = r["content_type"]

        if flow.request.pretty_host != host:
            request_host = flow.request.pretty_host
            continue
        if flow.request.method != method:
            request_method = flow.request.method
            continue
        if not path.match(flow.request.path):
            request_path = flow.request.path
            continue
        if content_type not in flow.response.headers.get("content-type", ""):
            response_content_type = flow.response.headers.get("content-type", "")
            continue
        return r
    return False

def get_metadata(retailer, flow, rule):
    metadata = {}
    for key, extractor in retailer.EXTRACTORS.items():
        try:
            metadata[key] = extractor(flow, rule)
        except Exception:
            metadata[key] = "error"

    return metadata

def build_signature(rule, metadata):
    retailer = rule["retailer"]
    type = rule["type"]
    suffix_tpl = rule.get("signature_suffix")

    signature = f"{retailer}_{type}"

    if suffix_tpl:
        suffix = suffix_tpl.format(**metadata)
        signature = f"{signature}_{suffix}"

    return signature

def build_payload(retailer, flow, rule, debug=False):
    request_body = None
    try:
        request_body = flow.request.get_text()
    except Exception:
        request_body = None

    metadata = get_metadata(retailer, flow, rule)
    print(metadata)
    signature = build_signature(rule, metadata)

    payload = {
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "retailer": rule["retailer"],
        "type": rule["type"],
        "metadata": metadata,
        "mode": "debug",
        "client": {
            "ip": flow.client_conn.peername[0],
            "user_agent": flow.request.headers.get("user-agent"),
        },
        "request": {
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "payload": request_body,
        },
        "response": {
            "headers": dict(flow.response.headers),
            "status_code": flow.response.status_code,
            "body": flow.response.get_text(),
        },
    }

    if debug is True:
        payload["mode"] = "debug"
        payload["request"]["headers"] = dict(flow.request.headers)

    return payload

def response(flow: http.HTTPFlow):
    if not flow.response:
        return

    try:
        strategy = get_strategy()
    except Exception:
        print("[bernardo.error] Could not connect to Guanaco.")
        return

    host = flow.request.host

    if any(pattern.search(host) for pattern in strategy["refused"]):
        return

    if not any(pattern.search(host) for pattern in strategy["accepted"]):
        print(f"[bernardo.explain] {host}")
        print(f"[bernardo.explain] {flow.request.path}")
        print(f"[bernardo.explain] {flow.request.method} {flow.request.pretty_url}")
        print(f"[bernardo.explain] {flow.request.get_text()}")

    rule = match_rule(flow)
    if not rule:
        return

    print(f"matched {rule}")

    retailer = get_retailer(rule["retailer"])
    name = rule["retailer"]
    if not retailer:
        return

    if rule.get("replay", False):
        retailer.replay(flow, rule)

    payload = build_payload(retailer, flow, rule, True)
    if rule.get("enabled", False) and rule.get("save", False):
        post_collect(payload)
