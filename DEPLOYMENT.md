# Deployment Guide - Railway + SQLite

Step-by-step guide to deploy Battle-D on Railway with SQLite database.

---

## Prerequisites

1. **Railway Account** (free tier available)
   - Sign up at: https://railway.app
   - Free tier: $5/month credit

2. **Resend Account** (for emails)
   - Sign up at: https://resend.com
   - Free tier: 100 emails/day

3. **GitHub Account** (optional but recommended for CI/CD)

---

## Step 1: Setup Resend (Email Service)

### 1.1 Create Account
1. Go to https://resend.com
2. Sign up with email
3. Verify your email address

### 1.2 Verify Domain or Email
**Option A: Use Resend Test Email (Quick Start)**
- No DNS setup needed
- Limited to test emails
- Good for POC/development

**Option B: Verify Custom Domain (Production)**
1. Add your domain in Resend dashboard
2. Add DNS records (SPF, DKIM, DMARC)
3. Wait for verification (5-30 minutes)

### 1.3 Get API Key
1. Dashboard → API Keys
2. Click "Create API Key"
3. Copy the key (starts with `re_`)
4. Save securely (you'll need it for Railway)

---

## Step 2: Generate Secret Key

Generate a secure secret key for your application:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output - you'll need it for Railway environment variables.

---

## Step 3: Create Railway Project

### 3.1 New Project
1. Login to Railway: https://railway.app
2. Click "New Project"
3. Select "Empty Project"

### 3.2 Add Persistent Volume (Critical for SQLite)

⚠️ **This step is essential - without it, your database will be lost on redeploy!**

1. In your project, click "+ New"
2. Select "Volume"
3. Configure:
   - **Name:** `battle-d-data`
   - **Mount Path:** `/data`
   - **Size:** 1 GB (plenty for ~50 dancers, hundreds of tournaments)
4. Click "Create"

---

## Step 4: Deploy Application

### Option A: Deploy from GitHub (Recommended)

1. **Push code to GitHub:**
   ```bash
   cd web-app
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/battle-d-web.git
   git push -u origin main
   ```

2. **Connect to Railway:**
   - In Railway project, click "+ New"
   - Select "GitHub Repo"
   - Authorize Railway to access your repos
   - Select your `battle-d-web` repository
   - Railway will auto-detect Python and start deploying

3. **Set Root Directory (if needed):**
   - If repo contains multiple folders, set root to `web-app/`
   - Settings → Root Directory → `/web-app`

### Option B: Deploy with Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Link project:**
   ```bash
   cd web-app
   railway link
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

---

## Step 5: Configure Environment Variables

In Railway Dashboard → Your Service → Variables, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `SECRET_KEY` | `[generated key from Step 2]` | Security token |
| `DATABASE_URL` | `sqlite:////data/battle_d.db` | Absolute path to volume |
| `RESEND_API_KEY` | `re_xxxxx` | From Resend dashboard |
| `FROM_EMAIL` | `noreply@yourdomain.com` | Verified email on Resend |
| `BASE_URL` | `https://[your-app].up.railway.app` | Auto-assigned by Railway |
| `DEBUG` | `False` | Production mode |

**How to get BASE_URL:**
- Railway assigns it automatically
- Check: Service → Settings → Domains
- Copy the `.up.railway.app` URL

---

## Step 6: Mount Volume to Service

1. Service → Settings → Volumes
2. Click "Mount Volume"
3. Select `battle-d-data`
4. Mount path: `/data` (must match DATABASE_URL)
5. Save

---

## Step 7: Deploy and Test

### 7.1 Trigger Deployment

If using GitHub:
- Push changes triggers auto-deploy
- Or click "Deploy" in Railway dashboard

If using CLI:
- Run `railway up`

### 7.2 Monitor Deployment

1. Railway → Deployments tab
2. Watch build logs
3. Wait for "Deployment successful" message (usually 2-5 minutes)

### 7.3 Test Application

1. **Health Check:**
   ```bash
   curl https://[your-app].up.railway.app/health
   ```
   Should return: `{"status":"ok","app":"Battle-D"}`

2. **Login Page:**
   - Open: `https://[your-app].up.railway.app`
   - Should redirect to `/auth/login`
   - See login form with test accounts listed

3. **Send Magic Link:**
   - Enter: `admin@battle-d.com`
   - Check email (if Resend configured)
   - Or check Railway logs for magic link (printed to console in dev mode)

4. **Login and Test:**
   - Click magic link from email
   - Should redirect to dashboard
   - Test phase navigation

---

## Step 8: Database Initialization (Phase 1+)

When you add SQLAlchemy in Phase 1:

```bash
# Run migrations via Railway CLI
railway run alembic upgrade head
```

Or add to start command:
```
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Backup Strategy

### Manual Backup

Download database from Railway:

```bash
# Via Railway CLI
railway run cat /data/battle_d.db > backup_$(date +%Y%m%d).db
```

### Automated Backup (Phase 4)

**Option A: Railway Cron**
- Add cron service to Railway project
- Schedule daily backups
- Upload to S3/Cloudflare R2

**Option B: GitHub Actions**
- Scheduled workflow
- Download DB via Railway API
- Commit to backup branch or upload to storage

**Retention:** Keep last 30 days

---

## Monitoring

### Railway Dashboard
- Service → Metrics
- CPU usage
- Memory usage
- Request count
- Errors

### Logs
- Service → Logs
- Real-time log streaming
- Filter by severity
- Search functionality

### Alerts (Optional)
- Railway integrations
- Slack/Discord webhooks
- Email notifications on crashes

---

## CI/CD Setup (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd web-app
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd web-app
          pytest tests/ -v

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: battle-d-web
```

**Setup:**
1. Railway → Account Settings → Tokens → Create Token
2. GitHub → Repo Settings → Secrets → Add `RAILWAY_TOKEN`

---

## Costs Breakdown

### Railway (Free Tier)

| Resource | Free Tier | Estimated Usage | Cost |
|----------|-----------|-----------------|------|
| Web Service | $5/month credit | $0-5/month | Covered by free tier |
| Volume (1GB) | Included | Minimal | $0 |
| **Total** | | | **~$0-5/month** |

### Resend

| Plan | Emails | Cost |
|------|--------|------|
| Free | 100/day | $0 |
| **Estimated usage** | **~10-20/day** | **$0** |

### Total Monthly Cost: ~$0-5

**Scaling Costs:**
- If usage exceeds free tier: ~$5-15/month
- Still much cheaper than PostgreSQL hosting (~$10-20/month)

---

## Troubleshooting

### Build Failures

**Issue:** `requirements.txt not found`
- **Solution:** Check Root Directory setting (should be `/web-app` if in subdirectory)

**Issue:** Python version mismatch
- **Solution:** Add `runtime.txt` with `python-3.11` (or your version)

### Runtime Errors

**Issue:** `500 Internal Server Error`
- **Solution:** Check logs: `railway logs`
- Look for stack traces
- Verify environment variables

**Issue:** `Database is locked`
- **Solution:** SQLite doesn't handle high concurrency well
- Check if multiple processes trying to write
- Consider PostgreSQL if concurrent writes > 10/sec

**Issue:** Magic links not received
- **Solution:**
  - Check `RESEND_API_KEY` is set correctly
  - Verify `FROM_EMAIL` is verified in Resend
  - Check Resend dashboard for delivery logs
  - Look for printed magic links in Railway logs (dev mode)

### Volume Issues

**Issue:** Database lost after redeploy
- **Solution:** Verify volume is mounted to `/data`
- Check `DATABASE_URL` uses absolute path: `sqlite:////data/battle_d.db`

**Issue:** Permission denied writing to `/data`
- **Solution:** Railway volumes should have correct permissions by default
- Try: `railway run ls -la /data` to check

---

## Security Best Practices

1. **Never commit secrets:**
   - Add `.env` to `.gitignore` (already done)
   - Use Railway environment variables

2. **Rotate SECRET_KEY:**
   - Change periodically (every 6-12 months)
   - Invalidates existing sessions

3. **HTTPS Only:**
   - Railway provides HTTPS automatically
   - Never use HTTP in production

4. **Monitor logs:**
   - Check for suspicious login attempts
   - Alert on repeated failures

5. **Backup regularly:**
   - Test restore process
   - Keep backups off-platform

---

## Rollback Procedure

If deployment breaks:

1. **Railway Dashboard:**
   - Deployments tab
   - Find last working deployment
   - Click "Redeploy"

2. **Via Git:**
   ```bash
   git revert HEAD
   git push origin main
   ```

3. **Database Rollback:**
   ```bash
   # Restore from backup
   railway run sh -c "cat > /data/battle_d.db" < backup_YYYYMMDD.db
   ```

---

## Scaling Considerations

### When to Migrate from SQLite

Consider PostgreSQL when:
- 500+ active dancers
- 20+ concurrent users writing
- 100+ tournaments/year
- Need multi-server deployment

**Migration is Easy:**
1. Add PostgreSQL service on Railway (one click)
2. Update `DATABASE_URL`
3. Run migrations: `alembic upgrade head`
4. SQLAlchemy handles the rest (same code)

### Performance Optimization

If app slows down:
- Add database indexes (Phase 1+)
- Enable SQLite WAL mode (better concurrency)
- Add Redis caching for read-heavy operations
- Profile slow queries

---

## Support

**Railway Issues:**
- Docs: https://docs.railway.app
- Community: Railway Discord

**Application Issues:**
- Check logs first
- Review DOMAIN_MODEL.md for business logic
- Test locally with same database

---

## Next Steps After Deployment

1. ✅ Test all features in production
2. ✅ Configure automated backups
3. ✅ Set up monitoring alerts
4. ✅ Document production URL in README
5. ✅ Train staff on new system
6. ✅ Start Phase 1 development (Database + CRUD)

---

**Deployment Complete! 🎉**

Your Battle-D application is now live on Railway with production-grade setup, costing ~$0-5/month.
