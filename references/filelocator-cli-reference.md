# FileLocator Pro CLI compact reference

Scope: FileLocator Pro 9.1.x-style install with `FileLocatorPro.exe`, `flpsearch.exe`, `flpidx.exe`, `IndexManager.exe`.

Do not assume `FileLocatorLite.exe` or `AgentRansack.exe` exist unless discovered locally.

## Tool discovery

```powershell
Get-Command FileLocatorPro.exe, flpsearch.exe, flpidx.exe, IndexManager.exe -ErrorAction SilentlyContinue
```

Common install path:

```powershell
$flpDir = "${env:ProgramFiles}\Mythicsoft\FileLocator Pro"
```

## Binaries

| Command | Use | Returns |
|---|---|---|
| `flpsearch.exe ...` | Console search. Best for automation. | Results to stdout or `-o` file. |
| `FileLocatorPro.exe ...` | GUI app; prefill/run/view searches. | GUI opens unless `-o`; with `-o`, writes file. May leave process running. |
| `flpidx.exe ...` | Console index create/update/list/remove. | Index status/progress/errors. |
| `IndexManager.exe -exec ...` | Run `flpidx` operation without console popup. | Same index operation result as `flpidx`. |

Exit codes are not clearly documented. Agent should parse stdout/output file and handle missing/empty output.

## Search command shape

```bat
flpsearch.exe [saved_search.srf] [criteria] [output]
FileLocatorPro.exe [saved_search.srf] [criteria] [-r] [GUI-only options] [output]
```

`|` in docs is an option separator, not a literal pipe.

Help caveat:

```bat
flpsearch.exe -h
```

In tested Pro install, `-h` only returned the docs URL; `-?` errored. Do not rely on `-?` in automation.

## Core search flags

| Flag | Meaning / return effect |
|---|---|
| `-d "C:\A;D:\B"` | Search location(s). Semicolon-separated. |
| `-dw` | Current working directory. |
| `-f "*.pdf;*.docx"` | File-name pattern(s). |
| `-c "text"` | Containing-text query. |
| `-s` / `-sn` | Search subfolders on/off. |
| `-cm` / `-cmn` | Content match-case on/off. |
| `-fm` / `-fmn` | File-name match-case on/off. |
| `-ma "datetime"` | Modified after. `now` works; relative text like `today -1 week` verified in Pro. |
| `-mb "datetime"` | Modified before. `now` works. |
| `-fx` | Treat `-f` as exclude list. |
| `-cf` | Search command only: content expression spans file; valid with Boolean expressions. |
| `-pa` | Always use CLI params when creating/opening searches. |
| `-pc` | Load config from saved `.srf`. |
| `-po` | CLI params override saved `.srf` values. |
| `-r` | Start GUI search immediately; implied by `-o`. |
| `-resetui` | GUI only: reset UI layout. |
| `-view "file"` | GUI only: open file in internal viewer. |
| `-viewline N` | With `-view`: open at line. |
| `-viewcol N` | With `-view`: open at column. |

Boolean flags can usually be switched off with `n`: `-sn`, `-fmn`, `-cmn`.

## Attribute flags

| Flag | Attribute |
|---|---|
| `-aa` | Archive |
| `-ac` | Compressed |
| `-ae` | Encrypted |
| `-ai` | Index |
| `-af` | Folder |
| `-ah` | Hidden |
| `-ao` | Offline |
| `-ar` | ReadOnly |
| `-asys` | System |
| `-asp` | Sparse |

Runtime-verified: `-aa`, `-af`, `-ah`, `-ar`. Other attribute flags are doc/help-confirmed.

## Expression flags

| Target | Flags |
|---|---|
| Contents `-c` | `-ceb` Boolean, `-cex` regex, `-cexl` multiline regex, `-cee` plain text, `-ceh` Boolean regex, `-cew` whole word, `-cefh` file hash, `-cez` fuzzy. |
| File name `-f` | `-fed` wildcard/DOS, `-fex` regex, `-feb` Boolean, `-fee` plain text, `-feh` Boolean regex, `-few` whole word, `-fez` fuzzy. |
| Look-in `-d` | `-leb` Boolean, `-lex` regex, `-lee` plain text. |
| Regex syntax | `-rep` Perl regex, `-rec` Classic regex. |
| Deprecated | `-fd` = old `-fed`; `-cr` = old `-cex`. Prefer new flags. |

