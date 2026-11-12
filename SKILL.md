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

### Execution Environment

On Windows, launch the search tools outside the Codex sandbox from the first attempt. This applies to Everything `es.exe`, normal `Everything.exe -startup` recovery, FileLocator `flpsearch.exe`, read-only `flpidx.exe -list`, and their CLI/API/IPC clients. Filesystem existence checks and reading skill documentation can remain sandboxed. On another computer, discover its executable paths instead of assuming the installation paths below.

- With `exec_command`, set `sandbox_permissions: "require_escalated"` on the tool-launch call. Use the execution interface's approval mechanism; this skill does not grant permissions or require administrator/UAC elevation. If outside execution is forbidden or denied, report that restriction and stop the dependent search.
- Launch the whole FileLocator Python preview command outside the sandbox so its `flpsearch.exe` child inherits that environment. Starting Python inside the sandbox and spawning a child does not move the child outside it.
- Prefer a single invocation with literal executable/helper paths when using command allow rules. Variable assignments, pipelines, compound scripts, and shell wrappers may prevent a narrow rule from matching; still request the approved outside execution mode. Do not allow a general PowerShell shell or Python interpreter merely to run this skill.
- The generated persistent FileLocator rule matches only `python.exe -B <preview> --executable <installed flpsearch.exe> -- <search arguments>`. Keep that order for ordinary previews. Additional helper options, raw CLI diagnostics, index listing, and app startup still use the approved outside execution mode and may need their own approval.
- If a tool was accidentally launched inside the sandbox and failed with DLL relocation, access, or IPC errors, correct the execution mode and retry once before declaring it unavailable. Do not replace a CLI/API search with Computer Use unless the user explicitly requests UI operation.

Codex command rules can persist approval for matching commands, but active host or managed policies may still restrict execution. Do not change global sandbox settings, services, or rules as part of an ordinary search. Downloads, setup/configuration changes, and index maintenance keep their existing authorization requirements.

When the user requests setup on another computer or persistent search approvals, read [execution-rules.md](references/execution-rules.md). The included generator prints rules using that computer's paths and installs them only with `--install` after authorization.

Use PowerShell, `&` with executable paths, and argument arrays for paths/queries containing spaces or quotes. Avoid `cmd /c`. Quote shell metacharacters (`;`, `|`, `&`, `>`, `<`); retain literal double quotes inside single-quoted PowerShell strings.

```powershell
$ES = 'J:\Program Files\Everything\cli\ES-1.1.0.30.x64\es.exe'
$flpDir = 'J:\Program Files\Mythicsoft\FileLocator Pro'
$flpsearch = Join-Path $flpDir 'flpsearch.exe'
```

Check the relevant executable before use. Distinguish a missing file from failure to start an existing program. If missing, follow **Setup And Recovery** in the appropriate reference below; do not start broad binary scans. Downloads, service/configuration/profile changes, and index maintenance require the user's request. Starting the normal Everything app after exit code 8 is the documented exception.

### File And Path Search

```powershell
& $ES -n 10 -path 'D:\Docs' report 'ext:pdf;docx'
```

`-path` includes descendants; `-parent` searches only the immediate folder. Default to `-n 10`; if the cap is reached, say more files may exist or obtain the count using **Safe Recipes**. Use FileLocator for contents, not Everything `content:`. Local ES 1.1.0.30 has no `-json`/`-export-json`.

In the [Everything reference](references/voidtools-everything-cli-quick-reference.md), follow **Setup And Recovery** if the executable is missing or returns exit code 8. Before adding query operators, read **Search Syntax**; before sorting/counting/paging, read **Safe Recipes**; before parsing/exporting, read **Return Model**; before GUI actions, read **Everything.exe**.

### File Content Search

Use [scripts/filelocator_preview.py](scripts/filelocator_preview.py) for ordinary searches. It streams results without saving files and prints a bounded JSON preview: **10 files, 3 matching lines per file, 12,000 total characters** by default. It continues reading to completion while discarding omitted results, preserving search statistics and errors. Do not print raw unbounded CLI output or capture the entire report in a variable first.

