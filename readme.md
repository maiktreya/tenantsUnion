# Sistema de Gestión para el Sindicato de Inquilinas de Madrid

[<img src="https://img.shields.io/badge/English-1f425f.svg" alt="Read in English">](./readme.en.md)

Este proyecto es una aplicación web de escritorio desarrollada para facilitar la gestión interna de la información del **Sindicato de Inquilinas e Inquilinos**. La interfaz, construida con **NiceGUI**, ofrece una experiencia de usuario rápida y reactiva para interactuar con una base de datos PostgreSQL a través de una API RESTful generada automáticamente con **PostgREST**.

## 🏛️ Arquitectura

El sistema sigue una arquitectura de tres capas, completamente dockerizada para garantizar la portabilidad y facilidad en el despliegue. Esta elección pragmática está optimizada para la máxima productividad de equipos pequeños.

```mermaid
graph TD
    subgraph "Cliente"
        A[Usuario en Navegador Web]
    end

    subgraph "Host Único Dockerizado"
        B[Firewall UFW <br> Puertos 22/80/443]
        C[Nginx Reverse Proxy <br> SSL Termination]
        D[Frontend NiceGUI <br> Python]
        E[API PostgREST <br> Generada desde BBDD]
        F[Base de Datos PostgreSQL]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E <--> F
```

- **Capa de Datos (PostgreSQL):** La única fuente de verdad. La lógica de bajo nivel, como la sincronización de nodos o la validación, se implementa directamente en la BBDD mediante vistas, funciones y triggers para centralizar las reglas y garantizar la consistencia.
- **Capa de API (PostgREST):** En lugar de escribir un backend manualmente, PostgREST genera una API RESTful de alto rendimiento directamente desde el esquema de la base de datos, reduciendo drásticamente el tiempo de desarrollo.
- **Capa de Presentación (NiceGUI):** Un framework moderno en Python que permite construir la interfaz de usuario de forma rápida y eficiente, sin necesidad de escribir JavaScript, HTML o CSS por separado.

## ⭐ Características Principales

La aplicación se organiza en módulos funcionales clave, accesibles según los roles de usuario asignados.

- **Administración de BBDD Completa (`ADMIN BBDD`):**
  - Gestión CRUD (Crear, Leer, Actualizar, Eliminar) en todas las tablas.
  - Resolución automática de claves foráneas con menús desplegables.
  - Explorador de relaciones para visualizar registros padre e hijo.
  - Importación y Exportación de datos a formato CSV.
- **Explorador de Vistas (`VISTAS`):**
  - Acceso de solo lectura a vistas materializadas para análisis de datos consolidados.
  - Potente sistema de filtros y búsqueda en el lado del cliente.
- **Gestor de Conflictos (`CONFLICTOS`):**
  - Módulo especializado para el seguimiento detallado de conflictos.
  - Permite añadir notas, acciones y seguir el historial de cada caso.
  - Actualización de estado y fechas automatizada al registrar notas.
- **Importador de Afiliadas (`IMPORTAR AFILIADAS`):**
  - Herramienta para la carga masiva de nuevas afiliadas desde un archivo CSV.
  - Validación de datos en tiempo real y previsualización editable antes de la importación.
- **Seguridad y Gestión de Usuarios:**
  - Autenticación segura con contraseñas hasheadas (bcrypt).
  - Control de Acceso Basado en Roles (RBAC) para `admin`, `gestor`, etc.
  - Interfaz para que los administradores gestionen usuarios y asignen roles.
  - Perfil de usuario para auto-gestión de datos personales y contraseña.

## 🚀 Tecnologías Utilizadas

