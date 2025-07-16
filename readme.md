# Aplicación de Integración de Pruebas CRUD Restful

## Descripción

Esta es una aplicación mínima para realizar pruebas de integración de una aplicación CRUD Restful. La aplicación está compuesta por tres servicios Docker sin imágenes personalizadas e integra DB + API + UI de manera robusta y minimalista

## Componentes

La aplicación está compuesta por los siguientes servicios:

1. **PostgreSQL (DB)**: Base de datos PostgreSQL que almacena los datos de la aplicación. (defidos en build/postgreSQL/init-scripts/*)
2. **PostgREST (API)**: Servidor PostgREST que expone una API RESTful sobre la base de datos PostgreSQL. (autodocumentada y segura)
3. **NiceGUI (frontend)**: Interfaz de usuario construida con NiceGUI que permite interactuar con la API. (1 fichero .py por claridad de cadena de ejecución)

## Configuración

Para configurar la aplicación, es necesario definir las siguientes variables de entorno en un archivo `.env`:

- `POSTGRES_DB`: Nombre de la base de datos PostgreSQL.
- `POSTGRES_USER`: Nombre de usuario de PostgreSQL.
- `POSTGRES_PASSWORD`: Contraseña de PostgreSQL.
- `POSTGREST_API_URL`: URL del servidor PostgREST.
- `POSTGRES_DB_SCHEMA`: Esquema de la base de datos PostgreSQL.

## Ejecución

Para ejecutar la aplicación, se debe utilizar Docker Compose. Ejecute el siguiente comando en el directorio raíz del proyecto:

```bash
docker-compose up
```

Esto iniciará los tres servicios: **PostgreSQL, PostgREST y NiceGUI.**

## Uso

- Una vez que la aplicación esté en funcionamiento, puede acceder a la interfaz **NiceGUI** de usuario en `http://localhost:8081`. Desde allí, puede interactuar con la API.

- **PostgREST** permite habilitar la creación automatizada de API endpoints para cada una de las tablas de un schema **postgreSQL**.
