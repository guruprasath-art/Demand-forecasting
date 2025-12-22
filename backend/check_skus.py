import requests
import sys

try:
    r = requests.get("http://127.0.0.1:8001/skus", timeout=20)
    r.raise_for_status()
    skus = r.json()
    print('type:', type(skus))
    # If it's a list, print length and first 60 items. If dict, pretty-print keys and sample value.
    if isinstance(skus, list):
        print(len(skus))
        print(skus[:60])
    elif isinstance(skus, dict):
        print('dict keys:', list(skus.keys())[:10])
        # show a sample representation of the value
        for k, v in list(skus.items())[:3]:
            print(k, '->', repr(v)[:200])
    else:
        print('response repr:', repr(skus)[:400])
except Exception as e:
    print('error fetching /skus:', e)
    sys.exit(1)
