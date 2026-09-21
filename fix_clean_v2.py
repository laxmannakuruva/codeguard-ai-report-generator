from pathlib import Path
import re

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Find start and end of _clean function
start = s.find("def _clean(v):")
if start == -1:
    print("_clean not found")
else:
    # Find the next "def " after _clean
    next_def = s.find("\ndef ", start + 1)
    if next_def == -1:
        next_def = len(s)

    new_clean = '''def _clean(v):
    if v is None:
        return ""
    s = CONFLICT_RE.sub("", str(v))
    s = html.unescape(html.unescape(html.unescape(s)))
    s = _strip_markdown(s)
    s = EMOJI_RE.sub("", s)
    s = re.sub(r"[ \\t]+", " ", s).strip()
    # Code-strip: cap length so raw code never floods the report
    if len(s) > 1500:
        s = s[:1500].rsplit(" ", 1)[0] + "..."
    return s


'''
    s = s[:start] + new_clean + s[next_def+1:]
    p.write_text(s, encoding="utf-8", newline="\n")
    print("_clean replaced cleanly")
    print("saved")