# Voidtools Everything CLI quick reference

Tested local setup:

- ES CLI: `1.1.0.30`
- Everything: `1.4.1.1030`
- Local ES path: `J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe`
- Local Everything path: `J:\Program Files\Everything\Everything.exe`

Use `es.exe` for stdout search results. Use `Everything.exe` only for GUI/app/service/database actions.

## PowerShell setup

Do not add the whole Everything folder to PATH. Prefer a per-script variable or wrapper.

```powershell
$ES = 'J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe'
$Everything = 'J:\Program Files\Everything\Everything.exe'
```

Invoke paths with spaces using `&`:

```powershell
& $ES -version
& $ES -get-everything-version
```

If a PowerShell function named `es` already exists, `es ...` may work interactively, but agents should prefer `& $ES ...` because profile functions may not load in non-interactive shells.

## Requirements

- Everything must be installed and running.
- `es.exe` queries the running Everything client over IPC.
- Base syntax: `es.exe [options] [search text]`.

## Return model

- Default: stdout full paths, one result per line.
- `-csv`, `-tsv`, `-txt`, `-efu`, `-m3u`, `-m3u8`: change stdout format.
- `-export-csv <file>`, `-export-tsv <file>`, etc.: write file; no result rows on stdout.
- Local ES `1.1.0.30`: do **not** use `-json` or `-export-json`; returns `Error 6: Unknown switch`.
- Useful exit codes locally/docs: `0` success; `6` unknown switch; `8` Everything IPC/window not found; `9` no results when `-no-result-error` is used.

## Search syntax notes

- Quote search terms containing PowerShell metacharacters: `;`, `|`, `&`, `>`, `<`.
- `ext:<list>` uses semicolon-delimited extensions; in PowerShell quote the whole token.
- Avoid `content:` entirely for this agent workflow.
- For Everything `1.4.1.1030`, keep syntax conservative; do not rely on Everything 1.5-only syntax unless tested.

Common filename/path search terms:

```text
abc 123          # AND
abc|123          # OR; quote in PowerShell if needed
!abc             # NOT
"abc 123"        # literal phrase / spaces
*.pdf            # wildcard
ext:pdf;docx     # extension list; quote in PowerShell
 dm:today        # modified today
size:>100mb      # size filter
```

## Safe ES recipes for agents

Always cap broad searches with `-n`.

```powershell
& $ES -n 20 report
# stdout: first 20 filename matches for report.

& $ES -o 20 -n 20 report
# stdout: 20 results starting at zero-based offset 20.

& $ES -n 20 -path 'D:\Docs' report
# stdout: results under D:\Docs, including subfolders.

& $ES -n 20 -parent 'D:\Docs' report
# stdout: results whose direct parent path is D:\Docs.

& $ES -n 20 /ad report
# stdout: folders only.

& $ES -n 20 /a-d report
# stdout: files only.

& $ES -n 20 'report' 'ext:pdf;docx'
# stdout: report matches with pdf/docx extension.

& $ES -n 20 '*.pdf' 'dm:today'
# stdout: PDFs modified today.

& $ES -sort size -n 10 -size -dm 'size:>100mb'
# stdout: top 10 largest matches, with size and date-modified columns.

& $ES -sort date-modified -n 10 -name -path-column -dm report
# stdout: 10 latest modified matches with name/path/date columns.

& $ES -r '^report.*\.pdf$' -n 20
# stdout: regex filename matches.

& $ES -case 'ABC' -n 20
# stdout: case-sensitive matches.

& $ES -whole-word 'pump' -n 20
# stdout: whole-word matches.

& $ES -match-path 'D:\Docs\report' -n 20
# stdout: matches full path + filename.

& $ES report -csv -n 20
# stdout: CSV formatted results.

& $ES report -tsv -n 20
# stdout: TSV formatted results.

& $ES report -csv -no-header -n 20
# stdout: CSV without header.

& $ES report -export-csv out.csv -n 200
# file: creates out.csv; no result rows on stdout.

& $ES report -get-result-count
# stdout: integer result count only; no filenames; -n ignored.

& $ES report -get-total-size
# caution: can be expensive on broad matches; prefer scoped -path and count first.

& $ES -no-result-error 'unlikely_filename_zzzz'
# no match: returns nonzero exit code locally, observed 9.

& $ES -version
# stdout: ES version; exits.

& $ES -get-everything-version
# stdout: Everything version; exits.

& $ES -timeout 3000 report -n 20
# waits up to 3000 ms for database load before query.
```

Named instance only if you actually run one:

```powershell
& $ES -instance '1.5a' report -n 20
# stdout: query named instance; fails/empty if that instance is not running.
```

## Everything.exe recipes

These are not for stdout search rows.

```powershell
& $Everything -s 'ABC|123'
# GUI: sets/open search. No machine-readable stdout result list.

& $Everything -filename 'report.pdf'
# GUI search by filename. No stdout result list.

& $Everything -path 'D:\Docs'
# GUI search for path. No stdout result list.

& $Everything -startup
# Starts Everything in background. No stdout result list.
```

Disruptive/admin-level actions; do not run unless explicitly requested:

```powershell
& $Everything -start-service
& $Everything -stop-service
# Starts/stops Everything service.

& $Everything -reindex
# Forces database rebuild.

& $Everything -update
# Saves database to disk.

& $Everything -exit
# Exits existing Everything instance.
```

File-list creation:

```powershell
& $Everything -create-file-list 'music.efu' 'D:\Music' -create-file-list-include-only-files '*.mp3;*.flac'
# Creates EFU file list and exits; no search window.
```

## Agent rules

- Prefer `& $ES`, not bare `es.exe`, unless PATH/profile setup is guaranteed.
- Do not add the Everything install folder to PATH.
- Do not use `content:` search.
- Always cap normal searches with `-n <num>`.
- Quote `ext:pdf;docx` and other semicolon/pipe expressions in PowerShell.
- Prefer `-csv` or `-tsv` for parseable local output.
- Do not use JSON on local ES `1.1.0.30`.
- Use `-get-result-count` before expensive exports or aggregates.
- Avoid broad `-get-total-size`; scope with `-path` first.
- Use `Everything.exe` only for GUI/app/service/database actions, not stdout search.
- Do not use `-instance` unless the named Everything instance is known to be running.
- `es.exe` does not access Everything bookmarks or filters.

## Sources

- Voidtools ES CLI docs: https://www.voidtools.com/support/everything/command_line_interface/
- Voidtools Everything.exe command-line options: https://www.voidtools.com/support/everything/command_line_options/
- Voidtools search syntax/searching docs: https://www.voidtools.com/support/everything/searching/
- Voidtools ES GitHub README/releases: https://github.com/voidtools/ES
