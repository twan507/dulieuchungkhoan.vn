# Build context = GỐC repo (lát 12): image mang cả backend/ lẫn database/ để migrate chạy trong container.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
# REPO_ROOT của core/env.py = parents[2] của /app/backend/core/env.py = /app — đúng cấp với native.
# Điểm gắn volume phải có sẵn và thuộc appuser: Docker chép quyền của thư mục trong image sang volume mới;
# không có sẵn thì volume ra đời root:root và tiến trình non-root không ghi được (AC4 lát 12, 2026-09-08).
# Tạo user và MỌI thư mục TRƯỚC `uv sync`, rồi `COPY --chown`: bản cũ `chown -R /app` sau `uv sync` nên
# `.venv` bị chép lại nguyên vẹn thành một layer thứ hai (Chuẩn M10, review toàn nhánh lát 12).
RUN mkdir -p /var/lib/dlck/logs /var/lib/dlck/measure /var/lib/dlck/spill /var/lib/dlck/etl-logs /backups /app/backend /app/database && useradd -m appuser && chown -R appuser /app /var/lib/dlck /backups
USER appuser
WORKDIR /app/backend
COPY --chown=appuser:appuser backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY --chown=appuser:appuser backend/ /app/backend/
COPY --chown=appuser:appuser database/ /app/database/
ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
