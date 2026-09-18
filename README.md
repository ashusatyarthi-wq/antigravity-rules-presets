<div align="center">

# 🛡️ Antigravity Agent Configuration Presets

**Production-hardened, battle-tested `GEMINI.md` and `AGENTS.md` rules presets for Google Antigravity to prevent agent hallucination loops, runaway scraper crashes, silent auth leaks, and broken builds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity Compatible](https://img.shields.io/badge/Antigravity-2.0%2B-blue.svg)](https://deepmind.google/technologies/gemini/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-%E2%99%A5-pink.svg)](https://github.com/sponsors/ashusatyarthi-wq)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 🎯 What Problem This Solves

Out of the box, agentic coding assistants generate code that works in happy-path prototypes but routinely triggers catastrophic production failures:
- Leaking `SUPABASE_SERVICE_ROLE_KEY` inside Next.js `'use client'` bundles.
- Spawning a fresh 400MB Chromium instance on every HTTP request until Linux Out-Of-Memory (OOM) kills the Node server.
- Breaking React Native mobile builds by running unpinned `npm install` instead of `npx expo install`.
- Getting permanent IP bans by blasting target endpoints with naive flat retries on HTTP 429.

This repository provides **drop-in configuration presets (`GEMINI.md`)** that constrain the agent to senior-level architectural patterns, automated review checkpoints, and anti-fragile failure handling.

---

## 📦 Available Presets

| Stack Preset | Primary Focus | Anti-Pattern Prevented | Files |
|---|---|---|---|
| **[Next.js + Supabase](./presets/nextjs-supabase/)** | App Router SSR, `@supabase/ssr`, RLS policies, cookie auth lifecycle | Secret leakage in client bundle, spoofed cookie auth, hydration mismatch | [Rules](./presets/nextjs-supabase/GEMINI.md) • [Why](./presets/nextjs-supabase/WHY.md) • [Diff](./presets/nextjs-supabase/before-after.md) |
| **[Express + Playwright Scraping](./presets/express-playwright-scraping/)** | Anti-bot evasion, selector drift tolerance, browser pooling, memory caps | OOM server crashes, zombie Chrome processes, brittle XPath breakages | [Rules](./presets/express-playwright-scraping/GEMINI.md) • [Why](./presets/express-playwright-scraping/WHY.md) • [Proof](./presets/express-playwright-scraping/verification-proof.md) |
| **[React Native + Expo](./presets/react-native-expo/)** | Cross-platform splits, native SDK alignment, Metro cache, async storage | Flash of unauthenticated content (FOUC), JS bridge animation stutter, native symbol crashes | [Rules](./presets/react-native-expo/GEMINI.md) • [Why](./presets/react-native-expo/WHY.md) • [Diff](./presets/react-native-expo/before-after.md) |
| **[FastAPI + PostgreSQL](./presets/fastapi-postgresql/)** | Async SQLAlchemy 2.0, Alembic migrations, connection pooling, Pydantic v2 DTOs | MissingGreenlet exceptions, leaked transaction locks, event-loop blocking, password leaks | [Rules](./presets/fastapi-postgresql/GEMINI.md) • [Why](./presets/fastapi-postgresql/WHY.md) • [Diff](./presets/fastapi-postgresql/before-after.md) |
| **[Go (Gin/Fiber) + HTMX](./presets/go-gin-htmx/)** | Context propagation, `database/sql` pool caps, dual-mode `HX-Request` rendering | Leaked goroutines, database socket exhaustion, page-in-a-page HTML corruptions | [Rules](./presets/go-gin-htmx/GEMINI.md) • [Why](./presets/go-gin-htmx/WHY.md) • [Diff](./presets/go-gin-htmx/before-after.md) |
| **[LangGraph + LangChain](./presets/langchain-langgraph-agent/)** | Multi-agent state machines, recursion caps, strict Pydantic v2 schemas, token budgets | Runaway token spend loops, schema hallucination, unhandled tool crashes | [Rules](./presets/langchain-langgraph-agent/GEMINI.md) • [Why](./presets/langchain-langgraph-agent/WHY.md) • [Diff](./presets/langchain-langgraph-agent/before-after.md) |
| **[Solana + Anchor (Rust)](./presets/solana-anchor-rust/)** | Canonical PDA derivation, unchecked math bans, compute unit budgeting, CPI auth | Silent balance underflow/overflow, spoofed CPI programs, 200k CU exhaustion | [Rules](./presets/solana-anchor-rust/GEMINI.md) • [Why](./presets/solana-anchor-rust/WHY.md) • [Diff](./presets/solana-anchor-rust/before-after.md) |

---

## 🚀 1-Command Installation

You can install any preset directly into your repository with one command:

```bash
# Clone and install preset into your current directory
python install.py <preset-name>

# Example:
python install.py nextjs-supabase
# => Installed 'nextjs-supabase' rules to .gemini/GEMINI.md
```

### Manual Installation
Copy the desired stack's `GEMINI.md` into `.gemini/` or root:

```bash
# Example: Using the Next.js + Supabase preset
curl -sSL https://raw.githubusercontent.com/ashusatyarthi-wq/antigravity-rules-presets/main/presets/nextjs-supabase/GEMINI.md -o .gemini/GEMINI.md
```

### Option 2: Scoped Customizations (`.agents/rules/`)
If your repository is a monorepo, place the rules into your targeted package directory or workspace `.agents/` folder:

```bash
mkdir -p apps/web/.agents/rules
cp presets/nextjs-supabase/GEMINI.md apps/web/.agents/rules/supabase-rules.md
```

Antigravity automatically discovers and hierarchically loads all rules walking up from the edited file to the workspace root.

---

## 🔬 Proof of Work & Verification

Our presets are not theoretical guidelines—they are verified against live targets. 

See the **[Express + Playwright Live Verification Report](./presets/express-playwright-scraping/verification-proof.md)** for execution metrics against a public HTTP test target (`httpbin.org`), proving:
- Multi-attempt exponential backoff with full randomized jitter on HTTP 429 rate limits.
- Anti-bot `sec-ch-ua` and browser fingerprint handshakes.
- Bounded socket timeouts with guaranteed resource reclamation.

---

## ⚖️ Architectural Decision Flags (Contested Choices)

We believe in transparency over dogma. When using these presets, note these opinionated trade-offs:

1. **Next.js Server Actions vs Route Handlers**:
   - *Preset Choice*: Prefers Server Actions with Zod schemas.
   - *Alternative View*: Some teams prefer standard REST Route Handlers for clearer OpenAPI doc generation and third-party webhook consumption.
2. **Playwright Locator Strategy**:
   - *Preset Choice*: Tier 1 requires `data-testid`.
   - *Alternative View*: Accessibility-first advocates argue `getByRole` should be Tier 1 to guarantee accessible DOM structures.
3. **Browser Instance Pooling**:
   - *Preset Choice*: Singleton browser with ephemeral `BrowserContext` instances and periodic 100-cycle worker recycling.
   - *Alternative View*: In zero-trust environments, isolated ephemeral worker threads or serverless browser APIs (e.g. Browserless.io) may be preferred.

---

## 🤝 Contributing

We welcome presets for additional stacks! Wanted presets include:
- `FastAPI + PostgreSQL (SQLAlchemy / Alembic)`
- `Django + Celery + Redis`
- `SvelteKit + Cloudflare Workers`
- `Go (Gin / Fiber) + HTMX`

### How to Submit:
1. Fork the repo and create a new folder under `presets/<stack-name>/`.
2. Provide:
   - `GEMINI.md`: Hardened rules and constraints.
   - `WHY.md`: Detailed failure modes prevented.
   - `before-after.md`: Concrete naive vs hardened code diff.
3. Open a Pull Request following our review checklist.

---

## 📄 License & Sponsorship

- Licensed under the **[MIT License](./LICENSE)**.
- If these presets save your team hours of debugging agent loops, consider supporting ongoing maintenance via **[GitHub Sponsors](https://github.com/sponsors/ashusatyarthi-wq)**.
