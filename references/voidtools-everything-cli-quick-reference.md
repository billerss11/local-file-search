# Voidtools Everything CLI Reference

Tested local setup:

- ES CLI: `1.1.0.30`
- Everything: `1.4.1.1030`
- ES path: `J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe`
- Everything path: `J:\Program Files\Everything\Everything.exe`

Use `es.exe` for stdout search results. Use `Everything.exe` only for GUI/service/database actions.

## PowerShell Pattern

```powershell
$ES = "J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe"
$Everything = "J:\Program Files\Everything\Everything.exe"

& $ES -version
& $ES -get-everything-version
```

Prefer `& $ES ...` over bare `es`; profile functions may not load in non-interactive shells. Do not add the whole Everything folder to PATH.

## Return Model

- Default stdout: one full path per line.
- `-csv`, `-tsv`, `-txt`, `-efu`, `-m3u`, `-m3u8` change stdout format.
- `-export-csv <file>` and similar write files and do not print result rows.
- Local ES `1.1.0.30` does not support `-json` or `-export-json`; it returns `Error 6: Unknown switch`.
- Useful observed/doc exit codes: `0` success, `6` unknown switch, `8` Everything not found/running, `9` no results with `-no-result-error`.

Everything must be installed and running; `es.exe` queries it over IPC.

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

Keep syntax conservative for Everything `1.4.1.1030`; do not rely on Everything 1.5-only syntax unless tested.

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

## Agent Rules

- Prefer `& $ES`, not bare `es.exe`, unless PATH/profile setup is guaranteed.
- Do not add the Everything install folder to PATH.
- Always cap normal searches with `-n <num>`.
- Quote `ext:pdf;docx` and other semicolon/pipe expressions.
- Prefer `-csv` or `-tsv` for parseable output.
- Do not use JSON on local ES `1.1.0.30`.
- Do not use `content:` search.
- Use `Everything.exe` only for GUI/app/service/database actions.
- Do not use `-instance` unless the named instance is known to be running.
- `es.exe` does not access Everything bookmarks or filters.

Sources:
- https://www.voidtools.com/support/everything/command_line_interface/
- https://www.voidtools.com/support/everything/command_line_options/
- https://www.voidtools.com/support/everything/searching/
