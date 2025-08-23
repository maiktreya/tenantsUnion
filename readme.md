
-----

# Sistema de Gestión para el Sindicato de Inquilinas de Madrid

Este proyecto es una aplicación web de escritorio desarrollada para facilitar la gestión interna de la información del **Sindicato de Inquilinas e Inquilinos de Madrid**. La interfaz, construida con **NiceGUI**, ofrece una experiencia de usuario rápida y reactiva para interactuar con una base de datos PostgreSQL a través de una API de PostgREST.

## 📋 Características Principales

La aplicación se organiza en tres módulos principales para cubrir todas las necesidades de gestión de datos:

### 1\. **Administración de BBDD (`ADMIN BBDD`)**

  - **Gestión CRUD Completa**: Permite crear, leer, actualizar y eliminar registros en cualquiera de las tablas de la base de datos.
  - **Relaciones Inteligentes**: Utiliza menús desplegables para los campos que son claves foráneas, facilitando la selección de registros relacionados (por ejemplo, al asignar una `afiliada` a un `conflicto`).
  - **Vista de Detalles Relacionados**: Al hacer clic en una fila, se muestra una vista detallada de los registros en tablas "hijas". Por ejemplo, al seleccionar una `empresa`, se pueden ver los `bloques` asociados a ella.
  - **Importación y Exportación**: Permite la exportación de los datos filtrados a formato **CSV** y la importación de nuevos registros desde archivos CSV.

### 2\. **Explorador de Vistas (`VISTAS`)**

  - **Visualización de Datos Agregados**: Ofrece acceso de solo lectura a vistas materializadas predefinidas en la base de datos, ideales para consultar información consolidada sin riesgo de modificación.
  - **Filtros y Búsqueda**: Permite filtrar y buscar datos dentro de estas vistas para un análisis más ágil.
  - **Exportación a CSV**: La información consultada en las vistas también puede ser exportada fácilmente.

### 3\. **Gestor de Conflictos (`CONFLICTOS`)**

  - **Módulo Especializado**: Una interfaz diseñada específicamente para la gestión de conflictos.
  - **Toma de Actas y Seguimiento**: Permite seleccionar un conflicto existente y añadir notas o actualizaciones a su historial (`diario_conflictos`).
  - **Edición y Borrado de Notas**: Las entradas del historial pueden ser editadas o eliminadas.
  - **Actualización Automática**: Al añadir una nota con el estado **"Cerrado"**, la `fecha_cierre` del conflicto principal se actualiza automáticamente.

## 🏗️ Arquitectura y Tecnologías

El sistema implementa una arquitectura de **3 microservicios** con una clara separación de responsabilidades.

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   NiceGUI       │    │  PostgREST   │    │   PostgreSQL    │
│   Frontend      │◄──►│   API        │◄──►│   Database      │
│   (Puerto 8081) │    │  (Puerto 3001) │    │   (Puerto 5432) │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

  - **Frontend**: Python con el framework [NiceGUI](https://nicegui.io/) para una interfaz web rápida y reactiva.
  - **API**: [PostgREST](http://postgrest.org/) para generar una API RESTful directamente desde la base de datos PostgreSQL.
  - **Base de Datos**: PostgreSQL 15.
  - **Orquestación**: Docker Compose para gestionar los servicios.

## 🛠️ Cómo Ejecutar la Aplicación

1.  **Clonar el repositorio**:

    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2.  **Configurar las variables de entorno**:
    Crea un archivo `.env` en la raíz del proyecto basándote en el fichero `.env` que ya existe y modifica los valores si es necesario.

3.  **Ejecutar la aplicación con Docker Compose**:
    Asegúrate de tener Docker instalado y ejecuta el siguiente comando:

    ```bash
    docker-compose up
    ```

4.  **Acceder a la aplicación**:
    Abre tu navegador y ve a `http://localhost:8081`.

## 📊 Modelo de Datos

El modelo de datos está bien normalizado y sigue una jerarquía lógica para representar las entidades del mundo real.

#### Jerarquía Principal

```
Entramado Empresas → Empresas → Bloques → Pisos → Afiliadas
```

#### Tablas Principales

  - **Entramado Empresas**: Grupos o redes de empresas inmobiliarias.
  - **Empresas**: Propietarios o gestores de propiedades individuales.
  - **Bloques**: Edificios completos.
  - **Pisos**: Unidades de vivienda individuales.
  - **Afiliadas**: Miembros del sindicato.
  - **Usuarios**: Personal del sindicato que utiliza el sistema.
  - **Conflictos**: Disputas y su seguimiento.
  - **Asesorías**: Consultas y servicios de asesoramiento.
  - **Facturación**: Gestión de cuotas de las afiliadas.

## 🌐 Endpoints de la API (Vistas Materializadas)

Para optimizar el rendimiento y simplificar las consultas desde el frontend, la API de PostgREST expone varias **vistas materializadas**. Estas vistas denormalizan los datos uniendo varias tablas para ofrecer endpoints estables y eficientes.

  - `v_afiliadas`: Ofrece una vista completa y aplanada de cada afiliada, uniendo información de `facturacion`, `pisos`, `bloques` y `empresas`.
  - `v_empresas`: Muestra información de las empresas y añade un conteo de las afiliadas asociadas a cada una.
  - `v_bloques`: Similar a la vista de empresas, pero centrada en los bloques, con un conteo de afiliadas por bloque.
  - `v_conflictos_con_afiliada`: Enriquece la tabla de conflictos con el nombre completo de la afiliada asociada, evitando consultas adicionales.
  - `v_diario_conflictos_con_afiliada`: Añade el nombre de la afiliada a las entradas del historial de conflictos.