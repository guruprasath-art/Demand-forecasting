import os, requests, json
from dotenv import load_dotenv

root = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(root, '.env'))
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print('No OPENAI_API_KEY in backend/.env; aborting')
    raise SystemExit(1)

# Try a few common OpenAI model IDs
model_ids = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo']

results = {}
url = 'https://api.openai.com/v1/chat/completions'
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
for mid in model_ids:
    try:
        resp = requests.post(url, headers=headers, json={
            'model': mid,
            'messages': [{'role': 'user', 'content': 'probe'}],
            'max_tokens': 8
        }, timeout=10)
        status = resp.status_code
        try:
            data = resp.json()
        except Exception:
            data = {'text': resp.text}
        results[mid] = {'status': status, 'body': data}
    except Exception as e:
        results[mid] = {'status': 'error', 'body': str(e)}

print(json.dumps(results, indent=2))
