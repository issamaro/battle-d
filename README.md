# Battle-D Web Application

**Dance Battle Tournament Management System** - Production web version

---

## 🎯 Overview

Battle-D is a complete tournament management system for dance battle competitions (breakdancing, hip hop, krump, etc.). Designed for a single organization hosting multiple tournaments per year with ~50 dancers.

**Status:** Phase 0 (POC) - ✅ Deployed on Railway

**Live Demo:** [To be added after deployment]

---

## 🗄️ Database: SQLite

Simple, fast, cost-free database perfect for our scale.

**Why SQLite?**
- Zero cost (vs $5-10/month for PostgreSQL)
- Perfect for ~50 dancers, sequential battles
- Easy backups (just a file)
- Dev = Prod environment

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Navigate to web-app directory
cd web-app

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Open browser
# → http://localhost:8000
```

### Test Accounts (POC)
- `admin@battle-d.com` (Admin)
- `staff@battle-d.com` (Staff)
- `mc@battle-d.com` (MC)

**Magic links** print to console in development mode.

---

## 📚 Documentation

- **[DOMAIN_MODEL.md](DOMAIN_MODEL.md)** - Complete business rules, entities, workflows
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Development roadmap (Phase 0-5)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Railway deployment guide (step-by-step)

---

## ✨ Features

### **Phase 0 (Current) - POC ✅**
- ✅ Magic link authentication (passwordless)
- ✅ Role-based access (Admin/Staff/MC)
- ✅ Hardcoded phase navigation
- ✅ Minimal HTML (zero CSS, structural only)
- ✅ **Deployed on Railway** with SQLite
- ✅ Production emails (Resend)
- ✅ 49 tests passing
- ✅ Cost: ~$0-5/month

### **Phase 1 (Next) - Database + CRUD** 📋
- SQLAlchemy models (User, Dancer, Tournament, etc.)
- Full CRUD interfaces
- **Dancer fields:** email, first_name, last_name, date_of_birth, blaze, country, city
- Staff manage dancers and tournaments
- Admin manage users

### **Phase 2 (Future) - Battle Management** ⏳
- **Mandatory preselection** (always triggered)
- Adaptive pool sizes
- Complete tie-breaking logic
- Sequential battle execution
- Manual score encoding

### **Phase 3 (Future) - Projection Interface** ⏳
- Public display screen
- Live tournament results
- Auto-refresh

### **Phase 4 (Future) - V1 Complete** 🎯
- End-to-end tests
- CI/CD pipeline
- Automated backups
- **V1 RELEASE**

### **Phase 5 (Future) - Judge Interface (V2)** 🎯
- Direct judge scoring
- Blind scoring
- Real-time aggregation
- **V2 RELEASE**

---

## 🏗️ Architecture

```
web-app/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── config.py          # Settings
│   ├── auth.py            # Magic link authentication
│   ├── email_service.py   # Resend email service
│   ├── dependencies.py    # Auth & role decorators
│   ├── routers/           # API routes
│   │   ├── auth.py        # Login, magic links
│   │   └── phases.py      # Phase navigation
│   └── templates/         # Jinja2 HTML
│       ├── base.html
│       ├── dashboard.html
│       ├── auth/
│       └── phases/
│
├── tests/                 # 49 tests (auth, permissions, phases)
│   ├── test_auth.py
│   ├── test_permissions.py
│   └── test_phases.py
│
├── data/                  # SQLite database
│   └── .gitkeep
│
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── railway.json          # Railway configuration
├── Procfile              # Start command
└── .gitignore            # Git ignore rules
```

---

## 🔐 Security

- **Passwordless auth:** Magic links (secure tokens)
- **HttpOnly cookies:** Session management
- **Role-based access:** Admin, Staff, MC, Judge
- **HTTPS only:** Railway provides SSL automatically
- **No plain passwords:** Ever

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Current status
49/49 tests passing ✅
```

---

## 🚢 Deployment (Production)

### Railway + SQLite

**Full deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)

**Quick Steps:**
1. Create Railway project
2. Add Volume (`/data`, 1GB)
3. Deploy from GitHub or CLI
4. Configure environment variables
5. Mount volume to service
6. Test production URL

**Cost:** ~$0-5/month (Railway free tier + Resend free tier)

**Environment Variables:**
- `SECRET_KEY` - Security token
- `DATABASE_URL` - `sqlite:////data/battle_d.db`
- `RESEND_API_KEY` - Email service
- `FROM_EMAIL` - Verified sender
- `BASE_URL` - Railway assigned URL
- `DEBUG` - False (production)

---

## 📊 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Web framework |
| **Templates** | Jinja2 | Server-side rendering |
| **Auth** | itsdangerous | Magic link tokens |
| **Email** | Resend API | Password less login |
| **Database** | SQLite | Data persistence |
| **Hosting** | Railway | Cloud platform |
| **Testing** | pytest + pytest-asyncio | Unit & integration tests |

**No CSS frameworks** - Structural HTML only (by design, AI-first development)

---

## 📖 Domain Model Summary

### **Key Concepts**

**Users (system accounts):**
- Admin, Staff, MC, Judge
- Have email + login access
- Manage the system

**Dancers (performers, no login):**
- Managed by staff
- email, first_name, last_name, date_of_birth, blaze, country, city
- Participate in tournaments
- No application access

### **Tournament Phases (Hardcoded)**

```
Registration → Preselection → Pools → Finals → Completed
```

- **Always 5 phases** in fixed order
- **Global phase** (all categories together)
- **Preselection MANDATORY** (always eliminates some performers)

### **Scoring**

- **Preselection:** Judges score 0-10, average determines qualification
- **Pools:** Win=3pts, Draw=1pt, Loss=0pt
- **Finals:** Win/Loss only (no draws)
- **Tie-breaking:** Automatic battles when tied

**Full details:** [DOMAIN_MODEL.md](DOMAIN_MODEL.md)

---

## 🛣️ Roadmap

| Phase | Status | ETA | Description |
|-------|--------|-----|-------------|
| **Phase 0** | ✅ Complete | Done | POC + Railway deployment |
| **Phase 1** | 📋 Next | +7-10 days | Database + CRUD |
| **Phase 2** | ⏳ Planned | +10-14 days | Battle management |
| **Phase 3** | ⏳ Planned | +3-5 days | Projection screen |
| **Phase 4** | 🎯 Target | +3-5 days | **V1 RELEASE** |
| **Phase 5** | 🎯 Extended | +5-7 days | **V2 RELEASE** (Judge interface) |

**Total V1:** ~26-39 days
**Total V2:** ~31-46 days

**Full roadmap:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

---

## 🤝 Contributing

Solo developer project. No external contributions at this time.

---

## 📝 License

[To be specified]

---

## 🆘 Support

**Documentation:**
- Domain model: [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- Implementation plan: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)

**Issues:**
- Check Railway logs: `railway logs`
- Review test output: `pytest tests/ -v`
- Verify environment variables

---

## 🎉 Achievements

- ✅ Zero-CSS, backend-focused architecture
- ✅ Complete authentication system (magic links)
- ✅ Role-based access control
- ✅ Hardcoded phase navigation
- ✅ 49 tests passing (100%)
- ✅ Production deployment (Railway)
- ✅ Cost-effective (~$0-5/month)
- ✅ Comprehensive documentation

**Next:** Phase 1 - Database + CRUD

---

**Built with ❤️ for the dance battle community**
