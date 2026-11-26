$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host "folder:" (Get-Location)

# 1) local check: card gone from index.html, noindex present on the page
$idx = Get-Content index.html -Raw -Encoding UTF8
$pg  = Get-Content products\partner\myeongfood.html -Raw -Encoding UTF8
if ($idx -match 'partner/myeongfood.html') { throw 'index.html still links myeongfood - stop' }
if ($pg -notmatch 'noindex') { throw 'myeongfood.html has no noindex - stop' }
Write-Host 'local check OK'

# 2) commit only these 3 files, then push
git add index.html products/partner/myeongfood.html sitemap.xml
git commit -m "hide myeongfood partner card from home, noindex page, remove from sitemap"
git push
Write-Host 'pushed. waiting for the live site (up to 3 min)...'

# 3) live check
for ($i=0; $i -lt 9; $i++) {
  Start-Sleep -Seconds 20
  $live = (Invoke-WebRequest -Uri ("https://www.changhoinc.com/?t=" + [guid]::NewGuid()) -UseBasicParsing).Content
  if ($live -notmatch 'partner/myeongfood.html') { Write-Host 'LIVE: card removed from home page. DONE'; return }
}
Write-Host 'LIVE: not updated yet - check again in a few minutes'
