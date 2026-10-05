# Mechanic Monitored Browser

A lightweight browser runtime designed specifically for Ori Mechanic.

The browser is an instrument, not an unrestricted desktop. Mechanic communicates with it through a narrow API and every navigation/action is observable and policy-checked.

## Design goals

- Lightweight headless Chromium-based runtime.
- No direct host filesystem access.
- No access to Mechanic credentials.
- HTTPS-only navigation.
- Explicit domain allowlists.
- Separate read, navigation, form, and download capabilities.
- Network requests observable at the browser boundary.
- Browser actions recorded as audit events.
- Downloads isolated into a disposable workspace.
- Browser session destroyed after a job unless explicitly retained by policy.
- Page content is untrusted input and cannot modify Mechanic policy.

## Planned API

- `POST /v1/sessions` — create an isolated browser session.
- `POST /v1/navigate` — navigate to an allowlisted HTTPS URL.
- `POST /v1/read` — return sanitized page content.
- `POST /v1/actions` — perform a permitted browser action.
- `POST /v1/close` — destroy the session.
- `GET /health` — health check.

The browser runtime must run separately from the Mechanic decision process and must not expose arbitrary shell execution.
