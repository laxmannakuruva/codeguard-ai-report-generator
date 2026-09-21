from app.services.report_renderer.ai_writer import _specs_from_headings, _roman_fix
from app.services.report_renderer.content import _clean

print("=== TEST 1: chapter numbering ===")
headings = [
    {"title": "1. Introduction"},
    {"title": "5. Overview of Organization"},
    {"title": "5.1 History"},
    {"title": "5.2 Business Size"},
    {"title": "22. Flask Backend"},
    {"title": "23. Technology Stack"},
]
result = _specs_from_headings(headings)
print(f"  {len(result)} chapters after filter:")
for r in result:
    print(f"    -> {r['title']}")

print()
print("=== TEST 2: roman I/1 fix ===")
bad = "1 express profound gratitude. 1 would like to thank. 1 am grateful."
good = _roman_fix(bad)
print(f"  before: {bad}")
print(f"  after:  {good}")

print()
print("=== TEST 3: HTML entity fix ===")
bad = "PM Kisan &amp;amp; Crop Fertilizer"
good = _clean(bad)
print(f"  before: {bad}")
print(f"  after:  {good}")

print()
print("=== TEST 4: code block length cap ===")
bad = "import logging " * 300
good = _clean(bad)
print(f"  input length: {len(bad)}")
print(f"  output length: {len(good)}")
print(f"  ends with: ...{good[-50:]}")