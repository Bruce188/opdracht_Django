# Compound Interest Calculator (Django)

A small Django app built for a school assignment on the MVT (Model-View-Template) pattern. The original brief, in Dutch, is in `opdracht.txt`.

It takes a principal amount, an annual interest rate and a number of years, and calculates the future value and the total interest earned with `A = P * (1 + r/100)^n`. Each calculation is saved to a SQLite database.

## Stack

- Python 3.12+
- Django 6.0.3
- python-dotenv (reads settings from `.env`)
- SQLite

## Project layout

- `config/` - project settings and root URLs
- `calculator/` - the app: form, model, view, URLs and tests
- `templates/calculator/` - HTML templates

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
```

Settings in `.env`:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Required when `DJANGO_DEBUG` is off. With debug on and no key set, one is generated and stored in `.secret_key`. |
| `DJANGO_DEBUG` | `True` or `1` enables debug mode. Defaults to `False`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host list. Defaults to `localhost,127.0.0.1` in debug mode, empty otherwise. |

For local development, set `DJANGO_DEBUG=True` in `.env`.

## Run

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the calculator. The Django admin is at `/admin/`.

## Test

```bash
python manage.py test
```

The suite has 30 tests covering the view, form validation, the model and the settings.
