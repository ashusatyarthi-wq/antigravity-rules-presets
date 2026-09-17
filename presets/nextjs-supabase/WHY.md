# Rationale: Next.js + Supabase Hardened Preset

This document details **why** each rule in `GEMINI.md` exists and the exact catastrophic failures or developer headaches it prevents.

---

### 1. The `supabase.auth.getUser()` vs `getSession()` Mandate
- **Failure Prevented: Authentication Bypass & Spoofed Claims**
- **The Problem**: In Next.js Server Components, naive AI agents frequently call `const { data: { session } } = await supabase.auth.getSession()`. However, `getSession()` simply reads and decodes the raw JWT from the browser cookie without validating its cryptographic signature against Supabase's auth server. An attacker can craft a tampered cookie with an elevated `user_id` or `role`, bypassing server checks.
- **The Hardened Fix**: Requiring `supabase.auth.getUser()`. This makes an authenticating round-trip to validate the JWT against the Supabase Auth server, guaranteeing that the caller is genuine and not a spoofed cookie.

---

### 2. Triple-Client Architecture (`@supabase/ssr`)
- **Failure Prevented: Cookie Mutation Runtime Exceptions & Silent Session Drop**
- **The Problem**: In Next.js App Router, Server Components render in a read-only stream where calling `cookies().set(...)` throws a fatal Next.js runtime error (`Cookies can only be modified in a Server Action or Route Handler`). Naive agents attempt to use a single universal client utility that tries to refresh cookies everywhere, breaking server renders.
- **The Hardened Fix**: Segregating clients into:
  1. Read-only client for Server Components.
  2. Read/Write cookie client for Server Actions & Route Handlers.
  3. Middleware client that refreshes expired tokens *before* downstream rendering begins.

---

### 3. Server Component Quarantine & Secret Leak Prevention
- **Failure Prevented: Service Role Key Leakage in Client Bundles**
- **The Problem**: AI agents writing Next.js code frequently move Supabase query logic into shared helper files. If a helper file containing the `SUPABASE_SERVICE_ROLE_KEY` is accidentally imported by a component marked with `'use client'`, Next.js either strips the variable (causing silent null queries) or leaks admin privileges to the browser bundle if bundled insecurely.
- **The Hardened Fix**: Strict leaf-level quarantine of `'use client'` directives and mandatory prohibition of service-role keys in any client-imported module.

---

### 4. Exponential Backoff with Jitter vs Naive Flat Loops
- **Failure Prevented: Thundering Herd & Postgres Connection Starvation**
- **The Problem**: When Supabase free/Pro tier hits connection pool limits (e.g., PgBouncer pool exhaustion or burst rate limits), naive agent code loops with `while (retries < 5) { await sleep(1000); }`. When 20 concurrent requests fail simultaneously, they all retry at exactly the 1-second mark, causing a secondary collapse ("thundering herd").
- **The Hardened Fix**: Truncated exponential backoff with full randomized jitter (`Math.random() * backoff`). This decorrelates retries and allows the database connection pool to recover gracefully.

---

### 5. Mandatory Approval for Migrations & RLS Policies
- **Failure Prevented: Accidental Data Wipes and Data Leaks**
- **The Problem**: Autonomous coding agents given database access will frequently run `DROP TABLE` or generate migrations that omit Row-Level Security policies to "make the tests pass quickly", inadvertently exposing all tenant data publicly.
- **The Hardened Fix**: Schema modifications and security policies are classified as blocking review artifacts requiring explicit human sign-off before execution.
