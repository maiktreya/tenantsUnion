# Management System for a Tenants' Union

[<img src="https://img.shields.io/badge/Español-1f425f.svg" alt="Leer en Español">](./readme.md)

This project is a desktop web application developed to facilitate the internal information management of the **Tenants' Union**. The interface, built with **NiceGUI**, offers a fast and reactive user experience to interact with a PostgreSQL database through a RESTful API automatically generated with **PostgREST**.

## 🏛️ Architecture

The system follows a three-tier architecture, fully containerized with Docker to ensure portability and ease of deployment. This pragmatic choice is optimized for maximum productivity for small teams.

```mermaid
graph TD
    subgraph "Client"
        A[User in Web Browser]
    end

    subgraph "Single Dockerized Host"
        B[UFW Firewall <br> Ports 22/80/443]
        C[Nginx Reverse Proxy <br> SSL Termination]
        D[NiceGUI Frontend <br> Python]
        E[PostgREST API <br> Generated from DB]
        F[PostgreSQL Database]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E <--> F
```

- **Data Layer (PostgreSQL):** The single source of truth. Low-level logic, such as node synchronization or validation, is implemented directly in the database using views, functions, and triggers to centralize rules and ensure consistency.
- **API Layer (PostgREST):** Instead of manually writing a backend, PostgREST generates a high-performance RESTful API directly from the database schema, drastically reducing development time.
- **Presentation Layer (NiceGUI):** A modern Python framework that allows for building the user interface quickly and efficiently, without needing to write separate JavaScript, HTML, or CSS.

## ⭐ Key Features

The application is organized into key functional modules, accessible according to assigned user roles.

- **Full DB Administration (`ADMIN BBDD`):**
  - CRUD (Create, Read, Update, Delete) management on all tables.
  - Automatic resolution of foreign keys with dropdown menus.
  - Relationship explorer to view parent and child records.
  - Data import and export to CSV format.
- **Views Explorer (`VISTAS`):**
  - Read-only access to materialized views for consolidated data analysis.
  - Powerful client-side filtering and search system.
- **Conflict Manager (`CONFLICTOS`):**
  - Specialized module for detailed conflict tracking.
  - Allows adding notes, actions, and tracking the history of each case.
  - Automated status and date updates when logging notes.
- **Member Importer (`IMPORTAR AFILIADAS`):**
  - Tool for bulk uploading new members from a CSV file.
  - Real-time data validation and editable preview before final import.
- **Security and User Management:**
  - Secure authentication with hashed passwords (bcrypt).
  - Role-Based Access Control (RBAC) for `admin`, `gestor`, etc.
  - Interface for administrators to manage users and assign roles.
  - User profile for self-management of personal data and password.

## 🚀 Technologies Used

| Component            | Technology                 | Purpose                                            |
| -------------------- | -------------------------- | -------------------------------------------------- |
| **Frontend**         | NiceGUI (on FastAPI)       | Fast and reactive web user interface in Python.    |
| **API**              | PostgREST                  | Automatic generation of RESTful API from the DB.   |
| **Database**         | PostgreSQL                 | Relational data storage and business logic.        |
| **Containerization** | Docker and Docker Compose  | Service orchestration for consistent deployment.   |
| **Reverse Proxy**    | Nginx                      | Single entry point, SSL termination, and security. |
| **SSL Certificates** | Let's Encrypt with Certbot | Free and automated HTTPS encryption.               |
| **Dynamic DNS**      | DuckDNS                    | Domain management for the SSL certificate.         |
| **Firewall**         | UFW                        | Firewall to restrict port access.                  |

---

## 🛠️ Installation Guide

### Quick Start (Local Development)

