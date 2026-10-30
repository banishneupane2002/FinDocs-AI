"""
Best Finance Company Ltd. Institutional UI Stylesheet
Official Brand Guidelines:
- Primary Brand Blue: #1c75bb (Corporate Blue)
- Primary Brand Green: #00a54f (Corporate Green / Compliance)
- Typography:
  - English Headings: Helvetica Bold - 39px
  - Nepali Headings: Aakriti Bold - 48px
- Canvas Background: #FFFFFF (Clean Pure White)
- User Chat Bubble: #1c75bb (Best Finance Blue Pill)
- Assistant Avatar: Dual-tone Gradient (#1c75bb -> #00a54f)
- Sidebar: #1c75bb (Exact Brand Corporate Blue)
- User Chat Bubble & Input: #00a54f (Exact Brand Corporate Green)
- Verified Sources Cited: #1c75bb (Exact Brand Corporate Blue)
"""

import os
import base64

def _get_toggle_icon_b64():
    p = os.path.join(os.path.dirname(__file__), "sidebar_toggle_icon.png")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

TOGGLE_ICON_B64 = _get_toggle_icon_b64()

# ==============================================================================
# 🎨 MASTER COLOR SETTINGS — EDIT ALL UI COLORS HERE!
# Change any color code below, save the file, and press 'R' in your browser:
# ==============================================================================

# 1. Left Sidebar
SIDEBAR_BACKGROUND_COLOR       = "linear-gradient(176deg,rgba(9, 92, 156, 1) 57%, rgba(6, 150, 76, 1) 97%);"   # Left sidebar background (Best Finance Corporate Blue)
SIDEBAR_TEXT_COLOR             = "#FFFFFF"   # Sidebar primary text color

# 1.5 Active Navigation Page Box ("Regulatory Assistant" / "Document Management")
NAV_ACTIVE_BOX_BG              = "rgba(255, 255, 255, 0.18)"  # Active page box background (e.g. #00a54f, #1867a3, rgba)
NAV_ACTIVE_BOX_BORDER          = "rgba(255, 255, 255, 0.35)"  # Active page box border (e.g. #008740, #1a6cab, rgba)
NAV_ACTIVE_TEXT_COLOR          = "#FFFFFF"                   # Active page text and icon color

# 2. Scope & Filter Dropdowns (Category Scope & Document)
DROPDOWN_BOX_COLOR             = "#094E83"   # Dropdown box background (Corporate Green)
DROPDOWN_BORDER_COLOR          = "#0F609E"   # Border for "All categories" & "All documents" boxes ONLY
DROPDOWN_TEXT_COLOR            = "#FFFFFF"   # Text inside the dropdown box
DROPDOWN_ARROW_COLOR           = "#FFFFFF"   # Dropdown chevron arrow icon color (Zero border, zero outline)
DROPDOWN_MENU_BACKGROUND       = "#094E83"   # Expanded dropdown menu background (Corporate Blue)
DROPDOWN_MENU_HOVER_COLOR      = "#094E83"   # Hover & selected item in dropdown menu (Corporate Green)

# 3. Sidebar Action Button ("Clear Chat History")
CLEAR_CHAT_BUTTON_COLOR        = "#04954aff"   # Clear chat history button background
CLEAR_CHAT_BUTTON_BORDER       = "#008740"   # Clear chat history button border
CLEAR_CHAT_BUTTON_TEXT         = "#FFFFFF"   # Clear chat history button text
CLEAR_CHAT_BUTTON_HOVER        = "#008740"   # Clear chat history button hover color

# 4. Chat Messages & Canvas
CANVAS_BACKGROUND_COLOR        = "#FFFFFF"   # Main chat canvas background
USER_CHAT_BUBBLE_COLOR         = "#0B9E52"   # User question bubble background
USER_CHAT_TEXT_COLOR           = "#FFFFFF"   # User question text color
ASSISTANT_TEXT_COLOR           = "#111827"   # Assistant response text color

# 5. Chat Input Bar (Bottom)
CHAT_INPUT_FOCUS_BORDER        = "#00a54f"   # Border color when typing in chat input
CHAT_SEND_BUTTON_COLOR         = "#00a54f"   # Round send button background
CHAT_SEND_BUTTON_HOVER         = "#008740"   # Send button hover color

# 6. Citations & Badges
VERIFIED_SOURCES_BADGE_BG      = "#F0F7FD"   # "Verified source(s) cited" badge background
VERIFIED_SOURCES_BADGE_TEXT    = "#1c75bb"   # "Verified source(s) cited" text and icon color
VERIFIED_SOURCES_BADGE_BORDER  = "#BAE0F8"   # "Verified source(s) cited" badge border
# ==============================================================================

