# Listary local HTTP search

Use Listary first for filename/path searches. This interface searches indexed names and paths, not document body text. The local installation uses `C:\Program Files\Listary\Listary.exe` and the default endpoint `http://127.0.0.1:38431/api/v1/search`. Discover the configured port on another installation instead of assuming it.

## Request and results

Send `POST` with UTF-8 JSON and `Content-Type: application/json`. Bypass system HTTP proxies for this loopback endpoint. The bundled helper does both.

| Field | Meaning |
| --- | --- |
| `query` | Search expression, required |
| `limit` | Page size; default 10, maximum 100 |
| `offset` | Zero-based result offset; default 0 |
| `search_in` | Optional array of absolute directories, including descendants |
| `types` | Optional array containing `file`, `folder`, or both |
| `extensions` | Optional array such as `pdf`, `docx`, or `.xlsx` |

Check `ok` before using `data`. Successful `data` contains `total`, `offset`, `limit`, `count`, and `results`. Each result supplies `path`, `name`, `type`, `size_bytes`, `modified_at`, and `score`. Preserve paths exactly. Treat score as an ordering value, not a relevance probability. Folder sizes can be null.

The helper CLI returns `total_matches`, `shown`, `has_more`, `next_offset`, `output_limited`, and `results`. Its default output budget is 12,000 characters. If that budget omits results, `next_offset` points to the first omitted result, so a continuation does not skip it. Increase `--max-chars` only when the requested output needs it. Errors return `ok: false` and exit code 1, not an empty successful search.

```powershell
& 'J:\Pythonenvs\codex_env\python.exe' -B 'C:\Users\17999\.codex\skills\local-file-search\scripts\listary_search.py' --query 'scssv' --scope 'J:\CENERTECH CX' --extension pdf --type file --limit 10
```

Repeat `--scope`, `--extension`, or `--type` for multiple values. Use `--port` only for a known configured port. The client always connects to `127.0.0.1`; it does not configure or start Listary. Check that an explicitly requested directory exists before interpreting an empty scoped search.

## Search expressions

Supported and locally tested patterns include a name substring (`scssv`), a quoted phrase (`"deep shield"`), Chinese text (`井筒完整性`), extension filtering (`ext:xlsx`), and exclusion (`thunder -storm`). Prefer structured scope/type/extension fields where possible.

`xlsx` also matches names such as `xlsx guide.txt` and `report.xlsx.bak`; use `ext:xlsx` or `--extension xlsx --type file` for spreadsheet files. `rev` also matches `preview` and `revenue`. Do not assume the API has the launcher's fuzzy abbreviation behavior. Translate syntax when falling back to Everything: for example, Listary's `-storm` becomes Everything's `!storm`.

## Pagination and completeness

The 100-result limit applies to one request. `total` can exceed 100. For example, 238 matches require pages at offsets 0, 100, and 200 with `limit=100`, provided the server returns full pages. Advance by the actual returned count, not an assumed page length.

For a few more candidates, call the CLI again with its reported `next_offset` and unchanged query/filters. `has_more: false` means the end was reached from that offset; it does not prove earlier pages were inspected. State preview size and total in the answer when results are omitted.

For an exhaustive search, use the helper's `iter_results` in a single Python process. It pages automatically, yields each result, and stores only seen-path keys for duplicate detection. It checks that the total stays consistent and stops with an error on duplicate paths or invalid pagination. A failure after some yields means partial results, not a complete search.

Example aggregate, run outside the sandbox; this writes no result files:

```python
import sys
sys.path.insert(0, r'C:\Users\17999\.codex\skills\local-file-search\scripts')
from listary_search import iter_results

count = sum(1 for _ in iter_results('deepshield', types=['file']))
print({'enumerated_files': count})
```

Consume the iterator locally for the actual task: inspect candidates, calculate an aggregate, or stream to a file when the user requested an export. Do not dump thousands of paths into agent context. Do not call a small preview exhaustive merely because the total is known. For a count alone, one API page already supplies `total`; enumerating every page is unnecessary.

Listary does not expose a snapshot token in this API. Changes to files or ranking during pagination may shift results. If counts change, duplicate paths appear, a page is empty before the reported end, or a request fails, label the retrieval incomplete. Retry once when stable or use a scoped alternative; do not loop indefinitely. Consistent pagination proves traversal of the reported index results, not filesystem completeness.

For a very large inventory/export, hundreds of API requests may be less efficient than Everything's larger batches. Use Everything when that tradeoff matters, preserving the requested filters and checking coverage. Neither tool's index is a guaranteed superset of the other's. A query with many matches is not by itself a reason to discard Listary's results or stop at 100.

## Availability and fallback

Run the client outside the sandbox from the first attempt, as specified in `SKILL.md`. A sandbox/proxy failure does not prove Listary is unavailable. Connection refusal at the actual configured port, an API error, or a timeout is a reason to report the failed attempt and fall back to Everything. Do not repeatedly retry an unchanged failure.

The tray app can run while its HTTP API is disabled. Do not enable the API, alter indexed locations, restart services, or rebuild indexes during an ordinary search without authorization. Respect existing authorization when the user requested setup or repair.

Use Everything for explicit regex or sorting requirements that this API does not expose. Check relevant output paths if either index misses a known file. Listary JSON avoids the ANSI character substitutions observed in redirected ES output; prefer its original Unicode path when the CLI output is unusable.

The field definitions come from the API documentation bundled in Listary 7.1.0.47. Pagination, Unicode output, and filters were verified against the installed API. Recheck the actual interface if an upgrade changes behavior.
