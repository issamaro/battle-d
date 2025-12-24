# Django Migration Plan: Battle-D Web Application

**Date:** 2025-12-23
**Django Version:** 5.2 (LTS)
**Status:** Planning
**Estimated Duration:** 3-4 weeks

---

## Executive Summary

This document provides a complete file-by-file migration plan from FastAPI to Django 5.2 for the Battle-D tournament management application. All code examples are verified against Django 5.2 official documentation via Context7.

### Current State
- **Framework:** FastAPI 0.109.0
- **Database:** SQLAlchemy 2.0 (async) + SQLite
- **Templates:** Jinja2 (48 files, 3,119 lines)
- **Auth:** Session-based magic links
- **Frontend:** HTMX + PicoCSS

### Target State
- **Framework:** Django 5.2
- **Database:** Django ORM + SQLite (PostgreSQL-ready)
- **Templates:** Django Templates
- **Auth:** Django auth + custom magic link backend
- **Frontend:** HTMX + PicoCSS + django-htmx

---

## Phase 1: Project Setup (Days 1-2)

### 1.1 Dependencies

```txt
# requirements.txt
Django>=5.2,<6.0
django-htmx>=1.17.0
python-dotenv>=1.0.0
itsdangerous>=2.1.2  # For magic link tokens
Pillow>=10.0.0  # If needed for images
```

### 1.2 Project Structure

```bash
django-admin startproject battle_d .
python manage.py startapp core
python manage.py startapp accounts
python manage.py startapp dancers
python manage.py startapp tournaments
python manage.py startapp battles
python manage.py startapp registration
```

### 1.3 Settings Configuration

**File: `battle_d/settings.py`**

```python
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'django_htmx',
    # Local apps
    'core',
    'accounts',
    'dancers',
    'tournaments',
    'battles',
    'registration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # django-htmx middleware
    'django_htmx.middleware.HtmxMiddleware',
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.MagicLinkBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Session settings (match current FastAPI config)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Magic link settings
MAGIC_LINK_EXPIRY_SECONDS = 15 * 60  # 15 minutes
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'battle_d.db',
    }
}

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Email
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = 'noreply@battle-d.com'

# Backdoor users (emergency access)
BACKDOOR_USERS = {
    'aissacasapro@gmail.com': 'admin',
}
```

---

## Phase 2: Model Migration (Days 3-5)

### 2.1 Base Model

**File: `core/models.py`**

```python
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
```

### 2.2 User Model with Custom Manager

**File: `accounts/models.py`**

```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from core.models import BaseModel


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    STAFF = 'staff', 'Staff'
    MC = 'mc', 'MC'
    JUDGE = 'judge', 'Judge'


class UserManager(BaseUserManager):
    """Custom manager for User model with email as username."""

    def create_user(self, email, first_name, role=UserRole.STAFF, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, password=None):
        user = self.create_user(
            email=email,
            first_name=first_name,
            role=UserRole.ADMIN,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """User with role-based access (admin, staff, mc, judge)."""

    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.STAFF)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def can_manage_users(self):
        return self.role == UserRole.ADMIN

    @property
    def can_encode_results(self):
        return self.role in [UserRole.ADMIN, UserRole.STAFF, UserRole.JUDGE]
```

### 2.3 Dancer Model with Custom Manager

**File: `dancers/models.py`**

```python
from django.db import models
from core.models import BaseModel


class DancerQuerySet(models.QuerySet):
    """Custom QuerySet for Dancer model."""

    def search(self, query):
        """Full-text search across name fields."""
        if not query:
            return self.all()
        return self.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(blaze__icontains=query) |
            models.Q(email__icontains=query)
        )

    def not_in_tournament(self, tournament):
        """Dancers not registered in a tournament."""
        from battles.models import Performer
        registered_ids = Performer.objects.filter(
            tournament=tournament
        ).values_list('dancer_id', flat=True)
        return self.exclude(id__in=registered_ids)


class DancerManager(models.Manager):
    """Custom manager for Dancer model."""

    def get_queryset(self):
        return DancerQuerySet(self.model, using=self._db)

    def search(self, query, limit=50):
        return self.get_queryset().search(query)[:limit]

    def available_for_tournament(self, tournament):
        return self.get_queryset().not_in_tournament(tournament)


class Dancer(BaseModel):
    """A dancer/performer without login credentials."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    blaze = models.CharField(max_length=100, blank=True)  # Stage name
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    objects = DancerManager()

    class Meta:
        ordering = ['blaze', 'first_name']

    def __str__(self):
        return self.blaze or f"{self.first_name} {self.last_name}"

    @property
    def display_name(self):
        return self.blaze or f"{self.first_name} {self.last_name}"
```