| Componente           | Tecnología                                     | Propósito                                               |
| -------------------- | ---------------------------------------------- | ------------------------------------------------------- |
| **Frontend**         | [NiceGUI](https://nicegui.io/) (sobre FastAPI) | Interfaz de usuario web rápida y reactiva en Python.    |
| **API**              | [PostgREST](http://postgrest.org/)             | Generación automática de API RESTful desde la BBDD.     |
| **Base de Datos**    | PostgreSQL                                     | Almacenamiento de datos relacional y lógica de negocio. |
| **Contenerización**  | Docker y Docker Compose                        | Orquestación de servicios para despliegue consistente.  |
| **Proxy Inverso**    | Nginx                                          | Punto de entrada único, terminación SSL y seguridad.    |
| **Certificados SSL** | Let's Encrypt con Certbot                      | Cifrado HTTPS gratuito y automatizado.                  |
| **DNS Dinámico**     | DuckDNS                                        | Gestión de dominio para el certificado SSL.             |
| **Firewall**         | UFW                                            | Cortafuegos para restringir el acceso a puertos.        |

---

## 🛠️ Guía de Instalación

### Inicio Rápido (Desarrollo Local)

Este método expone los puertos de la base de datos y la API para facilitar el desarrollo.

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/maiktreya/tenantsUnion.git
   cd tenantsUnion
   ```

2. **Configurar el entorno de desarrollo:**
   Copia `.env.example` a `.env`. Asegúrate de que la siguiente variable esté configurada para usar datos de prueba:

   ```dotenv
   INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts-dev
   ```

3. **Levantar los servicios:**

   ```bash
   # Desarrollo local
    docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --build --renew-anon-volumes
   ```

4. **Acceder a la aplicación:**
   - **Frontend:** `http://localhost:8081`
   - **API (ejemplo):** `http://localhost:3001/afiliadas`
   - **Base de Datos:** `postgresql://app_user:password@localhost:5432/mydb`

### Despliegue en Producción (Seguro con SSL)

Sigue estos pasos para un despliegue en un único host con seguridad y HTTPS habilitado.

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/maiktreya/tenantsUnion.git
   cd tenantsUnion
   ```

2. **Configurar las variables de entorno:**
   Crea una copia de `.env.example` y renómbrala a `.env`. **Ajusta los siguientes valores obligatorios**:

   ```dotenv
   # Asegúrate de usar los scripts de producción
   INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts

   # --- CONFIGURACIÓN SSL OBLIGATORIA ---
   HOSTNAME=tu-dominio.duckdns.org
   DUCKDNS_TOKEN=tu-token-de-duckdns
   EMAIL=tu-email@ejemplo.com
   ```

3. **Ejecutar el script de configuración inicial de SSL:**
   Este script automatiza la obtención de certificados. **Solo necesitas ejecutarlo la primera vez.**

   ```bash
   chmod +x utils/init-letsencrypt.sh
   ./utils/init-letsencrypt.sh
   ```

4. **Levantar todos los servicios:**
   Una vez generados los certificados, levanta la aplicación completa.

   ```bash
   docker compose --profile Secured --profile Frontend up -d
   ```

5. **Configurar el Firewall (Recomendado):**
   Asegura tu servidor permitiendo únicamente el tráfico necesario.

   ```bash
   chmod +x utils/setup_firewall.sh
   sudo ./utils/setup_firewall.sh
   ```

¡Listo\! La aplicación estará disponible en `https://tu-dominio.duckdns.org`.

---

### Explorando la API

Este proyecto utiliza **PostgREST**, que convierte tu base de datos en una API RESTful. No necesitas escribir código de backend para las operaciones CRUD.

- **Acceso:** La API es interna a la red de Docker. En un entorno de desarrollo, puedes acceder a ella a través del puerto expuesto (`http://localhost:3001`).
- **Endpoints:** Cada tabla y vista de tu esquema `sindicato_inq` se convierte en un endpoint. Por ejemplo, la tabla `afiliadas` es accesible en `/afiliadas`.
- **Consultas:** Puedes usar parámetros de URL para filtrar, ordenar y paginar. Por ejemplo, para obtener las afiliadas del estado "Alta":

`
http://localhost:3001/afiliadas?estado=eq.Alta
`

Para más información, consulta la [documentación oficial de PostgREST](https://postgrest.org/en/stable/api.html).

### Operaciones Comunes

- **Ver los logs:** `docker compose logs -f`
- **Detener la aplicación:** `docker compose down`
- **Actualizar (tras un `git pull`):** `docker compose --profile Secured --profile Frontend up -d --build`
- **Renovar certificados SSL manualmente:** `./utils/renew_certificates.sh`

## 🔐 Seguridad

- **Proxy Inverso:** Nginx es el único punto de entrada, ocultando los servicios internos.
- **Tráfico Cifrado:** HTTPS con certificados SSL de Let's Encrypt gestionados automáticamente.
- **Firewall:** `ufw` restringe el acceso a los puertos 22 (SSH), 80 (HTTP) y 443 (HTTPS).
- **Contraseñas Seguras:** Las contraseñas se almacenan hasheadas utilizando bcrypt.
- **Gestión de Secretos:** No hay claves ni secretos hardcodeados. Todo se gestiona a través de `.env`, que está excluido por `.gitignore`.

## 🧪 Pruebas

El proyecto cuenta con una suite de pruebas automatizadas para garantizar la calidad y estabilidad del código. Las pruebas cubren desde la consistencia entre la BBDD y el metadata de config.py hasta flujos completos de la interfaz de usuario. Para ejecutar la suite de pruebas completa, utiliza el siguiente comando:

```bash
pytest --cov
```

Para obtener una guía detallada sobre cómo configurar el entorno de pruebas y ejecutar diferentes tipos de tests, consulta el documento [guía de testeo](https://github.com/maiktreya/tenantsUnion/blob/main/doc/testing.md).

---

## 🗺️ Hoja de Ruta (Roadmap)

Planes de mejora y futuras implementaciones:

- [ ] **Revisión de Permisos en BBDD:** Auditar y granularizar los permisos a nivel de base de datos en PostgreSQL para un control de acceso más estricto @maiktreya 01-10-2025

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas, sugerencias o quieres colaborar en el desarrollo de este proyecto, no dudes en ponerte en contacto.

**Contacto:** <garciaduchm@gmail.com>

---

## 📄 Licencia

Este proyecto está licenciado bajo la [GNU General Public License v3.0 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.html). Además, el contenido y la documentación asociada se distribuyen bajo una licencia [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).

2025-10-21 @maiktreya
