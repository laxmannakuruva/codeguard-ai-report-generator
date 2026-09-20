from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\index.html")
s = p.read_text(encoding="utf-8")

tag = '    <meta name="google-site-verification" content="0q6lFSDoW5mzL8lBOg5diVhL4SzW8bzKC-AXXwCUNAI" />'

if "google-site-verification" not in s:
    # Insert right after the charset meta tag
    s = s.replace(
        '<meta charset="UTF-8" />',
        '<meta charset="UTF-8" />\n' + tag,
        1
    )
    p.write_text(s, encoding="utf-8", newline="\n")
    print("verification tag added")
else:
    print("already present")