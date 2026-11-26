Set-Location $PSScriptRoot
function Fail($m) { Write-Host ("STOP: " + $m) -ForegroundColor Red; exit 1 }
Write-Host "folder:" (Get-Location)

# 0) newest local commit must be the myeongfood one
$msg = git log -1 --format=%s
if ($msg -notlike 'hide myeongfood*') { Fail 'newest commit is not the myeongfood one - nothing changed' }

# 1) working folder must be clean (no unsaved edits), otherwise stop
$dirty = @(git status --porcelain --untracked-files=no)
if ($dirty.Count -gt 0) { Write-Host "unsaved edits:"; $dirty | ForEach-Object { Write-Host "  " $_ }; Fail 'unsaved edits in folder - nothing changed, tell Claude' }

# 2) bring GitHub changes under my commit
git pull --rebase
if ($LASTEXITCODE -ne 0) {
  $conf = @(git diff --name-only --diff-filter=U)
  Write-Host "conflict files:" $conf
  if ($conf.Count -eq 1 -and $conf[0] -eq 'sitemap.xml') {
    # sitemap is auto-generated on GitHub: keep GitHub's copy, it drops noindex pages by itself
    git checkout --ours -- sitemap.xml
    git add sitemap.xml
    git -c core.editor=true rebase --continue
    if ($LASTEXITCODE -ne 0) { git rebase --abort; Fail 'could not finish - back to before, tell Claude' }
  } else {
    git rebase --abort
    Fail 'conflict in other files - back to before, tell Claude'
  }
}

# 3) push
git push
if ($LASTEXITCODE -ne 0) { Fail 'push rejected - tell Claude, do not retry' }
Write-Host 'push OK. waiting for the live site (up to 3 min)...' -ForegroundColor Green

# 4) live check
for ($i=0; $i -lt 9; $i++) {
  Start-Sleep -Seconds 20
  $live = (Invoke-WebRequest -Uri ("https://www.changhoinc.com/?t=" + [guid]::NewGuid()) -UseBasicParsing).Content
  if ($live -notmatch 'partner/myeongfood.html') { Write-Host 'LIVE: card removed from home page. DONE' -ForegroundColor Green; return }
}
Write-Host 'LIVE: not updated yet - refresh the home page in a few minutes'
