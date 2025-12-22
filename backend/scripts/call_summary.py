import requests
try:
    r=requests.get('http://127.0.0.1:8000/llm/summary/1?horizon=14', timeout=30)
    print('STATUS', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
except Exception as e:
    print('EXC', e)
