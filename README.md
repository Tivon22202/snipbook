# SnipBook: online appointment booking for a barbershop

## 1. The project in three answers

**What problem am I solving?**
Small barbershops and salons take bookings by phone, WhatsApp or walk-in queues. Customers wait without knowing how long, double bookings happen, and the owner has no clear view of the day.

**Who will use it?**
- **Customers** who want to book, view and cancel appointments.
- **Staff / the owner** who need to see the day's bookings, confirm or complete them, and manage the service list.

**What can users do?**
| Customer | Staff / owner |
|---|---|
| Register, log in, log out | Dashboard with today's count, pending count and customers served |
| Browse services with price and duration | Filter bookings by date and status |
| Book only from genuinely free time slots | Confirm, complete or cancel any booking |
| See upcoming bookings and history | Add, edit, hide or delete services |
| Cancel their own future bookings | Full Django admin at `/admin/` |

Business rules: one chair (no overlapping bookings), open Mon–Sat 09:00–18:00, 30-minute slot grid, no booking in the past, and a service's length decides how many slots it occupies.

## 2. Run it

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations bookings
python manage.py migrate
python manage.py seed             # sample services + staff user "owner"
python manage.py test             # 9 tests
python manage.py runserver
```
Open http://127.0.0.1:8000/. Staff login after seeding: `owner` / `ChangeMe-dev-123` (development only; set `SEED_STAFF_PASSWORD` to choose your own). Change the time zone and currency with `DJANGO_TIME_ZONE` and `SHOP_CURRENCY`.

## 3. How it maps to the course

| Course topic | Where it appears |
|---|---|
| HTML/CSS | `templates/`, `static/css/style.css` (responsive, keyboard focus styles) |
| Python | `scheduling.py` (availability logic), `seed.py` |
| Django | Project `config/`, app `bookings/`, URL routing in `urls.py` |
| Forms | `forms.py`: `RegisterForm`, `BookingForm` (custom validation), service form in `views.py` |
| Database | `models.py`: `Service`, `Booking` with foreign keys and migrations |
| CRUD | Bookings (create, read, update status, cancel) and Services (full CRUD) |
| Authentication | Register, login, logout; `login_required`; staff-only views via `staff_required` |
| Security | CSRF on every form, POST-only state changes, owner-only cancel (404 otherwise), password validators, secrets from environment, HTTPS settings when `DEBUG=0` |
| APIs | `GET /api/services/` and `GET /api/slots/?date=YYYY-MM-DD&service=ID` (JSON; used by the booking page via `fetch`) |
| Deployment | WhiteNoise + gunicorn in `requirements.txt`; see below |

## 4. Deployment checklist

```bash
export DJANGO_DEBUG=0
export DJANGO_SECRET_KEY="a-long-random-string"
export DJANGO_ALLOWED_HOSTS="yourdomain.com"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://yourdomain.com"
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi
```
Works on hosts such as Render, Railway or PythonAnywhere. For production data, move from SQLite to PostgreSQL.

## 5. Stretch ideas

- Live dashboard updates with Django Channels (WebSockets) when a customer books.
- Email or SMS confirmations and reminders.
- Mobile-money payment for deposits.
- Several barbers, each with their own calendar.
