# Draft of the premium sustainability Earth illustration SVG
import xml.etree.ElementTree as ET

svg_markup = '''<svg viewBox="0 0 600 520" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <!-- Background Ambient Aura -->
        <radialGradient id="ambientGlow" cx="50%" cy="48%" r="50%">
            <stop offset="0%" stop-color="#D1FAE5" stop-opacity="0.6"/>
            <stop offset="45%" stop-color="#ECFDF5" stop-opacity="0.35"/>
            <stop offset="80%" stop-color="#F8FAF7" stop-opacity="0.0"/>
            <stop offset="100%" stop-color="#F8FAF7" stop-opacity="0.0"/>
        </radialGradient>

        <!-- Spherical Earth Base Gradient: Radiant Cyan to Deep Ocean Navy -->
        <radialGradient id="earthSphere" cx="38%" cy="32%" r="68%">
            <stop offset="0%" stop-color="#38BDF8"/>
            <stop offset="25%" stop-color="#0EA5E9"/>
            <stop offset="65%" stop-color="#0284C7"/>
            <stop offset="85%" stop-color="#0369A1"/>
            <stop offset="100%" stop-color="#0C4A6E"/>
        </radialGradient>

        <!-- 3D Spherical Shadow Overlay (Dark crescent giving dramatic volumetric depth) -->
        <radialGradient id="earthShadowOverlay" cx="30%" cy="25%" r="75%">
            <stop offset="50%" stop-color="#000000" stop-opacity="0.0"/>
            <stop offset="78%" stop-color="#02294F" stop-opacity="0.3"/>
            <stop offset="92%" stop-color="#011627" stop-opacity="0.65"/>
            <stop offset="100%" stop-color="#01101E" stop-opacity="0.85"/>
        </radialGradient>

        <!-- Atmosphere Outer Rim Glow -->
        <radialGradient id="atmosphereGlow" cx="50%" cy="50%" r="50%">
            <stop offset="80%" stop-color="#38BDF8" stop-opacity="0.0"/>
            <stop offset="90%" stop-color="#6EE7B7" stop-opacity="0.45"/>
            <stop offset="96%" stop-color="#38BDF8" stop-opacity="0.7"/>
            <stop offset="100%" stop-color="#0284C7" stop-opacity="0.0"/>
        </radialGradient>

        <!-- Continent Gradients: Rich Multi-Tone Vibrant Greens -->
        <linearGradient id="continentGreen1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#4ADE80"/>
            <stop offset="40%" stop-color="#22C55E"/>
            <stop offset="100%" stop-color="#15803D"/>
        </linearGradient>
        <linearGradient id="continentGreen2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#86EFAC"/>
            <stop offset="50%" stop-color="#16A34A"/>
            <stop offset="100%" stop-color="#14532D"/>
        </linearGradient>
        <linearGradient id="continentWarm" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FACC15"/>
            <stop offset="25%" stop-color="#4ADE80"/>
            <stop offset="85%" stop-color="#15803D"/>
        </linearGradient>

        <!-- Orbital Rings Gradients (Emerald / Mint / Cyan Circular Economy Track) -->
        <linearGradient id="orbitGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#10B981" stop-opacity="0.15"/>
            <stop offset="30%" stop-color="#34D399" stop-opacity="0.85"/>
            <stop offset="65%" stop-color="#059669" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.2"/>
        </linearGradient>
        <linearGradient id="orbitGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.1"/>
            <stop offset="40%" stop-color="#6EE7B7" stop-opacity="0.75"/>
            <stop offset="70%" stop-color="#10B981" stop-opacity="0.85"/>
            <stop offset="100%" stop-color="#059669" stop-opacity="0.15"/>
        </linearGradient>

        <!-- Material Gradients -->
        <!-- Cardboard Box Tones -->
        <linearGradient id="cardboardTop" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FDE68A"/>
            <stop offset="100%" stop-color="#F59E0B"/>
        </linearGradient>
        <linearGradient id="cardboardFrontLeft" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#EAB308"/>
            <stop offset="100%" stop-color="#D97706"/>
        </linearGradient>
        <linearGradient id="cardboardFrontRight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#D97706"/>
            <stop offset="100%" stop-color="#B45309"/>
        </linearGradient>
        <linearGradient id="tapeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#FEF08A" stop-opacity="0.85"/>
            <stop offset="100%" stop-color="#FDE047" stop-opacity="0.6"/>
        </linearGradient>

        <!-- Plastic Bottle Tones -->
        <linearGradient id="bottleBody" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#E0F2FE"/>
            <stop offset="40%" stop-color="#BAE6FD"/>
            <stop offset="100%" stop-color="#38BDF8"/>
        </linearGradient>
        <linearGradient id="bottleCap" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#34D399"/>
            <stop offset="100%" stop-color="#059669"/>
        </linearGradient>

        <!-- Glass Jar Tones -->
        <linearGradient id="jarBody" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#ECFDF5" stop-opacity="0.9"/>
            <stop offset="35%" stop-color="#D1FAE5" stop-opacity="0.5"/>
            <stop offset="70%" stop-color="#A7F3D0" stop-opacity="0.7"/>
            <stop offset="100%" stop-color="#34D399" stop-opacity="0.85"/>
        </linearGradient>
        <linearGradient id="jarLid" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FDE68A"/>
            <stop offset="50%" stop-color="#F59E0B"/>
            <stop offset="100%" stop-color="#B45309"/>
        </linearGradient>

        <!-- Botanical Leaf -->
        <linearGradient id="leafGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#86EFAC"/>
            <stop offset="50%" stop-color="#22C55E"/>
            <stop offset="100%" stop-color="#15803D"/>
        </linearGradient>

        <!-- Filters: Soft Isometric & Elevation Shadows -->
        <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        </filter>
        <filter id="elevShadow" x="-25%" y="-25%" width="150%" height="150%">
            <feDropShadow dx="0" dy="12" stdDeviation="14" flood-color="#064E3B" flood-opacity="0.18"/>
        </filter>
        <filter id="itemShadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="2" dy="8" stdDeviation="7" flood-color="#064E3B" flood-opacity="0.16"/>
        </filter>

        <!-- Earth Clipping Mask: Perfectly clips continents, clouds & shadows to sphere (cx=300, cy=255, r=120) -->
        <clipPath id="earthClip">
            <circle cx="300" cy="255" r="120"/>
        </clipPath>
    </defs>

    <!-- 1. Ambient Lighting Aura -->
    <circle cx="300" cy="255" r="230" fill="url(#ambientGlow)"/>

    <!-- 2. Circular Economy Orbital Paths (Back Orbit Segment) -->
    <!-- Orbit 1: Dynamic Tilt (~-26 deg) -->
    <g transform="rotate(-26 300 255)">
        <ellipse cx="300" cy="255" rx="235" ry="85" fill="none" stroke="url(#orbitGrad1)" stroke-width="2.5" stroke-dasharray="14 10"/>
    </g>
    <!-- Orbit 2: Counter Intersecting Tilt (~32 deg) -->
    <g transform="rotate(32 300 255)">
        <ellipse cx="300" cy="255" rx="210" ry="75" fill="none" stroke="url(#orbitGrad2)" stroke-width="2" stroke-dasharray="8 6"/>
    </g>

    <!-- 3. Atmospheric Outer Glow (Halo around Earth) -->
    <circle cx="300" cy="255" r="126" fill="url(#atmosphereGlow)"/>

    <!-- 4. Central 3D Earth Globe with Elevation Shadow -->
    <g filter="url(#elevShadow)">
        <!-- Base Ocean Sphere -->
        <circle cx="300" cy="255" r="120" fill="url(#earthSphere)"/>

        <!-- Clipped Continents, Topography & Clouds -->
        <g clip-path="url(#earthClip)">
            <!-- Shallow Ocean Continental Shelves / Turquoise Coastal Glow -->
            <path d="M 230 165 C 245 155, 275 160, 290 175 C 310 195, 295 230, 265 240 C 240 250, 220 220, 215 195 Z" fill="#38BDF8" opacity="0.35"/>
            <path d="M 290 240 C 315 230, 345 250, 350 280 C 340 310, 305 330, 280 315 C 265 295, 275 260, 290 240 Z" fill="#38BDF8" opacity="0.35"/>
            <path d="M 320 180 C 355 170, 395 190, 390 225 C 375 250, 340 240, 325 210 Z" fill="#38BDF8" opacity="0.35"/>

            <!-- Landmass 1: North America & Central Region -->
            <path d="M 220 170 C 235 158, 255 162, 270 172 C 285 182, 280 200, 268 215 C 255 228, 240 232, 228 220 C 218 210, 212 185, 220 170 Z" fill="url(#continentGreen1)"/>
            <path d="M 245 180 C 255 175, 265 182, 262 195 C 255 205, 242 200, 245 180 Z" fill="url(#continentWarm)" opacity="0.8"/>
            <circle cx="214" cy="182" r="5" fill="url(#continentGreen2)"/>
            <circle cx="282" cy="165" r="4" fill="url(#continentGreen1)"/>

            <!-- Landmass 2: South America -->
            <path d="M 262 235 C 280 230, 298 245, 302 265 C 305 290, 288 325, 272 340 C 265 335, 262 315, 265 295 C 268 275, 252 250, 262 235 Z" fill="url(#continentGreen2)"/>
            <path d="M 270 250 C 285 248, 292 265, 288 285 C 282 305, 272 310, 270 250 Z" fill="url(#continentWarm)" opacity="0.75"/>

            <!-- Landmass 3: Eurasia / Northern Landmass -->
            <path d="M 305 160 C 325 150, 360 155, 385 170 C 405 185, 412 205, 395 222 C 378 235, 350 228, 332 215 C 315 200, 295 180, 305 160 Z" fill="url(#continentGreen1)"/>
            <path d="M 330 168 C 355 162, 380 175, 375 195 C 362 210, 338 200, 330 168 Z" fill="url(#continentWarm)" opacity="0.7"/>

            <!-- Landmass 4: Africa & Mediterranean -->
            <path d="M 325 225 C 345 220, 365 235, 368 255 C 372 280, 358 315, 342 322 C 332 315, 330 295, 322 280 C 315 260, 312 238, 325 225 Z" fill="url(#continentGreen2)"/>
            <path d="M 335 240 C 350 238, 358 255, 352 275 C 342 295, 332 280, 335 240 Z" fill="url(#continentWarm)" opacity="0.6"/>

            <!-- Islands / Archipelagos -->
            <ellipse cx="388" cy="245" rx="7" ry="5" fill="url(#continentGreen1)"/>
            <circle cx="398" cy="260" r="4" fill="url(#continentGreen2)"/>
            <ellipse cx="372" cy="330" rx="9" ry="6" fill="url(#continentGreen1)"/>

            <!-- Natural Cloud Patterns / Swirls (Translucent White 3D Wisps) -->
            <path d="M 210 205 Q 240 185, 270 202 T 330 195 T 390 205" fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" opacity="0.32" filter="url(#softGlow)"/>
            <path d="M 240 280 Q 280 260, 320 285 T 380 270" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity="0.28" filter="url(#softGlow)"/>
            <path d="M 260 150 Q 295 138, 330 150" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.35" filter="url(#softGlow)"/>

            <!-- 3D Spherical Shading & Shadow Overlay -->
            <circle cx="300" cy="255" r="120" fill="url(#earthShadowOverlay)"/>

            <!-- Atmospheric Specular Light Reflection (Top-Left Curved Sun Reflection) -->
            <path d="M 205 210 C 205 160, 245 142, 290 142 C 270 148, 235 168, 222 205 C 215 225, 218 245, 210 260 C 206 245, 205 228, 205 210 Z" fill="#FFFFFF" opacity="0.4"/>
            <ellipse cx="255" cy="180" rx="55" ry="25" fill="#FFFFFF" opacity="0.15" transform="rotate(-35 255 180)"/>
        </g>

        <!-- Crisp Spherical Atmospheric Ring -->
        <circle cx="300" cy="255" r="120" fill="none" stroke="#6EE7B7" stroke-width="1.8" opacity="0.6"/>
    </g>

    <!-- 5. Floating Recyclable Materials Around Earth (Circular Economy Feedstock) -->

    <!-- ITEM A: Isometric Cardboard Box (Top-Right, ~ (460, 110)) -->
    <g transform="translate(435, 80)" filter="url(#itemShadow)">
        <!-- Floating Shadow -->
        <ellipse cx="40" cy="85" rx="32" ry="10" fill="#064E3B" opacity="0.12"/>
        <!-- 3D Box: Top Face -->
        <polygon points="40,15 78,32 40,49 2,32" fill="url(#cardboardTop)" stroke="#B45309" stroke-width="1"/>
        <!-- 3D Box: Left Face -->
        <polygon points="2,32 40,49 40,90 2,73" fill="url(#cardboardFrontLeft)" stroke="#B45309" stroke-width="1"/>
        <!-- 3D Box: Right Face -->
        <polygon points="40,49 78,32 78,73 40,90" fill="url(#cardboardFrontRight)" stroke="#B45309" stroke-width="1"/>
        <!-- Sealing Tape along Top & Front Seam -->
        <polygon points="35,17 45,21 45,47 35,43" fill="url(#tapeGrad)"/>
        <polygon points="36,44 44,47 44,72 36,69" fill="url(#tapeGrad)"/>
        <!-- Recycle Logo on Side -->
        <circle cx="21" cy="58" r="9" fill="#FFFFFF" opacity="0.85"/>
        <text x="16" y="62" font-size="11" font-weight="900" fill="#059669" font-family="-apple-system, sans-serif">♻</text>
        <!-- Sprouting Green Leaf from the Box (Waste -> Resource Life) -->
        <path d="M 40 18 Q 45 -2, 58 4 Q 48 16, 40 18 Z" fill="url(#leafGrad)"/>
        <path d="M 40 18 Q 30 2, 22 10 Q 32 18, 40 18 Z" fill="url(#leafGrad)" opacity="0.85"/>
        <line x1="40" y1="18" x2="52" y2="7" stroke="#A7F3D0" stroke-width="1"/>
    </g>

    <!-- ITEM B: Contoured Recycled Plastic Bottle (Top-Left, ~ (90, 105)) -->
    <g transform="translate(75, 95) rotate(-18 35 60)" filter="url(#itemShadow)">
        <!-- Soft Cast Shadow -->
        <ellipse cx="35" cy="115" rx="24" ry="7" fill="#064E3B" opacity="0.12"/>
        <!-- Screw Cap with Ribbing -->
        <rect x="26" y="6" width="18" height="12" rx="3" fill="url(#bottleCap)" stroke="#047857" stroke-width="1"/>
        <line x1="30" y1="6" x2="30" y2="18" stroke="#A7F3D0" stroke-width="1"/>
        <line x1="35" y1="6" x2="35" y2="18" stroke="#A7F3D0" stroke-width="1"/>
        <line x1="40" y1="6" x2="40" y2="18" stroke="#A7F3D0" stroke-width="1"/>
        <!-- Bottle Neck & Flange -->
        <polygon points="27,18 43,18 47,30 23,30" fill="#BAE6FD" stroke="#38BDF8" stroke-width="1"/>
        <!-- Contoured Ergonomic Body -->
        <path d="M 23 30 C 18 42, 14 55, 16 75 C 17 88, 14 96, 17 106 C 18 112, 52 112, 53 106 C 56 96, 53 88, 54 75 C 56 55, 52 42, 47 30 Z" fill="url(#bottleBody)" stroke="#0284C7" stroke-width="1.5"/>
        <!-- Bottle Waist Grip Bands -->
        <path d="M 16 68 Q 35 73, 54 68" fill="none" stroke="#38BDF8" stroke-width="1.5" opacity="0.7"/>
        <path d="M 16 76 Q 35 81, 54 76" fill="none" stroke="#38BDF8" stroke-width="1.5" opacity="0.7"/>
        <!-- Front Label -->
        <rect x="18" y="82" width="34" height="20" rx="3" fill="#FFFFFF" opacity="0.9" stroke="#A7F3D0" stroke-width="1"/>
        <text x="23" y="94" font-size="7" font-weight="800" fill="#047857" font-family="-apple-system, sans-serif">100% rPET</text>
        <circle cx="43" cy="92" r="3.5" fill="#10B981"/>
        <text x="41.2" y="94.5" font-size="5" font-weight="900" fill="#FFFFFF" font-family="-apple-system, sans-serif">♻</text>
        <!-- Glass/PET Specular Highlight Streak -->
        <path d="M 20 38 C 17 55, 17 85, 20 102" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
    </g>

    <!-- ITEM C: Translucent Glass Jar with Brass Lid (Bottom-Right, ~ (445, 315)) -->
    <g transform="translate(425, 305) rotate(10 40 55)" filter="url(#itemShadow)">
        <!-- Soft Cast Shadow -->
        <ellipse cx="40" cy="115" rx="30" ry="8" fill="#064E3B" opacity="0.14"/>
        <!-- Metallic Brass Lid with Grips -->
        <rect x="16" y="8" width="48" height="15" rx="4" fill="url(#jarLid)" stroke="#B45309" stroke-width="1"/>
        <line x1="24" y1="8" x2="24" y2="23" stroke="#FEF08A" stroke-width="1"/>
        <line x1="32" y1="8" x2="32" y2="23" stroke="#FEF08A" stroke-width="1"/>
        <line x1="40" y1="8" x2="40" y2="23" stroke="#FEF08A" stroke-width="1"/>
        <line x1="48" y1="8" x2="48" y2="23" stroke="#FEF08A" stroke-width="1"/>
        <line x1="56" y1="8" x2="56" y2="23" stroke="#FEF08A" stroke-width="1"/>
        <!-- Threaded Ring -->
        <rect x="20" y="21" width="40" height="6" rx="2" fill="#D97706" opacity="0.8"/>
        <!-- Thick Cylindrical Glass Jar Body -->
        <rect x="12" y="25" width="56" height="78" rx="12" fill="url(#jarBody)" stroke="#10B981" stroke-width="1.8"/>
        <!-- Inner Glow & Glass Base Layer -->
        <rect x="16" y="90" width="48" height="9" rx="4" fill="#059669" opacity="0.35"/>
        <!-- Modern Eco Minimalist Label -->
        <rect x="18" y="42" width="44" height="38" rx="4" fill="#FFFFFF" opacity="0.92" stroke="#A7F3D0" stroke-width="1"/>
        <text x="24" y="58" font-size="8.5" font-weight="900" fill="#065F46" font-family="-apple-system, sans-serif">REUSE</text>
        <text x="24" y="69" font-size="6.5" font-weight="700" fill="#059669" font-family="-apple-system, sans-serif">PURE GLASS</text>
        <circle cx="51" cy="62" r="5" fill="#ECFDF5" stroke="#10B981" stroke-width="1"/>
        <text x="48.5" y="65" font-size="7" font-weight="900" fill="#10B981" font-family="-apple-system, sans-serif">∞</text>
        <!-- Specular Glass Light Reflection -->
        <path d="M 18 32 L 18 96" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
        <path d="M 23 35 L 23 93" stroke="#FFFFFF" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>
    </g>

    <!-- ITEM D: Aluminum / Metal Cylinder with Pull-Ring (Bottom-Left, ~ (95, 335)) -->
    <g transform="translate(80, 320) rotate(16 30 45)" filter="url(#itemShadow)">
        <!-- Metallic Base Gradients -->
        <ellipse cx="30" cy="85" rx="22" ry="7" fill="#064E3B" opacity="0.14"/>
        <!-- Can Body -->
        <rect x="12" y="20" width="36" height="58" rx="6" fill="#E2E8F0" stroke="#94A3B8" stroke-width="1.2"/>
        <!-- Printed Green Wrap / Eco Brand -->
        <rect x="12" y="32" width="36" height="34" fill="#15803D" opacity="0.88"/>
        <text x="17" y="52" font-size="7" font-weight="800" fill="#FFFFFF" font-family="-apple-system, sans-serif">INFINITE</text>
        <text x="20" y="60" font-size="5.5" font-weight="600" fill="#A7F3D0" font-family="-apple-system, sans-serif">ALUMINUM</text>
        <!-- Can Top Lip and Pull-Ring -->
        <ellipse cx="30" cy="20" rx="18" ry="6" fill="#CBD5E1" stroke="#64748B" stroke-width="1"/>
        <ellipse cx="30" cy="20" rx="12" ry="4" fill="#94A3B8"/>
        <circle cx="30" cy="20" r="3" fill="#E2E8F0"/>
        <!-- Metallic Highlight Line -->
        <line x1="16" y1="22" x2="16" y2="76" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
    </g>

    <!-- 6. Foreground Circular Economy Orbit Elements & Accents -->
    <!-- Circular Arrow 1 (Clockwise Loop Top) -->
    <g transform="rotate(-15 300 255)">
        <path d="M 230 148 A 190 75 0 0 1 370 148" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
        <polygon points="372,141 385,150 372,159" fill="#10B981"/>
    </g>
    <!-- Circular Arrow 2 (Return Loop Bottom) -->
    <g transform="rotate(-15 300 255)">
        <path d="M 370 362 A 190 75 0 0 1 230 362" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
        <polygon points="228,369 215,360 228,351" fill="#10B981"/>
    </g>

    <!-- Lush Botanical Leaves Growing on Orbit -->
    <g transform="translate(195, 230) rotate(-35)">
        <path d="M 0 0 C 18 -28 50 -24 56 0 C 50 24 18 28 0 0 Z" fill="url(#leafGrad)"/>
        <path d="M 0 0 Q 28 -2 56 0" stroke="#DCFCE7" stroke-width="1.5" fill="none"/>
    </g>
    <g transform="translate(385, 215) rotate(40)">
        <path d="M 0 0 C 18 -28 50 -24 56 0 C 50 24 18 28 0 0 Z" fill="url(#leafGrad)"/>
        <path d="M 0 0 Q 28 -2 56 0" stroke="#DCFCE7" stroke-width="1.5" fill="none"/>
    </g>
    <g transform="translate(290, 395) rotate(15)">
        <path d="M 0 0 C 14 -22 38 -18 44 0 C 38 18 14 22 0 0 Z" fill="url(#leafGrad)"/>
        <path d="M 0 0 Q 22 -2 44 0" stroke="#DCFCE7" stroke-width="1.2" fill="none"/>
    </g>

    <!-- Glowing Stars / Sparkles (Representing Spark of Innovation) -->
    <!-- Sparkle 1 -->
    <g transform="translate(425, 205)">
        <path d="M 0 -8 Q 0 0 8 0 Q 0 0 0 8 Q 0 0 -8 0 Q 0 0 0 -8 Z" fill="#34D399"/>
        <circle cx="0" cy="0" r="2" fill="#FFFFFF"/>
    </g>
    <!-- Sparkle 2 -->
    <g transform="translate(165, 185)">
        <path d="M 0 -6 Q 0 0 6 0 Q 0 0 0 6 Q 0 0 -6 0 Q 0 0 0 -6 Z" fill="#38BDF8"/>
        <circle cx="0" cy="0" r="1.5" fill="#FFFFFF"/>
    </g>
    <!-- Sparkle 3 -->
    <g transform="translate(380, 345)">
        <path d="M 0 -7 Q 0 0 7 0 Q 0 0 0 7 Q 0 0 -7 0 Q 0 0 0 -7 Z" fill="#FACC15"/>
        <circle cx="0" cy="0" r="1.5" fill="#FFFFFF"/>
    </g>
    <!-- Sparkle 4 -->
    <g transform="translate(195, 325)">
        <path d="M 0 -5 Q 0 0 5 0 Q 0 0 0 5 Q 0 0 -5 0 Q 0 0 0 -5 Z" fill="#10B981"/>
    </g>
</svg>'''

# Validate XML
try:
    ET.fromstring(svg_markup)
    print("SUCCESS: SVG is valid XML!")
except Exception as e:
    print("ERROR parsing SVG:", e)