Caveat: `-cefh` file hash is documented but depends on FileLocator hash settings; simple MD5 smoke test may return zero.

## Output flags

| Flag | Meaning / return |
|---|---|
| `-o "out.ext"` | Write output to file; suppress GUI. |
| `-oa` | Append to output file. |
| `-oc` | Include matched content lines. |
| `-ol N` | Max found lines per file in output. |
| `-os` | Output surrounding lines; smoke test did not show extra lines, so verify before relying. |
| `-oea` | ASCII output. |
| `-oe8` | UTF-8 output. |
| `-oe8nb` | UTF-8 no BOM. |
| `-oeu` | Unicode output. |
| `-oeub` | Unicode big-endian. |
| `-oft` | Text format, default. |
| `-ofc` | CSV format. |
| `-ofb` | Tab format. |
| `-ofbs` | Tab spreadsheet; smoke test looked fixed-width, so verify before parsing as tabs. |
| `-ofx` | XML format; smoke test produced text-style output in tested install. Verify locally. |
| `-ofh` | HTML format. |
| `-oflsx` | Search session; smoke test produced text-style output in tested install. Verify locally. |
| `-ofr:files` | File list report. |
| `-ofr:contents` | Content match report. |
| `-ofr:keywords` | Keyword report. |
| `-ofr:file-keywords` | File-keyword report. |
| `-ofr:errors` | Error report. |
| `-ofrs:standard` | Standard report style. |
| `-ofrs:tabulated` | Tabulated report style; required for useful CSV-style output. |
| `-ofxslt "xsl"` | Custom XSLT transform; useful for path-only output. |

CSV caveat: output may include criteria/statistics before the column header. GUI report options can affect this.

## Recommended automation patterns

### File list to CSV

```bat
flpsearch.exe -d "C:\Docs" -f "*.pdf;*.docx" -s -ofrs:tabulated -ofc -ofr:files -o "C:\temp\files.csv"
```

Returns: CSV-style file report, usually with criteria/statistics header plus columns like `Name,Location,Modified,Size,Type,Hits`.

### Content hits to CSV

```bat
flpsearch.exe -d "C:\Repo" -f "*.py;*.md" -c "TODO" -cee -s -oc -ofrs:tabulated -ofc -ofr:contents -o "C:\temp\hits.csv"
```

Returns: content-hit report with matching lines because of `-oc`.

### Regex content search

```bat
flpsearch.exe -d "C:\Logs" -f "*.log" -c "ERROR|WARN" -cex -s -o "C:\temp\log_hits.txt"
```

Returns: default text report of files/hits matching regex.

### Modified-time filter

```bat
flpsearch.exe -d "C:\Data" -f "*.xlsx" -ma "today -1 week" -mb "now" -s -ofrs:tabulated -ofc -ofr:files -o "C:\temp\recent.csv"
```

Returns: file report for files modified in the window.

### GUI prefill only

```bat
FileLocatorPro.exe -d "C:\Docs" -f "*.pdf" -c "casing"
```

Returns: opens GUI with fields prefilled; does not auto-run unless `-r`.

### GUI run immediately

```bat
FileLocatorPro.exe -d "C:\Docs" -f "*.pdf" -c "casing" -s -r
```

Returns: GUI opens and search starts.

### GUI internal viewer

```bat
FileLocatorPro.exe -view "C:\Docs\a.txt" -viewline 50 -viewcol 1
```

Returns: opens file in internal viewer at requested line/column.

### Silent GUI-app export, but prefer `flpsearch`

```bat
FileLocatorPro.exe -d "C:\Windows" -f "*.sys" -o "C:\temp\results.txt"
```

Returns: writes output file; GUI not displayed. Caveat: may leave `FileLocatorPro.exe` running.

### Saved search

```bat
flpsearch.exe "C:\Searches\criteria.srf" -pc -o "C:\temp\out.txt"
FileLocatorPro.exe "C:\Searches\criteria.srf" -f "*.txt" -po -r
```

Returns: first runs saved criteria and writes output; second opens/runs GUI using saved search but overrides file pattern.

## Index search with `flpsearch`

```bat
flpsearch.exe -idxname "Files" -c "pump OR casing" -ofrs:tabulated -ofc -ofr:files -o "C:\temp\idx.csv"
flpsearch.exe -idxpath "D:\Indexes\Files" -c "pump"
```

