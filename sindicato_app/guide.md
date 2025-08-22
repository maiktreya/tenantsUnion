
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

## 🚀 Tecnologías Utilizadas

  - **Backend y Frontend**: Python con el framework [NiceGUI](https://nicegui.io/) para una interfaz web rápida.
  - **API**: [PostgREST](http://postgrest.org/) para generar una API RESTful directamente desde la base de datos PostgreSQL.
  - **Base de Datos**: PostgreSQL.

## 🛠️ Cómo Ejecutar la Aplicación

1.  **Clonar el repositorio**:

    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2.  **Instalar dependencias**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar la conexión a la API**:
    Asegúrate de que tu instancia de PostgREST esté corriendo. La aplicación buscará la URL en la variable de entorno `POSTGREST_API_URL`. Si no la encuentra, usará `http://localhost:3001` por defecto.

4.  **Ejecutar la aplicación**:

    ```bash
    python sindicato_app/main.py
    ```

5.  Abre tu navegador y ve a `http://localhost:8081`.

-----