import os
import re
import requests
import time

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

GUANACO_HOST = os.environ.get("GUANACO_HOST").rstrip("/")
GUANACO_TOKEN = os.environ.get("GUANACO_TOKEN")
STRATEGY_TTL = 24 * 60 * 60

_strategy_cache = {
    "expires": 0,
    "accepted": [],
    "refused": []
}

def get_strategy():
    global _strategy_cache

    now = time.time()
    if now < _strategy_cache["expires"]:
        return _strategy_cache

    r = requests.get(
        f"{GUANACO_HOST}/api/scraper/strategy",
        timeout=3,
    )
    r.raise_for_status()

    data = r.json()

    _strategy_cache = {
        "expires": time.time() + STRATEGY_TTL,
        "accepted": [re.compile(p) for p in data["acceptedHosts"]],
        "refused": [re.compile(p) for p in data["refusedHosts"]],
    }

    print("[bernardo.debug] strategy refreshed")

    return _strategy_cache

def post_collect(payload):
    try:
        endpoint = f"{GUANACO_HOST}/api/scraper/collect"
        r = requests.post(
            endpoint,
            json=payload,
            headers={
                "X-Bernardo-Token": f"{GUANACO_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        r.raise_for_status()
        print(f"[bernardo.info] sent {payload['retailer']} {payload['type']} -> {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"[bernardo.error] {e}")
        print(f"[bernardo.error] {r}")
