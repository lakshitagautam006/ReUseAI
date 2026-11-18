"""ReUseAI – Intelligent Waste-to-Resource Matcher
Streamlit Application Frontend (Phase 5 – Eco Green Dashboard).
Subsystem 1: Computer Vision & Material Perception Engine.
Theme: Forest Green (#14532D), Emerald Green (#16A34A), Mint Accent (#A7F3D0), Off-White (#F8FAF7).
"""

import streamlit as st
from PIL import Image
import base64
import json
from datetime import datetime
from src.database.repository import save_analysis, get_all_analyses, get_analysis_by_id

from src.config import (
    GROQ_API_KEY,
    DEFAULT_MODEL,
    MAX_IMAGE_DIMENSION,
    MAX_FILE_SIZE_MB,
    SUPPORTED_IMAGE_TYPES,
    is_api_configured,
)
from src.services.analyzer import WasteAnalyzer
from src.utils.image_processor import (
    get_image_metadata,
    validate_image,
    preprocess_image,
    process_uploaded_image,
)
from src.utils.sample_generator import (
    create_sample_plastic_bottle,
    create_sample_cardboard_box,
    create_sample_glass_jar,
    create_sample_aluminum_can,
)


# -----------------------------------------------------------------------------
# Streamlit Page Setup & Custom Eco Green Theme Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ReUseAI – Intelligent Waste-to-Resource Matcher",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Vector Sustainability Artwork for Homepage Hero (3D Earth, Circular Economy Orbit, Floating Recyclables)
HERO_SVG_MARKUP = """<svg viewBox="0 0 600 520" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
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
</svg>"""


def render_svg_as_image(svg_content: str, max_height: str = "420px") -> str:
    """Safely convert SVG XML into a self-contained base64 data URI img tag.
    Completely eliminates markdown code-block parsing and raw XML text exposure.
    """
    clean_svg = svg_content.strip()
    b64_svg = base64.b64encode(clean_svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64_svg}" alt="Sustainability Illustration" style="width: 100%; max-height: {max_height}; object-fit: contain; display: block; margin: auto;" />'


