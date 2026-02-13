FROM python:3.11-slim

WORKDIR /app

# Gerekli sistem paketlerini yükle (Pillow için)
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Python paketlerini yükle
RUN pip install --no-cache-dir flask pillow gunicorn

# Uygulamayı kopyala
COPY app.py .

# Production için Gunicorn kullan
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]