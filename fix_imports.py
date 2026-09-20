from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# 1. Remove the bad "List, " from react import
s = s.replace('import {\n  List, useState } from "react";', 'import { useState } from "react";', 1)

# 2. Add List to the lucide-react import block (after AlertCircle,)
s = s.replace('import {\n  AlertCircle,\n  Check,', 'import {\n  AlertCircle,\n  Check,\n  List,', 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("imports fixed")