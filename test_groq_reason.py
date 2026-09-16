import os, json, urllib.request, urllib.error
from dotenv import load_dotenv
load_dotenv(r'D:\codeguard-ai-stage3\.env')
key = os.getenv('GROQ_API_KEY')
body = json.dumps({'model': 'openai/gpt-oss-20b', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 5}).encode()
req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', data=body, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}, method='POST')
try:
    r = urllib.request.urlopen(req, timeout=15)
    print('OK:', r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print('STATUS:', e.code)
    print('REASON:', e.read().decode()[:500])
