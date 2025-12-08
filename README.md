# Battle-D Web Application
**Level 2: Derived** | Last Updated: 2025-11-24

**Dance Battle Tournament Management System** - Production web version

---

## 🎯 Overview

Battle-D is a complete tournament management system for dance battle competitions (breakdancing, hip hop, krump, etc.). Designed for a single organization hosting multiple tournaments per year with ~50 dancers.

**Status:** Phase 1 COMPLETE - ✅ 97+ tests passing

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
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

### One-Command Setup

```bash
# Navigate to web-app directory
cd web-app

# Run setup (creates venv, installs deps, seeds DB, starts server)
./scripts/dev.sh
```

**That's it!** Open http://localhost:8000

### Test Accounts
- `admin@battle-d.com` (Admin)
- `staff@battle-d.com` (Staff)
- `mc@battle-d.com` (MC)

**Magic links** print to console - copy/paste the URL to log in.

### Manual Setup (if preferred)

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed test accounts
python seed_db.py

# Start server
uvicorn app.main:app --reload
```

---

## 📚 Documentation

- **[DOMAIN_MODEL.md](DOMAIN_MODEL.md)** - Complete business rules, entities, workflows
- **[VALIDATION_RULES.md](VALIDATION_RULES.md)** - Phase transition and tournament validation rules
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap (Phase 0-5)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Railway deployment guide (step-by-step)
- **[TESTING.md](TESTING.md)** - Testing guide and best practices

---

## ✨ Features

### **Phase 0 - POC ✅**
- ✅ Magic link authentication (passwordless)
- ✅ Role-based access (Admin/Staff/MC)
- ✅ Minimal HTML (zero CSS, structural only)
- ✅ **Deployed on Railway** with SQLite
- ✅ Production emails (Brevo - no domain required)
- ✅ Cost: ~$0-5/month

### **Phase 1 - Database + CRUD UI ✅ COMPLETE**
- ✅ SQLAlchemy 2.0 async models (User, Dancer, Tournament, Category, Performer)
- ✅ Full CRUD interfaces with HTMX live search
- ✅ **Dancer fields:** email, first_name, last_name, date_of_birth, blaze, country, city
- ✅ Staff manage dancers and tournaments
- ✅ Admin manage users (create, edit, delete, resend magic link)
- ✅ Tournament management with category creation (1v1 and 2v2)
- ✅ Duo pairing registration UI with JavaScript partner selection
- ✅ Database-driven phase navigation with validation
- ✅ Dynamic minimum performer calculation display
- ✅ **Service layer architecture** (DancerService, TournamentService, PerformerService)
- ✅ **Validators & utils** (phase validation, tournament calculations)
- ✅ **Pydantic schemas** for all entities with field validation
- ✅ 97+ tests passing (integration + unit tests)

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
│   ├── dependencies.py    # Auth & role decorators, service factories
│   ├── exceptions.py      # Custom exceptions (ValidationError)
│   ├── services/          # Business services (SOLID principles)
│   │   ├── dancer_service.py       # Dancer CRUD with validation
│   │   ├── tournament_service.py   # Tournament phase management
│   │   ├── performer_service.py    # Registration with duo pairing
│   │   └── email/                  # Email service (Adapter pattern)
│   │       ├── provider.py         # Provider interface
│   │       ├── service.py          # EmailService (DI)
│   │       ├── factory.py          # Provider factory
│   │       ├── templates.py        # Email templates
│   │       └── providers/          # Provider implementations
│   │           ├── brevo_provider.py     # Brevo adapter (recommended)
│   │           ├── resend_provider.py    # Resend adapter
│   │           ├── gmail_provider.py     # Gmail adapter
│   │           └── console_provider.py   # Console adapter (dev)
│   ├── validators/        # Validation logic
│   │   ├── result.py              # ValidationResult dataclass
│   │   └── phase_validators.py    # Phase transition validators
│   ├── utils/             # Utility functions
│   │   └── tournament_calculations.py  # Tournament formulas
│   ├── schemas/           # Pydantic validation schemas
│   │   ├── user.py, dancer.py, tournament.py, category.py, performer.py
│   ├── routers/           # API routes
│   │   ├── auth.py        # Login, magic links
│   │   ├── admin.py       # User management
│   │   ├── dancers.py     # Dancer CRUD
│   │   ├── tournaments.py # Tournament management
│   │   ├── registration.py # Performer registration
│   │   └── phases.py      # Phase navigation
│   └── templates/         # Jinja2 HTML with HTMX
│       ├── base.html
│       ├── auth/, admin/, dancers/, tournaments/, registration/, phases/
│
├── tests/                 # 97+ tests (auth, permissions, models, calculations, workflows)
│   ├── test_auth.py
│   ├── test_permissions.py
│   ├── test_models.py
│   ├── test_tournament_calculations.py
│   ├── test_crud_workflows.py
│   └── test_*_provider.py
│
├── data/                  # SQLite database
│   └── .gitkeep
│
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── railway.json          # Railway configuration
└── .gitignore            # Git ignore rules
```

