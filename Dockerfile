FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/MoneyPrinterTurbo \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /MoneyPrinterTurbo

ARG DOCKER_BUILD_MIRROR=official
ARG PIP_USE_OFFICIAL=1

RUN set -eux; \
    if [ "$DOCKER_BUILD_MIRROR" = "china" ]; then \
      printf 'deb https://mirrors.aliyun.com/debian bullseye main\ndeb https://mirrors.aliyun.com/debian bullseye-updates main\ndeb https://mirrors.aliyun.com/debian-security bullseye-security main\n' > /etc/apt/sources.list; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends ffmpeg git; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN set -eux; \
    if [ "$PIP_USE_OFFICIAL" = "1" ]; then \
      pip install --no-cache-dir --retries 3 --timeout 60 -r requirements.txt; \
    else \
      pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --retries 3 --timeout 60 -r requirements.txt; \
    fi

COPY --chown=10001:10001 . .
RUN set -eux; \
    useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin mpt; \
    mkdir -p /MoneyPrinterTurbo/storage /MoneyPrinterTurbo/tmp; \
    chown -R 10001:10001 /MoneyPrinterTurbo

USER 10001:10001
EXPOSE 8501

CMD ["streamlit", "run", "./webui/Main.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.serverAddress=127.0.0.1", "--server.enableCORS=True", "--browser.gatherUsageStats=False", "--client.toolbarMode=minimal", "--logger.hideWelcomeMessage=True", "--server.showEmailPrompt=False"]
