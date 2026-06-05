FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY contracts ./contracts
COPY infra ./infra
COPY services ./services

RUN mkdir -p runtime && chown -R 10001:10001 /app

CMD ["python", "-m", "services.api_gateway.main"]
