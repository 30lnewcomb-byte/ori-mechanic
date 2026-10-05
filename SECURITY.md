# Ori Mechanic Security Model

Ori Mechanic follows a **passenger, not driver** model: it can perform approved work, but authority is deliberately constrained.

## Autonomy tiers

- **Green:** routine, reversible recovery work can run automatically.
- **Yellow:** infrastructure or deployment changes require explicit human approval.
- **Red:** destructive, credential-revealing, authentication, security-policy, or data-destroying actions are never autonomous.

## Anti-jailbreak architecture

Mechanic does not receive a shell or direct process-execution primitive. Execution goes through the authenticated sandbox API.

The sandbox independently enforces:

- Bearer-token authentication for job execution.
- Network disabled at both API and container layers.
- A small command allowlist; unknown executables are rejected.
- Explicit blocking of privilege escalation, container control, host networking, and destructive system commands.
- Non-root execution, dropped Linux capabilities, `no-new-privileges`, read-only container filesystem, resource limits, and a dedicated workspace.
- A fixed `/workspace` mount; clients cannot select another host path.
- A minimal environment with no provider credentials.

These controls are intentionally redundant. A model instruction, prompt, tool argument, or compromised decision layer must not be sufficient to grant itself new privileges.

## API credential rules

`SANDBOX_API_TOKEN` is supplied through the runtime environment and is never committed to Git. The sandbox API refuses execution when authentication is not configured.

The token grants access only to the sandbox API. It is not a provider credential and must not be reused for GitHub, Vercel, Render, cloud, or user accounts.

## Audit

Control-plane decisions should produce structured audit events. Logs must contain identifiers and outcomes, not secrets, tokens, passwords, or raw credentials.
