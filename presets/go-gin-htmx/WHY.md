# Rationale: Go (Gin / Fiber) + HTMX Preset

This document explains **why** each rule in `GEMINI.md` exists and the specific deadlocks, memory leaks, and UI rendering bugs it prevents in full-stack Go applications.

---

### 1. The Context Propagation & Unbounded Goroutine Mandate
- **Failure Prevented: Orphaned Database Queries & Goroutine Leaks**
- **The Problem**: In Go, when a client closes their browser tab or navigates away mid-request, the HTTP server closes the request connection. If an agent calls `db.QueryContext(context.Background(), ...)` or launches `go func() { doExpensiveWork() }()`, that database query and goroutine keep executing on the server until completion, consuming CPU, database read locks, and memory for a response that will never be received.
- **The Hardened Fix**: Always propagating `c.Request.Context()`. When the client disconnects, `ctx.Done()` fires instantly, canceling the database query at the socket level and stopping wasted CPU cycles.

---

### 2. Mandatory `rows.Close()` and `rows.Err()` Verification
- **Failure Prevented: Silent Database Pool Exhaustion & Truncated Datasets**
- **The Problem**: If an agent runs a `rows.Next()` loop but encounters a `return err` before the loop naturally finishes, failing to `defer rows.Close()` locks that database connection out of the pool. Over time, the pool runs out of connections and the app hangs completely. Additionally, if the network drops midway through reading 10,000 rows, `rows.Next()` simply returns `false`—without checking `rows.Err()`, the application assumes it fetched the complete dataset when it actually truncated silently.
- **The Hardened Fix**: Mandatory immediate `defer rows.Close()` and checking `if err := rows.Err(); err != nil`.

---

### 3. Dual-Mode `HX-Request` Rendering
- **Failure Prevented: Nested HTML Shell Duplication (Page-in-a-Page)**
- **The Problem**: When an HTMX `hx-get="/todos"` swaps a table body, it expects *only* the `<tr>...</tr>` fragments. If an agent renders the standard template that includes `<!DOCTYPE html><html><nav>...`, HTMX inserts an entire secondary web page into the table body, destroying the layout. Conversely, if a user refreshes or bookmarks `/todos`, they must receive the full page shell with navigation.
- **The Hardened Fix**: Detecting `c.GetHeader("HX-Request") == "true"`. If true, return the fragment; if false, return the full wrapped page.

---

### 4. Setting Explicit `SetMaxOpenConns` and `SetMaxIdleConns`
- **Failure Prevented: PostgreSQL `Too Many Clients` Crash**
- **The Problem**: By default, Go's `database/sql` driver has **no limit** on the number of open connections (`maxOpenConns = 0` is unlimited). Under a burst of 500 concurrent requests, Go opens 500 separate TCP connections to PostgreSQL, which by default caps connections at 100 (`max_connections = 100`). Postgres immediately rejects all connections, taking down the entire application.
- **The Hardened Fix**: Capping `SetMaxOpenConns` to match PostgreSQL pool capacity and tuning idle connections to avoid cold socket renegotiation penalties.
