# FileLocator Pro CLI Reference

Scope: FileLocator Pro 9.1.x with `flpsearch.exe`, `flpidx.exe`, `FileLocatorPro.exe`, and `IndexManager.exe`.

Use PowerShell by default. Avoid `cmd /c`; paths and queries often contain spaces/quotes.

## Binaries

| Command | Use |
|---|---|
| `flpsearch.exe` | Console search. Best for automation. |
| `flpidx.exe` | List/create/update/rebuild/remove indexes. |
| `IndexManager.exe -exec` | Run index maintenance without console popup. |
| `FileLocatorPro.exe` | GUI actions: prefill, run, view files. Prefer `flpsearch` for automation. |

Do not assume `FileLocatorLite.exe` or `AgentRansack.exe` exist unless discovered.

## PowerShell Pattern

```powershell
$flpsearch = "J:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe"
$argsList = @("-idxname", "New Group", "-c", "service unit", "-ofrs:tabulated", "-ofc", "-ofr:files")
& $flpsearch @argsList
```

Use argument arrays when a query/path contains spaces or quotes.

## Search Flags

Core:

| Flag | Meaning |
|---|---|
| `-d "C:\A;D:\B"` | Search locations. Semicolon-separated. |
| `-f "*.pdf;*.docx"` | File-name patterns. |
| `-c "text"` | Containing-text query. |
| `-s` / `-sn` | Search subfolders on/off. |
| `-ma "today -1 week"` | Modified after. |
| `-mb "now"` | Modified before. |
| `-cm` / `-cmn` | Content match case on/off. |
| `-fm` / `-fmn` | Filename match case on/off. |

Expression modes:

| Flag | Meaning |
|---|---|
| `-cee` | Plain text content search. |
| `-ceb` | Boolean content search. |
| `-cex` | Regex content search. |
| `-cexl` | Multiline regex content search. |
| `-cew` | Whole-word content search. |
| `-fed` | Wildcard filename search. |
| `-fex` | Regex filename search. |

Use known flags. In tested installs, `flpsearch -h` only returned a docs URL and `-?` errored.

## Output

Prefer machine-readable output:

```powershell
flpsearch -d "C:\Docs" -f "*.pdf;*.docx" -c "casing" -cee -s -ofrs:tabulated -ofc -ofr:files
```

Useful output flags:

| Flag | Meaning |
|---|---|
| `-ofrs:tabulated -ofc` | CSV-style output. Usually best for parsing. |
| `-ofr:files` | File list report. |
| `-ofr:contents` | Content-hit report. |
| `-oc` | Include matched content lines. |
| `-ol N` | Max found lines per file. |
| `-o "out.csv"` | Write file; do not use unless user asks to save/export. |

CSV output may include criteria/statistics before the `Name,Location,...` header. Parse from the header line.

Avoid relying on `-ofx`, `-oflsx`, `-ofbs`, or `-os` unless locally verified.

## Indexed Search

```powershell
flpidx -list
flpsearch -idxname "New Group" -c "deepshield" -ofrs:tabulated -ofc -ofr:files
flpsearch -idxpath "D:\Indexes\Files" -c "pump"
```

Important: with `-idxname` or `-idxpath`, only `-c` further restricts the index search. `-d`, `-f`, dates, and attributes are ignored.

For index path filtering, put it inside `-c`:

```powershell
flpsearch -idxname "Files" -c 'pump lookin:"C:\Users\Person"'
```

If exact phrase plus another term is unreliable, use a two-step approach:

1. Search the rarer term in the index, e.g. `deepshield`.
2. Test candidate files or candidate folders for the exact phrase using `-cee`, e.g. `service unit`.

## Non-Indexed Search

```powershell
flpsearch -d "C:\Docs" -f "*.pdf;*.docx" -c "service unit" -cee -s -ofrs:tabulated -ofc -ofr:files
flpsearch -d "C:\Logs" -f "*.log" -c "ERROR|WARN" -cex -s
flpsearch -d "C:\Data" -f "*.xlsx" -ma "today -1 week" -mb "now" -s -ofrs:tabulated -ofc -ofr:files
```

## Index Maintenance

Read carefully before destructive operations.

```powershell
flpidx -list
flpidx -name "Docs" -update
flpidx -path "D:\FLPIndex\Docs" -recreate
flpidx -name "Docs" -remove
flpidx -path "D:\FLPIndex\Docs" -remove -delete
IndexManager -exec -name "Docs" -update
```

Only create, remove, delete, or rebuild indexes when the user explicitly asks or the task clearly requires it.

## Agent Rules

- Prefer `flpsearch.exe` for unattended search.
- Prefer `flpidx.exe` / `IndexManager.exe -exec` for index maintenance.
- Prefer PowerShell argument arrays for queries with spaces or quotes.
- Prefer `-ofrs:tabulated -ofc` for parsing.
- Use `-oc` only when matching lines are needed.
- Use `-ol N` to cap content lines.
- Quote Windows paths.
- Use semicolons for multiple paths/patterns.
- Parse stdout; exit codes are not clearly documented.
- If first run triggers license/setup UI, configure FileLocator Pro before automation.

Sources:
- https://help.mythicsoft.com/filelocatorpro/en/commandline.htm
- https://download.mythicsoft.com/help/v9/FileLocatorPro_en.pdf
- https://qa.mythicsoft.com/24701/location-filter-path-look-path-index-search-from-command-line
