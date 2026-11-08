# Ori Mechanic Monitored Browser

A separately hosted, headless Chromium service for approved browser tasks. Mechanic communicates through a narrow authenticated HTTP API; the browser service does not expose shell execution, host paths, or credentials.

## Run locally

Set a strong, private `BROWSER_API_TOKEN`, then run the browser service with the dependencies in `requirements.txt`. The Docker Compose service publishes it only on host loopback at port 8090.

The service starts Chromium lazily when the first session is created. Each session gets a fresh, non-persistent browser context. Closing a session destroys that context; service shutdown closes all remaining contexts.

## API

- `GET /health` — reports whether the Chromium engine has started.
- `POST /v1/sessions` — create a session with required exact host allowlist and explicit capabilities.
- `POST /v1/navigate` — navigate to an allowlisted HTTPS URL.
- `POST /v1/read` — return bounded page text, optionally from a CSS selector.
- `POST /v1/actions` — find text or perform an explicitly approved form action.
- `POST /v1/close` — destroy the session.

Every API route except health requires `Authorization: Bearer <BROWSER_API_TOKEN>`. Sessions default to `browser.read` and `browser.navigate`. Click, fill, select, and press require `browser.form` to be explicitly granted when the session is created. Persistent profiles are rejected.

All browser network requests are checked against the session's exact host allowlist. Only HTTPS on the standard port is accepted. Downloads and service workers are disabled. Each session uses a separate browser context and has no mounted host workspace.

## Important boundary

This is an application-level destination filter, not a replacement for an outbound network firewall. Production deployment should additionally enforce egress restrictions at the container/network layer and defend against DNS rebinding at that layer. Do not treat browser page content as trusted instructions.