### Email Service Architecture (Adapter Pattern)

The email system follows **SOLID principles** with the **Adapter Pattern**, making it easy to swap email providers and add new email types:

```
EmailService (Facade)
    ↓ (Dependency Injection)
EmailProvider (Interface)
    ↓
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  BrevoProvider  │ ResendProvider  │  GmailProvider  │ ConsoleProvider │
│  (Recommended)  │ (Req. domain)   │ (Railway block) │ (Development)   │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
         ↓                ↓                ↓                ↓
              ALL use SAME templates from templates.py
```

**Key Principle:** ONE template per email type, shared across ALL providers.

**Benefits:**
- ✅ Easy to switch providers (just change config)
- ✅ Easy to add new email types (15-30 min per type)
- ✅ Consistent email design across all providers
- ✅ Testable with mock providers
- ✅ No code changes when adding new providers
- ✅ Development mode (console) vs Production mode (Brevo/Resend)
- ✅ SDK-verified implementation (Context7 documentation)
- ✅ Brevo: No domain required, works on Railway, 300 emails/day free

**Adding New Email Types (15-30 minutes):**

Follow the 4-step process documented in `app/services/email/provider.py`:

1. **Add templates** to `app/services/email/templates.py`
2. **Add method** to `EmailProvider` interface
3. **Implement** in all 4 providers (Brevo, Resend, Gmail, Console)
4. **Add facade** method to `EmailService`

See inline code comments for detailed examples.

**Adding a New Provider:**

1. Create new provider class implementing `EmailProvider` interface:
```python
# app/services/email/providers/sendgrid_provider.py
from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import generate_magic_link_html, generate_magic_link_subject

class SendGridEmailProvider(BaseEmailProvider):
    async def send_magic_link(self, to_email, magic_link, first_name) -> bool:
        # Use centralized template
        html = generate_magic_link_html(magic_link, first_name)
        subject = generate_magic_link_subject()
        # Implement SendGrid-specific sending logic
        pass
```

2. Update factory in `app/services/email/factory.py`:
```python
if provider_type == "sendgrid":
    return SendGridEmailProvider(...)
```

3. Set `EMAIL_PROVIDER=sendgrid` in `.env`

