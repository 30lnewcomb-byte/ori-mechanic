# Sandbox

The Mechanic sandbox is an execution boundary for repair work.

It intentionally starts with no network access, a narrow command allowlist, a non-root container, dropped Linux capabilities, resource limits, and a dedicated workspace.

The sandbox must never receive unrestricted infrastructure credentials. Provider APIs and deployment actions belong to a separate controlled integration layer.