# Use Python slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p /app/uploads \
    /app/scraped_data \
    /app/static \
    /app/templates \
    /app/utils \
    /app/gas_furnaces \
    /app/.scrapy \
    && chmod -R 777 /app/uploads \
    && chmod -R 777 /app/scraped_data \
    && chmod -R 777 /app/static \
    && chmod -R 777 /app/templates \
    && chmod -R 777 /app/gas_furnaces \
    && chmod -R 777 /app/.scrapy

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python packages
RUN  pip install --no-cache-dir --retries 10 --timeout 100 -r requirements.txt 

# Copy application files
COPY app.py .
COPY brain.py .
COPY hash.py .
COPY init.sql .
COPY scrapy.cfg .
COPY package-lock.json .
COPY requirements.txt .
COPY .env .
COPY file.json .
COPY package-lock.json .
COPY utils/ ./utils/
COPY static/ ./static/
COPY templates/ ./templates/
COPY scraped_data/ ./scraped_data/
COPY gas_furnaces/ ./gas_furnaces/
COPY .scrapy/ ./.scrapy/

# Copy and set entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN chmod -R 777 /app/uploads

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    RECAPTCHA_SECRET_KEY=6LdhBOcqAAAAAF3yO9Oex4XsQsWi-gVuHMM_uYk7 \
    SMTP_SERVER=smtp.gmail.com \
    SMTP_PORT=587

# Expose port 5000
EXPOSE 5000

# Command to run the application
ENTRYPOINT ["/entrypoint.sh"]
