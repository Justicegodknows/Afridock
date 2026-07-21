# Afridock — Progress Tracker

> **Every AI agent MUST read this file before writing any code**, and MUST update it after completing meaningful work (feature, epic story, migration, infra change). This is the single source of truth for what exists, what is in flight, and what comes next. The execution plan ([Afridock_Implementation_Execution_Plan.md](Afridock_Implementation_Execution_Plan.md)) defines *what to build*; this file records *what has been built*.
>
> **This is enforced mechanically, not just by convention** — see "Enforcement" below.

## Enforcement

Three deterministic checks back this policy; none rely on an agent choosing to comply:

1. **Claude Code hook** (`.claude/settings.json` + `.claude/hooks/`): a `PreToolUse` hook blocks any `Write`/`Edit` under `apps/`, `packages/`, or `infra/` in a session until a `PostToolUse` hook has recorded that `progress.md` was read in that same session. Enforces "read before writing any code" for AI agents using Claude Code specifically.
2. **Git pre-commit hook** (`.githooks/pre-commit`, activated via `git config core.hooksPath .githooks` — run once per clone, e.g. `make hooks-install`): blocks any commit that stages changes under `apps/`, `packages/`, or `infra/` unless `progress.md` is staged in the same commit. Enforces "update after completing work" for any committer (human or agent), regardless of tool. Escape hatch: `git commit --no-verify` for changes that genuinely don't warrant a progress.md update.
3. **CI check** (`.github/workflows/ci.yml`, job `progress-tracker`): re-runs the same check against the PR diff. Catches the case where hooks aren't installed locally or `--no-verify` was used — nothing merges without it passing.

## Current status

**Phase: 0 — Validation & Foundations (complete) → Phase 1 — Core MVP: Chat & Inference (scaffolding in progress)**

Last updated: 2026-07-21

## Completed

### Phase 0 — Validation & Foundations
- [x] Monorepo scaffolding: `apps/api` (FastAPI), `apps/web` (React + Vite), `packages/shared`, `infra/terraform`
- [x] Docker Compose stack (Postgres + pgvector, Redis, API, web) via `make dev`
- [x] FastAPI skeleton: `/healthz` endpoint, structured logging, config, async SQLAlchemy session setup, Alembic wiring (no migrations yet)
- [x] Backend test harness: pytest + pytest-bdd (health feature/steps)
- [x] Frontend shell: React app, Tailwind, Vitest + Testing Library setup
- [x] Makefile targets: `dev`, `down`, `test`, `lint`, `fmt`, `migrate`
- [x] Terraform skeleton in `infra/terraform` (af-south-1)

### Pre-Phase-1 groundwork — patterns adapted from Dify (langgenius/dify)
Reference architecture research (4 parallel agents against a shallow clone) + implementation, feeding E2–E5. **Not** full epic completion — see caveats below each item.

