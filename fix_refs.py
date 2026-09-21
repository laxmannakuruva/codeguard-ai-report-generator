from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\templates\back_matter.html.j2")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Replace the References section with auto-generation
import re

# Find the References section
start = s.find("{# REFERENCES #}")
if start == -1:
    start = s.find("anchor-references")

if start > 0:
    # Find the section end
    end = s.find("</section>", start)
    if end > 0:
        end += len("</section>")
        new_refs = '''{# REFERENCES #}
<section class="page front" id="anchor-references">
  <h1>{{ ctx.chapters|length + (2 if ctx.has_appendices else 1) }}. References</h1>
  <div class="rule"></div>

  {% set _langs = ctx.languages or [] %}
  {% set _frameworks = ctx.frameworks or [] %}
  {% set _libraries = ctx.libraries or [] %}

  {% if ctx.references_section and ctx.references_section.blocks %}
    {% for block in ctx.references_section.blocks %}
      {% if block.type == "ol" or block.type == "ul" %}
        <ol class="references-list">
          {% for item in block.items %}<li>{{ item }}</li>{% endfor %}
        </ol>
      {% elif block.text %}
        <p>{{ block.text }}</p>
      {% endif %}
    {% endfor %}
  {% else %}
    <ol class="references-list">
      {% for lang in _langs %}
        <li>{{ lang }}. Official Documentation. https://{{ lang|lower }}.org/docs/</li>
      {% endfor %}
      {% for fw in _frameworks %}
        <li>{{ fw }}. Official Documentation.</li>
      {% endfor %}
      {% for lib in _libraries[:10] %}
        <li>{{ lib }}. Official Documentation.</li>
      {% endfor %}
    </ol>
  {% endif %}
</section>'''
        s = s[:start] + new_refs + s[end:]
        print("references section replaced")
    else:
        print("could not find section end")
else:
    print("could not find references marker")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")