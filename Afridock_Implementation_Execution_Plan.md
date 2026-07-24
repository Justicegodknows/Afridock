# Afridock (AfricaAI Platform) — Implementation & Execution Plan

**An Enterprise AI Platform for African Markets — Nigeria First**

Document version: 1.0 · Last updated: 18 July 2026 · Owner: Product Lead

---

## 0. How to Read This Document

This plan turns the AfricaAI product brief into a buildable, testable engineering program. It is organized into five delivery phases (Phase 0–4) mapped to the brief's timeline. Each phase specifies scope, the exact technology stack and pinned dependencies, work packages, and — for every epic — **Acceptance Criteria (AC)** and **Definition of Done (DoD)** expressed in **Gherkin** so they are directly convertible into automated tests (Cucumber/Behave/pytest-bdd).

Conventions used throughout:

- **AC (Acceptance Criteria)** — the behavioural contract a feature must satisfy, written as `Feature/Scenario` Gherkin.
- **DoD (Definition of Done)** — the engineering gate a work item must pass before it is considered shippable (tests, docs, security, observability). A global DoD applies to every story; epic-specific DoD is additive.
- **MoSCoW** priority tags: (M)ust, (S)hould, (C)ould, (W)on't-this-phase.
- Version pins are the target baseline; exact patch versions are locked in `poetry.lock` / `package-lock.json` at sprint start.

---

## 1. Architecture Overview

### 1.1 System Context

Afridock is a multi-tenant SaaS + self-hostable middleware layer that sits between African enterprises and a pool of open-source and commercial LLMs. It provides a unified chat/API surface, enterprise governance (auth, RBAC, audit, cost), local-first resilience, and Africa-specific integrations (WhatsApp, Paystack/Flutterwave, local languages).

```
                        ┌───────────────────────────────────────────────┐
   Users / Admins  ───► │  Web App (React/TS)   Mobile-responsive PWA     │
                        └───────────────┬───────────────────────────────┘
                                        │ HTTPS / JSON + SSE (streaming)
                        ┌───────────────▼───────────────────────────────┐
   Slack / WhatsApp ──► │            API Gateway (FastAPI)                │
   Google Sheets    ──► │  Auth · RBAC · Rate-limit · Billing · Routing   │
                        └───┬───────────────┬───────────────┬────────────┘
                            │               │               │
                   ┌────────▼───┐   ┌────────▼─────┐  ┌──────▼────────┐
                   │ Inference   │   │  Postgres    │  │  Redis         │
                   │ Orchestrator│   │ (data/audit) │  │ (cache/queue/  │
                   │ + Fallback  │   │  + pgvector  │  │  rate-limit)   │
                   └───┬────┬────┘   └──────────────┘  └───────────────┘
                       │    │
             ┌─────────▼┐  ┌▼──────────────┐   ┌──────────────────────┐
             │ HF Infer │  │ vLLM / Ollama │   │ Claude / OpenAI (esc.)│
             │  API     │  │ (self-host)   │   │  fallback provider    │
             └──────────┘  └───────────────┘   └──────────────────────┘
```

### 1.2 Architectural Principles

**Low-cost AI via open-source models is the #1 design constraint, and it outranks every other principle below when they conflict.** Every model-routing, infrastructure, and pricing decision defaults to free or self-hosted open-weight inference (Llama, Mistral/Mixtral, via HF/vLLM/Ollama); commercial providers (Claude/GPT-4-class) are an explicit, cost-flagged, opt-in escape hatch — never a silent default a customer or organization can be enrolled into without consent. Concretely: the inference orchestrator's default fallback chain always exhausts open-source/self-hosted candidates before a commercial one is even considered, and an organization must explicitly opt in before any commercial (non-zero marginal cost) model call is permitted at all (see Phase 2 §E2/E6 and `progress.md`'s decisions log for the enforcement mechanism). This is what makes the platform viable for price-sensitive African markets — it is a business-model requirement, not a preference.

The platform is **provider-agnostic**: every model call passes through an inference orchestrator that abstracts provider, model, and transport, so a customer can move between Llama on Hugging Face, self-hosted vLLM, or a commercial fallback without changing application code. It is **offline-first**: requests are queued and retried with exponential backoff, and model artifacts are cached so on-prem deployments survive connectivity loss. It is **multi-tenant by default** with hard isolation at the organization boundary enforced in the data layer (row-level security) and the auth layer. It is **observable from day one**: every request emits structured logs, metrics, and cost attribution. Finally it is **deployable two ways** from a single codebase — managed SaaS and one-command self-hosted Docker.

