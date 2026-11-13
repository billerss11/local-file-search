"""Search Listary's local API; bounded CLI pages and a streaming page iterator."""

import argparse
import json
import ntpath
import sys
import urllib.request


def request_page(query, *, limit=10, offset=0, search_in=None, extensions=None,
                 types=None, port=38431, timeout=10):
    if not query.strip() or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('Use a nonempty query, limit 1..100, and offset >= 0.')
    if not 1 <= port <= 65535 or timeout <= 0:
        raise ValueError('Invalid port or timeout.')
    payload = {'query': query, 'limit': limit, 'offset': offset}
    for key, value in [('search_in', search_in), ('extensions', extensions), ('types', types)]:
        if value:
            payload[key] = value
    # The endpoint is local. Do not send it through system HTTP proxies.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/v1/search',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json; charset=utf-8'},
    )
    with opener.open(request, timeout=timeout) as response:
        envelope = json.load(response)
    if not isinstance(envelope, dict):
        raise RuntimeError('Listary returned an invalid response envelope.')
    if envelope.get('ok') is not True:
        raise RuntimeError(f"Listary error: {envelope.get('error')}: {envelope.get('message')}")
    data = envelope['data']
    if not isinstance(data, dict):
        raise RuntimeError('Listary returned invalid result metadata.')
    rows, total = data['results'], data['total']
    if (not isinstance(total, int) or total < 0 or not isinstance(rows, list)
            or data['offset'] != offset or data['count'] != len(rows)
            or len(rows) > limit or (rows and offset + len(rows) > total)):
        raise RuntimeError('Listary returned inconsistent pagination metadata.')
    if not rows and offset < total:
        raise RuntimeError('Listary returned an empty page before the reported end.')
    keys = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('path'), str) or not row['path']:
            raise RuntimeError('Listary returned a result without a usable path.')
        keys.append(ntpath.normcase(ntpath.normpath(row['path'])))
    if len(set(keys)) != len(keys):
        raise RuntimeError('Listary returned duplicate paths within a page.')
    return data


def iter_results(query, *, page_size=100, **filters):
    """Yield all indexed matches, failing on detected page drift; write no files."""
    offset, expected_total = 0, None
    seen = set()
    while True:
        page = request_page(query, limit=page_size, offset=offset, **filters)
        total = page['total']
        if expected_total is not None and total != expected_total:
            raise RuntimeError('Result count changed while paging; search is incomplete. Retry when stable.')
        expected_total = total
        for row in page['results']:
            key = ntpath.normcase(ntpath.normpath(row['path']))
            if key in seen:
                raise RuntimeError('Duplicate path across pages; search is incomplete. Retry when stable.')
            seen.add(key)
            yield row
        offset += len(page['results'])
        if offset >= total:
            return


def encode(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def preview(page, max_chars=12000, filters=None):
    """Never clip paths; continue at the first result omitted from stdout."""
    rows = list(page['results'])
    while True:
        next_offset = page['offset'] + len(rows)
        result = {
            'ok': True, 'query': page['query'], 'total_matches': page['total'],
            'offset': page['offset'], 'shown': len(rows),
            'has_more': next_offset < page['total'],
            'next_offset': next_offset if next_offset < page['total'] else None,
            'output_limited': len(rows) < len(page['results']),
            'filters': filters or {}, 'results': rows,
        }
        if len(encode(result)) <= max_chars:
            if page['results'] and not rows:
                raise RuntimeError('First result exceeds output budget; increase --max-chars. No path was truncated.')
            return result
        if not rows:
            raise RuntimeError('Query metadata exceeds output budget; increase --max-chars.')
        rows.pop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=10, help='Results per request: 1..100 (default 10).')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--scope', action='append', dest='search_in')
    parser.add_argument('--extension', action='append', dest='extensions')
    parser.add_argument('--type', action='append', choices=['file', 'folder'], dest='types')
    parser.add_argument('--port', type=int, default=38431)
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--max-chars', type=int, default=12000)
    args = vars(parser.parse_args())
    max_chars = args.pop('max_chars')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        if max_chars < 1000:
            raise ValueError('--max-chars must be at least 1000.')
        filters = {k: args[k] for k in ('search_in', 'extensions', 'types') if args[k]}
        result = preview(request_page(**args), max_chars, filters)
        print(encode(result))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        print(encode({'ok': False, 'error': str(error)[:1500]}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
