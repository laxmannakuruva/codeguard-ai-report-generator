from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\components\report-studio.tsx")
s = p.read_text(encoding="utf-8")

if "downloadState" in s and "setDownloadState" in s and "useState" in s.split("downloadState")[0].split("\n")[-1]:
    print("state already exists")
else:
    # Find the first existing useState and insert right after it
    import re
    m = re.search(r"const \[[^\]]+\] = useState[^\n]+\n", s)
    if m:
        insert_pos = m.end()
        new_line = '  const [downloadState, setDownloadState] = useState<"idle" | "loading" | "done">("idle");\n'
        s = s[:insert_pos] + new_line + s[insert_pos:]
        p.write_text(s, encoding="utf-8", newline="\n")
        print("state added")
    else:
        print("ERROR: no useState found — paste this output")

p.write_text(s, encoding="utf-8", newline="\n")