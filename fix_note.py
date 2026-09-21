from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\components\report-studio.tsx")
s = p.read_text(encoding="utf-8")

old = '''<p className="text-xs font-semibold text-[#58766e]">
                Report ready as editable text and PDF.
              </p>'''

new = '''<p className="text-xs font-semibold text-[#58766e]">
                Report ready as editable text and PDF.
                <span className="ml-2 text-[#9aa69e] font-normal">
                  (First download takes ~30 sec — cached after that)
                </span>
              </p>'''

if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("note added")
else:
    print("anchor not found")