# Complete Step-by-Step Guide: Dockerizing & Hosting Your Manager Demo

This guide walks you through setting up a dedicated, 24/7 online demo of the **Best Finance Regulatory Assistant** for your supervisor and manager, while keeping your local development code 100% untouched and safe.

---

## The Big Picture (How This Works)

```
[Your Laptop (feature/query-disambiguation)] ---> Stays untouched & safe
                    |
                    v (Create photocopy branch)
[deploy/manager-demo Branch] -------------> Adds Dockerfile & Web PDF links
                    |
                    v (Push to GitHub)
[Hugging Face Spaces or Streamlit Cloud] ---> Runs 24/7 Online for Manager & Supervisor
```

---

## Phase 1: Create Your Isolated Demo Branch

> Creating a separate branch means you can experiment with the cloud setup with **zero risk**. Your main code will never be touched or altered.

1. Open your terminal in VS Code (inside `C:\Users\Banish\RAG_FILESYSTEM`).
2. Run this command to create and switch to your new demo branch:
   ```powershell
   git checkout -b deploy/manager-demo
   ```
3. Verify that you are now on the new branch:
   ```powershell
   git branch
   ```
   *(You will see `* deploy/manager-demo` highlighted).*

---

## Phase 2: Add the 3 Minimal Web Adjustments

On this new branch, we only make 3 small additions:

### 1. Create the `Dockerfile` (What Your Supervisor Asked For)
Create a file named `Dockerfile` (with no file extension) in the root of `C:\Users\Banish\RAG_FILESYSTEM\` with this exact content:

```dockerfile
# Step 1: Use official lightweight Python image
FROM python:3.10-slim

# Step 2: Set working directory inside container
WORKDIR /app

# Step 3: Install system dependencies for PyMuPDF & networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy your project files and pre-built vector database
COPY . .

# Step 6: Expose the standard Streamlit web port
EXPOSE 8501

# Step 7: Start the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableStaticServing=true"]
```

### 2. Make the Sidebar Toggle Button (`[|`) Visible on the Web
In `styles.py`, modern Streamlit uses `[data-testid="stSidebarCollapsedControl"]`. Add this single selector alongside `[data-testid="stExpandSidebarButton"]` so the button displays on the website:

```css
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] button {
    position: fixed !important;
    top: 104px !important;
    left: 24px !important;
    z-index: 1000 !important;
    cursor: pointer !important;
    visibility: visible !important;
    pointer-events: auto !important;
}
```

### 3. Ensure PDFs Open in the Browser
In `app.py`, make sure the "Open Page" buttons open the static web link in a new browser tab:
```python
st.link_button(
    f"Open Page {pg_num} ↗", 
    f"app/static/{safe_filename}#page={pg_num}",
    use_container_width=True
)
```

---

## Phase 3: Commit and Push the Demo Branch to GitHub

Once the 3 additions are in place, save your demo branch to GitHub:

1. Stage all changes:
   ```powershell
   git add Dockerfile styles.py app.py
   ```
2. Commit with a clear message:
   ```powershell
   git commit -m "feat(demo): add Dockerfile and web-friendly navigation for manager demo"
   ```
3. Push this branch to GitHub:
   ```powershell
   git push origin deploy/manager-demo
   ```

---

## Phase 4: Deploy for Free (2 Options)

### Option A: Hugging Face Spaces (Recommended by Senior Engineers — 16 GB RAM Free)
1. Go to [huggingface.co](https://huggingface.co) and sign in (free account).
2. Click **Spaces** → **Create new Space**.
3. Name your space (e.g. `best-finance-assistant`).
4. Under **Select the Space SDK**, select **Docker** → **Blank**.
5. Connect your GitHub repository `banishneupane2002/FinDocs-AI` and select the branch: **`deploy/manager-demo`**.
6. Under **Settings** → **Variables and Secrets**, add your secret key:
   - Name: `GROQ_API_KEY`
   - Value: `gsk_your_groq_key_here`
7. Click **Deploy**. Hugging Face will read your `Dockerfile`, allocate **16 GB of free RAM**, and build the app in about 1 minute!

### Option B: Streamlit Community Cloud (1 GB RAM Free)
If you prefer staying on Streamlit Community Cloud:
1. Open your app on [share.streamlit.io](https://share.streamlit.io).
2. In App Settings, change the **Branch** to: `deploy/manager-demo`.
3. In App Settings → **Secrets**, ensure you have:
   ```toml
   GROQ_API_KEY = "gsk_your_groq_key_here"
   ```
4. Click **Save & Restart**.

---

## Phase 5: How to Switch Back to Your Localhost Anytime

Whenever you want to continue working on your local computer:

1. Switch back to your primary working branch:
   ```powershell
   git checkout feature/query-disambiguation
   ```
2. Run your local app as you always have:
   ```powershell
   streamlit run app.py
   ```

Your local computer remains completely untouched, while your manager and supervisor have their own dedicated link running 24/7!
