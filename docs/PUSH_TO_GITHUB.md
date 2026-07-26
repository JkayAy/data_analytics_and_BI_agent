# Push to GitHub (checklist)

## 1. Create repo

1. GitHub → **New repository** → name e.g. `insightbridge` → public → no README (you have one).
2. Copy the remote URL.

## 2. Initialize git (from project root)

```bash
git init
git add .
git status   # confirm .env is NOT listed
git commit -m "InsightBridge: conversational BI agent portfolio v1"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/insightbridge.git
git push -u origin main
```

## 3. Replace placeholders

Search repo for `YOUR_USERNAME` and update:

- `README.md` — badge URL, GitHub link, live demo URL
- `apps/web/components/SiteNav.tsx` — or set `NEXT_PUBLIC_GITHUB_URL` on Vercel
- `apps/web/app/about/page.tsx` — GitHub link

## 4. Pin & topics

Profile → **Pinned** → pin `insightbridge`.

Topics: `text-to-sql`, `fastapi`, `nextjs`, `postgresql`, `business-intelligence`, `openai`, `data-analytics`

## 5. CI badge

After first push, the CI badge in README should turn green if Actions ran successfully.

## 6. Before sharing with employers

- [ ] Live Vercel URL in README (optional but strong)
- [ ] 90s Loom: ask MRR by region → show SQL → mention audit page
- [ ] LinkedIn + resume link to **live demo**, not only GitHub
- [ ] `.env` never committed (only `.env.example`)

## 7. Secrets reminder

| Secret | Where |
|--------|--------|
| `DATABASE_URL` | Railway API service |
| `OPENAI_API_KEY` | Railway (optional) |
| `CORS_ORIGINS` | Railway = your Vercel URL |
| `API_KEY` / `NEXT_PUBLIC_API_KEY` | Optional pair if you lock POST routes |
| `DEMO_ACCESS_PASSWORD` | Vercel only — optional public demo lock |

Never commit API keys or production database URLs.
