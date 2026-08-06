# Renalloc

سامانهٔ پیوند کلیه با backend مبتنی بر Django/PostgreSQL و frontend مبتنی بر Vue.

## راه‌اندازی PostgreSQL و Redis

از ریشهٔ پروژه اجرا کنید:

```bash
docker compose -f infra/compose.yml up -d db redis
```

مقادیر پیش‌فرض توسعه `renalloc` هستند. PostgreSQL داخل کانتینر روی پورت استاندارد `5432` اجرا و برای جلوگیری از تداخل با PostgreSQL محلی، روی `127.0.0.1:5433` منتشر می‌شود. Redis نیز فقط روی `127.0.0.1:6379` منتشر می‌شود. برای تغییر پورت می‌توانید متغیرهای `POSTGRES_PORT` و `REDIS_PORT` را هنگام اجرای Compose مقداردهی کنید.

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

## ثبت پرونده‌های بالینی

ثبت نهایی فرم‌های گیرنده و اهداکننده به‌ترتیب از endpointهای احراز هویت‌شدهٔ `POST /api/registry/recipients/` و `POST /api/registry/donors/` انجام می‌شود. هر ثبت در یک transaction ذخیره می‌شود؛ بنابراین خطا در اطلاعات هویتی، پروفایل، آزمایش یا تأییدیه باعث rollback کل پرونده خواهد شد.

CDC PRA و Anti-HLA به‌صورت نوبت‌های مستقل و قابل افزودن/ویرایش نگهداری می‌شوند؛ بنابراین تغییر نتیجه در طول زمان، تاریخچهٔ قبلی را از بین نمی‌برد. این آزمایش‌ها و آزمایش‌های روتین/ویروسی همراه با `performed_at` و `expires_at` ذخیره می‌شوند و `expires_at` فقط در backend و دقیقاً شش ماه تقویمی پس از تاریخ انجام محاسبه می‌شود.

ثبت اولیهٔ CDC PRA، HLA و Anti-HLA اختیاری است. تایپ HLA تاریخ انقضا ندارد، برای هر locus حداکثر دو آلل می‌پذیرد و Anti-HLA از صفر تا تمام آنتی‌ژن‌های تعریف‌شده را می‌پذیرد. مقادیر HLA، Anti-HLA، نام آزمایش‌ها و سایر فیلدهای دارای دامنهٔ مشخص در backend نیز با Choice و اعتبارسنجی سمت سرور محدود شده‌اند. برای اعمال schema پیش از اجرای برنامه، `python manage.py migrate` را اجرا کنید.

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

برای ساخت دادهٔ نمایشیِ تکرارپذیر (با شناسه‌ها و نام‌های صریحاً آزمایشی):

```bash
cd backend
python manage.py seed_fake_registry --recipients 100 --donors 100
```

فرمان idempotent است؛ اجرای دوباره رکورد تکراری ایجاد نمی‌کند.

## موتور ملی Matching

موتور Matching سه مرحله را به‌ترتیب اجرا می‌کند: سازگاری ABO (بدون دخالت Rh)، فیلتر ایمنی با آخرین Anti-HLA و CDC-PRA معتبر، و رتبه‌بندی تطبیقی HLA. خروجی ایمنی یکی از `compatible`، `conditional` یا `incompatible` است. حالت مشروط برای اختلاف resolution تایپ HLA استفاده می‌شود و انجام Cross-Match فیزیکی و در صورت نیاز تایپ High-Resolution را الزامی نگه می‌دارد.

امتیاز نهایی از HLA، زمان انتظار، فوریت پزشکی، cPRA، سن و ضریب منطقه محروم تشکیل می‌شود. سیاست فعال نسخه‌دار است؛ تغییر ضرایب نسخه جدید می‌سازد تا پیشنهادهای قبلی قابل بازسازی و ممیزی بمانند. هموزیگوت با `copy_number=2` ذخیره می‌شود و در امتیاز HLA دو تطابق محسوب می‌شود.

در همهٔ مسیرهای Matching، تابعیت نیز یک فیلتر سخت است: ایرانی فقط با ایرانی و غیرایرانی فقط با غیرایرانی بررسی می‌شود. صفحهٔ «Matching اهداکننده جسد» فقط گیرندگان فعال دارای `donor_deceased=true` را در یک پنجرهٔ محدود و از پیش فیلترشده رتبه‌بندی می‌کند و خروجی CSV می‌دهد؛ سقف پنجره با `DECEASED_MATCH_CANDIDATE_LIMIT` کنترل می‌شود. CREG مطابق جدول طرح به‌عنوان هشدار بالقوه نمایش داده می‌شود و جایگزین Cross-Match فیزیکی نیست.

برای اجرای دستی/شبانه:

```bash
cd backend
python manage.py run_matching --top-n 10
```

