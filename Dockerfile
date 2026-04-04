FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}" \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

COPY pyproject.toml ./

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv lock && uv sync --frozen \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/* /root/.local/share/uv

COPY . .

EXPOSE 5000
CMD ["uv", "run", "gunicorn", "-w", "4", "-k", "gthread", "--threads", "8", "-b", "0.0.0.0:5000", "run:app", "--timeout", "60"]