from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
resp = client.post('/train')
print('status', resp.status_code)
print(resp.json())
