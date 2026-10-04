#!/usr/bin/env python3
"""sitemap.xml 자동 생성 스크립트 (순수 HTML 정적 사이트용, 외부 패키지 불필요)

사용법
    python3 generate_sitemap.py            # sitemap.xml 을 새로 씀
    python3 generate_sitemap.py --dry-run  # 파일은 건드리지 않고 결과 요약만 출력

동작 규칙
- 저장소 안의 모든 .html 파일을 찾아 사이트맵에 넣는다. 새 파일은 자동 포함된다.
- index.html 은 폴더 주소(예: /products/101/)로 적는다.
- 제외: 이름이 _ 로 시작하는 파일, google*.html(소유 확인용), index_* (시안),
        noindex 표시가 있는 페이지(예: thanks.html), .git 등 숨김 폴더
- lastmod(마지막 수정일)는 git 이력에서 그 파일을 마지막으로 바꾼 커밋 날짜.
  git 이력이 없거나 얕은 복제본의 맨 아래 커밋이면 기존 sitemap.xml 의 날짜를 유지하고,
  그것도 없으면 파일 수정 시각을 쓴다.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote
from xml.sax.saxutils import escape

BASE_URL = "https://www.changhoinc.com/"
ROOT = os.path.dirname(os.path.abspath(__file__))
SITEMAP = os.path.join(ROOT, "sitemap.xml")

EXCLUDE_NAME_PATTERNS = [
    re.compile(r"^_"),             # 임시·백업 파일
    re.compile(r"^google.*\.html$"),  # 구글 소유 확인 파일
    re.compile(r"^index_"),        # 시안 파일 (index.html 자체는 제외 아님)
]
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re.I)


def git(*args):
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, *args], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:
        return ""


def shallow_boundary():
    path = os.path.join(ROOT, ".git", "shallow")
    if os.path.exists(path):
        with open(path) as f:
            return {line.strip() for line in f if line.strip()}
    return set()


def load_old_lastmod():
    old = {}
    if os.path.exists(SITEMAP):
        text = open(SITEMAP, encoding="utf-8-sig").read()
        for loc, mod in re.findall(
            r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", text
        ):
            old[loc] = mod
    return old


def collect_html():
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if not name.endswith(".html"):
                continue
            if any(p.search(name) for p in EXCLUDE_NAME_PATTERNS) and name != "index.html":
                continue
            rel = os.path.relpath(os.path.join(folder, name), ROOT).replace(os.sep, "/")
            with open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore") as f:
                if NOINDEX_RE.search(f.read()):
                    continue
            found.append(rel)
    return found


def to_url(rel):
    if rel == "index.html":
        return BASE_URL
    if rel.endswith("/index.html"):
        return BASE_URL + quote(rel[: -len("index.html")])
    return BASE_URL + quote(rel)


def lastmod_for(rel, url, old, boundary):
    line = git("log", "-1", "--format=%H %cs", "--", rel)
    if line:
        commit, date = line.split()
        if commit not in boundary:
            return date
        if url in old:  # 얕은 복제본의 맨 아래 커밋 → 정확하지 않으니 기존 날짜 유지
            return old[url]
        return date
    if url in old:
        return old[url]
    ts = os.path.getmtime(os.path.join(ROOT, rel))
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def main():
    dry = "--dry-run" in sys.argv
    old = load_old_lastmod()
    boundary = shallow_boundary()
    entries = []
    for rel in collect_html():
        url = to_url(rel)
        entries.append((url, lastmod_for(rel, url, old, boundary)))
    entries = sorted(set(entries), key=lambda e: (e[0] != BASE_URL, e[0]))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, mod in entries:
        lines += ["  <url>", f"    <loc>{escape(url)}</loc>",
                  f"    <lastmod>{mod}</lastmod>", "  </url>"]
    lines.append("</urlset>")
    xml = "\n".join(lines) + "\n"

    print(f"주소 {len(entries)}개 (이전 {len(old)}개)")
    if dry:
        print("--dry-run: 파일은 쓰지 않았습니다.")
        return
    with open(SITEMAP, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    print("sitemap.xml 갱신 완료")


if __name__ == "__main__":
    main()
