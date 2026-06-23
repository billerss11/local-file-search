---
name: local-file-search
description: Use when Codex needs to quickly locate local Windows files, folders, or indexed document contents using Everything CLI (`es`) and FileLocator Pro CLI (`flpidx`, `flpsearch`) instead of slow recursive file reading. Trigger for local file/folder search, finding documents by name/path, listing FileLocator indexes, searching indexed document contents, or setting up these CLIs when missing.
---

# Local File Search

Use indexed local search before recursive scans or reading many files. Keep output capped and return only useful candidate paths.

## Tool Discovery

Check commands first:

```powershell
Get-Command es, flpidx, flpsearch -ErrorAction SilentlyContinue
```

If missing, probe known paths. If the user gives a nonstandard FileLocator path, put it in `$knownFileLocatorDir`; otherwise leave it `$null`. Use temporary aliases for the current PowerShell session, or call absolute paths directly:

```powershell
$everythingCli = @(
  "$env:LOCALAPPDATA\Programs\EverythingCLI\es.exe",
  "$env:ProgramFiles\Everything\es.exe",
  "${env:ProgramFiles(x86)}\Everything\es.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $everythingCli) {
  $everythingCli = Get-ChildItem @(
    "$env:LOCALAPPDATA\Programs\EverythingCLI",
    "$env:ProgramFiles\Everything",
    "${env:ProgramFiles(x86)}\Everything"
  ) -Filter es.exe -Recurse -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty FullName -First 1
}

$knownFileLocatorDir = $null # Set to a user-provided path when available.
$fileLocatorDir = @(
  $knownFileLocatorDir,
  "$env:ProgramFiles\Mythicsoft\FileLocator Pro",
  "${env:ProgramFiles(x86)}\Mythicsoft\FileLocator Pro"
) | Where-Object {
  $_ -and
  (Test-Path -LiteralPath (Join-Path $_ "flpidx.exe")) -and
  (Test-Path -LiteralPath (Join-Path $_ "flpsearch.exe"))
} | Select-Object -First 1

if (-not $fileLocatorDir -and (Get-Command es -ErrorAction SilentlyContinue)) {
  $flpsearchPath = es -n 20 flpsearch.exe |
    Where-Object { $_ -like "*\flpsearch.exe" } |
    Select-Object -First 1
  if ($flpsearchPath) { $fileLocatorDir = Split-Path -Parent $flpsearchPath }
}

if ($everythingCli) { Set-Alias -Name es -Value $everythingCli }
if ($fileLocatorDir) {
  Set-Alias -Name flpidx -Value (Join-Path $fileLocatorDir "flpidx.exe")
  Set-Alias -Name flpsearch -Value (Join-Path $fileLocatorDir "flpsearch.exe")
}
```

Prefer aliases/commands when available. Do not assume user-specific drives.

## Filename Or Path Search

Use Everything for names and paths. Always cap results:

```powershell
es -n 50 "oil and gas"
```

If using an absolute path:

```powershell
& $everythingCli -n 50 "oil and gas"
```

## Indexed Content Search

Use FileLocator for indexed document contents.

List indexes first:

```powershell
flpidx -list
```

Search a chosen index and write results to a file:

```powershell
$out = Join-Path (Get-Location) "work\flpsearch-results.txt"
New-Item -ItemType Directory -Path (Split-Path $out) -Force | Out-Null
flpsearch -idxname "AU Oil and gas Nopims" -c "Nopims" -o $out -oft -ofr:files
Get-Content -LiteralPath $out -TotalCount 40
```

With absolute paths:

```powershell
& "$fileLocatorDir\flpidx.exe" -list
& "$fileLocatorDir\flpsearch.exe" -idxname "AU Oil and gas Nopims" -c "Nopims" -o $out -oft -ofr:files
```

For FileLocator index searches using `-idxname` or `-idxpath`, only `-c` is used as an additional search restriction. Filename, date, and attribute filters are ignored.

## Optional Setup

Do not silently download tools, start services, or edit `$PROFILE`. Only do setup when the user asks or a required CLI is missing and you clearly state the side effect.

If Everything CLI is missing but Everything is installed, offer to download the official CLI zip:

```powershell
$dir = "$env:LOCALAPPDATA\Programs\EverythingCLI"
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$zip = Join-Path $env:TEMP "ES-1.1.0.30.x64.zip"
Invoke-WebRequest "https://www.voidtools.com/ES-1.1.0.30.x64.zip" -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $dir -Force
```

If Everything is not running, try a health check:

```powershell
es -n 1 "*"
```

If it fails, offer to start `Everything.exe`; do not install or reconfigure the service automatically.

For a Codex session, prefer temporary aliases in the current PowerShell session. They avoid PATH changes and do not edit the user's profile. Do not use `-Scope Process`; it is not valid for `Set-Alias` in Windows PowerShell.

```powershell
Set-Alias -Name es -Value "...\es.exe"
Set-Alias -Name flpidx -Value "...\flpidx.exe"
Set-Alias -Name flpsearch -Value "...\flpsearch.exe"
```

Only add permanent aliases to `$PROFILE` when the user explicitly asks. Prefer aliases over PATH. FileLocator must use aliases, not function wrappers, because flags like `-ofr:files` can be split incorrectly by functions.
