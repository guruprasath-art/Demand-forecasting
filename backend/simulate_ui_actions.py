import requests, sys, time
BASE = 'http://127.0.0.1:8001'
out = []

try:
    r = requests.get(f"{BASE}/skus", timeout=30)
    r.raise_for_status()
    body = r.json()
    skus = body.get('skus') if isinstance(body, dict) else body
    out.append(('skus_count', len(skus)))
    out.append(('skus_sample', skus[:6]))

    # pick a small set of SKUs to test interactions
    test_skus = skus[:3]

    for sku in test_skus:
        for horizon in (7, 14, 30):
            path = f"/forecast/{sku}?horizon={horizon}"
            try:
                fr = requests.get(f"{BASE}{path}", timeout=30)
                out.append((f'/forecast {sku} h={horizon} status', fr.status_code))
                if fr.status_code == 200:
                    d = fr.json()
                    out.append((f'/forecast {sku} h={horizon} points', len(d.get('data', []))))
                else:
                    out.append((f'/forecast {sku} h={horizon} error', fr.text[:400]))
            except Exception as e:
                out.append((f'/forecast {sku} h={horizon} exception', str(e)))

    # Overview
    try:
        ov = requests.get(f"{BASE}/overview?horizon=14", timeout=30)
        out.append(('/overview status', ov.status_code))
        if ov.status_code == 200:
            out.append(('/overview keys', list(ov.json().keys())[:10]))
        else:
            out.append(('/overview error', ov.text[:400]))
    except Exception as e:
        out.append(('/overview exception', str(e)))

    # Model status
    try:
        ms = requests.get(f"{BASE}/model/status", timeout=10)
        out.append(('/model/status', ms.status_code))
        out.append(('model/status body', ms.json()))
    except Exception as e:
        out.append(('/model/status exception', str(e)))

    # Internal LLM probe
    try:
        probe = requests.get(f"{BASE}/internal/llm/probe", timeout=30)
        out.append(('/internal/llm/probe', probe.status_code))
        out.append(('probe snippet', probe.text[:400]))
    except Exception as e:
        out.append(('/internal/llm/probe exception', str(e)))

    # LLM summary for first SKU
    sku = test_skus[0]
    try:
        llm = requests.get(f"{BASE}/llm/summary/{sku}?horizon=14", timeout=60)
        out.append(('/llm/summary', llm.status_code))
        out.append(('llm snippet', llm.text[:800]))
    except Exception as e:
        out.append(('/llm/summary exception', str(e)))

    # Trigger training via API
    try:
        tr = requests.post(f"{BASE}/train", timeout=10)
        out.append(('/train', tr.status_code))
        out.append(('train body', tr.text[:400]))
    except Exception as e:
        out.append(('/train exception', str(e)))

except Exception as e:
    print('fatal error contacting backend:', e)
    sys.exit(1)

# print report
for k, v in out:
    print(f"{k}: {v}")

print('\nSimulation complete')
