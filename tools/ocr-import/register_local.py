"""Register staged PDF copies using existing authenticated local BookOrbit APIs."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request
from import_ocr import digest, save


def register(base, work, token, library_id=None, timeout=900):
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Only a local private BookOrbit instance is supported')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError('Redirects are not allowed for authenticated imports')
    opener = urllib.request.build_opener(NoRedirect())
    def api(path, data=None):
        req = urllib.request.Request(base.rstrip('/') + '/api/v1' + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
        with opener.open(req, timeout=60) as response:
            return json.load(response)
    work = work.resolve()
    state_path = work / 'manifests.json'
    manifests = json.loads(state_path.read_text())
    staged = [x for x in manifests if x['status'] in ('staged', 'registered') and x.get('output')]
    for item in staged:
        path = work / item['output']
        if not path.resolve().is_relative_to(work / 'exports') or digest(path) != item['contentHash']:
            raise ValueError('Staged file changed; registration stopped')
    record_path = work / 'registration.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {}
    server_user = api('/auth/me')
    owner = server_user.get('id')
    if record and (record.get('baseUrl') != base or record.get('userId') != owner):
        raise ValueError('This work area belongs to another server or user')
    library_id = library_id or record.get('libraryId')
    if not library_id:
        root = str(work / 'exports')
        libraries = api('/libraries')
        matches = [lib for lib in libraries if any((f.get('path') if isinstance(f, dict) else f) == root for f in lib.get('folders', []))]
        if len(matches) > 1:
            raise ValueError('Ambiguous existing library')
        library = matches[0] if matches else api('/libraries', {'name': '나의 OCR 책장', 'icon': 'BookOpen', 'folders': [root], 'watch': False,
            'organizationMode': 'book_per_folder', 'allowedFormats': ['pdf'], 'metadataPrecedence': ['opfFile', 'embedded', 'folderStructure'],
            'fileWriteEnabled': False, 'fileRenameEnabled': False})
        library_id = library['id']
    else:
        library = api('/libraries/' + str(library_id))
        folders = library.get('folders', [])
        if not any((f.get('path') if isinstance(f, dict) else f) == str(work / 'exports') for f in folders):
            raise ValueError('Library must point at this work area exports directory')
    record = {'baseUrl': base, 'userId': owner, 'libraryId': library_id}
    save(record_path, record)
    api(f'/scanner/libraries/{library_id}/scan', {})
    expected = {str((work / x['output']).parent): x for x in staged}
    known = {x['bookorbitBookId']: x for x in staged if x.get('bookorbitBookId')}
    inspected = {}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        matched, page, total_seen = 0, 0, 0
        while True:
            result = api(f'/libraries/{library_id}/books', {'pagination': {'page': page, 'size': 100}})
            for book in result['items']:
                # Registration reads metadata only, never PDF bodies.
                item = known.get(book['id'])
                if item is None:
                    if book['id'] not in inspected:
                        inspected[book['id']] = api('/books/' + str(book['id']))['folderPath']
                    item = expected.get(inspected[book['id']])
                if item:
                    if item.get('bookorbitBookId') not in (None, book['id']):
                        raise ValueError('Existing book ID changed; manual review required')
                    item.update({'bookorbitBookId': book['id'], 'status': 'registered', 'registeredAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
                    known[book['id']] = item
                    matched += 1
            total_seen += len(result['items'])
            if total_seen >= result['total'] or not result['items']:
                break
            page += 1
        save(state_path, manifests)
        save(work / 'registration-report.json', {**record, 'registered': matched, 'expected': len(staged), 'totalBooks': total_seen})
        if matched == len(staged):
            print(json.dumps({'registered': matched, 'totalBooks': total_seen, 'libraryId': library_id}))
            return
        print(json.dumps({'registered': matched, 'expected': len(staged)}), flush=True)
        time.sleep(3)
    raise TimeoutError('Scanner still running; rerun to reconcile existing IDs')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://127.0.0.1:3147')
    p.add_argument('--work', required=True, type=Path)
    p.add_argument('--library-id', type=int)
    args = p.parse_args()
    token = os.environ.get('BOOKORBIT_TOKEN')
    if not token:
        p.error('Set BOOKORBIT_TOKEN to an existing authenticated local access token')
    register(args.base_url, args.work, token, args.library_id)


if __name__ == '__main__':
    main()
