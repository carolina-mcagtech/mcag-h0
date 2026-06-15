# MCAG Technologies SaaS — Claude Code Context

## Project
B2B SaaS for Florida home inspectors. White-label reports.
Multi-tenant via PostgreSQL RLS.

## Stack
- Backend: FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16
- Frontend: Next.js 14 + Tailwind + TypeScript strict
- Infra: AWS + Terraform + GitHub Actions (OIDC)

## Hard Rules
- RLS ALWAYS forced on all tables. No exceptions.
- NEVER include tenant_id in function signatures.
- Modular monolith — no microservices.
- Test-first: pytest (API) + vitest (web).
- 4h max per task. Decompose if larger.
- Never call session.add() directly on TenantScopedMixin objects. Always use repo.create()

## Repo Structure
/apps/api      → FastAPI application
/apps/web      → Next.js application  
/packages/shared → Shared types/utils
/infra         → Terraform (separate repo)

## Current Phase
Phase 0 — Foundation. No production workloads yet.
Customer discovery in progress (survey closes Jun 10).

## Architecture Rules
- AsyncSession + RLS: NUNCA event listeners para SET LOCAL.
  Usar `await session.execute(text(f"SET LOCAL ..."))` dentro de `session.begin()` en `get_session`.
  Sin `session.begin()`, SET LOCAL puede destruirse antes de que RLS evalúe la query (ADR-022/ADR-023).

- Transaction Lifecycle Hard Rule (ADR-023):
  `get_session` y `get_admin_session` son los ÚNICOS dueños del ciclo de vida de la transacción.
  Servicios y repos usan `flush()` = enviar SQL, permanecer en transacción, SET LOCAL sobrevive.
  `commit()` en servicios = terminar transacción = SET LOCAL destruido = RLS breach.
  NUNCA llamar `session.commit()` fuera de `get_session` / `get_admin_session`.

## When I ask for code
- Always include file path as comment
- Always include test alongside production code
- Flag if something violates RLS or tenant isolation
