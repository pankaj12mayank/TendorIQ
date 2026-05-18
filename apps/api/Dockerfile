# Backend Dockerfile (Optional)
# Required only if using Docker deployment

FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]