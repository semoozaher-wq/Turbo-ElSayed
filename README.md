# Turbo ElSayed 🎬

مولّد فيديوهات وسيناريوهات بالذكاء الاصطناعي: تكتب موضوعًا أو كلمة مفتاحية، فيكتب النظام السيناريو، ويطابق اللقطات، ويصنع الترجمة والموسيقى، ثم يُخرج فيديو HD.

[English](README-en.md) · [日本語](README-ja.md) · [مراجعة الكود](REVIEW_AR.md) · [سجل التغييرات](CHANGELOG.md)

## ✨ المميزات

- توليد سيناريو كامل (عنوان، ملخص، شخصيات، مشاهد) بصيغة JSON منظمة.
- نظام شخصيات ثابتة عبر كل المشاهد من خلال `characters.json`.
- توليد صور ومشاهد لوضع الأفلام الطويلة.
- تكامل مع عدة مزودات LLM (OpenAI، Gemini، DashScope، Kimi وغيرها).
- ثلاثة مداخل: واجهة رسومية (Streamlit)، واجهة API (FastAPI)، وسطر أوامر (CLI).

## 📁 هيكل المشروع

| المسار | الوظيفة |
|---|---|
| `app/services/` | خدمات التوليد والمعالجة (سيناريو، صوت، ترجمة، فيديو) |
| `app/controllers/` | نقاط النهاية HTTP والتحقق من المفاتيح |
| `app/config/` | تحميل وحفظ `config.toml` |
| `webui/` | واجهة Streamlit الرسومية |
| `cli.py` | واجهة سطر الأوامر |
| `main.py` | تشغيل خادم FastAPI |
| `characters.json` | تعريف الشخصيات الثابتة |
| `config.example.toml` | نموذج الإعدادات — انسخه إلى `config.toml` |

## 🚀 التشغيل السريع

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/Turbo-ElSayed.git
cd Turbo-ElSayed

# الأسلوب المُوصى به (نسخة مثبّتة بالكامل)
pip install uv
uv sync

# أو بالطريقة التقليدية
pip install -r requirements.txt
```

**مطلوب مسبقًا**: Python 3.11 أو أحدث، و`ffmpeg` مثبّت على النظام ومتاح في `PATH`.

### تشغيل الواجهة الرسومية

```bash
sh webui.sh          # macOS / Linux
webui.bat            # Windows
```

### تشغيل خادم الـ API

```bash
python main.py
# التوثيق التفاعلي على http://127.0.0.1:8501/docs
```

### أوامر أخرى

```bash
python start_app.py --mode webui     # مشغّل موحّد للواجهة
python cli.py --help                 # واجهة سطر الأوامر
python scripts/smoke_check.py        # فحص صحة شامل بلا استهلاك رصيد
```

## ⚙️ الإعداد

1. انسخ النموذج: `cp config.example.toml config.toml`
2. ضع مفاتيح المزوّدين داخله **محليًا فقط** — لا ترفع `config.toml` إلى المستودع (مستثنى في `.gitignore`).
3. بدائل متغيرات البيئة موجودة في `.env.example`.

## 🔐 الأمان

- في وضع الإنتاج (`MPT_ENVIRONMENT=production`) **يجب** ضبط `MPT_API_KEY`، وإلا يفشل الإقلاع عمدًا.
- ضع المفتاح في ترويسة `X-API-Key` أو `Authorization: Bearer`، ولا تستخدم متغيّرات الرابط (query string).
- شغّل الـ API خلف reverse proxy على شبكة موثوقة حتى عند تعطيل المصادقة في التطوير.

## 🧪 الاختبارات

```bash
uv run python -X utf8 -m pytest -q test
uv run python -X utf8 -m coverage run -m pytest -q test && uv run python -m coverage report
```

## 🐳 Docker

```bash
export MPT_API_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
docker compose up --build
```

## 📄 الترخيص

MIT — راجع [LICENSE](LICENSE). المشروع مبني على MoneyPrinterTurbo، ويُحفظ نسب المصدر الأصلي كما يقتضي الترخيص.
