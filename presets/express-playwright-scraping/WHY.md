# Rationale: Express + Playwright Web Scraping Preset

This document explains **why** each rule in `GEMINI.md` exists and the specific production outages or failures it prevents in web scraping and browser automation workloads.

---

### 1. Browser Context Recycling vs Fresh Browser Spawning
- **Failure Prevented: OOM (Out of Memory) Node.js Process Crashes**
- **The Problem**: Naive AI agents write Express route handlers with `const browser = await chromium.launch();` inside `app.get('/scrape', ...)`. Under a modest load of 10 concurrent requests, spawning 10 full Chromium processes consumes over 4GB of RAM, immediately triggering the OS Out-Of-Memory (OOM) killer and crashing the entire server.
- **The Hardened Fix**: A singleton browser instance with ephemeral, lightweight `BrowserContext` allocations. Contexts are isolated in cookies and storage, take <50ms to spawn, use <10MB of memory, and are closed in `finally` blocks.

---

### 2. Multi-Tier Selector Strategy vs Absolute XPath
- **Failure Prevented: Silent Scraper Failure from Minor CSS Drift**
- **The Problem**: Websites constantly change their CSS class names (especially when modern web apps compile with CSS Modules or Styled Components, e.g. `.Button_btn__a8x9f` changing to `.Button_btn__b7c1e`). Naive agents hardcode brittle selectors or absolute XPath strings (`/html/body/div[3]/section/div[1]`). When the target site deploys a minor layout tweak, the scraper fails silently or throws timeout errors.
- **The Hardened Fix**: Tiered fallbacks:
  1. Data attributes / IDs
  2. Accessibility roles (`getByRole`, `getByLabel`)
  3. Structural text anchoring
  4. Parent-scoped hierarchy
  If Tier 1 changes, Tier 2 automatically captures the data, logs a telemetry warning, and prevents pipeline downtime.

---

### 3. Full Jitter Exponential Backoff on HTTP 429
- **Failure Prevented: IP Bans and Rate-Limit Cascades**
- **The Problem**: When target anti-bot systems (Cloudflare, Akamai, AWS WAF) detect high request frequencies, they respond with HTTP 429 (Too Many Requests). Naive agents either retry immediately in a loop or use fixed 1-second delays. This bursts traffic right back into the rate limit bucket, escalating the temporary 429 throttle into a permanent IP ban or CAPTCHA challenge.
- **The Hardened Fix**: Exponential backoff with full randomized jitter (`Math.random() * backoff`) and inspection of `Retry-After` headers. Retries are spread out unpredictably, allowing rate limit buckets to drain.

---

### 4. Bounded Timeouts and Mandatory `page.close()` in `finally`
- **Failure Prevented: Hanging Zombie Chrome Processes & Event Loop Freezes**
- **The Problem**: When a target site hangs, Playwright's default 30-second timeout leaves contexts open. If an error occurs midway through data extraction and the agent didn't wrap cleanup in `finally`, the page and context remain open in memory indefinitely, leaking Chrome renderers and file descriptors until the host runs out of socket handles.
- **The Hardened Fix**: Mandatory 15-second bounded navigation timeouts and guaranteed teardown in `finally` blocks.
