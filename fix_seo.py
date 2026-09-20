from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\index.html")
s = p.read_text(encoding="utf-8")

s = s.replace(
    "<title>CodeGuard AI</title>",
    "<title>CodeGuard AI — AI Report Generator for Internship &amp; Project Reports</title>"
)
s = s.replace(
    '<meta name="description" content="CodeGuard AI — built on Replit. Update this description to reflect the app." />',
    '<meta name="description" content="Upload your code project, get a formatted internship report PDF automatically. AI-powered, matches your college format." />'
)
s = s.replace(
    '<meta property="og:description" content="CodeGuard AI — built on Replit. Update this description to reflect the app." />',
    '<meta property="og:description" content="AI report generator for internship and project reports." />'
)
s = s.replace(
    '<meta name="twitter:description" content="CodeGuard AI — built on Replit. Update this description to reflect the app." />',
    '<meta name="twitter:description" content="AI report generator for internship and project reports." />'
)

# Add keywords + robots if not present
if 'name="keywords"' not in s:
    s = s.replace(
        '<meta name="robots" content="index, follow" />',
        '<meta name="robots" content="index, follow" />\n    <meta name="keywords" content="internship report generator, AI report, project report, code to pdf" />'
    )

p.write_text(s, encoding="utf-8", newline="\n")
print("index.html updated")