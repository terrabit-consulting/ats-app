# Terrabit ATS (Branded) – Voice AI Interview + PDF + MYR Cost

## Deploy on Streamlit Cloud (no local setup)
1) Create a GitHub repo and upload the **ats_app_branded/** folder (or its contents).
2) In Streamlit Cloud, New app → set Main file path to:
   - `ats_app_branded/app.py` (if you uploaded the folder) OR
   - `app.py` (if you uploaded its contents to repo root)
3) Add Secrets (App → Settings → Secrets):
   ```
   OPENAI_API_KEY = "sk-..."
   ```
4) Allow mic in your browser for voice interview pages.

## Notes
- PDF reports include your logo and brand colors (`branding/logo.png` – replace this with your PNG).
- SQLite (`ats.db`) is created in app folder. On free cloud it may reset on restart.
- Costs appear in sidebar in MYR with per-feature breakdown.
