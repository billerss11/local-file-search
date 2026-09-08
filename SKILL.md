---
name: local-file-search
description: Find local Windows files or folders by filename or path with Everything CLI, and search text inside local documents with FileLocator Pro using indexes or direct folder searches. Do not use for source-code searches within the active workspace; use rg instead.
---

# Local File Search

## Choose The Search

- **Names/paths:** Everything `es.exe`. For source code within the active workspace, use `rg` instead.
- **Document contents:** FileLocator `flpsearch.exe`. Honor the user's requested mode.
- **Direct/fresh/no-index request:** Use `-d` and omit `-idxname`/`-idxpath`, even if an index exists. No index creation, update, or listing is needed.
- **Otherwise:** Use a known suitable existing index, or scan the requested folder directly. Discover indexes with `flpidx -list` when needed. Indexes can be stale or omit terms; prefer direct search for current contents or punctuation-sensitive literal text unless the user limits the task to an index.

Before a direct search, run `Test-Path -LiteralPath` on each requested location; report missing/inaccessible locations instead of treating them as zero matches. If scope is unknown, ask for a location rather than scanning entire drives. Do not create an index for an ordinary search.

## Run The Tools

Use PowerShell, `&` with executable paths, and argument arrays for paths/queries containing spaces or quotes. Avoid `cmd /c`. Quote shell metacharacters (`;`, `|`, `&`, `>`, `<`); retain literal double quotes inside single-quoted PowerShell strings.

```powershell
$ES = 'J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe'
$flpDir = 'J:\Program Files\Mythicsoft\FileLocator Pro'
$flpsearch = Join-Path $flpDir 'flpsearch.exe'
```

Check the relevant executable before use. If missing, follow **Setup And Recovery** in the appropriate reference below; do not start broad binary scans. Downloads, service/configuration/profile changes, and index maintenance require the user's request. Starting the normal Everything app after exit code 8 is the documented exception.

### File And Path Search

```powershell
& $ES -n 20 -path 'D:\Docs' report 'ext:pdf;docx'
```

`-path` includes descendants; `-parent` searches only the immediate folder. Always cap normal results with `-n`. Use FileLocator for contents, not Everything `content:`. Local ES 1.1.0.30 has no `-json`/`-export-json`.

In the [Everything reference](references/voidtools-everything-cli-quick-reference.md), follow **Setup And Recovery** if the executable is missing or returns exit code 8. Before adding query operators, read **Search Syntax**; before sorting/counting/paging, read **Safe Recipes**; before parsing/exporting, read **Return Model**; before GUI actions, read **Everything.exe**.

### File Content Search

Direct search (no index):

```powershell
$argsList = @('-d', 'C:\Docs', '-f', '*.pdf;*.docx', '-fed', '-c', 'service unit', '-cee', '-s', '-ofrs:tabulated', '-ofc', '-ofr:files')
& $flpsearch @argsList
```

Indexed search:

```powershell
& $flpsearch -idxname 'Index Name' -c 'pump lookin:"C:\Docs" ext:pdf;docx' -ofrs:tabulated -ofc -ofr:files
```

- Direct search includes subfolders with `-s` by default; use `-sn` when excluded. Set query modes explicitly: `-cee` literal, `-ceb` Boolean, `-cex` regex; `-fed` for wildcard filenames. Boolean operators are uppercase; `-cf` matches across the file, `-cfn` on one line.
- **Literal semicolon in a path:** pass inner quotes: `-d '"C:\Docs\2026;final"'`. Ordinary shell quoting alone is insufficient. For genuine multiple locations, semicolons remain outside each quoted path.
- **Index queries:** before constructing one, read **Indexed Search**. Put restrictions inside `-c`; `-d`, `-f`, dates, and attribute flags are ignored. Copy the case-sensitive index name from the index list.
- **CSV:** before parsing, read and use **Parse File-List CSV**. Select `-ofrs:tabulated -ofc`, inspect the actual header, strip console wrappers, and use `ConvertFrom-Csv`, never comma splitting. Return `Name` alone or combine `Location` and `Name` for full paths.
- **Content evidence:** before citing body text, read and follow **Verify Body Text**; request `-oc -ofr:contents -ol 5`. File-list hits may come from names/paths. If echoed criteria lost quotes, correct the quoting and verify the phrase directly in candidate files.

The named sections are in the [FileLocator reference](references/filelocator-cli-reference.md). Before advanced queries/exclusions, read **Direct Query And Location Patterns** and **Search Flags**; before changing report formats, read **Output**; before saved-search reuse or ZIP/Office/PDF/email/OCR searches, read **Saved Searches And Document Processing**; before index changes, read **Index Maintenance**. Use the reference for unknown flags, not `flpsearch -?`. Load only sections triggered by the task, not both references routinely.

## Verify And Recover

After each search:
1. Check exit status and reported completion/errors. For FileLocator, exit code 0 alone is insufficient. Label interrupted or partially failed results as incomplete; use `-ofr:errors` when failures need diagnosis.
2. Check echoed scope/filters and searched-item counts when reported. If zero files were searched, verify location and filters; report "no eligible files searched" when valid, not absence of text from unsearched files.
3. Check returned paths against the requested scope. For content claims, verify actual matching body lines; label unverifiable hits as candidates.
4. If an index misses known/current content or is stale, follow the **Indexed Search** fallback to search the requested folder directly, preserving text intent and filters. If no folder is known, ask for it. For index-only requests, report the limitation instead. Do not update/rebuild unless requested.

## Return Results

State the search mode and index/folder searched. Return useful paths and requested evidence; cap displayed file rows and label truncation. `-ol N` limits matching lines reported **per file**, not files searched or total results. Save/export results only when requested.

Source repository: https://github.com/billerss11/local-file-search
