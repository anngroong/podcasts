# Small, up-to-date Python base
FROM python:3.12-slim

# Security + reliability basics
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system packages that help with TLS, IDNA, and certs (usually already present,
# but these keep things robust across environments).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Workdir
WORKDIR /app

# Copy dependency list and install first (better Docker layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scraper
COPY scrape_groong_news.py /app/

# Drop privileges
USER appuser

# Default command: run the scraper with no date filter
# You can override args at runtime, e.g.:
#   docker run --rm groong-scraper --date 20251011
ENTRYPOINT ["python", "/app/scrape_groong_news.py"]

