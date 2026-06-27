FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY . .
RUN pip install --no-cache-dir ".[dev]"

CMD ["uvicorn", "app.main:combined_app", "--host", "0.0.0.0", "--port", "8000"]
