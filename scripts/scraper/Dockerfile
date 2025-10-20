FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Create app and output dirs and a non-root user
RUN useradd -m appuser && mkdir -p /app /out && chown -R appuser:appuser /app /out

# Install deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY scrape_groong_news.py /app/scrape_groong_news.py
RUN chown -R appuser:appuser /app

# Write outputs here by default
WORKDIR /out
USER appuser

ENTRYPOINT ["python", "-u", "/app/scrape_groong_news.py"]

