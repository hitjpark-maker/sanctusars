#!/usr/bin/env python3
"""Local records for the SanctusArs Codex workflow; no AI or posting API."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import shutil
import tempfile
import struct
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse


def resolve_date(value: str, now: datetime) -> str:
    if now.tzinfo is None:
        raise ValueError('Timezone-aware current time required')
    if value in ('오늘', '내일'):
        day = now.astimezone(ZoneInfo('Asia/Seoul')).date()
        return (day + timedelta(days=value == '내일')).isoformat()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('날짜는 YYYY-MM-DD, 오늘 또는 내일이어야 합니다')
    return date.fromisoformat(value).isoformat()


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_job(path: Path, data: dict) -> None:
    path = Path(path)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.record-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_job(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('지원하지 않는 제작 기록입니다')
    return data


def create_job(root: Path, date: str, post_id: str, kind: str) -> Path:
    day = resolve_date(date, datetime.now(timezone.utc))
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', post_id):
        raise ValueError('post_id는 영문 소문자, 숫자, 하이픈만 허용합니다')
    if kind not in ('gospel', 'occasion'):
        raise ValueError('kind는 gospel 또는 occasion이어야 합니다')
    directory = Path(root) / day / post_id
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / 'job.json'
    save_job(path, dict(schema_version=1, brand='SanctusArs', date=day,
                       timezone='Asia/Seoul', calendar='한국 천주교',
                       post_id=post_id, kind=kind, created_at=timestamp(),
                       evidence={}, candidates={}, selection=None,
                       final_approval=None, history=[]))
    return path


def normalized(text: str) -> str:
    return re.sub(r'\s+', '', text)


def web_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username


def validate_evidence(job: dict) -> list[str]:
    """Structural consistency only; Codex must read and compare real sources."""
    errors = []
    e = job.get('evidence')
    if not isinstance(e, dict):
        return ['검증 자료가 없습니다']
    required = ('primary_url', 'checked_at', 'body_date', 'liturgical_day',
                'calendar_url', 'calendar_date', 'calendar_day', 'mass_form',
                'gospel_reference', 'gospel_section', 'quotation', 'gospel_excerpt',
                'crosscheck_url', 'crosscheck_date', 'crosscheck_mass_form',
                'crosscheck_reference', 'review_note')
    for key in required:
        if not isinstance(e.get(key), str) or not e[key].strip():
            errors.append(f'검증 자료 누락: {key}')
    if errors:
        return errors
    for key in ('primary_url', 'calendar_url', 'crosscheck_url'):
        if not web_url(e[key]):
            errors.append(f'HTTPS 출처 필요: {key}')
    if urlparse(e['primary_url']).hostname != 'missa.cbck.or.kr':
        errors.append('기본 출처는 주교회의 날짜별 매일미사여야 합니다')
    if not urlparse(e['primary_url']).path.startswith('/DailyMissa/' + job['date'].replace('-', '')):
        errors.append('공식 출처 URL 날짜 불일치')
    for key in ('body_date', 'calendar_date', 'crosscheck_date'):
        if e[key] != job['date']:
            errors.append(f'요청 날짜 불일치: {key}')
    for left, right in (('liturgical_day', 'calendar_day'),
                        ('mass_form', 'crosscheck_mass_form'),
                        ('gospel_reference', 'crosscheck_reference')):
        if normalized(e[left]) != normalized(e[right]):
            errors.append(f'출처 간 불일치: {left}')
    if e['gospel_section'] != '복음':
        errors.append('복음 본문 구역을 확인해야 합니다')
    if normalized(e['quotation']) not in normalized(e['gospel_excerpt']):
        errors.append('인용문이 확인한 복음 본문과 다릅니다')
    try:
        if datetime.fromisoformat(e['checked_at']).tzinfo is None:
            raise ValueError()
    except ValueError:
        errors.append('확인 시각은 시간대가 포함된 ISO 날짜여야 합니다')
    if e.get('unresolved_choices') != []:
        errors.append('미사·기념일 선택 또는 출처 충돌이 미해결 상태입니다')
    if not isinstance(e.get('occasions'), list):
        errors.append('기념일 조사 결과 목록이 필요합니다 (없으면 빈 목록)')
    if job['kind'] == 'occasion':
        occasion = e.get('occasion', {})
        if not isinstance(occasion, dict):
            return errors + ['특별 포스팅 대상 자료가 잘못되었습니다']
        for key in ('name', 'rank', 'date', 'source_url', 'biography_url',
                    'meaning', 'symbols', 'choice_note'):
            if not isinstance(occasion.get(key), str) or not occasion[key].strip():
                errors.append(f'특별 포스팅 자료 누락: {key}')
        if occasion.get('date') != job['date']:
            errors.append('특별 포스팅 거행 날짜 불일치')
        if not web_url(occasion.get('source_url')) or not web_url(occasion.get('biography_url')):
            errors.append('특별 포스팅 교회 출처가 필요합니다')
        if not any(isinstance(o, dict) and o.get('name') == occasion.get('name')
                   and o.get('date') == occasion.get('date')
                   for o in (e['occasions'] if isinstance(e.get('occasions'), list) else [])):
            errors.append('조사한 기념일 목록에 선택한 대상이 없습니다')
    return errors


def require_evidence(job: dict) -> None:
    errors = validate_evidence(job)
    if errors:
        raise ValueError('검증 보류: ' + '; '.join(errors))


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context_hash(job: dict) -> str:
    # All verified context, including occasion identity, binds every candidate.
    payload = {key: job[key] for key in ('date', 'kind', 'post_id', 'calendar', 'timezone', 'evidence')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def inside(job_path: Path, name: str) -> Path:
    root = Path(job_path).resolve().parent
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('파일은 현재 제작 건 안에 있어야 합니다')
    return path


def image_type(path: Path) -> str:
    data = Path(path).read_bytes()
    if len(data) >= 33 and data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
        return '.png'
    if len(data) > 4 and data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9'):
        return '.jpg'
    if len(data) >= 20 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return '.webp'
    raise ValueError('PNG/JPEG/WebP 이미지 파일이 필요합니다 (시각 검토는 별도)')


def note(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('사용자의 실제 결정 메시지를 기록해야 합니다')


def register_candidate(job_path: Path, label: str, image: Path, prompt: str) -> None:
    job = load_job(job_path)
    require_evidence(job)
    if label not in ('A', 'B', 'C') or not prompt.strip():
        raise ValueError('A/B/C와 실제 생성 프롬프트가 필요합니다')
    extension = image_type(image)
    checksum = digest(image)
    if any(c['sha256'] == checksum for c in job['candidates'].values()):
        raise ValueError('기존 후보와 동일한 이미지입니다')
    directory = inside(job_path, 'candidates')
    directory.mkdir(exist_ok=True)
    version = 1
    while (directory / f'{label}-v{version}{extension}').exists():
        version += 1
    target = directory / f'{label}-v{version}{extension}'
    shutil.copyfile(image, target)
    job['candidates'][label] = dict(path=str(target.relative_to(job_path.parent.resolve())),
                                    sha256=checksum, prompt=prompt,
                                    context_hash=context_hash(job), created_at=timestamp())
    job['selection'] = None
    job['final_approval'] = None
    job.pop('preview', None)
    job['history'].append(dict(action='candidate', label=label, **job['candidates'][label]))
    save_job(job_path, job)


def require_candidates(job_path: Path, job: dict) -> None:
    require_evidence(job)
    if set(job['candidates']) != set('ABC'):
        raise ValueError('실제 시안 A/B/C 세 개가 모두 준비되어야 합니다')
    for candidate in job['candidates'].values():
        if candidate['context_hash'] != context_hash(job):
            raise ValueError('복음·날짜·검증 자료 변경: 시안을 다시 검토·등록하세요')
        path = inside(job_path, candidate['path'])
        if not path.is_file() or digest(path) != candidate['sha256']:
            raise ValueError('후보 이미지가 변경되거나 없습니다')


def select_candidate(job_path: Path, label: str, user_message: str) -> None:
    note(user_message)
    job = load_job(job_path)
    require_candidates(job_path, job)
    if label not in job['candidates']:
        raise ValueError('A/B/C 중 선택하세요')
    job['selection'] = dict(label=label, sha256=job['candidates'][label]['sha256'],
                            context_hash=context_hash(job), user_message=user_message, at=timestamp())
    job['final_approval'] = None
    job.pop('preview', None)
    job['history'].append(dict(action='select', **job['selection']))
    save_job(job_path, job)


def require_selection(job_path: Path, job: dict) -> None:
    require_candidates(job_path, job)
    s = job.get('selection')
    if not s or s['context_hash'] != context_hash(job) or s['sha256'] != job['candidates'][s['label']]['sha256']:
        raise ValueError('현재 시안에 대한 사용자 선택이 필요합니다')


def approve_final(job_path: Path, files: list[Path], user_message: str) -> None:
    note(user_message)
    job = load_job(job_path)
    require_selection(job_path, job)
    preview = job.get('preview')
    if not preview or not preview.get('rendered'):
        raise ValueError('검토한 최종 PNG와 미리보기가 필요합니다')
    expected = set(preview['files'])
    supplied = {str(inside(job_path, str(p.resolve())).relative_to(job_path.parent.resolve())) for p in files}
    if supplied != expected:
        raise ValueError('미리보기의 모든 최종 파일을 승인해야 합니다')
    checksums = {name: digest(inside(job_path, name)) for name in expected}
    if checksums != preview['files'] or preview['context_hash'] != context_hash(job):
        raise ValueError('미리보기 이후 파일 또는 복음이 바뀌었습니다')
    job['final_approval'] = dict(files=checksums, context_hash=context_hash(job),
                                 selection=job['selection'], user_message=user_message, at=timestamp())
    job['history'].append(dict(action='approve', approval=job['final_approval'], at=timestamp()))
    save_job(job_path, job)


def verify_approval(job_path: Path) -> list[str]:
    job = load_job(job_path)
    try:
        require_selection(job_path, job)
        approval = job.get('final_approval')
        if not approval or approval['context_hash'] != context_hash(job) or approval['selection'] != job['selection']:
            raise ValueError('현재 결과의 최종 승인이 필요합니다')
        if not job.get('preview') or approval['files'] != job['preview']['files']:
            raise ValueError('승인된 미리보기가 아닙니다')
        for name, checksum in approval['files'].items():
            if digest(inside(job_path, name)) != checksum:
                raise ValueError('승인 후 파일이 바뀌었습니다: ' + name)
    except (ValueError, KeyError, OSError) as exc:
        return [str(exc)]
    return []


def data_url(path: Path, mime: str) -> str:
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def render_preview(job_path: Path, image: Path, content: dict, logo: Path, font: Path) -> Path:
    job = load_job(job_path)
    require_selection(job_path, job)
    image = inside(job_path, str(image.resolve()))
    if digest(image) != job['selection']['sha256']:
        raise ValueError('선택한 이미지와 다릅니다. 수정본은 후보 등록 후 선택해 주세요')
    for key in ('scripture_quote', 'reference', 'meditation', 'prayer',
                'threads_text', 'blog_text', 'card_text', 'card_kind'):
        if not isinstance(content.get(key), str) or not content[key].strip():
            raise ValueError('본문 누락: ' + key)
    if not isinstance(content.get('question', ''), str):
        raise ValueError('question은 생략하거나 문자열로 작성하세요')
    e = job['evidence']
    if normalized(content['scripture_quote']) != normalized(e['quotation']) or normalized(content['reference']) != normalized(e['gospel_reference']):
        raise ValueError('본문의 복음 인용·장절이 검증 자료와 다릅니다')
    if content['card_kind'] not in ('scripture', 'meditation'):
        raise ValueError('card_kind는 scripture 또는 meditation입니다')
    if content['card_kind'] == 'scripture' and normalized(content['card_text']) not in normalized(e['gospel_excerpt']):
        raise ValueError('카드 성경 인용이 검증 자료와 다릅니다')
    if len(content['card_text']) > 90:
        raise ValueError('카드 핵심 문구는 90자 이내로 작성하세요')
    image_mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp'}
    image_uri = data_url(image, image_mime[image_type(image)])
    logo_uri = data_url(logo, image_mime[image_type(logo)])
    font_header = font.read_bytes()[:4]
    font_mime = {b'\x00\x01\x00\x00': 'font/ttf', b'OTTO': 'font/otf', b'wOFF': 'font/woff', b'wOF2': 'font/woff2'}
    if font_header not in font_mime:
        raise ValueError('사용 권한을 확인한 TTF/OTF/WOFF 글꼴이 필요합니다')
    preview_root = inside(job_path, 'preview')
    preview_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='v-', dir=preview_root))
    payload = dict(content, image=image_uri, logo=logo_uri, font=data_url(font, font_mime[font_header]),
                   date=job['date'], day=e['liturgical_day'], mass=e['mass_form'], brand='SanctusArs',
                   kind=job['kind'], occasion=e.get('occasion', {}).get('name', ''),
                   sources={key: e[key] for key in ('primary_url', 'calendar_url', 'crosscheck_url')})
    template = (Path(__file__).resolve().parents[1] / 'templates' / 'card.html').read_text(encoding='utf-8')
    # Escape '<' even inside JSON so a supplied sentence cannot close the script tag.
    encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = directory / 'review.html'
    page.write_text(template.replace('__PAYLOAD__', encoded), encoding='utf-8')
    (directory / 'content.json').write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for channel in ('threads', 'blog'):
        (directory / f'{channel}.txt').write_text(content[f'{channel}_text'] + '\n', encoding='utf-8')
    source = dict(date=job['date'], calendar=job['calendar'], kind=job['kind'], evidence=e)
    (directory / 'sources.json').write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    job['preview'] = dict(directory=str(directory.relative_to(job_path.parent.resolve())),
                           context_hash=context_hash(job), rendered=False,
                           files={str(p.relative_to(job_path.parent.resolve())): digest(p) for p in directory.iterdir()})
    job['final_approval'] = None
    job['history'].append(dict(action='preview', directory=job['preview']['directory'], at=timestamp()))
    save_job(job_path, job)
    return page


def register_rendered(job_path: Path, artwork: Path, card: Path, review_note: str) -> None:
    note(review_note)
    job = load_job(job_path)
    require_selection(job_path, job)
    preview = job.get('preview')
    if not preview or preview['context_hash'] != context_hash(job):
        raise ValueError('현재 제작 건의 미리보기를 먼저 만드세요')
    for name, checksum in preview['files'].items():
        if digest(inside(job_path, name)) != checksum:
            raise ValueError('미리보기 파일이 바뀌었습니다. 다시 조판하세요')
    for source in (artwork, card):
        if image_type(source) != '.png' or struct.unpack('!II', source.read_bytes()[16:24]) != (1080, 1350):
            raise ValueError('렌더링 결과는 1080×1350 PNG여야 합니다')
    directory = inside(job_path, preview['directory'])
    for source, name in ((artwork, 'artwork.png'), (card, 'card.png')):
        target = directory / name
        if target.exists():
            raise ValueError('기존 렌더링을 보존합니다. 새 미리보기를 만들어 주세요')
        shutil.copyfile(source, target)
        preview['files'][str(target.relative_to(job_path.parent.resolve()))] = digest(target)
    preview['rendered'] = True
    preview['render_review'] = review_note
    job['final_approval'] = None
    save_job(job_path, job)


def export_approved(job_path: Path) -> Path:
    errors = verify_approval(job_path)
    if errors:
        raise ValueError('; '.join(errors))
    job = load_job(job_path)
    parent = inside(job_path, 'export')
    parent.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.pending-', dir=parent))
    try:
        for name, checksum in job['final_approval']['files'].items():
            source = inside(job_path, name)
            target = stage / source.name
            if target.exists():
                raise ValueError('출력 파일 이름이 중복됩니다')
            shutil.copyfile(source, target)
            if digest(target) != checksum:
                raise ValueError('내보내는 동안 파일이 바뀌었습니다')
        (stage / 'approval.json').write_text(json.dumps(job['final_approval'], ensure_ascii=False, indent=2), encoding='utf-8')
        target = parent / ('approved-' + stage.name.removeprefix('.pending-'))
        stage.rename(target)
        return target
    except BaseException:
        shutil.rmtree(stage)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description='SanctusArs 제작 기록 · AI 생성은 Codex 내장 도구에서 실행')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='한국 날짜 기준 제작 건 시작')
    init.add_argument('date')
    init.add_argument('--root', type=Path, default=Path('output'))
    init.add_argument('--id', default='gospel')
    init.add_argument('--kind', choices=['gospel', 'occasion'], default='gospel')
    for name in ('check', 'status', 'evidence', 'candidate', 'select', 'preview', 'rendered', 'approve', 'export'):
        command = sub.add_parser(name)
        command.add_argument('job', type=Path)
        if name == 'evidence':
            command.add_argument('json_file', type=Path)
        elif name == 'candidate':
            command.add_argument('label', choices=list('ABC'))
            command.add_argument('image', type=Path)
            command.add_argument('--prompt-file', required=True, type=Path)
        elif name == 'select':
            command.add_argument('label', choices=list('ABC'))
            command.add_argument('--message', required=True)
        elif name == 'preview':
            command.add_argument('content', type=Path)
            command.add_argument('--logo', required=True, type=Path)
            command.add_argument('--font', required=True, type=Path)
        elif name == 'rendered':
            command.add_argument('artwork', type=Path)
            command.add_argument('card', type=Path)
            command.add_argument('--review', required=True)
        elif name == 'approve':
            command.add_argument('--message', required=True)
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 11):
            raise ValueError('Python 3.11 이상이 필요합니다')
        if args.command == 'init':
            print(create_job(args.root, args.date, args.id, args.kind).resolve())
            return 0
        path = args.job.resolve()
        job = load_job(path)
        if args.command == 'check':
            require_evidence(job)
            print('검증 기록 일치 — 출처 사실성·이미지 품질은 별도 검토 대상입니다')
        elif args.command == 'status':
            print(json.dumps(dict(date=job['date'], kind=job['kind'],
                                  evidence_errors=validate_evidence(job), candidates=list(job['candidates']),
                                  selection=job['selection'], preview=job.get('preview', {}).get('directory'),
                                  approval_errors=verify_approval(path)), ensure_ascii=False, indent=2))
        elif args.command == 'evidence':
            job['evidence'] = json.loads(args.json_file.read_text(encoding='utf-8'))
            job['selection'] = None
            job['final_approval'] = None
            job.pop('preview', None)
            job['history'].append(dict(action='evidence', at=timestamp(), evidence=job['evidence']))
            save_job(path, job)
            require_evidence(job)
            print('검증 자료 저장·일치 검사 완료')
        elif args.command == 'candidate':
            register_candidate(path, args.label, args.image, args.prompt_file.read_text(encoding='utf-8'))
        elif args.command == 'select':
            select_candidate(path, args.label, args.message)
        elif args.command == 'preview':
            require_selection(path, job)
            image = inside(path, job['candidates'][job['selection']['label']]['path'])
            print(render_preview(path, image, json.loads(args.content.read_text(encoding='utf-8')), args.logo, args.font))
        elif args.command == 'rendered':
            register_rendered(path, args.artwork, args.card, args.review)
        elif args.command == 'approve':
            files = [inside(path, name) for name in job.get('preview', {}).get('files', {})]
            approve_final(path, files, args.message)
        elif args.command == 'export':
            print(export_approved(path))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'중단: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
