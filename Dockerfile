FROM node:24-alpine AS assets
WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY frontend ./frontend
COPY templates ./templates
COPY scripts ./scripts
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=assets /build/static /app/static
RUN python manage.py collectstatic --noinput
RUN useradd --create-home finpilot && chown -R finpilot:finpilot /app
USER finpilot
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
