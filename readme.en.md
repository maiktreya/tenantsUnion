# Tenants Union Platform

The **Tenants Union Platform** is a secure web application designed for tenant organizing, affiliate tracking, and housing data analytics. Built using Python's **NiceGUI** framework (FastAPI + Vue.js/Quasar unified ecosystem), it connects a reactive management dashboard directly to a hardened PostgreSQL/PostGIS relational database.

Data ingestion is entirely automated via a headless asynchronous **ETL (Extract, Transform, Load) Pipeline** that pulls, enriches, and synchronizes registration updates on a daily schedule.

---

## 🛠️ Tech Stack

* **Frontend & Backend Interface:** NiceGUI (Python-unified fullstack layout)
* **Database Engine:** PostgreSQL + PostGIS (Spatial indexing, relational mapping)
* **DevOps & Server Security:** Docker Compose, Nginx Reverse Proxy, Certbot SSL, and automated iptables firewall scripting
* **Enrichment Integration:** CartoCiudad Geocoding API

---

## 🏗️ Asynchronous ETL Pipeline Architecture

Rather than relying on manual browser-based data uploads, a headless background sync orchestrates data transfers every 24 hours via `utils/cron/daily_sync.sh`:

1. **Extract:** Establishes a secure SSH tunnel to the remote WordPress application database. It un-pivots raw Gravity Forms entry parameters into tabular structures while deduplicating entries within the 24-hour window.
2. **Transform:** Cleans and normalizes Spanish street addresses (`ETL/02-geolink.py`). It queries the CartoCiudad API using exponential backoff retry logic to attach accurate location coordinates and unique Cadastral References.
3. **Load:** Streams the dataset into PostgreSQL staging layers (`ETL/03-load-from-csv.sql`). It transforms coordinate parameters into indexable PostGIS spatial geometries, cross-references and links vertical properties (`bloques`), and applies idempotent `UPSERT` statements to cleanly update records in place.

---

## 🚀 Quick Start & Deployment

### 1. Environment Configuration

Before launching the application containers, copy the environment template and populate it with your specific database configurations, network credentials, API endpoints, and server profiles:

```bash
cp .env.example .env

```

### 2. Running the Application

The infrastructure relies on specialized Docker Compose environment profiles to cleanly isolate local development tasks from fully secured production hosting setups.

#### 🛠️ Development Setup

To boot up the platform locally with synthetic database records, hot-reload configurations, and development-only volumes, run:

```bash
docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --renew-anon-volumes

```

#### 🔒 Production Setup

To spin up the fully hardened environment, activating automated reverse proxies, Row-Level Security (RLS) policies, SSL certificate management loops, and production firewalls, run:

```bash
docker compose --profile Secured up -d

```

---

## 🧪 Testing Suite

Automated system checks validate domain typing structures, user security scopes, and unified frontend-backend interaction paths. Run the testing harness using `pytest`:

```bash
pytest

```