---

## 2. Full Technology Stack

### 2.1 Backend

| Concern | Choice | Version (baseline) | Rationale |
|---|---|---|---|
| Language | Python | 3.12 | Team familiarity, ML ecosystem |
| Web framework | FastAPI | 0.111 | Async, OpenAPI, SSE streaming |
| ASGI server | Uvicorn + Gunicorn | 0.30 / 22.0 | Prod-grade async workers |
| Data validation | Pydantic | 2.8 | Request/response contracts |
| ORM | SQLAlchemy | 2.0 | Async ORM, mature |
| Migrations | Alembic | 1.13 | Schema versioning |
| Auth | fastapi-users + Authlib | 13.0 / 1.3 | Email + OAuth/SSO |
| Task queue | Celery | 5.4 | Async jobs, retries, offline queue |
| Queue broker/result | Redis | 7.2 | Broker, cache, rate-limit |
| Rate limiting | slowapi | 0.1.9 | Per-org/token throttling |
| LLM orchestration | LiteLLM | 1.40 | Unified provider interface + fallback |
| Local inference client | huggingface_hub, openai (vLLM-compatible) | 0.24 / 1.35 | HF Inference + vLLM/Ollama OpenAI-compatible endpoints |
| Vector search | pgvector | 0.7 | RAG / conversation search |
| Billing | stripe, paystack, custom Flutterwave client | 10.0 | Local + intl payments |
| HTTP client | httpx | 0.27 | Async provider calls |
| Observability | OpenTelemetry SDK, prometheus-client, structlog | 1.25 / 0.20 / 24.1 | Traces, metrics, structured logs |
| Testing | pytest, pytest-asyncio, pytest-bdd, httpx, factory-boy | 8.2 / 0.23 / 7.0 | Unit + BDD/Gherkin + fixtures |

### 2.2 Frontend

| Concern | Choice | Version (baseline) | Rationale |
|---|---|---|---|
| Language | TypeScript | 5.5 | Type safety |
| Framework | React | 18.3 | Team standard |
| Build/dev | Vite | 5.3 | Fast builds |
| Routing | React Router | 6.24 | SPA routing |
| Server state | TanStack Query | 5.51 | Caching, retries, offline |
| Client state | Zustand | 4.5 | Lightweight state |
| Styling | Tailwind CSS | 3.4 | Rapid, responsive |
| Components | shadcn/ui + Radix | latest | Accessible primitives |
| Streaming | native EventSource / fetch SSE | — | Token streaming |
| Offline | Workbox (service worker) + IndexedDB (idb) | 7.1 / 8.0 | PWA offline queue |
| Forms | react-hook-form + zod | 7.52 / 3.23 | Validation parity with backend |
| i18n | react-i18next | 14.1 | Local language UI |
| Testing | Vitest, Testing Library, Playwright | 2.0 / 16.0 / 1.45 | Unit + E2E |

### 2.3 Data, Infra & DevOps

| Concern | Choice | Version | Rationale |
|---|---|---|---|
| Primary DB | PostgreSQL | 16 | Relational + pgvector + RLS |
| Cache/queue | Redis | 7.2 | Cache, Celery, rate-limit |
| Object storage | AWS S3 (af-south-1) / MinIO (self-host) | — | Uploads, model cache |
| Containers | Docker + Docker Compose | 26 / v2 | Dev parity + self-host |
| Orchestration (SaaS) | AWS ECS Fargate (Cape Town, af-south-1) | — | Managed scaling, low latency to NG |
| IaC | Terraform | 1.9 | Reproducible infra |
| CI/CD | GitHub Actions | — | Test, build, scan, deploy |
| Registry | Amazon ECR / GHCR | — | Image hosting |
| CDN/edge | Cloudflare | — | Global access, DDoS, cache |
| Secrets | AWS Secrets Manager / Doppler | — | Secret management |
| Monitoring | Prometheus + Grafana; Sentry; Loki | — | Metrics, errors, logs |
| Uptime/synthetic | Better Stack / UptimeRobot | — | SLA tracking |
| Self-host inference | vLLM or Ollama | latest | On-prem model serving |

