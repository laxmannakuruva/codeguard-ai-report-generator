from pathlib import Path

RR = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")
T = RR / "templates"

# ---- 1. toc.html.j2: number Appendices + References ----
p = T / "toc.html.j2"
s = p.read_text(encoding="utf-8")

# Replace the two hardcoded lines with numbered ones
s = s.replace(
    '<li><span class="toc-title">Appendices</span></li>',
    '<li><span class="toc-title">{{ ctx.chapters|length + 1 }}. Appendices</span></li>',
    1)
s = s.replace(
    '<li><span class="toc-title">References</span></li>',
    '<li><span class="toc-title">{{ ctx.chapters|length + 2 }}. References</span></li>',
    1)

p.write_text(s, encoding="utf-8", newline="\n")
print("toc.html.j2 OK")

# ---- 2. back_matter.html.j2: number the appendices + references pages ----
p = T / "back_matter.html.j2"
s = p.read_text(encoding="utf-8")

s = s.replace('<h1>Appendices</h1>', '<h1>{{ ctx.chapters|length + 1 }}. Appendices</h1>', 1)
s = s.replace('<h1>References</h1>', '<h1>{{ ctx.chapters|length + 2 }}. References</h1>', 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("back_matter.html.j2 OK")
print("ALL DONE")