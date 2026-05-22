# Deploying SmartSpend to Render (Free)

## Prerequisites
- A [GitHub](https://github.com) account (free)
- A [Render](https://render.com) account (free)
- [Git](https://git-scm.com/downloads) installed on your machine

---

## Step 1 — Push to GitHub

Open a terminal in the `SmartSpend` project folder and run:

```bash
git init
git add .
git commit -m "Initial SmartSpend commit"
```

Create a new repo on GitHub (github.com → New repository → name it `smartspend` → Create).
Then push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/smartspend.git
git branch -M main
git push -u origin main
```

---

## Step 2 — Create a Web Service on Render

1. Go to [render.com](https://render.com) and sign in
2. Click **New → Web Service**
3. Connect your GitHub account and select the `smartspend` repo
4. Fill in the settings:

| Field | Value |
|-------|-------|
| Name | `smartspend` |
| Runtime | `Python 3` |
| Build Command | `./build.sh` |
| Start Command | `gunicorn spems.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

---

## Step 3 — Set Environment Variables

In the Render dashboard → your service → **Environment**, add:

| Key | Value |
|-----|-------|
| `DJANGO_SETTINGS_MODULE` | `spems.settings_prod` |
| `SECRET_KEY` | *(click Generate)* |
| `PYTHON_VERSION` | `3.11.0` |

> `DATABASE_URL` is set automatically if you add a Postgres database (optional).
> Without it, the app uses SQLite on a persistent disk (configured in render.yaml).

---

## Step 4 — Add a Persistent Disk (for SQLite)

In Render → your service → **Disks** → Add Disk:

| Field | Value |
|-------|-------|
| Name | `spems-data` |
| Mount Path | `/opt/render/project/src/spems` |
| Size | `1 GB` (free tier) |

This keeps your SQLite database across deploys.

---

## Step 5 — Deploy

Click **Deploy**. Render will:
1. Install dependencies from `requirements.txt`
2. Run `collectstatic`
3. Run `migrate`
4. Start gunicorn

Your app will be live at `https://smartspend.onrender.com` (or similar).

---

## Step 6 — Create Admin User (one-time)

In Render → your service → **Shell**:

```bash
python manage.py createsuperuser
```

---

## Optional — Add PostgreSQL (recommended for production)

1. Render → **New → PostgreSQL** → Free tier
2. Copy the **Internal Database URL**
3. Add it as `DATABASE_URL` environment variable on your web service
4. Redeploy

---

## Notes

- Free tier on Render spins down after 15 minutes of inactivity — first request after sleep takes ~30 seconds to wake up. This is normal on the free plan.
- To avoid spin-down, upgrade to Render's Starter plan ($7/mo) or use [UptimeRobot](https://uptimerobot.com) (free) to ping your app every 10 minutes.
- Never commit `.env` files or your `SECRET_KEY` to Git.
