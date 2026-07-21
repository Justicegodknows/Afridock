# Afridock (AfricaAI Platform)

A multi-tenant SaaS + self-hostable middleware layer that sits between African enterprises and a pool of open-source and commercial LLMs. See [Afridock_Implementation_Execution_Plan.md](Afridock_Implementation_Execution_Plan.md) for the full product/engineering plan and [CLAUDE.md](CLAUDE.md) for repository guidance.

## Monorepo layout

```
apps/api        FastAPI backend (Python 3.12)
apps/web        React + TypeScript frontend (Vite)
packages/shared Shared TypeScript types/contracts used by the frontend
infra/terraform Infrastructure as code (AWS af-south-1)
```

## Local development

Requires Docker and Docker Compose v2.

```bash
cp .env.example .env   # first time only
make dev
```

This starts Postgres (with pgvector), Redis, the API, and the web app:

- API: http://localhost:8000 (health check at `/healthz`, docs at `/docs`)
- Web: http://localhost:5173

Other common commands:

```bash
make test     # run backend + frontend test suites
make lint     # run backend + frontend linters
make migrate  # apply database migrations
make down     # stop the stack
```

## Repository status

This monorepo is scaffolding for **Phase 0 — Validation & Foundations**. It provides the skeleton described in the execution plan: a health-checked FastAPI service, a React shell, Docker Compose bootstrap, and CI. Feature work (auth, inference orchestration, chat UI, etc.) lands in subsequent phases — see the plan for the phase breakdown and acceptance criteria.
