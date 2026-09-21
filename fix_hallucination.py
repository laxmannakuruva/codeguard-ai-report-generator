from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\ai_writer.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add a filter in _specs_from_headings to drop headings that mention
# technologies the project doesn't have
old = '''def _specs_from_headings(headings):
    """Build SECTION_SPECS-like list from extracted headings."""
    if not headings or len(headings) < 5:
        return None
    out = []'''

new = '''def _specs_from_headings(headings):
    """Build SECTION_SPECS-like list from extracted headings."""
    if not headings or len(headings) < 5:
        return None

    # Tech keywords that AI often hallucinates but projects may not use
    HALLUCINATION_PRONE = {
        "flask", "django", "mysql", "mongodb", "mongoose",
        "machine learning model", "random forest", "k-nearest", "knn",
        "xgboost", "decision tree", "deep learning", "neural network",
        "tensorflow", "pytorch", "keras", "scikit-learn",
        "predictive analytics", "prediction output",
        "data preprocessing", "exploratory data analysis",
    }
    out = []'''

if old in s:
    s = s.replace(old, new, 1)
    print("step 1: hallucination block added")
else:
    print("step 1 FAILED: anchor not found")

# Add the actual filter inside the loop
old2 = '''    for h in headings:
        title = (h.get("title") or "").strip()
        # Strip leading number: "5.1 Objectives" -> "Objectives"
        import re as _re
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
        out.append({'''

new2 = '''    for h in headings:
        title = (h.get("title") or "").strip()
        # Strip leading number: "5.1 Objectives" -> "Objectives"
        import re as _re
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title

        # Skip hallucination-prone chapters if not in facts
        clean_lower = clean.lower()
        skip = False
        for bad in HALLUCINATION_PRONE:
            if bad in clean_lower:
                # Check if the tech is actually in the project facts
                facts_str = str(facts).lower() if facts else ""
                if bad not in facts_str:
                    skip = True
                    break
        if skip:
            continue

        out.append({'''

if old2 in s:
    s = s.replace(old2, new2, 1)
    print("step 2: filter added to loop")
else:
    print("step 2 FAILED: anchor not found")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")