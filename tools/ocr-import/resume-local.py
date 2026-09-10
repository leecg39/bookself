"""Resume this private local installation using its generated local credentials."""
import json
from pathlib import Path
import urllib.request
from register_local import register

root = Path(__file__).resolve().parents[2]
credentials = json.loads((root / 'local/access.json').read_text())
base = 'http://127.0.0.1:3147'
req = urllib.request.Request(base + '/api/v1/auth/login',
    data=json.dumps({'username': credentials['username'], 'password': credentials['password']}).encode(),
    headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as response:
    token = json.load(response)['accessToken']
register(base, root / 'local/ocr-import', token)
