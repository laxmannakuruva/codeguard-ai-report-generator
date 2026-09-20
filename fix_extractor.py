from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# 1. Replace hardcoded skip with "find first numbered chapter"
old = '''    # Skip cover (p1), certificate (p2), TOC page — keep everything else
    skip_pages = {1, 2}
    if toc_page:
        skip_pages.add(toc_page)
    start_page = 3'''

new = '''    # Find the first page where a real numbered chapter "1. X" begins
    start_page = None
    for l in lines:
        if toc_page and l["page"] <= toc_page:
            continue
        t = l["text"].strip()
        if re.match(r"^1\\.\\s+[A-Z]", t) and l["size"] >= body_size + 0.5:
            start_page = l["page"]
            break
    if start_page is None:
        start_page = (toc_page or 4) + 1
    skip_pages = set(range(1, start_page))
    if toc_page:
        skip_pages.add(toc_page)'''

if old in s:
    s = s.replace(old, new, 1)
    print("extractor: start-page logic fixed")
else:
    print("extractor: pattern NOT found")

# 2. Add title whitelist filter before append
old2 = '''        if l["bold"] and size_diff >= 1 and len(t) < 60:'''
new2 = '''        # REJECT titles that look like body text fragments
        _bad_starters = ("and ", "or ", "but ", "the dean", "we would", "i would",
                         "signature", "vice chancellor", "prof.", "dr ", "mr ", "ms ")
        _bad_contains = ("dean of the", "signature of", "we would like", "i would like",
                         "would like to express", "sincerely", "gratitude")
        tl_check = t.lower().strip()
        if any(tl_check.startswith(b) for b in _bad_starters):
            continue
        if any(b in tl_check for b in _bad_contains):
            continue
        if tl_check == "joining report":
            continue
        if len(t.split()) > 12:
            continue
        # Reject if starts lowercase
        if t and t[0].islower():
            continue

        if l["bold"] and size_diff >= 1 and len(t) < 60:'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("extractor: title whitelist added")
else:
    print("extractor: whitelist pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 2. content.py: fix "1 would like" -> "I would like" ==========
p2 = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
s2 = p2.read_text(encoding="utf-8").lstrip("\ufeff")
if "ROMAN_FIX" not in s2:
    old3 = 's = html.unescape(html.unescape(html.unescape(s)))'
    new3 = '''s = html.unescape(html.unescape(html.unescape(s)))
    # ROMAN_FIX: Groq models sometimes emit "1" instead of "I"
    s = re.sub(r"^1\\s+(would|am|have|had|will|was|wish|extend|sincerely)", r"I \\1", s)'''
    if old3 in s2:
        s2 = s2.replace(old3, new3, 1)
        print("content.py: 1->I fix added")
    else:
        print("content.py: pattern NOT found")
else:
    print("content.py: already has ROMAN_FIX")
p2.write_text(s2, encoding="utf-8", newline="\n")

print("ALL DONE")