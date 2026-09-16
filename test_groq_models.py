import os, json, urllib.request, urllib.error
from dotenv import load_dotenv
load_dotenv(r'D:\codeguard-ai-stage3\.env')
key = os.getenv('GROQ_API_KEY')
models = ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b', 'groq/compound-mini', 'groq/compound', 'openai/gpt-oss-20b']
for m in models:
    body = json.dumps({'model': m, 'messages': [{'role': 'user', 'content': 'Say OK'}], 'max_tokens': 5}).encode()
    req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', data=body, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}, method='POST')
    try:
        r = urllib.request.urlopen(req, timeout=15)
        print(m, '-> OK')
    except urllib.error.HTTPError as e:
        print(m, '-> HTTP', e.code)
    except Exception as e:
        print(m, '-> ERR', e)
