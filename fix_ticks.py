from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# Remove the Check icon from the two buttons
old1 = '''          {busy === "problem" ? (
            <LoaderCircle size={13} className="animate-spin" />
          ) : (
            <Check size={13} />
          )}
          Save problem statement'''
new1 = '''          {busy === "problem" && (
            <LoaderCircle size={13} className="animate-spin" />
          )}
          Save problem statement'''
if old1 in s:
    s = s.replace(old1, new1, 1)
    print("Save button: tick removed")

old2 = '''          {busy === "images" ? (
            <LoaderCircle size={13} className="animate-spin" />
          ) : (
            <Check size={13} />
          )}
          Upload images'''
new2 = '''          {busy === "images" && (
            <LoaderCircle size={13} className="animate-spin" />
          )}
          Upload images'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("Upload button: tick removed")

p.write_text(s, encoding="utf-8", newline="\n")
print("home.tsx saved")