# Management System for a Tenants' Union (`readme.en.md`)

This project is a comprehensive full-stack web application developed to facilitate internal information tracking, relationship mapping, and automated data analytics for the **Tenants' Union**. The interface, built natively using **NiceGUI**, delivers a highly reactive data management dashboard backed by a production-hardened PostgreSQL/PostGIS database instance.

The platform's data entry model is driven by an asynchronous, headless **ETL (Extract, Transform, Load) Pipeline**. This automated architecture removes old operational bottlenecks from legacy web-based spreadsheet interfaces, running out-of-band to ingest, format, geocode, and clean decentralized portal submissions with high consistency.

---

## 🏛️ Architecture

The application implements a secure, three-tier architecture fully isolated within a containerized Docker ecosystem. This structure maximizes data encapsulation and guarantees deployment reproducibility across localized test setups and secured production hosts.

```mermaid
graph TD
    subgraph "Client Layer"
        A[User Web Browser]
    end

    subgraph "Single Containerized Secure Host"
        B[UFW Firewall Host Restrictions <br> Ports: 22 / 80 / 443]
        C[Nginx Reverse Proxy <br> SSL/TLS Cryptographic Termination]
        D[NiceGUI Dashboard Application Engine <br> Python / FastAPI / Quasar Context]
        E[PostgreREST API Data Gateways]
        F[PostgreSQL Relational Storage Layer <br> PostGIS / Views / Row-Level Security]
    end

    subgraph "Asynchronous External Data Pipeline"
        G[Daily System Cron Engine <br> 0 2 * * * Execution Schedule]
        H[Remote WordPress / Gravity Forms DB]
        I[CartoCiudad External Geocoding API]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E <--> F
    G -->|1. Secure SSH Tunnel & Extract| H
    G -->|2. Address Standardization & Geocode| I
    G -->|3. High-Performance COPY Ingestion| F

```

- **Presentation Layer (NiceGUI):** A modern, high-performance Python framework built over FastAPI and Vue/Quasar. It unifies interface components and state layers directly into clean, type-checked Python modules, removing the need for separate JavaScript or CSS configurations.
- **API Data Gateway (PostgREST):** Eliminates manual backend boilerplate routing tasks by dynamically converting internal database schema mappings, tables, and relational components directly into accessible RESTful service endpoints.
- **Data & Spatial Layer (PostgreSQL + PostGIS):** Serves as the authoritative single source of truth for all system state. Business constraints, access controls, spatial indexing, automated timestamp auditing, and tracking metrics are enforced directly at the data layer using native PL/pgSQL functions, database views, triggers, and Row-Level Security (RLS) configurations.
- **Ingestion Automation (Headless ETL):** A modular background routine scheduled via `utils/cron/daily_sync.sh` that securely tunnels into remote target environments, isolates new registration records, standardizes unstructured user-typed strings, attaches geographic coordinate markers, and commits updates to PostgreSQL.

---

## ⭐ Key Features

The management console partitions functionalities into modular runtime interfaces, granting visibility across tracking nodes using role-based query permissions:

- **Database Administration Console (`ADMIN BBDD`):** \* Full multi-table Create, Read, Update, and Delete (CRUD) controls with integrated foreign key lookups and contextual selection menus.
- Interactive relationship explorers to traverse linked records across parent and child constraints.
- Localized diagnostic import and export routines utilizing standard CSV file structures.

- **Materialized Views Analytics (`VISTAS`):**
- Read-only administrative views exposing complex, aggregated analytical data blocks for union coordination.
- Fast client-side multi-parameter filtering, text-search indexes, and dynamic column sorting configurations.

- **Conflict & Organizing Tracker (`CONFLICTOS`):**
- Specialized modules explicitly designed to log, flag, and monitor tenant labor disputes, landlord updates, and collective organizing milestones.
- Automated historical logs that track notes, legal updates, and case status changes with immutable timestamp validation.

- **Automated Spatial ETL Engine (Gravity Forms Synchronization):**
- An autonomous background synchronization system running on a strict daily cron cycle.
- Performs secure SSH socket forwarding to extract new registrations from a remote WordPress database while cleaning up text strings and un-pivoting metadata records.
- Applies a multi-stage address matching fallback framework that calls the **CartoCiudad API** to append highly precise latitude/longitude markers and formal Spanish Cadastral References (`ref_catastral`).
- Uses high-speed staging imports and idempotent database `UPSERT` rules to process structural real estate properties (`bloques`), unit descriptions (`pisos`), billing updates (`facturacion`), and union members.

- **Security & Identity Protections:**
- Encrypted user credentials protected with adaptive cryptographic hashing (`bcrypt`).
- Strict Role-Based Access Control (RBAC) separating administrative roles, regional case managers, and read-only auditors.
- Database-enforced Row-Level Security (RLS) verifying active JSON Web Tokens (JWT) to shield sensitive organizational metrics from unprivileged queries.

