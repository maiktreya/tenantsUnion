# Tables description from Madrid Tenants Union

## DB definition in compose file

```bash
services:

  server:
    image: postgrest/postgrest:v12.2.8
    ports:
      - "3001:3000"
    environment:
      PGRST_DB_URI: postgres://app_user:password@db:5432/tenants_union_db
      PGRST_OPENAPI_SERVER_PROXY_URI: http://server:3000
      PGRST_DB_ANON_ROLE: app_user
      PGRST_DB_SCHEMA: idealista_scrapper
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    build:
      context: ./build/postgreSQL
      dockerfile: Dockerfile
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: tenants_union_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: password
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - ./build/postgreSQL/init-scripts:/docker-entrypoint-initdb.d
      - /mnt/pgdata:/var/lib/postgresql/data
    command: >
      postgres -c shared_preload_libraries='pg_cron'
               -c cron.database_name='tenants_union_db'
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U app_user -d tenants_union_db" ]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
volumes:
  datatest:
```

## Table setup

### 1. Afiliadas

Núm.Afiliada
Nombre
Apellidos
CIF
Género
Cuota
Frecuencia de Pago
Forma de Pago
Cuenta Corriente
Régimen
Estado
inmobiliaria_id
Propiedad
entramado_id

### 2. Pisos
Dirección


### 3. Bloques

### 4. Conflictos

### 4b. Histórico conflictos

### 5a. Empresas intermediarias

### 5b. Empresas propietarias


### 7. Solicitudes
N_afiliado
Solicitud
f_solicitud
notas
eina_si
brevo_si

### 8. Control económico
