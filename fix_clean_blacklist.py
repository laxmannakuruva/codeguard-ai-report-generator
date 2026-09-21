from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\ai_writer.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Replace the buggy hallucination filter with a simple unconditional blacklist
import re
pattern = re.compile(
    r"        # Skip hallucination-prone chapters.*?if skip:\n            continue\n",
    re.DOTALL
)

new = '''        # Unconditionally skip ML/Flask chapters (tool is for code projects)
        BLACKLIST = (
            "flask backend", "flask web application", "machine learning model",
            "random forest", "decision tree", "k-nearest", "knn",
            "xgboost", "prediction output", "dataset description",
            "data preprocessing", "exploratory data analysis",
            "model evaluation", "model development",
        )
        clean_lower = clean.lower()
        if any(b in clean_lower for b in BLACKLIST):
            continue
'''

s2 = pattern.sub(new, s)
if s2 != s:
    print("blacklist filter replaced")
else:
    print("regex didn't match — trying alternate")

# Remove the whole HALLUCINATION_PRONE block (no longer needed)
s2 = re.sub(
    r"\n    # Tech keywords that AI often hallucinates.*?\n    \}\n",
    "\n",
    s2,
    flags=re.DOTALL
)

# Remove the now-dead facts line if still present
s2 = s2.replace('        facts_str = str(facts).lower() if facts else ""\n', "")
s2 = s2.replace('        if bad not in facts_str:\n', "")
s2 = s2.replace('            skip = True\n            break\n', "")

p.write_text(s2, encoding="utf-8", newline="\n")
print("saved")