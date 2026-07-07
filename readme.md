# Sistema de Gestión para un Sindicato de Inquilinas (`readme.md`)

Este proyecto es una aplicación web de escritorio completa (full-stack) desarrollada para facilitar el registro de información interna, el mapeo de relaciones de propiedad y el análisis automatizado de datos para el **Sindicato de Inquilinas**. La interfaz, construida de forma nativa con **NiceGUI**, ofrece un panel de control interactivo y reactivo respaldado por una base de datos relacional PostgreSQL robustecida con la extensión espacial PostGIS.

El modelo de ingesta de datos del sistema está impulsado por un **pipeline ETL (Extracción, Transformación y Carga) asíncrono y desatendido**. Esta arquitectura automatizada elimina los antiguos cuellos de botella operativos de las interfaces de importación manuales en el navegador, ejecutándose de forma independiente en segundo plano para extraer, formatear, geolocalizar y limpiar los formularios descentralizados con un alto nivel de consistencia.

---

## 🏛️ Arquitectura

El sistema implementa una arquitectura segura de tres capas, totalmente aislada dentro de un ecosistema de contenedores Docker. Esta estructura maximiza la encapsulación de los datos y garantiza la reproducibilidad del despliegue tanto en entornos locales de desarrollo como en servidores de producción securizados.

```mermaid
graph TD
    subgraph "Capa del Cliente"
        A[Usuario en el Navegador Web]
    end

    subgraph "Servidor Seguro Contenedorizado"
        B[Cortafuegos UFW Restricciones del Host <br> Puertos: 22 / 80 / 443]
        C[Proxy Inverso Nginx <br> Terminación Criptográfica SSL/TLS]
        D[Motor de la Aplicación NiceGUI <br> Contexto Python / FastAPI / Quasar]
        E[Pasarela de Datos de la API PostgREST]
        F[Almacenamiento Relacional PostgreSQL <br> PostGIS / Vistas / Seguridad RLS]
    end

    subgraph "Pipeline Asíncrono de Datos Externos"
        G[Motor de Cron Diario del Sistema <br> Planificación de Ejecución 0 2 * * *]
        H[BD Remota de WordPress / Gravity Forms]
        I[API Externa de Geocodificación CartoCiudad]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E <--> F
    G -->|1. Túnel SSH Seguro y Extracción| H
    G -->|2. Estandarización y Geocodificación| I
    G -->|3. Ingesta mediante COPY de Alto Rendimiento| F

```

* **Capa de Presentación (NiceGUI):** Un framework de Python de alto rendimiento construido sobre FastAPI y Vue/Quasar. Centraliza los componentes de la interfaz y las capas de estado directamente en módulos de Python limpios y tipados, eliminando la necesidad de escribir código separado en JavaScript, HTML o CSS.
* **Pasarela de la API (PostgREST):** Elimina las tareas rutinarias de programación del backend al convertir dinámicamente el esquema de la base de datos, sus tablas y sus relaciones directamente en puntos de enlace (endpoints) RESTful completamente accesibles.
* **Capa de Datos y Espacial (PostgreSQL + PostGIS):** Actúa como la única fuente de verdad autoritativa para todo el estado del sistema. Las restricciones de negocio, los controles de acceso, el indexado espacial, el auditado automático de fechas y las métricas de seguimiento se implementan directamente en la base de datos mediante funciones PL/pgSQL nativas, vistas, disparadores (triggers) y políticas de Seguridad a Nivel de Fila (RLS).
* **Automatización de Ingesta (ETL Desatendido):** Una rutina modular en segundo plano programada mediante el script `utils/cron/daily_sync.sh` que abre un túnel SSH seguro hacia el entorno remoto, aísla los nuevos registros de afiliación, estandariza las cadenas de texto introducidas manualmente por los usuarios, añade coordenadas geográficas y consolida las actualizaciones en PostgreSQL.

---

## ⭐ Características Principales

La consola de administración organiza sus funciones en interfaces modulares, otorgando visibilidad sobre los nodos del sistema mediante permisos de consulta basados en roles:

