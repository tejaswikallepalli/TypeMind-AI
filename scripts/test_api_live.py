import urllib.request
import json

def test_endpoint(payload):
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/analyze',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

# 1. Python test
res_py = test_endpoint({'source_code': 'x: int = "bad"\n', 'language': 'python'})
print("Python Status:", res_py['status'], "Lang:", res_py['language'], "Findings:", len(res_py['findings']))

# 2. TypeScript test
res_ts = test_endpoint({'source_code': 'let x: number = "bad";\n', 'language': 'typescript'})
print("TypeScript Status:", res_ts['status'], "Lang:", res_ts['language'], "Findings:", len(res_ts['findings']), "Msg:", res_ts['findings'][0]['message'] if res_ts['findings'] else None)

# 3. Java test (tool unavailable)
res_java = test_endpoint({'source_code': 'public class Main { int x = "bad"; }', 'language': 'java'})
print("Java Status:", res_java['status'], "Support:", res_java['support_level'], "Msg:", res_java['status_message'])
