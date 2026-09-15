"""Print a bounded FileLocator preview; never write search results to disk."""

import argparse
import csv
import json
import ntpath
import re
import subprocess
import sys
import threading


DEFAULT_EXE = r"J:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe"
CRITERIA = {"File name", "Containing text", "Look in"}
STATISTICS = {"Found", "Text", "Searched", "Checked", "Status", "Completed", "Errors"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def clipped(text, limit):
    prefix = text[:limit]
    while len(json.dumps(prefix, ensure_ascii=False)) > limit:
        prefix = prefix[:-1]
    return prefix if prefix == text else prefix + " [truncated]"


class Preview:
    def __init__(self, report="contents", max_files=10, lines_per_file=3, max_chars=12000):
        self.report = report
        self.max_files = max_files
        self.lines_per_file = lines_per_file
        self.max_chars = max_chars
        self.files = {}
        self.header_seen = False
        self.finished = False
        self.data = {
            "complete": False,
            "exit_code": None,
            "report": report,
            "criteria": {},
            "statistics": {},
            "files": [],
            "preview_limited": False,
            "notes": [
                f"First returned files, not relevance-ranked; at most {max_files} files.",
                f"At most {lines_per_file} matching lines per file; not full document text."
                if report == "contents" else "File-list hits are candidates, not body-text evidence.",
            ],
            "diagnostics": [],
        }

    def diagnostic(self, message):
        if len(self.data["diagnostics"]) < 3:
            self.data["diagnostics"].append(clipped(message, 200))

    def fits(self):
        # Leave room for completion, statistics, diagnostics, and notices.
        return len(encode(self.data["files"])) <= self.max_chars - 2500

    def add_row(self, row):
        path = ntpath.join(row["Location"], row["Name"])
        key = ntpath.normcase(path)
        if key not in self.files:
            if len(self.files) >= self.max_files:
                self.data["preview_limited"] = True
                return
            item = {"path": path}
            if self.report == "contents":
                item["matches"] = []
            self.data["files"].append(item)
            if not self.fits():
                self.data["files"].pop()
                self.data["preview_limited"] = True
                return
            self.files[key] = item
        item = self.files[key]
        if self.report == "files":
            return
        if len(item["matches"]) >= self.lines_per_file:
            self.data["preview_limited"] = True
            return
        line = row["Line"].strip()
        if not line.isdecimal() or int(line) == 0:
            # FileLocator can search a synthetic filename/path line.
            return
        match = {"line": int(line), "text": row["Text"]}
        item["matches"].append(match)
        if not self.fits():
            self.data["preview_limited"] = True
            match["text_truncated"] = True
            text = match["text"]
            low, high = 0, min(len(text), self.max_chars)
            while low < high:
                middle = (low + high + 1) // 2
                match["text"] = text[:middle]
                if self.fits():
                    low = middle
                else:
                    high = middle - 1
            match["text"] = text[:low]
            if not low or not self.fits():
                item["matches"].pop()

    def read(self, stream):
        header = None
        # Limit individual CSV fields too; an oversized field is a reported parse
        # failure, never silently accepted as a complete search result.
        csv.field_size_limit(1024 * 1024)
        try:
            for row in csv.reader(stream, strict=True):
                if not row or not any(row):
                    continue
                if header is None and row[:2] == ["Name", "Location"]:
                    required = {"Name", "Location"}
                    if self.report == "contents":
                        required.update({"Line", "Text"})
                    if not required.issubset(row):
                        raise ValueError("Unexpected FileLocator report columns.")
                    header = row
                    self.header_seen = True
                elif header is not None and len(row) == len(header):
                    self.add_row(dict(zip(header, row)))
                elif len(row) == 1 and row[0].startswith("Finished "):
                    self.finished = True
                elif header is None and len(row) >= 2:
                    label = row[0].rstrip(":")
                    value = ",".join(row[1:])
                    if label in CRITERIA:
                        self.data["criteria"][label] = clipped(value, 220)
                    elif label in STATISTICS:
                        self.data["statistics"][label] = clipped(value, 100)
                    elif re.search(r"error|fail|cancel|interrupt", label, re.I):
                        self.diagnostic(",".join(row))
                elif header is not None or re.search(r"error|fail|cancel|interrupt", row[0], re.I):
                    self.diagnostic("Unexpected output: " + ",".join(row))
        except (csv.Error, ValueError) as error:
            self.diagnostic("Cannot parse complete report: " + str(error))
            # Drain the pipe so the child can finish, without collecting output.
            while stream.read(65536):
                pass

    def finish(self, exit_code, stderr=""):
        self.data["exit_code"] = exit_code
        if stderr:
            if len(self.data["diagnostics"]) == 3:
                self.data["diagnostics"].pop()
            self.diagnostic("stderr: " + stderr)
        status = self.data["statistics"].get("Status", "")
        self.data["complete"] = bool(
            exit_code == 0 and self.header_seen and self.finished
            and status.startswith("Completed")
            and not re.search(r"error|fail|cancel|interrupt", status, re.I)
            and not self.data["diagnostics"]
        )
        errors = self.data["statistics"].get("Errors", "0")
        if not re.match(r"^0(?:\D|$)", errors):
            self.data["complete"] = False
        if not self.data["complete"]:
            self.data["notes"].append(
                "Incomplete or unverified search. Check status/errors; do not infer absence from missing results."
            )
        if re.match(r"^0(?:\D|$)", self.data["statistics"].get("Searched", "")):
            self.data["notes"].append("No eligible files searched; this does not establish absence of text.")
        if self.report == "contents":
            self.data["notes"].append(
                "Found may include filename/path hits without body rows. Line numbers are extracted-text positions."
            )
        omission_note = "Some files or text omitted. Narrow the search or increase preview limits."
        if self.data["preview_limited"]:
            self.data["notes"].append(omission_note)
        # Guard the total serialized output, including metadata, not just text.
        while len(encode(self.data)) + 1 > self.max_chars and self.data["files"]:
            self.data["files"].pop()
            self.data["preview_limited"] = True
            if omission_note not in self.data["notes"]:
                self.data["notes"].append(omission_note)
        return encode(self.data)


def run_search(command, preview):
    stderr_parts = []

    def drain_stderr(pipe):
        kept = 0
        while chunk := pipe.read(4096):
            if kept < 600:
                stderr_parts.append(chunk[:600 - kept])
                kept += len(stderr_parts[-1])

    try:
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, text=True, encoding="utf-8-sig",
            errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ) as process:
            reader = threading.Thread(target=drain_stderr, args=(process.stderr,), daemon=True)
            reader.start()
            try:
                preview.read(process.stdout)
                exit_code = process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                preview.diagnostic("Search interrupted.")
                exit_code = 130
            reader.join()
    except OSError as error:
        preview.diagnostic(str(error))
        exit_code = 2
    return preview.finish(exit_code, "".join(stderr_parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", default=DEFAULT_EXE)
    parser.add_argument("--report", choices=("contents", "files"), default="contents")
    parser.add_argument("--max-files", type=int, default=10)
    parser.add_argument("--lines-per-file", type=int, default=3)
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("search_args", nargs=argparse.REMAINDER, help="-- followed by FileLocator search flags (no output flags)")
    args = parser.parse_args()
    if args.max_files < 1 or args.lines_per_file < 1 or args.max_chars < 4096:
        parser.error("Use positive file/line limits and --max-chars of at least 4096.")
    search_args = args.search_args
    if search_args[:1] == ["--"]:
        search_args = search_args[1:]
    if not search_args:
        parser.error("Supply scoped FileLocator search arguments after --.")
    # Output control belongs to this helper. In particular, reject file export.
    value_flags = {"-d", "-f", "-c", "-idxname", "-idxpath", "-ma", "-mb"}
    arguments = iter(search_args)
    for argument in arguments:
        if argument.lower().startswith("-o"):
            parser.error("Omit FileLocator output flags (-o...). Use this helper's preview options instead.")
        if argument.lower() in value_flags:
            next(arguments, None)
    command = [args.executable, *search_args, "-ofrs:tabulated", "-ofc",
               "-ofr:" + args.report, "-oe8nb"]
    if args.report == "contents":
        command.extend(["-oc", "-ol", str(args.lines_per_file)])
    preview = Preview(args.report, args.max_files, args.lines_per_file, args.max_chars)
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    print(run_search(command, preview))
    return 0 if preview.data["complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