This method exposes the database and API ports to facilitate development.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/maiktreya/tenantsUnion.git
   cd tenantsUnion
   ```

2. **Configure the development environment:**
   Copy `.env.example` to `.env`. Ensure the following variable is set to use test data:

   ```dotenv
   INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts-dev
   ```

3. **Start the services:**

   ```bash
   # Local development
   docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --build --renew-anon-volumes
   ```

4. **Access the application:**
   - **Frontend:** `http://localhost:8081`
   - **API (example):** `http://localhost:3001/afiliadas`
   - **Database:** `postgresql://app_user:password@localhost:5432/mydb`

### Production Deployment (Secure with SSL)

Follow these steps for a single-host deployment with security and HTTPS enabled.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/maiktreya/tenantsUnion.git
   cd tenantsUnion
   ```

2. **Configure environment variables:**
   Create a copy of `.env.example` and rename it to `.env`. **Adjust the following mandatory values**:

   ```dotenv
   # Ensure you use the production scripts
   INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts

   # --- MANDATORY SSL CONFIGURATION ---
   HOSTNAME=your-domain.duckdns.org
   DUCKDNS_TOKEN=your-duckdns-token
   EMAIL=your-email@example.com
   ```

3. **Run the initial SSL setup script:**
   This script automates obtaining certificates. **You only need to run it the first time.**

   ```bash
   chmod +x utils/init-letsencrypt.sh
   ./utils/init-letsencrypt.sh
   ```

4. **Start all services:**
   Once the certificates are generated, start the complete application.

   ```bash
   docker compose --profile Secured --profile Frontend up -d
   ```

5. **Configure the Firewall (Recommended):**
   Secure your server by allowing only necessary traffic.

   ```bash
   chmod +x utils/setup_firewall.sh
   sudo ./utils/setup_firewall.sh
   ```

Done! The application will be available at `https://your-domain.duckdns.org`.

---

### Exploring the API

This project uses **PostgREST**, which turns your database into a RESTful API. You don't need to write backend code for CRUD operations.

- **Access:** The API is internal to the Docker network. In a development environment, you can access it through the exposed port (`http://localhost:3001`).
- **Endpoints:** Each table and view in your `sindicato_inq` schema becomes an endpoint. For example, the `afiliadas` table is accessible at `/afiliadas`.
- **Queries:** You can use URL parameters to filter, sort, and paginate. For example, to get members with the "Alta" status:

  `http://localhost:3001/afiliadas?estado=eq.Alta`

For more information, check the official PostgREST documentation.

### Common Operations

- **View logs:** `docker compose logs -f`
- **Stop the application:** `docker compose down`
- **Update (after a `git pull`):** `docker compose --profile Secured --profile Frontend up -d --build`
- **Manually renew SSL certificates:** `./utils/renew_certificates.sh`

## 🔐 Security

- **Reverse Proxy:** Nginx is the single entry point, hiding internal services.
- **Encrypted Traffic:** HTTPS with Let's Encrypt SSL certificates, managed automatically.
- **Firewall:** `ufw` restricts access to ports 22 (SSH), 80 (HTTP), and 443 (HTTPS).
- **Secure Passwords:** Passwords are stored hashed using bcrypt.
- **Secret Management:** No hardcoded keys or secrets. Everything is managed via `.env`, which is excluded by `.gitignore`.
- **RLS (Row-Level Security):** DB level securization implemented with JWT tokens.

## 🧪 Testing

The project has an automated test suite to ensure code quality and stability. The tests cover everything from isolated units to complete user interface flows. To run the full test suite, use the following command:

```bash
pytest --cov
```

For a detailed guide on how to set up the testing environment and run different types of tests, refer to the [testing guide](https://github.com/maiktreya/tenantsUnion/blob/main/doc/testing.md).

---

## 🤝 Contributions

Contributions are welcome! If you have ideas, suggestions, or want to collaborate on the development of this project, feel free to get in touch.

**Contact:** <garciaduchm@gmail.com>

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPLv3). Additionally, the content and associated documentation are distributed under a Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) license.

2025-10-21 @maiktreya
