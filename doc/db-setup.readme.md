---

# Guía de Construcción del Esquema de la Base de Datos

---
Este documento describe el proceso paso a paso utilizado para construir y poblar el esquema de la base de datos PostgreSQL de la app. El proceso está automatizado a través de una serie de scripts SQL ordenados ubicados en el directorio `/build/postgreSQL/init-scripts/`.


(**NOTA:** Muchas de las tablas de la versión interior se han ignorado directamente por ser **a) innecesarias** o redundantes **b) inconsistentes** desde el punto de vista de la integridad relacional de los datos **c) vulnerables** desde el punto de vista de la seguridad, como el almacenamiento en texto plano de passwords).

* **El paso 1** se limita a **migrar y replicar parcialmente** la estructura y los datos ya existentes en la BBDD anterior.
* Los **pasos 2 a 5** definen **nuevas tablas y relaciones** no existentes en la versión actual de la BBDD

## Paso 1: Esquema Central y Migración de Datos (`01-init-schema-and-data.sql`)

Este es el script fundamental que establece la estructura de la base de datos y realiza la migración inicial de datos desde los archivos CSV heredados. Desde la antigua base de datos

1.  **Creación del Esquema**: Comienza creando el esquema principal, `sindicato_inq`, para encapsular todos los objetos de la base de datos.
2.  **Definición de Tablas**: El script define las tablas finales y normalizadas para la aplicación, incluyendo `empresas`, `bloques`, `pisos`, `afiliadas`, `conflictos` y `usuarios`. La integridad referencial se establece mediante el uso de claves foráneas.
3.  **Área de Staging (Temporal)**: Se crean tablas temporales de `staging` para replicar la estructura de los archivos CSV de origen (`Afiliadas.csv`, `Empresas.csv`, etc.).
4.  **Ingesta de Datos**: El comando `COPY` se utiliza para cargar de manera eficiente los datos en bloque desde los archivos CSV a sus correspondientes tablas de staging.
5.  **Migración y Transformación de Datos**: Se utilizan sentencias `INSERT INTO ... SELECT` para migrar los datos desde las tablas de staging a las tablas finales y normalizadas. Este paso incluye:
    * Transformar y limpiar datos (por ejemplo, convertir representaciones de texto de números a tipos numéricos).
    * Resolver relaciones buscando los IDs de las claves foráneas en los registros recién insertados.
6.  **Limpieza**: Las tablas de staging temporales se eliminan una vez que se completa la migración de datos.
7.  **Indexación**: Para garantizar el rendimiento de las consultas, se crean índices en todas las columnas de clave foránea.

---

## Paso 2: Nodos Territoriales (`02-init-nodos.sql` & `05-populate-nodes-cps.sql`)

Esta etapa introduce el concepto de "Nodos" (agrupaciones territoriales) para organizar los datos geográficamente.

1.  **Tablas de Nodos**: El script `02-init-nodos.sql` crea dos nuevas tablas:
    * `nodos`: Almacena los nombres y descripciones de los nodos territoriales (ej. 'Centro-Arganzuela-Retiro', 'Latina').
    * `nodos_cp_mapping`: Mapea códigos postales (`cp`) a un `nodo_id` específico.
2.  **Optimización de Rendimiento**: Se añade una columna `nodo_id` directamente a la tabla `bloques`. Esta desnormalización es una decisión deliberada para mejorar el rendimiento y evitar uniones complejas en consultas comunes.
3.  **Sincronización Automática**: Una característica clave es una función `trigger` (`sync_bloque_nodo`). Esta función actualiza automáticamente el `nodo_id` en un `bloque` cada vez que un `piso` vinculado a él se inserta o actualiza su código postal, asegurando la consistencia de los datos.
4.  **Población de Datos**: El script `05-populate-nodes-cps.sql` luego rellena estas tablas con los nodos específicos y sus correspondientes mapeos de códigos postales para la Comunidad de Madrid.

---

## Paso 3: Autenticación y Autorización de Usuarios (`03-init-userAuth.sql`)

Este script construye la infraestructura necesaria para la gestión de usuarios y el control de acceso.

1.  **Tablas de Autenticación**: Se crean tres tablas dentro del esquema `sindicato_inq`:
    * `usuario_credenciales`: Almacena los IDs de usuario y sus correspondientes contraseñas hasheadas.
    * `roles`: Una tabla simple para definir los roles de usuario disponibles (ej. `admin`, `gestor`).
    * `usuario_roles`: Una tabla de mapeo que vincula a los usuarios con los roles que tienen asignados, permitiendo una relación de muchos a muchos.
2.  **Datos por Defecto**: El script inserta roles por defecto ('admin', 'gestor') y establece una contraseña hasheada por defecto para el usuario administrador inicial, permitiendo el inicio de sesión inmediato después de configurar el sistema.

---

## Paso 4: Vistas para la Presentación de Datos (`04-init-views.sql`)

Para simplificar las consultas del frontend y mejorar el rendimiento, este script crea varias vistas de base de datos.

1.  **Creación de Vistas**: Se ejecuta una serie de sentencias `CREATE OR REPLACE VIEW`.
2.  **Desnormalización**: Estas vistas unen múltiples tablas para proporcionar una visión aplanada y completa de los datos. Por ejemplo, `v_afiliadas` combina información de `afiliadas`, `pisos`, `bloques` y `empresas` para presentar un registro completo de cada afiliada.
3.  **Propósito**: El objetivo principal es proporcionar fuentes de datos listas para usar para el "Explorador de Vistas" de la aplicación y otros módulos, reduciendo la necesidad de agregaciones de datos complejas en el lado del cliente.

---

## Paso 5: Población de Datos de Soporte (`05-populate-nodes-cps.sql`)

Finalmente, este script puebla tablas de consulta esenciales que fueron creadas en los pasos anteriores.

1.  **Tabla de Acciones**: Inserta una lista predefinida de acciones (`nota simple`, `llamada`, `demanda`, etc.) en la tabla `acciones`. Esto proporciona las opciones estandarizadas disponibles al añadir una entrada en el `diario_conflictos`.
2.  **Datos de Nodos y CPs**: Como se mencionó en el Paso 2, este script es responsable de rellenar las tablas `nodos` y `nodos_cp_mapping` con los datos geográficos reales.