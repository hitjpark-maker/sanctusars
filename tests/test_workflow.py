"""Synthetic evidence and images: never proof of a real liturgical review."""
import importlib.util
import tempfile
import unittest
import json
import struct
import zlib
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'sanctusars.py'


def evidence():
    return dict(primary_url='https://missa.cbck.or.kr/DailyMissa/20260928',
                checked_at='2026-09-28T16:00:00+00:00', body_date='2026-09-28',
                liturgical_day='연중 제26주간 월요일',
                calendar_url='https://missa.cbck.or.kr/', calendar_date='2026-09-28',
                calendar_day='연중 제26주간 월요일', mass_form='당일 미사',
                gospel_reference='루카 9,46-50', gospel_section='복음',
                quotation='너희를 반대하지 않는 이는 너희를 지지하는 사람이다.',
                gospel_excerpt='막지 마라. 너희를 반대하지 않는 이는 너희를 지지하는 사람이다.',
                crosscheck_url='https://maria.catholic.or.kr/mi_pr/missa/',
                crosscheck_date='2026-09-28', crosscheck_mass_form='당일 미사',
                crosscheck_reference='루카 9,46-50', occasions=[], unresolved_choices=[],
                review_note='SYNTHETIC TEST DATA — not a live source verification')


def png(path, color, width=2, height=2):
    """Valid tiny PNG made without a dependency; only a test asset."""
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' +
                     chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * width) * height)) +
                     chunk(b'IEND', b''))
    return path