* **Consola de Administración de la Base de Datos (`ADMIN BBDD`):**
* Control completo de operaciones CRUD (Crear, Leer, Actualizar, Borrar) en todas las tablas con menús de selección y resolución automática de claves foráneas.
* Explorador de relaciones interactivo para navegar de forma fluida entre registros padre e hijo.
* Rutinas de diagnóstico localizadas para la importación y exportación de datos utilizando archivos con estructura CSV estándar.


* **Análisis de Vistas Materializadas (`VISTAS`):**
* Vistas administrativas de solo lectura que exponen bloques de datos analíticos complejos y consolidados para la coordinación del sindicato.
* Sistema rápido de filtrado multiparámetro del lado del cliente, índices de búsqueda de texto y configuraciones de ordenación dinámica de columnas.


* **Seguimiento de Conflictos y Organización (`CONFLICTOS`):**
* Módulo especializado diseñado específicamente para registrar, etiquetar y supervisar los conflictos sindicales de vivienda, las novedades de los caseros y los hitos de organización colectiva.
* Historiales automatizados que registran notas, actualizaciones legales y cambios de estado del caso con validación inmutable de marcas de tiempo.


* **Motor ETL Espacial Automatizado (Sincronización con Gravity Forms):**
* Un sistema de sincronización autónomo en segundo plano que se ejecuta en un ciclo diario mediante tareas cron.
* Realiza un reenvío seguro de puertos por SSH para extraer las nuevas inscripciones de la base de datos remota de WordPress, limpiando cadenas de texto y des-pivotando los metadatos estructurados.
* Aplica un marco de emparejamiento de direcciones de varias etapas que consulta la **API de CartoCiudad** para adjuntar coordenadas de latitud/longitud precisas y Referencias Catastrales oficiales españolas (`ref_catastral`).
* Utiliza cargas de alta velocidad en tablas de staging y reglas de actualización condicional (`UPSERT`) para procesar bloques de propiedades de propiedad vertical (`bloques`), unidades de vivienda (`pisos`), datos de facturación (`facturacion`) e información de las afiliadas.


* **Seguridad e Identidad:**
* Credenciales de usuario encriptadas y protegidas mediante funciones de hash criptográfico adaptativo (`bcrypt`).
* Control de Acceso Basado en Roles (RBAC) estricto que separa las funciones de administración, los gestores de casos regionales y los auditores de solo lectura.
* Seguridad a Nivel de Fila (RLS) integrada en la base de datos que valida tokens web JSON (JWT) activos para proteger los datos organizativos sensibles frente a consultas no autorizadas.



---

## 🚀 Tecnologías Utilizadas

| Capa / Componente | Motor Tecnológico Especializado | Propósito Concreto en el Ecosistema |
| --- | --- | --- |
| **Interfaz de Usuario** | NiceGUI (Sobre FastAPI y Uvicorn) | Renderiza los paneles de control reactivos unificados en Python. |
| **Pasarela de la API** | Servidor PostgREST | Genera automáticamente endpoints REST de baja latencia desde el esquema. |
| **Base de Datos Core** | Servidor PostgreSQL | Proporciona almacenamiento relacional duradero y lógica de restricciones. |
| **Motor Geoespacial** | Extensión PostGIS | Gestiona el mapeo de coordenadas geográficas e indexación espacial. |
| **Capa de Contenedores** | Docker / Docker Compose | Aísla, empaqueta y construye los microservicios independientes. |
| **Seguridad de Acceso** | Plantilla de Proxy Inverso Nginx | Centraliza el tráfico de entrada, oculta servicios y limita conexiones. |
| **Automatización SSL** | Let's Encrypt + Certbot | Automatiza los ciclos de renovación para conexiones TLS seguras. |
| **Resolver de Direcciones** | Motor de la API de CartoCiudad | Proporciona coordenadas espaciales y validación catastral oficial. |
| **Protección del Host** | Uncomplicated Firewall (UFW) | Restringe los accesos del servidor externo a los puertos 22, 80 y 443. |

---

## 🛠️ Despliegue e Instalación

### Inicio Rápido (Modo de Desarrollo Local)

Esta configuración inicializa los servicios de software localmente en tu máquina, expone las interfaces de la base de datos y la API para su inspección, y carga un conjunto de datos sintéticos de prueba.

1. **Clona la instancia del repositorio objetivo:**
```bash
git clone https://github.com/maiktreya/tenantsUnion.git
cd tenantsUnion

```


