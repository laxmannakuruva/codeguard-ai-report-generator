from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\templates\back_matter.html.j2")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Wrap the entire Appendices section in {% if ctx.has_appendices %}
if "{% if ctx.has_appendices %}" not in s:
    # Add open-if before the APPENDICES comment
    s = s.replace(
        "{# APPENDICES #}",
        "{% if ctx.has_appendices %}\n{# APPENDICES #}",
        1
    )
    # Find the REFERENCES section and close the if before it
    if "{# REFERENCES #}" in s:
        s = s.replace("{# REFERENCES #}", "{% endif %}\n\n{# REFERENCES #}", 1)
        print("wrapped via REFERENCES comment")
    elif "{# REFERENCES" in s:
        s = s.replace("{# REFERENCES", "{% endif %}\n\n{# REFERENCES", 1)
        print("wrapped via REFERENCES (partial)")
    else:
        # Fallback: find the second </section> and add endif
        first = s.find("</section>")
        if first > 0:
            second = s.find("</section>", first + 1)
            if second > 0:
                s = s[:second + 10] + "\n{% endif %}" + s[second + 10:]
                print("wrapped via second </section>")
            else:
                print("only one </section> — manual check needed")
        else:
            print("no </section> found")
else:
    print("already wrapped")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")