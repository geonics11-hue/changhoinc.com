Set-Location $PSScriptRoot
function Fail($m) { Write-Host ("STOP: " + $m) -ForegroundColor Red; exit 1 }
Write-Host "folder:" (Get-Location)

$msg = git log -1 --format=%s
if ($msg -notlike 'hide myeongfood*') { Fail 'newest commit is not the myeongfood one - nothing changed' }

git fetch origin
if ($LASTEXITCODE -ne 0) { Fail 'fetch failed - nothing changed' }
$remote = @(git diff --name-only HEAD...origin/main)
Write-Host "files changed on remote:" $remote.Count
$remote | ForEach-Object { Write-Host "  " $_ }
$dirty = @(git diff --name-only)
$mine  = @('index.html','products/partner/myeongfood.html','sitemap.xml') + $dirty
$clash = @($remote | Where-Object { $mine -contains $_ })
if ($clash.Count -gt 0) { Write-Host "overlap:"; $clash | ForEach-Object { Write-Host "  " $_ }; Fail 'remote changed the same files - nothing changed, tell Claude' }

git pull --rebase --autostash
if ($LASTEXITCODE -ne 0) { Fail 'pull failed - tell Claude, do not retry' }
git push
if ($LASTEXITCODE -ne 0) { Fail 'push failed - tell Claude, do not retry' }
Write-Host 'push OK. waiting for the live site (up to 3 min)...'

for ($i=0; $i -lt 9; $i++) {
  Start-Sleep -Seconds 20
  $live = (Invoke-WebRequest -Uri ("https://www.changhoinc.com/?t=" + [guid]::NewGuid()) -UseBasicParsing).Content
  if ($live -notmatch 'partner/myeongfood.html') { Write-Host 'LIVE: card removed from home page. DONE' -ForegroundColor Green; return }
}
Write-Host 'LIVE: not updated yet - check again in a few minutes'
