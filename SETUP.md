# Guía de Borrado — Setup Guide

## What you need
- A free **GitHub** account → https://github.com
- A free **Streamlit Cloud** account → https://streamlit.io/cloud (sign in with GitHub)

---

## Step 1 — Create the GitHub repo

1. Go to https://github.com/new
2. Name it `deletion-tracker` (or anything you want)
3. Set it to **Private**
4. Click **Create repository**

---

## Step 2 — Upload the files

In the new repo, upload these files (drag & drop works):

```
app.py
requirements.txt
data.json
.gitignore
```

Do NOT upload `.streamlit/secrets.toml.template` — that's only for your reference.

---

## Step 3 — Create a GitHub Personal Access Token

This lets the app read and write `data.json` automatically.

1. Go to → https://github.com/settings/tokens/new
2. Note: `Deletion Tracker`
3. Expiration: **No expiration** (or 1 year)
4. Scopes: check **`repo`** (the top-level checkbox)
5. Click **Generate token**
6. **Copy the token now** — you won't see it again

---

## Step 4 — Deploy to Streamlit Cloud

1. Go to → https://share.streamlit.io
2. Click **New app**
3. Select your `deletion-tracker` repo
4. Main file path: `app.py`
5. Click **Advanced settings → Secrets** and paste:

```toml
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO  = "your-github-username/deletion-tracker"
```

6. Click **Deploy**

That's it! Streamlit gives you a URL like:
`https://your-username-deletion-tracker-app-xxxx.streamlit.app`

Share that URL with your team — everyone sees the same live state.

---

## How data is saved

Every time someone clicks a checkmark, the app writes directly to `data.json`
in your GitHub repo. You can always open `data.json` on GitHub to see a raw
backup of all checks and logs.

## Adding a new channel

Go to the **⚙ Admin** tab → **Canales** → type the channel name → click
**+ Agregar canal**. Then go to **Prefijos por canal**, select the new channel,
and add prefixes.

## Changing a rule or prefix

Go to **⚙ Admin** → **Prefijos por canal** → find the prefix → use the
dropdown to change the rule, or click ✕ to remove it.

## Year rollover

Checks are stored as `YEAR__PREFIX__MM` (e.g. `2025__NGGTA__03`).
When the year changes, old checks are invisible — the new year starts fresh.
Old log entries remain visible in the **📋 Log** tab filtered by year.