Returns: matches from selected index.

Important: with `-idxname`/`-idxpath`, only `-c` further restricts search. Other criteria such as `-f`, `-ma`, `-a`, etc. are ignored.

### Index path/location filter

```bat
filelocatorpro.exe -idxname "Files" -c "*.pdf lookin:\"C:\Users\Person\""
```

Returns: index results matching query and path filter. For index path filtering, use `lookin:` inside `-c`, not `-d`.

## Index manager: `flpidx`

Command shape:

```bat
flpidx.exe -name "Index Name" | -path "IndexStorePath" [operation] [options]
```

| Flag | Meaning / return |
|---|---|
| `-list` | Print configured index list. |
| `-create` | Create new index. |
| `-update` | Update index with changed files. |
| `-recreate` | Rebuild index. |
| `-remove` | Remove index reference from configured list. |
| `-delete` | With `-remove`, delete index files too. |
| `-addref` | Add reference to existing index/index group. |
| `-name "Name"` | Select index by configured name. |
| `-path "Path"` | Select/store index by path. |
| `-ab` | Allow binary files; do not detect binary. |
| `-apcn` | Do not allow partial commits. |
| `-ax` | Index/search compressed archives, e.g. zip/tar/7z. |
| `-cf` | Index command only: enable case-sensitive searching. |
| `-d "C:\A;D:\B"` | Locations to index. |
| `-dcn` | Do not include subfolders in index. |
| `-ds` | Index standard document locations. |
| `-f "*.docx;*.pdf;*.txt"` | File types to index. |
| `-fd` | Index standard document file types. |
| `-fm` | Index Outlook PST/MSG files. |
| `-fma` | Index email attachments. |
| `-fnc` | Include file names for non-content file types. |
| `-i` | Index files now after create/configure. |
| `-scheduler` | Start scheduler process. |
| `-verbose` | Print detailed indexing progress. |
| `-help` | Help. |

### Index examples

```bat
flpidx.exe -list
```

Returns: configured indexes.

```bat
flpidx.exe -create -name "Docs" -path "D:\FLPIndex\Docs" -d "D:\Docs;E:\Reports" -f "*.pdf;*.docx;*.txt" -dcn -i
```

Returns: creates index, excludes subfolders, starts indexing, prints status/progress/errors.

```bat
flpidx.exe -create -name "DocsArchive" -path "D:\FLPIndex\DocsArchive" -d "D:\Docs" -f "*.pdf;*.docx;*.zip" -ax -i
```

Returns: creates index including archive files.

```bat
flpidx.exe -name "Docs" -update
flpidx.exe -path "D:\FLPIndex\Docs" -recreate
flpidx.exe -name "Docs" -remove
flpidx.exe -path "D:\FLPIndex\Docs" -remove -delete
```

Returns: update/rebuild/remove/delete status.

```bat
IndexManager.exe -exec -name "Docs" -update
```

Returns: same as `flpidx -name "Docs" -update`, but avoids console popup.

## Agent rules

- Prefer `flpsearch.exe` for unattended search.
- Prefer `flpidx.exe` / `IndexManager.exe -exec` for index maintenance.
- Prefer `-ofrs:tabulated -ofc` for machine-readable output.
- Use `-oc` only when matching lines are required.
- Cap output with `-ol N` for content searches.
- Do not depend on `-?`; use known flags or docs.
- Do not depend on `-ofx`, `-oflsx`, `-ofbs`, or `-os` without local validation.
- For indexed searches, put path filters in `-c` using `lookin:`; do not expect `-d`/`-f`/date/attribute filters to apply.
- Quote Windows paths. Use semicolons for multiple paths/patterns.
- If first run triggers license/setup UI, configure FileLocator Pro before automation.

## Sources

- https://help.mythicsoft.com/filelocatorpro/en/commandline.htm
- https://download.mythicsoft.com/help/v9/FileLocatorPro_en.pdf
- https://qa.mythicsoft.com/13867/command-line-parameters-for-filelocator-pro
- https://qa.mythicsoft.com/21775/saving-command-line-output-to-csv-file
- https://qa.mythicsoft.com/25459/cli-file-search-with-no-header-in-the-output
- https://qa.mythicsoft.com/24701/location-filter-path-look-path-index-search-from-command-line
