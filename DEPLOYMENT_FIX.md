# Nexus Deployment Fix: Team Data Persistence

## 🔴 Issue Found & Fixed

**Problem:** When deploying to Streamlit via GitHub, team data was not persisting across user sessions. Teams created by one user were invisible to other users after sign-out/sign-in.

**Root Cause:** 
- Supabase credentials (`SUPABASE_URL`, `SUPABASE_KEY`) were not configured in Streamlit Cloud
- Without these, data was only stored in `st.session_state` (lost on sign-out)
- No fallback persistence existed

## ✅ Solution Implemented

### 1. **Local File Fallback**
- Added `teams_data.json` and `logbook_data.json` as persistent backups
- When Supabase is unavailable, data persists to local JSON files
- Works immediately on any platform (local, Streamlit Cloud, Docker, etc.)

### 2. **Dual-Write Strategy**
- **`sb_save_teams()`** and **`sb_save_log_entry()`** now:
  - Always save to local JSON file (for reliability)
  - Try to sync with Supabase (if configured)
  - Never silently fail—data is always persisted somewhere

### 3. **Fallback Loading**
- **`sb_load_teams()`** and **`sb_load_logbook()`** now:
  - First try Supabase (production ideal)
  - Fall back to local JSON files (if Supabase unavailable)
  - Load fresh data on every new user session

## 🚀 How to Use

### **Local Development (Recommended for Testing)**
No setup needed! Just run:
```bash
streamlit run app.py
```
Team data automatically persists to `teams_data.json` and `logbook_data.json`.

### **Streamlit Cloud (With Supabase)**
1. Go to your Streamlit app settings
2. Add secrets (click **Secrets** dropdown):
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   GROQ_API_KEY = "your-groq-key"
   HINDSIGHT_API_KEY = "your-hindsight-key"
   ```
3. Push to GitHub—Streamlit will auto-deploy
4. Data now syncs with Supabase ✅

### **Streamlit Cloud (Without Supabase)**
- Don't add Supabase secrets
- Data persists to local JSON files (within Streamlit filesystem)
- ⚠️ **Note:** Streamlit Cloud may clear files between deployments—Supabase is recommended for production

## 📋 Changes Made

| File | Changes |
|------|---------|
| `app.py` | Added fallback file persistence for teams & logbook |
| `.gitignore` | Added `teams_data.json`, `logbook_data.json` |

## 🧪 Test It

1. Create a team as **User A** (Leader)
2. See the team appear in session
3. **Sign out**
4. **Sign in as User B** (Member)
5. ✅ Team should now be visible to join!

## 🔧 Troubleshooting

**Teams still not persisting?**
- Check if `teams_data.json` is being created (should be in repo root)
- If it exists but is empty `{}`, all teams were deleted
- Check sidebar—it shows "Supabase ✅ / ⬜ / ❌" status

**Want to use Supabase in production?**
1. Create free Supabase project at https://supabase.com
2. Create tables `teams` and `logbook` with column `data` (JSONB) for teams
3. Add URL and API key to Streamlit secrets

## 📝 Notes

- Data is now **always persisted** (local files as minimum)
- No more silent failures—exceptions are logged
- Backward compatible—existing Supabase setups still work
- Multi-user sessions now work correctly across sign-out/sign-in
