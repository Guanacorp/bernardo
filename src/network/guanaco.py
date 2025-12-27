import os
import re
import requests
import time

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

GUANACO_HOST = os.environ.get("GUANACO_HOST").rstrip("/")
GUANACO_TOKEN = os.environ.get("GUANACO_TOKEN")
STRATEGY_TTL = 24 * 60 * 60
MAX_RETRIES = 5
BASE_DELAY = 10

_strategy_cache = {
    "expires": 0,
    "accepted": [],
    "refused": []
}

def get_strategy_uncached():
    retries = 0
    delay = BASE_DELAY
    while True:
        try:
            r = requests.get(
                f"{GUANACO_HOST}/api/scraper/strategy",
                timeout=3,
            )
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, requests.Timeout) as e:
            retries += 1
            if retries > MAX_RETRIES:
                raise
            print(f"[bernardo.debug] Request failed ({e})")
            print(f"[bernardo.debug] Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2

def get_strategy():
    global _strategy_cache

    now = time.time()
    if now < _strategy_cache["expires"]:
        return _strategy_cache

    data = get_strategy_uncached()

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
