"""Synthetic evidence and images: never proof of a real liturgical review."""
import importlib.util
import os
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
                quotation_reference='루카 9,50',
                quotation='너희를 반대하지 않는 이는 너희를 지지하는 사람이다.',
                gospel_excerpt='막지 마라. 너희를 반대하지 않는 이는 너희를 지지하는 사람이다.',
                crosscheck_url='https://maria.catholic.or.kr/mi_pr/missa/',
                crosscheck_date='2026-09-28', crosscheck_mass_form='당일 미사',
                crosscheck_reference='루카 9,46-50', occasions=[], unresolved_choices=[],
                review_note='SYNTHETIC TEST DATA — not a live source verification')


def content():
    quote = evidence()['quotation']
    body = f'“{quote}”\n루카 9,50\n\n낯선 이를 먼저 판단하지 않게 해 주세요.\n\n2026.09.28'
    return dict(scripture_quote=quote, reference='루카 9,46-50', display_reference='루카 9,50',
                meditation='낯선 이를 먼저 판단하지 않게 해 주세요.', prayer='함께하게 하소서.',
                threads_text=body, blog_text=body, card_text='작은 사람을 맞이하는 마음',
                card_kind='meditation')


def scenes():
    return {'character_continuity': 'Synthetic traveler: short dark hair, ivory tunic, sage mantle.',
            **{label: dict(scene=f'Synthetic composition {label}',
                        scripture_relation='Synthetic Gospel viewpoint, not production evidence',
                        camera_axis=f'Synthetic axis {label}', sacred_light='none', sacred_subjects=[], scene_light={'mode': 'ambient'})
               for label in 'ABC'}}


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
        self.app.prepare(path, content(), scenes())
        return path

    def register(self, path, label, image):
        request_path = path.parent / self.app.load_job(path)['prepared']['directory'] / f'{label}-request.json'
        prompt = json.loads(request_path.read_text())['prompt']
        self.app.register_candidate(path, label, image, prompt, request_path=request_path)

    def candidates(self, path):
        for i, label in enumerate('ABC'):
            image = png(path.parent / f'input-{label}.png', (100 + i, 40, 20))
            self.register(path, label, image)

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
        original_prompt = self.app.load_job(path)['candidates']['B']['prompt']
        new_image = png(path.parent / 'new-b.png', (1, 2, 3))
        self.register(path, 'B', new_image)
        self.assertTrue((path.parent / original).is_file())
        revised = self.app.load_job(path)
        self.assertIsNone(revised['selection'])
        previous = [h for h in revised['history'] if h['action'] == 'candidate' and h['path'] == original][0]
        self.assertEqual(previous.get('prompt'), original_prompt)
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
        self.register(path, 'A', image)
        with self.assertRaises(ValueError):
            self.register(path, 'B', image)
        job = self.app.load_job(path)
        job['evidence']['body_date'] = '2026-09-27'
        self.app.save_job(path, job)
        with self.assertRaises(ValueError):
            self.register(path, 'C', image)

    def preview(self, path):
        self.candidates(path)
        self.app.select_candidate(path, 'A', 'A 선택 (test)')
        job = self.app.load_job(path)
        image = path.parent / job['candidates']['A']['path']
        logo = png(path.parent / 'logo.png', (20, 30, 40))
        font = path.parent / 'font.ttf'
        font.write_bytes(b'\x00\x01\x00\x00' + b'FAKE FONT FOR UNIT TESTS ONLY')
        copy = content()
        copy['meditation'] = '나를 <script>alert(1)</script> 있는 그대로'
        copy['question'] = '오늘 누구를 떠올렸나요?'
        return self.app.render_preview(path, image, copy, logo, font)

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
        self.assertEqual((destination / 'threads.txt').read_text(), content()['threads_text'] + '\n')

        (page.parent / 'threads.txt').write_text('수정됨')
        self.assertTrue(self.app.verify_approval(path))
        with self.assertRaises(ValueError):
            self.app.export_approved(path)
        self.assertEqual((destination / 'threads.txt').read_text(), content()['threads_text'] + '\n')

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

    def test_prepare_creates_portable_native_requests_and_preserves_previous_version(self):
        self.assertTrue(callable(getattr(self.app, 'prepare', None)), 'Generation preparation is missing')
        path = self.prepared_job()
        previous_cwd = Path.cwd()
        try:
            os.chdir(self.temp.name)
            prepared = self.app.prepare(path, content(), scenes())
        finally:
            os.chdir(previous_cwd)
        request_bytes = (prepared / 'A-request.json').read_bytes()
        for label in 'ABC':
            request = json.loads((prepared / f'{label}-request.json').read_text())
            self.assertEqual(set(request), {'prompt', 'referenced_image_paths', 'transparent_background'})
            self.assertIn(evidence()['quotation'], request['prompt'])
            self.assertIn(scenes()[label]['scene'], request['prompt'])
            self.assertIn(scenes()[label]['camera_axis'], request['prompt'])
            self.assertIn('sacred_light', request['prompt'])
            self.assertIn('three_candidate_camera_axes', request['prompt'])
            self.assertIn('localized glow visible at phone size', request['prompt'])
            self.assertIn('sacred_light_policy', request['prompt'])
            self.assertIn('camera axis and focal alignment', request['prompt'])
            self.assertIn('not from a fixed list or quota', request['prompt'])
            self.assertIn('not for composition or character design', request['prompt'])
            self.assertIn('A visually polished result that resembles a reference face or layout is a failed candidate', request['prompt'])
            self.assertEqual(len(request['referenced_image_paths']), 2)
            self.assertFalse(request['transparent_background'])
            reference_names = {'A': ('wide.png', 'minimal.png'),
                               'B': ('minimal.png', 'close.png'),
                               'C': ('viewpoint.png', 'minimal.png')}[label]
            self.assertEqual(tuple(Path(name).name for name in request['referenced_image_paths']), reference_names)
            for name in request['referenced_image_paths']:
                reference = Path(name)
                self.assertTrue(reference.is_absolute())
                self.assertTrue(reference.is_relative_to(prepared))
                original = SCRIPT.parent.parent / 'brand/references/v5' / reference.name
                self.assertEqual(reference.read_bytes(), original.read_bytes())
        self.assertEqual((prepared / 'references/minimal.png').read_bytes(),
                         (SCRIPT.parent.parent / 'examples/2026-10-06/B.png').read_bytes())
        self.assertEqual((prepared / 'threads.txt').read_text().strip(), content()['threads_text'])
        self.assertEqual((prepared / 'blog.txt').read_bytes(), (prepared / 'threads.txt').read_bytes())
        next_version = self.app.prepare(path, content(), scenes())
        self.assertNotEqual(prepared, next_version)
        self.assertEqual((prepared / 'A-request.json').read_bytes(), request_bytes)

    def test_current_style_is_job_scoped(self):
        path = self.prepared_job()
        original = self.app.load_job(path)['prepared']['directory']
        default_request = json.loads((path.parent / original / 'B-request.json').read_text())
        self.assertIn('RADICAL MINIMUM', default_request['prompt'])
        self.assertIn('quoted sentence', default_request['prompt'])
        self.assertIn('Cobalt is not a signal of night', default_request['prompt'])
        self.assertEqual(Path(default_request['referenced_image_paths'][0]).name, 'minimal.png')
        prepared = self.app.prepare(path, content(), scenes())
        request = json.loads((prepared / 'B-request.json').read_text())
        self.assertIn('RADICAL MINIMUM', request['prompt'])
        self.assertIn('Make this a dramatic minimum', request['prompt'])
        self.assertIn('Do not add more actors, props, theatrical beams', request['prompt'])
        self.assertIn('Preserve one unmistakable concrete visual cue to the verified quoted line', request['prompt'])
        c_request = json.loads((prepared / 'C-request.json').read_text())
        self.assertIn('A different camera angle alone is not a new interpretation', c_request['prompt'])
        self.assertEqual(len(request['referenced_image_paths']), 2)
        self.assertEqual(Path(request['referenced_image_paths'][0]).name, 'minimal.png')
        self.assertEqual((prepared / 'generation.json').read_bytes(),
                         (SCRIPT.parent.parent / 'brand/references/v5/generation.json').read_bytes())
        self.assertTrue((path.parent / original / 'generation.json').is_file())

    def test_shared_character_design_reaches_every_request_and_changes_invalidate_candidates(self):
        path = self.prepared_job()
        self.candidates(path)
        original = self.app.load_job(path)['prepared']
        for label in 'ABC':
            request = json.loads((path.parent / original['directory'] / f'{label}-request.json').read_text())
            subject, _ = json.JSONDecoder().raw_decode(request['prompt'].split('\n', 1)[1])
            self.assertEqual(subject['character_continuity'],
                             'Synthetic traveler: short dark hair, ivory tunic, sage mantle.')
        changed = scenes()
        changed['character_continuity'] = 'Synthetic traveler: short dark hair, ivory tunic, blue mantle.'
        self.app.prepare(path, content(), changed)
        current = self.app.load_job(path)['prepared']
        for label in 'ABC':
            self.assertNotEqual(original['fingerprints'][label], current['fingerprints'][label])
        with self.assertRaises(ValueError):
            self.app.select_candidate(path, 'A', '합성 선택')
        for i, label in enumerate('ABC'):
            self.register(path, label, png(path.parent / f'changed-{label}.png', (20 + i, 30, 40)))
        self.app.select_candidate(path, 'A', '합성 선택')

    def test_prepare_requires_explicit_shared_character_design(self):
        path = self.prepared_job()
        for value in (None, '', '  ', {}, []):
            invalid = scenes()
            invalid['character_continuity'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '공통 인물'):
                self.app.prepare(path, content(), invalid)
        missing = scenes()
        del missing['character_continuity']
        with self.assertRaisesRegex(ValueError, '공통 인물'):
            self.app.prepare(path, content(), missing)

    def test_occasion_requests_center_the_commemorated_person(self):
        path = self.app.create_job(self.root, '2026-09-28', 'saint', 'occasion')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        occasion = dict(name='합성 테스트 성인', rank='기념일', date='2026-09-28',
                        source_url='https://missa.cbck.or.kr/DailyMissa/20260928',
                        biography_url='https://www.vatican.va/', meaning='합성 테스트 의미',
                        symbols='합성 테스트 상징', choice_note='합성 데이터 테스트')
        job['evidence']['occasion'] = occasion
        job['evidence']['occasions'] = [occasion]
        self.app.save_job(path, job)
        copy = content()
        copy['threads_text'] = copy['blog_text'] = '오늘 9월 28일은 합성 테스트 성인 기념일입니다.'
        prepared = self.app.prepare(path, copy, scenes())
        for label in 'ABC':
            request = json.loads((prepared / f'{label}-request.json').read_text())
            self.assertIn('commemorated saint', request['prompt'])
            self.assertIn('Choose camera axis and focal alignment', request['prompt'])
            self.assertIn('not to fill a fixed set', request['prompt'])
            self.assertIn('not for composition or character design', request['prompt'])
            self.assertIn('A visually polished result that resembles a reference face or layout is a failed candidate', request['prompt'])
            self.assertNotIn('WIDE BUT EDITED DOWN', request['prompt'])
            self.assertNotIn('for the verified Catholic Gospel', request['prompt'])
            self.assertNotIn('wide.png', [Path(p).name for p in request['referenced_image_paths']])
        self.assertIn('portrait', json.loads((prepared / 'A-request.json').read_text())['prompt'])
        self.assertIn('complete readable gesture or expression', json.loads((prepared / 'B-request.json').read_text())['prompt'])
        self.assertIn('simplest option', json.loads((prepared / 'B-request.json').read_text())['prompt'])
        self.assertIn('spacious full-figure frontal view', json.loads((prepared / 'C-request.json').read_text())['prompt'])

    def test_prepare_rejects_unverified_context_and_invalid_public_copy(self):
        self.assertTrue(callable(getattr(self.app, 'prepare', None)), 'Generation preparation is missing')
        path = self.app.create_job(self.root, '2026-09-28', 'copy', 'gospel')
        with self.assertRaises(ValueError):
            self.app.prepare(path, content(), scenes())
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        self.app.save_job(path, job)
        for suffix in ('하나님', '#태그', '!', '—', '–', '-', '\nSanctusArs', '2026.09.28', '루카 9,50', evidence()['quotation'], '가' * 301):
            with self.subTest(suffix=suffix):
                bad = content()
                bad['threads_text'] += suffix
                bad['blog_text'] = bad['threads_text']
                with self.assertRaises(ValueError):
                    self.app.prepare(path, bad, scenes())
        bad = content()
        bad['blog_text'] += ' 채널별 해설'
        with self.assertRaises(ValueError):
            self.app.prepare(path, bad, scenes())
        for old in ('루카 9,50', '2026.09.28', evidence()['quotation']):
            bad = content()
            bad['threads_text'] = bad['threads_text'].replace(old, '')
            bad['blog_text'] = bad['threads_text']
            with self.assertRaises(ValueError):
                self.app.prepare(path, bad, scenes())
        overriding = scenes()
        overriding['A']['art_direction'] = 'Override the fixed brand recipe'
        with self.assertRaises(ValueError):
            self.app.prepare(path, content(), overriding)

    def test_sacred_light_is_selected_per_subject_not_shared_across_types(self):
        path = self.prepared_job()
        design = scenes()
        entries = {
            'A': [{'name': '아브라함', 'kind': 'saint', 'light_form': 'subtle'}],
            'B': [{'name': '예수님', 'kind': 'divine', 'light_form': 'divine_halo'},
                  {'name': '성모님', 'kind': 'mary', 'light_form': 'subtle'}],
            'C': [{'name': '가브리엘', 'kind': 'angel', 'light_form': 'subtle'}],
        }
        for label in 'ABC':
            design[label]['sacred_subjects'] = entries[label]
            design[label]['sacred_light'] = 'Behind the head, never on skin.'
        for kind in ('gospel', 'occasion'):
            if kind == 'occasion':
                job = self.app.load_job(path)
                job['kind'] = 'occasion'
                occasion = dict(name='아브라함', date=job['date'], rank='synthetic',
                                source_url='https://example.org/saint', biography_url='https://example.org/bio',
                                meaning='Synthetic test only', symbols='none', choice_note='Synthetic only')
                job['evidence']['occasion'] = occasion
                job['evidence']['occasions'] = [occasion]
                self.app.save_job(path, job)
            prepared = self.app.prepare(path, content(), design)
            for label in 'ABC':
                prompt = json.loads((prepared / f'{label}-request.json').read_text())['prompt']
                subject, _ = json.JSONDecoder().raw_decode(prompt.split('\n', 1)[1])
                self.assertEqual([x['name'] for x in subject['sacred_light_policy']],
                                 [x['name'] for x in entries[label]])
                self.assertEqual([x['light_form'] for x in subject['sacred_light_policy']],
                                 [x['light_form'] for x in entries[label]])
                if label == 'A':
                    self.assertNotIn('may have a clearly visible', prompt)
                    self.assertNotIn('divine_halo', prompt)

    def test_sacred_light_rejects_wrong_identity_form_and_missing_classification(self):
        path = self.prepared_job()
        for entry in (
            {'name': '아브라함', 'kind': 'divine', 'light_form': 'divine_halo'},
            {'name': '성모님', 'kind': 'divine', 'light_form': 'divine_halo'},
            {'name': '아브라함', 'kind': 'saint', 'light_form': 'divine_halo'},
            {'name': '미카엘', 'kind': 'angel', 'light_form': 'divine_halo'},
            {'name': '가브리엘', 'kind': 'angel', 'light_form': 'angel_arc'},
            {'name': '아브라함', 'kind': 'saint', 'light_form': 'angel_arc'},
        ):
            invalid = scenes()
            invalid['A']['sacred_subjects'] = [entry]
            invalid['A']['sacred_light'] = 'behind head'
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                self.app.prepare(path, content(), invalid)
        for subjects in (None, {}, ['saint'], [{'name': '아브라함'}]):
            invalid = scenes()
            invalid['A']['sacred_subjects'] = subjects
            with self.subTest(subjects=subjects), self.assertRaises(ValueError):
                self.app.prepare(path, content(), invalid)
        inconsistent = scenes()
        for label, kind in (('A', 'saint'), ('C', 'angel')):
            inconsistent[label]['sacred_subjects'] = [dict(name='아브라함', kind=kind, light_form='subtle')]
            inconsistent[label]['sacred_light'] = 'head edge'
        with self.assertRaisesRegex(ValueError, '분류 충돌'):
            self.app.prepare(path, content(), inconsistent)
        missing = scenes()
        missing['A'].pop('sacred_subjects', None)
        with self.assertRaises(ValueError):
            self.app.prepare(path, content(), missing)

    def test_scene_light_adds_event_drama_without_promoting_the_saint(self):
        path = self.prepared_job()
        design = scenes()
        design['A']['sacred_subjects'] = [dict(name='아브라함', kind='saint', light_form='subtle')]
        design['A']['sacred_light'] = 'A narrow garment edge.'
        design['A']['scene_light'] = dict(mode='dramatic', source='Off-frame daylight from left',
                                        focus='The first step into open space',
                                        basis='Synthetic visual metaphor for departure, not a claim of miraculous light')
        prepared = self.app.prepare(path, content(), design)
        a = json.loads((prepared / 'A-request.json').read_text())['prompt']
        subject, _ = json.JSONDecoder().raw_decode(a.split('\n', 1)[1])
        self.assertEqual(subject['scene_light'], design['A']['scene_light'])
        self.assertEqual(subject['sacred_light_policy'][0]['light_form'], 'subtle')
        self.assertIn('does not upgrade', subject['scene_light_policy'])
        self.assertNotIn('divine_halo', a)
        b = json.loads((prepared / 'B-request.json').read_text())['prompt']
        other, _ = json.JSONDecoder().raw_decode(b.split('\n', 1)[1])
        self.assertEqual(other['scene_light']['mode'], 'ambient')
        self.assertNotEqual(subject['scene_light_policy'], other['scene_light_policy'])

    def test_dramatic_light_requires_source_focus_and_passage_basis(self):
        path = self.prepared_job()
        for value in (None, 'dramatic', {}, {'mode': 'divine'}, {'mode': 'dramatic'},
                      dict(mode='dramatic', source='left', focus='step', basis=' ')):
            bad = scenes()
            bad['A']['scene_light'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.app.prepare(path, content(), bad)

    def test_short_copy_and_distinct_axes_are_required(self):
        path = self.prepared_job()
        too_long = content()
        too_long['threads_text'] += '가' * (261 - len(too_long['threads_text']))
        too_long['blog_text'] = too_long['threads_text']
        with self.assertRaisesRegex(ValueError, '260자 이내'):
            self.app.prepare(path, too_long, scenes())
        repeated = scenes()
        repeated['C']['camera_axis'] = repeated['A']['camera_axis']
        with self.assertRaisesRegex(ValueError, '카메라 축'):
            self.app.prepare(path, content(), repeated)
        unlit = scenes()
        unlit['A']['scene'] = 'Jesus listens in the center.'
        with self.assertRaisesRegex(ValueError, '국소 빛'):
            self.app.prepare(path, content(), unlit)

    def test_prepared_candidate_rejects_missing_request_tampering_and_stale_evidence(self):
        self.assertTrue(callable(getattr(self.app, 'prepare', None)), 'Generation preparation is missing')
        path = self.prepared_job()
        prepared = self.app.prepare(path, content(), scenes())
        image = png(path.parent / 'new.png', (1, 2, 3))
        request_path = prepared / 'A-request.json'
        prompt = json.loads(request_path.read_text())['prompt']
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'A', image, prompt)
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'B', image, prompt, request_path=request_path)
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'A', image, 'Changed prompt', request_path=request_path)
        self.app.register_candidate(path, 'A', image, prompt, request_path=request_path)
        image = png(path.parent / 'replacement.png', (4, 5, 6))
        ref = Path(json.loads(request_path.read_text())['referenced_image_paths'][0]).relative_to(prepared)
        for name in ('content.json', 'scenes.json', 'B-request.json', str(ref)):
            target = prepared / name
            original = target.read_bytes()
            target.write_bytes(original + b' ')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.app.register_candidate(path, 'A', image, prompt, request_path=request_path)
            target.write_bytes(original)
        job = self.app.load_job(path)
        job['evidence']['review_note'] += ' corrected'
        self.app.save_job(path, job)
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'A', image, prompt, request_path=request_path)

    def test_extended_copy_requires_explicit_recorded_message(self):
        self.assertTrue(callable(getattr(self.app, 'prepare', None)), 'Generation preparation is missing')
        path = self.prepared_job()
        longer = content()
        longer['threads_text'] += '가' * 301
        longer['blog_text'] = longer['threads_text']
        with self.assertRaises(ValueError):
            self.app.prepare(path, longer, scenes(), extended_message='')
        self.app.prepare(path, longer, scenes(), extended_message='긴 본문 요청 (synthetic test)')
        self.assertEqual(self.app.load_job(path)['prepared']['extended_message'], '긴 본문 요청 (synthetic test)')

    def test_display_reference_requires_verified_quotation_reference(self):
        path = self.prepared_job()
        wrong = content()
        wrong['display_reference'] = '창세 1,1'
        wrong['threads_text'] = wrong['threads_text'].replace('루카 9,50', '창세 1,1')
        wrong['blog_text'] = wrong['threads_text']
        with self.assertRaises(ValueError):
            self.app.prepare(path, wrong, scenes())

    def test_occasion_copy_does_not_require_gospel_quote(self):
        path = self.prepared_job()
        job = self.app.load_job(path)
        job['kind'] = 'occasion'
        occasion = dict(name='테스트 성인', rank='선택 기념일', date='2026-09-28',
                        source_url='https://missa.cbck.or.kr/DailyMissa/20260928',
                        biography_url='https://www.vatican.va/', meaning='Synthetic fixture',
                        symbols='검증된 상징만 사용', choice_note='합성 선택')
        job['evidence']['occasion'] = occasion
        job['evidence']['occasions'] = [occasion]
        self.app.save_job(path, job)
        copy = content()
        copy['threads_text'] = '오늘 9월 28일은 합성 테스트 기념일입니다. 축일을 맞으신 분들께 축하를 전합니다.'
        copy['blog_text'] = copy['threads_text']
        prepared = self.app.prepare(path, copy, scenes())
        self.assertEqual(json.loads((prepared / 'content.json').read_text())['threads_text'], copy['threads_text'])
        self.assertIn('테스트 성인', json.loads((prepared / 'A-request.json').read_text())['prompt'])

    def test_reprepare_preserves_unchanged_candidates_and_blocks_changed_scene(self):
        path = self.prepared_job()
        self.candidates(path)
        self.app.prepare(path, content(), scenes())
        self.app.select_candidate(path, 'A', '합성 선택')
        changed = scenes()
        changed['B']['scene'] = 'A different synthetic viewpoint'
        self.app.prepare(path, content(), changed)
        with self.assertRaises(ValueError):
            self.app.select_candidate(path, 'A', '합성 선택')
        self.register(path, 'B', png(path.parent / 'new-b.png', (1, 2, 3)))
        self.app.select_candidate(path, 'A', '합성 선택')

    def test_legacy_jobs_resume_but_new_jobs_require_preparation(self):
        path = self.app.create_job(self.root, '2026-09-28', 'legacy', 'gospel')
        job = self.app.load_job(path)
        job['evidence'] = evidence()
        self.app.save_job(path, job)
        image = png(path.parent / 'legacy.png', (3, 4, 5))
        with self.assertRaises(ValueError):
            self.app.register_candidate(path, 'A', image, 'Legacy prompt')
        job.pop('generation_contract')
        self.app.save_job(path, job)
        self.app.register_candidate(path, 'A', image, 'Legacy prompt')
        self.assertEqual(self.app.load_job(path)['candidates']['A']['prompt'], 'Legacy prompt')

    def test_cli_prepares_and_registers_native_request_without_prompt_retyping(self):
        path = self.prepared_job()
        copy_file = path.parent / 'source content.json'
        scenes_file = path.parent / 'source scenes.json'
        copy_file.write_text(json.dumps(content(), ensure_ascii=False))
        scenes_file.write_text(json.dumps(scenes(), ensure_ascii=False))
        command = [sys.executable, str(SCRIPT), 'prepare', str(path), str(copy_file), str(scenes_file)]
        result = subprocess.run(command, capture_output=True, text=True, cwd=self.temp.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        prepared = Path(result.stdout.strip())
        self.assertTrue(prepared.is_absolute())
        image = png(path.parent / 'cli image.png', (4, 5, 6))
        candidate = subprocess.run([sys.executable, str(SCRIPT), 'candidate', str(path), 'A', str(image),
                                    '--request-file', str(prepared / 'A-request.json')],
                                   capture_output=True, text=True, cwd=self.temp.name)
        self.assertEqual(candidate.returncode, 0, candidate.stderr)
        self.assertEqual(set(self.app.load_job(path)['candidates']), {'A'})

    def test_full_reference_can_be_written_without_a_hyphen(self):
        path = self.prepared_job()
        copy = content()
        copy['display_reference'] = '루카 9장 46절부터 50절'
        copy['threads_text'] = copy['threads_text'].replace('루카 9,50', copy['display_reference'])
        copy['blog_text'] = copy['threads_text']
        self.app.prepare(path, copy, scenes())

    def test_explicit_long_blog_request_validates_both_channel_bodies(self):
        path = self.prepared_job()
        copy = content()
        copy['blog_text'] += '\n' + '긴 설명. ' * 100
        with self.assertRaises(ValueError):
            self.app.prepare(path, copy, scenes())
        self.app.prepare(path, copy, scenes(), extended_message='블로그는 긴 설명으로 (합성 요청)')
        for key in ('threads_text', 'blog_text'):
            invalid = deepcopy(copy)
            invalid[key] += '!'
            with self.subTest(channel=key), self.assertRaises(ValueError):
                self.app.prepare(path, invalid, scenes(), extended_message='블로그는 긴 설명으로 (합성 요청)')

    def test_verified_scripture_punctuation_is_preserved_but_not_added_to_prose(self):
        path = self.prepared_job()
        job = self.app.load_job(path)
        quote = job['evidence']['quotation']
        job['evidence']['quotation'] = quote + '!'
        job['evidence']['gospel_excerpt'] += '!'
        self.app.save_job(path, job)
        copy = content()
        copy['scripture_quote'] += '!'
        for key in ('threads_text', 'blog_text'):
            copy[key] = copy[key].replace(quote, quote + '!')
        self.app.prepare(path, copy, scenes())
        copy['threads_text'] += '강조!'
        copy['blog_text'] = copy['threads_text']
        with self.assertRaises(ValueError):
            self.app.prepare(path, copy, scenes())

    def test_revisions_only_prepare_fresh_images_and_preserve_old_candidates(self):
        path = self.prepared_job()
        self.candidates(path)
        before = self.app.load_job(path)
        changed = scenes()
        changed['A']['scene'] += ' A newly composed scene.'
        prepared = self.app.prepare(path, content(), changed)
        for label in 'ABC':
            request = json.loads((prepared / f'{label}-request.json').read_text())
            self.assertEqual(len(request['referenced_image_paths']), 2)
            self.assertNotIn('EDIT IMAGE', request['prompt'])
            self.assertTrue(all('repair-target' not in name for name in request['referenced_image_paths']))
        for candidate in before['candidates'].values():
            self.assertEqual(self.app.digest(path.parent / candidate['path']), candidate['sha256'])
        self.assertFalse(callable(getattr(self.app, 'refine', None)))
        result = subprocess.run([sys.executable, str(SCRIPT), 'refine', str(path), 'A',
                                 '--correction', 'Change color'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
