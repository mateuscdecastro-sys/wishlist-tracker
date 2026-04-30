# Setup Guide

## 1. Create a GitHub repository

Go to github.com → New repository. It can be **private** (recommended, since it stores your wishlist URL).

Push this folder to it:
```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

---

## 2. Get your Amazon wishlist URL

1. Go to your Amazon account → Lists → your wishlist
2. Copy the URL from your browser — it looks like:
   `https://www.amazon.com/hz/wishlist/ls/XXXXXXXXXX`
3. Paste it into `config.json` under `"wishlist_url"`

---

## 3. Export your Amazon session cookies

Your private wishlist requires you to be logged in. The script uses your browser cookies to authenticate.

1. Install the **Cookie-Editor** browser extension:
   - Chrome: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/

2. Go to **amazon.com** while logged in to your account

3. Click the Cookie-Editor icon → click **Export** (exports as JSON) → copy the full JSON text

4. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `AMAZON_COOKIES`
   - Value: paste the JSON you copied
   - Click **Add secret**

> **Note:** Amazon cookies expire after roughly 30 days. When they do, the script will send you an ntfy notification asking you to repeat this step.

---

## 4. Set up ntfy on your phone

1. Install the **ntfy** app on your Android phone (free, on Play Store)
2. Choose a unique topic name — something hard to guess, like `mateus-wishlist-abc123`
3. In the ntfy app: tap **+** → enter your topic name → subscribe
4. Put the same topic name in `config.json` under `"ntfy_topic"`

No account needed. Anyone who knows your topic name can send you notifications, so keep it private.

---

## 5. Edit config.json

Open `config.json` and fill in your values:

```json
{
  "wishlist_url": "https://www.amazon.com/hz/wishlist/ls/YOUR_LIST_ID",
  "ntfy_topic": "mateus-wishlist-abc123",
  "threshold": 0.40
}
```

`threshold: 0.40` means notify when price drops 40% or more from the first time the item was seen.

---

## 6. Push your changes and test

```bash
git add config.json
git commit -m "add config"
git push
```

Then go to your repo on GitHub → **Actions** tab → click **Wishlist Price Tracker** → **Run workflow** → **Run workflow**.

Watch the logs — you should see your wishlist items listed with prices.

### Test notifications

To force a test notification, temporarily set `"threshold": 0.0` in `config.json`, push, and run the workflow manually. Every item will trigger a notification. Reset to `0.40` after confirming it works.

---

## 7. Done

The workflow now runs every hour automatically. Check the **Actions** tab anytime to see the last run. Price history is saved in `prices.json` in the repo.
