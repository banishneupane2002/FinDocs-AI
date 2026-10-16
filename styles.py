"""
Institutional UI Stylesheet for Streamlit Web Application
Clean White & Slate Navy Theme with Sticky Navbar and ChatGPT/Gemini Bottom Dock
"""

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global White App Canvas */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Institutional Executive Header */
    .finance-header {
        background: linear-gradient(135deg, #0A2540 0%, #003366 60%, #08213B 100%);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(10, 37, 64, 0.10);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .finance-header-text h1 {
        margin: 0;
        font-size: 1.7rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #FFFFFF !important;
    }
    .finance-header-text p {
        margin: 4px 0 0 0;
        font-size: 0.92rem;
        color: #CBD5E1 !important;
    }
    .finance-badge {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #F8FAFC;
        white-space: nowrap;
    }
    
    /* Sidebar: Crisp Executive Slate */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #0F2C59 !important;
        font-weight: 600 !important;
    }
    
    /* Expander / Card Containers */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 10px !important;
    }
    
    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* User Message Container Accent */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #F8FAFC !important;
        border-left: 4px solid #64748B !important;
    }
    
    /* Assistant Message Container Accent (Institutional Navy) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background-color: #FFFFFF !important;
        border-left: 4px solid #003366 !important;
    }
    
    /* Quick Showcase Buttons */
    div[data-testid="stHorizontalBlock"] button {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #1E293B !important;
        text-align: left !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: #003366 !important;
        color: #003366 !important;
        background-color: #F8FAFC !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0, 51, 102, 0.08) !important;
    }

    /* Verification Citation Badge */
    .citation-container {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 14px;
        font-size: 0.88rem;
    }
    .citation-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        margin-right: 8px;
        border: 1px solid #BFDBFE;
    }

    /* Primary Interactive Buttons */
    .stButton>button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        transition: all 0.15s ease-in-out !important;
    }
    
    /* Stat Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #003366 !important;
    }
    
    /* Code and Pre Blocks */
    pre, code {
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
        border-radius: 6px !important;
    }
    
    /* Form Submissions */
    div[data-testid="stForm"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 20px !important;
        background-color: #FFFFFF !important;
    }
    
    /* Status Messages */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
    }
    
    /* Document Table Row */
    .doc-row {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* ChatGPT & Gemini Style Docked Chat Input Bar */
    div[data-testid="stBottom"] {
        background-color: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-top: 1px solid rgba(226, 232, 240, 0.8) !important;
        padding-top: 12px !important;
        padding-bottom: 20px !important;
        z-index: 999 !important;
    }
    div[data-testid="stBottom"] > div {
        background: transparent !important;
    }
    div[data-testid="stChatInput"] {
        max-width: 840px !important;
        margin: 0 auto !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(10, 37, 64, 0.08) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #003366 !important;
        box-shadow: 0 4px 24px rgba(0, 51, 102, 0.16) !important;
    }
    div[data-testid="stChatInput"] textarea {
        font-size: 0.96rem !important;
        line-height: 1.5 !important;
    }

    /* Header & Main Container Spacing */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        z-index: 996 !important;
    }

    .block-container {
        padding-top: 3.2rem !important;
        padding-bottom: 7rem !important;
    }

    /* Sticky Navbar Container for Assistant & Admin Selector */
    .stElementContainer.st-key-main_workspace_view,
    div.st-key-main_workspace_view,
    div[data-testid="stVerticalBlock"] > div:has(.stButtonGroup),
    .stElementContainer:has(div[data-testid="stButtonGroup"]) {
        position: sticky !important;
        top: 2.875rem !important;
        z-index: 995 !important;
        background-color: rgba(255, 255, 255, 0.96) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 8px 0 !important;
        margin-top: -6px !important;
        margin-bottom: 1.2rem !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.04) !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }

    /* Clean Segmented Navigation Switch */
    div.st-key-main_workspace_view div[data-testid="stButtonGroup"],
    div[data-testid="stButtonGroup"]:has(button[data-variant="segmented_control"]),
    div[data-testid="stSegmentedControl"] {
        background-color: #F1F5F9 !important;
        padding: 4px !important;
        border-radius: 12px !important;
        margin-bottom: 0 !important;
        display: inline-flex !important;
        border: 1px solid #E2E8F0 !important;
        white-space: nowrap !important;
    }
    div.st-key-main_workspace_view button[data-variant="segmented_control"],
    div[data-testid="stButtonGroup"] button[data-variant="segmented_control"],
    div[data-testid="stSegmentedControl"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 6px 18px !important;
        border: none !important;
        color: #475569 !important;
        transition: all 0.2s ease !important;
    }
    div.st-key-main_workspace_view button[data-variant="segmented_control"][aria-checked="true"],
    div[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #003366 !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.2) !important;
    }
</style>
"""

