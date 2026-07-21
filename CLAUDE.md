# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY: consult progress.md before writing any code

Before writing or modifying **any** code, read [progress.md](progress.md) — the single source of truth for what has been built, what is in flight, and what to build next. Claim your task there before starting, and update it (Completed section, decisions log, Last-updated date) after finishing meaningful work. Do not start later-phase work or duplicate completed/claimed work.

This is enforced mechanically, not just by convention — see progress.md's "Enforcement" section. In short: a Claude Code hook blocks edits under `apps/`, `packages/`, `infra/` until progress.md has been read this session; a git pre-commit hook (run `make hooks-install` once per clone to activate it) blocks commits that touch code without also touching progress.md; and CI re-checks the same thing on every PR.

## Repository state

Phase 0 scaffolding is **complete**: the monorepo contains `apps/api` (FastAPI backend with `/healthz`, async SQLAlchemy, Alembic wiring, pytest/pytest-bdd), `apps/web` (React + Vite + Tailwind + Vitest shell), `packages/shared` (TS types), and `infra/terraform`, bootstrapped via `make dev` (Docker Compose: Postgres+pgvector, Redis, API, web). See [progress.md](progress.md) for exact status and next steps (Phase 1: E1 auth/orgs, E2 inference orchestrator, E3 chat UI, E4 history/search).

Common commands (all run through Docker Compose — see the Makefile): `make dev`, `make test`, `make lint`, `make fmt`, `make migrate`.

## Working from the plan document

[Afridock_Implementation_Execution_Plan.md](Afridock_Implementation_Execution_Plan.md) is the source of truth for scope, sequencing, and acceptance criteria. Treat its Gherkin scenarios as the acceptance tests each feature must satisfy — they are written to convert directly into pytest-bdd / Playwright specs. Key things to know before implementing anything:

- **Phased delivery, not a flat backlog.** Work is organized into Phase 0–4 (Weeks 1–4 Foundations, 4–12 Core MVP, 8–16 Governance/Integrations/Billing, 16–20 Resilience/Beta Launch, Months 6–12 Scale). Phases 1 and 2 overlap intentionally. Check which phase a request falls into — later-phase work (e.g. fine-tuning, self-hosting) depends on earlier-phase foundations (auth, org model, inference orchestrator) existing first.
- **Global Definition of Done applies to every story** (§3 of the plan): ≥80% backend line coverage, passing BDD scenarios, clean ruff/black/mypy/eslint/prettier, no unremediated Critical/High CVEs, Trivy scan clean, updated OpenAPI + README, structured logs/metrics/traces on new endpoints, green staging smoke test, peer review, changelog entry. Epic-specific DoD sections (end of each phase) are additive to this, not a replacement.
- **MoSCoW tags** ((M)/(S)/(C)/(W)) on each epic indicate priority within a phase — don't build a (W) item before the (M) items in the same phase are done.

## Architecture (from the plan)

Afridock is a **multi-tenant SaaS + self-hostable middleware layer** sitting between African enterprises and a pool of open-source/commercial LLMs, exposing a unified chat/API surface. Four architectural principles drive most design decisions and should be checked against when implementing any feature:

- **Provider-agnostic inference**: all model calls go through an inference orchestrator (LiteLLM) that abstracts provider/model/transport, so switching between Hugging Face-hosted Llama, self-hosted vLLM/Ollama, or a commercial fallback (Claude/OpenAI) requires no application code changes. Default model is Llama 3.1 8B/70B Instruct.
- **Offline-first**: requests queue and retry with exponential backoff (Celery server-side, Workbox/IndexedDB client-side); self-hosted deployments cache model artifacts locally so they survive connectivity loss. This is not an edge case to skip — E11/E12 in the plan make it a first-class requirement.
- **Multi-tenant by default with hard isolation**: enforced via Postgres row-level security at the data layer plus org-scoped auth at the API layer. Any new table or endpoint touching org data must preserve this — cross-tenant access tests are part of CI (see E1's "Tenant isolation on login" scenario as the pattern to follow).
- **Two deployment targets from one codebase**: managed SaaS (AWS ECS Fargate, af-south-1) and one-command self-hosted Docker Compose. Avoid features that only work in one mode unless explicitly scoped that way (self-hosting is Phase 4 / E19).

Request flow: Web app / Slack / WhatsApp / Google Sheets → API Gateway (FastAPI: auth, RBAC, rate-limit, billing, routing) → Inference Orchestrator (with fallback) → HF Inference API / vLLM-Ollama / Claude-OpenAI, alongside Postgres+pgvector (data/audit) and Redis (cache/queue/rate-limit). See §1.1 of the plan for the full diagram.

## Technology stack (target baseline, §2 of the plan)

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async) + Alembic, Pydantic 2.8, fastapi-users + Authlib (auth/SSO), Celery + Redis (queue/cache/rate-limit via slowapi), LiteLLM (orchestration), pgvector (RAG/search), httpx, OpenTelemetry + prometheus-client + structlog, pytest/pytest-asyncio/pytest-bdd for testing.

**Frontend**: TypeScript, React 18, Vite, React Router, TanStack Query, Zustand, Tailwind + shadcn/ui + Radix, react-hook-form + zod, react-i18next, Workbox + idb (offline PWA), Vitest/Testing Library/Playwright.

**Infra**: PostgreSQL 16, Redis 7.2, S3 (af-south-1) / MinIO for self-host, Docker + Docker Compose, Terraform, GitHub Actions, Cloudflare CDN, Prometheus/Grafana + Sentry + Loki.

**Code style**: ruff + black + mypy (Python), eslint + prettier (TS). Conventional Commits, trunk-based development with short-lived feature branches.

Exact patch versions are meant to be locked in `poetry.lock` / `package-lock.json` at sprint start — the plan's version table (§2) is a baseline, not a strict pin, until those lockfiles exist.
