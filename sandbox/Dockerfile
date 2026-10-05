FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git nodejs npm build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 mechanic \
    && mkdir -p /workspace \
    && chown -R mechanic:mechanic /workspace

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY sandbox /app/sandbox

USER mechanic

ENV SANDBOX_WORKSPACE=/workspace
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/mechanic/.local/bin:/usr/local/bin:/usr/bin:/bin"

EXPOSE 8080
CMD ["uvicorn", "sandbox.runner:app", "--host", "0.0.0.0", "--port", "8080"]
