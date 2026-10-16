"""
Best Finance Company Ltd. Institutional UI Stylesheet
Brand Palette:
- Primary Brand Green: #00A94F
- Forest / Emerald Green: #047857 / #005528 / #013A1B
- Soft Emerald & Mint Accents: #ECFDF5 / #E6F7EE / #D1FAE5 / #A7F3D0
- Canvas Background: #FFFFFF / #F4FBF7
- Body & Heading Typography: Poppins, Mukta, sans-serif
"""

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mukta:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', 'Mukta', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Clean White Canvas */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Best Finance Executive Header */
    .finance-header {
        background: linear-gradient(135deg, #013A1B 0%, #047857 55%, #00A94F 100%);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(0, 169, 79, 0.16);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(167, 243, 208, 0.3);
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
        color: #D1FAE5 !important;
    }
    .finance-badge {
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(167, 243, 208, 0.45);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #FFFFFF;
        white-space: nowrap;
    }
    
    /* Sidebar: Clean Soft Mint Slate */
    section[data-testid="stSidebar"] {
        background-color: #F4FBF7 !important;
        border-right: 1px solid #D1FAE5;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #02402F !important;
        font-weight: 600 !important;
    }
    
    /* Expander / Card Containers */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #D1FAE5 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 169, 79, 0.04) !important;
        margin-bottom: 10px !important;
        overflow: hidden !important;
    }

    /* Expander Header Title: Dark Forest Green */
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] details summary span {
        color: #02402F !important;
        font-weight: 600 !important;
        font-size: 0.93rem !important;
        letter-spacing: -0.01em !important;
    }

    div[data-testid="stExpander"] summary:hover,
    div[data-testid="stExpander"] details summary:hover {
        background-color: #ECFDF5 !important;
    }
    div[data-testid="stExpander"] summary:hover p,
    div[data-testid="stExpander"] details summary:hover p,
    div[data-testid="stExpander"] summary:hover span,
    div[data-testid="stExpander"] details summary:hover span {
        color: #008C42 !important;
    }

    div[data-testid="stExpander"] summary svg,
    div[data-testid="stExpander"] details summary svg {
        color: #00A94F !important;
        fill: #00A94F !important;
    }

    /* Extracted Text Content in Expander: High-Legibility Dark Slate */
    div[data-testid="stExpander"] div[data-testid="stTextArea"] textarea,
    div[data-testid="stExpander"] textarea:disabled,
    div[data-testid="stExpander"] textarea[disabled] {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        background-color: #F4FBF7 !important;
        border: 1px solid #D1FAE5 !important;
        border-radius: 6px !important;
        font-size: 0.90rem !important;
        line-height: 1.6 !important;
        font-weight: 500 !important;
        opacity: 1 !important;
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
    
    /* Assistant Message Container Accent: Best Finance Brand Green */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background-color: #FFFFFF !important;
        border-left: 4px solid #00A94F !important;
    }
    
    /* Quick Showcase Buttons */
    div[data-testid="stHorizontalBlock"] button {
        background-color: #FFFFFF !important;
        border: 1px solid #D1FAE5 !important;
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
        border-color: #00A94F !important;
        color: #007035 !important;
        background-color: #ECFDF5 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0, 169, 79, 0.12) !important;
    }

    /* Verification Citation Badge */
    .citation-container {
        background-color: #F4FBF7;
        border: 1px solid #D1FAE5;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 14px;
        font-size: 0.88rem;
    }
    .citation-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #ECFDF5;
        color: #047857;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        margin-right: 8px;
        border: 1px solid #A7F3D0;
    }

    /* Buttons: Best Finance Green Theme */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid #D1FAE5 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    .stButton>button:hover {
        border-color: #00A94F !important;
        color: #007035 !important;
        background-color: #ECFDF5 !important;
        box-shadow: 0 4px 12px rgba(0, 169, 79, 0.12) !important;
    }
    
    .stButton>button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #00A94F 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0, 169, 79, 0.25) !important;
    }
    .stButton>button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #008C42 0%, #03543F 100%) !important;
        box-shadow: 0 4px 14px rgba(0, 169, 79, 0.35) !important;
    }
    
    /* Link Buttons */
    a[data-testid="baseButton-secondary"] {
        border-color: #D1FAE5 !important;
        color: #007035 !important;
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease-in-out !important;
    }
    a[data-testid="baseButton-secondary"]:hover {
        border-color: #00A94F !important;
        background-color: #ECFDF5 !important;
        color: #008C42 !important;
        box-shadow: 0 2px 8px rgba(0, 169, 79, 0.15) !important;
    }
    
    /* Stat Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #008C42 !important;
    }
    
    /* Code and Pre Blocks */
    pre, code {
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
        border-radius: 6px !important;
    }
    
    /* Form Submissions */
    div[data-testid="stForm"] {
        border: 1px solid #D1FAE5 !important;
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
        border: 1px solid #D1FAE5;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Bottom Docked Chat Input Bar */
    div[data-testid="stBottom"] {
        background-color: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-top: 1px solid rgba(209, 250, 229, 0.8) !important;
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
        border: 1.5px solid #A7F3D0 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 169, 79, 0.08) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #00A94F !important;
        box-shadow: 0 4px 24px rgba(0, 169, 79, 0.20) !important;
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
        padding-top: 2.5rem !important;
        padding-bottom: 7rem !important;
    }

    /* Complete removal of Streamlit Deploy button */
    .stDeployButton,
    [data-testid="stDeployButton"],
    .stAppDeployButton,
    header[data-testid="stHeader"] .stDeployButton,
    header[data-testid="stHeader"] [data-testid="stDeployButton"],
    header[data-testid="stHeader"] button[kind="header"]:has(span:contains("Deploy")),
    #MainMenu + div:has(button) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Page Navigation Links: Best Finance Mint & Emerald Theme */
    a[data-testid="stPageLink-NavLink"] {
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-weight: 500 !important;
        color: #1E293B !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid #D1FAE5 !important;
        background-color: #FFFFFF !important;
        text-decoration: none !important;
    }
    a[data-testid="stPageLink-NavLink"]:hover {
        background-color: #ECFDF5 !important;
        border-color: #00A94F !important;
        color: #007035 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 169, 79, 0.12) !important;
    }
    a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background-color: #E6F7EE !important;
        border-color: #00A94F !important;
        color: #007035 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background-color: #FFFFFF !important;
        margin-bottom: 6px !important;
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
</style>
"""

SIDEBAR_AUTO_CLOSE_SCRIPT = """
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

        // Replace any prior injected script to ensure latest handler logic
        const existing = parentDoc.getElementById('st-sidebar-autoclose-script');
        if (existing) {
            existing.remove();
        }

        // Inject script into top-level parent head so it lives permanently across Streamlit reruns
        const scriptEl = parentDoc.createElement('script');
        scriptEl.id = 'st-sidebar-autoclose-script';
        scriptEl.textContent = `
            (function() {
                if (window._sidebarAutoCloseHandler) {
                    document.removeEventListener('click', window._sidebarAutoCloseHandler, true);
                }

                window._sidebarClosing = false;

                window._sidebarAutoCloseHandler = function(event) {
                    try {
                        const sidebar = document.querySelector('[data-testid="stSidebar"]');
                        if (!sidebar) return;

                        // Check if sidebar is currently expanded
                        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true' ||
                                           (sidebar.getBoundingClientRect().width > 50 && sidebar.style.display !== 'none');
                        if (!isExpanded) return;

                        // Prevent rapid double-clicks while animation runs
                        if (window._sidebarClosing) return;

                        const target = event.target;
                        if (!target) return;

                        // 1. Keep open if click is inside the sidebar
                        if (sidebar.contains(target)) return;

                        // 2. Ignore clicks on expand or collapse controls
                        if (target.closest('[data-testid="stExpandSidebarButton"]') ||
                            target.closest('[data-testid="stSidebarCollapseButton"]') ||
                            target.closest('[data-testid="stSidebarHeader"]')) {
                            return;
                        }

                        // 3. Ignore clicks inside popovers, select menus, dropdowns, modals
                        if (target.closest('[data-baseweb="popover"]') ||
                            target.closest('[data-baseweb="menu"]') ||
                            target.closest('[role="listbox"]') ||
                            target.closest('[data-testid="stPopoverBody"]') ||
                            target.closest('[data-testid="stModal"]')) {
                            return;
                        }

                        // 4. Click was outside: find collapse button and trigger click
                        const collapseBtn = document.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                            document.querySelector('[data-testid="stSidebarCollapseButton"]') ||
                                            document.querySelector('button[aria-label="Close sidebar"]');

                        if (collapseBtn) {
                            window._sidebarClosing = true;
                            collapseBtn.click();
                            setTimeout(function() {
                                window._sidebarClosing = false;
                            }, 350);
                        }
                    } catch (err) {
                        // Ignore any DOM mutation errors during route transitions
                    }
                };

                document.addEventListener('click', window._sidebarAutoCloseHandler, true);
            })();
        `;
        parentDoc.head.appendChild(scriptEl);
    } catch (e) {
        // Silently catch if in restricted iframe context
    }
})();
</script>
"""

def inject_sidebar_auto_close():
    """Injects lightweight client-side listener to auto-collapse sidebar when clicking outside."""
    import streamlit.components.v1 as components
    components.html(SIDEBAR_AUTO_CLOSE_SCRIPT, height=0, width=0)


