FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY browser/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep the browser cache outside root's home so the unprivileged runtime user
# can launch the Chromium binary installed during the image build.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright \
    && chmod 755 /ms-playwright \
    && playwright install --with-deps chromium

RUN useradd --create-home --uid 10002 mechanic-browser

COPY browser /app/browser
USER mechanic-browser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "browser.service:app", "--host", "0.0.0.0", "--port", "8080"]