# Premium Eco Green Theme Stylesheet
st.markdown(
    """
    <style>
        /* -------------------------------------------------------------------------
           1. Global Color System & Typography
           ------------------------------------------------------------------------- */
        :root {
            --primary: #14532D;         /* Dark Forest Green */
            --secondary: #16A34A;       /* Vibrant Emerald Green */
            --accent: #A7F3D0;          /* Mint Green Accent */
            --accent-soft: #ECFDF5;     /* Soft Mint Background */
            --bg-main: #F8FAF7;         /* Soft Off-White */
            --card-bg: #FFFFFF;         /* Pure White */
            --text-dark: #1F2937;       /* Dark Charcoal */
            --text-muted: #6B7280;      /* Muted Slate Grey */
            --border-light: #E5E7EB;    /* Light Neutral Border */
            --border-green: #D1FAE5;    /* Subtle Mint Border */
            --sidebar-bg: #0F381E;      /* Rich Dark Forest */
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
            --shadow-md: 0 4px 14px rgba(20, 83, 45, 0.07), 0 1px 3px rgba(0, 0, 0, 0.03);
            --shadow-lg: 0 10px 25px -3px rgba(20, 83, 45, 0.12), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }

        /* Overall body & main container */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: var(--text-dark);
            background-color: var(--bg-main);
        }

        .main .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3.5rem;
            max-width: 1200px;
        }

        /* -------------------------------------------------------------------------
           2. Sidebar: Dark Forest Green Premium Sidebar
           ------------------------------------------------------------------------- */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0D331B 0%, #14532D 60%, #0F381E 100%) !important;
            border-right: 1px solid rgba(167, 243, 208, 0.15);
        }

        [data-testid="stSidebar"] * {
            color: #F3F4F6 !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.12) !important;
            margin: 1rem 0;
        }

        .sidebar-brand-container {
            padding: 0.5rem 0.25rem 0.85rem 0.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1.25rem;
        }
        .sidebar-brand-title {
            font-size: 1.45rem;
            font-weight: 800;
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .sidebar-brand-title span {
            color: #A7F3D0 !important;
        }
        .sidebar-tagline {
            font-size: 0.78rem;
            font-weight: 600;
            color: #A7F3D0 !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 0.25rem;
        }

        /* Radio Navigation Menu in Sidebar */
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
            gap: 0.35rem;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 0.55rem 0.85rem;
            cursor: pointer;
            transition: all 0.18s ease-in-out;
            margin-bottom: 0.25rem;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            background-color: rgba(167, 243, 208, 0.15) !important;
            border-color: rgba(167, 243, 208, 0.3) !important;
            transform: translateX(3px);
        }

        /* Sidebar Motivational Quote Card */
        .sidebar-eco-card {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(167, 243, 208, 0.2);
            border-radius: 10px;
            padding: 0.9rem;
            margin-top: 1rem;
            font-size: 0.82rem;
            line-height: 1.45;
        }
        .sidebar-eco-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: #A7F3D0 !important;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* -------------------------------------------------------------------------
           3. Core Card & Typography Components
           ------------------------------------------------------------------------- */
        .page-header {
            margin-bottom: 1.75rem;
        }
        .page-title {
            font-size: 1.85rem;
            font-weight: 800;
            color: var(--primary);
            letter-spacing: -0.025em;
            margin-bottom: 0.35rem;
        }
        .page-subtitle {
            font-size: 0.98rem;
            color: var(--text-muted);
            line-height: 1.5;
            max-width: 820px;
        }

        /* Standard Eco Card */
        .eco-card {
            background: var(--card-bg);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.22s ease-in-out;
            height: 100%;
            margin-bottom: 1rem;
        }
        .eco-card:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-md);
            border-color: #CBD5E1;
        }

        /* Feature Card on Home */
        .feature-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.35rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.22s ease-in-out;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-md);
            border-color: #86EFAC;
        }
        .feature-icon-wrapper {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            background: #ECFDF5;
            color: #15803D;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            margin-bottom: 0.9rem;
            border: 1px solid #A7F3D0;
        }
        .feature-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.45rem;
        }
        .feature-desc {
            font-size: 0.88rem;
            color: var(--text-muted);
            line-height: 1.45;
            margin-bottom: 1rem;
            flex-grow: 1;
        }
        .feature-cta {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--secondary);
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            text-decoration: none;
        }

        /* Workflow Steps */
        .workflow-step {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem 1.1rem;
            height: 100%;
            position: relative;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease-in-out;
        }
        .workflow-step:hover {
            border-color: #86EFAC;
            transform: translateY(-2px);
        }
        .workflow-step-badge {
            font-size: 0.75rem;
            font-weight: 800;
            background: #ECFDF5;
            color: #15803D;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 0.6rem;
            border: 1px solid #A7F3D0;
            letter-spacing: 0.05em;
        }
        .workflow-step-title {
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.35rem;
        }
        .workflow-step-desc {
            font-size: 0.84rem;
            color: var(--text-muted);
            line-height: 1.45;
        }

        /* Metric Dashboard Cards */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.15rem 1.25rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 0.85rem;
            border-top: 4px solid var(--secondary);
            transition: all 0.2s ease-in-out;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.35rem;
        }
        .metric-label {
            font-size: 0.76rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1.25;
            margin-bottom: 0.35rem;
        }
        .metric-subtext {
            font-size: 0.78rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        /* Project / Suggestion Cards */
        .project-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid var(--secondary);
            border-radius: 10px;
            padding: 1.35rem;
            margin-bottom: 1.1rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease-in-out;
        }
        .project-card:hover {
            box-shadow: var(--shadow-md);
            border-left-color: var(--primary);
        }
        .project-title {
            font-size: 1.12rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.35rem;
        }
        .project-meta-pill {
            display: inline-block;
            font-size: 0.78rem;
            background: #F1F5F9;
            color: #334155;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            margin-right: 0.4rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }

        /* -------------------------------------------------------------------------
           4. Streamlit Interactive Elements Overrides
           ------------------------------------------------------------------------- */
        .stButton > button {
            background-color: var(--primary) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.6rem 1.4rem !important;
            box-shadow: 0 2px 4px rgba(20, 83, 45, 0.2) !important;
            transition: all 0.2s ease-in-out !important;
        }
        .stButton > button:hover {
            background-color: var(--secondary) !important;
            color: #FFFFFF !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 10px rgba(22, 163, 74, 0.3) !important;
        }

        /* File Uploader Container */
        [data-testid="stFileUploader"] {
            border: 2px dashed #86EFAC !important;
            border-radius: 12px !important;
            background-color: #F8FAF7 !important;
            padding: 1.25rem 1rem !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #16A34A !important;
            background-color: #ECFDF5 !important;
        }

        /* Accordion / Expander */
        .streamlit-expanderHeader {
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            color: var(--primary) !important;
            border-radius: 8px !important;
            background-color: #F8FAF7 !important;
        }

        /* Badges */
        .api-badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .api-badge-ok {
            background-color: #DCFCE7;
            color: #14532D;
            border: 1px solid #86EFAC;
        }
        .api-badge-warn {
            background-color: #FEF3C7;
            color: #92400E;
            border: 1px solid #FCD34D;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Navigation State & Programmatic Routing
# -----------------------------------------------------------------------------
NAV_PAGES = ["Home","Analyze Waste","Analysis Results","Analysis History","Impact Dashboard","About"]

# Handle safe programmatic navigation before widgets render
if "pending_page" in st.session_state and st.session_state["pending_page"]:
    st.session_state["selected_page"] = st.session_state.pop("pending_page")

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Home"

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "uploaded_image" not in st.session_state:
    st.session_state["uploaded_image"] = None

if "preprocessed_image" not in st.session_state:
    st.session_state["preprocessed_image"] = None

if "image_metadata" not in st.session_state:
    st.session_state["image_metadata"] = {}

if "image_filename" not in st.session_state:
    st.session_state["image_filename"] = ""

if "image_validation_error" not in st.session_state:
    st.session_state["image_validation_error"] = None

if "last_processed_file_id" not in st.session_state:
    st.session_state["last_processed_file_id"] = None


def navigate_to(page_name: str):
    """Safely queue page navigation and trigger rerun without mutating instantiated widgets."""
    st.session_state["pending_page"] = page_name
    st.rerun()


# -----------------------------------------------------------------------------
# Left Sidebar: Dark Forest Green Dashboard Navigation & Secure Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-container">
            <div class="sidebar-brand-title">
                ♻️ ReUse<span>AI</span>
            </div>
            <div class="sidebar-tagline">Analyze • Reuse • Make Impact</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean Radio Menu bound to session state
    current_page = st.radio(
        "Navigation",
        options=NAV_PAGES,
        key="selected_page",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Sustainability Motivational Callout Card
    st.markdown(
        """
        <div class="sidebar-eco-card">
            <div class="sidebar-eco-badge">Circular Mindset</div>
            <em>"Every discard is a high-value resource waiting for intelligent direction."</em>
            <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #A7F3D0 !important;">
                🌍 SDG 12: Responsible Consumption
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("**ReUseAI Platform:** Phase 5 Eco Green Redesign  \n*Subsystem 1: Computer Vision & Material Perception*")


# -----------------------------------------------------------------------------
# Secure Backend AI Configuration (Loaded from environment variables)
# -----------------------------------------------------------------------------
effective_api_key = GROQ_API_KEY
has_active_key = bool(effective_api_key and not effective_api_key.startswith("your_"))
model_choice = DEFAULT_MODEL


# -----------------------------------------------------------------------------
# PAGE 1: Home Dashboard
# -----------------------------------------------------------------------------
if current_page == "Home":
    # Hero Section: Two-Column Responsive Layout
    col_hero_text, col_hero_art = st.columns([1.1, 0.9], gap="large")

    with col_hero_text:
        st.markdown(
            """
            <div style="padding-top: 1rem;">
                <div style="display: inline-block; background-color: #ECFDF5; color: #15803D; font-size: 0.8rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 20px; border: 1px solid #A7F3D0; margin-bottom: 0.9rem; text-transform: uppercase; letter-spacing: 0.06em;">
                    🌱 Intelligent Circular Economy
                </div>
                <h1 style="font-size: 2.75rem; font-weight: 900; color: #14532D; line-height: 1.15; margin-bottom: 0.4rem; letter-spacing: -0.03em;">
                    ReUseAI
                </h1>
                <h3 style="font-size: 1.45rem; font-weight: 700; color: #16A34A; margin-bottom: 1.1rem; letter-spacing: -0.01em;">
                    Turn Waste into Worth
                </h3>
                <p style="font-size: 1.05rem; color: #4B5563; line-height: 1.65; margin-bottom: 1.6rem; max-width: 540px;">
                    Analyze any waste material and discover smart ways to reuse, upcycle, or recycle it for a sustainable future.
                    Our vision AI identifies material grades, evaluates physical conditions, and connects discarded resources with high-value secondary applications.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Prominent CTA Button
        if st.button("🌱 Analyze Waste", use_container_width=False):
            navigate_to("Analyze Waste")

    with col_hero_art:
        # Streamlit-compatible Base64 SVG Illustration: Zero raw XML or code tags displayed
        st.markdown(render_svg_as_image(HERO_SVG_MARKUP, max_height="420px"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Four Feature Cards Section
    # -------------------------------------------------------------------------
    st.markdown("### Core Capabilities")
    st.markdown(
        '<div class="page-subtitle">Designed to transform post-consumer discards into active, productive assets.</div>',
        unsafe_allow_html=True,
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(
            """
            <div class="feature-card">
                <div>
                    <div class="feature-icon-wrapper">🔬</div>
                    <div class="feature-title">AI Waste Analysis</div>
                    <div class="feature-desc">Upload an image and get instant material identification, resin codes, and physical diagnostics.</div>
                </div>
                <div class="feature-cta">Identify Material →</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            """
            <div class="feature-card">
                <div>
                    <div class="feature-icon-wrapper">💡</div>
                    <div class="feature-title">Smart Suggestions</div>
                    <div class="feature-desc">Discover practical reuse and upcycling ideas with step-by-step actionable fabrication instructions.</div>
                </div>
                <div class="feature-cta">Explore Ideas →</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            """
            <div class="feature-card">
                <div>
                    <div class="feature-icon-wrapper">🤝</div>
                    <div class="feature-title">Resource Matching</div>
                    <div class="feature-desc">Find potential secondary users, makerspaces, and verified circular recyclers for your materials.</div>
                </div>
                <div class="feature-cta">Match Users →</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f4:
        st.markdown(
            """
            <div class="feature-card">
                <div>
                    <div class="feature-icon-wrapper">📈</div>
                    <div class="feature-title">Track Your Impact</div>
                    <div class="feature-desc">Monitor environmental impact, carbon offset potential, and landfill diversion as a future feature.</div>
                </div>
                <div class="feature-cta">Preview Metrics →</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # "How It Works" Section with 4 Stages
    # -------------------------------------------------------------------------
    st.markdown("### How It Works")
    st.markdown(
        '<div class="page-subtitle">A seamless four-stage progression from scrap item to circular value creation.</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            """
            <div class="workflow-step">
                <div class="workflow-step-badge">STAGE 01</div>
                <div class="workflow-step-title">Upload Waste Image</div>
                <div class="workflow-step-desc">Photograph any discarded container, scrap packaging, or item and upload to our perception pipeline.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            """
            <div class="workflow-step">
                <div class="workflow-step-badge">STAGE 02</div>
                <div class="workflow-step-title">Let AI Analyze Material</div>
                <div class="workflow-step-desc">Vision AI classifies specific polymers, evaluates surface contamination, and grades recyclability.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            """
            <div class="workflow-step">
                <div class="workflow-step-badge">STAGE 03</div>
                <div class="workflow-step-title">Discover Reuse Ideas</div>
                <div class="workflow-step-desc">Receive tailored 4–6 step instructions to transform discards into functional planters, organizers, or crafts.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            """
            <div class="workflow-step">
                <div class="workflow-step-badge">STAGE 04</div>
                <div class="workflow-step-title">Explore Matching</div>
                <div class="workflow-step-desc">Review scored matches for local makerspaces, organic farms, foundries, or packaging converters.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# PAGE 2: Analyze Waste
# -----------------------------------------------------------------------------
elif current_page == "Analyze Waste":
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">🔍 Analyze Waste Material</div>
            <div class="page-subtitle">
                Upload a photograph of any discarded item, packaging, or scrap material to execute real-time computer vision analysis,
                evaluate physical condition, and generate actionable reuse pathways.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_upload, col_preview = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("##### 📤 Image Upload")
        uploaded_file = st.file_uploader(
            "Select or drop an image file (JPG, JPEG, PNG, or WEBP)",
            type=SUPPORTED_IMAGE_TYPES,
            help=f"Accepts JPG, PNG, and WEBP up to {MAX_FILE_SIZE_MB}MB. Preprocessing standardizes colors, normalizes EXIF orientation, and constrains dimensions to {MAX_IMAGE_DIMENSION}px.",
        )

        if uploaded_file is not None:
            file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("last_processed_file_id") != file_signature:
                with st.spinner("Validating and preprocessing image..."):
                    preprocessed, original, meta, err_msg = process_uploaded_image(
                        uploaded_file,
                        max_dim=MAX_IMAGE_DIMENSION,
                        max_file_size_mb=MAX_FILE_SIZE_MB,
                    )
                    if err_msg:
                        st.session_state["uploaded_image"] = None
                        st.session_state["preprocessed_image"] = None
                        st.session_state["image_metadata"] = {}
                        st.session_state["image_filename"] = uploaded_file.name
                        st.session_state["image_validation_error"] = err_msg
                    else:
                        st.session_state["uploaded_image"] = original
                        st.session_state["preprocessed_image"] = preprocessed
                        st.session_state["image_metadata"] = meta
                        st.session_state["image_filename"] = uploaded_file.name
                        st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = file_signature
        else:
            if st.session_state.get("last_processed_file_id") is not None and not st.session_state.get("is_sample_image"):
                st.session_state["uploaded_image"] = None
                st.session_state["preprocessed_image"] = None
                st.session_state["image_metadata"] = {}
                st.session_state["image_filename"] = ""
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = None

        if st.session_state.get("image_validation_error"):
            st.error(f"❌ {st.session_state['image_validation_error']}")
        elif st.session_state.get("uploaded_image") is not None:
            st.success("✅ Image validated and preprocessed successfully.")

        # Quick Test Sample Shortcuts
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### ⚡ Quick Test Sample Discards")
        st.caption("Don't have an image ready? Test instantly with synthetic clean sample discards:")

        sample_col1, sample_col2 = st.columns(2)
        with sample_col1:
            if st.button("🧴 Plastic Bottle (PET)", use_container_width=True):
                sample_img = create_sample_plastic_bottle()
                st.session_state["uploaded_image"] = sample_img
                st.session_state["preprocessed_image"] = preprocess_image(sample_img)
                st.session_state["image_metadata"] = get_image_metadata(sample_img)
                st.session_state["image_filename"] = "sample_pet_bottle.jpg"
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = "sample_pet_bottle"
                st.session_state["is_sample_image"] = True
                st.rerun()

            if st.button("📦 Cardboard Box", use_container_width=True):
                sample_img = create_sample_cardboard_box()
                st.session_state["uploaded_image"] = sample_img
                st.session_state["preprocessed_image"] = preprocess_image(sample_img)
                st.session_state["image_metadata"] = get_image_metadata(sample_img)
                st.session_state["image_filename"] = "sample_cardboard_box.jpg"
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = "sample_cardboard_box"
                st.session_state["is_sample_image"] = True
                st.rerun()

        with sample_col2:
            if st.button("🫙 Glass Jar", use_container_width=True):
                sample_img = create_sample_glass_jar()
                st.session_state["uploaded_image"] = sample_img
                st.session_state["preprocessed_image"] = preprocess_image(sample_img)
                st.session_state["image_metadata"] = get_image_metadata(sample_img)
                st.session_state["image_filename"] = "sample_glass_jar.jpg"
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = "sample_glass_jar"
                st.session_state["is_sample_image"] = True
                st.rerun()

            if st.button("🥫 Aluminum Can", use_container_width=True):
                sample_img = create_sample_aluminum_can()
                st.session_state["uploaded_image"] = sample_img
                st.session_state["preprocessed_image"] = preprocess_image(sample_img)
                st.session_state["image_metadata"] = get_image_metadata(sample_img)
                st.session_state["image_filename"] = "sample_aluminum_can.jpg"
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = "sample_aluminum_can"
                st.session_state["is_sample_image"] = True
                st.rerun()

        # Action Button
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 Analyze Waste", use_container_width=True)

    with col_preview:
        st.markdown("##### 🖼️ Image Preview & Diagnostics")
        if st.session_state.get("uploaded_image") is not None:
            img = st.session_state["uploaded_image"]
            prep = st.session_state.get("preprocessed_image")
            meta = st.session_state.get("image_metadata", {})
            st.image(img, caption=f"Active Selection: {st.session_state['image_filename']}", use_container_width=True)

            orig_w, orig_h = img.size
            prep_w = prep.width if prep else orig_w
            prep_h = prep.height if prep else orig_h
            is_resized = meta.get("is_resized", False)
            fmt = meta.get("format", getattr(img, "format", "Image"))

            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem; font-size: 0.84rem; color: #4B5563; margin-top: 0.5rem;">
                    <strong>Original Resolution:</strong> {orig_w} × {orig_h} px &nbsp;|&nbsp;
                    <strong>Preprocessed:</strong> {prep_w} × {prep_h} px <br>
                    <strong>Format:</strong> {fmt} &nbsp;|&nbsp;
                    <strong>Color Mode:</strong> {img.mode} ➔ RGB &nbsp;|&nbsp;
                    <strong>Aspect Ratio:</strong> {meta.get('aspect_ratio', 'N/A')}
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif st.session_state.get("image_validation_error"):
            st.warning("⚠️ Invalid or corrupted file uploaded. Please upload a valid image.")
        else:
            st.info("ℹ️ No image selected. Please drop an image in the upload area or click one of the quick test sample buttons.")

    st.markdown("---")

    # Execution Feedback & Analysis Trigger
    if analyze_btn:
        if st.session_state.get("image_validation_error"):
            st.error(f"❌ Cannot analyze invalid image: {st.session_state['image_validation_error']}")
        elif st.session_state.get("uploaded_image") is None:
            st.warning("⚠️ Please select an image file first before clicking 'Analyze Waste'.")
        elif not has_active_key:
            st.error(
                "⚠️ **Vision API Key Required**  \n\n"
                "To perform genuine AI material recognition and upcycling analysis, please configure your "
                "Groq API key in the `.env` file.  \n\n"
                "*Note: Simulated or fabricated AI results are disabled to ensure true data integrity.*"
            )
        else:
            status_container = st.status("🚀 Running waste material perception & matching...", expanded=True)
            try:
                def on_progress(stage: str, msg: str):
                    status_container.write(f"• {msg}")

                analyzer = WasteAnalyzer(api_key=effective_api_key, model_name=model_choice)
                image_to_analyze = st.session_state.get("preprocessed_image") or st.session_state["uploaded_image"]
                result = analyzer.analyze(
                    image_to_analyze,
                    progress_callback=on_progress,
                )
                
                st.session_state["analysis_result"] = result

                # Save analysis to PostgreSQL
                try:
                    analysis_id = save_analysis(result)
                    st.session_state["saved_analysis_id"] = analysis_id
                    st.session_state["database_save_status"] = {
                        "success": True,
                        "analysis_id": analysis_id,
                        "message": f"Analysis saved successfully! ID: {analysis_id}",
                    }

                except Exception as db_error:
                    st.session_state["database_save_status"] = {
                        "success": False,
                        "analysis_id": None,
                        "message": f"Database saving failed: {db_error}",
                    }

                status_container.update(
                    label="Analysis completed successfully!",
                    state="complete",
                    expanded=False,
                )

                navigate_to("Analysis Results")
            except Exception as err:
                status_container.update(
                    label="❌ Analysis Failed",
                    state="error",
                    expanded=True,
                )
                st.error(f"Analysis failed: {str(err)}")
    else:
        if st.session_state["analysis_result"] is not None:
            st.success("✅ Analysis results are ready for the current image.")
            if st.button("📊 View Analysis Results →"):
                navigate_to("Analysis Results")


# -----------------------------------------------------------------------------
# PAGE 3: Material Analysis Results (Enhanced Eco Green Results Interface)
# -----------------------------------------------------------------------------
elif current_page == "Analysis Results":
    st.markdown(
        """
        <div class="page-header">
            <div style="display: inline-block; background-color: #ECFDF5; color: #15803D; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 12px; border: 1px solid #A7F3D0; margin-bottom: 0.5rem; text-transform: uppercase;">
                Verified AI Perception
            </div>
            <div class="page-title">📊 Material Analysis Results</div>
            <div class="page-subtitle">
                Comprehensive material identification, physical state diagnostics, practical upcycling instructions, and scored circular matches.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Database save status
    db_status = st.session_state.get("database_save_status")

    if db_status:
        if db_status["success"]:
            st.success(f"💾 {db_status['message']}")
        else:
            st.warning(f"⚠️ {db_status['message']}")

    result = st.session_state.get("analysis_result")

    if result is None:
        st.info(
            "ℹ️ No waste material has been analyzed yet. "
            "Please upload an image and click **Analyze Waste** in the 'Analyze Waste' section to view results."
        )
        if st.button("← Go to Analyze Waste"):
            navigate_to("Analyze Waste")
    else:
        mat = result.material

        # Sleek Performance Timings Banner
        timings = result.metadata.get("timings", {})
        if timings:
            t_total = timings.get("total_seconds", 0)
            t_prep = timings.get("preprocessing_seconds", 0)
            t_api = timings.get("api_request_seconds", 0)
            t_parse = timings.get("parsing_seconds", 0)
            t_reuse = timings.get("reuse_generation_seconds", 0)
            st.markdown(
                f"""
                <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 10px; padding: 0.65rem 1.1rem; margin-bottom: 1.5rem; font-size: 0.84rem; color: #14532D; display: flex; flex-wrap: wrap; gap: 1.25rem; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                    <span>⚡ <strong>Execution Total:</strong> {t_total}s</span>
                    <span>• <strong>Preprocessing:</strong> {t_prep}s</span>
                    <span>• <strong>Groq Vision AI:</strong> {t_api}s</span>
                    <span>• <strong>Schema Parser:</strong> {t_parse}s</span>
                    <span>• <strong>Matching Engines:</strong> {t_reuse}s</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---------------------------------------------------------------------
        # 1. Four Core Metric KPI Cards with Eco Green Styling
        # ---------------------------------------------------------------------
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Material Name</span>
                        <span>📦</span>
                    </div>
                    <div class="metric-value">{mat.material_type}</div>
                    <div class="metric-subtext">Resin / Subtype: {mat.sub_category}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Waste Category</span>
                        <span>🏷️</span>
                    </div>
                    <div class="metric-value">{mat.primary_category}</div>
                    <div class="metric-subtext">Classification: Solid Waste Stream</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Physical Condition</span>
                        <span>🔍</span>
                    </div>
                    <div class="metric-value">{mat.physical_condition}</div>
                    <div class="metric-subtext">Cleanliness: {mat.cleanliness_level}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k4:
            rec_badge_color = "#15803D" if mat.recyclability_score >= 70 else "#D97706"
            rec_badge_bg = "#DCFCE7" if mat.recyclability_score >= 70 else "#FEF3C7"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Recyclability Index</span>
                        <span>♻️</span>
                    </div>
                    <div class="metric-value">{mat.recyclability_score} <span style="font-size: 0.9rem; font-weight: 600; color: #6B7280;">/ 100</span></div>
                    <span style="background-color: {rec_badge_bg}; color: {rec_badge_color}; font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px;">
                        {'High Circular Viability' if mat.recyclability_score >= 70 else 'Condition Restricted'}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Executive Summary Callout
        if result.summary:
            st.markdown(
                f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 3px solid #16A34A; border-radius: 8px; padding: 0.9rem 1.1rem; margin-top: 0.5rem; margin-bottom: 1.5rem; font-size: 0.92rem; color: #374151; line-height: 1.5;">
                    <strong>Perception Diagnostics:</strong> {result.summary}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---------------------------------------------------------------------
        # 2. Detailed Material Classification & Handling Guidance
        # ---------------------------------------------------------------------
        c_left, c_right = st.columns(2, gap="medium")
        with c_left:
            st.markdown("##### 🔬 Detailed Material Classification")
            features_html = (
                "".join([f"<li style='margin-bottom: 0.25rem;'>✓ {feat}</li>" for feat in mat.detected_features])
                if mat.detected_features
                else "<li>Standard surface geometry detected</li>"
            )
            st.markdown(
                f"""
                <div class="eco-card" style="margin-bottom: 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.5rem;">
                        <span style="font-size: 0.9rem; font-weight: 700; color: #14532D;">Specific Sub-grade</span>
                        <span style="background: #F1F5F9; color: #334155; font-size: 0.8rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px;">{mat.sub_category}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.5rem;">
                        <span style="font-size: 0.9rem; font-weight: 700; color: #14532D;">Confidence Rating</span>
                        <span style="background: #DCFCE7; color: #14532D; font-size: 0.8rem; font-weight: 800; padding: 0.2rem 0.55rem; border-radius: 6px;">{mat.confidence_score * 100:.1f}% Match</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.5rem;">
                        <span style="font-size: 0.9rem; font-weight: 700; color: #14532D;">Cleanliness Level</span>
                        <span style="background: #F8FAF7; color: #475569; font-size: 0.8rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #E2E8F0;">{mat.cleanliness_level}</span>
                    </div>
                    <div style="font-size: 0.86rem; color: #4B5563;">
                        <strong style="color: #1F2937;">Observed Visual Features:</strong>
                        <ul style="margin-top: 0.4rem; padding-left: 1.1rem; list-style-type: none;">
                            {features_html}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_right:
            st.markdown("##### 🛡️ Safety and Handling Protocols")
            hazards_html = (
                "".join([f"<li style='margin-bottom: 0.25rem;'>⚠️ {h}</li>" for h in mat.hazardous_elements])
                if mat.hazardous_elements
                else "<li style='color: #15803D;'>✅ No immediate chemical, biological, or thermal hazards detected</li>"
            )
            prep_html = (
                "".join([f"<li style='margin-bottom: 0.25rem;'>🧼 {p}</li>" for p in result.handling_instructions])
                if result.handling_instructions
                else "<li>Standard workshop pre-cleaning and dust removal</li>"
            )
            st.markdown(
                f"""
                <div class="eco-card" style="margin-bottom: 1.25rem;">
                    <div style="margin-bottom: 0.9rem;">
                        <strong style="color: #1F2937; font-size: 0.88rem;">Hazard Evaluation:</strong>
                        <ul style="margin-top: 0.35rem; padding-left: 0.5rem; font-size: 0.85rem; color: #4B5563; list-style-type: none;">
                            {hazards_html}
                        </ul>
                    </div>
                    <div>
                        <strong style="color: #1F2937; font-size: 0.88rem;">Recommended Preparation Protocol:</strong>
                        <ul style="margin-top: 0.35rem; padding-left: 0.5rem; font-size: 0.85rem; color: #4B5563; list-style-type: none;">
                            {prep_html}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 3. Reuse and Upcycling Suggestions (Separated Visual Sections)
        # ---------------------------------------------------------------------
        st.markdown("### 💡 Practical Repurposing & Upcycling Pathways")
        st.markdown(
            '<div class="page-subtitle">Actionable sequential procedures designed to prolong the lifecycle of this material before disposal.</div>',
            unsafe_allow_html=True,
        )

        all_suggestions = result.reuse_suggestions or []

        # Partition suggestions into Direct Reuse vs Upcycling & Conversion
        reuse_opps = [
            s for s in all_suggestions
            if any(k in s.category.lower() for k in ["reuse", "storage", "organization", "pantry", "gardening"])
            or any(k in s.title.lower() for k in ["jar", "storage", "pantry", "pot", "planter", "caddy"])
        ]
        upcycle_opps = [s for s in all_suggestions if s not in reuse_opps]

        # Ensure balanced distribution if partitioning left one set empty
        if not reuse_opps and upcycle_opps:
            reuse_opps = [upcycle_opps[0]]
            upcycle_opps = upcycle_opps[1:]
        elif not upcycle_opps and len(reuse_opps) > 1:
            upcycle_opps = [reuse_opps[-1]]
            reuse_opps = reuse_opps[:-1]

        # Section A: Direct Reuse Opportunities
        st.markdown("#### A. Direct Reuse Opportunities")
        st.caption("Zero-remelting containment, immediate organizational, and botanical applications:")

        if not reuse_opps:
            st.write("No direct reuse suggestions returned for this specific item.")
        else:
            for idx, sugg in enumerate(reuse_opps, start=1):
                tools_str = ", ".join(sugg.tools_required) if sugg.tools_required else "Standard household tools"
                st.markdown(
                    f"""
                    <div class="project-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.45rem;">
                            <div class="project-title">{idx}. {sugg.title}</div>
                            <span style="background-color: #ECFDF5; color: #15803D; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid #A7F3D0;">
                                Direct Reuse
                            </span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <span class="project-meta-pill">📁 {sugg.category}</span>
                            <span class="project-meta-pill">⚡ {sugg.difficulty} Difficulty</span>
                            <span class="project-meta-pill">⏱️ {sugg.estimated_time}</span>
                            <span class="project-meta-pill">🌱 Carbon Offset: {sugg.carbon_offset_rating}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #4B5563; margin-top: 0.4rem; background: #F8FAF7; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid #E2E8F0;">
                            <strong>Required Tools / Materials:</strong> {tools_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if sugg.step_by_step_guide:
                    with st.expander(f"📋 View Sequential Fabrication Instructions ({len(sugg.step_by_step_guide)} Steps)"):
                        for step_num, step_text in enumerate(sugg.step_by_step_guide, start=1):
                            st.markdown(f"**Step {step_num}:** {step_text}")

                if sugg.environmental_benefit:
                    st.caption(f"🌿 *Eco-Benefit:* {sugg.environmental_benefit}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Section B: Upcycling Suggestions
        st.markdown("#### B. Creative Upcycling & Secondary Conversion")
        st.caption("Value-added mechanical conversions, additive manufacturing, and artisanal crafting:")

        if not upcycle_opps:
            st.write("No additional upcycling suggestions returned.")
        else:
            for idx, sugg in enumerate(upcycle_opps, start=1):
                tools_str = ", ".join(sugg.tools_required) if sugg.tools_required else "Workshop hand tools"
                st.markdown(
                    f"""
                    <div class="project-card" style="border-left-color: #059669;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.45rem;">
                            <div class="project-title">{idx}. {sugg.title}</div>
                            <span style="background-color: #DCFCE7; color: #14532D; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid #86EFAC;">
                                Upcycling Conversion
                            </span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <span class="project-meta-pill">📁 {sugg.category}</span>
                            <span class="project-meta-pill">⚡ {sugg.difficulty} Difficulty</span>
                            <span class="project-meta-pill">⏱️ {sugg.estimated_time}</span>
                            <span class="project-meta-pill">🌱 Carbon Offset: {sugg.carbon_offset_rating}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #4B5563; margin-top: 0.4rem; background: #F8FAF7; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid #E2E8F0;">
                            <strong>Required Tools / Materials:</strong> {tools_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if sugg.step_by_step_guide:
                    with st.expander(f"📋 View Sequential Fabrication Instructions ({len(sugg.step_by_step_guide)} Steps)"):
                        for step_num, step_text in enumerate(sugg.step_by_step_guide, start=1):
                            st.markdown(f"**Step {step_num}:** {step_text}")

                if sugg.environmental_benefit:
                    st.caption(f"🌿 *Eco-Benefit:* {sugg.environmental_benefit}")

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 4. Resource Matching Opportunities (Phase 4 Results)
        # ---------------------------------------------------------------------
        st.markdown("### 🤝 Best Matching Reuse Opportunities")
        st.markdown(
            '<div class="page-subtitle">Matched circular opportunities and potential secondary users based on material compatibility, condition, and reuse applications.</div>',
            unsafe_allow_html=True,
        )

        if not result.matched_opportunities:
            st.info(
                "ℹ️ **No verified reuse opportunities met the compatibility threshold for this item.**  \n"
                "This occurs when materials exhibit severe contamination, hazardous attributes, or lack certified recycling pathways. "
                "Consider municipal hazardous waste drop-off or safe disposal recovery."
            )
        else:
            for idx, opp in enumerate(result.matched_opportunities, start=1):
                badge_color = "#14532D" if opp.match_score >= 85 else ("#15803D" if opp.match_score >= 70 else "#D97706")
                badge_bg = "#DCFCE7" if opp.match_score >= 85 else ("#ECFDF5" if opp.match_score >= 70 else "#FEF3C7")

                st.markdown(
                    f"""
                    <div class="project-card" style="border-left: 5px solid {badge_color};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
                            <div class="project-title" style="margin-bottom: 0;">{idx}. {opp.opportunity_name}</div>
                            <span style="background-color: {badge_bg}; color: {badge_color}; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 800; font-size: 0.88rem; border: 1px solid rgba(0,0,0,0.06);">
                                {opp.match_score:.1f}% Match
                            </span>
                        </div>
                        <div style="margin-bottom: 0.65rem;">
                            <span class="project-meta-pill">🏢 Category: {opp.opportunity_category}</span>
                            <span class="project-meta-pill">🎯 Potential User: {opp.target_user or 'Secondary Processor'}</span>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Visual Match Score Progress Meter
                st.progress(float(min(100.0, max(0.0, opp.match_score))) / 100.0)

                st.markdown(
                    f"""
                        <div style="font-size: 0.88rem; color: #1F2937; margin-top: 0.65rem; line-height: 1.55; background: #F8FAF7; padding: 0.75rem 0.9rem; border-radius: 6px; border: 1px solid #E2E8F0;">
                            <strong>Match Rationale:</strong> {opp.reason}
                        </div>
                        <div style="font-size: 0.88rem; background-color: #ECFDF5; padding: 0.75rem 0.9rem; border-radius: 6px; border: 1px solid #A7F3D0; margin-top: 0.6rem; color: #14532D;">
                            🎯 <strong>Suggested Application:</strong> {opp.suggested_application}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 5. Export Actions & Navigation
        # ---------------------------------------------------------------------
        act_col1, act_col2 = st.columns([1.2, 3.8])
        with act_col1:
            if st.button("← Analyze Another Item"):
                st.session_state["analysis_result"] = None
                st.session_state["uploaded_image"] = None
                st.session_state["preprocessed_image"] = None
                st.session_state["image_metadata"] = {}
                st.session_state["image_filename"] = ""
                st.session_state["image_validation_error"] = None
                st.session_state["last_processed_file_id"] = None
                navigate_to("Analyze Waste")

        with act_col2:
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    label="📥 Export Standard Schema (JSON)",
                    data=result.to_schema_json(indent=2),
                    file_name=f"reuseai_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Exports exact JSON schema: material, waste_type, condition, recyclable, confidence, reuse_ideas",
                )
            with dl_col2:
                st.download_button(
                    label="📥 Export Full Telemetry Report (JSON)",
                    data=result.to_json(indent=2),
                    file_name=f"reuseai_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Exports complete telemetry, material diagnostics, and circular matching data",
                )


# -----------------------------------------------------------------------------
# PAGE 4: Analysis History
# -----------------------------------------------------------------------------
elif current_page == "Analysis History":

    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">📂 Analysis History</div>
            <div class="page-subtitle">
                Browse previously analyzed waste materials and revisit their results.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        analyses = get_all_analyses(limit=50)

        if not analyses:
            st.info("No saved analyses found. Analyze some waste materials to build your history!")
        else:
            st.success(f"Total saved analyses retrieved: {len(analyses)}")

            # Prepare history table
            st.markdown("### 🔎 Search & Filter Analyses")

            search_query = st.text_input(
                "Search by material name",
                placeholder="e.g., Plastic, Glass, Metal...",
            )

            categories = sorted(set(
                item["primary_category"]
                for item in analyses
                if item["primary_category"]
            ))

            conditions = sorted(set(
                item["physical_condition"]
                for item in analyses
                if item["physical_condition"]
            ))

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_category = st.selectbox(
                    "Filter by Category",
                    ["All Categories"] + categories,
                )

            with filter_col2:
                selected_condition = st.selectbox(
                    "Filter by Condition",
                    ["All Conditions"] + conditions,
                )

            # Apply filters
            filtered_analyses = analyses

            if search_query:
                filtered_analyses = [
                    item for item in filtered_analyses
                    if search_query.lower() in str(item["material_type"]).lower()
                ]

            if selected_category != "All Categories":
                filtered_analyses = [
                    item for item in filtered_analyses
                    if item["primary_category"] == selected_category
                ]

            if selected_condition != "All Conditions":
                filtered_analyses = [
                    item for item in filtered_analyses
                    if item["physical_condition"] == selected_condition
                ]

            st.caption(
                f"Showing {len(filtered_analyses)} of {len(analyses)} analyses"
            )

            # Prepare filtered history table
            history_table = []

            for item in filtered_analyses:
                created_at = item["created_at"]

                history_table.append({
                    "Analysis ID": item["id"],
                    "Material": item["material_type"],
                    "Category": item["primary_category"],
                    "Condition": item["physical_condition"],
                    "Confidence": (
                        f'{item["confidence_score"]:.1%}'
                        if item["confidence_score"] is not None
                        else "N/A"
                    ),
                    "Date": created_at.strftime("%d %b %Y, %I:%M %p")
                    if created_at
                    else "N/A",
                })

            st.markdown("### 🗃️ Saved Analyses")

            if filtered_analyses:
                st.dataframe(
                    history_table,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No analyses match your search or selected filters.")

            st.markdown("---")
            st.markdown("### 🔍 View Previous Analysis")

            analysis_ids = [item["id"] for item in analyses]

            selected_id = st.selectbox(
                "Select an Analysis ID",
                options=analysis_ids,
            )

            if st.button("View Analysis Details", use_container_width=True):
                st.session_state["history_selected_id"] = selected_id

            if "history_selected_id" in st.session_state:
                selected_history_id = st.session_state["history_selected_id"]

                if selected_history_id in analysis_ids:
                    saved_result = get_analysis_by_id(selected_history_id)

                    if saved_result:
                        material = saved_result.get("material", {})
                        st.markdown(f"## ♻️ Analysis Report #{selected_history_id}")

                        #Overview
                        st.markdown("### Material Overview")

                        st.markdown(f"**Material:** {material.get('material_type', 'Unknown')}")
                        st.markdown(f"**Category:** {material.get('primary_category', 'N/A')}")
                        st.markdown(f"**Sub-category:** {material.get('sub_category', 'N/A')}")

                        summary = saved_result.get("summary")
                        if summary:
                            st.info(summary)

                        # Key metrics
                        confidence = material.get("confidence_score", saved_result.get("confidence"))
                        recyclability = material.get("recyclability_score")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if isinstance(confidence, (int, float)):
                                confidence_display = (
                                    f"{confidence:.1%}" if confidence <= 1 else f"{confidence:.1f}%"
                                )
                            else:
                                confidence_display = str(confidence or "N/A")

                            st.metric("AI Confidence", confidence_display)

                        with col2:
                            st.metric(
                                "Recyclability Score",
                                recyclability if recyclability is not None else "N/A"
                            )

                        with col3:
                            st.metric(
                                "Physical Condition",
                                material.get("physical_condition", saved_result.get("condition", "N/A"))
                            )

                        st.markdown("---")

                        # Material details
                        st.markdown("### 🔬 Material Details")

                        details_col1, details_col2 = st.columns(2)

                        with details_col1:
                            st.write("**Cleanliness Level**")
                            st.write(material.get("cleanliness_level", "N/A"))

                            st.write("**Waste Type**")
                            st.write(saved_result.get("waste_type", "N/A"))

                        with details_col2:
                            st.write("**Recyclable**")
                            st.write(saved_result.get("recyclable", "N/A"))

                            st.write("**Detected Features**")
                            st.write(material.get("detected_features", "N/A"))

                        hazardous = material.get("hazardous_elements")
                        if hazardous:
                            st.warning("⚠️ Hazardous Elements")
                            st.write(hazardous)

                        st.markdown("---")

                        # Reuse suggestions
                        st.markdown("### 💡 Reuse Suggestions")

                        suggestions = saved_result.get("reuse_suggestions", [])

                        if suggestions:
                            for i, suggestion in enumerate(suggestions, start=1):

                                with st.container(border=True):
                                    st.markdown(f"### 💡 {suggestion.get('title', f'Suggestion                         {i}')}")
                                    st.caption(suggestion.get("category", "Reuse Idea"))

                                    col1, col2, col3 = st.columns(3)

                                    with col1:
                                        st.metric("Difficulty", suggestion.get("difficulty", "N/A"))

                                    with col2:
                                        st.metric("Estimated Time", suggestion.get("estimated_time", "N/A"))

                                    with col3:
                                        st.metric("Carbon Offset", suggestion.get("carbon_offset_rating", "N/A"))

                                    st.markdown("**🌱 Environmental Benefit**")
                                    st.write(suggestion.get("environmental_benefit", "N/A"))

                                    tools = suggestion.get("tools_required", [])
                                    if tools:
                                        st.markdown("**🧰 Tools Required**")
                                        for tool in tools:
                                            st.markdown(f"- {tool}")

                                    steps = suggestion.get("step_by_step_guide", [])
                                    if steps:
                                        st.markdown("**📝 Step-by-Step Guide**")
                                        for step_no, step in enumerate(steps, start=1):
                                            st.markdown(f"**{step_no}.** {step}")
                        else:
                            st.info("No reuse suggestions were saved for this analysis.")

                        # Matched opportunities
                        st.markdown("---")
                        st.markdown("### 🏭 Matched Opportunities")

                        opportunities = saved_result.get("matched_opportunities", [])

                        if opportunities:
                            for i, opportunity in enumerate(opportunities, start=1):

                                with st.container(border=True):
                                    st.markdown(
                                        f"### 🏭 {opportunity.get('opportunity_name', f'Opportunity {i}')}"
                                    )

                                    st.caption(opportunity.get("opportunity_category", "Industry Opportunity"))

                                    score = opportunity.get("match_score")

                                    if isinstance(score, (int, float)):
                                        st.progress(min(max(score / 100, 0.0), 1.0))
                                        st.metric("Material Match Score", f"{score:.1f}%")
                                    else:
                                        st.metric("Material Match Score", "N/A")

                                    st.markdown("**👥 Target Users**")
                                    st.write(opportunity.get("target_user", "N/A"))

                                    st.markdown("**🔧 Suggested Application**")
                                    st.write(opportunity.get("suggested_application", "N/A"))

                                    st.markdown("**🧠 Why This Match?**")
                                    st.write(opportunity.get("reason", "N/A"))
                        else:
                            st.info("No matched opportunities were saved.")

                        # Handling instructions
                        st.markdown("---")
                        st.markdown("### 🛡️ Handling Instructions")

                        handling = saved_result.get("handling_instructions")
                        if handling:
                            st.write(handling)
                        else:
                            st.info("No handling instructions available.")

                        # Additional data
                        with st.expander("View Additional Analysis Data"):
                            st.json({
                                "Reuse Ideas": saved_result.get("reuse_ideas"),
                                "Potential Industry Matches": saved_result.get("potential_industry_matches"),
                                "Metadata": saved_result.get("metadata"),
                            })
                    else:
                        st.warning("Could not retrieve this analysis.")

    except Exception as e:
        st.error(f"Unable to load analysis history: {e}")
# PAGE 4: Impact Dashboard (Coming Soon in Phase 6)
# -----------------------------------------------------------------------------
elif current_page == "Impact Dashboard":
    st.markdown(
        """
        <div class="page-header">
            <div style="display: inline-block; background-color: #ECFDF5; color: #15803D; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 12px; border: 1px solid #A7F3D0; margin-bottom: 0.5rem; text-transform: uppercase;">
                Phase 6 Roadmap
            </div>
            <div class="page-title">🌱 Circular Impact Dashboard</div>
            <div class="page-subtitle">
                Lifecycle carbon accounting, cumulative landfill diversion telemetry, and regional circularity benchmarks.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "ℹ️ **Coming Soon in Phase 6:** The Impact Dashboard is currently undergoing architectural modeling. "
        "In future phases, verified database telemetry will track cumulative kg diverted from landfill, "
        "avoided virgin extraction emissions, and localized resource circulation indexes. "
        "*No fabricated statistics are displayed in accordance with data integrity commitments.*"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Planned Lifecycle Capabilities")

    i1, i2 = st.columns(2)
    with i1:
        st.markdown(
            """
            <div class="eco-card">
                <div style="font-size: 1.25rem; font-weight: 700; color: #14532D; margin-bottom: 0.35rem;">
                    ⚖️ Landfill Diversion Accounting
                </div>
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.5;">
                    Measures physical mass diverted from municipal solid waste streams, cataloging specific resin grades, metals, paperboard, and glass.
                </p>
                <span class="project-meta-pill">Target: Cumulative Weight (kg)</span>
                <span class="project-meta-pill">Resin Segregation</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="eco-card">
                <div style="font-size: 1.25rem; font-weight: 700; color: #14532D; margin-bottom: 0.35rem;">
                    🔄 Circular Velocity Index
                </div>
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.5;">
                    Quantifies the number of secondary functional cycles each analyzed item undergoes before final biological or metallurgical breakdown.
                </p>
                <span class="project-meta-pill">Functional Longevity</span>
                <span class="project-meta-pill">Cascade Utilization</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            """
            <div class="eco-card">
                <div style="font-size: 1.25rem; font-weight: 700; color: #14532D; margin-bottom: 0.35rem;">
                    💨 Embodied Carbon Offsets
                </div>
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.5;">
                    Calculates displacement of petrochemical and bauxite refining energy by calculating carbon equivalent ($CO_2e$) savings per upcycled item.
                </p>
                <span class="project-meta-pill">Embodied Energy</span>
                <span class="project-meta-pill">Virgin Displacement</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="eco-card">
                <div style="font-size: 1.25rem; font-weight: 700; color: #14532D; margin-bottom: 0.35rem;">
                    📍 Localized Feedstock Exchange
                </div>
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.5;">
                    Connects community waste streams with regional makerspaces, community gardens, and secondary mills to minimize transport logistics emissions.
                </p>
                <span class="project-meta-pill">Regional Logistics</span>
                <span class="project-meta-pill">Decentralized Circularity</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Return to Waste Analysis"):
        navigate_to("Analyze Waste")


# -----------------------------------------------------------------------------
# PAGE 5: About ReUseAI
# -----------------------------------------------------------------------------
elif current_page == "About":
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">ℹ️ About ReUseAI</div>
            <div class="page-subtitle">
                Intelligent Waste-to-Resource Matcher — Subsystem 1: Computer Vision & Material Analysis Engine
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mission Statement
    st.markdown(
        """
        <div class="eco-card" style="border-left: 4px solid #16A34A; margin-bottom: 1.75rem;">
            <h3 style="font-size: 1.3rem; font-weight: 700; color: #14532D; margin-bottom: 0.5rem;">
                🌍 Project Purpose & Sustainability Mission
            </h3>
            <p style="font-size: 0.95rem; color: #4B5563; line-height: 1.6; margin-bottom: 0;">
                Traditional linear economies operate on a destructive <em>take-make-dispose</em> paradigm that discards millions of tons
                of recyclable polymers, clean paperboard, non-ferrous metals, and silica glass into landfills daily.
                <strong>ReUseAI</strong> redefines this dynamic by applying high-speed computer vision perception to identify discarded materials,
                diagnose their physical viability, and match them with high-value upcycling projects and secondary industrial users.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ab_col1, ab_col2 = st.columns(2, gap="medium")
    with ab_col1:
        st.markdown("##### 🔬 Why Material Perception Matters")
        st.markdown(
            """
            <div class="eco-card">
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.55;">
                    Contamination and misclassification are the primary bottlenecks in modern recycling systems. When incompatible polymers (e.g. PVC mixed into PET streams) enter secondary extruders, entire batches degrade.
                    ReUseAI's vision perception evaluates specific resin codes, surface cleanliness, and mechanical integrity before recommending reuse pathways.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### 🔄 Direct Reuse vs. Upcycling")
        st.markdown(
            """
            <div class="eco-card">
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.55;">
                    Recycling often consumes energy through shredding, thermal re-melting, and pelletization. In contrast,
                    <strong>direct reuse</strong> and <strong>functional upcycling</strong> preserve the existing structural energy of bottles, jars, and cartons,
                    converting them into sub-irrigated planters, airtight pantry containers, or prototyping mounts with zero thermal reprocessing.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ab_col2:
        st.markdown("##### 🎯 Sustainability Objectives (UN SDG 12)")
        st.markdown(
            """
            <div class="eco-card">
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.55;">
                    ReUseAI directly contributes to <strong>United Nations Sustainable Development Goal 12 (Responsible Consumption and Production)</strong> by:
                </p>
                <ul style="font-size: 0.88rem; color: #4B5563; line-height: 1.5; padding-left: 1.2rem;">
                    <li>Diverting post-consumer packaging from municipal landfills.</li>
                    <li>Lowering consumer demand for virgin petroleum-based household products.</li>
                    <li>Promoting open-source STEM and makerspace circular manufacturing tools.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### 🏗️ System Scope & Architecture")
        st.markdown(
            """
            <div class="eco-card">
                <p style="font-size: 0.9rem; color: #4B5563; line-height: 1.55;">
                    <strong>Subsystem 1 (This Application):</strong> Image preprocessing, vision perception, recyclability diagnostics, and reuse guide generation.<br>
                    <strong>Subsystem 2 (Partner Module):</strong> Database persistence, distributed inventory cataloging, and industrial secondary matching engine.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# Clean SaaS Footer
# -----------------------------------------------------------------------------
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #9CA3AF; padding: 0.5rem 0;">
        <div>ReUseAI Platform &nbsp;•&nbsp; Intelligent Waste-to-Resource Matcher</div>
        <div>Eco Green Design System &nbsp;•&nbsp; Phase 5 Complete</div>
    </div>
    """,
    unsafe_allow_html=True,
)