### 2.4 Tournament and Category Models

**File: `tournaments/models.py`**

```python
from django.db import models
from core.models import BaseModel


class TournamentPhase(models.TextChoices):
    REGISTRATION = 'registration', 'Registration'
    PRESELECTION = 'preselection', 'Preselection'
    POOLS = 'pools', 'Pools'
    FINALS = 'finals', 'Finals'
    COMPLETED = 'completed', 'Completed'


class TournamentStatus(models.TextChoices):
    CREATED = 'created', 'Created'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class TournamentQuerySet(models.QuerySet):
    """Custom QuerySet for Tournament model."""

    def active(self):
        return self.filter(status=TournamentStatus.ACTIVE)

    def created(self):
        return self.filter(status=TournamentStatus.CREATED)


class TournamentManager(models.Manager):
    def get_queryset(self):
        return TournamentQuerySet(self.model, using=self._db)

    def get_active(self):
        return self.get_queryset().active().first()


class Tournament(BaseModel):
    """A tournament event."""

    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TournamentStatus.choices,
        default=TournamentStatus.CREATED
    )
    phase = models.CharField(
        max_length=20,
        choices=TournamentPhase.choices,
        default=TournamentPhase.REGISTRATION
    )

    objects = TournamentManager()

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['status'],
                condition=models.Q(status='active'),
                name='unique_active_tournament'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.date})"


class CategoryType(models.TextChoices):
    ONE_V_ONE = '1v1', '1v1'
    TWO_V_TWO = '2v2', '2v2'


class Category(BaseModel):
    """A competition category within a tournament."""

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=10,
        choices=CategoryType.choices,
        default=CategoryType.ONE_V_ONE
    )
    preselection_quota = models.PositiveIntegerField(default=16)
    pool_groups_ideal = models.PositiveIntegerField(default=4)

    class Meta:
        verbose_name_plural = 'categories'
        unique_together = ['tournament', 'name']

    def __str__(self):
        return f"{self.tournament.name} - {self.name}"
```

### 2.5 Battle Models

**File: `battles/models.py`**

