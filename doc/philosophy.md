# ⚡ Database-Centric Architecture: An Executive Summary

## The Premise

Most business apps are just structured data with CRUD operations. Yet we often bury them under ORMs, boilerplate APIs, and overengineered layers.

This manifesto proposes a **pragmatic, database-first stack**:

- **PostgreSQL** → the application’s computational core
- **PostgREST** → instant, zero-boilerplate API from the schema
- **NiceGUI (+ FastAPI)** → Python-native UI, with FastAPI as an escape hatch

The result: faster delivery, fewer moving parts, and stronger guarantees.

---

## Why It Works

### 1. Database = The Heart ❤️

- Schema is the single source of truth.
- Constraints, triggers, and functions enforce integrity at the deepest layer.
- Business logic runs next to the data for performance and reliability.

### 2. Zero-Boilerplate API 🚀

- CRUD endpoints generated automatically.
- Add a column → it’s in the API.
- Add a view → instant read-only endpoint.
- Devs focus on real business value, not plumbing.

### 3. Simplicity as Robustness ⚙️

- **Fewer layers** = less code, less overhead, less debugging.
- Database as backend: just a **stateless PostgREST** server.
- **Config-driven** validation through metadata **schema mapping** = forget object-relational impedance!
- Minimal **full CRUD API** client with flexible generics & **integrated validation logic**.
- **Reactivity** everywhere: **async API** & **reactive UI** state fully centralized.

---

## Escape Hatch Pragmatism 🛠️

Not all problems are CRUD. For integrations, workflows, or heavy computations:

- **NiceGUI** delivers rapid UI in Python.
- **FastAPI** is always there for custom endpoints, advanced auth, or third-party APIs.
- Hybrid model: 80% handled by Postgres + PostgREST, 20% by FastAPI when needed.

---

## Real-World Example

A tenant-union system runs on:

```yaml
services:
  db: PostgreSQL with triggers/functions
  server: PostgREST API
  nicegui-app: Python UI (+ FastAPI auth)
    extras:
      - nginx: security + reverse proxy (with ufw for host-level firewall)
      - certbot: SSL certs via cronjob (automated renewal)
```

**Results:** 16 tables → 16+ endpoints (plus materialized views), instant UI updates from schema changes, secure & production-ready with Docker + firewall.

---

## Who This Is For 🎯

✅ CRUD-heavy apps (dashboards, membership systems, internal tools)
✅ Small/medium teams who value speed & simplicity
✅ Devs comfortable with SQL/Postgres

⚠️ Risky for:

- Large enterprises with rigid separation of concerns
- Teams who avoid SQL and prefer frontend-first workflows

---

## The Core Question

Instead of asking:

> _Which ORM should we use?_

Ask instead:

> _How much can Postgres do for us—and what’s the simplest way to handle the rest?_

---
