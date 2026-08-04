# Renalloc

سامانهٔ پیوند کلیه با backend مبتنی بر Django/PostgreSQL و frontend مبتنی بر Vue.

## راه‌اندازی PostgreSQL

از ریشهٔ پروژه اجرا کنید:

```bash
docker compose -f infra/compose.yml up -d db
```

مقادیر پیش‌فرض توسعه `renalloc` هستند. PostgreSQL داخل کانتینر روی پورت استاندارد `5432` اجرا و برای جلوگیری از تداخل با PostgreSQL محلی، روی `127.0.0.1:5433` منتشر می‌شود. برای تغییر پورت می‌توانید متغیر `POSTGRES_PORT` را هنگام اجرای Compose مقداردهی کنید و همان مقدار را در `backend/.env` قرار دهید.

## راه‌اندازی backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Django فایل `.env` را خودکار بارگذاری نمی‌کند؛ متغیرها را در shell یا ابزار اجرای محیط خود بارگذاری کنید. برای توسعه در Bash می‌توانید اجرا کنید:

```bash
set -a
source .env
set +a
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

پنل مدیریت در `http://127.0.0.1:8000/admin/` در دسترس است. ابتدا Center را بسازید و سپس از بخش «کاربران (هماهنگ‌کنندگان پیوند)» کاربر جدید ایجاد کنید. هیچ کاربر نمایشی یا رمز پیش‌فرضی ساخته نمی‌شود.

ایمیل بازیابی رمز در حالت توسعه در ترمینال backend چاپ می‌شود. در محیط production متغیرهای `EMAIL_BACKEND` و تنظیمات SMTP موجود در `backend/.env.example` را مقداردهی کنید.

## راه‌اندازی frontend

در ترمینال دیگری اجرا کنید:

```bash
cd frontend/kidney-transplant-system
npm install
npm run dev
```

Vite درخواست‌های `/api` و `/admin` را در توسعه به Django روی پورت `8000` proxy می‌کند. در production نیز frontend و API را پشت یک reverse proxy و روی یک origin ارائه کنید؛ در صورت استفاده از origin جدا باید CORS را در لایهٔ backend/proxy تنظیم کنید.

## بررسی‌ها

تست backend بدون نیاز به PostgreSQL:

```bash
cd backend
RENALLOC_USE_SQLITE=1 python manage.py test
```

build frontend:

```bash
cd frontend/kidney-transplant-system
npm run build
```