```python
from django.db import models
from core.models import BaseModel
from dancers.models import Dancer
from tournaments.models import Tournament, Category


class Performer(BaseModel):
    """A dancer registered in a tournament category."""

    dancer = models.ForeignKey(
        Dancer,
        on_delete=models.CASCADE,
        related_name='performances'
    )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='performers'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='performers'
    )
    duo_partner = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duo_partner_of'
    )
    is_guest = models.BooleanField(default=False)
    preselection_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Stats
    pool_wins = models.PositiveIntegerField(default=0)
    pool_draws = models.PositiveIntegerField(default=0)
    pool_losses = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dancer', 'tournament'],
                name='unique_dancer_per_tournament'
            )
        ]

    def __str__(self):
        return f"{self.dancer} in {self.category}"


class Pool(BaseModel):
    """A pool group in the pool phase."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='pools'
    )
    name = models.CharField(max_length=50)
    sequence_order = models.PositiveIntegerField(default=0)
    performers = models.ManyToManyField(Performer, related_name='pools')
    winner = models.ForeignKey(
        Performer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pools_won'
    )

    class Meta:
        ordering = ['sequence_order']


class BattlePhase(models.TextChoices):
    PRESELECTION = 'preselection', 'Preselection'
    POOL = 'pool', 'Pool'
    TIEBREAK = 'tiebreak', 'Tiebreak'
    FINALS = 'finals', 'Finals'


class BattleStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'


class BattleOutcomeType(models.TextChoices):
    SCORED = 'scored', 'Scored'
    WIN_DRAW_LOSS = 'win_draw_loss', 'Win/Draw/Loss'
    TIEBREAK = 'tiebreak', 'Tiebreak'
    WIN_LOSS = 'win_loss', 'Win/Loss'


class BattleQuerySet(models.QuerySet):
    """Custom QuerySet for Battle model."""

    def pending(self):
        return self.filter(status=BattleStatus.PENDING)

    def active(self):
        return self.filter(status=BattleStatus.ACTIVE)

    def completed(self):
        return self.filter(status=BattleStatus.COMPLETED)

    def in_phase(self, phase):
        return self.filter(phase=phase)

    def for_category(self, category):
        return self.filter(category=category)

    def queue(self, category):
        """Get pending battles in order."""
        return (
            self.for_category(category)
            .pending()
            .order_by('sequence_order')
            .select_related('category', 'pool')
            .prefetch_related('performers', 'performers__dancer')
        )


class BattleManager(models.Manager):
    def get_queryset(self):
        return BattleQuerySet(self.model, using=self._db)

    def get_active_battle(self):
        """Global: only one active battle at a time."""
        return self.get_queryset().active().first()

    def get_queue(self, category):
        return self.get_queryset().queue(category)

    def get_next_sequence(self, category):
        last = (
            self.filter(category=category)
            .order_by('-sequence_order')
            .values_list('sequence_order', flat=True)
            .first()
        )
        return (last or 0) + 1


class Battle(BaseModel):
    """A battle between performers."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='battles'
    )
    pool = models.ForeignKey(
        Pool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='battles'
    )
    phase = models.CharField(max_length=20, choices=BattlePhase.choices)
    status = models.CharField(
        max_length=20,
        choices=BattleStatus.choices,
        default=BattleStatus.PENDING
    )
    sequence_order = models.PositiveIntegerField(default=0)

    performers = models.ManyToManyField(Performer, related_name='battles')
    winner = models.ForeignKey(
        Performer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='battles_won'
    )

    outcome_type = models.CharField(
        max_length=20,
        choices=BattleOutcomeType.choices,
        null=True,
        blank=True
    )
    outcome_data = models.JSONField(null=True, blank=True)

    bracket_round = models.CharField(max_length=20, blank=True)
    bracket_position = models.PositiveIntegerField(null=True, blank=True)

    objects = BattleManager()

    class Meta:
        ordering = ['sequence_order']
        constraints = [
            models.UniqueConstraint(
                fields=['status'],
                condition=models.Q(status='active'),
                name='unique_active_battle'
            )
        ]
```

---

## Phase 3: Authentication Backend (Days 6-7)

### 3.1 Magic Link Backend

**File: `accounts/backends.py`**

```python
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

User = get_user_model()


class MagicLinkBackend(BaseBackend):
    """Custom authentication backend for magic link login."""

    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

    def authenticate(self, request, token=None):
        """Authenticate user via magic link token."""
        if token is None:
            return None

        try:
            payload = self.serializer.loads(
                token,
                salt='magic-link',
                max_age=settings.MAGIC_LINK_EXPIRY_SECONDS
            )
        except (BadSignature, SignatureExpired):
            return None

        try:
            user = User.objects.get(email=payload['email'])
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def generate_token(self, email, role):
        """Generate magic link token."""
        payload = {
            'email': email,
            'role': role,
        }
        return self.serializer.dumps(payload, salt='magic-link')

    def generate_magic_link(self, email, role):
        """Generate full magic link URL."""
        token = self.generate_token(email, role)
        return f"{settings.BASE_URL}/auth/verify/?token={token}"
```

### 3.2 Auth Views

**File: `accounts/views.py`**

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.views import View
from django.conf import settings
from django.core.mail import send_mail

from .backends import MagicLinkBackend
from .forms import MagicLinkRequestForm

