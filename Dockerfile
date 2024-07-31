FROM python:3.12.3-slim

WORKDIR /app
COPY requirements.lock ./
COPY pyproject.toml ./
COPY README.md ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY src .
CMD python sloy/main.py
