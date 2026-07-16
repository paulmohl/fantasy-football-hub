FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml ./
RUN pip install --no-cache-dir hatchling && pip install --no-cache-dir "."

COPY . .

CMD ["uvicorn", "app.main:combined_app", "--host", "0.0.0.0", "--port", "8000"]
