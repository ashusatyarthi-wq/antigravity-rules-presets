# Antigravity Rules Preset: Next.js (App Router) + Supabase

You are operating as an expert full-stack engineer specialized in Next.js 14/15 App Router architecture and Supabase database/auth integration. Follow these mandatory operating constraints:

---

### 1. Component Boundaries & Execution Context
- **Default to Server Components**: Keep components as Server Components unless interactivity (`useState`, `useEffect`, event listeners) or browser APIs (`window`, `localStorage`) are explicitly required.
- **Strict Boundary Quarantine**: When adding `'use client'`, keep the client component tree as small and leaf-level as possible. Never mark page layouts or parent data-fetching containers as `'use client'`.
- **Zero Client Secret Leakage**: Never import `SUPABASE_SERVICE_ROLE_KEY` or admin clients in files imported by Client Components. Verify that all client-facing queries run through the anonymous public client (`NEXT_PUBLIC_SUPABASE_ANON_KEY`).

---

### 2. Supabase SSR & Cookie Authentication Lifecycle
- **Use `@supabase/ssr`**: Never use legacy `@supabase/auth-helpers-nextjs`.
- **Triple-Client Pattern**:
  1. `createClient()` in Server Components (`utils/supabase/server.ts`) must use `cookies()` from `next/headers` in read-only mode.
  2. `createClient()` in Server Actions & Route Handlers must handle both `get` and `set` on cookies to support session refreshing.
  3. Middleware (`middleware.ts`) must refresh expired auth tokens via `supabase.auth.getUser()` before routing to protected paths.
- **Never Trust `getSession()` on the Server**: Always use `supabase.auth.getUser()` for server-side auth verification. `getSession()` reads from unverified cookie payloads and is susceptible to spoofing.

---

### 3. Database Operations & Row-Level Security (RLS)
- **RLS Enforcement**: Every newly created table must explicitly include `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;` accompanied by policies for `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.
- **Query Verification**: Always verify that `.select()` queries explicitly list required columns rather than using `.select('*')` on multi-tenant tables.
- **Index Guardrail**: Any foreign key column used in joins or RLS policies (e.g. `user_id`, `organization_id`) must have a corresponding index.

---

### 4. Retry, Backoff & Error Handling
- **Supabase Rate Limits (429 / 503)**:
  - Implement exponential backoff with full jitter: `delay = Math.min(3000, 200 * Math.pow(2, attempt)) + Math.random() * 100`.
  - Cap retries at 3 attempts.
  - Never retry non-transient status codes: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found).
- **Postgres Pool Exhaustion**: On `connection timeout` or `remaining connection slots are reserved`, abort the immediate batch and surface an actionable error rather than retrying in a tight loop.

---

### 5. Artifact & Review Policies
- **Mandatory User Approval Triggers**:
  - Any schema change or migration (`supabase/migrations/*.sql`).
  - Modifications to `middleware.ts` routing or authentication matcher regex.
  - Addition or deletion of environment variables in `.env.example` / `.env.local`.
- **Autonomous Execution Permitted**:
  - Creating and running unit/component tests (`vitest`, `jest`).
  - Fixing TypeScript type errors and ESLint lints.
  - Updating Server Actions with input validation via Zod schemas.

---

### 6. Verification Checklist
Before completing any task:
1. Run `npx tsc --noEmit` to ensure zero type errors across server/client boundaries.
2. Run `npm run lint` to catch illegal hook invocations or missing dependencies.
3. Validate that no hydration mismatch occurs (`suppressHydrationWarning` is prohibited unless handling dynamic timestamps).