**Configuration Options:**
- `EMAIL_PROVIDER=brevo` - Use Brevo API (RECOMMENDED for Railway, no domain, 300/day free)
- `EMAIL_PROVIDER=resend` - Use Resend API (requires domain verification)
- `EMAIL_PROVIDER=gmail` - Use Gmail SMTP (BLOCKED on Railway, local dev only)
- `EMAIL_PROVIDER=console` - Print to console (development)

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
97 passed, 8 skipped ✅
```

**Test Coverage:**
- Authentication & sessions (15 tests)
- Email providers (Brevo, Gmail) (13 tests)
- Permissions & role-based access (11 tests)
- Database models & repositories (14 tests)
- Tournament calculations (24 tests)
- CRUD workflows integration (9 tests)
- Email templates (11 tests)

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

**Cost:** ~$0-5/month (Railway free tier + Brevo free tier)

**Environment Variables:**
- `SECRET_KEY` - Security token
- `DATABASE_URL` - `sqlite:////data/battle_d.db`
- `EMAIL_PROVIDER` - `brevo` (recommended), `resend`, `gmail`, or `console`
- `BREVO_API_KEY` - Brevo API key (only if EMAIL_PROVIDER=brevo)
- `BREVO_FROM_EMAIL` - Sender email (only if EMAIL_PROVIDER=brevo)
- `BREVO_FROM_NAME` - Sender name (only if EMAIL_PROVIDER=brevo)
- `RESEND_API_KEY` - Resend API key (only if EMAIL_PROVIDER=resend)
- `GMAIL_EMAIL` - Gmail account email (only if EMAIL_PROVIDER=gmail, local dev only)
- `GMAIL_APP_PASSWORD` - Gmail App Password (only if EMAIL_PROVIDER=gmail, local dev only)
- `BASE_URL` - Railway assigned URL
- `DEBUG` - False (production)

---

## 📊 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Web framework |
| **Templates** | Jinja2 | Server-side rendering |
| **Auth** | itsdangerous | Magic link tokens |
| **Email** | Brevo Python SDK | Passwordless login (adapter pattern, SDK-verified) |
| **Database** | SQLite | Data persistence |
| **Hosting** | Railway | Cloud platform |
| **Testing** | pytest + pytest-asyncio | Unit & integration tests (79 passing) |

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
| **Phase 1** | ✅ Complete | Done | Database + CRUD UI + Service Layer |
| **Phase 2** | 📋 Next | +10-14 days | Battle management |
| **Phase 3** | ⏳ Planned | +3-5 days | Projection screen |
| **Phase 4** | 🎯 Target | +3-5 days | **V1 RELEASE** |
| **Phase 5** | 🎯 Extended | +5-7 days | **V2 RELEASE** (Judge interface) |

**Total V1:** ~16-22 days remaining
**Total V2:** ~21-29 days remaining

**Full roadmap:** [ROADMAP.md](ROADMAP.md)

---

## 🤝 Contributing

Solo developer project. No external contributions at this time.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🆘 Support

**Documentation:**
- Domain model: [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- Project roadmap: [ROADMAP.md](ROADMAP.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Testing guide: [TESTING.md](TESTING.md)

**Issues:**
- Check Railway logs: `railway logs`
- Review test output: `pytest tests/ -v`
- Verify environment variables

---

## 🎉 Achievements

### Phase 0 - POC ✅
- ✅ Zero-CSS, backend-focused architecture
- ✅ Complete authentication system (magic links)
- ✅ Role-based access control
- ✅ Multiple email providers (Brevo recommended for Railway)
- ✅ Production deployment ready (Railway)
- ✅ Cost-effective (~$0-5/month)

### Phase 1 - Database + CRUD ✅
- ✅ SQLAlchemy 2.0 async database with repository pattern
- ✅ Service layer architecture (DancerService, TournamentService, PerformerService)
- ✅ Validators and utils infrastructure (phase validation, tournament calculations)
- ✅ Pydantic schemas for all entities with field validation
- ✅ Full CRUD UIs with HTMX v2.0.4 live search
- ✅ Duo pairing registration with partner linking
- ✅ Database-driven phase navigation with validation
- ✅ Dynamic tournament calculation display
- ✅ 97+ tests passing (auth, permissions, models, calculations, workflows)
- ✅ Comprehensive documentation (DOMAIN_MODEL.md, VALIDATION_RULES.md, ARCHITECTURE.md)

**Next:** Phase 2 - Battle Management

---

**Built with ❤️ for the dance battle community**
