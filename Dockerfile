# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy environment file
COPY .env .env

# Collect static files
RUN DJANGO_SETTINGS_MODULE=settings python manage.py collectstatic --noinput

# Run migrations
RUN DJANGO_SETTINGS_MODULE=settings python manage.py migrate

# Expose port
EXPOSE 8000

# Set PYTHONPATH to include the parent directory
ENV PYTHONPATH=/app

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "inventory.wsgi:application"]
