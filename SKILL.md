---
name: local-file-search
description: Find local Windows files or folders by filename or path with Everything CLI, and search text inside local documents with FileLocator Pro using indexes or direct folder searches. Do not use for source-code searches within the active workspace; use rg instead.
---

# Local File Search

Follow the user's requested search mode. Otherwise prefer an appropriate existing index, or search the requested folder directly when no suitable index is available. Keep output capped and return only useful paths. Do not save/export results unless the user asks.

Detailed references:
- Everything CLI: `references/voidtools-everything-cli-quick-reference.md`
- FileLocator Pro CLI: `references/filelocator-cli-reference.md` — read for query syntax, index filters, CSV parsing, exclusions, saved searches, or document/OCR troubleshooting.

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

## File Content Search

Use FileLocator to search text inside local documents. Prefer `flpsearch.exe` for automation. For source-code searches within the active workspace, use `rg` instead.

Choose the search mode before running the command:

- **Indexed search:** Use `-idxname` or `-idxpath` when the user requests an existing index, or when a known suitable index covers the requested files. Use `flpidx -list` if you need to discover existing indexes.
- **Direct search without an index:** If the user asks for a fresh scan, direct folder search, or search without an index, use `-d "C:\Requested\Folder"` and omit both `-idxname` and `-idxpath`. Run this mode even if an index exists. It reads the files directly; no index creation, update, or listing is required.
- **No suitable index:** Search the requested folder directly. If no folder is known, ask for the search location instead of scanning entire drives. Do not create an index just to perform a search.
- For direct searches, set `-s` to include subfolders or `-sn` to search only the specified folder, according to the requested scope. Include subfolders by default unless the user says otherwise.
- Check that explicit local files/folders exist and are accessible before searching. Indexes can be stale or omit terms; use a scoped direct search when current contents or literal punctuation-sensitive text matters, unless the user explicitly limits the search to an index.

When returning results, briefly state whether the search used an index or scanned a folder directly, and identify the index or folder searched.

Indexed examples:

```powershell
flpidx -list
flpsearch -idxname "AU Oil and gas Nopims" -c "Nopims" -oft -ofr:files
flpsearch -idxname "AU Oil and gas Nopims" -c "pump OR casing" -ofrs:tabulated -ofc -ofr:files
```

Direct folder search (no index required):

```powershell
flpsearch -d "C:\Docs" -f "*.pdf;*.docx" -fed -c "casing" -cee -s -oc -ol 5 -ofrs:tabulated -ofc -ofr:contents
```

For FileLocator queries with spaces, use an argument array:

```powershell
$flpsearch = "J:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe"
$argsList = @("-idxname", "New Group", "-c", "service unit", "-ofrs:tabulated", "-ofc", "-ofr:files")
& $flpsearch @argsList
```

Rules:
- Set expression modes explicitly: `-cee` for literal text, `-ceb` for Boolean, `-cex` for regex, and `-fed` for wildcard file patterns. With Boolean queries, use `-cf` for terms anywhere in a file or `-cfn` for terms on the same line. Use uppercase `AND`, `OR`, and `NOT`.
- For machine-readable output, prefer `-ofrs:tabulated -ofc -ofr:files`. It produces CSV, not tabs. Strip the preamble/footer and use `ConvertFrom-Csv`; never split rows on commas. Use the tested parsing example in the reference. For full paths, combine `Location` and `Name`.
- Inspect the actual header when changing report modes; columns and language can depend on settings.
- Use `-oc -ofr:contents` when matching text is needed. A file-list hit is not proof of body text: indexed searches include names, and direct searches can include names/paths through Character Processing settings. Verify matching body lines before citing content; the reference shows a tested `LINES:1+` Boolean query to exclude the synthetic filename line.
- `-ol N` limits reported matching lines **per file**, not files searched or total results. Scope the search first and cap displayed file rows separately; label any truncation.
- With `-idxname` / `-idxpath`, only `-c` further restricts search.
- Put index restrictions inside `-c`, e.g. `pump lookin:"C:\Docs" ext:pdf;docx`. Direct-search flags such as `-d`, `-f`, and date filters are ignored. The reference covers name, date, and size prefixes.
- If a phrase query behaves unexpectedly, check the echoed criteria for lost quotes, then verify candidate files directly. Missing body lines must not be replaced with inferred document contents.
- Before reporting no matches, check the searched-item count and completion/error information. A missing location can return zero items with exit code 0. For document/archive/scanned-file misses, check the relevant reader, archive, and OCR settings described in the reference.
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