class DatesAndJobs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SCRIPT.exists():
            spec = importlib.util.spec_from_file_location('sanctusars', SCRIPT)
            cls.app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.app)
        else:
            cls.app = None

    def setUp(self):
        self.assertIsNotNone(self.app, 'Workflow implementation is not present')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / '한글 작업'

    def test_korean_date_boundary(self):
        now = datetime(2026, 9, 28, 16, tzinfo=timezone.utc)
        self.assertEqual(self.app.resolve_date('오늘', now), '2026-09-29')
        self.assertEqual(self.app.resolve_date('내일', now), '2026-09-30')
        self.assertEqual(self.app.resolve_date('2026-09-28', now), '2026-09-28')
        for bad in ['2026-02-30', '20260928', '09-28']:
            with self.assertRaises(ValueError):
                self.app.resolve_date(bad, now)

    def test_job_roundtrip_and_no_overwrite(self):
        path = self.app.create_job(self.root, '2026-09-28', 'gospel', 'gospel')
        record = self.app.load_job(path)
        self.assertEqual(record['date'], '2026-09-28')
        self.assertEqual(record['timezone'], 'Asia/Seoul')
        self.app.save_job(path, record)
        self.assertEqual(self.app.load_job(path), record)
        with self.assertRaises(FileExistsError):
            self.app.create_job(self.root, '2026-09-28', 'gospel', 'gospel')
        with self.assertRaises(ValueError):
            self.app.create_job(self.root, '2026-09-28', '../escape', 'gospel')

    def test_evidence_rejects_wrong_date_mass_and_section(self):
        self.assertTrue(hasattr(self.app, 'validate_evidence'), 'Evidence gate is missing')
        path = self.app.create_job(self.root, '2026-09-28', 'gospel', 'gospel')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        self.assertEqual(self.app.validate_evidence(job), [])
        for key, value in [('body_date', '2025-09-28'),
                           ('crosscheck_date', '2026-09-27'),
                           ('calendar_day', '연중 제25주간 월요일'),
                           ('gospel_section', '복음 환호송'),
                           ('crosscheck_reference', '마르 10,45'),
                           ('crosscheck_mass_form', '밤 미사'),
                           ('mass_form', ''), ('unresolved_choices', ['밤/낮']),
                           ('quotation', '다른 구절'), ('checked_at', 'yesterday'),
                           ('primary_url', 'https://example.com/20260928')]:
            with self.subTest(key=key):
                bad = deepcopy(job)
                bad['evidence'][key] = value
                self.assertTrue(self.app.validate_evidence(bad))

    def test_special_post_requires_matching_occurrence_and_sources(self):
        self.assertTrue(hasattr(self.app, 'validate_evidence'), 'Evidence gate is missing')
        path = self.app.create_job(self.root, '2026-09-28', 'saint', 'occasion')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        self.assertTrue(self.app.validate_evidence(job))

        occasion = dict(name='테스트 성인', rank='선택 기념일', date='2026-09-28',
                        source_url='https://missa.cbck.or.kr/DailyMissa/20260928',
                        biography_url='https://www.vatican.va/',
                        meaning='Synthetic fixture', symbols='검증된 상징만 사용',
                        choice_note='사용자 선택 기록 (test)')
        job['evidence']['occasion'] = occasion
        job['evidence']['occasions'] = [deepcopy(occasion)]
        self.assertEqual(self.app.validate_evidence(job), [])
        job['evidence']['occasion']['date'] = '2026-09-29'
        self.assertTrue(self.app.validate_evidence(job))

    def prepared_job(self, post_id='gospel'):
        path = self.app.create_job(self.root, '2026-09-28', post_id, 'gospel')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        self.app.save_job(path, job)
        return path

    def candidates(self, path):
        for i, label in enumerate('ABC'):
            image = png(path.parent / f'input-{label}.png', (100 + i, 40, 20))
            self.app.register_candidate(path, label, image, 'Synthetic test prompt')

    def test_candidates_and_selection_have_required_gates(self):
        self.assertTrue(hasattr(self.app, 'register_candidate'), 'Candidate gate is missing')
        path = self.prepared_job()
        with self.assertRaises(ValueError):
            self.app.select_candidate(path, 'A', 'A 선택')
        self.candidates(path)
        with self.assertRaises(ValueError):
            self.app.select_candidate(path, 'A', '')
        self.app.select_candidate(path, 'B', 'B 선택')
        self.assertEqual(self.app.load_job(path)['selection']['label'], 'B')
        original = self.app.load_job(path)['candidates']['B']['path']
        new_image = png(path.parent / 'new-b.png', (1, 2, 3))
        self.app.register_candidate(path, 'B', new_image, 'Revised prompt')
        self.assertTrue((path.parent / original).is_file())
        revised = self.app.load_job(path)
        self.assertIsNone(revised['selection'])
        previous = [h for h in revised['history'] if h['action'] == 'candidate' and h['path'] == original][0]
        self.assertEqual(previous.get('prompt'), 'Synthetic test prompt')
        self.assertTrue(previous.get('sha256'))
        self.assertTrue(previous.get('context_hash'))

    def test_candidate_change_and_evidence_change_invalidate_selection(self):
        self.assertTrue(hasattr(self.app, 'select_candidate'), 'Selection gate is missing')
        path = self.prepared_job()
        self.candidates(path)
        self.app.select_candidate(path, 'A', 'A 선택')
        job = self.app.load_job(path)
        job['evidence']['mass_form'] = '낮 미사'
        job['evidence']['crosscheck_mass_form'] = '낮 미사'
        self.app.save_job(path, job)
        with self.assertRaises(ValueError):
            self.app.approve_final(path, [], '승인')

    def test_duplicate_and_unverified_candidates_rejected(self):
        self.assertTrue(hasattr(self.app, 'register_candidate'), 'Candidate gate is missing')
        path = self.prepared_job()
        image = png(path.parent / 'input.png', (1, 2, 3))
        self.app.register_candidate(path, 'A', image, 'Test')
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'B', image, 'Same bytes')
        job = self.app.load_job(path)
        job['evidence']['body_date'] = '2026-09-27'
        self.app.save_job(path, job)
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'C', image, 'Wrong day')

    def preview(self, path):
        self.candidates(path)
        self.app.select_candidate(path, 'A', 'A 선택 (test)')
        job = self.app.load_job(path)
        image = path.parent / job['candidates']['A']['path']
        logo = png(path.parent / 'logo.png', (20, 30, 40))
        font = path.parent / 'font.ttf'
        font.write_bytes(b'\x00\x01\x00\x00' + b'FAKE FONT FOR UNIT TESTS ONLY')
        content = dict(scripture_quote=evidence()['quotation'], reference='루카 9,46-50',
                       meditation='나를 <script>alert(1)</script> 있는 그대로',
                       prayer='함께하게 하소서.', question='오늘 누구를 떠올렸나요?',
                       threads_text='Threads 테스트', blog_text='블로그 테스트',
                       card_text='작은 사람을 맞이하는 마음', card_kind='meditation')
        return self.app.render_preview(path, image, content, logo, font)

    def test_render_escapes_text_and_requires_correct_scripture(self):
        self.assertTrue(hasattr(self.app, 'render_preview'), 'Preview is missing')
        path = self.prepared_job()
        page = self.preview(path)
        html = page.read_text()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('SanctusArs', html)
        self.assertIn(evidence()['primary_url'], html)
        self.assertTrue((page.parent / 'threads.txt').is_file())
        with self.assertRaises(ValueError):
            self.app.export_approved(path)

    def test_preview_allows_no_question_but_rejects_invalid_type(self):
        path = self.prepared_job()
        page = self.preview(path)
        content = json.loads((page.parent / 'content.json').read_text())
        image = path.parent / self.app.load_job(path)['candidates']['A']['path']
        for value in ('', None):
            if value is None:
                content.pop('question', None)
            else:
                content['question'] = value
            self.app.render_preview(path, image, content, path.parent / 'logo.png', path.parent / 'font.ttf')
        content['question'] = 42
        with self.assertRaises(ValueError):
            self.app.render_preview(path, image, content, path.parent / 'logo.png', path.parent / 'font.ttf')

    def test_final_approval_export_and_tamper_detection(self):
        self.assertTrue(hasattr(self.app, 'render_preview'), 'Preview is missing')
        path = self.prepared_job()
        page = self.preview(path)
        files = [path.parent / p for p in self.app.load_job(path)['preview']['files']]
        with self.assertRaises(ValueError):
            self.app.approve_final(path, files, '최종 승인')
        art = png(path.parent / 'art.png', (30, 40, 50), 1080, 1350)
        card = png(path.parent / 'card.png', (40, 50, 60), 1080, 1350)
        self.app.register_rendered(path, art, card, 'Synthetic render review')
        files = [path.parent / p for p in self.app.load_job(path)['preview']['files']]
        self.app.approve_final(path, files, '최종 승인 (test)')
        self.assertEqual(self.app.verify_approval(path), [])
        history = self.app.load_job(path)['history']
        previous_approval = [h for h in history if h['action'] == 'approve'][-1]
        self.assertTrue(previous_approval.get('approval', {}).get('files'))
        destination = self.app.export_approved(path)
        self.assertTrue((destination / 'card.png').is_file())
        self.assertEqual((destination / 'threads.txt').read_text(), 'Threads 테스트\n')

        (page.parent / 'threads.txt').write_text('수정됨')
        self.assertTrue(self.app.verify_approval(path))
        with self.assertRaises(ValueError):
            self.app.export_approved(path)
        self.assertEqual((destination / 'threads.txt').read_text(), 'Threads 테스트\n')

    def test_cli_init_and_check_report_blocked_and_invalid_input(self):
        self.root.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), 'init', '2026-09-28',
                                 '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(result.stdout.strip())
        self.assertTrue(path.is_file(), 'CLI must print the new record path')
        check = subprocess.run([sys.executable, str(SCRIPT), 'check', str(path)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 2)
        bad = subprocess.run([sys.executable, str(SCRIPT), 'init', '2026-02-30'], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)

    def test_malformed_occasion_list_returns_errors(self):
        path = self.app.create_job(self.root, '2026-09-28', 'saint', 'occasion')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        job['evidence']['occasions'] = None
        self.assertTrue(self.app.validate_evidence(job))




if __name__ == '__main__':
    unittest.main()
