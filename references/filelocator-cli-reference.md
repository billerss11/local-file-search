# FileLocator Pro CLI Reference

Scope: FileLocator Pro 9.1.x with `flpsearch.exe`, `flpidx.exe`, `FileLocatorPro.exe`, and `IndexManager.exe`. Official help reviewed on 2026-09-07; local smoke checks used console version 9.1.3389.1. The linked online manual identifies itself as help version 9.0, so inspect local output when using less common options.

Use PowerShell by default. Avoid `cmd /c`; paths and queries often contain spaces/quotes.

## Binaries

| Command | Use |
|---|---|
| `flpsearch.exe` | Console search. Best for automation. |
| `flpidx.exe` | List/create/update/rebuild/remove indexes. |
| `IndexManager.exe -exec` | Run index maintenance without console popup. |
| `FileLocatorPro.exe` | GUI actions: prefill, run, view files. Prefer `flpsearch` for automation. |

Do not assume `FileLocatorLite.exe` or `AgentRansack.exe` exist unless discovered.

## Setup And Recovery

Use the fixed install folder first. The optional aliases below make the short commands in this reference runnable; direct executable paths also work.

```powershell
$flpDir = 'J:\Program Files\Mythicsoft\FileLocator Pro'
foreach ($toolName in 'flpsearch', 'flpidx', 'FileLocatorPro', 'IndexManager') {
  $toolPath = Join-Path $flpDir ($toolName + '.exe')
  if (Test-Path -LiteralPath $toolPath) { Set-Alias -Name $toolName -Value $toolPath }
}
```

If missing, use `Get-Command flpsearch, flpidx, FileLocatorPro, IndexManager -ErrorAction SilentlyContinue`; if still unavailable, locate `flpsearch.exe` through Everything with `-n 20`. Use **Setup And Recovery** in the Everything reference if that tool is unavailable. Do not scan entire drives or install tools automatically. If license/setup UI blocks the first search, complete the app's setup before automation.

If discovery still finds no usable executable, report which tool is unavailable and stop the dependent search. Do not retry unchanged discovery commands.

### PowerShell Pattern

```powershell
$flpsearch = "J:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe"
$argsList = @("-idxname", "New Group", "-c", "service unit", "-ofrs:tabulated", "-ofc", "-ofr:files")
& $flpsearch @argsList
```

Use argument arrays when a query/path contains spaces or quotes. Use single-quoted PowerShell strings when the query contains literal double quotes. Check the echoed search criteria if quoting behaves unexpectedly, especially on older PowerShell versions.

## Search Flags

Core:

| Flag | Meaning |
|---|---|
| `-d "C:\A;D:\B"` | Search locations. Semicolon-separated. |
| `-dw` | Search the current working directory; use only when that is the intended scope. |
| `-f "*.pdf;*.docx"` | File-name patterns. |
| `-c "text"` | Containing-text query. |
| `-s` / `-sn` | Search subfolders on/off. |
| `-cf` / `-cfn` | Boolean terms across the whole file / on the same line. |
| `-fx` / `-fxn` | Treat the file-name expression as exclusions / inclusions. |
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
| `-ceh` | Boolean combinations of regex terms. |
| `-cez` | Fuzzy matching; approximation settings affect results. |
| `-fed` | Wildcard filename search. |
| `-fex` | Regex filename search. |
| `-rep` / `-rec` | Perl / Classic regex syntax. |

Use known flags. In tested installs, `flpsearch -h` only returned a docs URL and `-?` errored.

## Direct Query And Location Patterns

Choose literal text for an exact string, Boolean for combinations, and regex only when pattern matching is needed. Explicitly set the expression type and, for Boolean queries, the file/line scope.

| Need | Arguments |
|---|---|
| Literal phrase | `-c "service unit" -cee` |
| Both terms anywhere in a file | `-c "pump AND casing" -ceb -cf` |
| Both terms on one line | `-c "pump AND casing" -ceb -cfn` |
| Either term, excluding a third | `-c "(pump OR casing) NOT cancelled" -ceb -cf` |
| Nearby terms | `-c "pump NEAR:40 casing" -ceb -cf` (distance is in characters, not words) |
| Line-based regex | `-c "ERROR[0-9]+" -cex -rep` |
| Multiline regex | Use `-cexl`; specify newline matching in the expression. |

