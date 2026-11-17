import base64

HERO_SVG = """<svg viewBox="0 0 520 380" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <circle cx="260" cy="190" r="80" fill="#38BDF8"/>
</svg>"""

def get_svg_html(svg_content: str) -> str:
    clean_svg = svg_content.strip()
    b64_svg = base64.b64encode(clean_svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64_svg}" alt="Sustainability Illustration" style="width: 100%; max-height: 350px; object-fit: contain; display: block; margin: auto;" />'

html = get_svg_html(HERO_SVG)
print("Result starts with:", html[:50])
print("Base64 length:", len(html))
