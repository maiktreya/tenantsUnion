# Fleet Operations & Scaling Architecture Guide

This document outlines the scaling philosophy, infrastructure architecture, and operational runbooks for managing a decentralized network of independent regional tenant union instances using unified codebase definitions.

---

## 1. Architectural Classification: Multi-Instance Isolated Monolith

Instead of scaling a single multi-tenant cloud application with row-level logical partitioning in a shared database, this project implements a **Multi-Instance Isolated Monolith (Federated Topology)**. 

```
                    [ Unified Repository: main branch ]
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
      [ Node 1: Madrid Stack ]          [ Node 2: Barcelona Stack ]
   ┌───────────────────────────────┐ ┌───────────────────────────────┐
   │ 💻 NiceGUI Monolith           │ │ 💻 NiceGUI Monolith           │
   │ 🧠 PostgreSQL (Isolated Data) │ │ 🧠 PostgreSQL (Isolated Data) │
   │ 🔒 Local .env Configuration   │ │ 🔒 Local .env Configuration   │
   └───────────────────────────────┘ └───────────────────────────────┘
                    ▲                                 ▲
                    └────── Federated Data Sync ──────┘
                             (federated_courier)
```

### Core Design Pillars
1. **Dynamic Parameterization:** The entire application stack is driven from a single branch (`main`). Branding, interface titles, and endpoint routes adapt dynamically at runtime using host-specific environment variables mapped inside `build/niceGUI/config.py` (e.g., `INSTANCE_NAME`).
2. **Strict Data Isolation:** Regional nodes maintain entirely separated database systems running on distinct physical or virtual hosts. This guarantees absolute data privacy, eliminates the risk of cross-tenant leaks, reduces database index contention, and guarantees compliance with localized data protection policies.
3. **Database-Driven Logic:** The architecture treats PostgreSQL as the primary analytical engine. Advanced routing and ETL processing are handled downstream via dedicated procedural layers (`plpgsql` functions and specialized views) instead of high-overhead Python ORMs.
4. **Federated Ingestion Loops:** Inter-instance cross-pollination happens safely via asynchronous remote procedure calls executed by service boundaries like `federated_courier.py`, which selectively fetch shared metadata records across sibling satellites.

---

## 2. Fleet Management and Server Automation

Infrastructure management is driven by a lightweight GitOps loop using Ansible. Configuration variables (credentials, API secrets) are decoupled from version control and managed via host-specific `.env` properties on target nodes.

Fleet management scripts are located in the `~/tenantsunion-ops` orchestration directory.

### Operational Command 1: Code Base Synchronization
To pull the latest verified commits down from the single source-of-truth branch to all active remote destination target installations, execute:

```bash
ansible-playbook pull.yaml
```

**Under the Hood:** This task iterates through the active fleet infrastructure defined inside your `hosts.yaml` map, hits the targeted remote locations over persistent multiplexed SSH sockets, and executes a clean upstream tracking sync:
* Targets: `inquilinato.duckdns.org`, `poderinquilino.duckdns.org`
* Repository target folder: `/home/other/github/prod/tenantsUnion`
* Core Branch: `main`

### Operational Command 2: Container Lifecycle & Rebuilds
To recompile modified visual layouts, compile updated packages, and apply structural changes to service configurations, execute:

```bash
ansible-playbook docker.yaml
```

**Under the Hood:** Instructs the remote daemon layers to execute an atomic, cache-aware reconstruction of targeted runtime layers:
* Command ran: `docker compose --profile Secured --profile Frontend up -d --build`
* Profile isolation guarantees that monitoring services, automated SSL/Certbot renewing environments, and the NiceGUI web monolithic layer are initialized safely in their correct network namespaces.

### Operational Command 3: Zero-Overhead Declarative Schema Synchronization
Because this project deliberately bypasses traditional Python Object-Relational Mappers (ORMs), it rejects step-by-step sequential migration timelines (like Alembic). Instead, it relies on a **Declarative Database Mutation Strategy** powered by `migra`.

To safely diff and push schema alterations from your declarative initialization scripts directly into running production tables without touching actual user data rows, execute:

```bash
ansible-playbook deploy_schema.yml
```

#### The Internal Automation Pipeline
1. **Ephemeral Instance Provisioning:** The playbook initializes a temporary, isolated target database container (`postgres:17-alpine`, matching the production major version so `migra` produces accurate diffs) running completely in memory.
2. **Source-of-Truth Convergence:** The playbook sequentially injects the entire versioned repository database initialization flow into the empty sandbox instance to build a complete architectural map:
   * `01-init-schemaDBdef.sql` (Tables & Primary Indices)
   * `02-init-plpgsql_functions.sql` (Procedural Business Logic)
   * `03-init-createViews.sql` (Relational Application Interfaces)
   * `04-init-user_roles.sql` (Roles & Seed Users — `web_anon` / `web_user` are not created here; they come from `06`)
   * `05-init-artificial_data.sql` (Artificial Data — empty stub in `init-scripts/`, populated only by the `-dev` override)
   * `06-init-rls.sql` (Database Privileges, Role Grants & Row-Level Security)
3. **State Differentiation Engine (`migra`):** The tool automatically inspects the live production database schemas and structural components of individual city databases against the compiled target repository sandbox.
4. **Data Protection Guardrail (Drop Interceptor):** A built-in regex scanner monitors the calculated migration block. If a column or table rename is misidentified as a destructive `DROP COLUMN` or `DROP TABLE` command, **the playbook instantly triggers a hard failure abort**, freezing the deployment pipeline before live production storage arrays are touched.
5. **Atomic Transaction Injection:** Valid additive operations (new tracking arrays, updated query views, or modified constraints) are encapsulated inside a strict explicit transaction block:
   ```sql
   BEGIN;
   -- Calculated Structural Alterations
   -- Automated Re-application of Security Access Matrices
   COMMIT;
   ```
   This ensures that if any patch execution errors occur on any individual host, the target instance automatically performs a full, non-destructive state rollback.