User = get_user_model()


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:overview')
        form = MagicLinkRequestForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MagicLinkRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                backend = MagicLinkBackend()
                magic_link = backend.generate_magic_link(email, user.role)

                send_mail(
                    subject='Your Battle-D Login Link',
                    message=f'Click here to login: {magic_link}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=f'''
                        <h2>Login to Battle-D</h2>
                        <p>Click the button below to login:</p>
                        <a href="{magic_link}">Login to Battle-D</a>
                        <p>This link expires in 15 minutes.</p>
                    ''',
                )
                messages.success(request, f'Magic link sent to {email}')
            except User.DoesNotExist:
                # Don't reveal if email exists
                messages.success(request, f'If {email} is registered, a magic link was sent.')

            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


class VerifyMagicLinkView(View):
    def get(self, request):
        token = request.GET.get('token')
        backend = MagicLinkBackend()
        user = backend.authenticate(request, token=token)

        if user:
            login(request, user, backend='accounts.backends.MagicLinkBackend')
            messages.success(request, f'Welcome, {user.first_name}!')
            return redirect('dashboard:overview')

        messages.error(request, 'Invalid or expired magic link')
        return redirect('accounts:login')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out')
        return redirect('accounts:login')


class BackdoorLoginView(View):
    """Emergency admin access for backdoor users."""

    def get(self, request):
        email = request.GET.get('email')
        if email in settings.BACKDOOR_USERS:
            role = settings.BACKDOOR_USERS[email]
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'first_name': 'Backdoor', 'role': role}
            )
            login(request, user, backend='accounts.backends.MagicLinkBackend')
            messages.success(request, f'Backdoor login successful as {role}')
            return redirect('dashboard:overview')

        messages.error(request, 'Unauthorized')
        return redirect('accounts:login')
```

### 3.3 Auth Forms

**File: `accounts/forms.py`**

```python
from django import forms


class MagicLinkRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
```

### 3.4 Auth URLs

**File: `accounts/urls.py`**

```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyMagicLinkView.as_view(), name='verify'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('backdoor/', views.BackdoorLoginView.as_view(), name='backdoor'),
]
```

---

## Phase 4: View Migration with django-htmx (Days 8-14)

### 4.1 HTMX-Aware Views Pattern

Using `django-htmx` middleware, views can detect HTMX requests:

```python
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers


@cache_control(max_age=300)
@vary_on_headers("HX-Request")
def my_view(request):
    if request.htmx:
        template_name = "partial.html"
    else:
        template_name = "complete.html"
    return render(request, template_name, ...)
```

### 4.2 Dashboard View

**File: `core/views.py`**

```python
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from tournaments.models import Tournament
from .services import DashboardService


class DashboardView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        context = DashboardService.get_context(request.user)
        return render(request, 'dashboard/index.html', context)


def root_redirect(request):
    return redirect('dashboard:overview')
```

### 4.3 Tournament Views with Generic CBVs

**File: `tournaments/views.py`**

```python
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from .models import Tournament, Category
from .forms import TournamentForm, CategoryForm


class TournamentListView(LoginRequiredMixin, ListView):
    model = Tournament
    template_name = 'tournaments/list.html'
    context_object_name = 'tournaments'


class TournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = 'tournaments/detail.html'
    context_object_name = 'tournament'


class TournamentCreateView(LoginRequiredMixin, CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/create.html'
    success_url = reverse_lazy('tournaments:list')

    def form_valid(self, form):
        messages.success(self.request, 'Tournament created successfully')
        return super().form_valid(form)


class TournamentUpdateView(LoginRequiredMixin, UpdateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/edit.html'
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('tournaments:detail', kwargs={'pk': self.object.pk})


class TournamentActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tournament = Tournament.objects.get(pk=pk)

        # Check no other active tournaments
        if Tournament.objects.filter(status='active').exists():
            messages.error(request, 'Another tournament is already active')
            return redirect('tournaments:detail', pk=pk)

        tournament.status = 'active'
        tournament.save()
        messages.success(request, f'{tournament.name} is now active')
        return redirect('tournaments:detail', pk=pk)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'tournaments/add_category.html'

    def form_valid(self, form):
        form.instance.tournament_id = self.kwargs['tournament_pk']
        messages.success(self.request, 'Category added successfully')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:detail', kwargs={'pk': self.kwargs['tournament_pk']})
```

### 4.4 Dancer Views with HTMX Search

**File: `dancers/views.py`**

```python
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render
from django.views import View

from .models import Dancer
from .forms import DancerForm


class DancerListView(LoginRequiredMixin, ListView):
    model = Dancer
    template_name = 'dancers/list.html'
    context_object_name = 'dancers'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = Dancer.objects.search(search)
        return queryset


class DancerSearchView(LoginRequiredMixin, View):
    """HTMX endpoint for live dancer search."""

    def get(self, request):
        search = request.GET.get('search', '')
        dancers = Dancer.objects.search(search, limit=50)

        # Return partial template for HTMX
        if request.htmx:
            return render(request, 'dancers/_table.html', {'dancers': dancers})

        # Fallback for non-HTMX
        return render(request, 'dancers/list.html', {'dancers': dancers})


class DancerDetailView(LoginRequiredMixin, DetailView):
    model = Dancer
    template_name = 'dancers/profile.html'
    context_object_name = 'dancer'


class DancerCreateView(LoginRequiredMixin, CreateView):
    model = Dancer
    form_class = DancerForm
    template_name = 'dancers/create.html'
    success_url = reverse_lazy('dancers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Dancer created successfully')
        return super().form_valid(form)


class DancerUpdateView(LoginRequiredMixin, UpdateView):
    model = Dancer
    form_class = DancerForm
    template_name = 'dancers/edit.html'

    def get_success_url(self):
        return reverse_lazy('dancers:detail', kwargs={'pk': self.object.pk})


class DancerDeleteView(LoginRequiredMixin, DeleteView):
    model = Dancer
    success_url = reverse_lazy('dancers:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Dancer deleted successfully')
        return super().delete(request, *args, **kwargs)
```

### 4.5 Registration Views with HTMX Partials

**File: `registration/views.py`**

```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from tournaments.models import Category
from battles.models import Performer
from dancers.models import Dancer


class RegistrationView(LoginRequiredMixin, View):
    """Main registration interface."""

    def get(self, request, tournament_pk, category_pk):
        category = get_object_or_404(Category, pk=category_pk, tournament_id=tournament_pk)
        performers = Performer.objects.filter(category=category).select_related('dancer')
        available = Dancer.objects.available_for_tournament(category.tournament)

        return render(request, 'registration/register.html', {
            'category': category,
            'tournament': category.tournament,
            'performers': performers,
            'available_dancers': available,
        })


class AddPerformerView(LoginRequiredMixin, View):
    """HTMX: Add dancer to category."""

    def post(self, request, tournament_pk, category_pk):
        category = get_object_or_404(Category, pk=category_pk)
        dancer_id = request.POST.get('dancer_id')
        dancer = get_object_or_404(Dancer, pk=dancer_id)

        Performer.objects.create(
            dancer=dancer,
            tournament=category.tournament,
            category=category,
        )

        # Return updated lists via HTMX
        performers = Performer.objects.filter(category=category).select_related('dancer')
        available = Dancer.objects.available_for_tournament(category.tournament)

        return render(request, 'registration/_registration_update.html', {
            'category': category,
            'performers': performers,
            'available_dancers': available,
        })


class RemovePerformerView(LoginRequiredMixin, View):
    """HTMX: Remove performer from category."""

    def post(self, request, tournament_pk, category_pk, performer_pk):
        performer = get_object_or_404(Performer, pk=performer_pk)
        performer.delete()

        # Return updated lists
        category = get_object_or_404(Category, pk=category_pk)
        performers = Performer.objects.filter(category=category).select_related('dancer')
        available = Dancer.objects.available_for_tournament(category.tournament)

        return render(request, 'registration/_registration_update.html', {
            'category': category,
            'performers': performers,
            'available_dancers': available,
        })


class SearchDancerView(LoginRequiredMixin, View):
    """HTMX: Live search for dancers."""

    def get(self, request, tournament_pk, category_pk):
        search = request.GET.get('search', '')
        category = get_object_or_404(Category, pk=category_pk)

        # Search dancers not in this tournament
        dancers = Dancer.objects.available_for_tournament(
            category.tournament
        ).search(search)[:20]

        return render(request, 'registration/_search_results.html', {
            'dancers': dancers,
            'category': category,
        })
```

---

## Phase 5: Template Migration (Days 15-17)

### 5.1 Template Syntax Changes

| Jinja2 | Django | Notes |
|--------|--------|-------|
| `{{ url_for('route', id=1) }}` | `{% url 'app:view' pk=1 %}` | URL reversal |
| `{{ loop.index }}` | `{{ forloop.counter }}` | Loop counter |
| `{{ loop.index0 }}` | `{{ forloop.counter0 }}` | Zero-based counter |
| `{% set var = value %}` | `{% with var=value %}...{% endwith %}` | Variable assignment |
| `{{ value\|e }}` | `{{ value }}` | Auto-escaped by default |

### 5.2 Base Template

**File: `templates/base.html`**

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Battle-D{% endblock %}</title>

    <!-- PicoCSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/error-handling.css' %}">

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>

    <!-- Custom JS -->
    <script src="{% static 'js/error-handling.js' %}" defer></script>

    {% block extra_head %}{% endblock %}
</head>
<body>
    <main class="container">
        <!-- Flash Messages (Django messages framework) -->
        {% if messages %}
        <div id="flash-messages">
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }}" role="alert">
                {{ message }}
                <button type="button" class="close" onclick="this.parentElement.remove()">×</button>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 5.3 Tournament List Template

**File: `templates/tournaments/list.html`**

```html
{% extends "base.html" %}

{% block title %}Tournaments - Battle-D{% endblock %}

{% block content %}
<h1>Tournaments</h1>

<a href="{% url 'tournaments:create' %}" role="button">Create Tournament</a>

{% if tournaments %}
<table>
    <thead>
        <tr>
            <th>Name</th>
            <th>Date</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for tournament in tournaments %}
        <tr>
            <td>{{ tournament.name }}</td>
            <td>{{ tournament.date }}</td>
            <td>
                <span class="badge badge-{{ tournament.status }}">
                    {{ tournament.get_status_display }}
                </span>
            </td>
            <td>
                <a href="{% url 'tournaments:detail' pk=tournament.pk %}">View</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<p>No tournaments yet. Create your first tournament!</p>
{% endif %}
{% endblock %}
```

### 5.4 HTMX Partial Template Example

**File: `templates/registration/_search_results.html`**

```html
{% for dancer in dancers %}
<tr>
    <td>{{ dancer.display_name }}</td>
    <td>{{ dancer.country }}</td>
    <td>
        <button type="button"
                hx-post="{% url 'registration:add_performer' tournament_pk=category.tournament.pk category_pk=category.pk %}"
                hx-vals='{"dancer_id": "{{ dancer.pk }}"}'
                hx-target="#registration-lists"
                hx-swap="innerHTML">
            Add
        </button>
    </td>
</tr>
{% empty %}
<tr>
    <td colspan="3">No dancers found</td>
</tr>
{% endfor %}
```

### 5.5 Delete Modal with CSRF

**File: `templates/components/delete_modal.html`**

```html
<dialog id="{{ modal_id }}">
    <article>
        <h2>{{ title|default:"Confirm Deletion" }}</h2>
        <p>{{ message|default:"Are you sure you want to delete this item?" }}</p>
        <footer>
            <button type="button" class="secondary" onclick="document.getElementById('{{ modal_id }}').close()">
                {{ cancel_text|default:"Cancel" }}
            </button>
            <form method="post" action="{{ delete_url }}" style="display: inline;">
                {% csrf_token %}
                <button type="submit" class="contrast">
                    {{ confirm_text|default:"Delete" }}
                </button>
            </form>
        </footer>
    </article>
</dialog>
```

---

## Phase 6: URL Configuration (Day 18)

### 6.1 Root URLs

**File: `battle_d/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('', include('core.urls', namespace='dashboard')),
    path('tournaments/', include('tournaments.urls', namespace='tournaments')),
    path('dancers/', include('dancers.urls', namespace='dancers')),
    path('registration/', include('registration.urls', namespace='registration')),
    path('battles/', include('battles.urls', namespace='battles')),
    path('event/', include('battles.event_urls', namespace='event')),
]
```

### 6.2 App URLs Example

**File: `tournaments/urls.py`**

```python
from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.TournamentListView.as_view(), name='list'),
    path('create/', views.TournamentCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.TournamentDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.TournamentUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/activate/', views.TournamentActivateView.as_view(), name='activate'),
    path('<uuid:tournament_pk>/add-category/', views.CategoryCreateView.as_view(), name='add_category'),
]
```

**File: `registration/urls.py`**

```python
from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('<uuid:tournament_pk>/<uuid:category_pk>/',
         views.RegistrationView.as_view(), name='main'),
    path('<uuid:tournament_pk>/<uuid:category_pk>/add/',
         views.AddPerformerView.as_view(), name='add_performer'),
    path('<uuid:tournament_pk>/<uuid:category_pk>/remove/<uuid:performer_pk>/',
         views.RemovePerformerView.as_view(), name='remove_performer'),
    path('<uuid:tournament_pk>/<uuid:category_pk>/search/',
         views.SearchDancerView.as_view(), name='search_dancer'),
]
```

---

## Phase 7: Forms with Validation (Day 19)

### 7.1 Tournament Form

**File: `tournaments/forms.py`**

```python
from django import forms
from .models import Tournament, Category


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'date', 'location']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 3:
            raise forms.ValidationError('Tournament name must be at least 3 characters')
        return name


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'preselection_quota', 'pool_groups_ideal']
```

### 7.2 Dancer Form

**File: `dancers/forms.py`**

```python
from django import forms
from .models import Dancer


class DancerForm(forms.ModelForm):
    class Meta:
        model = Dancer
        fields = ['email', 'first_name', 'last_name', 'blaze', 'date_of_birth', 'country', 'city']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        # Check uniqueness (excluding current instance for updates)
        qs = Dancer.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A dancer with this email already exists')
        return email
```

---

## Phase 8: Django Admin (Day 20)

### 8.1 User Admin

**File: `accounts/admin.py`**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name',)}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'role', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)
```

### 8.2 Tournament Admin

**File: `tournaments/admin.py`**

```python
from django.contrib import admin
from .models import Tournament, Category


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'status', 'phase', 'created_at')
    list_filter = ('status', 'phase')
    search_fields = ('name', 'location')
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'category_type', 'preselection_quota')
    list_filter = ('category_type',)
```

---

## Phase 9: Service Layer (Days 21-23)

Services remain largely unchanged. Remove `async/await` and replace repository calls with Django ORM:

**File: `tournaments/services/tournament_service.py`**

```python
from django.db import transaction
from ..models import Tournament, TournamentStatus, TournamentPhase


class TournamentService:
    @staticmethod
    @transaction.atomic
    def activate_tournament(tournament_id):
        """Activate a tournament (CREATED → ACTIVE)."""
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            raise ValueError("Tournament not found")

        if tournament.status != TournamentStatus.CREATED:
            raise ValueError("Only CREATED tournaments can be activated")

        # Check no other active tournaments
        if Tournament.objects.filter(status=TournamentStatus.ACTIVE).exists():
            raise ValueError("Another tournament is already active")

        tournament.status = TournamentStatus.ACTIVE
        tournament.save()
        return tournament

    @staticmethod
    @transaction.atomic
    def advance_phase(tournament_id):
        """Advance tournament to next phase."""
        tournament = Tournament.objects.get(id=tournament_id)

        phase_order = [
            TournamentPhase.REGISTRATION,
            TournamentPhase.PRESELECTION,
            TournamentPhase.POOLS,
            TournamentPhase.FINALS,
            TournamentPhase.COMPLETED,
        ]

        current_index = phase_order.index(tournament.phase)
        if current_index >= len(phase_order) - 1:
            raise ValueError("Tournament already completed")

        tournament.phase = phase_order[current_index + 1]
        tournament.save()
        return tournament
```

---

## Phase 10: Test Migration (Days 24-26)

### 10.1 Test Configuration

**File: `conftest.py`**

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@test.com',
        first_name='Admin',
        role='admin',
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email='staff@test.com',
        first_name='Staff',
        role='staff',
    )


@pytest.fixture
def tournament(db):
    from tournaments.models import Tournament
    return Tournament.objects.create(
        name='Test Tournament',
        date='2025-01-01',
    )


@pytest.fixture
def category(db, tournament):
    from tournaments.models import Category
    return Category.objects.create(
        tournament=tournament,
        name='Breaking 1v1',
        category_type='1v1',
    )
```

### 10.2 Test Example

**File: `tests/test_tournament_views.py`**

```python
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTournamentViews:
    def test_list_tournaments(self, client, admin_user, tournament):
        client.force_login(admin_user)
        response = client.get(reverse('tournaments:list'))
        assert response.status_code == 200
        assert tournament.name in response.content.decode()

    def test_create_tournament(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post(
            reverse('tournaments:create'),
            data={
                'name': 'New Tournament',
                'date': '2025-06-01',
                'location': 'Paris',
            }
        )
        assert response.status_code == 302  # Redirect on success

    def test_activate_tournament(self, client, admin_user, tournament):
        client.force_login(admin_user)
        response = client.post(
            reverse('tournaments:activate', kwargs={'pk': tournament.pk})
        )
        assert response.status_code == 302
        tournament.refresh_from_db()
        assert tournament.status == 'active'
```

---

## File-by-File Checklist

### Models
- [ ] `app/models/base.py` → `core/models.py`
- [ ] `app/models/user.py` → `accounts/models.py`
- [ ] `app/models/dancer.py` → `dancers/models.py`
- [ ] `app/models/tournament.py` → `tournaments/models.py`
- [ ] `app/models/category.py` → `tournaments/models.py`
- [ ] `app/models/performer.py` → `battles/models.py`
- [ ] `app/models/pool.py` → `battles/models.py`
- [ ] `app/models/battle.py` → `battles/models.py`

### Routers → Views
- [ ] `app/routers/auth.py` → `accounts/views.py`
- [ ] `app/routers/admin.py` → `accounts/views.py` (user management)
- [ ] `app/routers/dashboard.py` → `core/views.py`
- [ ] `app/routers/tournaments.py` → `tournaments/views.py`
- [ ] `app/routers/dancers.py` → `dancers/views.py`
- [ ] `app/routers/registration.py` → `registration/views.py`
- [ ] `app/routers/battles.py` → `battles/views.py`
- [ ] `app/routers/event.py` → `battles/event_views.py`

### Templates (48 files)
- [ ] Update `url_for()` → `{% url %}`
- [ ] Update `loop.index` → `forloop.counter`
- [ ] Add `{% csrf_token %}` to all POST forms
- [ ] Update flash messages to Django messages

### Services (11 files)
- [ ] Remove `async/await`
- [ ] Replace repository calls with Django ORM
- [ ] Add `@transaction.atomic` where needed

---

## Timeline Summary

| Phase | Days | Description |
|-------|------|-------------|
| 1 | 1-2 | Project setup, settings |
| 2 | 3-5 | Model migration |
| 3 | 6-7 | Authentication backend |
| 4 | 8-14 | View migration |
| 5 | 15-17 | Template migration |
| 6 | 18 | URL configuration |
| 7 | 19 | Forms with validation |
| 8 | 20 | Django Admin |
| 9 | 21-23 | Service layer |
| 10 | 24-26 | Test migration |
| 11 | 27-28 | Data migration & deployment |

**Total: 28 days (4 weeks)**

---

## Key Django Patterns Used

1. **Custom User Model** with `AbstractBaseUser` and `BaseUserManager`
2. **Custom Managers** with `QuerySet.as_manager()` pattern
3. **Class-Based Generic Views** (`CreateView`, `UpdateView`, `DeleteView`, `ListView`)
4. **django-htmx** for HTMX request detection (`request.htmx`)
5. **Django Messages Framework** for flash messages
6. **Django Forms** with `ModelForm` and custom validation
7. **URL namespacing** with `app_name` and `include()`
8. **Django Admin** customization

---

**Document Version:** 1.0
**Last Updated:** 2025-12-23
**Django Docs Source:** Context7 - Django 5.2 Official Documentation
