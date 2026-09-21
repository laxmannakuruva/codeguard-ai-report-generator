from pathlib import Path
import re

RR = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ========== 1. ai_writer.py: preserve number prefix on subheadings ==========
p = RR / "ai_writer.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = '''    for h in headings:
        title = (h.get("title") or "").strip()
        # Strip leading number: "5.1 Objectives" -> "Objectives"
        import re as _re
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
'''

new = '''    for h in headings:
        title = (h.get("title") or "").strip()
        import re as _re
        # If it is a subheading (5.1, 5.2), keep the full title as-is
        if _re.match(r"^\\d+\\.\\d+", title):
            clean = title
        else:
            clean = _re.sub(r"^\\d+\\.?\\s+", "", title).strip()
            if not clean:
                clean = title
'''

if old in s:
    s = s.replace(old, new, 1)
    print("ai_writer.py: subheading preservation added")
else:
    print("ai_writer.py: pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 2. api.py: has_appendices flag ==========
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old2 = '''            if not _custom and sample_pdf:
                try:
                    _custom = extract_structure(sample_pdf)
                    if _custom:
                        print(f"[AI] Extracted {len(_custom)} headings from sample PDF", flush=True)
                    else:
                        print("[AI] Structure extraction returned 0 headings, using defaults", flush=True)
                except Exception as _e:
                    print(f"[AI] Structure extraction failed: {_e}", flush=True)'''

new2 = '''            if not _custom and sample_pdf:
                try:
                    _custom = extract_structure(sample_pdf)
                    if _custom:
                        print(f"[AI] Extracted {len(_custom)} headings from sample PDF", flush=True)
                    else:
                        print("[AI] Structure extraction returned 0 headings, using defaults", flush=True)
                except Exception as _e:
                    print(f"[AI] Structure extraction failed: {_e}", flush=True)

            _has_appendices = False
            if _custom:
                for _h in _custom:
                    _t = (_h.get("title") or "").lower()
                    if "appendic" in _t:
                        _has_appendices = True
                        break
            ctx["has_appendices"] = _has_appendices
            print(f"[AI] sample has appendices: {_has_appendices}", flush=True)'''

if old2 in s:
    s = s.replace(old2, new2, 1)
    print("api.py: has_appendices flag added")
else:
    print("api.py: pattern NOT found")

old3 = '''    for i, ch in enumerate(chapters, 1):
        ch.heading = f"{i}. {ch.title}"'''
new3 = '''    import re as _renum
    for i, ch in enumerate(chapters, 1):
        if _renum.match(r"^\\d+", ch.title):
            ch.heading = ch.title
        else:
            ch.heading = f"{i}. {ch.title}"'''
if old3 in s:
    s = s.replace(old3, new3, 1)
    print("api.py: no-double-number added")
else:
    print("api.py: renumber pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 3. toc.html.j2 ==========
p = RR / "templates" / "toc.html.j2"
new_toc = '''<section class="page front" id="anchor-toc">
  <h1>Table of Contents</h1>
  <div class="rule"></div>

  <ul class="toc-list">
    {% for ch in ctx.chapters %}
    <li><span class="toc-title">{{ ch.heading }}</span></li>
    {% endfor %}

    {% if ctx.has_appendices %}
    <li><span class="toc-title">{{ ctx.chapters|length + 1 }}. Appendices</span></li>
    {% endif %}
    <li><span class="toc-title">{{ ctx.chapters|length + (2 if ctx.has_appendices else 1) }}. References</span></li>
  </ul>
</section>
'''
p.write_text(new_toc, encoding="utf-8", newline="\n")
print("toc.html.j2: conditional Appendices")

p.write_text(s, encoding="utf-8", newline="\n")
print("ALL DONE")