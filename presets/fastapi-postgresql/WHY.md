# Rationale: FastAPI + PostgreSQL (Async SQLAlchemy 2.0 & Alembic) Preset

This document explains **why** each rule in `GEMINI.md` exists and the specific production outages and concurrency bugs it prevents in asynchronous Python backends.

---

### 1. The `selectinload` / `joinedload` Eager Loading Mandate
- **Failure Prevented: `MissingGreenlet` Fatal Concurrency Crashes**
- **The Problem**: In synchronous SQLAlchemy, accessing an un-queried relationship (e.g. `user.orders`) triggers a lazy SQL query on the fly. In asynchronous SQLAlchemy (`asyncpg`), lazy-loading is strictly prohibited because Python coroutines cannot perform non-blocking I/O synchronously during property attribute access. When naive AI agents access relationships in response schemas without eager loading, SQLAlchemy throws:
  `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call a greenlet-only function...`
  This crashes the HTTP request at the serialization stage.
- **The Hardened Fix**: Mandatory explicit eager loading with `options(selectinload(Model.relation))` or `joinedload()`. All relational data required by the response schema is pre-fetched in a single asynchronous pass.

---

### 2. Context-Managed Session Injection with Auto-Rollback
- **Failure Prevented: Leaked Transactions & Stale Connection Starvation**
- **The Problem**: When an unhandled exception occurs inside a route handler, naive session handlers that don't wrap execution in `try...except...finally` leave open transactions active in the Postgres pool. Postgres holds table locks and connection slots open until client timeout. Under moderate traffic, the pool runs out of slots, returning:
  `asyncpg.exceptions.TooManyConnectionsError: sorry, too many clients already`
- **The Hardened Fix**: The `async with async_session_factory()` generator pattern. If any exception occurs during endpoint execution, `session.rollback()` is executed immediately, releasing transaction locks and returning the socket to the pool.

---

### 3. Separation of DTO Schemas from Database ORM Models
- **Failure Prevented: Password Hash Exposure & Mass Assignment Vulnerabilities**
- **The Problem**: Naive AI agents often create a single Pydantic schema for both inputs and outputs, or return the raw ORM model with `PydanticORM.from_orm(user)`. If the ORM model contains columns like `hashed_password`, `verification_token`, or internal audit flags, they are accidentally serialized into the public JSON response.
- **The Hardened Fix**: Strict separation into `UserCreate` (input), `UserUpdate` (patch), and `UserResponse` (strictly whitelisted public fields).

---

### 4. Mandatory Review for Alembic Autogenerate
- **Failure Prevented: Accidental Data Loss on Column/Index Renames**
- **The Problem**: Alembic's `--autogenerate` does not detect column renames—it generates a `op.drop_column()` followed by `op.add_column()`. If an agent executes this automatically without human approval, all existing production data in that column is permanently destroyed.
- **The Hardened Fix**: Alembic migrations are classified as high-risk review artifacts requiring human sign-off before being applied.
