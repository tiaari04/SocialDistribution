"""Simple markdown reflow tool.
Rewraps paragraphs and list items to target width while preserving code fences and fenced code blocks.
Not perfect but helps reduce MD013 complaints.
"""
import re
import textwrap
from pathlib import Path

TARGET = 120
DOCS = Path("docs")

list_item_re = re.compile(r"^(?P<prefix>\s*(?:[-*+]\s|\d+\.\s))(?P<body>.*)$")
code_fence_re = re.compile(r"^(\s*)```")

def reflow_file(p: Path):
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    out_lines = []
    in_code = False
    i = 0
    buf = []

    def flush_paragraph(buf_lines):
        if not buf_lines:
            return []
        # decide whether these are list items or plain paragraph
        m = list_item_re.match(buf_lines[0])
        if m:
            # reflow as list item(s). For simplicity, reflow each list item separately
            out = []
            for line in buf_lines:
                mm = list_item_re.match(line)
                if mm:
                    prefix = mm.group('prefix')
                    body = mm.group('body').strip()
                    wrapped = textwrap.fill(body, width=TARGET, initial_indent=prefix, subsequent_indent=' ' * len(prefix))
                    out.extend(wrapped.splitlines())
                else:
                    # continuation line - just append
                    out.append(line)
            return out
        else:
            # plain paragraph
            para = " ".join(l.strip() for l in buf_lines)
            wrapped = textwrap.fill(para, width=TARGET)
            return wrapped.splitlines()

    while i < len(lines):
        line = lines[i]
        if code_fence_re.match(line):
            # flush any paragraph buffer
            out_lines.extend(flush_paragraph(buf))
            buf = []
            in_code = not in_code
            out_lines.append(line)
            i += 1
            continue
        if in_code:
            out_lines.append(line)
            i += 1
            continue
        # not in code block
        if line.strip() == "":
            out_lines.extend(flush_paragraph(buf))
            buf = []
            out_lines.append(line)
            i += 1
            continue
        # headings or blockquotes or list items or indented code (4+ spaces) should be buffered as separate paragraphs
        if line.lstrip().startswith('#'):
            out_lines.extend(flush_paragraph(buf))
            buf = []
            out_lines.append(line)
            i += 1
            continue
        if line.startswith('    '):
            out_lines.extend(flush_paragraph(buf))
            buf = []
            out_lines.append(line)
            i += 1
            continue
        # otherwise accumulate into buffer
        # If current line is a list item or starts with list marker, flush previous paragraph first
        if list_item_re.match(line):
            out_lines.extend(flush_paragraph(buf))
            buf = [line]
            # consume subsequent lines that are continuations (start with spaces but not a new list marker or blank)
            j = i + 1
            while j < len(lines) and lines[j].strip() != '' and not list_item_re.match(lines[j]) and not lines[j].lstrip().startswith('#') and not code_fence_re.match(lines[j]):
                buf.append(lines[j])
                j += 1
            out_lines.extend(flush_paragraph(buf))
            buf = []
            i = j
            continue
        # otherwise a normal paragraph line
        buf.append(line)
        i += 1
    # flush remaining
    out_lines.extend(flush_paragraph(buf))
    p.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    md_files = list(DOCS.glob('**/*.md'))
    for f in md_files:
        print('Reflowing', f)
        reflow_file(f)
    print('Done')
