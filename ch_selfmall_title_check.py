#!/usr/bin/env python3
"""자사몰 게시 전 제목 점검 (2026-10-29)

사용법 (저장소 뿌리에서)
    python3 ch_selfmall_title_check.py                 # 아직 안 올린 바뀐/새 html 만 점검
    python3 ch_selfmall_title_check.py 파일1 파일2 ...   # 지정한 파일만
    python3 ch_selfmall_title_check.py --all           # 사이트 전체 요약

판정
    막힘 = 올리면 안 됨 (고친 뒤 다시 돌린다)
    주의 = 사람이 보고 판단 (이유를 보고에 적는다)
"""
import html, os, re, subprocess, sys, collections

TAIL = '| 창호종합기계'
LIMIT = {'products': 40, 'cases': 40, 'repair': 40}   # 사례·자가수리 기준은 나나파파 결정 전 임시값
ORIGIN = re.compile(r'중국산|대만산|국내산|이탈리아산|독일산|일본산|터키산|수입산')
SERIES = re.compile(r'(?:^|[\s—-])\d{3}\.\s')          # 「— 111. 」 같은 사내 계열 번호
INNER = re.compile(r'중분류|대역|소급|SUPPLY JOURNEY|A/S')  # 제목에 넣지 않는 사내 말·옛 표기


def clean(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x))).strip() if x else ''


def read(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        s = f.read()
    head = s.split('</head>')[0]
    g = lambda pat, src=head: (re.search(pat, src, re.S | re.I) or [None, ''])[1]
    return dict(
        title=clean(g(r'<title[^>]*>(.*?)</title>')),
        og=clean(g(r'<meta[^>]+content="([^"]*)"[^>]*property="og:title"') or g(r'<meta[^>]+property="og:title"[^>]*content="([^"]*)"')),
        desc=clean(g(r'<meta[^>]+content="([^"]*)"[^>]*name="description"') or g(r'<meta[^>]+name="description"[^>]*content="([^"]*)"')),
        h1=clean(g(r'<h1[^>]*>(.*?)</h1>', s)),
        skip=bool(re.search(r'noindex|http-equiv=["\']refresh', head, re.I)),
    )


def all_html():
    out = []
    for dp, dn, fn in os.walk('.'):
        dn[:] = [d for d in dn if not d.startswith('.')]
        out += [os.path.join(dp, f)[2:] for f in fn if f.endswith('.html') and not f.startswith('google')]
    return sorted(out)


def changed():
    r = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all'], capture_output=True, text=True)
    files = [l[3:].strip().strip('"') for l in r.stdout.splitlines()]
    r2 = subprocess.run(['git', 'diff', '--name-only', '@{u}..HEAD'], capture_output=True, text=True)
    files += r2.stdout.split()
    return sorted({f for f in files if f.endswith('.html') and os.path.exists(f)})


def check(path, info, titles):
    block, warn = [], []
    t = info['title']
    sec = path.split('/')[0] if '/' in path else ''
    if not t:
        return ['제목 없음'], []
    if not t.endswith(TAIL):
        block.append('끝이 「| 창호종합기계」가 아님')
    if not info['og']:
        block.append('공유용 제목(og:title) 없음')
    elif info['og'] != t:
        block.append('공유용 제목이 화면 제목과 다름')
    if not info['desc']:
        block.append('검색 설명(description) 없음')
    if SERIES.search(t):
        block.append('사내 계열 번호가 제목에 있음')
    if ORIGIN.search(t):
        block.append('원산지 낱말이 제목에 있음')
    if INNER.search(t):
        warn.append('사내 말·옛 표기: ' + ','.join(sorted(set(INNER.findall(t)))))
    others = [p for p in titles.get(t, []) if p != path]
    if others:
        block.append('다른 쪽과 제목이 같음: ' + others[0])
    lim = LIMIT.get(sec)
    if lim and len(t) > lim:
        warn.append(f'{len(t)}자 (기준 {lim}자 안팎)')
    if re.search(r'20\d\d[.\-년]\s?\d{1,2}', t):
        block.append('제목에 날짜가 있음')
    return block, warn


def main():
    args = sys.argv[1:]
    every = all_html()
    infos = {p: read(p) for p in every}
    titles = collections.defaultdict(list)
    for p, i in infos.items():
        if not i['skip'] and i['title']:
            titles[i['title']].append(p)
    if args == ['--all']:
        targets = every
    elif args:
        targets = [a for a in args if a.endswith('.html')]
    else:
        targets = changed()
    if not targets:
        print('점검할 바뀐 html 이 없습니다.')
        return 0
    nb = nw = 0
    for p in targets:
        info = infos.get(p) or read(p)
        if info['skip']:
            continue
        b, w = check(p, info, titles)
        if b or w:
            print(f'\n{p}\n  제목: {info["title"]}  ({len(info["title"])}자)')
            for x in b:
                print('  [막힘]', x)
            for x in w:
                print('  [주의]', x)
        nb += bool(b)
        nw += bool(w) and not b
    print(f'\n점검 {len(targets)}쪽 — 막힘 {nb}쪽 · 주의만 {nw}쪽 · 통과 {len(targets)-nb-nw}쪽')
    return 1 if nb else 0


if __name__ == '__main__':
    sys.exit(main())
