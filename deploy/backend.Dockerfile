# Build context = GỐC repo (lát 12): image mang cả backend/ lẫn database/ để migrate chạy trong container.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ /app/backend/
COPY database/ /app/database/
ENV PATH="/app/backend/.venv/bin:$PATH"
# REPO_ROOT của core/env.py = parents[2] của /app/backend/core/env.py = /app — đúng cấp với native.
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
