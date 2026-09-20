from pathlib import Path
base = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai")

# robots.txt
(base / "public" / "robots.txt").write_text(
    "User-agent: *\nAllow: /\nSitemap: https://codeguard-frontend-chev.onrender.com/sitemap.xml\n",
    encoding="utf-8"
)

# sitemap.xml
(base / "public" / "sitemap.xml").write_text(
    '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://codeguard-frontend-chev.onrender.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
''',
    encoding="utf-8"
)

print("sitemap.xml + robots.txt created")