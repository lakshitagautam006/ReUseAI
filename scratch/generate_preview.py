from test_earth_svg import svg_markup
import base64

b64 = base64.b64encode(svg_markup.strip().encode("utf-8")).decode("utf-8")
html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sustainability Artwork Preview</title>
<style>
body {{
    background-color: #F8FAF7;
    margin: 0;
    padding: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: sans-serif;
}}
.container {{
    max-width: 650px;
    width: 100%;
    background: #FFFFFF;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(20, 83, 45, 0.1);
    padding: 30px;
    text-align: center;
}}
img {{
    width: 100%;
    max-height: 460px;
    object-fit: contain;
}}
</style>
</head>
<body>
<div class="container">
    <h2 style="color: #14532D; margin-top: 0;">ReUseAI Eco Illustration</h2>
    <img src="data:image/svg+xml;base64,{b64}" alt="ReUseAI Earth Illustration" />
</div>
</body>
</html>
"""

with open("scratch/preview.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Generated scratch/preview.html successfully!")
