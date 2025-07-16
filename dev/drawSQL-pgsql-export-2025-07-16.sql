CREATE TABLE "afiliadas" (
    "id" BIGINT NOT NULL,
    "n_afiliado" BIGINT NOT NULL,
    "nif" TEXT NOT NULL
);

CREATE TABLE "pisos" (
    "id" BIGINT NOT NULL,
    "direccion" TEXT NOT NULL,
    "cp" INTEGER NOT NULL,
    "new_column" BIGINT NOT NULL
);

CREATE TABLE "bloques" ("id" BIGINT NOT NULL);

CREATE TABLE "conflictos" ("id" BIGINT NOT NULL);

CREATE TABLE "empresas" ("id" BIGINT NOT NULL);

CREATE TABLE "diario_conflictos" ("id" BIGINT NOT NULL);

CREATE TABLE "entramado_empresas" ("id" BIGINT NOT NULL);

CREATE TABLE "facturacion" (
    "id" BIGINT NOT NULL,
    "Cuota" DECIMAL(8, 2) NOT NULL,
    "Periodicidad" SMALLINT NOT NULL,
    "IBAN" TEXT NOT NULL
);

CREATE TABLE "solicitudes" ("id" BIGINT NOT NULL);

CREATE TABLE "usuarios" ("id" BIGINT NOT NULL);