For Boolean phrases, preserve embedded quotes, e.g. `-c '"service unit" AND pump' -ceb -cf`. `LIKE` is available for approximate Boolean terms. These are direct-search patterns; index queries have different matching rules below.

`-d` accepts an individual file as well as folders. This is useful for verifying index candidates without rescanning their parent folders:

```powershell
flpsearch -d "C:\Docs\report.pdf" -c "service unit" -cee -oc -ol 5 -ofrs:tabulated -ofc -ofr:contents
flpsearch -d "C:\Docs;D:\Reports;!C:\Docs\Archive" -f "*.pdf;*.docx" -fed -c "pump" -cee -s -ofrs:tabulated -ofc -ofr:files
```

An entry beginning with `!` excludes a specific location. Folder filters such as `-.svn` exclude matching folder names. An existing newline-separated location list can be passed as `-d "=C:\Lists\locations.txt"`. Do not broaden the user's scope with drive-wide macros.

For a literal semicolon inside a file/folder name, pass double quotes through to FileLocator. PowerShell's outer quotes only group the argument and are not enough: `-d "C:\Docs\2026;final"` is interpreted as two locations. The following form was tested with PowerShell 7.6.5 and FileLocator 9.1.3389.1:

```powershell
flpsearch -d '"C:\Docs\2026;final"' -c "pump" -cee -s -ofrs:tabulated -ofc -ofr:files

# Preserve the same inner double quotes in an argument array.
$argsList = @('-d', '"C:\Docs\2026;final"', '-c', 'pump', '-cee', '-s', '-ofrs:tabulated', '-ofc', '-ofr:files')
& $flpsearch @argsList
```

Do not quote a genuine multi-location list as a single literal path; its separating semicolons must remain outside individual quoted paths.

### Verify Body Text

Character Processing settings can include file names or paths in content searches. In the local check, a file named `pump casing.txt` with unrelated body text appeared in the file report with a hit, but had no matching rows in the contents report. Therefore, inspect body lines before saying a document contains the query.

For direct Boolean searches, the following excludes the synthetic filename line (line 0) without changing the user's configuration:

```powershell
flpsearch -d "C:\Docs" -f "*.txt;*.pdf;*.docx" -fed -c 'LINES:1+ ("service unit" AND pump)' -ceb -cf -s -oc -ol 5 -ofrs:tabulated -ofc -ofr:contents
```

This was locally checked with separate-line terms and a filename-only false match. Treat reported line numbers as extracted-text positions, not necessarily PDF page or Word paragraph numbers. When body text cannot be verified, describe the result as a candidate match.

## Output

Prefer machine-readable output:

```powershell
flpsearch -d "C:\Docs" -f "*.pdf;*.docx" -fed -c "casing" -cee -s -ofrs:tabulated -ofc -ofr:files
```

Useful output flags:

| Flag | Meaning |
|---|---|
| `-ofrs:tabulated -ofc` | CSV-style output. Usually best for parsing. |
| `-ofr:files` | File list report. |
| `-ofr:contents` | Content-hit report. |
| `-ofr:keywords` / `-ofr:file-keywords` | Keyword totals / counts per file. Inspect the report's actual columns. |
| `-ofr:errors` | Errors report; useful for investigating search failures. |
| `-oc` | Include matched content lines. |
| `-ol N` | Max matching lines reported per file, not a search/file-count limit. |
| `-os` | Request surrounding lines; depends on context settings and report format. Verify the output includes them. |
| `-ofx` | XML output. Locally confirmed; console text surrounds the XML document. |
| `-ofb` / `-ofbs` | Tab / spreadsheet-style tab output. `-ofc` is CSV regardless of report style. |
| `-ofh` | HTML output. |
| `-oft` | Plain text output (default). |
| `-oe8` / `-oe8nb` | UTF-8 output with / without BOM, useful for requested exports. |
| `-o "out.csv"` | Write file; do not use unless user asks to save/export. |
| `-oa` | Append to the requested output file. |

Use file reports for discovery and content reports for evidence. Reported hit counts may include filename matches and may depend on hit-count settings; they are not automatically document/body-occurrence counts.

