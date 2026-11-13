# Voidtools Everything CLI Reference

Tested local setup:

- ES CLI: `1.1.0.30`
- Everything: `1.5.0.1417` (IPC version verified on 2026-11-12)
- ES path: `J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe`
- Everything path: `J:\Program Files\Everything\Everything.exe`

Use `es.exe` for stdout search results. Use `Everything.exe` only for GUI/service/database actions.

## Setup And Recovery

Use the **Execution Environment** in `../SKILL.md` for every CLI invocation below: request outside-sandbox execution from the first attempt. On this machine, `es.exe` failed to launch inside the sandbox with a Windows DLL relocation error and worked outside it. That startup error does not establish a damaged index or a missing installation.

```powershell
$ES = "J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe"
$Everything = "J:\Program Files\Everything\Everything.exe"

& $ES -version
& $ES -get-everything-version
```

Prefer `& $ES ...` over bare `es`; profile functions may not load in non-interactive shells. Do not add the whole Everything folder to PATH.

Check the fixed paths with `Test-Path -LiteralPath`. If missing, use `Get-Command es, Everything -ErrorAction SilentlyContinue`. If an ES executable is available, locate a missing binary with `& $ES -n 20 es.exe` or `& $ES -n 20 flpsearch.exe`; do not substitute broad drive scans. Optional aliases are `Set-Alias es $ES` and `Set-Alias Everything $Everything`, after verifying each target exists.

If neither a verified executable nor `Get-Command` provides a usable ES, report that filename search is unavailable and stop that search. Do not retry unchanged discovery commands.

Everything must be installed and running; `es.exe` queries it over IPC.

If `es.exe` returns exit code `8` and `$Everything` exists, launch the normal Everything app and retry the original `es.exe` command once:

```powershell
Start-Process -FilePath $Everything -ArgumentList '-startup' -WindowStyle Hidden
Start-Sleep -Seconds 2
& $ES -n 20 report
```

Initial database loading can take longer than the two-second pause. If the retry is still running, keep collecting that same query's output; do not repeatedly launch Everything or describe a pending query as a failure. If it ends with an IPC/startup error, report the observed error and stop. Do not start the Everything service, reindex, update, exit, install tools, or edit profile settings unless the user explicitly asks.

Do not use `-instance` unless the named instance is known to be running.

## Return Model

- Default stdout: one full path per line. Prefer `-csv` or `-tsv` for parsing.
- On the tested Windows setup, redirected ES output uses the system ANSI encoding and can replace characters outside that code page with `?` or other substitutions. CSV does not fix this. If a returned path fails to resolve, check the original through Listary JSON or a scoped filesystem listing before treating it as stale or missing; do not guess replacements.
- `-csv`, `-tsv`, `-txt`, `-efu`, `-m3u`, `-m3u8` change stdout format.
- `-export-csv <file>` and similar write files and do not print result rows.
- Local ES `1.1.0.30` does not support `-json` or `-export-json`; it returns `Error 6: Unknown switch`.
- Useful observed/doc exit codes: `0` success, `6` unknown switch, `8` Everything not found/running, `9` no results with `-no-result-error`.

## Search Syntax

Quote PowerShell metacharacters: `;`, `|`, `&`, `>`, `<`.

Common terms:

```text
abc 123          # AND
abc|123          # OR; quote in PowerShell
!abc             # NOT
"abc 123"        # phrase / spaces
*.pdf            # wildcard
ext:pdf;docx     # extension list; quote as one token
dm:today         # modified today
size:>100mb      # size filter
```

Avoid `content:` for this workflow. Use FileLocator for content search.

Keep syntax conservative and verify version-specific features before relying on them. The CLI version and Everything application version are separate.

`es.exe` does not access Everything bookmarks or filters.

## Safe Recipes

Always cap broad searches with `-n`.

```powershell
& $ES -n 20 report
& $ES -o 20 -n 20 report
& $ES -n 20 -path "D:\Docs" report
& $ES -n 20 -parent "D:\Docs" report
& $ES -n 20 /ad report
& $ES -n 20 /a-d report
& $ES -n 20 "report" "ext:pdf;docx"
& $ES -n 20 "*.pdf" "dm:today"
& $ES -sort size -n 10 -size -dm "size:>100mb"
& $ES -sort date-modified -n 10 -name -path-column -dm report
& $ES -r "^report.*\.pdf$" -n 20
& $ES -case "ABC" -n 20
& $ES -whole-word "pump" -n 20
& $ES -match-path "D:\Docs\report" -n 20
& $ES report -csv -no-header -n 20
& $ES report -get-result-count
& $ES -timeout 3000 report -n 20
```

Use `-get-result-count` before expensive exports or aggregates. Avoid broad `-get-total-size`; scope with `-path` first.

## Everything.exe

These do not return machine-readable search rows:

```powershell
& $Everything -s "ABC|123"
& $Everything -filename "report.pdf"
& $Everything -path "D:\Docs"
& $Everything -startup
```

Do not run these unless explicitly requested:

```powershell
& $Everything -start-service
& $Everything -stop-service
& $Everything -reindex
& $Everything -update
& $Everything -exit
```

File list creation:

```powershell
& $Everything -create-file-list "music.efu" "D:\Music" -create-file-list-include-only-files "*.mp3;*.flac"
```

Sources:
- https://www.voidtools.com/support/everything/command_line_interface/
- https://www.voidtools.com/support/everything/command_line_options/
- https://www.voidtools.com/support/everything/searching/
