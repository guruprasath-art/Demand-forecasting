import os, requests, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key=os.getenv('OPENAI_API_KEY')
model=os.getenv('OPENAI_MODEL','gpt-3.5-turbo')
url='https://api.openai.com/v1/chat/completions'
headers={'Authorization': f'Bearer {api_key}', 'Content-Type':'application/json'}
body={'model':model, 'messages':[{'role':'user','content':'hello'}], 'max_tokens':32}
try:
    r=requests.post(url, headers=headers, json=body, timeout=20)
    print('STATUS_CODE', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('EXC', repr(e))
