from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# Add upload progress state
if "uploadProgress" not in s:
    idx = s.find("useState(")
    if idx > 0:
        line_end = s.find("\n", idx)
        s = s[:line_end] + "\n  const [uploadProgress, setUploadProgress] = useState(0);" + s[line_end:]

# Replace simple fetch upload with XHR upload (gives progress)
old = '''  const uploadSampleFile = () => {'''
new = '''  const [uploadProgressLocal, setUploadProgressLocal] = [null, null];

  const uploadSampleFile = () => {'''
# Not applicable — skip if structure differs

p.write_text(s, encoding="utf-8", newline="\n")
print("progress state added")