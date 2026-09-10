import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('ocr', Path(__file__).with_name('import_ocr.py'))
ocr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocr)


class ImportTests(unittest.TestCase):
    def test_stage_rerun_changed_revision_and_source_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            root, out = Path(temp) / 'source', Path(temp) / 'work'
            root.mkdir(); out.mkdir()
            pdf = root / '한글_ocr.pdf'
            pdf.write_bytes(b'%PDF-1.7\nexample')
            original = ocr.digest(pdf)
            with patch.object(ocr, 'inspect_pdf', return_value={'pageCount': 12, 'textSamplePages': 3}):
                ocr.inventory(root, out)
                first = json.loads((out / 'manifests.json').read_text())[0]
                ocr.stage(root, out, {first['sourceBookId']})
                ocr.stage(root, out, {first['sourceBookId']})
                self.assertEqual(json.loads((out / 'import-log.json').read_text())['alreadyStaged'], 1)
                self.assertEqual(ocr.digest(pdf), original)
                content = pdf.read_bytes()
                pdf.unlink()
                ocr.inventory(root, out)
                self.assertEqual(json.loads((out / 'manifests.json').read_text())[0]['status'], 'source_missing')
                pdf.write_bytes(content)
                ocr.inventory(root, out)
                self.assertEqual(json.loads((out / 'manifests.json').read_text())[0]['status'], 'staged')
                pdf.rename(root / '다른이름.pdf')
                ocr.inventory(root, out)
                renamed = json.loads((out / 'manifests.json').read_text())[0]
                self.assertEqual(renamed['sourceBookId'], first['sourceBookId'])
                (root / '다른이름.pdf').write_bytes(b'%PDF-1.7\nchanged')
                ocr.inventory(root, out)
                changed = json.loads((out / 'manifests.json').read_text())[0]
                self.assertEqual(changed['sourceBookId'], first['sourceBookId'])
                self.assertEqual(changed['revision'], 2)
                self.assertEqual(changed['status'], 'changed_needs_review')
                self.assertTrue((out / changed['previousRevisions'][0]['output']).exists())

    def test_symlinks_errors_and_duplicate_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root, out = Path(temp) / 'source', Path(temp) / 'work'
            root.mkdir(); out.mkdir()
            (root / 'empty.pdf').touch()
            (root / 'external.pdf').symlink_to('/etc/hosts')
            (root / 'a.pdf').write_bytes(b'%PDF-1.7\nsame')
            (root / 'b.pdf').write_bytes(b'%PDF-1.7\nsame')
            with patch.object(ocr, 'inspect_pdf', return_value={'pageCount': 1, 'textSamplePages': 1}):
                ocr.inventory(root, out)
            result = json.loads((out / 'inventory.json').read_text())
            self.assertEqual(len(result['errors']), 2)
            self.assertEqual(len(result['files']), 2)
            self.assertNotEqual(result['files'][0]['sourceBookId'], result['files'][1]['sourceBookId'])
            self.assertEqual(len(result['files'][0]['duplicateCandidates']), 2)
            ocr.stage(root, out, {item['sourceBookId'] for item in result['files']})
            self.assertEqual(json.loads((out / 'import-log.json').read_text())['failed'], 2)


if __name__ == '__main__':
    unittest.main()