Direct search (no index; use the actual installed skill location):

```powershell
$python = 'J:\Pythonenvs\codex_env\python.exe'
$preview = 'C:\Users\17999\.codex\skills\local-file-search\scripts\filelocator_preview.py'
$argsList = @('-d', 'C:\Docs', '-f', '*.pdf;*.docx', '-fed', '-c', 'service unit', '-cee', '-s')
& $python -B $preview --executable $flpsearch -- @argsList
```

Indexed search:

```powershell
& $python -B $preview --executable $flpsearch -- -idxname 'Index Name' -c 'pump lookin:"C:\Docs" ext:pdf;docx'
```

- Direct search includes subfolders with `-s` by default; use `-sn` when excluded. Set query modes explicitly: `-cee` literal, `-ceb` Boolean, `-cex` regex; `-fed` for wildcard filenames. Boolean operators are uppercase; `-cf` matches across the file, `-cfn` on one line.
- **Literal semicolon in a path:** pass inner quotes: `-d '"C:\Docs\2026;final"'`. Ordinary shell quoting alone is insufficient. For genuine multiple locations, semicolons remain outside each quoted path.
- **Index queries:** before constructing one, read **Indexed Search**. Put restrictions inside `-c`; `-d`, `-f`, dates, and attribute flags are ignored. Copy the case-sensitive index name from the index list.
- **Preview options:** read **Bounded Preview** in the FileLocator reference for file-list mode, larger previews, and result interpretation. The helper needs only Python's standard library; prefer `codex_env`. Pass search arguments after `--`; the helper supplies output flags itself.
- **Content evidence:** read **Verify Body Text** before citing body text. Use the returned positive-numbered matching lines directly when sufficient; do not reopen/re-extract a document just to read the same passage. File-list hits may come from names/paths. If echoed criteria lost quotes, correct the quoting and verify the phrase directly in candidate files.

The named sections are in the [FileLocator reference](references/filelocator-cli-reference.md). Before advanced queries/exclusions, read **Direct Query And Location Patterns** and **Search Flags**; before changing report formats, read **Output**; before saved-search reuse or ZIP/Office/PDF/email/OCR searches, read **Saved Searches And Document Processing**; before index changes, read **Index Maintenance**. Use the reference for unknown flags, not `flpsearch -?`. Load only sections triggered by the task, not both references routinely.

## Verify And Recover

After each search:
1. Check exit status and reported completion/errors. If the execution tool returns a running session, continue collecting its output; a wait interval ending or no early output does not prove the search tool is unavailable. The FileLocator preview prints its JSON after the search finishes. Label interrupted or partially failed results as incomplete. For FileLocator, exit code 0 alone is insufficient; use `-ofr:errors` when failures need diagnosis.
2. Check echoed scope/filters and searched-item counts when reported. If zero files were searched, verify location and filters; report "no eligible files searched" when valid, not absence of text from unsearched files.
3. Check returned paths against the requested scope. For content claims, verify actual matching body lines; label unverifiable hits as candidates.
4. If an index misses known/current content or is stale, follow the **Indexed Search** fallback to search the requested folder directly, preserving text intent and filters. If no folder is known, ask for it. For index-only requests, report the limitation instead. Do not update/rebuild unless requested.

## Return Results

State the search mode and index/folder searched. Return useful paths with matching passages when searching contents. Distinguish a limited preview from an incomplete search; report omissions and never treat the first files as relevance-ranked or exhaustive. `-ol N` limits matching lines reported **per file**, not files searched or total results.

Answer from the returned passages when sufficient. For missing context, narrow the search to selected files and adjust the preview limits, or use a document reader when full text, tables, or layout are required. Omitted results are not retained after the helper exits, so further retrieval requires another search. Do not silently stop at the preview when the user requested exhaustive results.

Create no temporary result files, result caches, or automatic exports. Save/export results only when the user requests it. The limits apply before output reaches the agent, not only to the final chat reply.

Source repository: https://github.com/billerss11/local-file-search
