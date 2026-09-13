# ============================================
# MoneyPrinterTurbo - Dockerfile for Railway
# ============================================

FROM python:3.11-slim

# متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8501

# مجلد العمل
WORKDIR /app

# تثبيت المكتبات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تثبيت uv (مدير الحزم السريع)
RUN pip install --no-cache-dir uv

# نسخ ملفات المشروع
COPY pyproject.toml uv.lock ./
COPY requirements.txt* ./

# تثبيت الاعتماديات
RUN uv sync --frozen || pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# إنشاء مجلدات مطلوبة
RUN mkdir -p storage resource/songs resource/fonts

# فتح المنفذ
EXPOSE 8501

# أمر التشغيل
CMD ["sh", "-c", "uv run streamlit run webui/Main.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
