import requests
import sys

BASE = 'http://127.0.0.1:8001'

try:
    r = requests.get(f"{BASE}/skus", timeout=30)
    r.raise_for_status()
    body = r.json()
    skus = body.get('skus') if isinstance(body, dict) else body
    print('SKUS count:', len(skus))
    print('SKUS sample:', skus[:5])

    sku = skus[0]
    print('\nTesting forecast for sku:', sku)
    fr = requests.get(f"{BASE}/forecast/{sku}?horizon=14", timeout=60)
    print('/forecast status', fr.status_code)
    if fr.status_code == 200:
        data = fr.json()
        print('forecast points:', len(data.get('data', [])))
    else:
        print('forecast error:', fr.text)

    print('\nTesting overview')
    ov = requests.get(f"{BASE}/overview?horizon=14", timeout=60)
    print('/overview status', ov.status_code)
    if ov.status_code == 200:
        print('overview keys:', list(ov.json().keys())[:10])
    else:
        print('overview error:', ov.text)

    print('\nTesting LLM summary (may require OPENAI_API_KEY)')
    llm = requests.get(f"{BASE}/llm/summary/{sku}?horizon=14", timeout=60)
    print('/llm/summary status', llm.status_code)
    print('llm response snippet:', llm.text[:400])

    print('\nTriggering training via API (/train)')
    tr = requests.post(f"{BASE}/train", timeout=10)
    print('/train status', tr.status_code, 'body:', tr.text)

except Exception as e:
    print('error during checks:', e)
    sys.exit(1)
