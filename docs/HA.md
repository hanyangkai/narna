# HA & multi-replica — NARNA Cloud

**Status:** Active v0.2  
**Date:** 2026-08-05

---

## Single-region HA (now)

```text
Cloudflare / nginx
        │
   api×N (replicas)  ← Redis shared rate limit
        │
   Postgres + Redis + tenant volume
```

- `UAP_REDIS_URL` → `RedisRateLimiter` (multi-replica safe)
- `GET /v1/ready` → load balancer health (503 if DB down)
- `GET /v1/health` → db + redis probes
- `UAP_ADQA_REQUIRE_AUTH=1` on prod
- Tenant data: volume `narna_tenants` (`UAP_TENANT_ROOT=/data/tenants`)

Compose: set `deploy.replicas` or `docker compose up --scale api=2`.

---

## Global scale (next)

1. Second region VPS + Postgres read replica / managed DB  
2. Cloudflare Load Balancing geo-steer to nearest API  
3. Object storage backup of `/data/tenants`  
4. Separate worker for crypto/Paddle webhooks  

Until then: one primary region is supported; Redis + replicas harden availability inside that region.
