# tasks pending of implementation

##  A) PostgreSQL DB

1. Integrate in th DB the table of **nodos** consistently along **cp** and conflics.

   * Nodos should be one level over **bloques** but instead of built over **cp** as  foreign key it uses.

   * The classification of a **bloque** as part of a **nodo** is based in dividing all the **cp** available at madrid region among the existing sindicato nodos.

2. Incorporate separate user authentication and role management (at least 3 tables, **users**, **roles** and **passwords** for a securely stored hashed passwords system).

## B) UI Frontend APP

1. Integrate an straightforward auth layer (preferably annonimized without integration with any major external system)

## C) Data sniffing and other tasks

1. Migrate to a temporal DB the original word from legacy actas system

2. Check Alberto's summary in telegram for any missing feature still not implemented

3. Impelemntar tipos de acciones para los conflictos:
Tipos de acciones para los conflictos
 ⁃ nota simple
 ⁃ nota localización propiedades
 ⁃ deposito fianza
 ⁃ puerta a puerta
 ⁃ comunicación enviada
 ⁃ llamada
 ⁃ acción
 ⁃ reunión de negociación
 ⁃ informe vulnerabilidad
 ⁃ MASC
 ⁃ justicia gratuita
 ⁃ demanda
 ⁃ Sentencia

4. Roles para usuarios (Listado roles db)

* Administrador de todo
 ⁃ remuneradas organización

* Coordinación de comision: Visor de todos datos salvo cuotas:
 ⁃ coordinadoras accion sindical, organización y comunicación
 ⁃ remuneradas accion sindical y comunicación

* Coordinación de sección: Visor de todos los datos de tu territorio o seccion
 ⁃ una por cada coordi de nodo + sección

1. Coger acta:
 ⁃ una por cada nodo
 ⁃ una para bienvenida?

¿como hacer con el punto de apoyo?