### Parse File-List CSV

Console output includes a banner, criteria/statistics, the CSV table, and a `Finished ...` footer. CSV quotes names containing commas; never use `-split ','`. This example is for the locally observed English file-list report, not multiline contents CSV:

```powershell
# $argsList must select -ofrs:tabulated -ofc -ofr:files.
$raw = @(& $flpsearch @argsList)
$header = $raw | Select-String -Pattern '^Name,Location,' | Select-Object -First 1
if (-not $header) {
  throw 'File-list CSV header missing; inspect output for errors, localization, or changed columns.'
}
$csvLines = for ($i = $header.LineNumber - 1; $i -lt $raw.Count; $i++) {
  if ($raw[$i] -match '^Finished [^,]*$') { break }
  if (-not [string]::IsNullOrWhiteSpace($raw[$i])) { $raw[$i] }
}
$files = @($csvLines | ConvertFrom-Csv)

# Filename-only PDF results; state the displayed count if truncated.
$files | Where-Object { $_.Name -like '*.pdf' } |
  Select-Object -First 50 -ExpandProperty Name

# Or full paths, preserving files with identical names in different folders.
$files | Select-Object -First 50 | ForEach-Object {
  [System.IO.Path]::Combine($_.Location, $_.Name)
}
```

Inspect the search statistics separately before treating an empty table as no matches. The local CLI returned exit code 0 and an empty errors report for a nonexistent folder; validate the location and searched-item count. A missing header or unreadable location is not a successful zero-result search.

For XML, extract the complete XML document from the console wrapper and parse its `rslt` namespace. For specialized exports, `-ofxslt` accepts a transform; the installed `Sample Transforms` folder includes `fullname_only.xsl`, `hits_only.xsl`, and `unique_hits_only.xsl`. Use these only when that output is requested, and inspect a sample before relying on its format.

## Indexed Search

```powershell
flpidx -list
flpsearch -idxname "New Group" -c "deepshield" -ofrs:tabulated -ofc -ofr:files
flpsearch -idxpath "D:\Indexes\Files" -c "pump"
```

Index names are case sensitive; copy them from `flpidx -list`. With `-idxname` or `-idxpath`, only `-c` further restricts the index search. `-d`, `-f`, dates, and attributes are ignored.

Put restrictions inside `-c`:

```powershell
flpsearch -idxname "Files" -c 'pump lookin:"C:\Docs" ext:pdf;docx' -ofrs:tabulated -ofc -ofr:files
```

| Index prefix | Example inside `-c` |
|---|---|
| `name:` | `name:report` |
| `lookin:` | `lookin:"C:\Docs"` |
| `ext:` | `ext:pdf;docx` |
| `moddt:` | `moddt:"> 1 Sep 2026"` |
| `createdt:` | `createdt:"> 1 Jan 2026" createdt:"< 1 Sep 2026"` |
| `size:` | `size:"> 100KB"` |

Index matching differs from direct matching: `fine` matches word starts; `*fine` allows mid-word matches; `"fine"` matches the whole word; `"fine day"` matches a phrase. Unprefixed terms search names and indexed contents. Confirm returned paths satisfy the requested folder boundary, especially for similarly named folders.

An index may omit common words, punctuation-heavy tokens, unsupported content, or recent changes. If this prevents answering the request, scan the requested folder directly with `-d` and no index flags; ask for the folder if unknown. For index-only requests, report the coverage limitation. Do not silently rebuild or update an index, or claim that no index hits proves absence from current files.

For that fallback, do not copy index prefixes into the direct `-c` text. Map `lookin:` to `-d`, name/extension restrictions to `-f -fed`, and modified-date bounds to `-ma`/`-mb`; preserve other restrictions by checking returned file metadata. Select `-cee` for literal text or `-ceb` with explicit file/line scope for Boolean text.

## Additional Direct-Search Examples

```powershell
flpsearch -d "C:\Logs" -f "*.log" -fed -c "ERROR|WARN" -cex -rep -s
flpsearch -d "C:\Data" -f "*.xlsx" -fed -ma "today -1 week" -mb "now" -s -ofrs:tabulated -ofc -ofr:files
```

## Saved Searches And Document Processing

