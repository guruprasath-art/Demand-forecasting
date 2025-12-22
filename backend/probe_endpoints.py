import sys
sys.path.insert(0, r"c:\Users\Guru Prasath\Desktop\Demand-forecasting\backend")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print('health ->', client.get('/health').json())
print('model/status ->', client.get('/model/status').json())
print('skus ->', client.get('/skus').json())
# Probe LLM - may fail if no API key; catch exceptions
try:
    r = client.get('/internal/llm/probe')
    print('llm/probe ->', r.status_code, r.text)
except Exception as e:
    print('llm/probe -> exception:', e)
