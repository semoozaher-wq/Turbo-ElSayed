# سجل التغييرات

## [1.3.7] - 2026-09-25

### إصلاحات
- **docker-compose.yml**: أحجام القراءة/الكتابة كانت تشير إلى `/MoneyPrinterTurbo/...` ومجلد العمل في الصورة `/app`، فكانت الحاويتان تُقلعان بلا `config.toml` وبلا تخزين دائم. صُحّحت المسارات.
- **docker-compose.yml**: منفذ خدمة `api` كان `8080` بينما `config.listen_port = 8501`، فكان فحص الصحة يفشل دائمًا. وُحّد المنفذ.
- **Dockerfile**: أُضيف مستخدم غير جذري `10001`، و`HEALTHCHECK` على `/ping`، وإنشاء كل الأدلة المطلوبة، وأصبح `uv sync --frozen` أولوية قبل `requirements.txt`.
- **CI**: كل خطوة lint/اختبار كانت منتهية بـ`|| true` و`continue-on-error: true`، فكان الفشل يمر بصمت. الآن أخطاء الصياغة والاختبارات تُسقِط البناء.
- **main.py**: أُضيفت تجاوزات `MPT_LISTEN_HOST` / `MPT_LISTEN_PORT` / `MPT_LOG_LEVEL` بدل تجميد `127.0.0.1`.
- **pyproject.toml**: أُضيفت حزم تُستورَد مباشرة وكانت غائبة (`pydantic`, `toml`, `numpy`, `Pillow`, `imageio-ffmpeg`).
- **requirements.txt**: أُعيد بناؤه ليطابق `pyproject.toml` حرفيًا.
- **README.md**: كان مقطوعًا في منتصف كتلة كود ويشير إلى مستودع غير موجود (`printer-turbo`). أُعيد كتابته.

### إضافات
- `.gitignore` و`.dockerignore` — لم يكونا موجودين إطلاقًا.
- `.env.example` — نموذج كامل لمتغيرات البيئة.
- `scripts/smoke_check.py` — فحص صحة شامل بلا استهلاك أرصدة.
- `CHANGELOG.md` و`REVIEW_AR.md`.
