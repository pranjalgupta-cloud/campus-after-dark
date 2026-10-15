# Campus After Dark — Setup & Deployment Guide

## Project Structure

```
campus_after_dark/        ← Django project config (settings, main URLs)
accounts/                 ← User auth, institution & org profiles
  models.py               ← User, InstitutionProfile, OrganizationProfile, InstitutionDocument
  views.py                ← Login, logout, registration, dashboard routing, profile
  forms.py                ← All auth and profile forms
  urls.py                 ← Auth URL routes
  admin.py                ← Django admin registrations
facilities/               ← Facility listings, images, availability
  models.py               ← Facility, FacilityImage, Amenity, BlockedDate, AvailabilityRule
  views.py                ← Public explore, detail, institution CRUD
  forms.py                ← Facility form, search form, blocked date form
  urls.py                 ← Facility URL routes
  admin.py
bookings/                 ← Bookings, payments, reviews, notifications
  models.py               ← Booking, Payment, Payout, Review, Notification, AuditLog, PlatformSetting
  views.py                ← Full booking workflow (request, approve, reject, pay, complete, review)
  forms.py                ← BookingRequestForm, ReviewForm
  urls.py
  admin.py
core/                     ← Public pages and dashboards
  views.py                ← Home, public pages, institution/org/admin dashboards
  urls.py                 ← All route definitions
  management/commands/
    seed_demo_data.py     ← Idempotent demo data seeder
templates/
  base.html               ← Shared site-wide layout (navbar, footer)
  dashboards/
    base_dashboard.html   ← Shared sidebar dashboard layout
    institution.html      ← Institution dashboard
    organization.html     ← Organization dashboard
    admin.html            ← Admin dashboard
    admin_institutions.html
    admin_users.html
    admin_bookings.html
    admin_settings.html
  accounts/               ← Login, register, setup templates
  facilities/             ← Explore, detail, form, institution list
  bookings/               ← Booking request, detail, payment, lists
  public/                 ← Home, about, FAQ, contact, legal pages
static/
  css/style.css           ← Complete custom styles (deep navy + amber palette)
  js/main.js              ← Shared JS (sidebar, alerts, price calculator, charts)
```

## Local Development Setup

### Prerequisites
- Python 3.10+
- pip

### Install Dependencies

```bash
pip install django pillow django-crispy-forms crispy-bootstrap5
```

Optional for MySQL:
```bash
pip install mysqlclient
```

Optional for PostgreSQL:
```bash
pip install psycopg2-binary dj-database-url
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### Run Migrations

```bash
python manage.py migrate
```

### Seed Demo Data

```bash
python manage.py seed_demo_data
```

This creates:
- Admin: `admin@campusafterdark.in` / `Admin@1234`
- Institution: `iit@campusafterdark.in` / `Demo@1234`
- Organization: `events@campusafterdark.in` / `Demo@1234`
- 3 demo institutions (all verified/approved)
- 6 demo facilities (published)
- 4 demo bookings in various statuses
- 16 amenities

> ⚠️ ALL demo data is clearly labelled with [DEMO] in names and descriptions.

### Run Development Server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000

## MySQL Setup (Optional)

1. Create database:
```sql
CREATE DATABASE campus_after_dark CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'caduser'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON campus_after_dark.* TO 'caduser'@'localhost';
```

2. Set in `.env`:
```
DATABASE_URL=mysql://caduser:yourpassword@localhost:3306/campus_after_dark
```

3. Install driver: `pip install mysqlclient`

## GitHub Deployment (Free Hosting via Railway or Render)

### Option 1: Railway.app (Recommended)

1. Push code to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add environment variables from `.env.example`
4. Railway auto-detects Django and deploys

Add to project root:
```
# Procfile
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn campus_after_dark.wsgi
```

Install gunicorn: `pip install gunicorn`

Create `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Option 2: Render.com

1. Create Web Service → connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn campus_after_dark.wsgi`
4. Add env vars

### Option 3: PythonAnywhere (Free Tier)

1. Upload code via git or zip
2. Create virtual environment
3. Configure WSGI file to point to `campus_after_dark.wsgi`
4. Set `DEBUG=False`, `ALLOWED_HOSTS=yourusername.pythonanywhere.com`

## Features Requiring External Credentials

| Feature | Env Var | Status |
|---------|---------|--------|
| Real Payments | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | **Demo mode** — simulated |
| Email Notifications | `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | **Console backend** — printed to terminal |
| Cloud File Storage | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | **Local disk** — works for dev |
| MySQL Database | `DATABASE_URL` | **SQLite** — works for dev |

## Database Relationships

- `User` (custom AbstractUser) → has `role` field (institution/organization/admin)
- `InstitutionProfile` → OneToOne with User (role=institution)
- `OrganizationProfile` → OneToOne with User (role=organization)
- `InstitutionDocument` → ForeignKey to InstitutionProfile
- `Facility` → ForeignKey to InstitutionProfile
- `FacilityImage` → ForeignKey to Facility
- `FacilityAmenity` → M2M through table (Facility ↔ Amenity)
- `BlockedDate` → ForeignKey to Facility
- `Booking` → ForeignKey to Facility + OrganizationProfile
- `BookingStatusHistory` → ForeignKey to Booking (audit trail)
- `Payment` → ForeignKey to Booking
- `Payout` → OneToOne with Booking, ForeignKey to InstitutionProfile
- `Review` → OneToOne with Booking, ForeignKey to Facility + User
- `Notification` → ForeignKey to User
- `PlatformSetting` → standalone key-value config
- `AuditLog` → ForeignKey to User (optional)

## Security Notes

- Role-based access enforced in every view with `request.user.is_institution`, `is_org`, `is_platform_admin`
- Django's CSRF protection enabled on all forms
- File uploads restricted by type and size
- Verification documents served from `/media/institution_docs/` — not publicly listed
- All booking overlap checks performed **server-side** using `select_for_update` pattern
- Admin actions are logged in `AuditLog`
- Passwords never stored in plaintext (Django's `PBKDF2PasswordHasher`)

## Demo Walk-Through

1. **Admin**: Login as admin → approve institutions → configure commission
2. **Institution**: Login → setup profile → add facilities → publish → manage bookings
3. **Organization**: Login → search facilities → request booking → pay (demo) → review

All flows work end-to-end with demo data provided by `seed_demo_data`.
