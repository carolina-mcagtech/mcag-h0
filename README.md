# MCAG Technologies · SaaS Platform

B2B SaaS for Florida home inspectors. White-label inspection 
reports and client portal with 100% inspector branding.

**Status:** Pre-revenue · Customer discovery phase · Jun 2026

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 (multi-tenant via RLS) |
| Frontend | Next.js 14 + Tailwind + TypeScript |
| Auth | AWS Cognito |
| Infra | AWS + Terraform (see mcagtech-infra) |
| CI/CD | GitHub Actions + OIDC → AWS |

## Architecture principles

- Multi-tenancy via Row-Level Security (RLS) — forced on all tables
- Modular monolith — no microservices until Phase 3+
- Test-first: pytest (API) + vitest (web)
- Cost ceiling: $200/mo pre-revenue

## Repo structure
apps/
api/          → FastAPI application
web/          → Next.js application
packages/
shared/       → Shared types and utilities

## Development

> Setup instructions will be added when development begins (Week 4+)

## Company

MCAG Technologies LLC · Florida · mcagtech.com
