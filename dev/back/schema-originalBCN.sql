-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Servidor: localhost
-- Temps de generació: 16-07-2025 a les 18:22:25
-- Versió del servidor: 8.0.41-32
-- Versió de PHP: 8.2.29

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de dades: `sindica7_bo`
--

-- --------------------------------------------------------

--
-- Estructura de la taula `afiliada_historic_regims`
--

CREATE TABLE `afiliada_historic_regims` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `pis` int DEFAULT NULL,
  `adreca_no_normalitzada` tinyint DEFAULT NULL,
  `adreca_no_normalitzada_text` varchar(400) DEFAULT NULL,
  `data_inici_contracte` datetime DEFAULT NULL,
  `contracte_indefinit` tinyint DEFAULT NULL,
  `durada_contracte` decimal(2,0) DEFAULT NULL,
  `durada_contracte_prorrogues` decimal(1,0) DEFAULT NULL,
  `renda_contracte` decimal(6,2) DEFAULT NULL,
  `num_habitants` decimal(2,0) DEFAULT NULL,
  `ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `data_fi_regim` datetime NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `afiliades`
--

CREATE TABLE `afiliades` (
  `id` int NOT NULL,
  `cif` varchar(20) NOT NULL,
  `persona` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `data_alta` datetime NOT NULL,
  `data_baixa` datetime DEFAULT NULL,
  `origen_afiliacio` int DEFAULT NULL,
  `nivell_participacio` int DEFAULT NULL,
  `comissio` int DEFAULT NULL,
  `forma_pagament` varchar(1) DEFAULT NULL,
  `compte_corrent` varchar(24) DEFAULT NULL,
  `quota` decimal(5,2) DEFAULT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `pis` int DEFAULT NULL,
  `data_inici_contracte` datetime DEFAULT NULL,
  `durada_contracte` decimal(2,0) DEFAULT NULL,
  `renda_contracte` decimal(6,2) DEFAULT NULL,
  `num_habitants` decimal(2,0) DEFAULT NULL,
  `ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `collectiu` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `contracte_indefinit` tinyint DEFAULT NULL,
  `durada_contracte_prorrogues` decimal(1,0) DEFAULT NULL,
  `comentaris` text,
  `adreca_no_normalitzada` tinyint DEFAULT NULL,
  `adreca_no_normalitzada_text` varchar(400) DEFAULT NULL,
  `frequencia_pagament` varchar(1) DEFAULT NULL,
  `seccio_sindical` int NOT NULL,
  `data_seguiment` datetime DEFAULT NULL,
  `tipus_seguiment` int DEFAULT NULL,
  `observacions_estat` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `afiliades_delegades_conflicte`
--

CREATE TABLE `afiliades_delegades_conflicte` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `agrupacions_blocs`
--

