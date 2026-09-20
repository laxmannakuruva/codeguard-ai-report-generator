from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# 1. Add state for chapters inside ContextStage
old_state = '''  const [sampleFile, setSampleFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);'''
new_state = '''  const [sampleFile, setSampleFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [chapters, setChapters] = useState<string[]>([]);
  const [chaptersSaved, setChaptersSaved] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);'''
if old_state in s:
    s = s.replace(old_state, new_state, 1)
    print("state added")
else:
    print("state pattern NOT found")

# 2. Add loader — fetch detected chapters
old_effect = '''  const saveProblem = async () => {'''
new_effect = '''  const loadChapters = async () => {
    setLoadingChapters(true);
    try {
      const r = await fetch(`${API_BASE}/api/project/${projectId}/chapters/suggest`);
      if (r.ok) {
        const j = await r.json();
        setChapters(j.chapters || []);
      }
    } catch (e) { /* ignore */ }
    finally { setLoadingChapters(false); }
  };

  const saveChapters = async () => {
    setBusy("chapters");
    setError(null);
    try {
      const r = await fetch(`${API_BASE}/api/project/${projectId}/chapters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chapters }),
      });
      if (!r.ok) throw new Error(await r.text());
      setChaptersSaved(true);
    } catch (e) {
      setError("Chapters could not be saved.");
    } finally {
      setBusy(null);
    }
  };

  const saveProblem = async () => {'''
if old_effect in s:
    s = s.replace(old_effect, new_effect, 1)
    print("functions added")
else:
    print("function insert point NOT found")

# 3. Auto-load chapters when sample report is uploaded
old_upload_success = '''        onSuccess: () => {
          setSampleFile(null);
          invalidateInputs();
        },'''
new_upload_success = '''        onSuccess: () => {
          setSampleFile(null);
          invalidateInputs();
          setTimeout(loadChapters, 500);
        },'''
if old_upload_success in s:
    s = s.replace(old_upload_success, new_upload_success, 1)
    print("auto-load hooked")
else:
    print("upload success pattern NOT found")

# 4. Add UI block — insert before sample report section
old_ui_anchor = '''      {/* SAMPLE REPORT */}
      <div className="border-t border-[#eef2eb] p-6">'''
new_ui_block = '''      {/* CHAPTERS */}
      {(chapters.length > 0 || loadingChapters) && (
        <div className="border-t border-[#eef2eb] p-6">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-[#41605e]">
              <ListChecks size={14} className="text-[#4ca189]" />
              Report chapters
            </div>
            {chaptersSaved && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#267967]">
                Saved
              </span>
            )}
          </div>
          <p className="mb-3 text-xs leading-5 text-[#87918a]">
            We detected these from your sample. Edit, remove, or add freely — the report uses this exact list.
          </p>
          {loadingChapters ? (
            <div className="flex items-center gap-2 text-xs text-[#41605e]">
              <LoaderCircle size={12} className="animate-spin" /> Detecting chapters...
            </div>
          ) : (
            <div className="space-y-2">
              {chapters.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    value={c}
                    onChange={(e) => {
                      const next = [...chapters];
                      next[i] = e.target.value;
                      setChapters(next);
                      setChaptersSaved(false);
                    }}
                    className="flex-1 rounded-md border border-[#dde4da] bg-white px-2 py-1 text-xs text-[#3f5b57] outline-none focus:border-[#8dc0ae]"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setChapters(chapters.filter((_, idx) => idx !== i));
                      setChaptersSaved(false);
                    }}
                    className="rounded px-2 py-1 text-xs font-bold text-[#934a39] hover:bg-[#fff4f0]"
                  >
                    ✕
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => { setChapters([...chapters, ""]); setChaptersSaved(false); }}
                className="text-[11px] font-bold text-[#216e65] hover:underline"
              >
                + Add chapter
              </button>
              <button
                type="button"
                onClick={saveChapters}
                disabled={busy === "chapters" || chapters.filter((c) => c.trim()).length === 0}
                className="ml-3 inline-flex items-center gap-2 rounded-lg bg-[#216e65] px-3 py-1.5 text-[11px] font-bold text-white disabled:opacity-50"
              >
                {busy === "chapters" && <LoaderCircle size={11} className="animate-spin" />}
                Save chapters
              </button>
            </div>
          )}
        </div>
      )}

      {/* SAMPLE REPORT */}
      <div className="border-t border-[#eef2eb] p-6">'''
if old_ui_anchor in s:
    s = s.replace(old_ui_anchor, new_ui_block, 1)
    print("UI block added")
else:
    print("UI anchor NOT found")

# 5. Add ListChecks import
if "ListChecks" not in s.split("from \"lucide-react\"")[0]:
    s = s.replace('import {', 'import {\n  ListChecks,', 1)
    print("ListChecks imported")
else:
    print("ListChecks already imported")

p.write_text(s, encoding="utf-8", newline="\n")
print("home.tsx saved")