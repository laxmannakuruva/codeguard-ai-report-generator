from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\components\report-studio.tsx")
s = p.read_text(encoding="utf-8")

# 1. Add downloadState useState if missing
if "downloadState" not in s:
    # find first useState and add after it
    idx = s.find("useState(")
    if idx > 0:
        line_end = s.find("\n", idx)
        insert = "\n  const [downloadState, setDownloadState] = useState<\"idle\" | \"loading\" | \"done\">(\"idle\");"
        s = s[:line_end] + insert + s[line_end:]
        print("state added")
    else:
        print("useState anchor not found")

# 2. Ensure LoaderCircle and Check imports
if "LoaderCircle" not in s:
    s = s.replace("Download", "Download,\n  LoaderCircle,", 1)
    print("LoaderCircle import added")
if "  Check," not in s and "Check }" not in s:
    s = s.replace("Download,", "Download,\n  Check,", 1)
    print("Check import added")

# 3. Replace the <a> download block with <button>
old = '''<a
                href={`${API_BASE}/api/project/${projectId}/report.pdf`}
                download="project-report.pdf"
                className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-[#216e65] px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-[#185b54]"
                data-testid="button-download-report-pdf"
              >
                <Download size={14} />
                Download PDF
              </a>'''

new = '''<button
                type="button"
                onClick={async () => {
                  setDownloadState("loading");
                  try {
                    const r = await fetch(`${API_BASE}/api/project/${projectId}/report.pdf`);
                    if (!r.ok) throw new Error("download failed");
                    const blob = await r.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "project-report.pdf";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);
                    setDownloadState("done");
                    setTimeout(() => setDownloadState("idle"), 3000);
                  } catch {
                    setDownloadState("idle");
                  }
                }}
                disabled={downloadState === "loading"}
                className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-[#216e65] px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-[#185b54] disabled:opacity-70"
                data-testid="button-download-report-pdf"
              >
                {downloadState === "loading" && (
                  <>
                    <LoaderCircle size={14} className="animate-spin" />
                    Downloading...
                  </>
                )}
                {downloadState === "done" && (
                  <>
                    <Check size={14} />
                    Downloaded
                  </>
                )}
                {downloadState === "idle" && (
                  <>
                    <Download size={14} />
                    Download PDF
                  </>
                )}
              </button>'''

if old in s:
    s = s.replace(old, new, 1)
    print("button replaced")
else:
    print("WARN: exact <a> block not found — will try regex")
    import re
    pattern = re.compile(
        r"<a\s+href=\{`\$\{API_BASE\}[^`]*report\.pdf`\}\s+download=\"project-report\.pdf\"[^>]*>.*?</a>",
        re.DOTALL
    )
    m = pattern.search(s)
    if m:
        s = s[:m.start()] + new + s[m.end():]
        print("button replaced via regex")
    else:
        print("FAILED: could not find block")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")