---

## 🚀 Technologies Used

| Layer / Component     | Specialized Technology Engine          | Concrete Purpose within Ecosystem                                   |
| --------------------- | -------------------------------------- | ------------------------------------------------------------------- |
| **User Interface**    | NiceGUI (Built over FastAPI & Uvicorn) | Renders reactive, Python-unified system dashboards.                 |
| **API Framework**     | PostgREST Gateway                      | Auto-generates low-latency REST endpoints directly from schemas.    |
| **Database Core**     | PostgreSQL Server                      | Provides durable relational table tracking and constraint logic.    |
| **Geospatial Engine** | PostGIS Extension                      | Handles geographic coordinate mapping and spatial indexing.         |
| **Container Layer**   | Docker / Docker Compose                | Isolates, packages, and builds independent microservices.           |
| **Gateway Security**  | Nginx Reverse Proxy Template           | Centralizes ingress traffic, hides services, and handles rate maps. |
| **SSL Automation**    | Let's Encrypt + Certbot                | Automates renewal loops for TLS connection paths.                   |
| **Address Resolver**  | CartoCiudad API Engine                 | Provides spatial coordinates and official cadastral validation.     |
| **Host Protection**   | Uncomplicated Firewall (UFW)           | Restricts connection entryways to ports 22, 80, and 443.            |

---

## 🛠️ Deployment & Installation

### Quick Start (Local Development Mode)

This configuration initializes the software services locally, exposes the raw database and API gateway interfaces for inspection, and seeds a synthetic dataset for testing.

1. **Clone the target repository instance:**

```bash
git clone https://github.com/maiktreya/tenantsUnion.git
cd tenantsUnion

```

2. **Initialize your development environment file:**
   Copy the sample environment file to `.env`:

```bash
cp .env.example .env

```

1. **Spin up the development environment profile:**
   Execute the multi-file Compose setup to enable hot-reloading configurations, allocate development volumes, and run the service containers:

```bash
docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --renew-anon-volumes

```

4. **Local Access Endpoints:**

- **Management Panel:** `http://localhost:8081`
- **API Explorer:** `http://localhost:3001/afiliadas`
- **Raw Database Target:** `postgresql://app_user:password@localhost:5432/mydb`

---

### Production Deployment (Hardened SSL Setup)

Follow these instructions to run the application on a production-facing cloud host with active firewalls, automated reverse proxies, and valid TLS certificates.

1. **Clone and enter the repository context:**

```bash
git clone https://github.com/maiktreya/tenantsUnion.git
cd tenantsUnion

```

2. **Configure production environment keys:**
   Copy the template to `.env` and fill in your unique domain routing indicators, security tokens, and administration contact emails:

```dotenv

# Production Server DNS Routing Profiles
HOSTNAME=your-domain.duckdns.org
DUCKDNS_TOKEN=your-duckdns-token
EMAIL=your-email@example.com

```

3. **Bootstrap Let's Encrypt certificates:**
   Run the initial certificate generation wrapper script to establish your server credentials. **This step is only required on the first deployment initialization:**

```bash
chmod +x utils/init-letsencrypt.sh
./utils/init-letsencrypt.sh

```

4. **Launch the secured production containers:**
   Start up the service stacks under the `Secured` network environment profile:

```bash
docker compose --profile Secured up -d

```

5. **Enable host-level network protections:**
   Lock down unneeded open entryways on the host machine using the provided automated network firewall setup script:

```bash
chmod +x utils/setup_firewall.sh
sudo ./utils/setup_firewall.sh

```

The application dashboard will now be live and securely accessible via HTTPS at `https://your-domain.duckdns.org`.

---

## 🧪 Testing Suite

You can check in detail how to deploy the dev version of this application for the firt time [Here](https://github.com/maiktreya/tenantsUnion/blob/main/doc/first_run.md)

The system includes a comprehensive automated testing framework powered by `pytest`. This test suite validates database constraint mechanics, JWT access permissions, address sanitization patterns, and asynchronous UI workflow rendering.

To run the testing framework inside your execution context and review code coverage matrices, execute:

```bash
pytest --cov

```

For comprehensive configuration steps, framework setups, and instructions on running isolated integration passes, review the [Testing documentation](https://github.com/maiktreya/tenantsUnion/blob/main/doc/testing.md).

---

## 🤝 Contributions & Contact

Community review, enhancements, and tracking modifications are highly appreciated. For design discussions, scaling questions, or repository coordination, please open an issue tracking card or submit a pull request.

**Primary Infrastructure Contact:** [garciaduchm@gmail.com](mailto:garciaduchm@gmail.com)

---

## 📄 License

This software architecture and its codebase are distributed under the **GNU General Public License v3.0 (GPLv3)**. Technical documentation sheets, structural diagrams, and associated resource materials are shared under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license framework.
