"""In-memory regression checks; no fixture files or search result files."""

import csv
import io
import json
import unittest

from filelocator_preview import Preview


def report(rows=(), found=1, searched=1, status="Completed (< 1 sec)", finished=True, contents=True):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerows([
        ["Command Line Search [Version 9.1.3389.1]"],
        ["Search Criteria"], ["Containing text:", 'pump "test", 中文'],
        ["Look in:", "C:\\Docs\\"], ["Search Statistics"],
        ["Found:", f"{found} items"], ["Searched:", f"{searched} items"],
        ["Status:", status],
        ["Name", "Location", "Modified", "Hits"] + (["Line", "Text"] if contents else []),
    ])
    writer.writerows(rows)
    if finished:
        writer.writerow(["Finished 2026/9/15 17:00:00 (1 secs)"])
    stream.seek(0)
    return stream


def body(name="report.txt", line=1, text="pump failed"):
    return [name, "C:\\Docs\\", "2026/9/15", 1, line, text]


class PreviewTests(unittest.TestCase):
    def parse(self, stream, **limits):
        preview = Preview(**limits)
        preview.read(stream)
        output = preview.finish(0)
        self.assertLessEqual(len(output) + 1, preview.max_chars)
        return json.loads(output)

    def test_many_files_and_lines_preserve_final_status(self):
        rows = (body(f"report-{i}.txt", line, "pump failed") for i in range(10000) for line in range(1, 5))
        result = self.parse(report(rows, found=10000, searched=10000))
        self.assertTrue(result["complete"])
        self.assertEqual(result["statistics"]["Found"], "10000 items")
        self.assertEqual(len(result["files"]), 10)
        self.assertTrue(all(len(item["matches"]) == 3 for item in result["files"]))
        self.assertTrue(result["preview_limited"])

    def test_quoted_multiline_unicode_content(self):
        text = '泵出现故障, "pressure test"\nsecond line'
        result = self.parse(report([body("a,b.txt", text=text)]))
        self.assertEqual(result["files"][0]["path"], "C:\\Docs\\a,b.txt")
        self.assertEqual(result["files"][0]["matches"][0]["text"], text)
        self.assertTrue(result["complete"])

    def test_long_line_is_explicitly_shortened(self):
        for limit in (4096, 12000):
            with self.subTest(limit=limit):
                result = self.parse(report([body(text='"\\\t中文' * 20000)]), max_chars=limit)
                self.assertTrue(result["complete"])
                self.assertTrue(result["preview_limited"])
                match = result["files"][0]["matches"][0]
                self.assertTrue(match["text_truncated"])
                self.assertGreater(len(match["text"]), 0)

    def test_failure_and_missing_finish_are_not_success(self):
        for stream in (report(status="Cancelled"), report(finished=False), io.StringIO("Error: failed\n")):
            with self.subTest(stream=stream):
                self.assertFalse(self.parse(stream)["complete"])

    def test_zero_matches_vs_zero_searched(self):
        result = self.parse(report(found=0, searched=10))
        self.assertTrue(result["complete"])
        self.assertEqual(result["files"], [])
        empty_scope = self.parse(report(found=0, searched=0))
        self.assertTrue(any("No eligible files" in note for note in empty_scope["notes"]))

    def test_file_list_and_filename_only_content(self):
        result = self.parse(report([body()[:4]], contents=False), report="files")
        self.assertTrue(result["complete"])
        self.assertNotIn("matches", result["files"][0])
        candidate = self.parse(report([body(line=0, text="pump in filename")]))
        self.assertEqual(candidate["files"][0]["matches"], [])

    def test_oversized_csv_field_reports_failure_and_drains(self):
        stream = report([body(text="x" * (1024 * 1024 + 1))])
        result = self.parse(stream)
        self.assertFalse(result["complete"])
        self.assertTrue(result["diagnostics"])
        self.assertEqual(stream.read(), "")

    def test_final_budget_keeps_omission_notice_and_stderr(self):
        preview = Preview(max_chars=4096)
        preview.read(report([body(text="x" * 10000)]))
        for index in range(4):
            preview.diagnostic(f"Parser problem {index}: " + "x" * 300)
        output = preview.finish(0, "File access failed")
        result = json.loads(output)
        self.assertLessEqual(len(output) + 1, 4096)
        self.assertTrue(result["preview_limited"])
        self.assertTrue(any("omitted" in note for note in result["notes"]))
        self.assertTrue(any("File access failed" in note for note in result["diagnostics"]))
        self.assertFalse(result["complete"])


if __name__ == "__main__":
    unittest.main()
