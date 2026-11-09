# Hosting evaluation — 9 November 2026

This is a fit check, not a production-provider commitment. Re-check plan limits
before creating services because free tiers can change.

## What the repository actually needs

The current Compose file defines two isolated execution services:

- Browser: 2 CPU and 1 GiB RAM, with a dedicated Chromium image.
- Sandbox: 1 CPU and 512 MiB RAM, network disabled, restricted capabilities.

The eventual coordinator/API also needs durable job storage, secrets, health
checks, and private service-to-service communication. Do not put Chromium and
the sandbox inside the public coordinator process just to fit a tiny free tier.

## Candidate comparison

| Provider | Current published free offer | Ori Mechanic fit |
| --- | --- | --- |
| Back4App Containers | 0.25 CPU, 256 MiB RAM, 100 GB transfer per free container; GitHub Docker deploy; no card stated on official pricing page | Useful for a very small API experiment. Not enough for the current Chromium worker (1 GiB / 2 CPU) or sandbox (512 MiB / 1 CPU). Treat as a possible small control-plane host, not the whole stack. |
| Northflank Sandbox | No card; 2 services, 2 jobs, 1 database, up to $20/month of cloud resources; always-on/no sleeping | Best candidate for an initial multi-service prototype. Its own docs say the free Sandbox is for exploring/hobby projects and not production. Measure the resource budget before deploying the browser worker. |
| Freestyle Free | 10 concurrent VMs; included monthly allowances of 200 vCPU-hours, 400 GiB-memory-hours, and 50 GB transfer; Free plan does not include persistent VMs | Interesting for temporary worker experiments and on-demand VM work. Not a safe assumption for an always-on production coordinator: free persistent VMs are not included and compute allowances are hard limits. |
| Koyeb Free | One web service, 512 MiB RAM, 0.1 vCPU, 2 GB SSD; no volumes; cannot be used as a Worker Service; scales to zero after one idle hour | Not suitable for the persistent coordinator + separate workers architecture. |

## Recommended next step

Use Northflank only as the leading candidate for a disposable staging/prototype
deployment, subject to confirming the service resource sizes and free resource
budget. Keep Back4App on the shortlist for a tiny stateless API or a separate
managed data component, not Chromium hosting. Do not deploy production jobs to
any free tier until persistence, backups, private networking, limits, and
recovery have been verified.

Keep the production architecture portable in Docker Compose. The host should
not become a runtime dependency of the Mechanic codebase.

## Official plan references

- Back4App Containers: https://www.back4app.com/pricing/container-as-a-service
- Northflank pricing: https://northflank.com/pricing
- Northflank free-plan notes: https://northflank.com/docs/v1/application/billing/pricing-on-northflank
- Freestyle pricing and limits: https://www.freestyle.sh/docs/vms/pricing-and-limits
- Koyeb instance limits: https://www.koyeb.com/docs/reference/instances
