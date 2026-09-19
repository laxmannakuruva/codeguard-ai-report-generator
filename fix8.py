from pathlib import Path
import re

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# --- 1. Append instead of replace ---
old_onchange = '''              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                if (files.length) {
                  setImages(files);
                  setImagesSaved(false);
                }
              }}'''
new_onchange = '''              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                if (files.length) {
                  setImages((prev) => [...prev, ...files]);
                  setImagesSaved(false);
                }
                e.target.value = "";
              }}'''
if old_onchange in s:
    s = s.replace(old_onchange, new_onchange, 1)
    print("onChange: append mode ON")
else:
    print("onChange: pattern NOT found (may already be patched)")

# --- 2. Add thumbnails with remove buttons below the label ---
anchor = '''          <button
            type="button"
            onClick={saveImages}
            disabled={busy === "images" || !images.length}'''
thumb_block = '''          {images.length > 0 && (
            <ul className="mt-3 space-y-1">
              {images.map((f, i) => (
                <li
                  key={`${f.name}-${i}`}
                  className="flex items-center justify-between gap-2 rounded-md border border-[#e5ebe0] bg-white px-2 py-1 text-xs text-[#41605e]"
                >
                  <span className="truncate">
                    {i + 1}. {f.name}{" "}
                    <span className="text-[#9aa69e]">({formatBytes(f.size)})</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setImages((prev) => prev.filter((_, idx) => idx !== i));
                      setImagesSaved(false);
                    }}
                    className="rounded px-1 text-[#934a39] hover:bg-[#fff4f0]"
                    aria-label={`Remove ${f.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
              <li className="pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setImages([]);
                    setImagesSaved(false);
                  }}
                  className="text-[11px] font-bold text-[#934a39] hover:underline"
                >
                  Clear all
                </button>
              </li>
            </ul>
          )}
          <button
            type="button"
            onClick={saveImages}
            disabled={busy === "images" || !images.length}'''
if "Clear all" not in s and anchor in s:
    s = s.replace(anchor, thumb_block, 1)
    print("thumbnails + remove buttons added")
else:
    print("thumbnails: pattern NOT found or already added")

p.write_text(s, encoding="utf-8", newline="\n")
print("home.tsx OK")
print("ALL DONE")