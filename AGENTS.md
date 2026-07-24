# Afridock — Agent Instructions

## MANDATORY: consult progress.md before writing any code

Before writing or modifying **any** code, read [progress.md](progress.md). It is the single source of truth for what has been built, what is in flight, and what to build next. Do not start work that belongs to a later phase, and do not duplicate work already completed or claimed. After completing meaningful work, update progress.md (move items to Completed, log decisions, refresh the date) per its "How to update" section.

## What this repo is

Afridock is a multi-tenant SaaS + self-hostable middleware layer between African enterprises and a pool of open-source/commercial LLMs, exposing a unified chat/API surface.

- **Scope, sequencing, acceptance criteria**: [Afridock_Implementation_Execution_Plan.md](Afridock_Implementation_Execution_Plan.md) — the source of truth for *what to build*. Its Gherkin scenarios are the acceptance tests (pytest-bdd / Playwright).
- **Architecture principles, stack, and detailed repo guidance**: [CLAUDE.md](CLAUDE.md)
- **Layout and local dev**: [README.md](README.md)

## Layout

- `apps/api` — FastAPI backend (Python 3.12, SQLAlchemy 2.0 async, Alembic, pytest/pytest-bdd)
- `apps/web` — React 18 + TypeScript + Vite frontend (Tailwind, Vitest)
- `packages/shared` — shared TypeScript types/contracts
- `infra/terraform` — AWS infra (af-south-1)

## Commands (run via Docker Compose — see Makefile)

```bash
make dev       # full local stack (Postgres+pgvector, Redis, API :8000, web :5173)
make test      # backend (pytest) + frontend (vitest) suites
make lint      # ruff + black + mypy (API), eslint (web)
make fmt       # auto-format both
make migrate   # alembic upgrade head
```

## Non-negotiable rules

1. **Read progress.md first** (see above), claim your task there, update it when done.
2. **Low-cost AI via open-source models is the #1 constraint** — it outranks every other rule below when they conflict. Default every model-routing/infra/pricing decision to free or self-hosted open-weight inference; never let a commercial provider (Claude/OpenAI) become reachable without an organization's explicit opt-in (`Organization.allow_commercial_fallback`, enforced in `inference/fallback.py`'s `FallbackChain`). Adding a new model, provider, or pricing path without checking this is a bug, not a style nit.
3. **Follow the phase order** — MoSCoW (M) items in the current phase before (S)/(C) items; never build later-phase features on missing foundations.
4. **Tenant isolation**: any table or endpoint touching org data must enforce Postgres RLS + org-scoped auth, with cross-tenant access tests.
5. **Provider-agnostic inference**: all model calls go through the LiteLLM orchestrator — never call a provider SDK directly from application code.
6. **Two deployment targets**: features must work in managed SaaS *and* self-hosted Docker Compose unless explicitly scoped otherwise.
7. **Definition of Done** (plan §3) applies to every story: ≥80% backend coverage, passing BDD scenarios, clean ruff/black/mypy/eslint, updated OpenAPI, structured logs/metrics on new endpoints.
8. Conventional Commits; trunk-based development with short-lived branches.
