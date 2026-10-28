#!/usr/bin/env python3
"""Turn one downloaded course file into Markdown for the tutor's source cache.

Usage: extract.py <input> <output.md>

Standard library only (Python 3.7+); PDFs go through poppler's pdftotext.
Exit 2: no extractor exists for the file's type.
Exit 3: the file could not be read as its type (often a viewer, login or
redirect page saved under a binary name).
"""
import html.parser
import json
import os
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

CODE_EXTS = {
    ".py": "python", ".java": "java", ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp",
    ".go": "go", ".rs": "rust", ".js": "javascript", ".ts": "typescript", ".sh": "bash",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".sql": "sql",
}
PLAIN_EXTS = {".md", ".txt", ".csv", ".tsv", ".rst"}


def pdf(path):
    out = subprocess.run(["pdftotext", "-layout", path, "-"], stdout=subprocess.PIPE, check=True)
    pages = out.stdout.decode("utf-8", "replace").split("\f")
    return "\n".join("## Page {}\n\n{}".format(i, p.strip()) for i, p in enumerate(pages, 1) if p.strip())


def numbered(names, pattern):
    hits = [(int(m.group(1)), n) for n in names for m in [re.fullmatch(pattern, n)] if m]
    return [n for _, n in sorted(hits)]


def paragraphs(xml_bytes, para_tag, text_tag):
    root = ET.fromstring(xml_bytes)
    lines = []
    for p in root.iter(para_tag):
        text = "".join(t.text or "" for t in p.iter(text_tag)).strip()
        if text:
            lines.append(text)
    return lines


def pptx(path):
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        notes = {re.search(r"(\d+)", n).group(1): n for n in numbered(names, r"ppt/notesSlides/notesSlide(\d+)\.xml")}
        parts = []
        for n in numbered(names, r"ppt/slides/slide(\d+)\.xml"):
            num = re.search(r"slide(\d+)\.xml", n).group(1)
            body = paragraphs(z.read(n), a + "p", a + "t")
            parts.append("## Slide {}\n\n{}".format(num, "\n".join(body)))
            if num in notes:
                spoken = [l for l in paragraphs(z.read(notes[num]), a + "p", a + "t") if l != num]
                if spoken:
                    parts.append("Notes: " + " ".join(spoken))
    return "\n\n".join(parts)


def docx(path):
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        return "\n\n".join(paragraphs(z.read("word/document.xml"), w + "p", w + "t"))


def xlsx(path):
    s = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(s + "si"):
                shared.append("".join(t.text or "" for t in si.iter(s + "t")))
        parts = []
        for n in numbered(z.namelist(), r"xl/worksheets/sheet(\d+)\.xml"):
            rows = []
            for row in ET.fromstring(z.read(n)).iter(s + "row"):
                cells = []
                for c in row.iter(s + "c"):
                    v = c.find(s + "v")
                    inline = c.find(s + "is")
                    if c.get("t") == "s" and v is not None:
                        cells.append(shared[int(v.text)])
                    elif inline is not None:
                        cells.append("".join(t.text or "" for t in inline.iter(s + "t")))
                    else:
                        cells.append(v.text if v is not None else "")
                rows.append("\t".join(cells))
            parts.append("## {}\n\n{}".format(os.path.basename(n), "\n".join(rows)))
    return "\n\n".join(parts)


class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg"}
    BLOCK = {"p", "div", "li", "tr", "br", "pre", "section", "article", "table", "blockquote"}

    def __init__(self):
        super().__init__()
        self.out, self.skip, self.href = [], 0, None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in self.BLOCK:
            self.out.append("\n")
        elif tag == "a":
            self.href = dict(attrs).get("href")
        elif tag == "img" and not self.skip:
            a = dict(attrs)
            self.out.append("\n![{}]({})\n".format(a.get("alt") or "", a.get("src") or ""))

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag == "a" and self.href and not self.skip:
            if not self.href.startswith("#"):
                self.out.append(" <{}>".format(self.href))
            self.href = None

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_page(path):
    parser = _Text()
    with open(path, encoding="utf-8", errors="replace") as f:
        parser.feed(f.read())
    text = "".join(parser.out)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def ipynb(path):
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    parts = []
    for cell in nb.get("cells", []):
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code":
            parts.append("```python\n" + src + "\n```")
            for o in cell.get("outputs", []):
                text = "".join(o.get("text", []) or o.get("data", {}).get("text/plain", []))
                if text:
                    parts.append("```\n" + text[:2000] + "\n```")
        else:
            parts.append(src)
    return "\n\n".join(parts)


def captions(path):
    lines, last, minute = [], None, -1
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            stamp = re.match(r"(?:(\d+):)?(\d+):(\d+)[.,]\d+\s+-->", line)
            if stamp:
                h, m = int(stamp.group(1) or 0), int(stamp.group(2))
                if h * 60 + m != minute:
                    minute = h * 60 + m
                    lines.append("\n[{}:{:02d}:00] ".format(h, m) if h else "\n[{:02d}:00] ".format(m))
                continue
            if not line or line.isdigit() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
                continue
            text = re.sub(r"<[^>]+>", "", line).strip()
            if text and text != last:
                lines.append(text + " ")
                last = text
    return "".join(lines).strip()


def archive(path):
    with zipfile.ZipFile(path) as z:
        rows = ["{}\t{}".format(i.file_size, i.filename) for i in z.infolist()]
    return "Archive contents (bytes, path). Unpack before extracting members.\n\n" + "\n".join(rows)


def plain(path, ext):
    with open(path, encoding="utf-8", errors="replace") as f:
        body = f.read()
    return "```{}\n{}\n```".format(CODE_EXTS[ext], body) if ext in CODE_EXTS else body


HANDLERS = {
    ".pdf": pdf, ".pptx": pptx, ".docx": docx, ".xlsx": xlsx,
    ".html": html_page, ".htm": html_page, ".ipynb": ipynb,
    ".vtt": captions, ".srt": captions, ".zip": archive,
}


BINARY_EXTS = {".pdf", ".pptx", ".docx", ".xlsx", ".zip"}


def fail(message):
    sys.stderr.write(message + "\n")
    sys.exit(3)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    ext = os.path.splitext(src)[1].lower()
    if ext in BINARY_EXTS:
        with open(src, "rb") as f:
            head = f.read(512).lstrip().lower()
        if head.startswith((b"<!doctype", b"<html")):
            fail("{} is an HTML page, not a {} file: the URL served a viewer, login or redirect page".format(src, ext))
    if ext in HANDLERS:
        try:
            text = HANDLERS[ext](src)
        except Exception as e:  # any parse failure is reported, never a traceback
            fail("could not read {} as {}: {}: {}".format(src, ext, type(e).__name__, e))
    elif ext in CODE_EXTS or ext in PLAIN_EXTS:
        text = plain(src, ext)
    else:
        sys.stderr.write("no extractor for {} ({})\n".format(ext or "no extension", src))
        sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write("<!-- source: {} -->\n\n{}\n".format(os.path.abspath(src), text))
    print("{}: {} chars".format(dst, len(text)))


if __name__ == "__main__":
    main()
