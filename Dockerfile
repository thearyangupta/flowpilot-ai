# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip wheel \
        --wheel-dir=/wheels \
        -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd \
        --gid 10001 \
        flowpilot \
    && useradd \
        --uid 10001 \
        --gid flowpilot \
        --create-home \
        --shell /usr/sbin/nologin \
        flowpilot

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install \
        --no-cache-dir \
        --no-index \
        --find-links=/wheels \
        -r requirements.txt \
    && rm -rf /wheels

COPY --chown=flowpilot:flowpilot app ./app
COPY --chown=flowpilot:flowpilot ui ./ui
COPY --chown=flowpilot:flowpilot alembic ./alembic
COPY --chown=flowpilot:flowpilot alembic.ini ./alembic.ini
COPY --chown=flowpilot:flowpilot .streamlit ./.streamlit

USER flowpilot

EXPOSE 8000
EXPOSE 8501

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]