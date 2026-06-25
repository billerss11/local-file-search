---
name: local-file-search
description: Use when Codex needs to quickly locate local Windows files, folders, or indexed document contents using Everything CLI (`es`) and FileLocator Pro CLI (`flpidx`, `flpsearch`) instead of slow recursive file reading. Trigger for local file/folder search, finding documents by name/path, listing FileLocator indexes, searching indexed document contents, or setting up these CLIs when missing.
---

# Local File Search

Use indexed search before recursive scans. Keep output capped and return only useful paths. Do not save/export results unless the user asks.

Detailed references:
- Everything CLI: `references/voidtools-everything-cli-quick-reference.md`
- FileLocator Pro CLI: `references/filelocator-cli-reference.md`

## Setup

Use PowerShell by default. Avoid `cmd /c` for Everything/FileLocator; paths and queries often contain spaces/quotes. Use `&` with executable variables, and use PowerShell argument arrays when FileLocator arguments contain spaces.

Use the user's fixed install paths first:

```powershell
$everythingCli = "J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe"
$everythingExe = "J:\Program Files\Everything\Everything.exe"
$fileLocatorDir = "J:\Program Files\Mythicsoft\FileLocator Pro"

if (Test-Path -LiteralPath $everythingCli) { Set-Alias es $everythingCli }
if (Test-Path -LiteralPath $everythingExe) { Set-Alias Everything $everythingExe }
if (Test-Path -LiteralPath (Join-Path $fileLocatorDir "flpsearch.exe")) {
  Set-Alias flpsearch (Join-Path $fileLocatorDir "flpsearch.exe")
  Set-Alias flpidx (Join-Path $fileLocatorDir "flpidx.exe")
  if (Test-Path -LiteralPath (Join-Path $fileLocatorDir "FileLocatorPro.exe")) { Set-Alias FileLocatorPro (Join-Path $fileLocatorDir "FileLocatorPro.exe") }
  if (Test-Path -LiteralPath (Join-Path $fileLocatorDir "IndexManager.exe")) { Set-Alias IndexManager (Join-Path $fileLocatorDir "IndexManager.exe") }
}
```

If a command is missing, check:

```powershell
Get-Command es, Everything, flpsearch, flpidx, FileLocatorPro, IndexManager -ErrorAction SilentlyContinue
```

If still missing, do not run broad drive scans by default. Use Everything to locate missing binaries if available:

```powershell
es -n 20 es.exe
es -n 20 flpsearch.exe
```

If `es.exe` returns exit code `8` because Everything is not running, and `$everythingExe` exists, start the normal Everything app with `& $everythingExe -startup`, wait briefly, then retry the original `es.exe` command once. If the retry fails, report that Everything could not be reached. Only download tools, start services, reindex, or edit `$PROFILE` when the user explicitly asks.

## File And Path Search

Use Everything `es.exe` for filename/path search. Prefer `& $everythingCli ...` when `$everythingCli` is set. Always cap broad searches with `-n`.

```powershell
& $everythingCli -n 50 "oil and gas"
& $everythingCli -n 20 -path "D:\Docs" report
& $everythingCli -n 20 -parent "D:\Docs" report
& $everythingCli -n 20 /ad report
& $everythingCli -n 20 /a-d report
& $everythingCli -n 20 "report" "ext:pdf;docx"
& $everythingCli -sort date-modified -n 10 -name -path-column -dm report
& $everythingCli -csv -no-header -n 20 report
& $everythingCli -get-result-count report
```

Rules:
- Quote PowerShell metacharacters: `;`, `|`, `&`, `>`, `<`.
- Quote extension lists as one token: `"ext:pdf;docx"`.
- Do not use `content:`; use FileLocator for content search.
- Do not use `-json` / `-export-json` with local ES `1.1.0.30`.
- Use `Everything.exe` only for GUI/service/database actions, not stdout search rows.
- If `es.exe` returns exit code `8`, use `Everything.exe -startup` to launch Everything and retry the same capped search once.

## Content Search

Use FileLocator for indexed document contents. Prefer `flpsearch.exe` for automation.

```powershell
flpidx -list
flpsearch -idxname "AU Oil and gas Nopims" -c "Nopims" -oft -ofr:files
flpsearch -idxname "AU Oil and gas Nopims" -c "pump OR casing" -ofrs:tabulated -ofc -ofr:files
flpsearch -d "C:\Docs" -f "*.pdf;*.docx" -c "casing" -cee -s -oc -ol 5 -ofrs:tabulated -ofc -ofr:contents
```

For FileLocator queries with spaces, use an argument array:

```powershell
$flpsearch = "J:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe"
$argsList = @("-idxname", "New Group", "-c", "service unit", "-ofrs:tabulated", "-ofc", "-ofr:files")
& $flpsearch @argsList
```

Rules:
- For machine-readable output, prefer `-ofrs:tabulated -ofc`.
- Use `-oc` only when matching lines are needed.
- Use `-ol N` to cap content lines.
- With `-idxname` / `-idxpath`, only `-c` further restricts search.
- For index path filtering, put `lookin:"C:\Path"` inside `-c`; `-d`, `-f`, date, and attribute filters are ignored.
- If exact phrase plus another term is unreliable, search the rarer term first, then test candidate files for the exact phrase with `-cee`.
- Do not rely on `flpsearch -?`; read the bundled reference for uncommon flags.

## Index Maintenance

Use `flpidx.exe` for console index work. Use `IndexManager.exe -exec` to avoid a console popup.

```powershell
flpidx -list
flpidx -name "Docs" -update
IndexManager -exec -name "Docs" -update
```

Read `references/filelocator-cli-reference.md` before creating, deleting, removing, or rebuilding indexes.

## Maintenance

Source repository: https://github.com/billerss11/local-file-search