2. **Inicializa tu archivo de entorno de desarrollo:**
Copia el archivo de ejemplo a un archivo `.env` definitivo:
```bash
cp .env.example .env

```

1. **Levanta el perfil del entorno de desarrollo:**
Ejecuta el comando de Compose con múltiples archivos para habilitar la recarga en caliente, asignar volúmenes de desarrollo e iniciar los contenedores:
```bash
docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --renew-anon-volumes

```


4. **Puntos de Enlace Locales:**
* **Panel de Gestión:** `http://localhost:8081`
* **Explorador de la API:** `http://localhost:3001/afiliadas`
* **Base de Datos Nativa:** `postgresql://app_user:password@localhost:5432/mydb`



---

### Despliegue en Producción (Configuración SSL Segura)

Sigue estas instrucciones para ejecutar la aplicación en un servidor en la nube expuesto a internet con cortafuegos activos, proxies inversos automatizados y certificados TLS válidos.

1. **Clona e ingresa al contexto del repositorio:**
```bash
git clone https://github.com/maiktreya/tenantsUnion.git
cd tenantsUnion

```


2. **Configura las claves del entorno de producción:**
Copia la plantilla a un archivo `.env` e introduce tus indicadores únicos de dominio, tokens de seguridad y correos de contacto administrativo:
```dotenv

# Perfiles de Enrutamiento DNS del Servidor de Producción
HOSTNAME=tu-dominio.duckdns.org
DUCKDNS_TOKEN=tu-token-de-duckdns
EMAIL=tu-email@ejemplo.com

```


3. **Arranca los certificados de Let's Encrypt:**
Ejecuta el script de inicialización de certificados para establecer las credenciales criptográficas de tu servidor. **Este paso solo es necesario en el primer despliegue del proyecto:**
```bash
chmod +x utils/init-letsencrypt.sh
./utils/init-letsencrypt.sh

```


4. **Lanza los contenedores de producción securizados:**
Inicia las pilas de servicios bajo el perfil de entorno de red securizado de producción (`Secured`):
```bash
docker compose --profile Secured up -d

```


5. **Habilita las protecciones de red a nivel de host:**
Cierra los puertos innecesarios del servidor utilizando el script automatizado de configuración de cortafuegos provisto:
```bash
chmod +x utils/setup_firewall.sh
sudo ./utils/setup_firewall.sh

```



¡Listo! El panel de control de la aplicación estará activo y accesible de forma segura a través de HTTPS en `https://tu-dominio.duckdns.org`.

---

## 🧪 Suite de Pruebas

Puedes ver más en detalle como desplegar la versión de desarrollo de esta aplicación [Aquí](https://github.com/maiktreya/tenantsUnion/blob/main/doc/first_run.md).

El sistema incluye un marco integral de pruebas automatizadas impulsado por `pytest`. Esta suite valida los mecanismos de restricciones de la base de datos, los permisos de acceso JWT, los patrones de saneamiento de direcciones y el correcto renderizado de los flujos de la interfaz de usuario.

Para ejecutar las pruebas del sistema en tu entorno de desarrollo y revisar las matrices de cobertura de código, ejecuta:

```bash
pytest --cov

```

Para consultar los pasos detallados de configuración del entorno e instrucciones sobre la ejecución de pasadas de integración aisladas, revisa la [Documentación Test & Pruebas](https://github.com/maiktreya/tenantsUnion/blob/main/doc/testing.md).

---

## 🤝 Contribuciones y Contacto

Cualquier revisión, propuesta de mejora o modificación de código por parte de la comunidad es bienvenida. Para discutir cambios de diseño, problemas de escala o coordinar contribuciones, abre una tarjeta de issue o envía una solicitud de pull request.

**Contacto de Infraestructura Principal:** [garciaduchm@gmail.com](https://www.google.com/search?q=mailto%3Agarciaduchm%40gmail.com)

---

## 📄 Licencia

La arquitectura de este software y su código fuente se distribuyen bajo los términos de la **Licencia Pública General GNU v3.0 (GPLv3)**. Las hojas de documentación técnica, los diagramas estructurales y los materiales de recursos asociados se comparten bajo el marco de la licencia **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.