### 2.4 ML / Model Layer

Default model **Llama 3.1 8B/70B Instruct** (updated from brief's Llama 2 to current-generation open weights), plus **Mistral 7B / Mixtral 8x7B**, with **Claude / GPT-4-class** as escape-hatch fallback. Fine-tuning (Phase 2) uses **PEFT/LoRA** via `peft` + `transformers` + `trl`, tracked with **MLflow**, artifacts stored in S3/MinIO. Local-language coverage (Yoruba, Hausa, Igbo, Swahili) is delivered first via a translation layer (NLLB-200 / commercial MT) and localized prompt templates, then via fine-tuned adapters.

### 2.5 Cross-cutting Standards

Code style enforced by **ruff + black + mypy** (Python) and **eslint + prettier** (TS). Commits follow **Conventional Commits**; branches use trunk-based flow with short-lived feature branches. Every service ships an **OpenAPI 3.1** spec and a **README**. Security baseline: OWASP ASVS L2 target, dependency scanning (Dependabot + `pip-audit`/`npm audit`), container scanning (Trivy), secret scanning (gitleaks).

---

## 3. Global Definition of Done

The following DoD applies to **every** user story in every phase. Epic-specific DoD sections are additive.

```gherkin
Feature: Global Definition of Done
  A story is only "Done" when it clears every engineering gate.

  Scenario: Story passes the universal quality gate
    Given a completed user story with merged code
    When the CI pipeline runs on the pull request
    Then all unit tests pass with backend line coverage >= 80%
    And all BDD acceptance scenarios for the story pass
    And linting (ruff, black, mypy, eslint, prettier) reports no errors
    And no dependency has a known Critical or High CVE unremediated
    And the container image passes Trivy scan with no Critical findings
    And OpenAPI docs and the relevant README are updated
    And structured logs, metrics, and traces are emitted for new endpoints
    And the feature is deployed to staging and smoke-tested green
    And the story is peer-reviewed and approved by at least one engineer
    And user-facing changes have an entry in the changelog
```

---

## 4. Phased Delivery Plan

| Phase | Timeline | Theme | Exit outcome |
|---|---|---|---|
| Phase 0 | Weeks 1–4 | Validation & Foundations | 20+ interviews, 3–5 pilots, repo + CI + skeleton |
| Phase 1 | Weeks 4–12 | Core MVP | Chat + Llama inference + auth + org mgmt |
| Phase 2 | Weeks 8–16 | Governance, Integrations, Billing | RBAC, audit, Slack, WhatsApp, Paystack |
| Phase 3 | Weeks 16–20 | Resilience, Polish, Beta Launch | Offline queue, mobile, security audit, public launch |
| Phase 4 | Months 6–12 | Scale & Differentiation | Fine-tuning, local languages, workflows, self-hosting |

Phases 1 and 2 overlap intentionally so integration work begins while chat hardens.

---

## Phase 0 — Validation & Foundations (Weeks 1–4)

### Scope
Confirm market/pricing via discovery interviews, stand up the engineering foundation (repos, CI/CD, environments, IaC skeleton), and freeze the tech stack.

### Work packages
Customer discovery (20 interviews, shared tracking sheet, validation doc); monorepo scaffolding (`apps/api`, `apps/web`, `infra/`, `packages/shared`); CI/CD baseline; Postgres + Redis provisioned in af-south-1; skeleton FastAPI health service and React shell deployed to staging; observability bootstrap (Sentry, Prometheus scrape, structlog).

### Dependencies introduced
Backend: FastAPI, Uvicorn, SQLAlchemy, Alembic, structlog, pytest, pytest-bdd. Infra: Terraform, Docker Compose, GitHub Actions, Trivy, gitleaks. Frontend: Vite, React, TypeScript, Tailwind.

### Acceptance Criteria (Gherkin)

```gherkin
Feature: Validation evidence gate
  Ensure we build against validated demand.

  Scenario: Discovery threshold met
    Given the go-to-market lead has conducted customer interviews
    When the validation review is held at end of Week 4
    Then at least 20 completed interviews are logged in the tracking sheet
    And at least 3 customers have committed in writing to a pilot
    And a validation document summarizes problems, use cases, and pricing sensitivity

  Scenario: Pricing sensitivity captured
    Given each interview record
    Then it contains the prospect's current AI stack
    And a stated willingness-to-pay band
    And a self-host vs managed hosting preference
```

```gherkin
Feature: Engineering foundation ready
  A new engineer can build and ship on day one.

  Scenario: One-command local bootstrap
    Given a fresh checkout of the monorepo
    When a developer runs "make dev"
    Then Postgres, Redis, the API, and the web app start via Docker Compose
    And the API health endpoint returns 200 at /healthz
    And the web shell loads at localhost with no console errors

  Scenario: CI pipeline enforces quality on every PR
    Given a pull request is opened
    When GitHub Actions runs
    Then lint, type-check, unit tests, and container scan all execute
    And a failing check blocks merge to main

  Scenario: Staging deploy is automated
    Given code is merged to main
    When the deploy workflow runs
    Then the API and web app are deployed to the af-south-1 staging environment
    And a post-deploy smoke test hits /healthz and returns 200
```

### Phase 0 DoD (additive)
Terraform state stored remotely with locking; staging reachable over HTTPS via Cloudflare; runbook for local dev committed; validation doc signed off by Product Lead.

---

## Phase 1 — Core MVP: Chat & Inference (Weeks 4–12)

### Scope
Deliver the core multi-model chat experience over Llama 3.1 (default) with conversation persistence, search, streaming, email auth, and organization/workspace scaffolding.

### Epics
E1 Authentication & Organizations · E2 Inference Orchestrator (LiteLLM) · E3 Chat UI & Streaming · E4 Conversation History & Search.

### Dependencies introduced
Backend: fastapi-users, Authlib, LiteLLM, huggingface_hub, openai (vLLM-compatible), httpx, pgvector, Celery. Frontend: TanStack Query, Zustand, react-hook-form, zod, EventSource/SSE, Workbox (baseline).

### E1 — Authentication & Organizations (M)

```gherkin
Feature: Email authentication and organization membership
  Users sign up, verify, and belong to an isolated organization.

  Background:
    Given the auth service is running

  Scenario: Successful signup and email verification
    Given a visitor provides a valid email and a strong password
    When they submit the signup form
    Then an organization is created and the user becomes its Admin
    And a verification email is sent
    And the account is inactive until the verification link is used

  Scenario: Weak password rejected
    Given a visitor provides a password shorter than 12 characters
    When they submit the signup form
    Then signup is rejected with a clear validation message

  Scenario: Tenant isolation on login
    Given two organizations "Alpha" and "Beta" exist
    When a user from "Alpha" authenticates
    Then their session can only access "Alpha" resources
    And any request scoped to "Beta" returns 403
```

### E2 — Inference Orchestrator (M)

```gherkin
Feature: Provider-agnostic model inference
  The platform routes chat requests to a configured model provider.

  Scenario: Default model responds
    Given an authenticated user in an organization
    And the default model is "llama-3.1-8b-instruct" served via Hugging Face
    When they send a chat message
    Then a completion is returned within the configured timeout
    And the response tokens stream to the client incrementally

  Scenario: Model switching at conversation level
    Given a conversation currently using "llama-3.1-8b-instruct"
    When the user switches the model to "mistral-7b-instruct"
    Then subsequent messages in that conversation use the new model
    And earlier messages retain their original model attribution

  Scenario: Provider failure triggers fallback
    Given the primary Hugging Face endpoint returns errors
    And a fallback provider is configured
    When a chat request is made
    Then the orchestrator retries and routes to the fallback provider
    And the user receives a valid completion
    And the fallback event is recorded in logs and metrics
```

### E3 — Chat UI & Streaming (M)

```gherkin
Feature: Responsive streaming chat interface
  Users converse with the model in a fast, mobile-friendly UI.

  Scenario: Streaming tokens render live
    Given a user has opened a conversation
    When they submit a prompt
    Then a streaming response appears token-by-token
    And a stop-generation control is available while streaming

  Scenario: Mobile-responsive layout
    Given the app is viewed at a 375px viewport width
    Then the chat is fully usable with no horizontal scrolling
    And the input remains fixed and reachable

  Scenario: Error surfaced gracefully
    Given the backend returns an inference error
    When the user is waiting on a response
    Then a non-blocking error message is shown with a retry action
```

### E4 — Conversation History & Search (S)

```gherkin
Feature: Persistent conversation history and search
  Users revisit and find past conversations.

  Scenario: Conversations persist across sessions
    Given a user has chatted and then logged out
    When they log back in
    Then their previous conversations are listed newest-first

  Scenario: Full-text and semantic search
    Given a user has 50 past conversations
    When they search for a phrase used in an earlier chat
    Then matching conversations are returned ranked by relevance
    And results are scoped to the user's organization only
```

### Phase 1 DoD (additive)
Chat p95 latency to first token < 2s on staging with the default model; all E1–E4 scenarios automated in pytest-bdd + Playwright; tenant isolation verified by an automated cross-tenant access test; OpenAPI spec published for chat and auth endpoints.

---

## Phase 2 — Governance, Integrations & Billing (Weeks 8–16)

### Scope
Add enterprise governance (RBAC, API keys, audit logs, cost attribution) and the Africa-priority integrations and billing (Slack, WhatsApp Business, Google Sheets, Paystack, Flutterwave).

### Epics
E5 RBAC & API Keys · E6 Audit Logs & Cost Attribution · E7 Slack Integration · E8 WhatsApp Business Integration · E9 Google Sheets Integration · E10 Usage-Based Billing (Paystack/Flutterwave).

### Dependencies introduced
Backend: slowapi, stripe, paystack SDK, custom Flutterwave client, slack-sdk, google-api-python-client + google-auth, Meta WhatsApp Cloud API (httpx), OpenTelemetry exporters. Frontend: recharts (cost dashboards), data-table components.

### E5 — RBAC & API Keys (M)

```gherkin
Feature: Role-based access control and API keys
  Admins govern who can do what, and issue machine credentials.

  Scenario Outline: Role permissions enforced
    Given a user with role "<role>"
    When they attempt the action "<action>"
    Then the request is "<result>"

    Examples:
      | role   | action                    | result   |
      | Admin  | invite a new user         | allowed  |
      | Admin  | rotate an API key         | allowed  |
      | User   | send a chat message       | allowed  |
      | User   | change billing settings   | denied   |
      | Viewer | view conversations        | allowed  |
      | Viewer | send a chat message       | denied   |

  Scenario: API key scoped to organization
    Given an Admin generates an API key
    When a request is made with that key
    Then it is authorized only for that key's organization
    And the key can be revoked, after which further requests return 401
```

### E6 — Audit Logs & Cost Attribution (M)

```gherkin
Feature: Audit logging and cost attribution
  Every billable action is traceable to who, what, when, and how much.

  Scenario: Chat request is audited
    Given a user sends a chat message
    When the response completes
    Then an audit record captures user id, org id, model, timestamp
    And token counts for prompt and completion are stored
    And an estimated cost is computed and attributed to the organization

  Scenario: Admin exports an audit trail
    Given an Admin opens the audit view for a date range
    When they export the logs
    Then a CSV is produced containing all actions in that range
    And Viewers cannot access the audit export
```

### E7 — Slack Integration (M)

```gherkin
Feature: Slack integration
  Teams invoke Afridock from Slack.

  Scenario: Slash command returns a completion
    Given an organization has connected its Slack workspace via OAuth
    When a member runs the "/afridock <prompt>" command
    Then the model response is posted back in the same channel or thread
    And the interaction is attributed to the linked organization for billing

  Scenario: Signature verification
    Given an inbound Slack request
    When the request signature is invalid or expired
    Then the request is rejected with 401 and no model call is made
```

### E8 — WhatsApp Business Integration (M)

```gherkin
Feature: WhatsApp Business support automation
  Customers of a BPO reach an AI agent over WhatsApp.

  Scenario: Inbound message answered
    Given an organization has configured a WhatsApp Business number
    When an end customer sends a WhatsApp message
    Then the platform verifies the Meta webhook signature
    And routes the message to the org's configured model
    And replies to the customer within the WhatsApp session window

  Scenario: Delivery resilience under connectivity loss
    Given an outbound reply fails due to a transient network error
    When the send is attempted
    Then it is queued and retried with exponential backoff
    And the message is marked delivered once acknowledged
```

### E9 — Google Sheets Integration (S)

```gherkin
Feature: Google Sheets input and output
  Users pipe data in and out of Sheets.

  Scenario: Write model output to a sheet
    Given an organization has authorized Google Sheets access
    When a user directs a completion to a target spreadsheet and range
    Then the output is written to the specified range
    And a failure to write surfaces a clear, actionable error
```

### E10 — Usage-Based Billing (M)

```gherkin
Feature: Usage-based billing with local payment methods
  Organizations pay for what they use via Paystack or Flutterwave.

  Scenario: Metered usage accrues to an invoice
    Given an organization on the Starter tier
    When its members consume 1,200,000 tokens in a billing period
    Then usage above the included 1,000,000 tokens is billed as overage
    And the cost dashboard reflects near-real-time consumption

  Scenario: Successful Paystack payment
    Given an organization initiates payment via Paystack
    When the Paystack webhook confirms a successful charge
    Then the invoice is marked paid
    And the webhook signature is verified before the state change
    And a duplicate webhook does not double-credit the account

  Scenario: Free tier limits enforced
    Given an organization on the Free tier
    When it exceeds the free monthly inference allowance
    Then further requests are rejected with an upgrade prompt
    And no charge is made without an active paid plan
```

### Phase 2 DoD (additive)
Every integration verifies inbound webhook signatures; billing webhook handlers are idempotent (proven by a replay test); cost attribution reconciles to within 1% of provider-reported usage in a staging load test; RBAC matrix fully covered by scenario tests; PII in logs is redacted.

---

## Phase 3 — Resilience, Polish & Beta Launch (Weeks 16–20)

### Scope
Harden offline/low-bandwidth behaviour, complete PWA offline queueing and local model caching, finish mobile responsiveness, pass a security audit, and launch publicly with community activation.

### Epics
E11 Offline Queue & Retry · E12 Local Model Caching · E13 Mobile/PWA Polish · E14 Security Hardening & Audit · E15 Launch Readiness.

### Dependencies introduced
Frontend: Workbox (full), idb, background sync. Backend: Celery beat, dead-letter queue handling. Security: Trivy (gate), OWASP ZAP baseline scan in CI, `pip-audit`, `npm audit`, gitleaks (gate).

### E11 — Offline Queue & Retry (M)

```gherkin
Feature: Offline-first request handling
  Work is not lost during connectivity gaps.

  Scenario: Request queued while offline
    Given a user is composing a chat message
    And the device loses network connectivity
    When they submit the message
    Then it is stored in an on-device queue
    And a "queued — will send when online" indicator is shown

  Scenario: Automatic flush on reconnect
    Given queued messages exist on the device
    When connectivity is restored
    Then queued messages are sent in order
    And successful sends are removed from the queue
    And a message failing after max retries moves to a visible failed state

  Scenario: Server-side retry with backoff
    Given a background inference job fails transiently
    When Celery processes the job
    Then it retries with exponential backoff up to the configured limit
    And exhausted jobs land in a dead-letter queue for inspection
```

### E12 — Local Model Caching (S)

```gherkin
Feature: Local model caching for offline inference
  Self-hosted deployments run without live internet.

  Scenario: Download once, serve offline
    Given a self-hosted deployment configured for a cached model
    When the model has been downloaded to local storage
    And the host has no internet access
    Then inference requests are served by the local model
    And no external provider call is attempted
```

### E13 — Mobile / PWA Polish (S)

```gherkin
Feature: Installable, responsive PWA
  The app works well on low-end mobile devices.

  Scenario: Installable to home screen
    Given a user visits the app on a mobile browser
    Then a valid web app manifest and service worker are served
    And the app can be installed to the home screen

  Scenario: Usable on low bandwidth
    Given a simulated 2G/3G connection
    When the app loads
    Then the initial interactive load completes within the performance budget
    And core chat remains usable
```

### E14 — Security Hardening & Audit (M)

```gherkin
Feature: Security baseline and audit
  The platform meets its security bar before public launch.

  Scenario: Automated security gates in CI
    Given a release candidate build
    When the security pipeline runs
    Then dependency, container, secret, and DAST baseline scans execute
    And any Critical finding blocks the release

  Scenario: Third-party audit remediation
    Given an external security review is completed
    When findings are triaged
    Then all Critical and High findings are remediated or formally accepted with mitigation
    Before the production launch is approved
```

### E15 — Launch Readiness (M)

```gherkin
Feature: Beta launch readiness
  We can safely onboard the public and first paying customers.

  Scenario: Production SLOs configured
    Given the production environment
    Then uptime monitoring, alerting, and on-call rotation (NG timezone) are active
    And error budget and latency SLOs are defined and dashboarded

  Scenario: First paying customers onboarded
    Given the public launch has occurred
    When onboarding runs for the first cohort
    Then at least 5 organizations are on Starter or Pro
    And each has completed at least one successful billed transaction
```

### Phase 3 DoD (additive)
Production runbooks and incident process documented; rollback tested; backups automated with a verified restore drill; status page live; launch checklist signed off by Product + Eng leads.

---

## Phase 4 — Scale & Differentiation (Months 6–12)

### Scope
Build the moat: customer fine-tuning pipeline, local-language support, light workflow automation, and the packaged self-hosting product.

### Epics
E16 Fine-Tuning Pipeline · E17 Local Language Support · E18 Workflow Automation · E19 Self-Hosting Distribution · E20 Projects (proposed, not yet confirmed).

### Dependencies introduced
ML: transformers, peft, trl, accelerate, datasets, MLflow; GPU inference via vLLM. Workflows: APScheduler/Celery beat, webhook framework. Distribution: Docker Compose bundle, Helm chart (optional), license-key service.

### E16 — Fine-Tuning Pipeline (M)

```gherkin
Feature: Customer fine-tuning with LoRA
  Customers adapt models to their domain data.

  Scenario: Upload data and launch a fine-tune
    Given a Pro or Enterprise organization
    When it uploads a validated training dataset
    And starts a LoRA fine-tuning job
    Then the job is tracked with a status and progress
    And on success a versioned adapter is registered for that organization only

  Scenario: Deploy and roll back a fine-tuned model
    Given a completed fine-tuned adapter version
    When the org selects it for a conversation
    Then inference uses the adapter
    And the org can roll back to a previous version at any time

  Scenario: Data isolation for training artifacts
    Given two organizations have fine-tuned models
    Then neither can access, list, or infer with the other's adapters
```

### E17 — Local Language Support (M)

```gherkin
Feature: Local language support
  Users operate in Yoruba, Hausa, Igbo, and Swahili.

  Scenario: Translation layer round-trip
    Given a user writes a prompt in Yoruba
    When the message is processed
    Then it is translated for the model as needed
    And the response is returned to the user in Yoruba

  Scenario: Localized UI
    Given a user selects Hausa as their interface language
    Then navigation, buttons, and system messages render in Hausa
    And unsupported strings fall back to English without breaking layout
```

### E18 — Workflow Automation (S)

```gherkin
Feature: Light workflow automation
  Events trigger AI actions and route outputs.

  Scenario: Trigger on Slack message
    Given a workflow is configured to run on messages in a Slack channel
    When a matching message arrives
    Then the configured model action executes
    And the output is delivered to the configured destination (Sheet, Slack, or email)

  Scenario: Scheduled job
    Given a workflow scheduled to run daily at a set time
    When the scheduled time is reached
    Then the job runs once
    And a failure is retried and surfaced in the run history
```

### E19 — Self-Hosting Distribution (M)

```gherkin
Feature: One-command self-hosted deployment
  Enterprises run Afridock on their own infrastructure.

  Scenario: One-command install
    Given a supported Linux host with Docker
    When an operator runs the documented single install command
    Then the full stack starts and passes its health checks
    And the operator can create the first Admin account

  Scenario: License validation
    Given a self-hosted deployment with a license key
    When the key is valid
    Then licensed features are enabled
    And an invalid or expired key disables licensed features with a clear message

  Scenario: Offline operation
    Given a self-hosted deployment using a cached local model
    When the host has no internet access
    Then chat and core features continue to function
```

### E20 — Projects (C) — proposed, not yet confirmed

Surfaced by a design mockup (a top-level "Projects" nav item grouping conversations, each with its own members/default model/status) that predates this epic being added to the plan. Logged here per the project's decisions log (see progress.md, 2026-07-21 "Projects depth" decision) so it isn't lost, but scope, priority, and whether it ships at all are unconfirmed — treat the MoSCoW tag and scenario below as a starting proposal, not a commitment. `apps/web` currently ships only a nav placeholder for this (no schema, no real functionality).

```gherkin
Feature: Project-scoped conversation grouping
  Users organize conversations under a shared project rather than a flat list.

  Scenario: Create a project and scope conversations to it
    Given an organization member with permission to create projects
    When they create a project with a name and a default model
    Then the project appears in the Projects list
    And new conversations can be started within that project

  Scenario: Project-level membership is independent of org role
    Given a project with a defined set of members
    When a user who belongs to the organization but not the project opens it
    Then they cannot view the project's conversations
    And an organization Admin can add or remove project members at any time
```

If confirmed, this epic needs its own schema design pass (a `projects` table, a `project_id` FK on `conversations`, and a `project_members` table for the project-level permission layer) before implementation — see the "Projects depth" decision in progress.md for why that was deferred rather than built alongside the Phase 1 conversation schema.

### Phase 4 DoD (additive)
Fine-tuning artifacts isolated and encrypted at rest; local-language quality validated with native-speaker review sign-off; self-host bundle versioned and reproducible from a tagged release; upgrade/migration path documented and tested between two releases. E20 (if confirmed): project-level membership isolation verified by an automated cross-project access test, mirroring the org-level tenant-isolation test from Phase 1.

---

## 5. Cross-Phase Concerns

### 5.1 Testing Strategy
A test pyramid: fast unit tests (pytest, Vitest) at the base; contract/integration tests for provider adapters, webhooks, and billing using recorded fixtures and sandbox credentials; BDD acceptance tests (pytest-bdd + Playwright) executing the Gherkin in this document as living specs; and a thin layer of E2E smoke tests against staging. Provider and payment integrations use sandbox/mock modes in CI and are exercised against real sandboxes nightly.

### 5.2 Observability & SLOs
Target SLOs: API availability 99.0% (MVP) rising to 99.5%; p95 time-to-first-token < 2s on the default model; webhook processing success > 99%. Every request carries a trace id; cost and token metrics are first-class. Alerts page the NG-timezone on-call.

### 5.3 Security & Compliance
Multi-tenant isolation via Postgres row-level security and org-scoped auth; secrets in a managed vault; TLS everywhere via Cloudflare; PII minimization and redaction in logs. Monitor evolving Nigerian data-protection (NDPR) and fintech requirements; keep audit trails exportable for customer compliance needs.

### 5.4 Environments & Branching
Environments: local (Compose) → staging (af-south-1) → production (af-south-1). Trunk-based development, PR-gated by the Global DoD, automated deploy to staging on merge, manual promotion to production with change log and rollback plan.

### 5.5 Risk Register (engineering view)
Open-source model quality shortfall — mitigate with fine-tuning and commercial fallback; connectivity constraints — mitigate with offline-first design and local caching; payment-provider variability — mitigate with multi-provider abstraction and idempotent webhooks; multi-tenant data leakage — mitigate with RLS plus automated cross-tenant tests in CI.

---

## 6. Milestones & Metrics

| Milestone | Target week | Engineering signal |
|---|---|---|
| Foundations ready | 4 | CI green, staging live, validation signed off |
| Core chat usable | 12 | E1–E4 scenarios pass; TTFT < 2s |
| Governance + billing | 16 | E5–E10 pass; billing reconciles; webhooks idempotent |
| Beta launch | 20 | E11–E15 pass; security audit cleared; 5+ paying orgs |
| Differentiation GA | Month 12 | Fine-tuning, local languages, self-host GA; $20K+ MRR |

Product/business KPIs (from the brief) ride alongside: 50+ signups and 5+ paying customers by month 6; $10–20K MRR, 30+ paid customers, NPS > 40, churn < 5% by month 12; expansion readiness to Ghana/Kenya.

---

## 7. Immediate Next Steps (Week 1)

Align the team on this plan and confirm buy-in; assign the discovery interview lead and open the tracking sheet; provision the af-south-1 accounts and create the monorepo with the CI/CD skeleton; lock exact dependency versions into `poetry.lock` and `package-lock.json`; and schedule the Week-4 validation review as the Phase 0 exit gate.
