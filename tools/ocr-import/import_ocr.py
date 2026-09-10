"""Read-only PDF inventory and resumable staging for BookOrbit's library scanner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from xml.sax.saxutils import escape

VERSION = '1.0.0'


def digest(path):
    with path.open('rb') as stream:
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    if temp.is_symlink():
        raise ValueError('unsafe_temporary_path')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.chmod(temp, 0o600)
    temp.replace(path)


def inspect_pdf(path):
    with path.open('rb') as stream:
        if not stream.read(1024).startswith(b'%PDF-'):
            raise ValueError('invalid_pdf_signature')
    info = subprocess.run(['pdfinfo', str(path)], capture_output=True, timeout=60, check=True).stdout.decode('utf-8', 'strict')
    pages = re.search(r'^Pages:\s+(\d+)', info, re.M)
    if not pages or re.search(r'^Encrypted:\s+yes', info, re.M):
        raise ValueError('encrypted_or_invalid_pdf')
    count = int(pages[1])
    # Inspect representative pages without publishing extracted content.
    samples = sorted({1, min(2, count), min(10, count), max(1, count // 2), count})
    text_pages = 0
    for page in samples:
        data = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), str(path), '-'], capture_output=True, timeout=60, check=True).stdout.decode('utf-8', 'strict')
        text_pages += len(data.strip()) > 20
    return {'pageCount': count, 'sampledPages': samples, 'textSamplePages': text_pages}


def inventory(root, out):
    state_path = out / 'manifests.json'
    previous = json.loads(state_path.read_text()) if state_path.exists() else []
    by_path = {x['sourceFiles'][0]['relativePath']: x for x in previous}
    by_hash = {}
    for item in previous:
        by_hash.setdefault(item['contentHash'], []).append(item)
    records, errors, seen = [], [], set()
    def walk_error(error):
        errors.append({'relativePath': str(Path(error.filename).relative_to(root)), 'reason': 'permission_or_io_error'})
    for base, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink())
        for name in sorted(files):
            path = Path(base) / name
            rel = str(path.relative_to(root))
            if path.is_symlink() or name.startswith('.'):
                errors.append({'relativePath': rel, 'reason': 'symlink_or_hidden_skipped'})
                continue
            try:
                before = path.stat()
                if before.st_size == 0:
                    raise ValueError('empty_file')
                hash_value = digest(path)
                old = by_path.get(rel)
                if old is None and len(by_hash.get(hash_value, [])) == 1:
                    old = by_hash[hash_value][0]
                source_id = str(uuid.UUID(old['sourceBookId'])) if old else str(uuid.uuid4())
                if source_id in seen:
                    source_id = str(uuid.uuid4())
                seen.add(source_id)
                same = old is not None and old['contentHash'] == hash_value
                details = inspect_pdf(path) if path.suffix.lower() == '.pdf' else {}
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError('source_changed_during_scan')
                status = 'ready_for_review' if details.get('textSamplePages', 0) else 'needs_processing'
                record = dict(old) if old else {}
                record.update({'schemaVersion': 1, 'sourceBookId': source_id, 'revision': old['revision'] + (not same) if old else 1,
                    'bookorbitBookId': old.get('bookorbitBookId') if old else None,
                    'title': old['title'] if old else re.sub(r'_ocr$', '', path.stem, flags=re.I),
                    'authors': old.get('authors', []) if old else [],
                    'metadataProvenance': old.get('metadataProvenance') if old else {'title': {'source': 'filename', 'verified': False}},
                    'sourceFiles': [{'relativePath': rel, 'sha256': hash_value, 'size': before.st_size, 'mtimeNs': before.st_mtime_ns}],
                    'contentHash': hash_value, 'converterVersion': VERSION, 'coverKind': 'unverified',
                    'status': record.get('status', status) if same else status, 'pdf': details,
                    'output': record.get('output') if same else None})
                if same and record.get('status') == 'source_missing':
                    record['status'] = 'registered' if record.get('bookorbitBookId') else ('staged' if record.get('output') else status)
                if old and not same:
                    record['previousRevisions'] = old.get('previousRevisions', []) + [{'revision': old['revision'], 'output': old.get('output'), 'contentHash': old['contentHash']}]
                    record['status'] = 'changed_needs_review'
                records.append(record)
            except Exception as exc:
                errors.append({'relativePath': rel, 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
    for old in previous:
        if old['sourceBookId'] not in seen:
            records.append({**old, 'status': 'source_missing'})
    duplicates = {}
    for item in records:
        duplicates.setdefault(item['contentHash'], []).append(item['sourceBookId'])
    for item in records:
        item.pop('duplicateCandidates', None)
        if len(duplicates[item['contentHash']]) > 1:
            item['duplicateCandidates'] = duplicates[item['contentHash']]
    save(state_path, records)
    save(out / 'inventory.json', {'files': records, 'errors': errors})
    save(out / 'book-candidates.json', [{'sourceBookId': x['sourceBookId'], 'title': x['title'], 'status': x['status'], 'evidence': 'one standalone PDF; filename title unverified'} for x in records])
    report = f'# OCR 인벤토리\n\n후보 {len(records)}권, 점검 오류/제외 {len(errors)}건.\n\nPDF 본문 전체를 교정하거나 페이지 누락을 검증한 결과가 아닙니다. 표본 페이지의 텍스트 레이어를 검사했습니다.\n\n'
    report += '\n'.join(f"- {x['title']}: {x['status']}, PDF {x['pdf'].get('pageCount', '?')}쪽" for x in records)
    (out / 'inventory-report.md').write_text(report)
    print(json.dumps({'candidates': len(records), 'errors': len(errors), 'ready': sum(x['status'] == 'ready_for_review' for x in records)}))


def stage(root, out, ids):
    root, out = root.resolve(), out.resolve()
    state_path = out / 'manifests.json'
    records = json.loads(state_path.read_text())
    exported, skipped, failed = 0, 0, 0
    for item in records:
        if item['sourceBookId'] not in ids:
            continue
        try:
            if item['status'] not in ('ready_for_review', 'staged', 'registered') or item.get('duplicateCandidates'):
                raise ValueError('review_required')
            source = root / item['sourceFiles'][0]['relativePath']
            if source.is_symlink() or not source.resolve().is_relative_to(root):
                raise ValueError('source_outside_root')
            if digest(source) != item['contentHash']:
                raise ValueError('source_changed')
            uuid.UUID(item['sourceBookId'])
            destination = out / 'exports' / item['sourceBookId'] / f"revision-{item['revision']}" / 'book.pdf'
            if not destination.resolve().is_relative_to(out):
                raise ValueError('output_outside_work_area')
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if destination.exists():
                if digest(destination) != item['contentHash']:
                    raise ValueError('staged_file_changed')
                skipped += 1
            else:
                temp = destination.with_suffix('.tmp')
                if temp.is_symlink():
                    raise ValueError('unsafe_temporary_path')
                if sys.platform == 'darwin':
                    subprocess.run(['cp', '-c', str(source), str(temp)], check=True, capture_output=True)
                else:
                    shutil.copyfile(source, temp)
                os.chmod(temp, 0o600)
                if digest(temp) != item['contentHash'] or digest(source) != item['contentHash']:
                    temp.unlink()
                    raise ValueError('copy_hash_mismatch')
                temp.replace(destination)
                exported += 1
            opf = destination.parent / 'metadata.opf'
            if not opf.exists():
                opf.write_text('<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">' + item['sourceBookId'] + '</dc:identifier><dc:title>' + escape(item['title']) + '</dc:title><dc:language>ko</dc:language></metadata></package>', encoding='utf-8')
            item['output'] = str(destination.relative_to(out))
            maps = out / 'source-maps' / item['sourceBookId']
            if not maps.resolve().is_relative_to(out):
                raise ValueError('source_map_outside_work_area')
            maps.mkdir(parents=True, exist_ok=True, mode=0o700)
            map_path = maps / f"revision-{item['revision']}.json"
            save(map_path, {'kind': 'unchanged_pdf', 'sourceRelativePath': item['sourceFiles'][0]['relativePath'], 'sourceSha256': item['contentHash'], 'output': item['output'], 'pageCount': item['pdf']['pageCount'], 'mapping': 'PDF page index is identical; printed original page numbers are not inferred'})
            item['sourceMap'] = str(map_path.relative_to(out))
            if item['status'] != 'registered':
                item['status'] = 'staged'
            item.pop('lastError', None)
        except Exception as exc:
            failed += 1
            item['lastError'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        save(state_path, records)
    save(out / 'import-log.json', {'exported': exported, 'alreadyStaged': skipped, 'failed': failed})
    print(json.dumps({'exported': exported, 'alreadyStaged': skipped, 'failed': failed}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['inventory', 'stage'])
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--ids', nargs='*', default=[])
    args = parser.parse_args()
    root, out = args.source.resolve(strict=True), args.work.resolve()
    if out.is_relative_to(root) or root.is_relative_to(out):
        parser.error('Source and work directories must be separate')
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    out.chmod(0o700)
    if args.command == 'inventory':
        inventory(root, out)
    else:
        stage(root, out, set(args.ids))


if __name__ == '__main__':
    main()