CREATE TABLE `agrupacions_blocs` (
  `id` int NOT NULL,
  `nom` varchar(200) NOT NULL,
  `propietat` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `api` int DEFAULT NULL,
  `propietat_any_actualitzacio` decimal(4,0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `assessoraments`
--

CREATE TABLE `assessoraments` (
  `id` int NOT NULL,
  `afiliada` int DEFAULT NULL,
  `tipus` int NOT NULL,
  `tecnica` int DEFAULT NULL,
  `data_assessorament` datetime DEFAULT NULL,
  `descripcio` text,
  `comentaris` text,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `status` varchar(50) NOT NULL,
  `data_contacte` datetime DEFAULT NULL,
  `data_finalitzacio` datetime DEFAULT NULL,
  `resultat` int DEFAULT NULL,
  `tipus_beneficiaria` varchar(1) NOT NULL DEFAULT 'A',
  `no_afiliada` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `assessorament_documents`
--

CREATE TABLE `assessorament_documents` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `document` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `blocs`
--

CREATE TABLE `blocs` (
  `id` int NOT NULL,
  `google_id` varchar(400) NOT NULL,
  `adreca` varchar(400) NOT NULL,
  `nom_via` varchar(200) NOT NULL,
  `numero` varchar(20) NOT NULL,
  `municipi` int NOT NULL,
  `codi_postal` varchar(5) NOT NULL,
  `estat` int DEFAULT NULL,
  `any_construccio` decimal(4,0) DEFAULT NULL,
  `num_habitatges` decimal(3,0) DEFAULT NULL,
  `num_locals` decimal(3,0) DEFAULT NULL,
  `propietat_vertical` varchar(1) DEFAULT NULL,
  `ascensor` varchar(1) DEFAULT NULL,
  `parquing` varchar(1) DEFAULT NULL,
  `buit` varchar(1) DEFAULT NULL,
  `data_buit` datetime DEFAULT NULL,
  `api` int DEFAULT NULL,
  `propietat` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `superficie` decimal(5,0) DEFAULT NULL,
  `propietat_ultima_actualitzacio` datetime DEFAULT NULL,
  `propietat_any_actualitzacio` decimal(4,0) DEFAULT NULL,
  `observacions` varchar(200) DEFAULT NULL,
  `hpo` varchar(1) DEFAULT NULL,
  `data_fi_hpo` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `blocs_agrupacio_blocs`
--

CREATE TABLE `blocs_agrupacio_blocs` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `bloc` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `blocs_entramat`
--

CREATE TABLE `blocs_entramat` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `blocs_importats`
--

CREATE TABLE `blocs_importats` (
  `id` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `nom_via_original` varchar(200) DEFAULT NULL,
  `numero_original` varchar(20) DEFAULT NULL,
  `municipi_original` varchar(200) DEFAULT NULL,
  `codi_postal_original` varchar(5) DEFAULT NULL,
  `adreca_original` varchar(400) DEFAULT NULL,
  `google_id` varchar(400) DEFAULT NULL,
  `adreca` varchar(400) DEFAULT NULL,
  `nom_via` varchar(200) DEFAULT NULL,
  `numero` varchar(20) DEFAULT NULL,
  `municipi` int DEFAULT NULL,
  `codi_postal` varchar(5) DEFAULT NULL,
  `estat` int DEFAULT NULL,
  `any_construccio` decimal(4,0) DEFAULT NULL,
  `num_habitatges` decimal(3,0) DEFAULT NULL,
  `num_locals` decimal(3,0) DEFAULT NULL,
  `propietat_vertical` varchar(1) DEFAULT NULL,
  `superficie` decimal(5,0) DEFAULT NULL,
  `ascensor` varchar(1) DEFAULT NULL,
  `parquing` varchar(1) DEFAULT NULL,
  `buit` varchar(1) DEFAULT NULL,
  `data_buit` datetime DEFAULT NULL,
  `cif_api_original` varchar(20) DEFAULT NULL,
  `api_original` varchar(200) DEFAULT NULL,
  `cif_propietat_original` varchar(20) DEFAULT NULL,
  `propietat_original` varchar(200) DEFAULT NULL,
  `api` int DEFAULT NULL,
  `propietat` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `propietat_ultima_actualitzacio` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `causes_conflicte`
--

CREATE TABLE `causes_conflicte` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `changes_log`
--

CREATE TABLE `changes_log` (
  `id` int NOT NULL,
  `object` varchar(200) NOT NULL,
  `object_id` int NOT NULL,
  `child_table` varchar(50) DEFAULT NULL,
  `child_table_id` int DEFAULT NULL,
  `operation` varchar(1) DEFAULT NULL,
  `timestamp` timestamp NOT NULL,
  `user` int NOT NULL,
  `changes` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `collaboradores_collectiu`
--

CREATE TABLE `collaboradores_collectiu` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `collectius`
--

CREATE TABLE `collectius` (
  `id` int NOT NULL,
  `nom` varchar(200) NOT NULL,
  `descripcio` text,
  `email` varchar(150) NOT NULL,
  `telefon` varchar(50) DEFAULT NULL,
  `persona_contacte` varchar(200) DEFAULT NULL,
  `telefon_persona_contacte` varchar(50) DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `cobraments` tinyint DEFAULT '0',
  `assessoraments` tinyint DEFAULT '0',
  `quota` decimal(5,2) DEFAULT NULL,
  `num_serie` varchar(8) DEFAULT NULL,
  `domiciliacions` tinyint DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `comissions`
--

CREATE TABLE `comissions` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `conflictes`
--

CREATE TABLE `conflictes` (
  `id` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `ambit` varchar(1) NOT NULL,
  `afiliada_afectada` int DEFAULT NULL,
  `bloc_afectat` int DEFAULT NULL,
  `entramat_afectat` int DEFAULT NULL,
  `delegada` int DEFAULT NULL,
  `causa` int NOT NULL,
  `data_obertura` datetime NOT NULL,
  `data_darrera_assemblea` datetime DEFAULT NULL,
  `data_hivernacio` datetime DEFAULT NULL,
  `data_tancament` datetime DEFAULT NULL,
  `data_proper_desnonament` datetime DEFAULT NULL,
  `demanda` tinyint DEFAULT NULL,
  `registre_propietat` tinyint DEFAULT NULL,
  `assemblea` tinyint DEFAULT NULL,
  `carta_enviada` tinyint DEFAULT NULL,
  `embustiada` tinyint DEFAULT NULL,
  `accions` tinyint DEFAULT NULL,
  `accions_descripcio` varchar(400) DEFAULT NULL,
  `resolucio` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `agrupacio_blocs_afectada` int DEFAULT NULL,
  `no_afiliada_afectada` int DEFAULT NULL,
  `oficina_habitatge` tinyint DEFAULT NULL,
  `serveis_socials` tinyint DEFAULT NULL,
  `justicia_gratuita` tinyint DEFAULT NULL,
  `taula_emergencia` tinyint DEFAULT NULL,
  `padro_municipal` tinyint DEFAULT NULL,
  `informe_exclusio_residencial` tinyint DEFAULT NULL,
  `afiliades_delegades` text,
  `trucada_propietat` tinyint DEFAULT NULL,
  `simpatitzant_afectada` int DEFAULT NULL,
  `informe_vulnerabilitat` tinyint DEFAULT NULL,
  `reunions_negociacio` tinyint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `directius`
--

CREATE TABLE `directius` (
  `id` int NOT NULL,
  `nom` varchar(200) NOT NULL,
  `descripcio` text,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `directius_empresa`
--

CREATE TABLE `directius_empresa` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `domiciliacions`
--

CREATE TABLE `domiciliacions` (
  `id` int NOT NULL,
  `data_emissio` datetime DEFAULT NULL,
  `fitxer` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `empreses`
--

CREATE TABLE `empreses` (
  `id` int NOT NULL,
  `cif` varchar(20) DEFAULT NULL,
  `nom` varchar(100) NOT NULL,
  `api` tinyint DEFAULT NULL,
  `web` varchar(200) DEFAULT NULL,
  `email` text,
  `telefon` varchar(50) DEFAULT NULL,
  `google_id` varchar(400) DEFAULT NULL,
  `adreca` varchar(400) DEFAULT NULL,
  `nom_via` varchar(200) DEFAULT NULL,
  `numero` varchar(20) DEFAULT NULL,
  `escala` varchar(10) DEFAULT NULL,
  `pis` varchar(10) DEFAULT NULL,
  `porta` varchar(10) DEFAULT NULL,
  `complement` varchar(50) DEFAULT NULL,
  `municipi` int DEFAULT NULL,
  `codi_postal` varchar(5) DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `web_info_empresa` varchar(200) DEFAULT NULL,
  `entramat` int DEFAULT NULL,
  `descripcio` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `entramats`
--

CREATE TABLE `entramats` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `descripcio` text,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `especialitats`
--

CREATE TABLE `especialitats` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `estats_habitatge`
--

CREATE TABLE `estats_habitatge` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `nom_es` varchar(50) DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `groups`
--

CREATE TABLE `groups` (
  `id` int NOT NULL,
  `code` varchar(20) NOT NULL,
  `title` varchar(150) NOT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `import_templates`
--

CREATE TABLE `import_templates` (
  `id` int NOT NULL,
  `import` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `content` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `interessades`
--

CREATE TABLE `interessades` (
  `id` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `genere` varchar(1) DEFAULT NULL,
  `nom` varchar(100) DEFAULT NULL,
  `cognoms` varchar(100) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `telefon` varchar(50) DEFAULT NULL,
  `butlleti` tinyint DEFAULT '1',
  `no_rebre_info` tinyint DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `medias`
--

CREATE TABLE `medias` (
  `id` int NOT NULL,
  `file_name` varchar(400) NOT NULL,
  `hash` varchar(100) NOT NULL,
  `title` varchar(100) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `is_image` tinyint DEFAULT NULL,
  `is_public` tinyint DEFAULT NULL,
  `file_size` decimal(12,0) NOT NULL,
  `image_width` decimal(5,0) DEFAULT NULL,
  `image_height` decimal(5,0) DEFAULT NULL,
  `mime_type` varchar(100) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `image_quality` int DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `municipis`
--

CREATE TABLE `municipis` (
  `id` int NOT NULL,
  `nom` varchar(200) NOT NULL,
  `provincia` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `negociacions_conflicte`
--

CREATE TABLE `negociacions_conflicte` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `data` datetime NOT NULL,
  `estat` text NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `tasques` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `nivells_participacio`
--

CREATE TABLE `nivells_participacio` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `no_afiliades`
--

CREATE TABLE `no_afiliades` (
  `id` int NOT NULL,
  `persona` int NOT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `pis` int DEFAULT NULL,
  `data_inici_contracte` datetime DEFAULT NULL,
  `durada_contracte` decimal(2,0) DEFAULT NULL,
  `renda_contracte` decimal(6,2) DEFAULT NULL,
  `num_habitants` decimal(2,0) DEFAULT NULL,
  `ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `collectiu` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `data_alta` datetime DEFAULT NULL,
  `doble_afiliada` tinyint DEFAULT '0',
  `tipus_id` varchar(1) NOT NULL DEFAULT 'C',
  `cif` varchar(20) DEFAULT NULL,
  `pais` varchar(20) DEFAULT NULL,
  `forma_pagament` varchar(1) DEFAULT NULL,
  `frequencia_pagament` varchar(1) DEFAULT NULL,
  `compte_corrent` varchar(24) DEFAULT NULL,
  `quota` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `options`
--

CREATE TABLE `options` (
  `id` int NOT NULL,
  `section` varchar(50) NOT NULL,
  `option_key` varchar(200) DEFAULT NULL,
  `option_value` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `origens_afiliacio`
--

CREATE TABLE `origens_afiliacio` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `patterns`
--

CREATE TABLE `patterns` (
  `id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `summary` varchar(400) DEFAULT NULL,
  `content` text NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `persones`
--

CREATE TABLE `persones` (
  `id` int NOT NULL,
  `genere` varchar(1) DEFAULT NULL,
  `nom` varchar(100) NOT NULL,
  `cognoms` varchar(100) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `telefon` varchar(50) DEFAULT NULL,
  `butlleti` tinyint DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `no_rebre_info` tinyint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `pisos`
--

CREATE TABLE `pisos` (
  `id` int NOT NULL,
  `adreca` varchar(400) NOT NULL,
  `bloc` int NOT NULL,
  `escala` varchar(10) DEFAULT NULL,
  `pis` varchar(50) DEFAULT NULL,
  `porta` varchar(10) DEFAULT NULL,
  `complement` varchar(50) DEFAULT NULL,
  `estat` int DEFAULT NULL,
  `superficie` decimal(3,0) DEFAULT NULL,
  `num_habitacions` decimal(2,0) DEFAULT NULL,
  `cedula_habitabilitat` varchar(1) DEFAULT NULL,
  `certificat_energetic` varchar(1) DEFAULT NULL,
  `buit` varchar(1) DEFAULT NULL,
  `data_buit` datetime DEFAULT NULL,
  `api` int DEFAULT NULL,
  `propietat` int DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `propietat_ultima_actualitzacio` datetime DEFAULT NULL,
  `propietat_any_actualitzacio` decimal(4,0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `pisos_entramat`
--

CREATE TABLE `pisos_entramat` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `processes`
--

CREATE TABLE `processes` (
  `id` int NOT NULL,
  `code` varchar(50) NOT NULL,
  `title` varchar(200) NOT NULL,
  `periodicity` varchar(50) NOT NULL,
  `process_running` tinyint DEFAULT '0',
  `last_execution` datetime DEFAULT NULL,
  `next_execution` datetime DEFAULT NULL,
  `process_active` tinyint DEFAULT NULL,
  `class` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `process_executions`
--

CREATE TABLE `process_executions` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `start` datetime DEFAULT NULL,
  `end` datetime DEFAULT NULL,
  `ok` tinyint DEFAULT NULL,
  `result` text,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `provincies`
--

CREATE TABLE `provincies` (
  `id` int NOT NULL,
  `codi` varchar(2) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `remote_printers`
--

CREATE TABLE `remote_printers` (
  `id` int NOT NULL,
  `mac_address` varchar(12) NOT NULL,
  `computer_name` varchar(100) NOT NULL,
  `printer_name` varchar(100) NOT NULL,
  `title` varchar(100) NOT NULL,
  `print_paper_size` varchar(20) NOT NULL,
  `print_format` varchar(20) NOT NULL,
  `token` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `remote_printer_jobs`
--

CREATE TABLE `remote_printer_jobs` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `title` varchar(100) NOT NULL,
  `report` varchar(50) NOT NULL,
  `parameters` text NOT NULL,
  `status` varchar(50) NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `resolucions_conflicte`
--

CREATE TABLE `resolucions_conflicte` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `resultat` varchar(1) NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `resultats_assessoraments`
--

CREATE TABLE `resultats_assessoraments` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `roles`
--

CREATE TABLE `roles` (
  `id` int NOT NULL,
  `code` varchar(20) NOT NULL,
  `title` varchar(150) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `role_permissions`
--

CREATE TABLE `role_permissions` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `permission` varchar(50) NOT NULL,
  `operation` varchar(50) NOT NULL,
  `level` varchar(1) DEFAULT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `seccions_sindicals`
--

CREATE TABLE `seccions_sindicals` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `codis_postals` varchar(400) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `serveis_juridics`
--

CREATE TABLE `serveis_juridics` (
  `id` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `afiliada` int NOT NULL,
  `tipus` int NOT NULL,
  `tecnica` int DEFAULT NULL,
  `data_servei` datetime DEFAULT NULL,
  `preu` decimal(5,2) DEFAULT NULL,
  `descripcio` text,
  `comentaris` text,
  `resultat` varchar(1) DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `servei_juridic_documents`
--

CREATE TABLE `servei_juridic_documents` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `document` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `service_tokens`
--

CREATE TABLE `service_tokens` (
  `id` int NOT NULL,
  `token_hash` varchar(100) NOT NULL,
  `user` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `simpatitzants`
--

CREATE TABLE `simpatitzants` (
  `id` int NOT NULL,
  `cif` varchar(20) NOT NULL,
  `persona` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `data_alta` datetime NOT NULL,
  `data_baixa` datetime DEFAULT NULL,
  `observacions_estat` text,
  `origen_afiliacio` int DEFAULT NULL,
  `seccio_sindical` int NOT NULL,
  `nivell_participacio` int DEFAULT NULL,
  `comissio` int DEFAULT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `pis` int DEFAULT NULL,
  `data_inici_contracte` datetime DEFAULT NULL,
  `contracte_indefinit` tinyint DEFAULT NULL,
  `durada_contracte` decimal(2,0) DEFAULT NULL,
  `durada_contracte_prorrogues` decimal(1,0) DEFAULT NULL,
  `renda_contracte` decimal(6,2) DEFAULT NULL,
  `num_habitants` decimal(2,0) DEFAULT NULL,
  `ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `collectiu` int DEFAULT NULL,
  `comentaris` text,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `simpatitzant_historic_regims`
--

CREATE TABLE `simpatitzant_historic_regims` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `pis` int DEFAULT NULL,
  `data_inici_contracte` datetime DEFAULT NULL,
  `contracte_indefinit` tinyint DEFAULT NULL,
  `durada_contracte` decimal(2,0) DEFAULT NULL,
  `durada_contracte_prorrogues` decimal(1,0) DEFAULT NULL,
  `renda_contracte` decimal(6,2) DEFAULT NULL,
  `num_habitants` decimal(2,0) DEFAULT NULL,
  `ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `data_fi_regim` datetime NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `sollicituds`
--

CREATE TABLE `sollicituds` (
  `id` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `genere` varchar(1) DEFAULT NULL,
  `nom` varchar(100) DEFAULT NULL,
  `cognoms` varchar(100) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `telefon` varchar(50) DEFAULT NULL,
  `butlleti` tinyint DEFAULT NULL,
  `cif` varchar(20) DEFAULT NULL,
  `data_alta` datetime DEFAULT NULL,
  `origen_afiliacio` int DEFAULT NULL,
  `forma_pagament` varchar(1) DEFAULT NULL,
  `compte_corrent` varchar(24) DEFAULT NULL,
  `quota` decimal(5,2) DEFAULT NULL,
  `regim` varchar(1) DEFAULT NULL,
  `regim_altres` varchar(50) DEFAULT NULL,
  `google_id_original` text,
  `adreca_original` varchar(400) DEFAULT NULL,
  `municipi_original` varchar(200) DEFAULT NULL,
  `codi_postal_original` varchar(5) DEFAULT NULL,
  `google_id` text,
  `adreca` varchar(400) DEFAULT NULL,
  `nom_via` varchar(200) DEFAULT NULL,
  `numero` varchar(20) DEFAULT NULL,
  `municipi` int DEFAULT NULL,
  `codi_postal` varchar(5) DEFAULT NULL,
  `escala` varchar(10) DEFAULT NULL,
  `pis` varchar(50) DEFAULT NULL,
  `porta` varchar(10) DEFAULT NULL,
  `complement` varchar(50) DEFAULT NULL,
  `any_construccio` decimal(4,0) DEFAULT NULL,
  `ascensor` varchar(1) DEFAULT NULL,
  `parquing` varchar(1) DEFAULT NULL,
  `estat_pis` int DEFAULT NULL,
  `superficie` decimal(3,0) DEFAULT NULL,
  `cedula_habitabilitat` varchar(1) DEFAULT NULL,
  `certificat_energetic` varchar(1) DEFAULT NULL,
  `cif_api_original` varchar(20) DEFAULT NULL,
  `nom_api_original` varchar(100) DEFAULT NULL,
  `api` int DEFAULT NULL,
  `cif_propietat_original` varchar(20) DEFAULT NULL,
  `nom_propietat_original` varchar(100) DEFAULT NULL,
  `propietat` int DEFAULT NULL,
  `pis_data_inici_contracte` datetime DEFAULT NULL,
  `pis_durada_contracte` decimal(2,0) DEFAULT NULL,
  `pis_renda_contracte` decimal(6,2) DEFAULT NULL,
  `habitacio_renda_contracte` decimal(6,2) DEFAULT NULL,
  `pis_num_habitants` decimal(2,0) DEFAULT NULL,
  `habitacio_num_habitants` decimal(2,0) DEFAULT NULL,
  `pis_ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `habitacio_ingressos_mensuals` decimal(7,2) DEFAULT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `pis_contracte_indefinit` tinyint DEFAULT NULL,
  `pis_durada_contracte_prorrogues` decimal(1,0) DEFAULT NULL,
  `comentaris` text,
  `adreca_no_normalitzada` tinyint DEFAULT NULL,
  `adreca_no_normalitzada_text` text,
  `frequencia_pagament` varchar(1) DEFAULT NULL,
  `seccio_sindical` int DEFAULT NULL,
  `no_rebre_info` tinyint DEFAULT NULL,
  `propietat_vertical` varchar(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `tecniques`
--

CREATE TABLE `tecniques` (
  `id` int NOT NULL,
  `nom` varchar(200) NOT NULL,
  `email` varchar(150) NOT NULL,
  `telefon` varchar(50) DEFAULT NULL,
  `especialitat` int NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `tipus_assessoraments`
--

CREATE TABLE `tipus_assessoraments` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `tipus_serveis_juridics`
--

CREATE TABLE `tipus_serveis_juridics` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `tipus_sseguiment`
--

CREATE TABLE `tipus_sseguiment` (
  `id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `owner_user` int NOT NULL,
  `owner_group` int NOT NULL,
  `create_user` int NOT NULL,
  `update_user` int NOT NULL,
  `delete_user` int DEFAULT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` timestamp NOT NULL,
  `delete_timestamp` timestamp NULL DEFAULT NULL,
  `active` tinyint NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `code` varchar(20) NOT NULL,
  `password` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(150) NOT NULL,
  `default_group` int NOT NULL,
  `active` tinyint NOT NULL DEFAULT '1',
  `phone` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `user_groups`
--

CREATE TABLE `user_groups` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `user_page_options`
--

CREATE TABLE `user_page_options` (
  `id` int NOT NULL,
  `user_code` varchar(50) NOT NULL,
  `page_code` varchar(200) NOT NULL,
  `option_key` varchar(200) NOT NULL,
  `option_value` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de la taula `user_roles`
--

CREATE TABLE `user_roles` (
  `id` int NOT NULL,
  `parent_id` int NOT NULL,
  `child_id` int NOT NULL,
  `create_user` int NOT NULL,
  `create_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Estructura de suport per a vistes `vw_afiliades`
-- (mireu a sota per a la visualització real)
--
CREATE TABLE `vw_afiliades` (
`adreca` varchar(400)
,`adreca_normalitzada` varchar(1)
,`any_construccio` decimal(4,0)
,`api` varchar(100)
,`ascensor` varchar(1)
,`butlleti` varchar(1)
,`cedula_habitabilitat` varchar(1)
,`certificat_energetic` varchar(1)
,`cif` varchar(20)
,`codi_postal` varchar(5)
,`cognoms` varchar(100)
,`collectiu` varchar(200)
,`comissio` varchar(50)
,`data_alta` datetime
,`data_baixa` datetime
,`email` varchar(150)
,`estat` varchar(50)
,`estat_bloc` varchar(50)
,`estat_pis` varchar(50)
,`forma_pagament` varchar(1)
,`frequencia_pagament` varchar(1)
,`genere` varchar(1)
,`municipi` varchar(200)
,`nivell_participacio` varchar(50)
,`nom` varchar(100)
,`num_habitacions` decimal(2,0)
,`num_habitatges` decimal(3,0)
,`num_locals` decimal(3,0)
,`origen_afiliacio` varchar(50)
,`parquing` varchar(1)
,`propietat` varchar(100)
,`propietat_vertical` varchar(1)
,`provincia` varchar(100)
,`quota` decimal(5,2)
,`regim` varchar(1)
,`regim_descripcio` varchar(50)
,`superficie_bloc` decimal(5,0)
,`superficie_pis` decimal(3,0)
,`telefon` varchar(50)
);

--
-- Índexs per a les taules bolcades
--

--
-- Índexs per a la taula `afiliada_historic_regims`
--
ALTER TABLE `afiliada_historic_regims`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_afiliada_historic_regims_parent_id_afiliades` (`parent_id`),
  ADD KEY `fk_afiliada_historic_regims_pis_pisos` (`pis`),
  ADD KEY `fk_afiliada_historic_regims_create_user_users` (`create_user`),
  ADD KEY `fk_afiliada_historic_regims_update_user_users` (`update_user`);

--
-- Índexs per a la taula `afiliades`
--
ALTER TABLE `afiliades`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_cif` (`cif`),
  ADD KEY `fk_afiliades_persona_persones` (`persona`),
  ADD KEY `fk_afiliades_origen_afiliacio_origens_afiliacio` (`origen_afiliacio`),
  ADD KEY `fk_afiliades_nivell_participacio_nivells_participacio` (`nivell_participacio`),
  ADD KEY `fk_afiliades_comissio_comissions` (`comissio`),
  ADD KEY `fk_afiliades_pis_pisos` (`pis`),
  ADD KEY `fk_afiliades_collectiu_collectius` (`collectiu`),
  ADD KEY `fk_afiliades_owner_user_users` (`owner_user`),
  ADD KEY `fk_afiliades_owner_group_groups` (`owner_group`),
  ADD KEY `fk_afiliades_create_user_users` (`create_user`),
  ADD KEY `fk_afiliades_update_user_users` (`update_user`),
  ADD KEY `fk_afiliades_delete_user_users` (`delete_user`),
  ADD KEY `fk_afiliades_seccio_sindical_seccions_sindicals` (`seccio_sindical`),
  ADD KEY `fk_afiliades_tipus_seguiment_tipus_sseguiment` (`tipus_seguiment`);

--
-- Índexs per a la taula `afiliades_delegades_conflicte`
--
ALTER TABLE `afiliades_delegades_conflicte`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_afiliades_delegades_conflicte_child_id_afiliades` (`child_id`),
  ADD KEY `fk_afiliades_delegades_conflicte_create_user_users` (`create_user`);

--
-- Índexs per a la taula `agrupacions_blocs`
--
ALTER TABLE `agrupacions_blocs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_agrupacions_blocs_propietat_empreses` (`propietat`),
  ADD KEY `fk_agrupacions_blocs_owner_user_users` (`owner_user`),
  ADD KEY `fk_agrupacions_blocs_owner_group_groups` (`owner_group`),
  ADD KEY `fk_agrupacions_blocs_create_user_users` (`create_user`),
  ADD KEY `fk_agrupacions_blocs_update_user_users` (`update_user`),
  ADD KEY `fk_agrupacions_blocs_delete_user_users` (`delete_user`),
  ADD KEY `fk_agrupacions_blocs_api_empreses` (`api`);

--
-- Índexs per a la taula `assessoraments`
--
ALTER TABLE `assessoraments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_assessoraments_afiliada_afiliades` (`afiliada`),
  ADD KEY `fk_assessoraments_tipus_tipus_assessoraments` (`tipus`),
  ADD KEY `fk_assessoraments_tecnica_tecniques` (`tecnica`),
  ADD KEY `fk_assessoraments_owner_user_users` (`owner_user`),
  ADD KEY `fk_assessoraments_owner_group_groups` (`owner_group`),
  ADD KEY `fk_assessoraments_create_user_users` (`create_user`),
  ADD KEY `fk_assessoraments_update_user_users` (`update_user`),
  ADD KEY `fk_assessoraments_delete_user_users` (`delete_user`),
  ADD KEY `fk_assessoraments_resultat_resultats_assessoraments` (`resultat`),
  ADD KEY `fk_assessoraments_no_afiliada_no_afiliades` (`no_afiliada`);

--
-- Índexs per a la taula `assessorament_documents`
--
ALTER TABLE `assessorament_documents`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_assessorament_documents_parent_id_assessoraments` (`parent_id`),
  ADD KEY `fk_assessorament_documents_document_medias` (`document`),
  ADD KEY `fk_assessorament_documents_create_user_users` (`create_user`),
  ADD KEY `fk_assessorament_documents_update_user_users` (`update_user`);

--
-- Índexs per a la taula `blocs`
--
ALTER TABLE `blocs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_blocs_municipi_municipis` (`municipi`),
  ADD KEY `fk_blocs_estat_estats_habitatge` (`estat`),
  ADD KEY `fk_blocs_api_empreses` (`api`),
  ADD KEY `fk_blocs_propietat_empreses` (`propietat`),
  ADD KEY `fk_blocs_owner_user_users` (`owner_user`),
  ADD KEY `fk_blocs_owner_group_groups` (`owner_group`),
  ADD KEY `fk_blocs_create_user_users` (`create_user`),
  ADD KEY `fk_blocs_update_user_users` (`update_user`),
  ADD KEY `fk_blocs_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `blocs_agrupacio_blocs`
--
ALTER TABLE `blocs_agrupacio_blocs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_bloc` (`parent_id`,`bloc`),
  ADD KEY `fk_blocs_agrupacio_blocs_bloc_blocs` (`bloc`),
  ADD KEY `fk_blocs_agrupacio_blocs_create_user_users` (`create_user`),
  ADD KEY `fk_blocs_agrupacio_blocs_update_user_users` (`update_user`);

--
-- Índexs per a la taula `blocs_entramat`
--
ALTER TABLE `blocs_entramat`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_blocs_entramat_child_id_blocs` (`child_id`),
  ADD KEY `fk_blocs_entramat_create_user_users` (`create_user`);

--
-- Índexs per a la taula `blocs_importats`
--
ALTER TABLE `blocs_importats`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_blocs_importats_municipi_municipis` (`municipi`),
  ADD KEY `fk_blocs_importats_estat_estats_habitatge` (`estat`),
  ADD KEY `fk_blocs_importats_api_empreses` (`api`),
  ADD KEY `fk_blocs_importats_propietat_empreses` (`propietat`),
  ADD KEY `fk_blocs_importats_owner_user_users` (`owner_user`),
  ADD KEY `fk_blocs_importats_owner_group_groups` (`owner_group`),
  ADD KEY `fk_blocs_importats_create_user_users` (`create_user`),
  ADD KEY `fk_blocs_importats_update_user_users` (`update_user`),
  ADD KEY `fk_blocs_importats_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `causes_conflicte`
--
ALTER TABLE `causes_conflicte`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_causes_conflicte_owner_user_users` (`owner_user`),
  ADD KEY `fk_causes_conflicte_owner_group_groups` (`owner_group`),
  ADD KEY `fk_causes_conflicte_create_user_users` (`create_user`),
  ADD KEY `fk_causes_conflicte_update_user_users` (`update_user`),
  ADD KEY `fk_causes_conflicte_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `changes_log`
--
ALTER TABLE `changes_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_changes_log_user_users` (`user`);

--
-- Índexs per a la taula `collaboradores_collectiu`
--
ALTER TABLE `collaboradores_collectiu`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_collaboradores_collectiu_child_id_users` (`child_id`),
  ADD KEY `fk_collaboradores_collectiu_create_user_users` (`create_user`);

--
-- Índexs per a la taula `collectius`
--
ALTER TABLE `collectius`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_collectius_owner_user_users` (`owner_user`),
  ADD KEY `fk_collectius_owner_group_groups` (`owner_group`),
  ADD KEY `fk_collectius_create_user_users` (`create_user`),
  ADD KEY `fk_collectius_update_user_users` (`update_user`),
  ADD KEY `fk_collectius_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `comissions`
--
ALTER TABLE `comissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_comissions_owner_user_users` (`owner_user`),
  ADD KEY `fk_comissions_owner_group_groups` (`owner_group`),
  ADD KEY `fk_comissions_create_user_users` (`create_user`),
  ADD KEY `fk_comissions_update_user_users` (`update_user`),
  ADD KEY `fk_comissions_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `conflictes`
--
ALTER TABLE `conflictes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_conflictes_afiliada_afectada_afiliades` (`afiliada_afectada`),
  ADD KEY `fk_conflictes_bloc_afectat_blocs` (`bloc_afectat`),
  ADD KEY `fk_conflictes_entramat_afectat_entramats` (`entramat_afectat`),
  ADD KEY `fk_conflictes_delegada_users` (`delegada`),
  ADD KEY `fk_conflictes_resolucio_resolucions_conflicte` (`resolucio`),
  ADD KEY `fk_conflictes_owner_user_users` (`owner_user`),
  ADD KEY `fk_conflictes_owner_group_groups` (`owner_group`),
  ADD KEY `fk_conflictes_create_user_users` (`create_user`),
  ADD KEY `fk_conflictes_update_user_users` (`update_user`),
  ADD KEY `fk_conflictes_delete_user_users` (`delete_user`),
  ADD KEY `fk_conflictes_causa_causes_conflicte` (`causa`),
  ADD KEY `fk_conflictes_agrupacio_blocs_afectada_agrupacions_blocs` (`agrupacio_blocs_afectada`),
  ADD KEY `fk_conflictes_no_afiliada_afectada_no_afiliades` (`no_afiliada_afectada`),
  ADD KEY `fk_conflictes_simpatitzant_afectada_simpatitzants` (`simpatitzant_afectada`);

--
-- Índexs per a la taula `directius`
--
ALTER TABLE `directius`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_directius_owner_user_users` (`owner_user`),
  ADD KEY `fk_directius_owner_group_groups` (`owner_group`),
  ADD KEY `fk_directius_create_user_users` (`create_user`),
  ADD KEY `fk_directius_update_user_users` (`update_user`),
  ADD KEY `fk_directius_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `directius_empresa`
--
ALTER TABLE `directius_empresa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_directius_empresa_child_id_directius` (`child_id`),
  ADD KEY `fk_directius_empresa_create_user_users` (`create_user`);

--
-- Índexs per a la taula `domiciliacions`
--
ALTER TABLE `domiciliacions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_domiciliacions_fitxer_medias` (`fitxer`),
  ADD KEY `fk_domiciliacions_owner_user_users` (`owner_user`),
  ADD KEY `fk_domiciliacions_owner_group_groups` (`owner_group`),
  ADD KEY `fk_domiciliacions_create_user_users` (`create_user`),
  ADD KEY `fk_domiciliacions_update_user_users` (`update_user`),
  ADD KEY `fk_domiciliacions_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `empreses`
--
ALTER TABLE `empreses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_cif` (`cif`),
  ADD KEY `fk_empreses_municipi_municipis` (`municipi`),
  ADD KEY `fk_empreses_owner_user_users` (`owner_user`),
  ADD KEY `fk_empreses_owner_group_groups` (`owner_group`),
  ADD KEY `fk_empreses_create_user_users` (`create_user`),
  ADD KEY `fk_empreses_update_user_users` (`update_user`),
  ADD KEY `fk_empreses_delete_user_users` (`delete_user`),
  ADD KEY `fk_empreses_entramat_entramats` (`entramat`);

--
-- Índexs per a la taula `entramats`
--
ALTER TABLE `entramats`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_entramats_owner_user_users` (`owner_user`),
  ADD KEY `fk_entramats_owner_group_groups` (`owner_group`),
  ADD KEY `fk_entramats_create_user_users` (`create_user`),
  ADD KEY `fk_entramats_update_user_users` (`update_user`),
  ADD KEY `fk_entramats_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `especialitats`
--
ALTER TABLE `especialitats`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_especialitats_owner_user_users` (`owner_user`),
  ADD KEY `fk_especialitats_owner_group_groups` (`owner_group`),
  ADD KEY `fk_especialitats_create_user_users` (`create_user`),
  ADD KEY `fk_especialitats_update_user_users` (`update_user`),
  ADD KEY `fk_especialitats_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `estats_habitatge`
--
ALTER TABLE `estats_habitatge`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_estats_habitatge_owner_user_users` (`owner_user`),
  ADD KEY `fk_estats_habitatge_owner_group_groups` (`owner_group`),
  ADD KEY `fk_estats_habitatge_create_user_users` (`create_user`),
  ADD KEY `fk_estats_habitatge_update_user_users` (`update_user`),
  ADD KEY `fk_estats_habitatge_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `groups`
--
ALTER TABLE `groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_code` (`code`);

--
-- Índexs per a la taula `import_templates`
--
ALTER TABLE `import_templates`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`);

--
-- Índexs per a la taula `interessades`
--
ALTER TABLE `interessades`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_email` (`email`),
  ADD KEY `fk_interessades_owner_user_users` (`owner_user`),
  ADD KEY `fk_interessades_owner_group_groups` (`owner_group`),
  ADD KEY `fk_interessades_create_user_users` (`create_user`),
  ADD KEY `fk_interessades_update_user_users` (`update_user`),
  ADD KEY `fk_interessades_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `medias`
--
ALTER TABLE `medias`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_hash` (`hash`),
  ADD KEY `fk_medias_owner_user_users` (`owner_user`),
  ADD KEY `fk_medias_owner_group_groups` (`owner_group`),
  ADD KEY `fk_medias_create_user_users` (`create_user`),
  ADD KEY `fk_medias_update_user_users` (`update_user`),
  ADD KEY `fk_medias_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `municipis`
--
ALTER TABLE `municipis`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_municipis_provincia_provincies` (`provincia`),
  ADD KEY `fk_municipis_owner_user_users` (`owner_user`),
  ADD KEY `fk_municipis_owner_group_groups` (`owner_group`),
  ADD KEY `fk_municipis_create_user_users` (`create_user`),
  ADD KEY `fk_municipis_update_user_users` (`update_user`),
  ADD KEY `fk_municipis_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `negociacions_conflicte`
--
ALTER TABLE `negociacions_conflicte`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_negociacions_conflicte_parent_id_conflictes` (`parent_id`),
  ADD KEY `fk_negociacions_conflicte_create_user_users` (`create_user`),
  ADD KEY `fk_negociacions_conflicte_update_user_users` (`update_user`);

--
-- Índexs per a la taula `nivells_participacio`
--
ALTER TABLE `nivells_participacio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_nivells_participacio_owner_user_users` (`owner_user`),
  ADD KEY `fk_nivells_participacio_owner_group_groups` (`owner_group`),
  ADD KEY `fk_nivells_participacio_create_user_users` (`create_user`),
  ADD KEY `fk_nivells_participacio_update_user_users` (`update_user`),
  ADD KEY `fk_nivells_participacio_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `no_afiliades`
--
ALTER TABLE `no_afiliades`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_cif` (`cif`),
  ADD KEY `fk_no_afiliades_persona_persones` (`persona`),
  ADD KEY `fk_no_afiliades_pis_pisos` (`pis`),
  ADD KEY `fk_no_afiliades_collectiu_collectius` (`collectiu`),
  ADD KEY `fk_no_afiliades_owner_user_users` (`owner_user`),
  ADD KEY `fk_no_afiliades_owner_group_groups` (`owner_group`),
  ADD KEY `fk_no_afiliades_create_user_users` (`create_user`),
  ADD KEY `fk_no_afiliades_update_user_users` (`update_user`),
  ADD KEY `fk_no_afiliades_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `options`
--
ALTER TABLE `options`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_key` (`section`,`option_key`);

--
-- Índexs per a la taula `origens_afiliacio`
--
ALTER TABLE `origens_afiliacio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_origens_afiliacio_owner_user_users` (`owner_user`),
  ADD KEY `fk_origens_afiliacio_owner_group_groups` (`owner_group`),
  ADD KEY `fk_origens_afiliacio_create_user_users` (`create_user`),
  ADD KEY `fk_origens_afiliacio_update_user_users` (`update_user`),
  ADD KEY `fk_origens_afiliacio_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `patterns`
--
ALTER TABLE `patterns`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_patterns_owner_user_users` (`owner_user`),
  ADD KEY `fk_patterns_owner_group_groups` (`owner_group`),
  ADD KEY `fk_patterns_create_user_users` (`create_user`),
  ADD KEY `fk_patterns_update_user_users` (`update_user`),
  ADD KEY `fk_patterns_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `persones`
--
ALTER TABLE `persones`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_persones_owner_user_users` (`owner_user`),
  ADD KEY `fk_persones_owner_group_groups` (`owner_group`),
  ADD KEY `fk_persones_create_user_users` (`create_user`),
  ADD KEY `fk_persones_update_user_users` (`update_user`),
  ADD KEY `fk_persones_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `pisos`
--
ALTER TABLE `pisos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_pisos_bloc_blocs` (`bloc`),
  ADD KEY `fk_pisos_estat_estats_habitatge` (`estat`),
  ADD KEY `fk_pisos_api_empreses` (`api`),
  ADD KEY `fk_pisos_propietat_empreses` (`propietat`),
  ADD KEY `fk_pisos_owner_user_users` (`owner_user`),
  ADD KEY `fk_pisos_owner_group_groups` (`owner_group`),
  ADD KEY `fk_pisos_create_user_users` (`create_user`),
  ADD KEY `fk_pisos_update_user_users` (`update_user`),
  ADD KEY `fk_pisos_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `pisos_entramat`
--
ALTER TABLE `pisos_entramat`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_pisos_entramat_child_id_pisos` (`child_id`),
  ADD KEY `fk_pisos_entramat_create_user_users` (`create_user`);

--
-- Índexs per a la taula `processes`
--
ALTER TABLE `processes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_code` (`code`),
  ADD UNIQUE KEY `uk_class` (`class`);

--
-- Índexs per a la taula `process_executions`
--
ALTER TABLE `process_executions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_process_executions_parent_id_processes` (`parent_id`),
  ADD KEY `fk_process_executions_create_user_users` (`create_user`),
  ADD KEY `fk_process_executions_update_user_users` (`update_user`);

--
-- Índexs per a la taula `provincies`
--
ALTER TABLE `provincies`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_codi` (`codi`),
  ADD KEY `fk_provincies_owner_user_users` (`owner_user`),
  ADD KEY `fk_provincies_owner_group_groups` (`owner_group`),
  ADD KEY `fk_provincies_create_user_users` (`create_user`),
  ADD KEY `fk_provincies_update_user_users` (`update_user`),
  ADD KEY `fk_provincies_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `remote_printers`
--
ALTER TABLE `remote_printers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_mac_address_printer_name` (`mac_address`,`printer_name`),
  ADD KEY `fk_remote_printers_token_service_tokens` (`token`),
  ADD KEY `fk_remote_printers_owner_user_users` (`owner_user`),
  ADD KEY `fk_remote_printers_owner_group_groups` (`owner_group`),
  ADD KEY `fk_remote_printers_create_user_users` (`create_user`),
  ADD KEY `fk_remote_printers_update_user_users` (`update_user`),
  ADD KEY `fk_remote_printers_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `remote_printer_jobs`
--
ALTER TABLE `remote_printer_jobs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_remote_printer_jobs_parent_id_remote_printers` (`parent_id`),
  ADD KEY `fk_remote_printer_jobs_create_user_users` (`create_user`),
  ADD KEY `fk_remote_printer_jobs_update_user_users` (`update_user`);

--
-- Índexs per a la taula `resolucions_conflicte`
--
ALTER TABLE `resolucions_conflicte`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_nom` (`parent_id`,`nom`),
  ADD KEY `fk_resolucions_conflicte_create_user_users` (`create_user`),
  ADD KEY `fk_resolucions_conflicte_update_user_users` (`update_user`);

--
-- Índexs per a la taula `resultats_assessoraments`
--
ALTER TABLE `resultats_assessoraments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_resultats_assessoraments_owner_user_users` (`owner_user`),
  ADD KEY `fk_resultats_assessoraments_owner_group_groups` (`owner_group`),
  ADD KEY `fk_resultats_assessoraments_create_user_users` (`create_user`),
  ADD KEY `fk_resultats_assessoraments_update_user_users` (`update_user`),
  ADD KEY `fk_resultats_assessoraments_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_code` (`code`),
  ADD KEY `fk_roles_owner_user_users` (`owner_user`),
  ADD KEY `fk_roles_owner_group_groups` (`owner_group`),
  ADD KEY `fk_roles_create_user_users` (`create_user`),
  ADD KEY `fk_roles_update_user_users` (`update_user`),
  ADD KEY `fk_roles_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `role_permissions`
--
ALTER TABLE `role_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_id_permission_operation` (`parent_id`,`permission`,`operation`),
  ADD KEY `fk_role_permissions_create_user_users` (`create_user`),
  ADD KEY `fk_role_permissions_update_user_users` (`update_user`);

--
-- Índexs per a la taula `seccions_sindicals`
--
ALTER TABLE `seccions_sindicals`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_seccions_sindicals_owner_user_users` (`owner_user`),
  ADD KEY `fk_seccions_sindicals_owner_group_groups` (`owner_group`),
  ADD KEY `fk_seccions_sindicals_create_user_users` (`create_user`),
  ADD KEY `fk_seccions_sindicals_update_user_users` (`update_user`),
  ADD KEY `fk_seccions_sindicals_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `serveis_juridics`
--
ALTER TABLE `serveis_juridics`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_serveis_juridics_afiliada_afiliades` (`afiliada`),
  ADD KEY `fk_serveis_juridics_tipus_tipus_serveis_juridics` (`tipus`),
  ADD KEY `fk_serveis_juridics_tecnica_tecniques` (`tecnica`),
  ADD KEY `fk_serveis_juridics_owner_user_users` (`owner_user`),
  ADD KEY `fk_serveis_juridics_owner_group_groups` (`owner_group`),
  ADD KEY `fk_serveis_juridics_create_user_users` (`create_user`),
  ADD KEY `fk_serveis_juridics_update_user_users` (`update_user`),
  ADD KEY `fk_serveis_juridics_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `servei_juridic_documents`
--
ALTER TABLE `servei_juridic_documents`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_servei_juridic_documents_parent_id_serveis_juridics` (`parent_id`),
  ADD KEY `fk_servei_juridic_documents_document_medias` (`document`),
  ADD KEY `fk_servei_juridic_documents_create_user_users` (`create_user`),
  ADD KEY `fk_servei_juridic_documents_update_user_users` (`update_user`);

--
-- Índexs per a la taula `service_tokens`
--
ALTER TABLE `service_tokens`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_token_hash` (`token_hash`),
  ADD KEY `fk_service_tokens_user_users` (`user`),
  ADD KEY `fk_service_tokens_owner_user_users` (`owner_user`),
  ADD KEY `fk_service_tokens_owner_group_groups` (`owner_group`),
  ADD KEY `fk_service_tokens_create_user_users` (`create_user`),
  ADD KEY `fk_service_tokens_update_user_users` (`update_user`),
  ADD KEY `fk_service_tokens_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `simpatitzants`
--
ALTER TABLE `simpatitzants`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_cif` (`cif`),
  ADD KEY `fk_simpatitzants_persona_persones` (`persona`),
  ADD KEY `fk_simpatitzants_origen_afiliacio_origens_afiliacio` (`origen_afiliacio`),
  ADD KEY `fk_simpatitzants_seccio_sindical_seccions_sindicals` (`seccio_sindical`),
  ADD KEY `fk_simpatitzants_nivell_participacio_nivells_participacio` (`nivell_participacio`),
  ADD KEY `fk_simpatitzants_comissio_comissions` (`comissio`),
  ADD KEY `fk_simpatitzants_pis_pisos` (`pis`),
  ADD KEY `fk_simpatitzants_collectiu_collectius` (`collectiu`),
  ADD KEY `fk_simpatitzants_owner_user_users` (`owner_user`),
  ADD KEY `fk_simpatitzants_owner_group_groups` (`owner_group`),
  ADD KEY `fk_simpatitzants_create_user_users` (`create_user`),
  ADD KEY `fk_simpatitzants_update_user_users` (`update_user`),
  ADD KEY `fk_simpatitzants_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `simpatitzant_historic_regims`
--
ALTER TABLE `simpatitzant_historic_regims`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_simpatitzant_historic_regims_parent_id_simpatitzants` (`parent_id`),
  ADD KEY `fk_simpatitzant_historic_regims_pis_pisos` (`pis`),
  ADD KEY `fk_simpatitzant_historic_regims_create_user_users` (`create_user`),
  ADD KEY `fk_simpatitzant_historic_regims_update_user_users` (`update_user`);

--
-- Índexs per a la taula `sollicituds`
--
ALTER TABLE `sollicituds`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD KEY `fk_sollicituds_origen_afiliacio_origens_afiliacio` (`origen_afiliacio`),
  ADD KEY `fk_sollicituds_municipi_municipis` (`municipi`),
  ADD KEY `fk_sollicituds_estat_pis_estats_habitatge` (`estat_pis`),
  ADD KEY `fk_sollicituds_api_empreses` (`api`),
  ADD KEY `fk_sollicituds_propietat_empreses` (`propietat`),
  ADD KEY `fk_sollicituds_owner_user_users` (`owner_user`),
  ADD KEY `fk_sollicituds_owner_group_groups` (`owner_group`),
  ADD KEY `fk_sollicituds_create_user_users` (`create_user`),
  ADD KEY `fk_sollicituds_update_user_users` (`update_user`),
  ADD KEY `fk_sollicituds_delete_user_users` (`delete_user`),
  ADD KEY `fk_sollicituds_seccio_sindical_seccions_sindicals` (`seccio_sindical`);

--
-- Índexs per a la taula `tecniques`
--
ALTER TABLE `tecniques`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_tecniques_especialitat_especialitats` (`especialitat`),
  ADD KEY `fk_tecniques_owner_user_users` (`owner_user`),
  ADD KEY `fk_tecniques_owner_group_groups` (`owner_group`),
  ADD KEY `fk_tecniques_create_user_users` (`create_user`),
  ADD KEY `fk_tecniques_update_user_users` (`update_user`),
  ADD KEY `fk_tecniques_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `tipus_assessoraments`
--
ALTER TABLE `tipus_assessoraments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_tipus_assessoraments_owner_user_users` (`owner_user`),
  ADD KEY `fk_tipus_assessoraments_owner_group_groups` (`owner_group`),
  ADD KEY `fk_tipus_assessoraments_create_user_users` (`create_user`),
  ADD KEY `fk_tipus_assessoraments_update_user_users` (`update_user`),
  ADD KEY `fk_tipus_assessoraments_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `tipus_serveis_juridics`
--
ALTER TABLE `tipus_serveis_juridics`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_tipus_serveis_juridics_owner_user_users` (`owner_user`),
  ADD KEY `fk_tipus_serveis_juridics_owner_group_groups` (`owner_group`),
  ADD KEY `fk_tipus_serveis_juridics_create_user_users` (`create_user`),
  ADD KEY `fk_tipus_serveis_juridics_update_user_users` (`update_user`),
  ADD KEY `fk_tipus_serveis_juridics_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `tipus_sseguiment`
--
ALTER TABLE `tipus_sseguiment`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_nom` (`nom`),
  ADD KEY `fk_tipus_sseguiment_owner_user_users` (`owner_user`),
  ADD KEY `fk_tipus_sseguiment_owner_group_groups` (`owner_group`),
  ADD KEY `fk_tipus_sseguiment_create_user_users` (`create_user`),
  ADD KEY `fk_tipus_sseguiment_update_user_users` (`update_user`),
  ADD KEY `fk_tipus_sseguiment_delete_user_users` (`delete_user`);

--
-- Índexs per a la taula `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_code` (`code`),
  ADD UNIQUE KEY `uk_email` (`email`),
  ADD KEY `fk_users_default_group_groups` (`default_group`);

--
-- Índexs per a la taula `user_groups`
--
ALTER TABLE `user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_user_groups_child_id_groups` (`child_id`),
  ADD KEY `fk_user_groups_create_user_users` (`create_user`);

--
-- Índexs per a la taula `user_page_options`
--
ALTER TABLE `user_page_options`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_key` (`user_code`,`page_code`,`option_key`);

--
-- Índexs per a la taula `user_roles`
--
ALTER TABLE `user_roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_id` (`id`),
  ADD UNIQUE KEY `uk_parent_child` (`parent_id`,`child_id`),
  ADD KEY `fk_user_roles_child_id_roles` (`child_id`),
  ADD KEY `fk_user_roles_create_user_users` (`create_user`);

--
-- AUTO_INCREMENT per les taules bolcades
--

--
-- AUTO_INCREMENT per la taula `afiliada_historic_regims`
--
ALTER TABLE `afiliada_historic_regims`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `afiliades`
--
ALTER TABLE `afiliades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `afiliades_delegades_conflicte`
--
ALTER TABLE `afiliades_delegades_conflicte`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agrupacions_blocs`
--
ALTER TABLE `agrupacions_blocs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `assessoraments`
--
ALTER TABLE `assessoraments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `assessorament_documents`
--
ALTER TABLE `assessorament_documents`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `blocs`
--
ALTER TABLE `blocs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `blocs_agrupacio_blocs`
--
ALTER TABLE `blocs_agrupacio_blocs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `blocs_entramat`
--
ALTER TABLE `blocs_entramat`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `blocs_importats`
--
ALTER TABLE `blocs_importats`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `causes_conflicte`
--
ALTER TABLE `causes_conflicte`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `changes_log`
--
ALTER TABLE `changes_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `collaboradores_collectiu`
--
ALTER TABLE `collaboradores_collectiu`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `collectius`
--
ALTER TABLE `collectius`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `comissions`
--
ALTER TABLE `comissions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `conflictes`
--
ALTER TABLE `conflictes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `directius`
--
ALTER TABLE `directius`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `directius_empresa`
--
ALTER TABLE `directius_empresa`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `domiciliacions`
--
ALTER TABLE `domiciliacions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `empreses`
--
ALTER TABLE `empreses`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `entramats`
--
ALTER TABLE `entramats`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `especialitats`
--
ALTER TABLE `especialitats`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `estats_habitatge`
--
ALTER TABLE `estats_habitatge`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `groups`
--
ALTER TABLE `groups`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `import_templates`
--
ALTER TABLE `import_templates`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `interessades`
--
ALTER TABLE `interessades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `medias`
--
ALTER TABLE `medias`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `municipis`
--
ALTER TABLE `municipis`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `negociacions_conflicte`
--
ALTER TABLE `negociacions_conflicte`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `nivells_participacio`
--
ALTER TABLE `nivells_participacio`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `no_afiliades`
--
ALTER TABLE `no_afiliades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `options`
--
ALTER TABLE `options`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `origens_afiliacio`
--
ALTER TABLE `origens_afiliacio`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `patterns`
--
ALTER TABLE `patterns`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `persones`
--
ALTER TABLE `persones`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pisos`
--
ALTER TABLE `pisos`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pisos_entramat`
--
ALTER TABLE `pisos_entramat`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `processes`
--
ALTER TABLE `processes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `process_executions`
--
ALTER TABLE `process_executions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `provincies`
--
ALTER TABLE `provincies`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `remote_printers`
--
ALTER TABLE `remote_printers`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `remote_printer_jobs`
--
ALTER TABLE `remote_printer_jobs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `resolucions_conflicte`
--
ALTER TABLE `resolucions_conflicte`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `resultats_assessoraments`
--
ALTER TABLE `resultats_assessoraments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `role_permissions`
--
ALTER TABLE `role_permissions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `seccions_sindicals`
--
ALTER TABLE `seccions_sindicals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `serveis_juridics`
--
ALTER TABLE `serveis_juridics`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `servei_juridic_documents`
--
ALTER TABLE `servei_juridic_documents`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `service_tokens`
--
ALTER TABLE `service_tokens`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `simpatitzants`
--
ALTER TABLE `simpatitzants`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `simpatitzant_historic_regims`
--
ALTER TABLE `simpatitzant_historic_regims`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `sollicituds`
--
ALTER TABLE `sollicituds`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `tecniques`
--
ALTER TABLE `tecniques`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `tipus_assessoraments`
--
ALTER TABLE `tipus_assessoraments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `tipus_serveis_juridics`
--
ALTER TABLE `tipus_serveis_juridics`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `tipus_sseguiment`
--
ALTER TABLE `tipus_sseguiment`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `user_groups`
--
ALTER TABLE `user_groups`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `user_page_options`
--
ALTER TABLE `user_page_options`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `user_roles`
--
ALTER TABLE `user_roles`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

-- --------------------------------------------------------

--
-- Estructura per a vista `vw_afiliades`
--
DROP TABLE IF EXISTS `vw_afiliades`;

CREATE ALGORITHM=UNDEFINED DEFINER=`sindica7_bo`@`localhost` SQL SECURITY DEFINER VIEW `vw_afiliades`  AS SELECT `pe`.`genere` AS `genere`, `pe`.`nom` AS `nom`, `pe`.`cognoms` AS `cognoms`, `pe`.`email` AS `email`, `pe`.`telefon` AS `telefon`, if(((`pe`.`butlleti` is null) or (`pe`.`butlleti` = 0)),'n','s') AS `butlleti`, `a`.`cif` AS `cif`, if(((`a`.`adreca_no_normalitzada` is null) or (`a`.`adreca_no_normalitzada` = 0)),'s','n') AS `adreca_normalitzada`, if((`a`.`adreca_no_normalitzada` = 1),`a`.`adreca_no_normalitzada_text`,`p`.`adreca`) AS `adreca`, `b`.`codi_postal` AS `codi_postal`, `m`.`nom` AS `municipi`, `pr`.`nom` AS `provincia`, `a`.`data_alta` AS `data_alta`, `a`.`status` AS `estat`, `a`.`data_baixa` AS `data_baixa`, `a`.`regim` AS `regim`, (case when (`a`.`regim` = 'P') then 'Propietat' when (`a`.`regim` = 'L') then 'Lloguer' when (`a`.`regim` = 'H') then 'Habitació' when (`a`.`regim` = 'A') then `a`.`regim_altres` end) AS `regim_descripcio`, `co`.`nom` AS `collectiu`, `c`.`nom` AS `comissio`, `a`.`forma_pagament` AS `forma_pagament`, `a`.`frequencia_pagament` AS `frequencia_pagament`, `a`.`quota` AS `quota`, `np`.`nom` AS `nivell_participacio`, `of`.`nom` AS `origen_afiliacio`, `ehp`.`nom` AS `estat_pis`, `p`.`num_habitacions` AS `num_habitacions`, `p`.`cedula_habitabilitat` AS `cedula_habitabilitat`, `p`.`certificat_energetic` AS `certificat_energetic`, `p`.`superficie` AS `superficie_pis`, `b`.`any_construccio` AS `any_construccio`, `b`.`ascensor` AS `ascensor`, `b`.`num_habitatges` AS `num_habitatges`, `b`.`num_locals` AS `num_locals`, `b`.`parquing` AS `parquing`, `b`.`propietat_vertical` AS `propietat_vertical`, `b`.`superficie` AS `superficie_bloc`, `ehb`.`nom` AS `estat_bloc`, if((`p`.`propietat` is not null),`epp`.`nom`,if((`b`.`propietat` is not null),`epb`.`nom`,if((`ag`.`propietat` is not null),`epa`.`nom`,NULL))) AS `propietat`, if((`p`.`api` is not null),`eap`.`nom`,if((`b`.`api` is not null),`eab`.`nom`,NULL)) AS `api` FROM ((((((((((((((((((`afiliades` `a` left join `persones` `pe` on((`a`.`persona` = `pe`.`id`))) left join `comissions` `c` on((`a`.`comissio` = `c`.`id`))) left join `collectius` `co` on((`a`.`collectiu` = `co`.`id`))) left join `nivells_participacio` `np` on((`a`.`nivell_participacio` = `np`.`id`))) left join `origens_afiliacio` `of` on((`a`.`origen_afiliacio` = `of`.`id`))) left join `pisos` `p` on((`a`.`pis` = `p`.`id`))) left join `blocs` `b` on((`p`.`bloc` = `b`.`id`))) left join `blocs_agrupacio_blocs` `bag` on((`b`.`id` = `bag`.`bloc`))) left join `agrupacions_blocs` `ag` on((`bag`.`parent_id` = `ag`.`id`))) left join `estats_habitatge` `ehp` on((`p`.`estat` = `ehp`.`id`))) left join `estats_habitatge` `ehb` on((`b`.`estat` = `ehb`.`id`))) left join `municipis` `m` on((`b`.`municipi` = `m`.`id`))) left join `provincies` `pr` on((`m`.`provincia` = `pr`.`id`))) left join `empreses` `epp` on((`p`.`propietat` = `epp`.`id`))) left join `empreses` `epb` on((`b`.`propietat` = `epb`.`id`))) left join `empreses` `epa` on((`ag`.`propietat` = `epa`.`id`))) left join `empreses` `eap` on((`p`.`api` = `eap`.`id`))) left join `empreses` `eab` on((`b`.`api` = `eab`.`id`))) ;

--
-- Restriccions per a les taules bolcades
--

--
-- Restriccions per a la taula `afiliada_historic_regims`
--
ALTER TABLE `afiliada_historic_regims`
  ADD CONSTRAINT `fk_afiliada_historic_regims_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliada_historic_regims_parent_id_afiliades` FOREIGN KEY (`parent_id`) REFERENCES `afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliada_historic_regims_pis_pisos` FOREIGN KEY (`pis`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliada_historic_regims_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `afiliades`
--
ALTER TABLE `afiliades`
  ADD CONSTRAINT `fk_afiliades_collectiu_collectius` FOREIGN KEY (`collectiu`) REFERENCES `collectius` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_comissio_comissions` FOREIGN KEY (`comissio`) REFERENCES `comissions` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_nivell_participacio_nivells_participacio` FOREIGN KEY (`nivell_participacio`) REFERENCES `nivells_participacio` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_origen_afiliacio_origens_afiliacio` FOREIGN KEY (`origen_afiliacio`) REFERENCES `origens_afiliacio` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_persona_persones` FOREIGN KEY (`persona`) REFERENCES `persones` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_pis_pisos` FOREIGN KEY (`pis`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_seccio_sindical_seccions_sindicals` FOREIGN KEY (`seccio_sindical`) REFERENCES `seccions_sindicals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_tipus_seguiment_tipus_sseguiment` FOREIGN KEY (`tipus_seguiment`) REFERENCES `tipus_sseguiment` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `afiliades_delegades_conflicte`
--
ALTER TABLE `afiliades_delegades_conflicte`
  ADD CONSTRAINT `fk_afiliades_delegades_conflicte_child_id_afiliades` FOREIGN KEY (`child_id`) REFERENCES `afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_delegades_conflicte_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_afiliades_delegades_conflicte_parent_id_conflictes` FOREIGN KEY (`parent_id`) REFERENCES `conflictes` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `agrupacions_blocs`
--
ALTER TABLE `agrupacions_blocs`
  ADD CONSTRAINT `fk_agrupacions_blocs_api_empreses` FOREIGN KEY (`api`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_propietat_empreses` FOREIGN KEY (`propietat`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_agrupacions_blocs_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `assessoraments`
--
ALTER TABLE `assessoraments`
  ADD CONSTRAINT `fk_assessoraments_afiliada_afiliades` FOREIGN KEY (`afiliada`) REFERENCES `afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_no_afiliada_no_afiliades` FOREIGN KEY (`no_afiliada`) REFERENCES `no_afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_resultat_resultats_assessoraments` FOREIGN KEY (`resultat`) REFERENCES `resultats_assessoraments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_tecnica_tecniques` FOREIGN KEY (`tecnica`) REFERENCES `tecniques` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_tipus_tipus_assessoraments` FOREIGN KEY (`tipus`) REFERENCES `tipus_assessoraments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessoraments_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `assessorament_documents`
--
ALTER TABLE `assessorament_documents`
  ADD CONSTRAINT `fk_assessorament_documents_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessorament_documents_document_medias` FOREIGN KEY (`document`) REFERENCES `medias` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessorament_documents_parent_id_assessoraments` FOREIGN KEY (`parent_id`) REFERENCES `assessoraments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_assessorament_documents_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `blocs`
--
ALTER TABLE `blocs`
  ADD CONSTRAINT `fk_blocs_api_empreses` FOREIGN KEY (`api`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_estat_estats_habitatge` FOREIGN KEY (`estat`) REFERENCES `estats_habitatge` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_municipi_municipis` FOREIGN KEY (`municipi`) REFERENCES `municipis` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_propietat_empreses` FOREIGN KEY (`propietat`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `blocs_agrupacio_blocs`
--
ALTER TABLE `blocs_agrupacio_blocs`
  ADD CONSTRAINT `fk_blocs_agrupacio_blocs_bloc_blocs` FOREIGN KEY (`bloc`) REFERENCES `blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_agrupacio_blocs_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_agrupacio_blocs_parent_id_agrupacions_blocs` FOREIGN KEY (`parent_id`) REFERENCES `agrupacions_blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_agrupacio_blocs_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `blocs_entramat`
--
ALTER TABLE `blocs_entramat`
  ADD CONSTRAINT `fk_blocs_entramat_child_id_blocs` FOREIGN KEY (`child_id`) REFERENCES `blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_entramat_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_entramat_parent_id_entramats` FOREIGN KEY (`parent_id`) REFERENCES `entramats` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `blocs_importats`
--
ALTER TABLE `blocs_importats`
  ADD CONSTRAINT `fk_blocs_importats_api_empreses` FOREIGN KEY (`api`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_estat_estats_habitatge` FOREIGN KEY (`estat`) REFERENCES `estats_habitatge` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_municipi_municipis` FOREIGN KEY (`municipi`) REFERENCES `municipis` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_propietat_empreses` FOREIGN KEY (`propietat`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_blocs_importats_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `causes_conflicte`
--
ALTER TABLE `causes_conflicte`
  ADD CONSTRAINT `fk_causes_conflicte_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_causes_conflicte_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_causes_conflicte_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_causes_conflicte_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_causes_conflicte_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `changes_log`
--
ALTER TABLE `changes_log`
  ADD CONSTRAINT `fk_changes_log_user_users` FOREIGN KEY (`user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `collaboradores_collectiu`
--
ALTER TABLE `collaboradores_collectiu`
  ADD CONSTRAINT `fk_collaboradores_collectiu_child_id_users` FOREIGN KEY (`child_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collaboradores_collectiu_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collaboradores_collectiu_parent_id_collectius` FOREIGN KEY (`parent_id`) REFERENCES `collectius` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `collectius`
--
ALTER TABLE `collectius`
  ADD CONSTRAINT `fk_collectius_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collectius_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collectius_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collectius_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_collectius_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `comissions`
--
ALTER TABLE `comissions`
  ADD CONSTRAINT `fk_comissions_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_comissions_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_comissions_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_comissions_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_comissions_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `conflictes`
--
ALTER TABLE `conflictes`
  ADD CONSTRAINT `fk_conflictes_afiliada_afectada_afiliades` FOREIGN KEY (`afiliada_afectada`) REFERENCES `afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_agrupacio_blocs_afectada_agrupacions_blocs` FOREIGN KEY (`agrupacio_blocs_afectada`) REFERENCES `agrupacions_blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_bloc_afectat_blocs` FOREIGN KEY (`bloc_afectat`) REFERENCES `blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_causa_causes_conflicte` FOREIGN KEY (`causa`) REFERENCES `causes_conflicte` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_delegada_users` FOREIGN KEY (`delegada`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_entramat_afectat_entramats` FOREIGN KEY (`entramat_afectat`) REFERENCES `entramats` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_no_afiliada_afectada_no_afiliades` FOREIGN KEY (`no_afiliada_afectada`) REFERENCES `no_afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_resolucio_resolucions_conflicte` FOREIGN KEY (`resolucio`) REFERENCES `resolucions_conflicte` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_simpatitzant_afectada_simpatitzants` FOREIGN KEY (`simpatitzant_afectada`) REFERENCES `simpatitzants` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_conflictes_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `directius`
--
ALTER TABLE `directius`
  ADD CONSTRAINT `fk_directius_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `directius_empresa`
--
ALTER TABLE `directius_empresa`
  ADD CONSTRAINT `fk_directius_empresa_child_id_directius` FOREIGN KEY (`child_id`) REFERENCES `directius` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_empresa_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_directius_empresa_parent_id_empreses` FOREIGN KEY (`parent_id`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `domiciliacions`
--
ALTER TABLE `domiciliacions`
  ADD CONSTRAINT `fk_domiciliacions_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_domiciliacions_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_domiciliacions_fitxer_medias` FOREIGN KEY (`fitxer`) REFERENCES `medias` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_domiciliacions_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_domiciliacions_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_domiciliacions_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `empreses`
--
ALTER TABLE `empreses`
  ADD CONSTRAINT `fk_empreses_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_entramat_entramats` FOREIGN KEY (`entramat`) REFERENCES `entramats` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_municipi_municipis` FOREIGN KEY (`municipi`) REFERENCES `municipis` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_empreses_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `entramats`
--
ALTER TABLE `entramats`
  ADD CONSTRAINT `fk_entramats_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_entramats_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_entramats_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_entramats_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_entramats_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `especialitats`
--
ALTER TABLE `especialitats`
  ADD CONSTRAINT `fk_especialitats_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_especialitats_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_especialitats_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_especialitats_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_especialitats_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `estats_habitatge`
--
ALTER TABLE `estats_habitatge`
  ADD CONSTRAINT `fk_estats_habitatge_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_estats_habitatge_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_estats_habitatge_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_estats_habitatge_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_estats_habitatge_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `interessades`
--
ALTER TABLE `interessades`
  ADD CONSTRAINT `fk_interessades_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_interessades_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_interessades_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_interessades_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_interessades_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `medias`
--
ALTER TABLE `medias`
  ADD CONSTRAINT `fk_medias_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_medias_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_medias_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_medias_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_medias_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `municipis`
--
ALTER TABLE `municipis`
  ADD CONSTRAINT `fk_municipis_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_municipis_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_municipis_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_municipis_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_municipis_provincia_provincies` FOREIGN KEY (`provincia`) REFERENCES `provincies` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_municipis_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `negociacions_conflicte`
--
ALTER TABLE `negociacions_conflicte`
  ADD CONSTRAINT `fk_negociacions_conflicte_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_negociacions_conflicte_parent_id_conflictes` FOREIGN KEY (`parent_id`) REFERENCES `conflictes` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_negociacions_conflicte_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `nivells_participacio`
--
ALTER TABLE `nivells_participacio`
  ADD CONSTRAINT `fk_nivells_participacio_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_nivells_participacio_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_nivells_participacio_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_nivells_participacio_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_nivells_participacio_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `no_afiliades`
--
ALTER TABLE `no_afiliades`
  ADD CONSTRAINT `fk_no_afiliades_collectiu_collectius` FOREIGN KEY (`collectiu`) REFERENCES `collectius` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_persona_persones` FOREIGN KEY (`persona`) REFERENCES `persones` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_pis_pisos` FOREIGN KEY (`pis`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_no_afiliades_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `origens_afiliacio`
--
ALTER TABLE `origens_afiliacio`
  ADD CONSTRAINT `fk_origens_afiliacio_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_origens_afiliacio_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_origens_afiliacio_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_origens_afiliacio_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_origens_afiliacio_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `patterns`
--
ALTER TABLE `patterns`
  ADD CONSTRAINT `fk_patterns_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_patterns_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_patterns_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_patterns_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_patterns_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `persones`
--
ALTER TABLE `persones`
  ADD CONSTRAINT `fk_persones_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_persones_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_persones_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_persones_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_persones_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `pisos`
--
ALTER TABLE `pisos`
  ADD CONSTRAINT `fk_pisos_api_empreses` FOREIGN KEY (`api`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_bloc_blocs` FOREIGN KEY (`bloc`) REFERENCES `blocs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_estat_estats_habitatge` FOREIGN KEY (`estat`) REFERENCES `estats_habitatge` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_propietat_empreses` FOREIGN KEY (`propietat`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `pisos_entramat`
--
ALTER TABLE `pisos_entramat`
  ADD CONSTRAINT `fk_pisos_entramat_child_id_pisos` FOREIGN KEY (`child_id`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_entramat_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_pisos_entramat_parent_id_entramats` FOREIGN KEY (`parent_id`) REFERENCES `entramats` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `process_executions`
--
ALTER TABLE `process_executions`
  ADD CONSTRAINT `fk_process_executions_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_process_executions_parent_id_processes` FOREIGN KEY (`parent_id`) REFERENCES `processes` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_process_executions_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `provincies`
--
ALTER TABLE `provincies`
  ADD CONSTRAINT `fk_provincies_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_provincies_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_provincies_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_provincies_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_provincies_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `remote_printers`
--
ALTER TABLE `remote_printers`
  ADD CONSTRAINT `fk_remote_printers_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printers_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printers_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printers_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printers_token_service_tokens` FOREIGN KEY (`token`) REFERENCES `service_tokens` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printers_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `remote_printer_jobs`
--
ALTER TABLE `remote_printer_jobs`
  ADD CONSTRAINT `fk_remote_printer_jobs_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printer_jobs_parent_id_remote_printers` FOREIGN KEY (`parent_id`) REFERENCES `remote_printers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_remote_printer_jobs_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `resolucions_conflicte`
--
ALTER TABLE `resolucions_conflicte`
  ADD CONSTRAINT `fk_resolucions_conflicte_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resolucions_conflicte_parent_id_causes_conflicte` FOREIGN KEY (`parent_id`) REFERENCES `causes_conflicte` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resolucions_conflicte_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `resultats_assessoraments`
--
ALTER TABLE `resultats_assessoraments`
  ADD CONSTRAINT `fk_resultats_assessoraments_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resultats_assessoraments_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resultats_assessoraments_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resultats_assessoraments_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_resultats_assessoraments_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `roles`
--
ALTER TABLE `roles`
  ADD CONSTRAINT `fk_roles_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_roles_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_roles_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_roles_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_roles_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `role_permissions`
--
ALTER TABLE `role_permissions`
  ADD CONSTRAINT `fk_role_permissions_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_role_permissions_parent_id_roles` FOREIGN KEY (`parent_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_role_permissions_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `seccions_sindicals`
--
ALTER TABLE `seccions_sindicals`
  ADD CONSTRAINT `fk_seccions_sindicals_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_seccions_sindicals_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_seccions_sindicals_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_seccions_sindicals_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_seccions_sindicals_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `serveis_juridics`
--
ALTER TABLE `serveis_juridics`
  ADD CONSTRAINT `fk_serveis_juridics_afiliada_afiliades` FOREIGN KEY (`afiliada`) REFERENCES `afiliades` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_tecnica_tecniques` FOREIGN KEY (`tecnica`) REFERENCES `tecniques` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_tipus_tipus_serveis_juridics` FOREIGN KEY (`tipus`) REFERENCES `tipus_serveis_juridics` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_serveis_juridics_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `servei_juridic_documents`
--
ALTER TABLE `servei_juridic_documents`
  ADD CONSTRAINT `fk_servei_juridic_documents_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_servei_juridic_documents_document_medias` FOREIGN KEY (`document`) REFERENCES `medias` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_servei_juridic_documents_parent_id_serveis_juridics` FOREIGN KEY (`parent_id`) REFERENCES `serveis_juridics` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_servei_juridic_documents_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `service_tokens`
--
ALTER TABLE `service_tokens`
  ADD CONSTRAINT `fk_service_tokens_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_service_tokens_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_service_tokens_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_service_tokens_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_service_tokens_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_service_tokens_user_users` FOREIGN KEY (`user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `simpatitzants`
--
ALTER TABLE `simpatitzants`
  ADD CONSTRAINT `fk_simpatitzants_collectiu_collectius` FOREIGN KEY (`collectiu`) REFERENCES `collectius` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_comissio_comissions` FOREIGN KEY (`comissio`) REFERENCES `comissions` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_nivell_participacio_nivells_participacio` FOREIGN KEY (`nivell_participacio`) REFERENCES `nivells_participacio` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_origen_afiliacio_origens_afiliacio` FOREIGN KEY (`origen_afiliacio`) REFERENCES `origens_afiliacio` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_persona_persones` FOREIGN KEY (`persona`) REFERENCES `persones` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_pis_pisos` FOREIGN KEY (`pis`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_seccio_sindical_seccions_sindicals` FOREIGN KEY (`seccio_sindical`) REFERENCES `seccions_sindicals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzants_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `simpatitzant_historic_regims`
--
ALTER TABLE `simpatitzant_historic_regims`
  ADD CONSTRAINT `fk_simpatitzant_historic_regims_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzant_historic_regims_parent_id_simpatitzants` FOREIGN KEY (`parent_id`) REFERENCES `simpatitzants` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzant_historic_regims_pis_pisos` FOREIGN KEY (`pis`) REFERENCES `pisos` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_simpatitzant_historic_regims_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `sollicituds`
--
ALTER TABLE `sollicituds`
  ADD CONSTRAINT `fk_sollicituds_api_empreses` FOREIGN KEY (`api`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_estat_pis_estats_habitatge` FOREIGN KEY (`estat_pis`) REFERENCES `estats_habitatge` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_municipi_municipis` FOREIGN KEY (`municipi`) REFERENCES `municipis` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_origen_afiliacio_origens_afiliacio` FOREIGN KEY (`origen_afiliacio`) REFERENCES `origens_afiliacio` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_propietat_empreses` FOREIGN KEY (`propietat`) REFERENCES `empreses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_seccio_sindical_seccions_sindicals` FOREIGN KEY (`seccio_sindical`) REFERENCES `seccions_sindicals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_sollicituds_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `tecniques`
--
ALTER TABLE `tecniques`
  ADD CONSTRAINT `fk_tecniques_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tecniques_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tecniques_especialitat_especialitats` FOREIGN KEY (`especialitat`) REFERENCES `especialitats` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tecniques_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tecniques_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tecniques_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `tipus_assessoraments`
--
ALTER TABLE `tipus_assessoraments`
  ADD CONSTRAINT `fk_tipus_assessoraments_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_assessoraments_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_assessoraments_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_assessoraments_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_assessoraments_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `tipus_serveis_juridics`
--
ALTER TABLE `tipus_serveis_juridics`
  ADD CONSTRAINT `fk_tipus_serveis_juridics_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_serveis_juridics_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_serveis_juridics_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_serveis_juridics_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_serveis_juridics_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `tipus_sseguiment`
--
ALTER TABLE `tipus_sseguiment`
  ADD CONSTRAINT `fk_tipus_sseguiment_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_sseguiment_delete_user_users` FOREIGN KEY (`delete_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_sseguiment_owner_group_groups` FOREIGN KEY (`owner_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_sseguiment_owner_user_users` FOREIGN KEY (`owner_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_tipus_sseguiment_update_user_users` FOREIGN KEY (`update_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_users_default_group_groups` FOREIGN KEY (`default_group`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `user_groups`
--
ALTER TABLE `user_groups`
  ADD CONSTRAINT `fk_user_groups_child_id_groups` FOREIGN KEY (`child_id`) REFERENCES `groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_user_groups_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_user_groups_parent_id_users` FOREIGN KEY (`parent_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Restriccions per a la taula `user_roles`
--
ALTER TABLE `user_roles`
  ADD CONSTRAINT `fk_user_roles_child_id_roles` FOREIGN KEY (`child_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_user_roles_create_user_users` FOREIGN KEY (`create_user`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_user_roles_parent_id_users` FOREIGN KEY (`parent_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
