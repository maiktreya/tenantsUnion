# The Why (Not?): A Manifesto for the Pragmatic, Database-Centric Architecture

## The Premise: A Better Stack for Data-Centric Apps

In an era of ever-increasing complexity in application backends, we often default to multi-layered, ORM-driven architectures that require vast amounts of boilerplate code before delivering any business value.

This document outlines a more pragmatic and productive approach: a **database-centric architecture** that treats PostgreSQL as the computational core of the system. Specifically, we advocate for a stack combining:

- **PostgreSQL** as the core logic and data engine
- **PostgREST** for zero-boilerplate API generation
- **NiceGUI** for rapid UI development (with FastAPI available as an "escape hatch" when needed)

This is a manifesto for treating the database as the powerful computational center of the system, not merely as a passive persistence layer. At their heart, most business applications are systems for managing structured data (CRUD), and this architecture embraces that reality to maximize efficiency and reliability.

## The Alternative: A Declarative, Data-First Approach

Instead of writing imperative code to manage data, we adopt a declarative approach. By using PostgREST, we automatically generate a secure, high-performance, and fully-featured RESTful API directly from the database schema itself.

This architecture is built on three core pillars:

### 1. The Database is the Application's Heart ❤️

The database schema is treated as the single source of truth. It's not just a blueprint for storage; it's the contract for the entire system.

**Data Integrity is Guaranteed**: Business rules, constraints, and data validation are enforced at the deepest possible layer, ensuring no invalid state can ever be created, regardless of the client consuming the API.

**Logic Lives with the Data**: By using database views, functions (PL/pgSQL), and triggers, data-centric logic is executed right next to the data it operates on. This is orders of magnitude more performant than pulling data across a network into an application layer, processing it, and then sending it back.

### 2. Radical Productivity Through a "Zero-Boilerplate" API 🚀

The most time-consuming part of backend development is often writing repetitive CRUD endpoints. A declarative API layer eliminates this entirely.

**Develop at the Speed of SQL**: Need a new field? Add a column. Need a new read-only endpoint with joined data? Create a view. The API instantly reflects these changes without a single line of application code being written.

**Focus on Business Value, Not Plumbing**: Developer time is freed from writing tedious data access logic and can be spent on what truly matters: implementing the unique business features that deliver value.

### 3. Performance and Simplicity by Design ⚙️

Fewer layers mean less overhead and a simpler system that is easier to understand, debug, and maintain. The entire "middle tier" of a traditional application is effectively replaced by a single, stateless, and highly optimized binary.

## The Pragmatic "Escape Hatch": When You Need More

This architecture is not a rigid dogma; it's a pragmatic starting point. We recognize that not all logic is simple data manipulation. What happens when you need to orchestrate complex workflows, integrate with third-party systems, or implement sophisticated UI interactions?

This is where **NiceGUI** becomes strategically valuable. Built on top of FastAPI, NiceGUI provides:

### Primary Role: Rapid UI Development
- **Python-Native Frontend**: Build complex, reactive user interfaces entirely in Python
- **No Context Switching**: Stay in one language and ecosystem for the entire stack
- **Immediate Productivity**: Skip the HTML/CSS/JavaScript learning curve for data-driven applications

### Strategic "Escape Hatch": Full FastAPI Power When Needed
Because NiceGUI runs on FastAPI, you have access to the complete FastAPI ecosystem without adding another service or increasing architectural complexity:

**80% of the Work**: Handled by the database and PostgREST for unparalleled speed in CRUD operations.

**20% of the Work**: Handled by custom FastAPI endpoints written directly within the NiceGUI application for tasks such as:
- **External API Integrations**: Communicating with payment gateways, government services, or third-party APIs
- **Complex Workflows**: Multi-step processes requiring coordination between services
- **Heavy Computations**: Complex calculations better suited to Python's rich ecosystem than pure SQL
- **Advanced UI Logic**: Custom authentication middleware, file uploads, or real-time features

This creates a powerful hybrid model where FastAPI capabilities are available on-demand, but not required for basic functionality.

## Real-World Implementation: A Concrete Example

Consider this actual production stack for a tenant union management system:

```yaml
# Three services, maximum productivity + 2 secured by default
services:
  db:           # PostgreSQL with business logic in triggers/functions
  server:       # PostgREST auto-generating API from schema
  nicegui-app:  # Python UI with FastAPI middleware for auth
  certbot:     # SSL certificates for HTTPS
  nginx:       # Reverse proxy with SSL termination
```

**The Results**:
- **Zero API Boilerplate**: 15+ database tables become 15+ REST endpoints automatically
- **Database-Driven Features**: Complex geographic node assignments handled by PL/pgSQL triggers
- **Hybrid Flexibility**: Authentication middleware implemented in FastAPI, UI interactions in pure Python
- **Rapid Development**: New data relationships appear in the UI immediately after schema changes

**Key Insight**: FastAPI isn't the primary development paradigm—it's an available tool when PostgreSQL and NiceGUI reach their limits.

## Ready for production and secure by default

At the host level, it is trivial to secure the system with a firewall and automated renewal of SSL certificates. The system is ready for production with minimal configuration and just docker compose:

```yaml
# Single container host with security and automation
 host:
  docker:      # Single container host for simplicity
  ufw:         # Firewall with only ports 22, 80, 443 op
  cron:        # Automated backups and certbot renewal
```


## Summarizing

The database-centric architecture represents a conscious choice to prioritize pragmatism over architectural purity. It challenges the notion that more layers and more code equate to a better system.

**FastAPI is present not as a requirement, but as an insurance policy**—a powerful escape hatch that ensures you're never boxed in by architectural decisions. You can start with pure PostgreSQL + PostgREST + NiceGUI productivity and selectively add FastAPI endpoints only when and where they provide genuine value.

For the right project, this approach offers an unparalleled combination of development speed, runtime performance, data integrity, and the flexibility to handle any future requirement.

It's time we stopped asking "Which ORM should we use?" and started asking, "How much of this can our database do for us, and what's the simplest way to handle the rest?"

## 🎯 Is this my Crewd?

This manifesto is not for every project. It’s perfect for:

* CRUD-heavy apps (internal tools, data management, admin dashboards, membership/union systems).

* Small/medium teams that want to deliver value fast without drowning in boilerplate.

Teams already comfortable with SQL and PostgreSQL.

It will feel risky to:

* Large enterprises with strict separation-of-concerns dogma.

* Teams where most devs are frontend-first and don’t want to touch SQL.