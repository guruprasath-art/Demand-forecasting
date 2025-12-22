from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def pretty(r):
    try:
        return json.dumps(r.json(), indent=2)[:4000]
    except Exception:
        return r.text[:4000]

print('Running in-process API tests')

def do_get(path, params=None):
    print('\nGET', path, 'params=', params)
    r = client.get(path, params=params)
    print('status:', r.status_code)
    print(pretty(r))
    return r

# Basic checks
checks = [
    ('/health', None),
    ('/skus', None),
    ('/sku_health', {'horizon': 14}),
    ('/overview', {'horizon': 14}),
    ('/executive/pulse', {'horizon': 14}),
    ('/model/status', None),
    ('/internal/llm/probe', None),
]

first_sku = None
for path, params in checks:
    try:
        r = do_get(path, params)
        if path == '/skus' and r.status_code == 200:
            data = r.json()
            skus = data.get('skus', [])
            if skus:
                first_sku = skus[0]
                print('first sku:', first_sku)
    except Exception as e:
        print('ERROR calling', path, e)

if first_sku:
    print('\nTesting forecast and summary for', first_sku)
    r = client.get(f'/forecast/{first_sku}', params={'horizon': 14})
    print('forecast status', r.status_code)
    print(pretty(r))

    r = client.get(f'/llm/summary/{first_sku}', params={'horizon': 14})
    print('llm summary status', r.status_code)
    print(pretty(r))

print('\nTrigger training')
r = client.post('/train')
print('train status', r.status_code)
print(pretty(r))

print('\nDone in-process tests')
