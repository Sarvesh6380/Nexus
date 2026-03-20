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

### **Local Development (With Supabase - RECOMMENDED)**

1. **Copy the template:** 
   ```bash
   cp .env.example .env
   ```

2. **Add your credentials to `.env`:**
   ```
   GROQ_API_KEY="your-actual-groq-key"
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_KEY="your-actual-supabase-key"
   HINDSIGHT_API_KEY="your-actual-hindsight-key"
   ```

3. **Run Streamlit:**
   ```bash
   streamlit run app.py
   ```

4. ✅ Teams now persist to both **Supabase** (primary) and **JSON files** (fallback)

### **Local Development (Without Supabase)**
No setup needed! Just run:
```bash
streamlit run app.py
```
Team data automatically persists to `teams_data.json` and `logbook_data.json` (local files only).

### **Streamlit Cloud (With Supabase) - PRODUCTION**
1. Go to your Streamlit app settings → **Secrets**
2. Add these secrets:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   GROQ_API_KEY = "your-groq-key"
   HINDSIGHT_API_KEY = "your-hindsight-key"  
   ```
3. Push to GitHub—Streamlit will auto-deploy
4. ✅ Data persists in Supabase (production-grade)

## 🗄️ Supabase Setup (Optional but Recommended)

### Create Supabase Tables

If using Supabase, create these two tables in your Supabase project:

#### **Table 1: `teams`**
```sql
CREATE TABLE teams (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Table 2: `logbook`**
```sql
CREATE TABLE logbook (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  team TEXT,
  author TEXT,
  content TEXT,
  category TEXT DEFAULT 'general',
  timestamp TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

Then get your credentials from Supabase:
- **Project URL:** Settings → General → Project URL
- **Anon Key:** Settings → API → Project API keys → anon public

## 📋 Changes Made

| File | Changes |
|------|---------|
| `app.py` | Added fallback file persistence for teams & logbook |
| `.gitignore` | Added `teams_data.json`, `logbook_data.json` |
| `.env.example` | Template showing required credentials |
| `DEPLOYMENT_FIX.md` | Setup and troubleshooting guide |

## 🧪 Test It

1. Create a team as **User A** (Leader)
2. See the team appear in session
3. **Sign out**
4. **Sign in as User B** (Member)
5. ✅ Team should now be visible to join!

## 🔧 Troubleshooting

**Teams still not persisting?**

1. **Check if .env credentials are set:**
   ```bash
   cat .env
   ```
   Should show `SUPABASE_URL` and `SUPABASE_KEY` (not empty)

2. **Check if JSON files are being created:**
   ```bash
   ls -la *.json
   ```
   Should show `teams_data.json` and `logbook_data.json`

3. **Check Streamlit terminal for debug logs:**
   Look for these messages:
   - ✅ `[DEBUG] Saved N teams to ...` = File saving works
   - ✅ `[DEBUG] Loaded N teams from ...` = File loading works
   - ❌ If you see 0 teams always = Something is clearing data

4. **In Streamlit app sidebar:**
   Shows "Supabase ✅ / ⬜ / ❌" status
   - ✅ = Supabase connected
   - ❌ = Supabase not configured (use JSON files)
   - ⬜ = Hindsight not configured (optional)
