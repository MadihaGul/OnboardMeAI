import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8000'
repo = 'https://github.com/social-agile/Social'

def post(path, data):
    url = BASE + path
    b = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=b, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return resp.read().decode('utf-8'), resp.getcode()
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8'), e.code
    except Exception as e:
        return str(e), None

print('Posting /ingest... this may take a while')
body, status = post('/ingest', {'repo_url': repo})
print('INGEST STATUS:', status)
print(body)

print('\nPosting /query: What is this project about?')
body, status = post('/query', {'repo_url': repo, 'question': 'What is this project about?'})
print('QUERY STATUS:', status)
print(body)
