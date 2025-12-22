import requests
import sys
import json

BASE = "http://127.0.0.1:8001"
TIMEOUT = 20

def safe_get(path, params=None):
    url = BASE + path
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        return r.status_code, r.text
    except Exception as e:
        return None, f"ERROR: {e}"

def safe_post(path, json_body=None):
    url = BASE + path
    try:
        r = requests.post(url, json=json_body, timeout=TIMEOUT)
        return r.status_code, r.text
    except Exception as e:
        return None, f"ERROR: {e}"

def pretty(s):
    try:
        o = json.loads(s)
        return json.dumps(o, indent=2)[:4000]
    except Exception:
        return s[:4000]

if __name__ == '__main__':
    checks = [
        ("GET", "/health", None),
        ("GET", "/skus", None),
        ("GET", "/sku_health", {"horizon":14}),
        ("GET", "/overview", {"horizon":14}),
        ("GET", "/executive/pulse", {"horizon":14}),
        ("GET", "/model/status", None),
        ("GET", "/internal/llm/probe", None),
    ]

    print("Running API smoke tests against:", BASE)
    first_sku = None
    for method, path, params in checks:
        print(f"\n{method} {path} params={params}")
        if method == "GET":
            status, body = safe_get(path, params=params)
        else:
            status, body = None, "unsupported"
        print("status:", status)
        print(pretty(body))
        if path == "/skus" and status == 200:
            try:
                obj = json.loads(body)
                skus = obj.get("skus", [])
                if skus:
                    first_sku = skus[0]
                    print("first SKU:", first_sku)
            except Exception:
                pass

    if first_sku:
        print(f"\nTesting forecast and llm summary for SKU: {first_sku}")
        s, b = safe_get(f"/forecast/{requests.utils.requote_uri(first_sku)}", params={"horizon":14})
        print("/forecast status:", s)
        print(pretty(b))

        s, b = safe_get(f"/llm/summary/{requests.utils.requote_uri(first_sku)}", params={"horizon":14})
        print("/llm/summary status:", s)
        print(pretty(b))

    print("\nTriggering training (POST /train)")
    s, b = safe_post("/train")
    print("/train status:", s)
    print(pretty(b))

    print("\nDone.")