- [x] **Inference abstraction** (`apps/api/src/afridock_api/inference/`): `ModelProfileRegistry` (static YAML registry, `profiles.yaml`) mapping plan model names → LiteLLM model strings; `FallbackChain` + cooldown-based failover (mirrors Dify's `LBModelManager`); `InferenceClient` wrapping `litellm.acompletion`/streaming with normalized `InferenceError` hierarchy; Fernet-based credential encryption (`credentials.py`). Unit-tested (profiles/fallback/credentials), no live provider calls made. *Missing for E2: no FastAPI endpoint wires this up yet; no real HF/vLLM credentials configured.*
- [x] **Chat DB schema** (`apps/api/src/afridock_api/db/models/{conversation,message,provider}.py` + hand-written migration `alembic/versions/0001_conversations_messages_providers.py`): one row per turn (departs from Dify's query/answer-pair rows) with per-message model attribution, Postgres RLS policies on `org_id`, real `tsvector`/pgvector `Vector(1536)` columns + HNSW/GIN indexes, `provider_credentials`/`model_profile_overrides`/`inference_usage_logs` tables. Verified: tables register on `Base.metadata`, migration is the sole Alembic head, ruff/black/mypy/pytest all pass. *Missing for E4/E1: never run against a live Postgres (no Docker daemon in this environment); `org_id`/`user_id` have no FK constraint yet (organizations/users tables land with E1) — add those FKs in a follow-up migration.*
- [x] **Chat UI streaming + markdown** (`apps/web/src/{lib/sse.ts,hooks/useChatStream.ts,hooks/useAutoScroll.ts,components/chat/}`): `parseSSEStream` (fetch+ReadableStream line-buffered SSE parsing, ported from Dify's `handleStream`), Zustand+Immer `chatStore` (autoFreeze disabled, same reason as Dify), `MarkdownRenderer` wrapping `streamdown`/`@streamdown/code` (Dify's actual markdown stack — handles incomplete markdown mid-stream natively, no custom balancing logic needed), `MessageList`/`MessageItem` (memoized)/`ChatPanel`/`ChatInput`/`StopButton`. Build/lint/test all pass; unit tests cover SSE chunk-boundary recovery and store token-append isolation. *Missing for E3: `useChatStream` POSTs to `/conversations/:id/messages`, which doesn't exist on the backend yet — this is forward-looking scaffolding, same status as the original `/healthz`-only frontend.*
- [x] **Admin dashboard: members/RBAC** (`apps/web/src/{lib/permissions.ts,store/authStore.ts,hooks/useHasCapability.ts,services/members.ts,components/members/}`): flat `Role → Capability[]` map (simpler than Dify's granular permission-key RBAC, appropriate since the plan only needs Admin/User/Viewer), `MembersTable`/`InviteMemberDialog` (Radix Dialog/AlertDialog)/`RoleBadge`/`WorkspaceSwitcher`. Build/lint/test all pass; unit tests cover capability resolution. Routing superseded by the design-unification pass below (moved from `/settings/*` to a top-level `/team` route). *Missing for E5: `role` is a hardcoded Zustand placeholder (`store/authStore.ts`) pending real auth; `services/members.ts` calls `/organizations/current/members*` endpoints that don't exist on the backend yet.*

New dependencies: backend — `pgvector`, `cryptography`, `pyyaml` (added to `pyproject.toml`); frontend — `streamdown`, `@streamdown/code`, `immer`, `@radix-ui/react-dialog`, `@radix-ui/react-alert-dialog`, `clsx`, `tailwind-merge`, `@hookform/resolvers` (added to `package.json`).

### Design unification — reconciled Dify-adapted `apps/web` with the design mockup
The user supplied a fully-worked visual prototype ("AfricaAI Platform (standalone).html", a Figma-Make-style bundle export — not real source code) with a "Classical" editorial theme and a 10-item nav that independently converged on almost the same epic breakdown as the plan. Reconciled per explicit user decisions (asked via AskUserQuestion since guessing wrong meant real rework): adopt the mockup's visual design via a *swappable token layer* rather than either discarding it or hardcoding it; build the *full nav shell now* with phase-gated placeholder pages for anything not yet in scope; treat *"Projects"* (a mockup nav item with no epic in the plan) as a nav placeholder only, its real data model deferred to Phase 4 as new epic **E20** (see the plan and the decision below); leave *out-of-phase UI* (the mockup's offline-queue banner and language picker in the chat screen — Phase 3/4 features) out of the Phase-1 chat screen entirely.

- [x] **Design-token layer** (`apps/web/src/styles/theme.css`, `tailwind.config.js`, `hooks/useTheme.ts`): CSS custom properties for the Classical theme (Cormorant Garamond/Lora fonts, cream/gold palette) as the default `:root`, with a `:root[data-theme="dark"]` override repurposing the original dark slate/emerald palette onto the same token names — proven swappable via a working sidebar toggle (`useTheme`, localStorage-backed, guards `localStorage` access since it throws in some test/private-browsing contexts), not just plumbed. Verified via Playwright: computed styles and cropped-element screenshots confirm both themes render correctly (a full-page screenshot's compression initially made dark-mode nav text look wrongly low-contrast — checked via `getComputedStyle` and an element-level screenshot before concluding it wasn't a bug).
- [x] **AppShell + Sidebar** (`apps/web/src/components/layout/{AppShell,Sidebar,PageHeader,PageContainer,ApiStatusIndicator}.tsx`): single persistent sidebar (replacing the old nested `SettingsLayout`) with all 10 mockup nav items — Assistant, Conversations, Projects, Workflows, Usage & Cost, Audit Log, Team & Roles, Integrations, Billing, Resilience — grouped into Workspace/Automation/Insights/Administration sections. A `PAGE_META` lookup derives each page's kicker/title for one shared header. The old `/healthz` check moved from the chat header into a small sidebar-footer `ApiStatusIndicator`.
- [x] **Route restructure** (`apps/web/src/routes/router.tsx`): `/chat` (Assistant, model picker + re-themed chat components), `/conversations` (new real-ish list page + `services/conversations.ts`), `/team` (Members functionality + 3 role-explainer cards + an API-Keys tab, replacing the old `/settings/members` + `/settings/api-keys`), `/workspace` (renamed from `/settings/organization`, now reachable only via the sidebar's WorkspaceSwitcher, matching the mockup's lack of a dedicated nav item for it), and 6 simple `PlaceholderPage` routes (`/projects`, `/workflows`, `/usage`, `/audit`, `/integrations`, `/billing`) each citing its plan epic and phase. Old `/settings/*` directory deleted.
- [x] **Model picker** (`apps/web/src/components/chat/ModelPicker.tsx`, `lib/models.ts`, `store/chatStore.ts`'s new `selectedModelProfile`): backs plan E2's "model switching at conversation level" directly in the chat UI — clicking a model chip changes which model the *next* message uses; already-sent messages keep their own `modelProfile` regardless of later switches.
- [x] Re-themed every existing chat/members/dialog component to the new tokens; fixed a real bug found via visual testing: `Button` wasn't using `forwardRef`, so Radix's `asChild` (`DialogTrigger`, `AlertDialogCancel`) couldn't attach its ref, throwing a console warning — fixed by wrapping `Button` in `React.forwardRef`.

Build/lint/9 tests all still pass. Visually verified end-to-end with a Playwright driver script (no project run-skill existed yet) against the dev server: chat, team, conversations, billing placeholder, invite dialog, and the dark-mode toggle all render and function correctly.

## In progress

_(nothing — claim work here before starting it)_

| Epic / story | Owner (agent/session) | Started | Notes |
|---|---|---|---|

## Next up (Phase 1, in priority order — see plan §Phase 1)

- [ ] **E1 — Authentication & Organizations (M)**: fastapi-users + Authlib, org/user models (unblocks the `org_id`/`user_id` FKs deferred above), Postgres RLS session variable (`app.org_id`) set per-request in FastAPI middleware, first real Alembic migration on top of `0001_conversations_messages_providers`
- [ ] **E2 — Inference Orchestrator (M)**: wire `inference/` (done above) into a real FastAPI endpoint; configure real HF/vLLM credentials; persist `InferenceResult` to `inference_usage_logs` + `messages`
- [ ] **E3 — Chat UI & Streaming (M)**: build the `/conversations/:id/messages` SSE endpoint `useChatStream` (done above) already expects; wire real conversation IDs instead of the `"demo"` placeholder in `ChatPage`; wire `/conversations` (`services/conversations.ts`) to a real list endpoint
- [ ] **E4 — Conversation History & Search (S)**: run migration `0001` against a live Postgres; verify the `search_tsv` trigger and HNSW index actually work; pick and wire a real embedding model for `messages.embedding`

Later phases (do not start before Phase 1 (M) items are done): Phase 2 E5–E10 (RBAC/API keys, audit, Slack, WhatsApp, Sheets, billing — note `apps/web`'s members/RBAC UI scaffolding above gets a head start on E5), Phase 3 E11–E15 (offline queue, caching, PWA, security, launch), Phase 4 E16–E19, Phase 4 E20 Projects (proposed — see plan, not yet confirmed).

## Decisions & deviations log

Record any decision that deviates from or refines the execution plan.

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-21 | Created progress.md as mandatory pre-coding checkpoint for all agents | Keep multi-agent/multi-session work coordinated against the phased plan |
| 2026-07-21 | Backed the progress.md policy with a Claude Code hook, a git pre-commit hook, and a CI check (see "Enforcement" above) | A prose instruction in CLAUDE.md is not deterministic — an agent can forget or skip it; mechanical checks at the tool, commit, and PR layers can't be silently ignored |
| 2026-07-21 | Researched langgenius/dify (shallow clone, 4 parallel research agents, spot-checked against the actual repo) and adapted 4 patterns rather than designing from scratch: chat streaming/markdown, admin RBAC dashboard, LLM-provider abstraction, conversation/message schema | Avoid reinventing solved problems; Dify is a mature, similar-domain (multi-provider LLM platform) open-source reference |
| 2026-07-21 | Departed from Dify's schema: one row per turn (not query/answer pairs) with per-message model attribution, `org_id`-scoped Postgres RLS (Dify isolates only at the app layer), real `tsvector`/pgvector columns (Dify has neither on chat tables) | Plan requires hard multi-tenant isolation at the data layer and mid-conversation model switching with attribution preserved — Dify's shape doesn't give us either directly |
| 2026-07-21 | Kept only a thin abstraction over LiteLLM (`ModelProfileRegistry` + `FallbackChain` + `InferenceClient`) rather than Dify's full plugin-daemon/manifest provider system | LiteLLM already normalizes provider SDKs the way Dify's extracted `graphon` package does; the plugin-daemon exists to let third parties ship out-of-process providers, which is out of scope for the plan |
| 2026-07-21 | Used real React Router routes (originally under `/settings/*`, later flattened to top-level — see below) instead of Dify's single account-setting modal; flat `Role → Capability[]` map instead of Dify's granular permission-key RBAC | Deep-linkable routes are more idiomatic outside Next.js; the plan only needs 3 fixed roles (Admin/User/Viewer), so Dify's indirection for arbitrary custom roles is unneeded complexity |
| 2026-07-21 | Adopted the user-supplied design mockup's Classical editorial visual theme (not the original dark slate/emerald palette) as the default, via a swappable CSS-variable token layer with both a light (default) and dark override | User's explicit choice ("support both via a token layer") after being asked; the mockup was a fully-worked design, not a placeholder, and the plan itself doesn't mandate a specific visual language |
| 2026-07-21 | Built the full 10-item nav shell from the mockup now, with simple phase-gated `PlaceholderPage` placeholders (text notice + epic/phase citation, no fake data) for anything not yet in scope, rather than only showing in-phase nav items | User's explicit choice; matches the pattern already used for Billing/API Keys before this pass — avoids restructuring the sidebar repeatedly as each phase starts |
| 2026-07-21 | Flattened `/settings/*` (nested SettingsLayout with its own sub-nav) into top-level routes (`/team`, `/workspace`, `/billing`, etc.) under one AppShell sidebar; "API Keys" lives as an in-page tab on `/team` rather than its own nav item, since the mockup has none | The mockup has one sidebar, not a nested settings area with its own — Team & Roles, Integrations, and Billing are separate top-level items in it, not sub-tabs |
| 2026-07-21 | Deferred "Projects" (a mockup nav item/concept not in any epic) to a nav-only placeholder now; logged as candidate epic **E20** in the plan's Phase 4 (Could-have, unconfirmed), with its real data model (a `projects` table + project-level membership layer) explicitly deferred until confirmed | User's explicit choice ("make it a placeholder but document it... so it will not be forgotten"); a project-level membership layer is a real scaling/complexity cost (two-level RBAC) not worth taking on unscoped |

## Known issues / blockers

- Migration `0001_conversations_messages_providers` has never been run against a live Postgres in this environment (no Docker daemon available) — only validated via `Base.metadata` registration, `ast.parse`, and Alembic's offline revision discovery. Run `make migrate` for real before trusting it fully.
- `conversations.org_id`/`user_id` and `messages.org_id` have no FK constraint — add them once E1's organizations/users tables exist.
- Frontend chat (`useChatStream`), conversations (`services/conversations.ts`), and members (`services/members.ts`) hooks call backend endpoints (`/conversations/:id/messages`, `/conversations`, `/organizations/current/members*`) that don't exist yet — they'll 404 until E2/E3/E5 build them.
- `apps/web`'s current role (`store/authStore.ts`) is a hardcoded `"admin"` placeholder, not real auth — replace once E1 lands.
- No project run-skill exists yet for launching `apps/web`/`apps/api` — this session drove the dev server with an ad hoc Playwright script (see `/run` skill's guidance to capture this as a project skill via `/run-skill-generator` next time it's needed).
- The frontend build emits a "chunks larger than 500 kB" warning (mainly Shiki's per-language grammar chunks via `@streamdown/code`, lazy-loaded on demand) — non-blocking, not new debt from this session beyond a modest size increase, but worth code-splitting attention eventually.

## How to update this file

1. Before coding: read this file top to bottom; confirm your task matches the current phase and isn't already in progress.
2. Claim your task in **In progress** (epic/story, short note).
3. After finishing: move it to **Completed** (with checkbox), update **Next up**, log any decisions/deviations, and refresh the **Last updated** date.
4. Keep entries terse — one line per item; link to plan sections or files rather than duplicating detail.
