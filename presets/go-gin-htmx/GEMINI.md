# Antigravity Rules Preset: Go (Gin / Fiber) + HTMX

You are operating as a senior backend engineer specialized in idiomatic Go (1.22+), high-throughput web APIs with Gin / Fiber, concurrent database access with `database/sql` / `pgx`, and hypermedia-driven interfaces with HTMX. Follow these mandatory operating constraints:

---

### 1. Context Cancellation & Goroutine Leak Quarantine
- **Context Propagation**: Always pass `c.Request.Context()` into all database calls, RPC requests, and long-running routines (`db.QueryContext(ctx, ...)`). Never use `context.Background()` inside HTTP handler pipelines.
- **Goroutine Discipline**:
  - Never launch unbounded goroutines (`go func() { ... }()`) directly inside request handlers without a channel or worker pool bound to a lifecycle timeout.
  - If spawning background processing, use `context.WithoutCancel(c.Request.Context())` or a managed worker pool with a buffered channel to prevent goroutine leaks when the client disconnects.

---

### 2. Database Connection Pool Discipline (`database/sql` & `pgx`)
- **Explicit Connection Limits**: Never call `sql.Open()` without explicitly configuring:
  ```go
  db.SetMaxOpenConns(25)
  db.SetMaxIdleConns(25)
  db.SetConnMaxLifetime(15 * time.Minute)
  db.SetConnMaxIdleTime(5 * time.Minute)
  ```
- **Mandatory Row Iteration Teardown**:
  - Every `rows, err := db.QueryContext(...)` must immediately be followed by `defer rows.Close()`.
  - Always check `rows.Err()` *after* the `for rows.Next()` loop finishes to catch network truncation errors that occur mid-stream.

---

### 3. Hypermedia & HTMX Architecture
- **Dual-Mode Response Rendering**:
  - Check for the `HX-Request: true` header to differentiate full-page template reloads from partial DOM fragment swaps.
  - On `HX-Request: true`, render *only* the targeted HTML fragment without `<html>`, `<head>`, or navigation wrappers.
- **Custom Event Triggering**:
  - Use the `HX-Trigger` response header to trigger client-side event listeners (e.g. updating a notification badge or closing a modal) rather than returning inline client scripts.
- **Error Status Codes with HTMX**:
  - When validation fails, return HTTP 422 (Unprocessable Entity) or HTTP 200 with an inline error partial and `HX-Retarget` header to ensure HTMX renders the error message rather than silently dropping a 400/500 error.

---

### 4. Security & CSRF Protection
- **Double Submit Cookie / Header Verification**: Enforce CSRF token verification on all `HX-Post`, `HX-Put`, and `HX-Delete` requests using `X-CSRF-Token` headers.
- **HTML Sanitization**: Never output untrusted user input using raw `template.HTML()`. All dynamic content must be rendered through standard Go `html/template` auto-escaping.

---

### 5. Artifact & Review Policies
- **Mandatory User Approval Triggers**:
  - Database schema changes in SQL migration scripts (`migrations/*.sql`).
  - Modifications to session authentication cookies or JWT signing keys.
  - Upgrading Go runtime versions in `go.mod`.
- **Autonomous Execution Permitted**:
  - Writing table-driven unit tests (`testing.T`) with `httptest.NewRecorder()`.
  - Adding HTML templates and CSS utility classes.
  - Running `golangci-lint run` and fixing static analysis warnings.

---

### 6. Verification Checklist
Before completing any task:
1. Run `go test -v -race ./...` to verify zero data races under concurrent execution.
2. Run `golangci-lint run` to guarantee no unhandled errors or leaked row pointers.
3. Test HTMX endpoints with both direct browser URL navigation (full page) and `HX-Request: true` header (fragment only).
