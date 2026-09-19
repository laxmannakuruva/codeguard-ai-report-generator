import re
p = r"artifacts\codeguard-ai\backend\app\services\report_renderer\styles\report.css"
s = open(p, encoding="utf-8").read()
count = 0

# Longest pattern first (special case)
old1 = "@bottom-center { content: none !important; } @bottom-right { content: none !important; } }"
new1 = "@bottom-center { content: counter(page) !important; font-size: 10pt; color: #333; } @bottom-right { content: none !important; } }"
if old1 in s:
    s = s.replace(old1, new1)
    count += 1

# Single-line !important version
old2 = "@bottom-center { content: none !important; }"
new2 = "@bottom-center { content: counter(page) !important; font-size: 10pt; color: #333; }"
n = s.count(old2)
if n:
    s = s.replace(old2, new2)
    count += n

# Single-line plain version
old3 = "@bottom-center { content: none; }"
new3 = "@bottom-center { content: counter(page); font-size: 10pt; color: #333; }"
n = s.count(old3)
if n:
    s = s.replace(old3, new3)
    count += n

open(p, "w", encoding="utf-8", newline="\n").write(s)
print(f"Replaced {count} bottom-center rules")