اجرای Matching داخل request وب انجام نمی‌شود. با ورود گیرنده به وضعیت «فعال در لیست انتظار»، یک task همان گیرنده را با تمام اهداکنندگان واجد شرایط بررسی می‌کند؛ با ورود اهداکننده به وضعیت «در دسترس»، task متناظر نیز آن را با تمام گیرندگان فعال بررسی می‌کند. تغییر HLA، CDC-PRA یا Anti-HLA نیز پس از commit تراکنش، Matching همان پرونده را دوباره در صف قرار می‌دهد.

برای اجرای worker و زمان‌بند با Compose:

```bash
docker compose -f infra/compose.yml up -d matching-worker matching-beat
```

یا در محیط مجازی backend:

```bash
celery -A config worker -l INFO -Q matching,maintenance --concurrency 2
celery -A config beat -l INFO
```

صف روی Redis قرار دارد، دریافت taskها به‌صورت late acknowledgement انجام می‌شود، prefetch پیش‌فرض یک است و concurrency از `CELERY_CONCURRENCY` قابل تنظیم است. Celery Beat تطبیق ملی را ساعت ۰۲:۰۰ و بررسی انقضای آزمایش‌ها را ساعت ۰۸:۰۰ به وقت تهران اجرا می‌کند. endpoint پروفایل فقط task را enqueue می‌کند و با پاسخ `202` منتظر پایان محاسبه نمی‌ماند.

## چرخه وضعیت و Cross-Match

وضعیت گیرنده و اهداکننده فقط از گذارهای مجاز تغییر می‌کند. کنترل «تغییر وضعیت» در هر دو پروفایل و «ویرایش اولویت» در پروفایل گیرنده فقط برای کاربر دارای سطح `level_one` نمایش داده می‌شود و همان محدودیت در API نیز اعمال می‌شود. سطح پیش‌فرض، مطابق اصل حداقل دسترسی، `level_two` است؛ دسترسی سطح یک باید صریحاً از پنل مدیریت به هماهنگ‌کننده واگذار شود. هر تغییر، همراه با کاربر، زمان، دلیل و metadata در `ClinicalStateEvent` ثبت می‌شود. تأیید یک پیشنهاد توسط مرکز، هر دو پرونده را وارد گردش Cross-Match می‌کند؛ نتیجه منفی هر دو را آماده عمل/پیوند و نتیجه مثبت آن‌ها را به استخر فعال بازمی‌گرداند. بیمار فقط «درخواست مشاوره» ثبت می‌کند و نمی‌تواند Cross-Match را مستقیماً تأیید یا اجرا کند.

نمای بیمار در `/patient-portal/matches` هویت اهداکننده را نمایش نمی‌دهد. دسترسی به داده HLA در `SensitiveDataAccessLog` ثبت می‌شود و APIهای جدید مرکز، پرونده گیرندگان را بر اساس مرکز کاربر محدود می‌کنند.

در production باید volume پایگاه داده با رمزنگاری دیسک/volume سازمان میزبانی شود، اتصال PostgreSQL با `POSTGRES_SSLMODE=verify-full` و API فقط پشت HTTPS در دسترس باشد. با `DJANGO_DEBUG=false`، redirect اجباری HTTPS، secure cookie و HSTS به‌صورت پیش‌فرض فعال می‌شوند؛ فعال‌سازی HSTS فقط پس از اطمینان از پوشش کامل HTTPS انجام شود. کلیدها و گذرواژه‌ها نباید در repository یا فایل Compose نگهداری شوند و باید از secret manager تزریق شوند.

## انقضای آزمایش‌ها و اعلان‌ها

گیرنده فاقد Anti-HLA یا CDC-PRA معتبر توسط موتور رد می‌شود. فرمان زیر هشدار ۱۴ روزه ایجاد و گیرنده فعالِ فاقد آزمایش معتبر را به‌صورت ممیزی‌شده موقتاً غیرفعال می‌کند:

```bash
cd backend
python manage.py check_expiring_tests --days 14
```

این فرمان به‌صورت روزانه توسط Celery Beat اجرا می‌شود. اعلان‌های تطبیق، تغییر وضعیت و انقضای آزمایش در رابط کاربری و endpoint اعلان‌ها قابل مشاهده‌اند.

## آزمون مقیاس ملی

ایندکس‌های مرکب HLA و Anti-HLA در migration ساخته شده‌اند. برای بنچمارک مصنوعی بدون درج داده شخصی و برون‌یابی به ابعاد ۵ میلیون گیرنده و ۱ میلیون اهداکننده:

```bash
cd backend
python manage.py benchmark_matching --recipients 5000000 --donors 1000000 --sample-size 100000
```

این بنچمارک برای مقایسه الگوریتم و صحت ظرفیت‌سنجی اولیه است؛ Load Test نهایی باید روی topology واقعی PostgreSQL، partitioning، صف پردازش و سخت‌افزار production اجرا شود.
