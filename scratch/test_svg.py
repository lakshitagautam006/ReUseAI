"""Test generating the Eco Green Hero SVG illustration."""

def get_hero_svg() -> str:
    return """
    <svg viewBox="0 0 520 400" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="max-height: 360px;">
        <defs>
            <linearGradient id="earthOcean" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#38BDF8"/>
                <stop offset="100%" stop-color="#0284C7"/>
            </linearGradient>
            <linearGradient id="earthLand" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#4ADE80"/>
                <stop offset="100%" stop-color="#15803D"/>
            </linearGradient>
            <linearGradient id="greenLeaf" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#34D399"/>
                <stop offset="100%" stop-color="#059669"/>
            </linearGradient>
            <linearGradient id="orbitGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#10B981" stop-opacity="0.2"/>
                <stop offset="50%" stop-color="#34D399" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#10B981" stop-opacity="0.2"/>
            </linearGradient>
            <filter id="softShadow" x="-10%" y="-10%" width="130%" height="130%">
                <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#14532D" flood-opacity="0.15"/>
            </filter>
        </defs>

        <!-- Background Ambient Glow -->
        <circle cx="260" cy="200" r="170" fill="#ECFDF5" opacity="0.8"/>
        <circle cx="260" cy="200" r="140" fill="#D1FAE5" opacity="0.4"/>

        <!-- Orbit Ring 1 -->
        <ellipse cx="260" cy="200" rx="190" ry="75" fill="none" stroke="url(#orbitGlow)" stroke-width="3" stroke-dasharray="10 8" transform="rotate(-25 260 200)"/>

        <!-- Center Earth Globe -->
        <g filter="url(#softShadow)">
            <circle cx="260" cy="200" r="85" fill="url(#earthOcean)"/>
            <!-- Continents -->
            <path d="M 230 140 Q 250 130 275 145 Q 295 160 280 185 Q 260 200 240 180 Q 220 160 230 140 Z" fill="url(#earthLand)" opacity="0.95"/>
            <path d="M 245 210 Q 270 205 285 225 Q 295 250 270 265 Q 250 270 235 250 Q 230 230 245 210 Z" fill="url(#earthLand)" opacity="0.95"/>
            <path d="M 195 180 Q 210 170 220 190 Q 215 210 200 215 Q 185 200 195 180 Z" fill="url(#earthLand)" opacity="0.95"/>
            <path d="M 310 175 Q 330 170 335 195 Q 325 210 310 200 Z" fill="url(#earthLand)" opacity="0.95"/>
            <!-- Atmospheric Shine -->
            <ellipse cx="230" cy="165" rx="55" ry="35" fill="#FFFFFF" opacity="0.18" transform="rotate(-30 230 165)"/>
        </g>

        <!-- Orbiting Item 1: Plastic Bottle (Top Left) -->
        <g transform="translate(75, 90) rotate(-15)" filter="url(#softShadow)">
            <rect x="25" y="10" width="16" height="10" rx="2" fill="#0284C7"/>
            <rect x="27" y="20" width="12" height="15" rx="1" fill="#E0F2FE" stroke="#38BDF8" stroke-width="1.5"/>
            <rect x="18" y="35" width="30" height="55" rx="8" fill="#BAE6FD" stroke="#0284C7" stroke-width="2"/>
            <rect x="19" y="50" width="28" height="22" rx="2" fill="#E0F2FE" opacity="0.9"/>
            <path d="M 26 57 L 33 57 M 26 62 L 38 62" stroke="#0284C7" stroke-width="1.5" stroke-linecap="round"/>
            <!-- Recycle mini badge -->
            <circle cx="33" cy="72" r="5" fill="#10B981"/>
            <path d="M 31 72 L 35 72 M 33 70 L 35 72 L 33 74" stroke="#FFFFFF" stroke-width="1" fill="none"/>
        </g>

        <!-- Orbiting Item 2: Cardboard Box (Top Right) -->
        <g transform="translate(370, 70) rotate(12)" filter="url(#softShadow)">
            <!-- Isometric Box -->
            <polygon points="40,20 75,5 110,20 75,35" fill="#E4C198" stroke="#A77A44" stroke-width="1.5"/>
            <polygon points="40,20 75,35 75,75 40,60" fill="#C99B63" stroke="#A77A44" stroke-width="1.5"/>
            <polygon points="75,35 110,20 110,60 75,75" fill="#B3864F" stroke="#A77A44" stroke-width="1.5"/>
            <!-- Flap Tape -->
            <line x1="58" y1="12" x2="92" y2="28" stroke="#8C6233" stroke-width="2"/>
            <!-- Recycle Stamp -->
            <circle cx="58" cy="48" r="8" fill="#A77A44" opacity="0.4"/>
            <text x="54" y="52" font-size="10" fill="#FFFFFF" font-family="sans-serif">♻</text>
        </g>

        <!-- Orbiting Item 3: Glass Jar (Bottom Right) -->
        <g transform="translate(365, 245) rotate(-10)" filter="url(#softShadow)">
            <!-- Metal Lid -->
            <rect x="18" y="10" width="44" height="12" rx="3" fill="#D4AF37" stroke="#A68218" stroke-width="1.5"/>
            <line x1="28" y1="10" x2="28" y2="22" stroke="#A68218" stroke-width="1"/>
            <line x1="40" y1="10" x2="40" y2="22" stroke="#A68218" stroke-width="1"/>
            <line x1="52" y1="10" x2="52" y2="22" stroke="#A68218" stroke-width="1"/>
            <!-- Glass Body -->
            <rect x="14" y="22" width="52" height="65" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
            <rect x="20" y="36" width="40" height="34" rx="4" fill="#FFFFFF" opacity="0.85" stroke="#A7F3D0" stroke-width="1"/>
            <text x="27" y="52" font-size="8" font-weight="bold" fill="#047857" font-family="sans-serif">REUSE</text>
            <text x="27" y="62" font-size="7" fill="#059669" font-family="sans-serif">100% PURE</text>
            <!-- Highlight Reflection -->
            <path d="M 20 28 L 20 80" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
        </g>

        <!-- Green Leaves & Vines around Earth -->
        <!-- Leaf 1 (Left of Earth) -->
        <g transform="translate(145, 210) rotate(-40)">
            <path d="M 0 0 C 15 -25 45 -20 50 0 C 45 20 15 25 0 0 Z" fill="url(#greenLeaf)"/>
            <path d="M 0 0 Q 25 -2 50 0" stroke="#A7F3D0" stroke-width="1.5" fill="none"/>
        </g>
        <!-- Leaf 2 (Right of Earth) -->
        <g transform="translate(345, 170) rotate(50)">
            <path d="M 0 0 C 18 -30 50 -25 55 0 C 50 25 18 30 0 0 Z" fill="url(#greenLeaf)"/>
            <path d="M 0 0 Q 28 -2 55 0" stroke="#A7F3D0" stroke-width="1.5" fill="none"/>
        </g>
        <!-- Leaf 3 (Bottom Center) -->
        <g transform="translate(250, 305) rotate(10)">
            <path d="M 0 0 C 15 -28 42 -22 48 0 C 42 22 15 28 0 0 Z" fill="url(#greenLeaf)"/>
            <path d="M 0 0 Q 24 -2 48 0" stroke="#A7F3D0" stroke-width="1.5" fill="none"/>
        </g>

        <!-- Circular Recycling Arrows around Earth -->
        <!-- Arrow 1 (Top Arc) -->
        <path d="M 205 135 A 85 85 0 0 1 315 135" fill="none" stroke="#10B981" stroke-width="4" stroke-linecap="round"/>
        <polygon points="315,127 327,137 315,145" fill="#10B981"/>

        <!-- Arrow 2 (Bottom Arc) -->
        <path d="M 315 265 A 85 85 0 0 1 205 265" fill="none" stroke="#10B981" stroke-width="4" stroke-linecap="round"/>
        <polygon points="205,273 193,263 205,255" fill="#10B981"/>

        <!-- Sparkles / Eco Stars -->
        <circle cx="160" cy="110" r="3" fill="#34D399"/>
        <circle cx="370" cy="170" r="2.5" fill="#6EE7B7"/>
        <circle cx="210" cy="330" r="3" fill="#10B981"/>
        <circle cx="340" cy="320" r="2" fill="#34D399"/>
    </svg>
    """

if __name__ == "__main__":
    svg = get_hero_svg()
    print(f"SVG Length: {len(svg)} chars. Successfully formatted.")