RAW_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mukta:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap');

    /* Local / System Fonts for Helvetica Bold and Aakriti Bold */
    @font-face {
        font-family: 'Helvetica Bold';
        src: local('Helvetica Bold'), local('Helvetica-Bold'), local('HelveticaNeue-Bold'), local('Helvetica Neue Bold');
        font-weight: 700;
        font-style: normal;
    }

    @font-face {
        font-family: 'Aakriti Bold';
        src: local('Aakriti Bold'), local('Aakriti-Bold'), local('Aakriti');
        font-weight: 700;
        font-style: normal;
    }

    :root {
        /* Best Finance Company Ltd. Brand Guidelines */
        --brand-blue: #1c75bb;
        --brand-green: #00a54f;
        --brand-blue-hover: #155d96;
        --brand-blue-light: #EBF4FC;
        --brand-blue-border: #BAE0F8;
        --brand-green-hover: #008740;
        --brand-green-light: #ECFDF5;
        --brand-green-border: #A7F3D0;
        --sidebar-bg: #1c75bb;
        --sidebar-border: rgba(255, 255, 255, 0.20);
        --sidebar-dropdown-bg: #00a54f;
        --sidebar-btn-bg: #00a54f;

        /* Typography */
        --font-helvetica-bold: 'Helvetica Bold', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        --font-aakriti-bold: 'Aakriti Bold', 'Aakriti', 'Mukta', 'Poppins', sans-serif;
        --font-body: 'Helvetica Neue', Helvetica, 'Mukta', 'Poppins', Arial, sans-serif;
    }

    html, body {
        overflow-x: hidden !important;
        font-family: var(--font-body) !important;
    }

    /* Company Typography Rules */
    /* English Headings: Helvetica Bold - 39px */
    .brand-title-en, .en-title-39, .stMarkdown h1 {
        font-family: var(--font-helvetica-bold) !important;
        font-size: 39px !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.015em !important;
        color: #111827 !important;
    }

    /* Nepali Headings: Aakriti Bold - 48px */
    .brand-title-np, .np-title-48 {
        font-family: var(--font-aakriti-bold) !important;
        font-size: 48px !important;
        font-weight: 700 !important;
        line-height: 1.25 !important;
        color: #111827 !important;
    }

    .stMarkdown h2 {
        font-family: var(--font-helvetica-bold) !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1c75bb !important;
    }

    .stMarkdown h3 {
        font-family: var(--font-helvetica-bold) !important;
        font-size: 1.22rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    
    /* Global Clean White Canvas */
    .stApp {
        background-color: __CANVAS_BG__ !important;
        color: #111827 !important;
        overflow-x: hidden !important;
    }

    /* ---------------------------------------------------- */
    /* 0. TOP INSTITUTIONAL NAVBAR (RESPONSIVE: LOGO, TITLE, BADGE) */
    /* ---------------------------------------------------- */
    .institutional-navbar {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        max-width: 100vw !important;
        height: 88px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 28px !important;
        z-index: 998 !important;
        background: #FFFFFF !important;
        border-bottom: 1.5px solid #E5E7EB !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
        box-sizing: border-box !important;
        transform: translate3d(0, 0, 0) !important;
        -webkit-transform: translate3d(0, 0, 0) !important;
        backface-visibility: hidden !important;
        will-change: transform !important;
    }

    .navbar-left {
        display: flex !important;
        align-items: center !important;
        flex: 1 1 0% !important;
        justify-content: flex-start !important;
        padding-left: 0 !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    .navbar-brand-link {
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
    }

    .navbar-brand-logo {
        max-height: 50px !important;
        width: auto !important;
        max-width: 250px !important;
        object-fit: contain !important;
        display: block !important;
        
    }

    .navbar-center {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: 2 1 0% !important;
        text-align: center !important;
        min-width: 0 !important;
        padding: 0 12px !important;
    }

    .navbar-title-container {
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        max-width: 100% !important;
    }

    .navbar-title-icon {
        width: 34px !important;
        height: 34px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #1c75bb 0%, #00a54f 100%) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        box-shadow: 0 2px 6px rgba(28, 117, 187, 0.25) !important;
    }

    .navbar-title-content {
        text-align: left !important;
        min-width: 0 !important;
    }

    .navbar-title-heading,
    h1.navbar-title-heading,
    div.navbar-title-heading {
        margin: 0 !important;
        font-family: var(--font-helvetica-bold) !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.25 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    .navbar-title-sub {
        margin: 4px 0 0 0 !important;
        font-size: 0.82rem !important;
        color: #64748B !important;
        line-height: 1.25 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        
    }

    .navbar-right {
        display: flex !important;
        align-items: center !important;
        flex: 1 1 0% !important;
        justify-content: flex-end !important;
        padding-right: 0 !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    .navbar-status-badge {
        background: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        color: #008740 !important;
        padding: 6px 14px !important;
        border-radius: 9999px !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 7px !important;
        flex-shrink: 0 !important;
        white-space: nowrap !important;
            }

    @keyframes statusPulse {
        0% {
            box-shadow: 0 0 0 0 rgba(0, 165, 79, 0.7);
            transform: scale(0.95);
        }
        70% {
            box-shadow: 0 0 0 6px rgba(0, 165, 79, 0);
            transform: scale(1.05);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(0, 165, 79, 0);
            transform: scale(0.95);
        }
    }

    @keyframes thinkingBounce {
        0%, 80%, 100% {
            transform: translateY(0);
            opacity: 0.35;
        }
        40% {
            transform: translateY(-4px);
            opacity: 1;
        }
    }

    .status-pulse-dot {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        background: #00a54f !important;
        display: inline-block !important;
        flex-shrink: 0 !important;
        animation: statusPulse 2s infinite cubic-bezier(0.4, 0, 0.6, 1) !important;
    }

    .thinking-dots {
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        margin-left: 5px !important;
        vertical-align: middle !important;
    }

    .thinking-dot {
        width: 5px !important;
        height: 5px !important;
        background-color: #008740 !important;
        border-radius: 50% !important;
        display: inline-block !important;
        animation: thinkingBounce 1.4s infinite ease-in-out both !important;
    }

    .thinking-dot:nth-child(1) { animation-delay: -0.32s !important; }
    .thinking-dot:nth-child(2) { animation-delay: -0.16s !important; }
    .thinking-dot:nth-child(3) { animation-delay: 0s !important; }

    .system-status-indicator {
        display: inline-flex !important;
        align-items: center !important;
        gap: 9px !important;
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 6px 15px !important;
        font-size: 0.82rem !important;
        color: #008740 !important;
        font-weight: 500 !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease !important;
    }

    .status-badge-text {
        display: inline !important;
    }

    /* ---------------------------------------------------- */
    /* 1. SIDEBAR: FULL-HEIGHT OVERLAY DRAWER               */
    /* ---------------------------------------------------- */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {
        background: __SIDEBAR_BG__ !important;
        border-right: 1px solid rgba(255, 255, 255, 0.18) !important;
        top: 0 !important;
        height: 100vh !important;
        height: 100dvh !important;
        width: 21rem !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        position: fixed !important;
        z-index: 1020 !important;
        box-shadow: 8px 0 32px rgba(28, 117, 187, 0.30) !important;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin-left 0.3s ease !important;
    }

    section[data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(-110%) !important;
        margin-left: -22rem !important;
        box-shadow: none !important;
        pointer-events: none !important;
    }

    section[data-testid="stSidebar"][aria-expanded="true"] {
        transform: translateX(0) !important;
        margin-left: 0 !important;
        box-shadow: 6px 0 24px rgba(0, 0, 0, 0.45) !important;
        pointer-events: auto !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.20) !important;
        margin: 16px 0 !important;
    }

    /* Container wrappers for navigation links (zero extra padding/margin) */
    div[class*="st-key-nav_active_link"],
    div[class*="st-key-nav_inactive_link"] {
        margin: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }

    /* Base Page Link styling */
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        padding: 9px 12px !important;
        color: rgba(255, 255, 255, 0.88) !important;
        font-weight: 500 !important;
        font-size: 0.90rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        margin-bottom: 5px !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
    }

    /* Inactive Link Hover */
    div[class*="st-key-nav_inactive_link"] a:hover,
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.14) !important;
        color: #FFFFFF !important;
    }

    /* ACTIVE PAGE BOX — ALWAYS SHOWN on current page (regardless of hover) */
    div[class*="st-key-nav_active_link"] a,
    div[class*="st-key-nav_active_link"] [data-testid="stPageLink-NavLink"],
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: __NAV_ACTIVE_BG__ !important;
        background-color: __NAV_ACTIVE_BG__ !important;
        border: 1px solid __NAV_ACTIVE_BORDER__ !important;
        border-color: __NAV_ACTIVE_BORDER__ !important;
        border-radius: 8px !important;
        color: __NAV_ACTIVE_TEXT__ !important;
        -webkit-text-fill-color: __NAV_ACTIVE_TEXT__ !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
    }

    div[class*="st-key-nav_active_link"] a *,
    div[class*="st-key-nav_active_link"] [data-testid="stPageLink-NavLink"] * {
        color: __NAV_ACTIVE_TEXT__ !important;
        -webkit-text-fill-color: __NAV_ACTIVE_TEXT__ !important;
    }

    div[class*="st-key-nav_active_link"] a svg {
        fill: __NAV_ACTIVE_TEXT__ !important;
        color: __NAV_ACTIVE_TEXT__ !important;
    }

    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span {
        color: inherit !important;
    }

    /* ---------------------------------------------------- */
    /* 1.1 SIDEBAR SELECTBOX: CLEAN, MODERN, ZERO BORDERS  */
    /* ---------------------------------------------------- */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Labels inside sidebar (Scope & Filter, Category scope, Document) NEVER have borders or boxes */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label *,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] {
        border: none !important;
        border-color: transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        margin-bottom: 5px !important;
        padding: 0 !important;
    }

    /* Outer selectbox parent wrappers have ZERO border */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }

    /* The ONE single dropdown input box */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[role="combobox"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div:has(> input),
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] .st-emotion-cache-1jf1gc {
        background-color: __DROPDOWN_BG__ !important;
        background: __DROPDOWN_BG__ !important;
        border: 1px solid __DROPDOWN_BORDER__ !important;
        border-color: __DROPDOWN_BORDER__ !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    /* Inner input text & cursor */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] input,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] input[type="text"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] input {
        background: transparent !important;
        background-color: transparent !important;
        color: __DROPDOWN_TEXT__ !important;
        -webkit-text-fill-color: __DROPDOWN_TEXT__ !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        cursor: pointer !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] input::placeholder {
        color: rgba(255, 255, 255, 0.85) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.85) !important;
    }

    /* Dropdown chevron button on the right - ALWAYS transparent, ZERO border, ZERO outline */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:hover,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:focus,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:active,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button[aria-label="Open"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button[aria-label="Open"]:hover,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button[aria-label="Open"]:focus,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [aria-label="Open"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [aria-label="Open"]:hover,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [aria-label="Open"]:focus,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] .st-emotion-cache-14ikocw,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] .e1fp86qc2,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button[data-rac],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-react-aria-pressable],
    div[data-testid="stSelectbox"] .st-emotion-cache-14ikocw,
    div[data-testid="stSelectbox"] .e1fp86qc2,
    div[data-testid="stSelectbox"] button[aria-label="Open"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-width: 0 !important;
        border-style: none !important;
        border-color: transparent !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        outline-color: transparent !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        transform: none !important;
        color: __DROPDOWN_ARROW_COLOR__ !important;
        padding: 0 !important;
    }

    /* Dropdown chevron SVG and paths - ABSOLUTELY ZERO BORDER / ZERO STROKE */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button svg,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] .st-emotion-cache-1eamic5,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] .ex0cdmw0,
    div[data-testid="stSelectbox"] .st-emotion-cache-1eamic5,
    div[data-testid="stSelectbox"] .ex0cdmw0 {
        border: none !important;
        border-width: 0 !important;
        outline: none !important;
        outline-width: 0 !important;
        box-shadow: none !important;
        fill: __DROPDOWN_ARROW_COLOR__ !important;
        color: __DROPDOWN_ARROW_COLOR__ !important;
        stroke: none !important;
        stroke-width: 0 !important;
    }

    /* Completely eliminate white bounding-box rectangle outline from SVG */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg path,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button svg path {
        stroke: none !important;
        stroke-width: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg path[fill="none"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button svg path[fill="none"] {
        display: none !important;
        fill: none !important;
        stroke: none !important;
        stroke-width: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg path:not([fill="none"]),
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button svg path:not([fill="none"]) {
        fill: __DROPDOWN_ARROW_COLOR__ !important;
        color: __DROPDOWN_ARROW_COLOR__ !important;
        stroke: none !important;
        stroke-width: 0 !important;
    }

    /* Fallback for BaseWeb select value spans */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="ValueContainer"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="SingleValue"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="Placeholder"],
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        background-color: transparent !important;
    }

    /* High-contrast crisp sidebar typography */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        opacity: 1 !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 5px !important;
    }

    section[data-testid="stSidebar"] .stCaption, 
    section[data-testid="stSidebar"] .stCaption p,
    section[data-testid="stSidebar"] p {
        color: rgba(255, 255, 255, 0.88) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.88) !important;
        font-size: 0.78rem !important;
        font-weight: 400 !important;
        line-height: 1.45 !important;
    }

    /* ---------------------------------------------------- */
    /* 1.2 DROPDOWN MENU (STREAMLIT 1.65+ VIRTUAL DROPDOWN) */
    /* ---------------------------------------------------- */
    div[data-testid="stSelectboxVirtualDropdown"],
    div[data-testid="stSelectboxVirtualDropdown"] > div,
    div[data-testid="stSelectboxVirtualDropdown"] div[role="listbox"],
    div[data-testid="stSelectboxVirtualDropdown"] ul[role="listbox"],
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] [data-baseweb="menu"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] ul[role="listbox"],
    ul[role="listbox"] {
        background-color: __DROPDOWN_MENU_BG__ !important;
        background: __DROPDOWN_MENU_BG__ !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 8px !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55) !important;
        padding: 4px 0 !important;
        overflow: hidden !important;
    }

    div[data-testid="stSelectboxVirtualDropdown"] div[role="option"],
    div[data-testid="stSelectboxVirtualDropdown"] li[role="option"],
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"],
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] [role="option"],
    ul[role="listbox"] li,
    ul[role="listbox"] li[role="option"] {
        background-color: #1c75bb !important;
        background: #1c75bb !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        padding: 10px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        border: none !important;
    }

    /* Force all nested text inside dropdown options to be pure crisp white */
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"] *,
    div[data-baseweb="popover"] li *,
    div[data-baseweb="popover"] [role="option"] *,
    ul[role="listbox"] li * {
        background-color: transparent !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }

    /* Hover & Selected states: Rich emerald background with mint text */
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"],
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"],
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-selected="true"],
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] [role="option"]:hover,
    ul[role="listbox"] li:hover,
    ul[role="listbox"] li[role="option"]:hover,
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] li[role="option"][aria-selected="true"],
    ul[role="listbox"] li[aria-selected="true"],
    ul[role="listbox"] li[role="option"][aria-selected="true"] {
        background-color: __DROPDOWN_MENU_HOVER__ !important;
        background: __DROPDOWN_MENU_HOVER__ !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    div[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover *,
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] *,
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"] *,
    div[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-selected="true"] *,
    div[data-baseweb="popover"] li:hover *,
    div[data-baseweb="popover"] li[role="option"]:hover *,
    div[data-baseweb="popover"] [role="option"]:hover *,
    ul[role="listbox"] li:hover *,
    ul[role="listbox"] li[role="option"]:hover *,
    div[data-baseweb="popover"] li[aria-selected="true"] *,
    div[data-baseweb="popover"] li[role="option"][aria-selected="true"] *,
    ul[role="listbox"] li[aria-selected="true"] *,
    ul[role="listbox"] li[role="option"][aria-selected="true"] * {
        background-color: transparent !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Sidebar Action Buttons (Clear Chat History) - ONLY target stButton */
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: __CLEAR_CHAT_BTN_BG__ !important;
        background: __CLEAR_CHAT_BTN_BG__ !important;
        border: 1px solid __CLEAR_CHAT_BTN_BORDER__ !important;
        color: __CLEAR_CHAT_BTN_TEXT__ !important;
        -webkit-text-fill-color: __CLEAR_CHAT_BTN_TEXT__ !important;
        border-radius: 8px !important;
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 2px 6px rgba(0, 165, 79, 0.25) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: __CLEAR_CHAT_BTN_HOVER__ !important;
        background: __CLEAR_CHAT_BTN_HOVER__ !important;
        border-color: __CLEAR_CHAT_BTN_HOVER__ !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0, 165, 79, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* ---------------------------------------------------- */
    /* 2. CHAT STREAM & BUBBLES                             */
    /* ---------------------------------------------------- */
    /* Remove generic container boxes around chat messages */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 6px 0 !important;
        margin-bottom: 12px !important;
    }

    /* Markdown Blockquotes as Exact Clause Callouts */
    blockquote {
        border-left: 3px solid #00a54f !important;
        padding-left: 14px !important;
        margin: 12px 0 !important;
        color: #374151 !important;
        font-style: normal !important;
        background: transparent !important;
    }

    /* Clean Enterprise Table Styling matching Lovable */
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        margin: 14px 0 !important;
        overflow: hidden !important;
        font-size: 0.88rem !important;
    }
    th {
        background-color: #F9FAFB !important;
        color: #111827 !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        border-bottom: 1.5px solid #E5E7EB !important;
    }
    td {
        padding: 10px 14px !important;
        border-bottom: 1px solid #F3F4F6 !important;
        color: #374151 !important;
    }
    tr:hover td {
        background-color: #F8FAFC !important;
    }

    /* ---------------------------------------------------- */
    /* 3. METRIC CARDS & CITATIONS                          */
    /* ---------------------------------------------------- */
    .metric-highlight-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px 22px;
        margin: 14px 0;
        max-width: 480px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .metric-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #059669;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #047857;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 1.15rem;
        font-weight: 500;
        color: #374151;
        margin-left: 4px;
    }

    /* Expander inside citation cards */
    div[data-testid="stExpander"] {
        background-color: #FAFAFA !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        margin-top: 8px !important;
        overflow: hidden !important;
    }

    div[data-testid="stExpander"] summary {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #4B5563 !important;
        padding: 8px 12px !important;
    }

    div[data-testid="stExpander"] summary:hover {
        color: #111827 !important;
    }

    /* Minimal Institutional Link Button */
    div[data-testid="stLinkButton"] a {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #334155 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 5px 12px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div[data-testid="stLinkButton"] a:hover {
        background-color: #F8FAFC !important;
        border-color: #CBD5E1 !important;
        color: #0F172A !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06) !important;
    }

    div[data-testid="stLinkButton"] a p {
        color: inherit !important;
        font-weight: inherit !important;
        font-size: inherit !important;
        margin: 0 !important;
    }

    /* High-Contrast Extracted Text Box */
    .extracted-text-box {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        padding: 12px 14px !important;
        font-family: 'Mukta', 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 0.92rem !important;
        line-height: 1.65 !important;
        color: #0F172A !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
        max-height: 240px !important;
        overflow-y: auto !important;
        user-select: text !important;
    }

    /* ---------------------------------------------------- */
    /* 4.5 ADMIN & DOCUMENT MANAGEMENT PANEL STYLING        */
    /* ---------------------------------------------------- */

    /* 1. Metric Stat Cards */
    .admin-stat-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        box-sizing: border-box !important;
    }

    .admin-stat-card:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px) !important;
    }

    .admin-stat-header {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-bottom: 8px !important;
    }

    .admin-stat-icon {
        width: 17px !important;
        height: 17px !important;
        color: #059669 !important;
        flex-shrink: 0 !important;
    }

    .admin-stat-label {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }

    .admin-stat-value {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #059669 !important;
        line-height: 1.15 !important;
    }

    /* 2. Add New Documents Card Container */
    .admin-upload-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 16px !important;
        padding: 24px 28px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
        margin-top: 18px !important;
        margin-bottom: 24px !important;
    }

    .admin-upload-title {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        margin: 0 0 4px 0 !important;
    }

    .admin-upload-subtitle {
        font-size: 0.85rem !important;
        color: #64748B !important;
        margin: 0 0 16px 0 !important;
    }

    /* 3. Drag & Drop File Uploader Zone */
    div[data-testid="stFileUploader"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    section[data-testid="stFileUploaderDropzone"] {
        background-color: #F8FAFC !important;
        border: 1.5px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 26px 20px !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        cursor: pointer !important;
    }

    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #1c75bb !important;
        background-color: #F0FDF4 !important;
    }

    section[data-testid="stFileUploaderDropzone"] svg {
        color: #059669 !important;
        fill: none !important;
        stroke: #059669 !important;
        width: 32px !important;
        height: 32px !important;
        background-color: #DCFCE7 !important;
        border-radius: 50% !important;
        padding: 6px !important;
        margin-bottom: 4px !important;
    }

    section[data-testid="stFileUploaderDropzone"] span,
    section[data-testid="stFileUploaderDropzone"] div {
        color: #475569 !important;
        font-size: 0.90rem !important;
        font-weight: 500 !important;
    }

    section[data-testid="stFileUploaderDropzone"] small {
        color: #94A3B8 !important;
        font-size: 0.78rem !important;
        font-weight: 400 !important;
    }

    /* Dropzone Browse Button */
    section[data-testid="stFileUploaderDropzone"] button {
        background-color: #FFFFFF !important;
        border: 1px solid #D1FAE5 !important;
        color: #059669 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        border-radius: 8px !important;
        padding: 6px 18px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
            }

    section[data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #ECFDF5 !important;
        border-color: #10B981 !important;
        color: #008740 !important;
    }

    /* 4. Primary Brand Blue Button */
    button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background-color: #1c75bb !important;
        border: none !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 12px 24px !important;
        box-shadow: 0 2px 8px rgba(28, 117, 187, 0.25) !important;
        transition: all 0.15s ease !important;
        margin-top: 12px !important;
    }

    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background-color: #155d96 !important;
        box-shadow: 0 4px 14px rgba(28, 117, 187, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* 5. Catalogue Pill Search Input */
    div[data-testid="stTextInput"]:has(input[aria-label="Filter documents"]) input,
    div:has(> input[placeholder*="Filter by name"]) input {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 50px !important;
        padding: 9px 18px 9px 38px !important;
        font-size: 0.88rem !important;
        color: #1E293B !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="%2394A3B8" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"/></svg>') !important;
        background-repeat: no-repeat !important;
        background-position: 13px center !important;
        background-size: 16px 16px !important;
            }

    div[data-testid="stTextInput"]:has(input[aria-label="Filter documents"]) input:focus,
    div:has(> input[placeholder*="Filter by name"]) input:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
    }

    /* 6. Admin Category Cards (Expanders) */
    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]),
    details[data-testid="stExpander"]:has(.stExpanderIcon) {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        overflow: hidden !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]):hover,
    details[data-testid="stExpander"]:has(.stExpanderIcon):hover {
        border-color: #A7F3D0 !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.08) !important;
    }

    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"])[open],
    details[data-testid="stExpander"]:has(.stExpanderIcon)[open] {
        border-color: #10B981 !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.10) !important;
    }

    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]) summary,
    details[data-testid="stExpander"]:has(.stExpanderIcon) summary {
        display: flex !important;
        align-items: center !important;
        padding: 16px 20px !important;
        background-color: #FFFFFF !important;
        cursor: pointer !important;
        border-radius: 14px !important;
        transition: background-color 0.2s ease !important;
    }

    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]) summary:hover,
    details[data-testid="stExpander"]:has(.stExpanderIcon) summary:hover {
        background-color: #F8FAFC !important;
    }

    /* Category Card Icon inside green square */
    details[data-testid="stExpander"] summary [data-testid="stIconMaterial"],
    details[data-testid="stExpander"] summary .stExpanderIcon,
    details[data-testid="stExpander"] summary span.material-symbols-rounded {
        background-color: #ECFDF5 !important;
        color: #059669 !important;
        border-radius: 8px !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
        margin-right: 14px !important;
    }

    /* Category Card Chevron */
    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]) summary svg,
    details[data-testid="stExpander"]:has([data-testid="stIconMaterial"]) summary [data-testid="stExpanderToggleIcon"] {
        margin-left: auto !important;
        order: 10 !important;
        color: #94A3B8 !important;
        width: 18px !important;
        height: 18px !important;
    }

    /* 7. Document Table Styling inside Open Category */
    .admin-doc-table-header {
        background-color: #F8FAFC !important;
        border: 1px solid #F1F5F9 !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        margin-bottom: 8px !important;
    }

    .admin-badge-size {
        display: inline-block !important;
        background-color: #FFFFFF !important;
        color: #475569 !important;
        font-size: 0.80rem !important;
        font-weight: 500 !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
    }

    .admin-badge-chunks {
        display: inline-block !important;
        background-color: #ECFDF5 !important;
        color: #059669 !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
    }

    /* Delete Button Styling */
    div:has(> button[help*="Delete"]) button {
        border-color: #FEE2E2 !important;
        color: #DC2626 !important;
        background-color: #FEF2F2 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 5px 10px !important;
        transition: all 0.15s ease !important;
    }

    div:has(> button[help*="Delete"]) button:hover {
        background-color: #FEE2E2 !important;
        border-color: #FCA5A5 !important;
        color: #B91C1C !important;
    }

    /* Hide empty bottom container on admin page */
    div[data-testid="stBottom"]:not(:has(div[data-testid="stChatInput"])) {
        display: none !important;
    }

    /* ---------------------------------------------------- */
    /* 4.55 RIGHT SOURCES & REFERENCES SLIDE-OVER DRAWER   */
    /* ---------------------------------------------------- */
    .drawer-backdrop {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background-color: rgba(15, 23, 42, 0.35) !important;
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
        z-index: 1001 !important;
        cursor: pointer !important;
        animation: fadeInBackdrop 0.18s ease forwards !important;
    }

    @keyframes fadeInBackdrop {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* The Slide-Over Drawer Container */
    div[class*="st-key-right_popup_drawer_wrap"] {
        position: fixed !important;
        top: 88px !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 440px !important;
        max-width: 90vw !important;
        height: calc(100vh - 88px) !important;
        height: calc(100dvh - 88px) !important;
        background-color: #FAFAFA !important;
        border-left: 1.5px solid #E2E8F0 !important;
        box-shadow: -6px 0 24px rgba(0, 0, 0, 0.08) !important;
        z-index: 997 !important;
        padding: 20px 20px 40px 20px !important;
        overflow-y: auto !important;
        box-sizing: border-box !important;
        animation: slideInFromRight 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    }

    @keyframes slideInFromRight {
        from {
            transform: translateX(100%);
            opacity: 0.6;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    /* Sleek Scrollbar for Drawer */
    div[class*="st-key-right_popup_drawer_wrap"]::-webkit-scrollbar {
        width: 6px !important;
    }
    div[class*="st-key-right_popup_drawer_wrap"]::-webkit-scrollbar-track {
        background: transparent !important;
    }
    div[class*="st-key-right_popup_drawer_wrap"]::-webkit-scrollbar-thumb {
        background: #CBD5E1 !important;
        border-radius: 4px !important;
    }
    div[class*="st-key-right_popup_drawer_wrap"]::-webkit-scrollbar-thumb:hover {
        background: #94A3B8 !important;
    }

    /* Drawer Close Button */
    div[class*="st-key-right_popup_drawer_wrap"] button[kind="secondary"] {
        background: #F1F5F9 !important;
        color: #475569 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        margin-left: auto !important;
        transition: all 0.15s ease !important;
    }
    div[class*="st-key-right_popup_drawer_wrap"] button[kind="secondary"]:hover {
        background: #FEE2E2 !important;
        color: #DC2626 !important;
        border-color: #FECACA !important;
        transform: scale(1.06) !important;
    }

    /* Drawer Link Buttons */
    div[class*="st-key-right_popup_drawer_wrap"] [data-testid="stLinkButton"] a {
        background-color: #FFFFFF !important;
        color: #065F46 !important;
        border: 1.5px solid #10B981 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 6px 12px !important;
        transition: all 0.2s ease !important;
        text-align: center !important;
    }
    div[class*="st-key-right_popup_drawer_wrap"] [data-testid="stLinkButton"] a:hover {
        background-color: #ECFDF5 !important;
        border-color: #059669 !important;
        color: #008740 !important;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15) !important;
    }

    /* Drawer Header & Badges */
    .right-sidebar-icon-box {
        width: 34px !important;
        height: 34px !important;
        border-radius: 8px !important;
        background-color: #ECFDF5 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }

    .right-sidebar-badge {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        padding: 3px 10px !important;
        border-radius: 20px !important;
        background-color: #ECFDF5 !important;
        color: #059669 !important;
        border: 1px solid #A7F3D0 !important;
        letter-spacing: 0.02em !important;
    }

    .right-sidebar-empty-state {
        text-align: center !important;
        padding: 40px 16px !important;
        color: #64748B !important;
    }

    .right-sidebar-empty-icon {
        width: 52px !important;
        height: 52px !important;
        border-radius: 50% !important;
        background-color: #ECFDF5 !important;
        color: #059669 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-bottom: 14px !important;
    }

    .right-sidebar-source-item {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px 14px !important;
        margin-bottom: 8px !important;
        transition: all 0.15s ease !important;
    }

    .right-sidebar-source-item:hover {
        border-color: #BAE0F8 !important;
        box-shadow: 0 4px 12px rgba(28, 117, 187, 0.10) !important;
    }

    /* Chat View in Sidebar Button */
    button[key*="btn_src_"] {
        border-radius: 20px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 4px 14px !important;
        border-color: #10B981 !important;
        color: #065F46 !important;
        background: #FFFFFF !important;
        transition: all 0.15s ease !important;
    }
    button[key*="btn_src_"]:hover {
        background: #ECFDF5 !important;
        color: #008740 !important;
        border-color: #059669 !important;
    }

    /* Admin Page Centered Wrapper */
    .admin-page-wrapper {
        max-width: 960px !important;
        margin: 0 auto !important;
    }

    /* ---------------------------------------------------- */
    /* 4. FLOATING PILL CHAT INPUT BAR                      */
    /* ---------------------------------------------------- */
    div[data-testid="stBottom"],
    footer[data-testid="stBottom"],
    div[data-testid="stBottom"] > div {
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        transform: translate3d(0, 0, 0) !important;
        -webkit-transform: translate3d(0, 0, 0) !important;
        transition: none !important;
    }

    div[data-testid="stBottom"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-top: 1px solid #F3F4F6 !important;
        padding-top: 12px !important;
        padding-bottom: 16px !important;
        z-index: 999 !important;
    }

    header[data-testid="stHeader"] {
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        transform: translate3d(0, 0, 0) !important;
        -webkit-transform: translate3d(0, 0, 0) !important;
        transition: none !important;
    }

    div[data-testid="stBottom"]::after {
        content: "Responses cite official documents. Always confirm with Compliance before acting.";
        display: block;
        text-align: center;
        color: #9CA3AF;
        font-size: 0.74rem;
        margin-top: -20px;
    }

    div[data-testid="stBottom"] > div {
        background: transparent !important;
    }

    /* Outer wrapper: completely transparent, no border, no shadow */
    div[data-testid="stChatInput"] {
        max-width: 760px !important;
        margin: 0 auto !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* THE ONE SINGLE CHAT INPUT PILL BOX (No rectangle inside) */
    div[data-testid="stChatInput"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
        padding: 4px 10px 4px 18px !important;
        display: flex !important;
        align-items: center !important;
        box-sizing: border-box !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    div[data-testid="stChatInput"] > div:focus-within {
        border-color: __CHAT_FOCUS_BORDER__ !important;
        box-shadow: 0 6px 24px rgba(0, 165, 79, 0.18) !important;
    }

    /* Remove any inner borders from nested elements and textareas */
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] div:has(> textarea),
    div[data-testid="stChatInput"] [data-baseweb="textarea"] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        font-size: 0.92rem !important;
        color: #111827 !important;
        padding: 8px 10px !important;
    }

    /* Circular Brand Green Send Button */
    div[data-testid="stChatInput"] button {
        background-color: __CHAT_SEND_BTN__ !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
        width: 34px !important;
        height: 34px !important;
        min-width: 34px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
        flex-shrink: 0 !important;
        transition: background-color 0.2s ease, transform 0.15s ease !important;
    }

    div[data-testid="stChatInput"] button:hover {
        background-color: __CHAT_SEND_HOVER__ !important;
        transform: scale(1.05) !important;
    }

    div[data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* ---------------------------------------------------- */
    /* 5. GENERAL CLEANUPS & REMOVAL OF UNWANTED ELEMENTS   */
    /* ---------------------------------------------------- */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
        height: 88px !important;
        z-index: 999 !important;
    }

    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"],
    header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"],
    [data-testid="stExpandSidebarButton"] {
        pointer-events: auto !important;
    }

    /* Floating Sidebar Expand Button (Clean icon only, no background box, no arrow) */
    [data-testid="stExpandSidebarButton"] {
        position: fixed !important;
        top: 104px !important;
        left: 24px !important;
        z-index: 997 !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        padding: 0 !important;
        width: 30px !important;
        height: 30px !important;
        min-width: 30px !important;
        min-height: 30px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: transform 0.15s ease, opacity 0.15s ease !important;
    }

    [data-testid="stExpandSidebarButton"]:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        transform: scale(1.12) !important;
        opacity: 0.75 !important;
    }

    /* Completely hide all default Streamlit arrow SVGs, Material icons, spans, text */
    [data-testid="stExpandSidebarButton"] *,
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="stExpandSidebarButton"] span {
        display: none !important;
        visibility: hidden !important;
        font-size: 0 !important;
        line-height: 0 !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }

    /* Show ONLY the clean sidebar toggle icon image as an icon */
    [data-testid="stExpandSidebarButton"]::after {
        content: "" !important;
        display: block !important;
        width: 20px !important;
        height: 20px !important;
        background-image: url("data:image/png;base64,__TOGGLE_ICON_B64__") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        pointer-events: none !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* Collapse button inside sidebar header */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
        background: transparent !important;
        border: none !important;
        color: #A7F3D0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {
        fill: #A7F3D0 !important;
        color: #A7F3D0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* CRITICAL FIX: Keep main canvas full-width & never shifted by the sidebar */
    div[data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
    }

    div[data-testid="stAppViewContainer"] > div:nth-child(2),
    div[data-testid="stAppViewContainer"] > div:has(section[data-testid="stMain"]),
    section[data-testid="stMain"],
    div[data-testid="stMain"],
    .stMain,
    .main {
        margin-left: 0 !important;
        left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Main Canvas: Generous width to house both Chat Stream and Right Sources Sidebar */
    .block-container,
    div[data-testid="stMainBlockContainer"] {
        margin-left: auto !important;
        margin-right: auto !important;
        max-width: 860px !important;
        width: 100% !important;
        padding-top: 114px !important;
        padding-bottom: 7.5rem !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
    }

    div[data-testid="stColumn"] {
        overflow: visible !important;
    }

    /* Hide Streamlit Deploy button & chrome */
    .stDeployButton,
    [data-testid="stDeployButton"],
    .stAppDeployButton,
    header[data-testid="stHeader"] .stDeployButton,
    header[data-testid="stHeader"] [data-testid="stDeployButton"],
    #MainMenu + div:has(button) {
        display: none !important;
        visibility: hidden !important;
    }

    /* Invisible utility iframe styling */
    iframe[title="st.iframe"] {
        position: absolute !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
        border: none !important;
    }

    /* ---------------------------------------------------- */
    /* 6. RESPONSIVE BREAKPOINTS (DESKTOP, TABLET, MOBILE)  */
    /* ---------------------------------------------------- */

    /* 1. Large Tablet / Laptop (< 1120px) */
    @media (max-width: 1120px) {
        .right-sidebar-sticky {
            position: static !important;
            max-height: none !important;
            margin-top: 24px !important;
        }
        .institutional-navbar {
            padding: 0 20px !important;
            height: 84px !important;
        }
        header[data-testid="stHeader"] {
            height: 84px !important;
        }
        section[data-testid="stSidebar"] {
            top: 0 !important;
            height: 100vh !important;
            height: 100dvh !important;
            z-index: 1020 !important;
        }
        .navbar-brand-logo {
            max-height: 44px !important;
            max-width: 210px !important;
        }
        .navbar-title-heading,
        h1.navbar-title-heading,
        div.navbar-title-heading {
            margin: 0 !important;
            font-family: var(--font-helvetica-bold) !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
            letter-spacing: -0.01em !important;
            line-height: 1.25 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .navbar-title-sub {
            font-size: 0.78rem !important;
        }
        .navbar-title-icon {
        width: 34px !important;
        height: 34px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #1c75bb 0%, #00a54f 100%) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        box-shadow: 0 2px 6px rgba(28, 117, 187, 0.25) !important;
    }
        .navbar-status-badge {
            padding: 5px 12px !important;
            font-size: 0.76rem !important;
        }
        [data-testid="stExpandSidebarButton"] {
            top: 98px !important;
            left: 20px !important;
        }
    }

    /* 2. Tablet / Narrow Viewport (< 880px) */
    @media (max-width: 880px) {
        .institutional-navbar {
            padding: 0 16px !important;
            height: 76px !important;
        }
        header[data-testid="stHeader"] {
            height: 76px !important;
        }
        section[data-testid="stSidebar"] {
            top: 0 !important;
            height: 100vh !important;
            height: 100dvh !important;
            width: 19.5rem !important;
            min-width: 19.5rem !important;
            z-index: 1020 !important;
        }
        .block-container,
        div[data-testid="stMainBlockContainer"] {
            padding-top: 98px !important;
        }
        .navbar-brand-logo {
            max-height: 38px !important;
            max-width: 165px !important;
        }
        .navbar-title-heading,
        h1.navbar-title-heading,
        div.navbar-title-heading {
            margin: 0 !important;
            font-family: var(--font-helvetica-bold) !important;
            font-size: 0.96rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
            letter-spacing: -0.01em !important;
            line-height: 1.25 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .navbar-title-sub {
            display: none !important;
        }
        .navbar-title-icon {
        width: 34px !important;
        height: 34px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #1c75bb 0%, #00a54f 100%) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        box-shadow: 0 2px 6px rgba(28, 117, 187, 0.25) !important;
    }
        .navbar-title-container {
            gap: 10px !important;
        }
        .navbar-status-badge {
            padding: 4px 10px !important;
            font-size: 0.74rem !important;
        }
        [data-testid="stExpandSidebarButton"] {
            top: 88px !important;
            left: 16px !important;
            width: 28px !important;
            height: 28px !important;
        }
        [data-testid="stExpandSidebarButton"]::after {
            width: 24px !important;
            height: 24px !important;
        }
    }

    /* 3. Small Mobile (< 580px) */
    @media (max-width: 580px) {
        .institutional-navbar {
            padding: 0 12px !important;
            height: 66px !important;
        }
        header[data-testid="stHeader"] {
            height: 66px !important;
        }
        section[data-testid="stSidebar"] {
            top: 0 !important;
            height: 100vh !important;
            height: 100dvh !important;
            width: 86vw !important;
            min-width: 86vw !important;
            max-width: 20rem !important;
            z-index: 1020 !important;
        }
        .block-container,
        div[data-testid="stMainBlockContainer"] {
            padding-top: 84px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        .navbar-left {
            flex: 0 0 auto !important;
        }
        .navbar-brand-logo {
            max-height: 30px !important;
            max-width: 110px !important;
        }
        .navbar-center {
            flex: 1 1 auto !important;
            padding: 0 6px !important;
            justify-content: center !important;
        }
        .navbar-title-icon {
            width: 30px !important;
            height: 30px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #1c75bb 0%, #00a54f 100%) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            box-shadow: 0 2px 6px rgba(28, 117, 187, 0.25) !important;
        }
        .navbar-title-heading,
        h1.navbar-title-heading,
        div.navbar-title-heading {
            margin: 0 !important;
            font-family: var(--font-helvetica-bold) !important;
            font-size: 0.86rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
            letter-spacing: -0.01em !important;
            line-height: 1.25 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .navbar-right {
            flex: 0 0 auto !important;
        }
        .status-badge-text {
            display: none !important;
        }
        .navbar-status-badge {
            padding: 6px !important;
            border-radius: 50% !important;
            min-width: 20px !important;
            min-height: 20px !important;
            justify-content: center !important;
        }
        [data-testid="stExpandSidebarButton"] {
            top: 76px !important;
            left: 10px !important;
            width: 26px !important;
            height: 26px !important;
        }
        [data-testid="stExpandSidebarButton"]::after {
            width: 22px !important;
            height: 22px !important;
        }
    }
</style>
"""

# Inject toggle icon base64 into stylesheet
CUSTOM_CSS = (
    RAW_CSS
    .replace("__TOGGLE_ICON_B64__", TOGGLE_ICON_B64)
    .replace("__SIDEBAR_BG__", SIDEBAR_BACKGROUND_COLOR.rstrip(";"))
    .replace("__SIDEBAR_TEXT__", SIDEBAR_TEXT_COLOR)
    .replace("__NAV_ACTIVE_BG__", NAV_ACTIVE_BOX_BG.rstrip(";"))
    .replace("__NAV_ACTIVE_BORDER__", NAV_ACTIVE_BOX_BORDER.rstrip(";"))
    .replace("__NAV_ACTIVE_TEXT__", NAV_ACTIVE_TEXT_COLOR)
    .replace("__DROPDOWN_BG__", DROPDOWN_BOX_COLOR.rstrip(";"))
    .replace("__DROPDOWN_BORDER__", DROPDOWN_BORDER_COLOR.rstrip(";"))
    .replace("__DROPDOWN_TEXT__", DROPDOWN_TEXT_COLOR)
    .replace("__DROPDOWN_ARROW_COLOR__", DROPDOWN_ARROW_COLOR.rstrip(";"))
    .replace("__DROPDOWN_MENU_BG__", DROPDOWN_MENU_BACKGROUND.rstrip(";"))
    .replace("__DROPDOWN_MENU_HOVER__", DROPDOWN_MENU_HOVER_COLOR.rstrip(";"))
    .replace("__CLEAR_CHAT_BTN_BG__", CLEAR_CHAT_BUTTON_COLOR.rstrip(";"))
    .replace("__CLEAR_CHAT_BTN_BORDER__", CLEAR_CHAT_BUTTON_BORDER.rstrip(";"))
    .replace("__CLEAR_CHAT_BTN_TEXT__", CLEAR_CHAT_BUTTON_TEXT)
    .replace("__CLEAR_CHAT_BTN_HOVER__", CLEAR_CHAT_BUTTON_HOVER.rstrip(";"))
    .replace("__CANVAS_BG__", CANVAS_BACKGROUND_COLOR.rstrip(";"))
    .replace("__CHAT_FOCUS_BORDER__", CHAT_INPUT_FOCUS_BORDER.rstrip(";"))
    .replace("__CHAT_SEND_BTN__", CHAT_SEND_BUTTON_COLOR.rstrip(";"))
    .replace("__CHAT_SEND_HOVER__", CHAT_SEND_BUTTON_HOVER.rstrip(";"))
)

SIDEBAR_BACKDROP_SCRIPT = """
<script>
(function() {
    try {
        const parentDoc = window.parent.document;
        const parentWin = window.parent;
        if (!parentDoc || !parentWin) return;

        // Hide iframe element cleanly so it takes 0 visual space
        if (window.frameElement) {
            window.frameElement.style.cssText = 'position:absolute!important;width:0!important;height:0!important;opacity:0!important;pointer-events:none!important;border:none!important;';
            if (window.frameElement.parentElement) {
                window.frameElement.parentElement.style.cssText = 'height:0!important;min-height:0!important;margin:0!important;padding:0!important;display:none!important;';
            }
        }

        // Clean up any old listeners or scripts
        if (parentWin._sidebarAutoCloseHandler) {
            parentDoc.removeEventListener('click', parentWin._sidebarAutoCloseHandler, true);
            delete parentWin._sidebarAutoCloseHandler;
        }
        const oldScript = parentDoc.getElementById('st-sidebar-autoclose-script');
        if (oldScript) oldScript.remove();

        // 1. Ensure backdrop element exists in parent body
        let backdrop = parentDoc.getElementById('st-sidebar-backdrop');
        if (!backdrop) {
            backdrop = parentDoc.createElement('div');
            backdrop.id = 'st-sidebar-backdrop';
            parentDoc.body.appendChild(backdrop);
        }

        // 2. Click on backdrop -> Collapse the sidebar
        backdrop.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            const collapseBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                parentDoc.querySelector('[data-testid="stSidebarCollapseButton"]') ||
                                parentDoc.querySelector('button[aria-label="Close sidebar"]');
            if (collapseBtn) {
                collapseBtn.click();
            }
            backdrop.style.cssText = 'display:none!important;pointer-events:none!important;opacity:0!important;';
        };

        // 3. Helper to update backdrop display based on sidebar aria-expanded state
        function syncBackdrop() {
            const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
            if (!sidebar) {
                backdrop.style.cssText = 'display:none!important;pointer-events:none!important;opacity:0!important;';
                return;
            }

            const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
            if (isExpanded) {
                backdrop.style.cssText = 'position:fixed!important;top:0!important;left:0!important;right:0!important;bottom:0!important;width:100%!important;height:100%!important;background:rgba(0,0,0,0.32)!important;z-index:1015!important;cursor:pointer!important;display:block!important;opacity:1!important;transition:opacity 0.2s ease!important;';
            } else {
                backdrop.style.cssText = 'display:none!important;pointer-events:none!important;opacity:0!important;';
            }
        }

        // Right drawer is only closed via the cross (X) button as requested

        // 4. Attach MutationObserver to sidebar so backdrop always stays synchronized
        if (parentWin._sidebarObserver) {
            parentWin._sidebarObserver.disconnect();
        }

        const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            const observer = new MutationObserver(function() {
                syncBackdrop();
                            });
            observer.observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded', 'style', 'class'] });
            parentWin._sidebarObserver = observer;
        }

        // Also observe main document body for right drawer popup
        const bodyObs = new MutationObserver(function() {
                    });
        bodyObs.observe(parentDoc.body, { childList: true, subtree: true });

        // Run sync immediately on load / rerun
        syncBackdrop();

    } catch (e) {}
})();
</script>
"""

def inject_sidebar_backdrop():
    """Injects high-reliability backdrop listener: clicking outside expanded sidebar collapses it."""
    import streamlit.components.v1 as components
    components.html(SIDEBAR_BACKDROP_SCRIPT, height=0, width=0)

# Backward-compatibility alias
ensure_sidebar_cleanup = inject_sidebar_backdrop