Reuse an existing `.srf` criteria file when supplied. `-po` makes the explicit CLI arguments override saved criteria:

```powershell
flpsearch "C:\Searches\Reports.srf" -po -d "C:\Docs" -c "pump" -cee -s -ofrs:tabulated -ofc -ofr:files
```

Inspect the loaded criteria for unexpected scope or filters. `.srf` stores criteria; `.flsx` stores a session including results/history. `-pc` also replaces the current configuration with that stored in the criteria file, so do not add it merely to load a search. Use it only when restoring that configuration is part of the request.

Before searches involving the formats below, verify their processing settings from the current configuration or a known-content probe. Do not assume a format is enabled because the executable is installed. When expected content is missing, check these settings rather than guessing undocumented flags:

- **Office/PDF:** Enhanced file searching and document readers must be enabled. Text Search searches extracted text; Deep Search also tries raw data when extracted text does not match. A raw-data hit can be metadata rather than visible body text.
- **Archives:** Activated formats are traversed as virtual folders, e.g. `archive.zip\folder\report.txt`. Preserve the container/member path in results; it is not necessarily a standalone disk file.
- **Email:** Outlook/Thunderbird searching handles PST, MSG, and MBOX; attachment searching is a separate option. Verify it when the request includes attachments.
- **Scans/images:** OCR must be enabled with suitable formats/languages. OCR text caching can accelerate repeat searches; existing text PDFs can skip OCR. Do not claim an image-only file was searched successfully just because the file was enumerated.
- **Coverage:** Persistent location filters, binary exclusions, reader failures, and character processing can change results. Inspect errors/settings when the observed results conflict with known content. Do not silently alter persistent configuration.

If required processing is disabled, report the affected formats as unsearched. If the user has authorized enabling it, enable the relevant option and rerun a known-content probe before repeating the requested search; otherwise explain the needed setting. For direct searches: enable ZIP in **Compressed Files**; enable **Options → OCR Images**, then choose formats/language under **OCR...**. Verify that `flpsearch -d` returns the expected body text. These settings do not create an index; existing indexes have separate processing settings. Do not repeat the same disabled search and report its empty output as no matches.

## Index Maintenance

Read carefully before destructive operations. Use `flpidx.exe` for console maintenance, or `IndexManager.exe -exec` to avoid a console popup.

```powershell
flpidx -list
flpidx -create -name "Docs" -path "C:\Indexes\Docs" -d "C:\Docs" -f "*.pdf;*.docx;*.txt" -i
flpidx -name "Docs" -update
flpidx -path "D:\FLPIndex\Docs" -recreate
flpidx -name "Docs" -remove
flpidx -path "D:\FLPIndex\Docs" -remove -delete
IndexManager -exec -name "Docs" -update
```

Only create, update, recreate, remove, or delete indexes when the user requests the maintenance operation. Ordinary searches do not require index creation. For creation, `-i` starts indexing immediately. `-remove` drops the configured reference; adding `-delete` also deletes stored index files. Confirm the intended index name/path from the list before maintenance.

Flags are executable-specific: `flpsearch -cf` means Boolean matching across a file, while `flpidx -cf` enables case-sensitive index searching. Do not copy search flags into index maintenance commands.

Sources:
- https://help.mythicsoft.com/filelocatorpro/en/commandline.htm
- https://help.mythicsoft.com/filelocatorpro/en/index-interface.htm
- https://help.mythicsoft.com/filelocatorpro/en/boolean_expressions.htm
- https://help.mythicsoft.com/filelocatorpro/en/look_in.htm
- https://help.mythicsoft.com/filelocatorpro/en/character_processing_settings.htm
- https://help.mythicsoft.com/filelocatorpro/en/reports.htm
- https://help.mythicsoft.com/filelocatorpro/en/save_results.htm
- https://help.mythicsoft.com/filelocatorpro/en/sessions_and_workspaces.htm
- https://help.mythicsoft.com/filelocatorpro/en/options_advanced.htm
- https://help.mythicsoft.com/filelocatorpro/en/document_search_settings.htm
- https://help.mythicsoft.com/filelocatorpro/en/extension_tab.htm
- https://help.mythicsoft.com/filelocatorpro/en/ocrsettings.htm
