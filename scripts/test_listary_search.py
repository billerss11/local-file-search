import unittest
import io
import json
from unittest.mock import patch

import listary_search as search


def page(offset, count, total):
    return {'query': 'test', 'total': total, 'offset': offset, 'count': count,
            'results': [{'path': f'J:\\test\\井筒-{i}.txt'} for i in range(offset, offset + count)]}


class PagingTests(unittest.TestCase):
    def test_iterator_crosses_100_without_skips(self):
        def reply(query, *, offset, limit, **kwargs):
            return page(offset, min(limit, 238-offset), 238)
        with patch.object(search, 'request_page', side_effect=reply) as request:
            rows = list(search.iter_results('test'))
        self.assertEqual(len(rows), 238)
        self.assertEqual(len({r['path'] for r in rows}), 238)
        self.assertEqual([c.kwargs['offset'] for c in request.call_args_list], [0, 100, 200])

    def test_preview_continues_at_first_omitted_path(self):
        data = page(17, 100, 238)
        result = search.preview(data, max_chars=1000)
        self.assertTrue(result['output_limited'])
        self.assertLess(result['shown'], 100)
        self.assertEqual(result['next_offset'], 17 + result['shown'])
        self.assertEqual(result['results'], data['results'][:result['shown']])
        self.assertLessEqual(len(search.encode(result)), 1000)

    def test_count_change_and_duplicate_fail(self):
        for second in [page(100, 100, 239), page(0, 100, 238)]:
            with self.subTest(second=second['total']):
                with patch.object(search, 'request_page', side_effect=[page(0,100,238),second]):
                    with self.assertRaises(RuntimeError):
                        list(search.iter_results('test'))

    def test_empty_search_and_final_partial_page(self):
        with patch.object(search, 'request_page', return_value=page(0,0,0)):
            self.assertEqual(list(search.iter_results('test')), [])
        result=search.preview(page(200,38,238))
        self.assertFalse(result['has_more'])
        self.assertIsNone(result['next_offset'])

    def test_oversized_path_is_not_clipped(self):
        data=page(0,1,1)
        data['results'][0]['path']='J:\\'+'a'*2000
        with self.assertRaises(RuntimeError):
            search.preview(data,max_chars=1000)

    def test_malformed_api_responses_fail_explicitly(self):
        bad_row=page(0,1,1)
        bad_row['results']=[None]
        for envelope in [[], {'ok':True,'data':None}, {'ok':True,'data':bad_row}]:
            with self.subTest(envelope=envelope):
                with patch.object(search.urllib.request,'build_opener') as build:
                    build.return_value.open.return_value=io.BytesIO(json.dumps(envelope).encode())
                    with self.assertRaises(RuntimeError):
                        search.request_page('test')


if __name__ == '__main__':
    unittest.main()
