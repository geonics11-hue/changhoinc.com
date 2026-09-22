# -*- coding: utf-8 -*-
"""
eh-pr-lx55 실물 갤러리 + 히어로 반영 스크립트 (2026-09-22)
device_bash 에서 changhoinc.com 저장소 루트를 cwd 로 실행한다.
"""
import re, base64, glob, sys, os

ASSET_DIR = "_incoming_eh_pr_lx55_260922"

def b64_of(name):
    with open(os.path.join(ASSET_DIR, name), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

B_229 = b64_of("gallery_229.jpg")
B_238 = b64_of("gallery_238.jpg")
B_242 = b64_of("gallery_242.jpg")
B_HCARD = b64_of("hero_hcard.jpg")
B_LB = b64_of("hero_lbstrip.jpg")
B_RT = b64_of("hero_rowthumb.jpg")

CAP1 = "LX 창호 프로파일 물구멍 위치를 자로 확인하는 모습"
CAP2 = "LX Hausys 각인이 보이는 프로파일에 물구멍 위치를 잰 모습"
CAP3 = "가공을 마친 사각 물구멍에 배수 커버를 끼운 모습"
NEW_SUB = "EH-PR-LX55로 LX 창호 프로파일에 가공한 사각 물구멍과 배수 커버입니다."

NEW_GALLERY = (
    '<div class="gallery">'
    f'<div class="gcell"><img alt="{CAP1}" src="data:image/jpeg;base64,{B_229}"/><div class="gc">{CAP1}</div></div>'
    f'<div class="gcell"><img alt="{CAP2}" src="data:image/jpeg;base64,{B_238}"/><div class="gc">{CAP2}</div></div>'
    f'<div class="gcell"><img alt="{CAP3}" src="data:image/jpeg;base64,{B_242}"/><div class="gc">{CAP3}</div></div>'
    '</div>'
)

report = []

def count_imgs(txt):
    return len(re.findall(r"<img ", txt))

# ---------- 1) eh-pr-lx55.html : 갤러리 + sub + hcard hero + 자기 lb-strip ----------
target = "products/304/eh-pr-lx55.html"
with open(target, encoding="utf-8") as f:
    txt = f.read()
before_imgs = count_imgs(txt)

m_gallery = re.search(r'<div class="gallery"><div class="gcell">.*?</div></div></div>', txt)
assert m_gallery, "gallery block not found"
txt2 = txt[:m_gallery.start()] + NEW_GALLERY + txt[m_gallery.end():]

old_sub = '<div class="sub">물구멍 펀칭기의 실물입니다.</div>'
assert txt2.count(old_sub) == 1, f"sub line match count = {txt2.count(old_sub)}"
txt2 = txt2.replace(old_sub, f'<div class="sub">{NEW_SUB}</div>', 1)

m_hcard = re.search(r'(<div class="hcard"><img alt="[^"]*" src="data:image/jpeg;base64,)[A-Za-z0-9+/=]+(")', txt2)
assert m_hcard, "hcard hero not found"
txt2 = txt2[:m_hcard.start()] + m_hcard.group(1) + B_HCARD + m_hcard.group(2) + txt2[m_hcard.end():]

OWN_LB_RE = r'(<img alt="EH-PR-LX55"(?: class="cur")? src="data:image/jpeg;base64,)[A-Za-z0-9+/=]+(")'
m_lb = re.search(OWN_LB_RE, txt2)
assert m_lb, "own lb-strip thumb not found"
n_lb = len(re.findall(OWN_LB_RE, txt2))
assert n_lb == 1, f"lb-strip match count = {n_lb}"
txt2 = txt2[:m_lb.start()] + m_lb.group(1) + B_LB + m_lb.group(2) + txt2[m_lb.end():]

after_imgs = count_imgs(txt2)
assert before_imgs == after_imgs, f"img count changed {before_imgs} -> {after_imgs}"

with open(target, "w", encoding="utf-8") as f:
    f.write(txt2)
report.append(f"{target}: OK (img {before_imgs}->{after_imgs})")

# ---------- 2) 형제 12곳 : lb-strip 썸네일만 ----------
siblings = [
    "products/304/eh-pr-01a.html",
    "products/304/eh-pr-01b.html",
    "products/304/hp-07.html",
    "products/304/pvc-punch-line.html",
    "products/304/pvc-punch.html",
    "products/304/wtm-24pvc-l1.html",
    "products/304/wtm-pr-01a.html",
    "products/304/wtm-pr-02-02.html",
    "products/304/wtm-pr-02.html",
    "products/304/wtm-pr-02ms.html",
    "products/304/wtm-pr-lxs.html",
]
for f_path in siblings:
    with open(f_path, encoding="utf-8") as f:
        txt = f.read()
    before_imgs = count_imgs(txt)
    n = len(re.findall(OWN_LB_RE, txt))
    if n == 0:
        report.append(f"{f_path}: SKIP (lb-strip alt not found)")
        continue
    assert n == 1, f"{f_path}: lb-strip match count = {n}"
    m = re.search(OWN_LB_RE, txt)
    txt2 = txt[:m.start()] + m.group(1) + B_LB + m.group(2) + txt[m.end():]
    after_imgs = count_imgs(txt2)
    assert before_imgs == after_imgs, f"{f_path}: img count changed"
    with open(f_path, "w", encoding="utf-8") as f:
        f.write(txt2)
    report.append(f"{f_path}: OK (img {before_imgs}->{after_imgs})")

# ---------- 3) index.html : lb-strip + rowthumb(같은 행만) ----------
idx_path = "products/304/index.html"
with open(idx_path, encoding="utf-8") as f:
    txt = f.read()
before_imgs = count_imgs(txt)

n_lb_idx = len(re.findall(OWN_LB_RE, txt))
assert n_lb_idx == 1, f"index lb-strip match count = {n_lb_idx}"
m = re.search(OWN_LB_RE, txt)
txt = txt[:m.start()] + m.group(1) + B_LB + m.group(2) + txt[m.end():]

# rowthumb: eh-pr-lx55.html 을 href 로 갖는 <tr> 안의 rowthumb 만 교체
tr_pattern = re.compile(r'<tr>(?:(?!</tr>).)*?href="eh-pr-lx55\.html"(?:(?!</tr>).)*?</tr>', re.S)
m_tr = tr_pattern.search(txt)
assert m_tr, "eh-pr-lx55 row not found in index.html"
tr_txt = m_tr.group()
n_rt = len(re.findall(r'rowthumb" src="data:image/jpeg;base64,', tr_txt))
assert n_rt == 1, f"rowthumb in row match count = {n_rt}"
m_rt = re.search(r'(rowthumb" src="data:image/jpeg;base64,)[A-Za-z0-9+/=]+(")', tr_txt)
new_tr = tr_txt[:m_rt.start()] + m_rt.group(1) + B_RT + m_rt.group(2) + tr_txt[m_rt.end():]
txt = txt[:m_tr.start()] + new_tr + txt[m_tr.end():]

after_imgs = count_imgs(txt)
assert before_imgs == after_imgs, f"index.html img count changed {before_imgs} -> {after_imgs}"

with open(idx_path, "w", encoding="utf-8") as f:
    f.write(txt)
report.append(f"{idx_path}: OK (img {before_imgs}->{after_imgs}, lb-strip+rowthumb)")

print("\n".join(report))
print("DONE", len(report), "files")
