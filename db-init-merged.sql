-- =============================================================================
-- A24 Restaurant Platform - Complete Database Initialization
-- =============================================================================
-- Single merged file: extensions + all tables + all data + app tables
-- Generated from: init.sql + a24_finalschema + 03-app-tables.sql
-- =============================================================================

-- =============================================================================
-- SECTION: Extensions and setup
-- Source: restaurant-chatbot/db/init.sql
-- =============================================================================

-- =============================================================================
-- Restaurant AI Database Initialization
-- =============================================================================
-- This file sets up the database foundation (extensions, timezone).
--
-- Migration Strategy (Hybrid Approach):
-- - Docker handles: 01-schema.sql, 02-data.sql, 03-app-tables.sql (initial setup)
-- - App handles: 04+ migrations (incremental changes via app/core/migrations.py)
--
-- This approach ensures:
-- - Docker properly initializes complex schema (pg_dump files, multi-statement DDL)
-- - App handles incremental migrations without destroying volumes
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Note: pgvector extension not included in postgres:15-alpine
-- Install manually if needed: https://github.com/pgvector/pgvector

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Restaurant AI Database Initialized';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pgcrypto';
    RAISE NOTICE 'Timezone: UTC';
    RAISE NOTICE '';
    RAISE NOTICE 'Initial schema will be loaded by Docker (01-03)';
    RAISE NOTICE 'Incremental migrations handled by app (04+)';
    RAISE NOTICE '========================================';
END $$;


-- =============================================================================
-- SECTION: Full database schema and data
-- Source: petpooja-service/a24_finalschema_20251219_2.sql
-- =============================================================================

-- Adminer 5.3.0 PostgreSQL 17.5 dump

DROP TABLE IF EXISTS "account_lock";
CREATE TABLE "public"."account_lock" (
    "account_lock_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "account_lock_at" timestamptz,
    "account_lock_until" timestamptz,
    "account_lock_reason" text,
    "account_lock_failed_attempts" integer,
    "account_lock_unlocked_at" timestamptz,
    "account_lock_unlocked_by" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "account_lock_pkey" PRIMARY KEY ("account_lock_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "alembic_version";
CREATE TABLE "public"."alembic_version" (
    "version_num" character varying(32) NOT NULL,
    CONSTRAINT "alembic_version_pkc" PRIMARY KEY ("version_num")
)
WITH (oids = false);


DROP TABLE IF EXISTS "allergens";
CREATE TABLE "public"."allergens" (
    "allergen_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "allergen_name" character varying(255) NOT NULL,
    "allergen_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "allergens_pkey" PRIMARY KEY ("allergen_id")
)
WITH (oids = false);

INSERT INTO "allergens" ("allergen_id", "allergen_name", "allergen_description", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('77a068d9-82eb-46da-a5ea-a6d295e78163',	'Gluten',	'Found in wheat, barley, rye and oats',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('8e3f8afb-945f-41d2-b41c-bfa9e117fa4f',	'Dairy',	'Milk and milk-based products including cheese, butter, yogurt',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('2a2a3db7-6b67-488c-ae1f-050ae504b2b5',	'Peanuts',	'Peanuts and peanut-based products',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('7295f259-5fb2-463a-b8e5-e75a8cd9a9e1',	'Tree Nuts',	'Almonds, cashews, walnuts, pistachios, etc.',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('b927f2b8-9ee7-41eb-acd7-1b24403a7171',	'Shellfish',	'Shrimp, crab, lobster, prawns, crayfish',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('a95cbb80-621e-4a1d-9382-7d08624b81aa',	'Eggs',	'Eggs and egg-based products',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('26c5b6cd-e0db-468a-8581-04b9acdee9ce',	'Soy',	'Soybeans and soy-based products',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('dae98fd4-e836-4dd3-a049-e3e811495e2f',	'Wheat',	'Wheat and wheat-based products',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('0427d6ea-ed21-468a-9408-d5ca79947130',	'Fish',	'All types of fish',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('b86c2545-1836-418c-80d7-7ae7a48f3adf',	'Sesame',	'Sesame seeds and sesame oil',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('a06e852b-0860-46e6-b451-48979b675033',	'Mustard',	'Mustard seeds, oil, and paste',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('6041d84b-ca2b-45ec-94fa-375abe6338c3',	'Celery',	'Celery stalks, leaves, seeds, and celeriac',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('b5543c80-4664-4663-afd6-b6680ccbf73d',	'Lupin',	'Lupin seeds and flour',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('eafae1f8-9c90-4f0b-a7d9-77cda5dbfce6',	'Molluscs',	'Mussels, oysters, squid, snails',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f'),
('3e13a6f6-620e-4413-8c12-72b6da24af37',	'Sulphites',	'Sulphur dioxide and sulphites',	'2025-12-19 16:39:41.209217+05:30',	'2025-12-19 16:39:41.209217+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "branch_contact_table";
CREATE TABLE "public"."branch_contact_table" (
    "branch_contact_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "branch_id" uuid,
    "contact_type" character varying(255),
    "contact_value" character varying(255),
    "is_primary" boolean DEFAULT false,
    "contact_label" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "branch_contact_table_pkey" PRIMARY KEY ("branch_contact_id")
)
WITH (oids = false);

INSERT INTO "branch_contact_table" ("branch_contact_id", "branch_id", "contact_type", "contact_value", "is_primary", "contact_label", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('e9ba79e9-1fb9-4ccd-b032-e377b74f706c',	'c81a8694-3087-4a1e-9419-9e0144e623db',	'phone',	'7228959098',	't',	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "branch_info_table";
CREATE TABLE "public"."branch_info_table" (
    "branch_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "chain_id" uuid,
    "branch_name" character varying(255) NOT NULL,
    "branch_website_url" text,
    "branch_logo_url" text,
    "branch_personalized_greeting" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "is_active" boolean,
    "ext_petpooja_restaurant_id" character varying(255),
    CONSTRAINT "branch_info_table_pkey" PRIMARY KEY ("branch_id")
)
WITH (oids = false);

CREATE INDEX idx_branch_info_petpooja_rid ON public.branch_info_table USING btree (ext_petpooja_restaurant_id);

CREATE INDEX idx_branch_info_chain_branch ON public.branch_info_table USING btree (chain_id, branch_id);

INSERT INTO "branch_info_table" ("branch_id", "chain_id", "branch_name", "branch_website_url", "branch_logo_url", "branch_personalized_greeting", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "is_active", "ext_petpooja_restaurant_id") VALUES
('c81a8694-3087-4a1e-9419-9e0144e623db',	'a2f85907-c48a-47ca-b96c-89de28ed2483',	'Aswins sweets[34467]',	NULL,	NULL,	'Hello from Aswins Sweets',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	't',	'czw6b9ykas');

DROP TABLE IF EXISTS "branch_location_table";
CREATE TABLE "public"."branch_location_table" (
    "branch_location_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "branch_id" uuid,
    "address_line" text,
    "landmark" text,
    "pincode_id" uuid,
    "latitude" numeric(10,8),
    "longitude" numeric(11,8),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "branch_location_table_pkey" PRIMARY KEY ("branch_location_id")
)
WITH (oids = false);

INSERT INTO "branch_location_table" ("branch_location_id", "branch_id", "address_line", "landmark", "pincode_id", "latitude", "longitude", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('481b14ad-b976-48ce-8345-1f08f012e8cb',	'c81a8694-3087-4a1e-9419-9e0144e623db',	'Ahmedabad',	'Poonga Road',	'31001195-d51e-4297-92d9-38e74083665c',	1.00000000,	1.00000000,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "branch_policy";
CREATE TABLE "public"."branch_policy" (
    "branch_timing_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "opening_time" time without time zone,
    "closing_time" time without time zone,
    "food_ordering_start_time" time without time zone,
    "food_ordering_closing_time" time without time zone,
    "table_booking_open_time" time without time zone,
    "table_booking_close_time" time without time zone,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "order_type" character varying(255),
    "minimum_order_amount" numeric(5,2),
    "minimum_delivery_time_min" integer,
    "delivery_charge" numeric(5,2),
    "minimum_prep_time_min" integer,
    "calculate_tax_on_packing" boolean,
    "calculate_tax_on_delivery" boolean,
    "packaging_applicable_on" character varying(255),
    "packaging_charge" numeric(5,2),
    "packaging_charge_type" character varying(255),
    "delivery_hours_from1" time without time zone,
    "delivery_hours_to1" time without time zone,
    "delivery_hours_from2" time without time zone,
    "delivery_hours_to2" time without time zone,
    CONSTRAINT "branch_timing_policy_pkey" PRIMARY KEY ("branch_timing_id")
)
WITH (oids = false);

INSERT INTO "branch_policy" ("branch_timing_id", "restaurant_id", "opening_time", "closing_time", "food_ordering_start_time", "food_ordering_closing_time", "table_booking_open_time", "table_booking_close_time", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "order_type", "minimum_order_amount", "minimum_delivery_time_min", "delivery_charge", "minimum_prep_time_min", "calculate_tax_on_packing", "calculate_tax_on_delivery", "packaging_applicable_on", "packaging_charge", "packaging_charge_type", "delivery_hours_from1", "delivery_hours_to1", "delivery_hours_from2", "delivery_hours_to2") VALUES
('aa5c74f4-953d-4e87-82ff-071c60a70eb6',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'10:00:00',	'23:00:00',	'10:00:00',	'23:00:00',	'10:00:00',	'23:00:00',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL,	0.00,	30,	0.00,	30,	'f',	'f',	'NONE',	NULL,	'',	NULL,	NULL,	NULL,	NULL);

DROP TABLE IF EXISTS "chain_contact_table";
CREATE TABLE "public"."chain_contact_table" (
    "chain_contact_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "chain_id" uuid,
    "contact_type" character varying(255),
    "contact_value" character varying(255),
    "is_primary" boolean DEFAULT false,
    "contact_label" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "chain_contact_table_pkey" PRIMARY KEY ("chain_contact_id")
)
WITH (oids = false);

INSERT INTO "chain_contact_table" ("chain_contact_id", "chain_id", "contact_type", "contact_value", "is_primary", "contact_label", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('7636006b-9bd6-46ce-841e-448e1f19ad42',	'a2f85907-c48a-47ca-b96c-89de28ed2483',	'phone',	'9876543210',	't',	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('356037bf-07ea-4779-b9fe-59e9215ef85b',	'a2f85907-c48a-47ca-b96c-89de28ed2483',	'email',	'aswins@sweets.com',	'f',	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "chain_info_table";
CREATE TABLE "public"."chain_info_table" (
    "chain_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "chain_name" character varying(255) NOT NULL,
    "chain_website_url" text,
    "chain_logo_url" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "chain_type" character varying(255) NOT NULL,
    CONSTRAINT "chain_info_table_pkey" PRIMARY KEY ("chain_id")
)
WITH (oids = false);

INSERT INTO "chain_info_table" ("chain_id", "chain_name", "chain_website_url", "chain_logo_url", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "chain_type") VALUES
('a2f85907-c48a-47ca-b96c-89de28ed2483',	'Aswins sweets',	'aswinssweets.com',	'data:image/png;base64,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',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	'Restaurant');

DROP TABLE IF EXISTS "chain_location_table";
CREATE TABLE "public"."chain_location_table" (
    "chain_location_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "chain_id" uuid,
    "address_line" text,
    "landmark" text,
    "pincode_id" uuid,
    "latitude" numeric(10,8),
    "longitude" numeric(11,8),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "chain_location_table_pkey" PRIMARY KEY ("chain_location_id")
)
WITH (oids = false);

INSERT INTO "chain_location_table" ("chain_location_id", "chain_id", "address_line", "landmark", "pincode_id", "latitude", "longitude", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('7caff67c-60b2-4302-a0c2-2a685db7b0f2',	'a2f85907-c48a-47ca-b96c-89de28ed2483',	'123, Park st, Annanagar',	'Bus Stand',	'c8e6f4b5-3d86-4b51-88ba-2e084199eed0',	11.02200000,	12.02300000,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "city_table";
CREATE TABLE "public"."city_table" (
    "city_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "city_name" character varying(255) NOT NULL,
    "state_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "city_table_pkey" PRIMARY KEY ("city_id")
)
WITH (oids = false);

INSERT INTO "city_table" ("city_id", "city_name", "state_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('7328f7d2-4e1b-4648-9f85-5d1f132e832f',	'Chennai',	'777021eb-8469-479a-9fe6-e4bcbb754fc4',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('e7126541-cea5-49fc-8f0a-9a13ff44c09d',	'Ahmedabad',	'965117a8-cb18-40c2-b91e-751b5d974764',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "combo_item";
CREATE TABLE "public"."combo_item" (
    "combo_item_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "combo_item_component_id" uuid,
    "restaurant_id" uuid,
    "combo_type" character varying(255),
    "is_available" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "combo_item_pkey" PRIMARY KEY ("combo_item_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "combo_item_components";
CREATE TABLE "public"."combo_item_components" (
    "combo_item_component_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "combo_item_id" uuid,
    "menu_item_id" uuid,
    "quantity" integer DEFAULT '1',
    "is_optional" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "combo_item_components_pkey" PRIMARY KEY ("combo_item_component_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "country_table";
CREATE TABLE "public"."country_table" (
    "country_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "country_name" character varying(255) NOT NULL,
    "iso_code" character varying(8),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "country_table_pkey" PRIMARY KEY ("country_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX country_table_country_name_key ON public.country_table USING btree (country_name);

INSERT INTO "country_table" ("country_id", "country_name", "iso_code", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('5f8b485f-2ce9-45d6-8f81-915ffe145308',	'India',	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "cuisines";
CREATE TABLE "public"."cuisines" (
    "cuisine_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "cuisine_name" character varying(255),
    "cuisine_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "cuisines_pkey" PRIMARY KEY ("cuisine_id")
)
WITH (oids = false);

INSERT INTO "cuisines" ("cuisine_id", "cuisine_name", "cuisine_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('ef6c4623-b8cf-4aac-9126-2c8e39951563',	'South Indian',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('3d19c017-5028-4a55-ac97-5e95d4189b4c',	'North Indian',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('556607f0-ecd8-48a8-8fec-399f24d16863',	'Chinese',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('0bac581f-9e35-418b-8a87-2ec232ec4c94',	'Italian',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('adf00bd9-e2ca-4f82-88ab-1f1a7b33635f',	'Continental',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('d123b94c-8399-43af-926b-f7cd8f3b8e91',	'Mexican',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('37acbbc2-7781-4063-8601-cb47c7ddd247',	'Thai',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('ac674a75-de64-48c3-b938-2bd28e222294',	'Japanese',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('2ff64e99-2da6-4329-be2c-0eb98ac0b162',	'Mediterranean',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('2961bcf2-215d-4ab6-8b93-88c9706d3a8b',	'American',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('759d55a9-f752-402d-b7ca-d4b66f6945db',	'Korean',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('8a77dce8-d94e-4bf3-b36a-260dc572e2d6',	'Middle Eastern',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('0a7dd263-f685-4bf2-97b9-223f26d345ad',	'Mughlai',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('ed65ca49-c7d6-4ef0-afd5-94713487dd8f',	'Tandoori',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('514b1acc-7df3-4eee-8818-0d74c3e5bc87',	'Chettinad',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('a46c72a2-8bda-4aac-b4e1-8a50f1d2dcb9',	'Bengali',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('19f66bb0-537e-417a-bdd4-5bdb1cec8afb',	'Gujarati',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('1167b279-fea0-4bee-8496-f63219fc51be',	'Rajasthani',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('784c781e-946d-482d-af06-c8c02220bc68',	'Kerala',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('87a9e571-1588-4751-b963-dd217876366f',	'Street Food',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('cbf24f86-254b-4664-a14d-2095d16ddbc3',	'Fast Food',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('5e6a19e0-db83-4439-9a6f-bd2c7c457f26',	'Desserts',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('b3cdb8d8-c00b-4ab8-939d-571148736a7f',	'Beverages',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f'),
('94bc0578-9e6c-4064-8909-98fb87a04da2',	'Bakery',	'active',	'2025-12-19 16:39:41.223738+05:30',	'2025-12-19 16:39:41.223738+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "customer_activity_log";
CREATE TABLE "public"."customer_activity_log" (
    "log_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "activity_type" character varying(255),
    "activity_timestamp" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "ip_address" character varying(255),
    "user_agent" character varying(255),
    "details" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_activity_log_pkey" PRIMARY KEY ("log_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_address_table";
CREATE TABLE "public"."customer_address_table" (
    "customer_address_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "customer_address_type" character varying(255),
    "customer_address_label" character varying(255),
    "customer_street_address_1" text,
    "customer_street_address_2" text,
    "customer_city" text,
    "customer_state_province" text,
    "customer_postal_code" text,
    "customer_country" text,
    "customer_latitude" numeric(10,8),
    "customer_longitude" numeric(11,8),
    "customer_is_default" boolean DEFAULT false,
    "customer_delivery_instructions" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_address_table_pkey" PRIMARY KEY ("customer_address_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_allergens";
CREATE TABLE "public"."customer_allergens" (
    "customer_id" uuid NOT NULL,
    "allergen_id" uuid NOT NULL,
    "customer_allergen_severity" character varying(255),
    "customer_allergen_notes" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_allergens_pkey" PRIMARY KEY ("customer_id", "allergen_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_authentication";
CREATE TABLE "public"."customer_authentication" (
    "auth_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "auth_method" character varying(255),
    "auth_provider" character varying(255),
    "password_hash" text,
    "last_login" timestamptz,
    "failed_attempts" integer DEFAULT '0',
    "locked_until" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_authentication_pkey" PRIMARY KEY ("auth_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_consent";
CREATE TABLE "public"."customer_consent" (
    "consent_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "consent_type" character varying(255),
    "consent_given" boolean DEFAULT true,
    "consent_date" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "consent_withdrawn_at" timestamptz,
    "consent_method" character varying(255),
    "ip_address" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_consent_pkey" PRIMARY KEY ("consent_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_contact_table";
CREATE TABLE "public"."customer_contact_table" (
    "contact_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "customer_contact_type" character varying(255),
    "customer_contact_value" character varying(255),
    "customer_is_primary" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_contact_table_pkey" PRIMARY KEY ("contact_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_devices";
CREATE TABLE "public"."customer_devices" (
    "device_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "device_type" character varying(255),
    "device_name" character varying(255),
    "os" character varying(255),
    "browser" character varying(255),
    "first_seen" timestamptz,
    "last_seen" timestamptz,
    "is_trusted" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_devices_pkey" PRIMARY KEY ("device_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_dietary_restrictions";
CREATE TABLE "public"."customer_dietary_restrictions" (
    "customer_id" uuid NOT NULL,
    "dietary_restriction_id" uuid NOT NULL,
    "customer_dietary_restriction_severity" character varying(255),
    "customer_dietary_restriction_notes" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_dietary_restrictions_pkey" PRIMARY KEY ("customer_id", "dietary_restriction_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_favorite_items";
CREATE TABLE "public"."customer_favorite_items" (
    "favorite_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "menu_item_id" uuid,
    "added_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_favorite_items_pkey" PRIMARY KEY ("favorite_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_gender";
CREATE TABLE "public"."customer_gender" (
    "customer_gender_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_gender_name" character varying(255) NOT NULL,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_gender_pkey" PRIMARY KEY ("customer_gender_id")
)
WITH (oids = false);

INSERT INTO "customer_gender" ("customer_gender_id", "customer_gender_name", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('5d55aa23-a098-4cc3-b83e-f5922ea9d2c3',	'Male',	'2025-12-19 16:39:41.238688+05:30',	'2025-12-19 16:39:41.238688+05:30',	NULL,	NULL,	NULL,	'f'),
('9cdadd25-2a49-427d-8230-0f2946187d60',	'Female',	'2025-12-19 16:39:41.238688+05:30',	'2025-12-19 16:39:41.238688+05:30',	NULL,	NULL,	NULL,	'f'),
('ffe708ed-89c8-4182-b18d-9002d4eaa06c',	'Other',	'2025-12-19 16:39:41.238688+05:30',	'2025-12-19 16:39:41.238688+05:30',	NULL,	NULL,	NULL,	'f'),
('97f1fbb4-01f2-4027-b7df-243bb865b1b1',	'Prefer not to say',	'2025-12-19 16:39:41.238688+05:30',	'2025-12-19 16:39:41.238688+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "customer_info_table";
CREATE TABLE "public"."customer_info_table" (
    "customer_id" uuid NOT NULL,
    "customer_name" character varying(255),
    "customer_phone" character varying(50),
    "customer_email" character varying(255),
    "created_at" timestamptz DEFAULT now(),
    "updated_at" timestamptz DEFAULT now(),
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean,
    CONSTRAINT "customer_info_table_pkey" PRIMARY KEY ("customer_id")
)
WITH (oids = false);

CREATE INDEX ix_customer_info_table_customer_id ON public.customer_info_table USING btree (customer_id);


DROP TABLE IF EXISTS "customer_preferences";
CREATE TABLE "public"."customer_preferences" (
    "customer_preference_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_preferences_pkey" PRIMARY KEY ("customer_preference_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_profile_table";
CREATE TABLE "public"."customer_profile_table" (
    "customer_id" uuid NOT NULL,
    "customer_first_name" character varying(255),
    "customer_last_name" character varying(255),
    "customer_display_name" character varying(255),
    "customer_date_of_birth" date,
    "customer_gender_id" uuid,
    "language_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_profile_table_pkey" PRIMARY KEY ("customer_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_search_queries";
CREATE TABLE "public"."customer_search_queries" (
    "query_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "conversation_id" uuid,
    "search_query" text,
    "search_timestamp" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_search_queries_pkey" PRIMARY KEY ("query_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_sessions";
CREATE TABLE "public"."customer_sessions" (
    "session_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "session_token" text,
    "expires_at" timestamptz,
    "ip_address" character varying(255),
    "user_agent" character varying(255),
    "is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_sessions_pkey" PRIMARY KEY ("session_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_table";
CREATE TABLE "public"."customer_table" (
    "customer_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_account_status" character varying(20),
    "customer_type" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_table_pkey" PRIMARY KEY ("customer_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_tag_mapping";
CREATE TABLE "public"."customer_tag_mapping" (
    "customer_id" uuid NOT NULL,
    "tag_id" uuid NOT NULL,
    "tagged_by" uuid,
    "tagged_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_tag_mapping_pkey" PRIMARY KEY ("customer_id", "tag_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "customer_tags";
CREATE TABLE "public"."customer_tags" (
    "tag_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "tag_name" character varying(255) NOT NULL,
    "tag_category" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_tags_pkey" PRIMARY KEY ("tag_id")
)
WITH (oids = false);

INSERT INTO "customer_tags" ("tag_id", "tag_name", "tag_category", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('40a5cc01-7e15-4eb9-a3e7-0230a68f1763',	'VIP',	'loyalty',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('bf4b1e19-a8f2-412e-a563-1ac4a8a640f3',	'Regular',	'loyalty',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('45b0c633-81bd-4499-b72a-8d6f45c7164f',	'New Customer',	'lifecycle',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('aa84dae5-994c-4038-9dc5-6bffa889fd14',	'Loyal Customer',	'loyalty',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('1c9cdff6-4ef1-4f7b-82b0-519f46ff20c3',	'High Value',	'spending',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('378afad4-1182-4b37-af94-0d3b3be64aff',	'Frequent Visitor',	'behavior',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('6e4547d4-a9d2-4dd3-9cbe-e5ef099829ec',	'Corporate',	'type',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('2794f890-55ce-486b-ae0f-511bd756409b',	'Family',	'type',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('ffdbd131-c082-4d24-85bc-29ab523647ef',	'Student',	'type',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('0db21d8e-3f3d-4dea-a403-9c4e0ad5b8a0',	'Senior Citizen',	'type',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('27172556-f896-4047-a173-0d0fac60c4b3',	'Influencer',	'marketing',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('25d19382-4e23-4893-a263-0874dc8368fb',	'Birthday This Month',	'occasion',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('7c5827c0-04f8-4c11-bc44-a236a97b4021',	'Anniversary This Month',	'occasion',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('ee0fe0f9-c84b-4135-9ef8-e68b7c682e7f',	'Inactive',	'lifecycle',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f'),
('123e8f07-ff66-446c-bd5a-567da020253f',	'At Risk',	'lifecycle',	'2025-12-19 16:39:41.242502+05:30',	'2025-12-19 16:39:41.242502+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "department";
CREATE TABLE "public"."department" (
    "department_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "department_name" character varying(255),
    "department_unique_code" character varying(20),
    "department_description" text,
    "department_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "department_pkey" PRIMARY KEY ("department_id")
)
WITH (oids = false);

INSERT INTO "department" ("department_id", "department_name", "department_unique_code", "department_description", "department_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('e1f8759e-8f4f-4cd5-bdae-f4a280021e1e',	'Management',	'MGMT',	'Management and administration department',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('022d55d0-5b69-4631-90a2-5d83add5342d',	'Kitchen',	'KITCHEN',	'Food preparation and cooking department',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('acd0db3e-53fb-48bd-adbd-8b43a9efe4da',	'Service',	'SERVICE',	'Customer service and floor staff',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('b0d96d65-7770-4e0a-973e-6a7b3f6dc529',	'Delivery',	'DELIVERY',	'Food delivery department',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('dffe0c69-cc8c-4c83-8dcd-e8b8eadd44cd',	'Accounts',	'ACCOUNTS',	'Accounting and finance department',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('67408f81-3a00-46f8-891b-4ca892ff5589',	'Customer Support',	'SUPPORT',	'Customer support and complaints handling',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('02434523-57f0-49d5-870b-d45ec2c37035',	'Housekeeping',	'HOUSEKEEP',	'Cleaning and maintenance',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f'),
('3cf1759f-8c26-4b58-98c4-577968147b8b',	'Inventory',	'INVENTORY',	'Stock and inventory management',	'active',	'2025-12-19 16:39:41.315232+05:30',	'2025-12-19 16:39:41.315232+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "dietary_restrictions";
CREATE TABLE "public"."dietary_restrictions" (
    "dietary_restriction_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "dietary_restriction_name" character varying(255) NOT NULL,
    "dietary_restriction_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "dietary_restrictions_pkey" PRIMARY KEY ("dietary_restriction_id")
)
WITH (oids = false);

INSERT INTO "dietary_restrictions" ("dietary_restriction_id", "dietary_restriction_name", "dietary_restriction_description", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('970b98b7-3ab0-43ea-bf88-561515092f55',	'Vegetarian',	'No meat, poultry, or fish',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('b4d9dd31-0800-4ede-9d27-6441bda85130',	'Vegan',	'No animal products including dairy, eggs, and honey',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('c146f8c3-db28-4742-8325-6a383bd8e611',	'Gluten-Free',	'No gluten-containing grains',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('57ca24a1-17fe-4f7b-89a3-f908b260e432',	'Lactose Intolerant',	'No dairy products',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('8539b1b9-59e6-4f17-a6ba-b65bd42d5b47',	'Nut Allergy',	'No tree nuts or peanuts',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('86f56556-b878-4a4b-96c5-83053785aa2a',	'Halal',	'Prepared according to Islamic dietary laws',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('69c0f606-0df8-42b6-a135-774c012477ad',	'Kosher',	'Prepared according to Jewish dietary laws',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('c85eafc7-bfb4-48fe-a861-c2df6bd39255',	'Jain',	'No root vegetables, no onion, no garlic',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('bc6c1522-22d3-4f45-ad52-360b3b7ecbbc',	'Pescatarian',	'Vegetarian plus fish and seafood',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('6b771d54-dedf-439e-b233-e8112e244f7d',	'Eggetarian',	'Vegetarian plus eggs',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('a15a5f58-5a11-4716-b79d-7266401ad8d7',	'Low Sodium',	'Reduced salt diet',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('06899e99-a8d9-450d-bf53-07c443854785',	'Diabetic Friendly',	'Low sugar and low glycemic index',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('bc2bb22c-0fae-4552-ba36-bd89cfff36a7',	'Keto',	'Low carbohydrate, high fat diet',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f'),
('4dcc1764-6f80-4b0e-9404-cadea32cd603',	'Paleo',	'No processed foods, grains, or dairy',	'2025-12-19 16:39:41.253027+05:30',	'2025-12-19 16:39:41.253027+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "dietary_types";
CREATE TABLE "public"."dietary_types" (
    "dietary_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "dietary_type_name" character varying(255),
    "dietary_type_label" character varying(255),
    "dietary_type_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "dietary_types_pkey" PRIMARY KEY ("dietary_type_id")
)
WITH (oids = false);

INSERT INTO "dietary_types" ("dietary_type_id", "dietary_type_name", "dietary_type_label", "dietary_type_description", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('b6976039-33c3-4d36-aff5-aedc9ab880d2',	'veg',	'Vegetarian',	'Pure vegetarian food without any meat, fish or eggs',	'2025-12-19 16:39:41.261107+05:30',	'2025-12-19 16:39:41.261107+05:30',	NULL,	NULL,	NULL,	'f'),
('0c522ecd-8667-4294-a17f-61c63cd4b4cc',	'non-veg',	'Non-Vegetarian',	'Contains meat, poultry, or fish',	'2025-12-19 16:39:41.261107+05:30',	'2025-12-19 16:39:41.261107+05:30',	NULL,	NULL,	NULL,	'f'),
('48c544c1-2d70-4926-a1b3-466e97056606',	'egg',	'Contains Egg',	'Vegetarian but contains eggs',	'2025-12-19 16:39:41.261107+05:30',	'2025-12-19 16:39:41.261107+05:30',	NULL,	NULL,	NULL,	'f'),
('0a74fa33-0eb0-456a-9680-7140abeffbbc',	'vegan',	'Vegan',	'No animal products at all',	'2025-12-19 16:39:41.261107+05:30',	'2025-12-19 16:39:41.261107+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "discount";
CREATE TABLE "public"."discount" (
    "discount_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "discount_name" character varying(255),
    "discount_description" text,
    "discount_type" character varying(20),
    "discount_value" numeric(10,2),
    "discount_ordertype" character varying(20),
    "discount_applicable_on" text,
    "discount_days" text,
    "discount_status" character varying(20),
    "discount_rank" integer,
    "discount_on_total" boolean DEFAULT false,
    "discount_starts_at" timestamptz,
    "discount_time_from" time without time zone,
    "discount_time_to" time without time zone,
    "discount_min_amount" numeric(10,2),
    "discount_max_amount" numeric(10,2),
    "discount_has_coupon" boolean DEFAULT false,
    "discount_max_limit" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_discount_id" bigint,
    CONSTRAINT "discount_pkey" PRIMARY KEY ("discount_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "discount_schedule";
CREATE TABLE "public"."discount_schedule" (
    "discount_schedule_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "discount_id" uuid,
    "discount_schedule_day_of_week" integer,
    "discount_schedule_start_time" time without time zone,
    "discount_schedule_end_time" time without time zone,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "discount_schedule_pkey" PRIMARY KEY ("discount_schedule_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "discount_type";
CREATE TABLE "public"."discount_type" (
    "discount_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "discount_type_code" character varying(20),
    "discount_type_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "discount_type_pkey" PRIMARY KEY ("discount_type_id")
)
WITH (oids = false);

INSERT INTO "discount_type" ("discount_type_id", "discount_type_code", "discount_type_name", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('5715b61e-ef23-48c9-8677-561715ee3f87',	'PERCENTAGE',	'Percentage Discount',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('a1937354-ced2-4cf9-846f-60d221b4bce1',	'FLAT',	'Flat Amount Discount',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('d8b7939c-6f9d-44e8-a393-558a86369141',	'BOGO',	'Buy One Get One',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('bc0c2cf6-aea4-4509-9431-fe6f4ae41e09',	'FREE_ITEM',	'Free Item',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('0124fde6-04da-40a8-ab66-768b7fa50ad5',	'CASHBACK',	'Cashback',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('85bc297c-2e5d-41ba-a7ee-a2501d11a98b',	'FREE_DELIVERY',	'Free Delivery',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('87102fac-270f-42a7-852c-b7c719305512',	'COMBO',	'Combo Discount',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f'),
('c8608a9f-c198-401b-9334-b3028d02858b',	'FIRST_ORDER',	'First Order Discount',	'2025-12-19 16:39:41.265231+05:30',	'2025-12-19 16:39:41.265231+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "email_verification";
CREATE TABLE "public"."email_verification" (
    "email_verification_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "email_verification_email" character varying(255),
    "email_verification_otp" character varying(255),
    "email_verification_expires_at" timestamptz,
    "email_verification_verified_at" timestamptz,
    "email_verification_attempts" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "email_verification_pkey" PRIMARY KEY ("email_verification_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "entity_slot_config";
CREATE TABLE "public"."entity_slot_config" (
    "slot_config_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "slot_capacity" integer,
    "slot_duration" integer,
    "slot_frequency" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "entity_slot_config_pkey" PRIMARY KEY ("slot_config_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback";
CREATE TABLE "public"."feedback" (
    "feedback_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "is_anonymous" boolean DEFAULT false,
    "contact_email" character varying(255),
    "order_id" uuid,
    "booking_id" uuid,
    "product_id" uuid,
    "service_id" uuid,
    "title" character varying(255),
    "feedback_text" text NOT NULL,
    "rating" integer,
    "category_id" uuid,
    "feedback_type_id" uuid,
    "sentiment" text,
    "priority_id" uuid,
    "status_id" uuid,
    "assigned_to" uuid,
    "assigned_at" timestamptz,
    "platform_id" uuid,
    "device_info" character varying(255),
    "ip_address" character varying(255),
    "user_agent" character varying(255),
    "page_url" text,
    "is_urgent" boolean DEFAULT false,
    "is_featured" boolean DEFAULT false,
    "requires_followup" boolean DEFAULT false,
    "submitted_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "resolved_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_pkey" PRIMARY KEY ("feedback_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_attachments";
CREATE TABLE "public"."feedback_attachments" (
    "attachment_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "feedback_id" uuid,
    "file_name" character varying(255) NOT NULL,
    "file_path" text NOT NULL,
    "file_type" character varying(20),
    "file_size" bigint,
    "uploaded_by" uuid,
    "uploaded_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_attachments_pkey" PRIMARY KEY ("attachment_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_categories";
CREATE TABLE "public"."feedback_categories" (
    "category_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "category_name" character varying(255) NOT NULL,
    "description" text,
    "icon" text,
    "display_order" integer DEFAULT '0',
    "is_active" boolean DEFAULT true,
    "parent_category_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_categories_pkey" PRIMARY KEY ("category_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX feedback_categories_category_name_key ON public.feedback_categories USING btree (category_name);


DROP TABLE IF EXISTS "feedback_notifications";
CREATE TABLE "public"."feedback_notifications" (
    "notification_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "feedback_id" uuid,
    "recipient_email" character varying(255) NOT NULL,
    "notification_type" character varying(20),
    "subject" text,
    "sent_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "opened_at" timestamptz,
    "clicked_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_notifications_pkey" PRIMARY KEY ("notification_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_platforms";
CREATE TABLE "public"."feedback_platforms" (
    "platform_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "platform_name" character varying(255) NOT NULL,
    "platform_type" character varying(20),
    "is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "platforms_pkey" PRIMARY KEY ("platform_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX platforms_platform_name_key ON public.feedback_platforms USING btree (platform_name);


DROP TABLE IF EXISTS "feedback_priorities";
CREATE TABLE "public"."feedback_priorities" (
    "priority_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "priority_name" character varying(255) NOT NULL,
    "priority_level" integer,
    "color_code" character varying(20),
    "response_sla_hours" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "priorities_pkey" PRIMARY KEY ("priority_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX priorities_priority_name_key ON public.feedback_priorities USING btree (priority_name);


DROP TABLE IF EXISTS "feedback_priority_history";
CREATE TABLE "public"."feedback_priority_history" (
    "history_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "feedback_id" uuid,
    "old_priority_id" uuid,
    "new_priority_id" uuid,
    "changed_by" uuid,
    "changed_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "change_reason" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_priority_history_pkey" PRIMARY KEY ("history_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_responses";
CREATE TABLE "public"."feedback_responses" (
    "response_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "feedback_id" uuid,
    "responded_by" uuid,
    "response_text" text NOT NULL,
    "is_internal" boolean DEFAULT false,
    "is_automated" boolean DEFAULT false,
    "is_public" boolean DEFAULT false,
    "response_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "edited_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_responses_pkey" PRIMARY KEY ("response_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_status_history";
CREATE TABLE "public"."feedback_status_history" (
    "history_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "feedback_id" uuid,
    "old_status_id" uuid,
    "new_status_id" uuid,
    "changed_by" uuid,
    "changed_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "change_reason" text,
    "is_automated" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_status_history_pkey" PRIMARY KEY ("history_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_statuses";
CREATE TABLE "public"."feedback_statuses" (
    "status_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "status_name" character varying(255) NOT NULL,
    "description" text,
    "color_code" character varying(255),
    "is_initial" boolean DEFAULT false,
    "is_final" boolean DEFAULT false,
    "display_order" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "statuses_pkey" PRIMARY KEY ("status_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX statuses_status_name_key ON public.feedback_statuses USING btree (status_name);


DROP TABLE IF EXISTS "feedback_tags";
CREATE TABLE "public"."feedback_tags" (
    "feedback_id" uuid NOT NULL,
    "tag_id" uuid NOT NULL,
    "added_by" uuid,
    "added_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_tags_pkey" PRIMARY KEY ("feedback_id", "tag_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "feedback_types";
CREATE TABLE "public"."feedback_types" (
    "type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "type_name" character varying(255) NOT NULL,
    "description" text,
    "color_code" character varying(20),
    "icon" text,
    "requires_response" boolean DEFAULT true,
    "is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "feedback_types_pkey" PRIMARY KEY ("type_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX feedback_types_type_name_key ON public.feedback_types USING btree (type_name);


DROP TABLE IF EXISTS "integration_config_table";
CREATE TABLE "public"."integration_config_table" (
    "integration_config_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "provider_id" uuid,
    "is_enabled" boolean DEFAULT false,
    "api_key" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "restaurant_id" uuid,
    CONSTRAINT "integration_config_table_pkey" PRIMARY KEY ("integration_config_id")
)
WITH (oids = false);

CREATE INDEX idx_integration_config_rest_enabled ON public.integration_config_table USING btree (restaurant_id, is_enabled);

INSERT INTO "integration_config_table" ("integration_config_id", "provider_id", "is_enabled", "api_key", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "restaurant_id") VALUES
('90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'9205309f-df48-4bd1-858f-4b795f71c041',	't',	'client_q5kGbbAe02PLbygz6pk1tvEei0n78B2Kf8pYoTPzcwjP7PUYm2poW0HFkRnCYFNY',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	'58d98970-fe89-406a-a0fd-94581cb5a94c');

DROP TABLE IF EXISTS "integration_credentials_table";
CREATE TABLE "public"."integration_credentials_table" (
    "credential_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "integration_config_id" uuid,
    "credential_key" character varying(255),
    "credential_value" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "integration_credentials_table_pkey" PRIMARY KEY ("credential_id")
)
WITH (oids = false);

CREATE INDEX idx_integration_creds_config ON public.integration_credentials_table USING btree (integration_config_id, is_deleted);

INSERT INTO "integration_credentials_table" ("credential_id", "integration_config_id", "credential_key", "credential_value", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('2390c3d9-867e-4fef-aded-214aa39681e4',	'90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'app_key',	'gAAAAABpRTcxMJJi7ZUdG1tPHhbuP3MYEMumnTu17XuW_2chw5kc-EQ4m41PA_VbYRrBGz3zSjJ9A3Vxu16XyVT-ENeaiEx-nwndDF5a8KXZ6r5wok3appbcl-2ZOnQn8hReFJMMJvnT',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('75fe91c7-ab29-45ab-9360-2576348a317c',	'90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'app_secret',	'gAAAAABpRTcxlhIJJjmRGaj4dAh_vjvFzkOQaQLSLtHrn17vqhKUp13prnvIiu2auVLgoQLJjl6Zj1DsmmFffZ0yQFTltd-63iXqtYo04GhvvqUzbo7X5s-eKk0nNsbDWwWDv7H6-7QL',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c6b407fa-cb3e-4a2a-a26d-9c5b95ed8ad5',	'90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'access_token',	'gAAAAABpRTcxhs-CtAyL2Qc7V5eG5IX7PQPHfAuvhiDP_fnnv4lvgu6L9JHugJgBfkvLup7jTQ0LdsQ5fy7oPZzCaIBFbIp-8y_s-vnEzNBc_h0tA2WD8yNiS4BpOJn8Z08URSZpmVM7',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f9625de8-030e-4b96-9c4c-46ec7c64d22c',	'90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'restaurant_mapping_id',	'czw6b9ykas',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d3736fc8-e4a7-46c1-b502-36f81cca6449',	'90c102c3-e052-4c3a-b69a-387b53dfa2ab',	'petpooja_restaurantid',	'4878',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "integration_metadata_table";
CREATE TABLE "public"."integration_metadata_table" (
    "metadata_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "integration_config_id" uuid,
    "metadata_key" character varying(255),
    "metadata_value" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "integration_metadata_table_pkey" PRIMARY KEY ("metadata_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "integration_provider_table";
CREATE TABLE "public"."integration_provider_table" (
    "provider_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "provider_name" character varying(255) NOT NULL,
    "provider_description" text,
    "provider_base_url" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "integration_provider_table_pkey" PRIMARY KEY ("provider_id")
)
WITH (oids = false);

INSERT INTO "integration_provider_table" ("provider_id", "provider_name", "provider_description", "provider_base_url", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('9205309f-df48-4bd1-858f-4b795f71c041',	'Petpooja',	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "languages";
CREATE TABLE "public"."languages" (
    "language_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "language_iso" character varying(10) NOT NULL,
    "language_name" character varying(255) NOT NULL,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "languages_pkey" PRIMARY KEY ("language_id")
)
WITH (oids = false);

INSERT INTO "languages" ("language_id", "language_iso", "language_name", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('c1e234f4-4cff-4122-b2a9-182f4b1fd086',	'en',	'English',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('0290bb63-924c-42c2-9fd5-f3529409a5fd',	'hi',	'Hindi',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('ae2dcecb-11fe-4c8c-a0d4-cb18876ce7d7',	'ta',	'Tamil',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('e9b60138-5b70-4352-9158-e43c6c2cd8f4',	'te',	'Telugu',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('8606ef82-8e0a-4402-8b08-e6bcae6dacb8',	'kn',	'Kannada',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('5b59d07f-5a92-48e4-9758-7668bebacf56',	'ml',	'Malayalam',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('0bad44c8-f738-47d0-a888-bc4e97b42108',	'mr',	'Marathi',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('e68158fd-74b2-419b-8111-5dabda650a73',	'gu',	'Gujarati',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('827eb2c7-0acf-438d-a548-7764c64e169a',	'bn',	'Bengali',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('e117dc78-306e-46f9-aaff-671ce715d383',	'pa',	'Punjabi',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('9478ea6f-cd69-4f02-ba58-9ff1d3479c1a',	'or',	'Odia',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f'),
('b1703f72-eb16-4a51-8610-51f59108530c',	'as',	'Assamese',	'2025-12-19 16:39:41.27135+05:30',	'2025-12-19 16:39:41.27135+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "login_attempt";
CREATE TABLE "public"."login_attempt" (
    "login_attempt_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "login_attempt_email" character varying(255),
    "login_attempt_success" boolean DEFAULT false,
    "login_attempt_ip_address" character varying(255),
    "login_attempt_user_agent" character varying(255),
    "login_attempt_failure_reason" text,
    "login_attempt_attempted_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "login_attempt_pkey" PRIMARY KEY ("login_attempt_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "loyalty_transaction";
CREATE TABLE "public"."loyalty_transaction" (
    "loyalty_txn_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_id" uuid,
    "order_id" uuid,
    "payment_transaction_id" uuid,
    "points_used" integer DEFAULT '0',
    "points_earned" integer DEFAULT '0',
    "points_balance_after" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "loyalty_transaction_pkey" PRIMARY KEY ("loyalty_txn_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "meal_slot_timing";
CREATE TABLE "public"."meal_slot_timing" (
    "meal_slot_timing_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "slot_config_id" uuid,
    "meal_type_id" uuid,
    "opening_time" time without time zone,
    "closing_time" time without time zone,
    "is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "meal_slot_timing_pkey" PRIMARY KEY ("meal_slot_timing_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "meal_type";
CREATE TABLE "public"."meal_type" (
    "meal_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "meal_type_name" character varying(255),
    "display_order" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "meal_type_pkey" PRIMARY KEY ("meal_type_id")
)
WITH (oids = false);

INSERT INTO "meal_type" ("meal_type_id", "meal_type_name", "display_order", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('dad20a2b-b485-40f4-8d61-1e1692581872',	'Breakfast',	1,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f'),
('60613e2a-6562-4818-b62d-35d4d585cdaf',	'Lunch',	2,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f'),
('1b953fee-e406-48bf-85ff-c10313a7bca2',	'Snacks',	3,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f'),
('5ec1c06a-39f3-47e1-971f-3e0c8b72ab03',	'Dinner',	4,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f'),
('d9aabf3a-2b47-4e06-8bda-62fed8965f05',	'Late Night',	5,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f'),
('8e57bd2f-3652-4056-8b3a-2741c2ecb8a9',	'All Day',	6,	'2025-12-19 16:39:41.278306+05:30',	'2025-12-19 16:39:41.278306+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "menu_categories";
CREATE TABLE "public"."menu_categories" (
    "menu_category_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_category_status" character varying(20),
    "menu_category_rank" integer,
    "menu_category_name" character varying(255),
    "menu_category_description" text,
    "menu_category_timings" text,
    "menu_category_image_url" text,
    "menu_parent_category_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_group_category_id" bigint,
    CONSTRAINT "menu_categories_pkey" PRIMARY KEY ("menu_category_id")
)
WITH (oids = false);

-- [INSERT data for menu_categories removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item";
CREATE TABLE "public"."menu_item" (
    "menu_item_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_sub_category_id" uuid,
    "menu_item_name" character varying(255),
    "menu_item_status" character varying(20),
    "menu_item_description" text,
    "menu_item_price" numeric(12,2) DEFAULT '0',
    "menu_item_allow_variation" boolean DEFAULT false,
    "menu_item_allow_addon" boolean DEFAULT false,
    "menu_item_minimum_preparation_time" integer,
    "menu_item_tax_id" uuid,
    "menu_item_tax_cgst" numeric(8,2),
    "menu_item_tax_sgst" numeric(8,2),
    "menu_item_timings" text,
    "menu_item_packaging_charges" numeric(10,2) DEFAULT '0',
    "menu_item_attribute_id" uuid,
    "menu_item_rank" integer,
    "menu_item_favorite" boolean DEFAULT false,
    "menu_item_ignore_taxes" boolean DEFAULT false,
    "menu_item_ignore_discounts" boolean DEFAULT false,
    "menu_item_in_stock" boolean DEFAULT true,
    "menu_item_is_combo" boolean DEFAULT false,
    "menu_item_is_recommended" boolean DEFAULT false,
    "menu_item_spice_level" character varying(50),
    "menu_item_addon_based_on" text,
    "menu_item_markup_price" numeric(12,2),
    "menu_item_is_combo_parent" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_item_id" bigint,
    "menu_item_quantity" integer DEFAULT 0,
    "menu_item_calories" integer,
    "menu_item_is_seasonal" boolean DEFAULT false,
    "menu_item_image_url" character varying(500),
    "menu_item_serving_unit" character varying(20),
    CONSTRAINT "menu_item_pkey" PRIMARY KEY ("menu_item_id")
)
WITH (oids = false);

-- [INSERT data for menu_item removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_addon_group";
CREATE TABLE "public"."menu_item_addon_group" (
    "menu_item_addon_group_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_item_addon_group_name" character varying(255),
    "menu_item_addon_group_rank" integer,
    "menu_item_addon_group_status" character varying(20),
    "menu_item_addon_group_selection_min" integer,
    "menu_item_addon_group_selection_max" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_addon_group_id" bigint,
    CONSTRAINT "menu_item_addon_group_pkey" PRIMARY KEY ("menu_item_addon_group_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_addon_group removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_addon_item";
CREATE TABLE "public"."menu_item_addon_item" (
    "menu_item_addon_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_addon_group_id" uuid,
    "restaurant_id" uuid,
    "menu_item_addon_item_name" character varying(255),
    "menu_item_addon_item_price" numeric(10,2),
    "menu_item_addon_item_status" character varying(20),
    "menu_item_addon_item_rank" integer,
    "menu_item_addon_item_attribute_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_addon_item_id" bigint,
    CONSTRAINT "menu_item_addon_item_pkey" PRIMARY KEY ("menu_item_addon_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_addon_item removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_addon_mapping";
CREATE TABLE "public"."menu_item_addon_mapping" (
    "menu_item_addon_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "menu_item_variation_id" uuid,
    "menu_item_addon_group_id" uuid,
    "restaurant_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_addon_mapping_pkey" PRIMARY KEY ("menu_item_addon_mapping_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_addon_mapping removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_attribute";
CREATE TABLE "public"."menu_item_attribute" (
    "menu_item_attribute_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_attribute_name" character varying(255),
    "menu_item_attribute_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_attributes_id" bigint,
    "restaurant_id" uuid,
    CONSTRAINT "menu_item_attribute_pkey" PRIMARY KEY ("menu_item_attribute_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_attribute removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_availability_schedule";
CREATE TABLE "public"."menu_item_availability_schedule" (
    "schedule_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "day_of_week" character varying(255),
    "time_from" time without time zone,
    "time_to" time without time zone,
    "is_available" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_availability_schedule_pkey" PRIMARY KEY ("schedule_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_item_cuisine_mapping";
CREATE TABLE "public"."menu_item_cuisine_mapping" (
    "menu_item_cuisine_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "cuisine_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_cuisine_mapping_pkey" PRIMARY KEY ("menu_item_cuisine_mapping_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_item_discount_mapping";
CREATE TABLE "public"."menu_item_discount_mapping" (
    "menu_item_discount_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "discount_id" uuid,
    "restaurant_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_discount_mapping_pkey" PRIMARY KEY ("menu_item_discount_mapping_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_item_option";
CREATE TABLE "public"."menu_item_option" (
    "menu_item_option_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "menu_item_option_name" character varying(255),
    "menu_item_option_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_option_pkey" PRIMARY KEY ("menu_item_option_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_item_ordertype_mapping";
CREATE TABLE "public"."menu_item_ordertype_mapping" (
    "menu_item_ordertype_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "menu_item_ordertype_id" uuid,
    "restaurant_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_ordertype_mapping_pkey" PRIMARY KEY ("menu_item_ordertype_mapping_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_item_tag";
CREATE TABLE "public"."menu_item_tag" (
    "menu_item_tag_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_tag_name" character varying(255),
    "menu_item_tag_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_tag_pkey" PRIMARY KEY ("menu_item_tag_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_tag removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_tag_mapping";
CREATE TABLE "public"."menu_item_tag_mapping" (
    "menu_item_tag_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "menu_item_tag_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_tag_mapping_pkey" PRIMARY KEY ("menu_item_tag_mapping_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_tag_mapping removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_tax_mapping";
CREATE TABLE "public"."menu_item_tax_mapping" (
    "menu_item_tax_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "restaurant_id" uuid,
    "tax_id" uuid,
    "is_tax_inclusive" boolean DEFAULT false,
    "gst_liability" text,
    "gst_type" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_tax_mapping_pkey" PRIMARY KEY ("menu_item_tax_mapping_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_tax_mapping removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_variation";
CREATE TABLE "public"."menu_item_variation" (
    "menu_item_variation_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "restaurant_id" uuid,
    "variation_group_id" uuid,
    "menu_item_variation_name" character varying(255),
    "menu_item_variation_price" numeric(12,2),
    "menu_item_variation_markup_price" numeric(12,2),
    "menu_item_variation_status" character varying(20),
    "menu_item_variation_rank" integer,
    "menu_item_variation_allow_addon" boolean DEFAULT false,
    "menu_item_variation_packaging_charges" numeric(10,2),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_variation_id" bigint,
    CONSTRAINT "menu_item_variation_pkey" PRIMARY KEY ("menu_item_variation_id")
)
WITH (oids = false);

-- [INSERT data for menu_item_variation removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_item_variation_mapping";
CREATE TABLE "public"."menu_item_variation_mapping" (
    "menu_item_variation_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "menu_item_id" uuid,
    "menu_item_variation_group_id" uuid,
    "menu_item_variation_rank" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_variation_mapping_pkey" PRIMARY KEY ("menu_item_variation_mapping_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_sections";
CREATE TABLE "public"."menu_sections" (
    "menu_section_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_section_status" character varying(20),
    "menu_section_name" character varying(255),
    "menu_section_description" text,
    "menu_section_image_url" text,
    "menu_section_rank" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_parent_categories_id" bigint NOT NULL,
    CONSTRAINT "menu_sections_pkey" PRIMARY KEY ("menu_section_id")
)
WITH (oids = false);

-- [INSERT data for menu_sections removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_sub_categories";
CREATE TABLE "public"."menu_sub_categories" (
    "menu_sub_category_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "category_id" uuid,
    "sub_category_status" character varying(20),
    "sub_category_rank" integer,
    "sub_category_name" character varying(255),
    "sub_category_description" text,
    "sub_category_timings" text,
    "sub_category_image_url" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_categories_id" bigint,
    "menu_section_id" uuid,
    CONSTRAINT "menu_sub_categories_pkey" PRIMARY KEY ("menu_sub_category_id")
)
WITH (oids = false);

-- [INSERT data for menu_sub_categories removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "menu_sync_log";
CREATE TABLE "public"."menu_sync_log" (
    "menu_sync_log_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_sync_source" text,
    "menu_sync_status" character varying(20),
    "menu_sync_started_at" timestamptz,
    "menu_sync_completed_at" timestamptz,
    "menu_items_synced" jsonb,
    "menu_errors" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_sync_log_pkey" PRIMARY KEY ("menu_sync_log_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "menu_version_history";
CREATE TABLE "public"."menu_version_history" (
    "menu_version_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "menu_version_number" integer,
    "menu_version_changed_by" uuid,
    "menu_version_change_summary" text,
    "menu_version_snapshot_data" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_version_history_pkey" PRIMARY KEY ("menu_version_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_audit";
CREATE TABLE "public"."order_audit" (
    "order_audit_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "session_id" uuid,
    "order_version" integer,
    "modified_by" uuid,
    "modification_reason" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_audit_pkey" PRIMARY KEY ("order_audit_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_charges";
CREATE TABLE "public"."order_charges" (
    "order_charges_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "order_item_id" uuid,
    "order_charges_type" character varying(20),
    "order_charges_base_amount" numeric(10,2),
    "order_charges_taxable_amount" numeric(10,2),
    "order_charges_metadata_json" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_charges_pkey" PRIMARY KEY ("order_charges_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_customer_details";
CREATE TABLE "public"."order_customer_details" (
    "order_customer_details_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "customer_id" uuid,
    "restaurant_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_customer_details_pkey" PRIMARY KEY ("order_customer_details_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_delivery_info";
CREATE TABLE "public"."order_delivery_info" (
    "order_delivery_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "delivery_partner_id" uuid,
    "enable_delivery" boolean DEFAULT false,
    "delivery_type" character varying(20),
    "delivery_slot" text,
    "delivery_address_id" uuid,
    "delivery_distance_km" numeric(10,2),
    "delivery_estimated_time" timestamptz,
    "delivery_actual_time" timestamptz,
    "delivery_person_id" uuid,
    "delivery_started_at" timestamptz,
    "delivery_completed_at" timestamptz,
    "delivery_otp" character varying(20),
    "delivery_verification_method" character varying(255),
    "delivery_tracking_url" text,
    "delivery_proof_url" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_delivery_info_pkey" PRIMARY KEY ("order_delivery_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_dining_info";
CREATE TABLE "public"."order_dining_info" (
    "order_dining_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "table_id" uuid,
    "table_no" integer,
    "table_area" character varying(255),
    "no_of_persons" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_dining_info_pkey" PRIMARY KEY ("order_dining_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_discount";
CREATE TABLE "public"."order_discount" (
    "order_discount_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_discount_type_id" uuid,
    "order_id" uuid,
    "order_item_id" uuid,
    "order_discount_amount" numeric(10,2),
    "order_discount_percentage" numeric(5,2),
    "order_discount_code" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_discount_pkey" PRIMARY KEY ("order_discount_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_instruction";
CREATE TABLE "public"."order_instruction" (
    "order_instruction_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "special_instructions" text,
    "kitchen_notes" text,
    "delivery_notes" text,
    "allergen_warning" text,
    "dietary_preferences" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_instruction_pkey" PRIMARY KEY ("order_instruction_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_integration_sync";
CREATE TABLE "public"."order_integration_sync" (
    "order_integration_sync_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "sync_status" character varying(20),
    "sync_errors" text,
    "last_synced_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_integration_sync_pkey" PRIMARY KEY ("order_integration_sync_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_invoice";
CREATE TABLE "public"."order_invoice" (
    "order_invoice_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "is_invoice_generated" boolean DEFAULT false,
    "invoice_url" text,
    "invoice_generated_at" timestamptz,
    "gstin" character varying(255),
    "is_business_order" boolean DEFAULT false,
    "business_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_invoice_pkey" PRIMARY KEY ("order_invoice_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_item";
CREATE TABLE "public"."order_item" (
    "order_item_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "menu_item_id" uuid,
    "menu_item_variation_id" uuid,
    "sku" character varying(100),
    "hsn_code" character varying(20),
    "category_id" uuid,
    "category_name" character varying(100),
    "base_price" numeric(10,2),
    "discount_amount" numeric(10,2),
    "tax_amount" numeric(10,2),
    "addon_total" numeric(10,2),
    "is_available" boolean DEFAULT true,
    "unavailable_reason" text,
    "substitute_item_id" uuid,
    "cooking_instructions" text,
    "spice_level" character varying(20),
    "customizations" jsonb,
    "item_status" character varying(50),
    "prepared_at" timestamptz,
    "served_at" timestamptz,
    "cancelled_at" timestamptz,
    "cancellation_reason" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_item_pkey" PRIMARY KEY ("order_item_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_kitchen_detail";
CREATE TABLE "public"."order_kitchen_detail" (
    "order_kitchen_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "order_item_id" uuid,
    "estimated_ready_time" timestamptz,
    "actual_ready_time" timestamptz,
    "preparation_start_time" timestamptz,
    "minimum_preparation_time" integer,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_kitchen_detail_pkey" PRIMARY KEY ("order_kitchen_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_note";
CREATE TABLE "public"."order_note" (
    "order_note_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "order_note_type" character varying(20),
    "order_note_text" text,
    "order_note_visibility" boolean DEFAULT true,
    "order_note_added_by" uuid,
    "is_important" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_note_pkey" PRIMARY KEY ("order_note_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_payment";
CREATE TABLE "public"."order_payment" (
    "order_payment_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_order_id" uuid,
    "primary_transaction_id" uuid,
    "order_id" uuid,
    "order_payment_method_id" uuid,
    "tax_calculation_type_id" uuid,
    "paid_amount" numeric(12,2),
    "refund_amount" numeric(12,2),
    "wallet_amount_used" numeric(12,2),
    "loyalty_points_used" integer,
    "loyalty_points_earned" integer,
    "collect_cash" boolean DEFAULT false,
    "order_payment_status" character varying(20),
    "order_payment_transaction_reference" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_payment_pkey" PRIMARY KEY ("order_payment_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_payment_method";
CREATE TABLE "public"."order_payment_method" (
    "order_payment_method_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_payment_method_code" character varying(20),
    "order_payment_method_name" character varying(255),
    "order_payment_method_is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_payment_method_pkey" PRIMARY KEY ("order_payment_method_id")
)
WITH (oids = false);

INSERT INTO "order_payment_method" ("order_payment_method_id", "order_payment_method_code", "order_payment_method_name", "order_payment_method_is_active", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('0281452c-b065-47a9-adf6-7c3cd08276a3',	'CASH',	'Cash',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('6e764bd3-a061-47b0-b11f-cfc2b9c91249',	'CARD',	'Credit/Debit Card',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('ec7ab5f3-aa84-40f0-b505-13b5d08c62a4',	'UPI',	'UPI',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('0332578e-b542-4869-a915-6faa5b987382',	'WALLET',	'Digital Wallet',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('8318cfcc-6b99-4299-8ded-688047b88134',	'NET_BANKING',	'Net Banking',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('0e045867-87b4-48da-a9e3-8bf5d3b4c839',	'COD',	'Cash on Delivery',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('5b680e4e-0c5d-4631-955a-db6c2cc5d971',	'PREPAID',	'Prepaid',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('39d150da-63a9-4238-b78d-77457a8dd348',	'PAY_LATER',	'Pay Later',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f'),
('8911f697-1224-4be6-a489-4e819aabbc61',	'SPLIT',	'Split Payment',	't',	'2025-12-19 16:39:41.283204+05:30',	'2025-12-19 16:39:41.283204+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "order_priority";
CREATE TABLE "public"."order_priority" (
    "order_priority_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "is_urgent" boolean DEFAULT false,
    "priority_level" integer,
    "is_vip_order" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_priority_pkey" PRIMARY KEY ("order_priority_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_scheduling";
CREATE TABLE "public"."order_scheduling" (
    "order_scheduling_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "is_preorder" boolean DEFAULT false,
    "is_scheduled" boolean DEFAULT false,
    "preorder_date" date,
    "preorder_time" time without time zone,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_scheduling_pkey" PRIMARY KEY ("order_scheduling_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_security_detail";
CREATE TABLE "public"."order_security_detail" (
    "order_security_detail_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "otp" character varying(255),
    "callback_url" text,
    "callback_received_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_security_detail_pkey" PRIMARY KEY ("order_security_detail_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_source_type";
CREATE TABLE "public"."order_source_type" (
    "order_source_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_source_type_code" character varying(20),
    "order_source_type_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_source_type_pkey" PRIMARY KEY ("order_source_type_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_status_history";
CREATE TABLE "public"."order_status_history" (
    "order_status_history_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "order_status_type_id" uuid,
    "order_status_changed_by" uuid,
    "order_status_changed_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "order_status_notes" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_status_history_pkey" PRIMARY KEY ("order_status_history_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_status_type";
CREATE TABLE "public"."order_status_type" (
    "order_status_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_status_code" character varying(20),
    "order_status_name" character varying(255),
    "order_status_description" text,
    "order_status_is_active" boolean DEFAULT true,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_status_type_pkey" PRIMARY KEY ("order_status_type_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_tax_line";
CREATE TABLE "public"."order_tax_line" (
    "order_tax_line_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_tax_line_charge_id" uuid,
    "order_item_id" uuid,
    "order_tax_line_tax_type" character varying(20),
    "order_tax_line_percentage" numeric(5,2),
    "order_tax_line_amount" numeric(10,2),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_tax_line_pkey" PRIMARY KEY ("order_tax_line_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_total";
CREATE TABLE "public"."order_total" (
    "order_total_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "items_total" numeric(12,2),
    "addons_total" numeric(12,2),
    "charges_total" numeric(12,2),
    "discount_total" numeric(12,2),
    "tax_total" numeric(12,2),
    "platform_fee" numeric(10,2),
    "convenience_fee" numeric(10,2),
    "subtotal" numeric(12,2),
    "roundoff_amount" numeric(10,2),
    "total_before_tip" numeric(12,2),
    "tip_amount" numeric(10,2),
    "final_amount" numeric(12,2),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "order_total_pkey" PRIMARY KEY ("order_total_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "order_type_table";
CREATE TABLE "public"."order_type_table" (
    "order_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_type_code" character varying(20),
    "order_type_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_order_type_id" bigint,
    "restaurant_id" uuid,
    CONSTRAINT "order_type_table_pkey" PRIMARY KEY ("order_type_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "orders";
CREATE TABLE "public"."orders" (
    "order_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "table_booking_id" uuid,
    "order_number" bigint,
    "order_invoice_number" character varying(20),
    "order_vr_order_id" character varying(255),
    "order_external_reference_id" character varying(255),
    "order_type_id" uuid,
    "order_source_type_id" uuid,
    "order_status_type_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "orders_pkey" PRIMARY KEY ("order_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "password_reset";
CREATE TABLE "public"."password_reset" (
    "password_reset_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "password_reset_token" character varying(255),
    "password_reset_expires_at" timestamptz,
    "password_reset_used_at" timestamptz,
    "password_reset_ip_address" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "password_reset_pkey" PRIMARY KEY ("password_reset_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_audit_log";
CREATE TABLE "public"."payment_audit_log" (
    "audit_log_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_order_id" uuid,
    "payment_transaction_id" uuid,
    "payment_refund_id" uuid,
    "event_type" text,
    "event_source" text,
    "request_payload" jsonb,
    "response_payload" jsonb,
    "gateway_event_id" text,
    "gateway_event_type" text,
    "initiated_by" uuid,
    "ip_address" character varying(255),
    "user_agent" character varying(255),
    "event_status" character varying(20),
    "error_message" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_audit_log_pkey" PRIMARY KEY ("audit_log_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_external_mapping";
CREATE TABLE "public"."payment_external_mapping" (
    "external_mapping_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_order_id" uuid,
    "payment_transaction_id" uuid,
    "external_system" text,
    "external_payment_id" text,
    "external_order_id" text,
    "sync_status" character varying(20),
    "sync_attempts" integer DEFAULT '0',
    "last_synced_at" timestamptz,
    "sync_error" text,
    "external_response" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_external_mapping_pkey" PRIMARY KEY ("external_mapping_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_gateway";
CREATE TABLE "public"."payment_gateway" (
    "payment_gateway_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_gateway_code" character varying(20),
    "payment_gateway_name" character varying(255),
    "payment_gateway_is_active" boolean DEFAULT true,
    "payment_gateway_config" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_gateway_pkey" PRIMARY KEY ("payment_gateway_id")
)
WITH (oids = false);

INSERT INTO "payment_gateway" ("payment_gateway_id", "payment_gateway_code", "payment_gateway_name", "payment_gateway_is_active", "payment_gateway_config", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('bf409800-9905-4b16-825b-d4508d5b34b7',	'RAZORPAY',	'Razorpay',	't',	'{"supported_methods": ["card", "upi", "netbanking", "wallet"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f'),
('6104e6af-23c6-4469-87b4-e149e824028b',	'PAYU',	'PayU',	't',	'{"supported_methods": ["card", "upi", "netbanking", "wallet"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f'),
('0d4f7630-ccc6-47f3-9416-35eaf6b34169',	'PHONEPE',	'PhonePe',	't',	'{"supported_methods": ["upi", "wallet"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f'),
('cd96faf0-9ac7-4b05-99f9-783559769428',	'PAYTM',	'Paytm',	't',	'{"supported_methods": ["upi", "wallet", "card"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f'),
('63e5bf8f-682c-451b-bc18-cb85ae417187',	'STRIPE',	'Stripe',	'f',	'{"supported_methods": ["card"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f'),
('db707973-8137-460f-b563-c19d4a18a1c7',	'CASHFREE',	'Cashfree',	't',	'{"supported_methods": ["card", "upi", "netbanking"]}',	'2025-12-19 16:39:41.289397+05:30',	'2025-12-19 16:39:41.289397+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "payment_order";
CREATE TABLE "public"."payment_order" (
    "payment_order_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "order_id" uuid,
    "restaurant_id" uuid,
    "customer_id" uuid,
    "payment_gateway_id" uuid,
    "gateway_order_id" text,
    "payment_order_status" character varying(20),
    "order_amount" numeric(12,2),
    "order_currency" character varying(3) DEFAULT 'INR',
    "payment_link_url" text,
    "payment_link_id" character varying(255),
    "payment_link_short_url" text,
    "payment_link_expires_at" timestamptz,
    "retry_count" integer DEFAULT '0',
    "max_retry_attempts" integer DEFAULT '3',
    "notes" text,
    "metadata" jsonb,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_order_pkey" PRIMARY KEY ("payment_order_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_refund";
CREATE TABLE "public"."payment_refund" (
    "payment_refund_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_transaction_id" uuid,
    "order_id" uuid,
    "order_item_id" uuid,
    "payment_order_id" uuid,
    "payment_gateway_id" uuid,
    "gateway_refund_id" character varying(255),
    "gateway_payment_id" character varying(255),
    "refund_amount" numeric(12,2),
    "refund_currency" character varying(3) DEFAULT 'INR',
    "refund_reason_type_id" uuid,
    "refund_reason_notes" text,
    "refund_status_type_id" uuid,
    "initiated_by" uuid,
    "approved_by" uuid,
    "processing_notes" text,
    "gateway_response" jsonb,
    "refund_initiated_at" timestamptz,
    "refund_processed_at" timestamptz,
    "refund_completed_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_refund_pkey" PRIMARY KEY ("payment_refund_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_retry_attempt";
CREATE TABLE "public"."payment_retry_attempt" (
    "retry_attempt_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_order_id" uuid,
    "payment_transaction_id" uuid,
    "attempt_number" integer,
    "gateway_payment_id" text,
    "attempt_status" character varying(20),
    "failure_reason" text,
    "failure_code" character varying(20),
    "retry_metadata" jsonb,
    "attempted_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_retry_attempt_pkey" PRIMARY KEY ("retry_attempt_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_split";
CREATE TABLE "public"."payment_split" (
    "payment_split_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_transaction_id" uuid,
    "order_id" uuid,
    "split_party_type" character varying(20),
    "split_party_id" uuid,
    "split_amount" numeric(12,2),
    "split_percentage" numeric(5,2),
    "split_currency" character varying(3) DEFAULT 'INR',
    "delivery_partner_id" uuid,
    "is_settled" boolean DEFAULT false,
    "settled_at" timestamptz,
    "settlement_reference" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_split_pkey" PRIMARY KEY ("payment_split_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_status_type";
CREATE TABLE "public"."payment_status_type" (
    "payment_status_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_status_code" character varying(20),
    "payment_status_name" character varying(255),
    "payment_status_description" text,
    "payment_status_is_terminal" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_status_type_pkey" PRIMARY KEY ("payment_status_type_id")
)
WITH (oids = false);

INSERT INTO "payment_status_type" ("payment_status_type_id", "payment_status_code", "payment_status_name", "payment_status_description", "payment_status_is_terminal", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('6464c62d-a9e3-44f5-a351-288e151d79a4',	'PENDING',	'Pending',	'Payment initiated but not yet processed',	'f',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('ff5dcfeb-6cb0-4f60-bedf-2f98298f87bc',	'PROCESSING',	'Processing',	'Payment is being processed',	'f',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('ad20f5c0-4ec5-4e7b-a91c-ec2e5c4d2f40',	'AUTHORIZED',	'Authorized',	'Payment authorized but not captured',	'f',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('0367c7e0-46be-4cb6-acb0-408504708c8d',	'SUCCESS',	'Success',	'Payment completed successfully',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('88a56a1e-44b5-431c-b067-35db91b845c1',	'FAILED',	'Failed',	'Payment failed',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('ef2163f0-48bc-4e74-b187-e4856632ee66',	'CANCELLED',	'Cancelled',	'Payment cancelled by user',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('0e48ae63-f0bf-4e76-8505-292b738d314b',	'REFUNDED',	'Refunded',	'Payment has been refunded',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('71c0bdf7-494c-468e-92aa-fdc419c106ab',	'PARTIAL_REFUND',	'Partially Refunded',	'Payment has been partially refunded',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f'),
('f8828669-44db-4566-bf97-e2df9749e42c',	'EXPIRED',	'Expired',	'Payment session expired',	't',	'2025-12-19 16:39:41.29392+05:30',	'2025-12-19 16:39:41.29392+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "payment_transaction";
CREATE TABLE "public"."payment_transaction" (
    "payment_transaction_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_order_id" uuid,
    "order_id" uuid,
    "restaurant_id" uuid,
    "customer_id" uuid,
    "payment_gateway_id" uuid,
    "gateway_payment_id" text,
    "gateway_transaction_id" text,
    "gateway_signature" text,
    "order_payment_method_id" uuid,
    "payment_method_details" jsonb,
    "transaction_amount" numeric(12,2),
    "amount_paid" numeric(12,2),
    "amount_due" numeric(12,2),
    "transaction_currency" character varying(3) DEFAULT 'INR',
    "gateway_fee" numeric(10,2),
    "gateway_tax" numeric(10,2),
    "net_amount" numeric(12,2),
    "payment_status_type_id" uuid,
    "failure_reason" text,
    "failure_code" character varying(20),
    "error_description" text,
    "bank_name" text,
    "card_network" text,
    "card_type" text,
    "card_last4" character varying(4),
    "wallet_provider" text,
    "upi_vpa" text,
    "customer_email" text,
    "customer_contact" text,
    "gateway_response" jsonb,
    "attempted_at" timestamptz,
    "authorized_at" timestamptz,
    "captured_at" timestamptz,
    "settled_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_transaction_pkey" PRIMARY KEY ("payment_transaction_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "payment_webhook_log";
CREATE TABLE "public"."payment_webhook_log" (
    "webhook_log_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "payment_gateway_id" uuid,
    "webhook_event_id" text,
    "webhook_event_type" text,
    "webhook_payload" jsonb,
    "webhook_signature" text,
    "signature_verified" boolean DEFAULT false,
    "processing_status" character varying(20),
    "processing_attempts" integer DEFAULT '0',
    "processing_error" text,
    "extracted_payment_id" text,
    "extracted_order_id" text,
    "matched_payment_transaction_id" text,
    "source_ip" text,
    "received_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "processed_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "payment_webhook_log_pkey" PRIMARY KEY ("webhook_log_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "pincode_table";
CREATE TABLE "public"."pincode_table" (
    "pincode_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "pincode" character varying(255) NOT NULL,
    "city_id" uuid,
    "area_name" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "pincode_table_pkey" PRIMARY KEY ("pincode_id")
)
WITH (oids = false);

INSERT INTO "pincode_table" ("pincode_id", "pincode", "city_id", "area_name", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('c8e6f4b5-3d86-4b51-88ba-2e084199eed0',	'601001',	'7328f7d2-4e1b-4648-9f85-5d1f132e832f',	'Chennai',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('31001195-d51e-4297-92d9-38e74083665c',	'602012',	'e7126541-cea5-49fc-8f0a-9a13ff44c09d',	'Ahmedabad',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "refund_reason_type";
CREATE TABLE "public"."refund_reason_type" (
    "refund_reason_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "refund_reason_code" character varying(20),
    "refund_reason_name" character varying(255),
    "refund_reason_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "refund_reason_type_pkey" PRIMARY KEY ("refund_reason_type_id")
)
WITH (oids = false);

INSERT INTO "refund_reason_type" ("refund_reason_type_id", "refund_reason_code", "refund_reason_name", "refund_reason_description", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('183867e8-299b-418c-bca2-071c71dc1f23',	'CUSTOMER_REQUEST',	'Customer Request',	'Refund requested by customer',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('e497a025-4884-4f09-b476-07590b1cf557',	'ORDER_CANCELLED',	'Order Cancelled',	'Order was cancelled',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('0fd53d88-84ad-4e4b-a72e-271876f6df60',	'ITEM_UNAVAILABLE',	'Item Unavailable',	'Ordered item was not available',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('a1b19a38-c9f1-4248-a98b-751347667ccd',	'QUALITY_ISSUE',	'Quality Issue',	'Food quality was not satisfactory',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('2e1bb5b4-8ed4-4331-ae97-dc29be0fd248',	'WRONG_ORDER',	'Wrong Order',	'Wrong items were delivered',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('b914e894-1ba3-4470-88a1-6500895ba352',	'DELAYED_DELIVERY',	'Delayed Delivery',	'Order was significantly delayed',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('e90560e8-6b96-4ae3-9d10-29413f150081',	'MISSING_ITEMS',	'Missing Items',	'Some items were missing from order',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('dee708bc-8f23-4195-91d7-bd2af3bafefc',	'DUPLICATE_CHARGE',	'Duplicate Charge',	'Customer was charged twice',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('8b3056d8-fb55-4b1c-bb49-4c163f6a1735',	'RESTAURANT_CLOSED',	'Restaurant Closed',	'Restaurant was closed unexpectedly',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f'),
('a7c8d772-8349-4195-b5a4-9704f77b63bb',	'PAYMENT_ERROR',	'Payment Error',	'Error during payment processing',	'2025-12-19 16:39:41.300762+05:30',	'2025-12-19 16:39:41.300762+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "refund_status_type";
CREATE TABLE "public"."refund_status_type" (
    "refund_status_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "refund_status_code" character varying(20) NOT NULL,
    "refund_status_name" character varying(255) NOT NULL,
    "refund_status_description" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "refund_status_type_pkey" PRIMARY KEY ("refund_status_type_id")
)
WITH (oids = false);

INSERT INTO "refund_status_type" ("refund_status_type_id", "refund_status_code", "refund_status_name", "refund_status_description", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('9efd5fcb-1469-4a9c-b427-6e095c06d63e',	'INITIATED',	'Initiated',	'Refund request has been initiated',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('77ce2e96-044d-40d9-8d22-a9939e3750c1',	'PENDING',	'Pending',	'Refund is pending approval',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('490a39d3-78a9-426e-8489-7d434f325850',	'APPROVED',	'Approved',	'Refund has been approved',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('5264b410-b2dd-492d-9f0a-3f35a439999d',	'PROCESSING',	'Processing',	'Refund is being processed',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('0482f453-d269-47ce-b3a6-3859314b8680',	'COMPLETED',	'Completed',	'Refund has been completed',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('471e0fac-315c-42e9-bbd8-857d1842b43c',	'FAILED',	'Failed',	'Refund processing failed',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f'),
('ce9361ef-2511-45ed-9816-cdb7022e4d49',	'REJECTED',	'Rejected',	'Refund request was rejected',	'2025-12-19 16:39:41.307092+05:30',	'2025-12-19 16:39:41.307092+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "restaurant_faq";
CREATE TABLE "public"."restaurant_faq" (
    "restaurant_faq_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "restaurant_faq_question" text NOT NULL,
    "restaurant_faq_answer" text NOT NULL,
    "restaurant_faq_category" character varying(100),
    "restaurant_faq_display_order" integer DEFAULT '0',
    "restaurant_faq_is_active" boolean DEFAULT true,
    "restaurant_faq_view_count" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "restaurant_faq_pkey" PRIMARY KEY ("restaurant_faq_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "restaurant_policy";
CREATE TABLE "public"."restaurant_policy" (
    "restaurant_policy_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "restaurant_policy_category" character varying(100) NOT NULL,
    "restaurant_policy_title" text NOT NULL,
    "restaurant_policy_description" text,
    "restaurant_is_active" boolean DEFAULT true,
    "restaurant_effective_from" date,
    "restaurant_effective_until" date,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "restaurant_policy_pkey" PRIMARY KEY ("restaurant_policy_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "restaurant_table";
CREATE TABLE "public"."restaurant_table" (
    "restaurant_id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "chain_id" uuid NOT NULL,
    "branch_id" uuid NOT NULL,
    "created_at" timestamptz DEFAULT now(),
    "updated_at" timestamptz DEFAULT now(),
    "is_deleted" boolean DEFAULT false,
    "deleted_at" timestamptz,
    "iframe" text,
    CONSTRAINT "restaurant_table_pkey" PRIMARY KEY ("restaurant_id")
)
WITH (oids = false);

CREATE INDEX idx_restaurant_chain_branch ON public.restaurant_table USING btree (chain_id, branch_id);

INSERT INTO "restaurant_table" ("restaurant_id", "chain_id", "branch_id", "created_at", "updated_at", "is_deleted", "deleted_at", "iframe") VALUES
('58d98970-fe89-406a-a0fd-94581cb5a94c',	'a2f85907-c48a-47ca-b96c-89de28ed2483',	'c81a8694-3087-4a1e-9419-9e0144e623db',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	'f',	NULL,	'<iframe
  src="https://chatbot.assist24.com/?api_key=client_q5kGbbAe02PLbygz6pk1tvEei0n78B2Kf8pYoTPzcwjP7PUYm2poW0HFkRnCYFNY"
  width="100%"
  height="700px"
  style="border:none; border-radius:16px;"
  allow="microphone"
></iframe>');

DROP TABLE IF EXISTS "role";
CREATE TABLE "public"."role" (
    "role_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "role_name" character varying(255) NOT NULL,
    "role_unique_code" character varying(50) NOT NULL,
    "role_description" text,
    "role_level" integer,
    "is_system_role" boolean DEFAULT false,
    "role_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "role_pkey" PRIMARY KEY ("role_id")
)
WITH (oids = false);

INSERT INTO "role" ("role_id", "role_name", "role_unique_code", "role_description", "role_level", "is_system_role", "role_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('db8224f8-b6e7-49bf-84bd-0699c410425e',	'Super Admin',	'SUPER_ADMIN',	'Full system access with all permissions',	1,	't',	'active',	'2025-12-19 16:39:41.311811+05:30',	'2025-12-19 16:39:41.311811+05:30',	NULL,	NULL,	NULL,	'f'),
('798d684e-279e-43c8-add4-da4879583d2f',	'Manager',	'HOTEL_MANAGERS',	'Restaurant manager with operational access',	3,	'f',	'active',	'2025-12-19 16:39:41.311811+05:30',	'2025-12-19 16:39:41.311811+05:30',	NULL,	NULL,	NULL,	'f'),
('468bef1b-8189-4bbb-ae60-a1085564894d',	'Front Desk',	'HOTEL_FRONT_DESK_STAFF',	'Restaurant Front desk staff with booking access',	3,	'f',	'active',	'2025-12-19 16:39:41.311811+05:30',	'2025-12-19 16:39:41.311811+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "round_robin_pool";
CREATE TABLE "public"."round_robin_pool" (
    "round_robin_pool_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "round_robin_pool_name" character varying(255),
    "round_robin_pool_type" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "round_robin_pool_pkey" PRIMARY KEY ("round_robin_pool_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "round_robin_pool_member";
CREATE TABLE "public"."round_robin_pool_member" (
    "round_robin_pool_member_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "round_robin_pool_id" uuid NOT NULL,
    "user_id" uuid NOT NULL,
    "round_robin_pool_member_priority" integer,
    "round_robin_pool_member_is_active" boolean DEFAULT true,
    "round_robin_pool_member_last_assigned_at" timestamptz,
    "round_robin_pool_member_total_assignments" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "round_robin_pool_member_pkey" PRIMARY KEY ("round_robin_pool_member_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "shift_timing";
CREATE TABLE "public"."shift_timing" (
    "shift_timing_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "shift_timing_name" character varying(255),
    "shift_timing_shift_code" character varying(20),
    "shift_timing_start_time" time without time zone,
    "shift_timing_end_time" time without time zone,
    "shift_timing_break_duration_minutes" integer,
    "shift_timing_is_overnight" boolean DEFAULT false,
    "shift_timing_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "shift_timing_pkey" PRIMARY KEY ("shift_timing_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "state_table";
CREATE TABLE "public"."state_table" (
    "state_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "state_name" character varying(255) NOT NULL,
    "country_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "state_table_pkey" PRIMARY KEY ("state_id")
)
WITH (oids = false);

INSERT INTO "state_table" ("state_id", "state_name", "country_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('777021eb-8469-479a-9fe6-e4bcbb754fc4',	'Tamil Nadu',	'5f8b485f-2ce9-45d6-8f81-915ffe145308',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('965117a8-cb18-40c2-b91e-751b5d974764',	'Gujarat',	'5f8b485f-2ce9-45d6-8f81-915ffe145308',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "table_booking_info";
CREATE TABLE "public"."table_booking_info" (
    "table_booking_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "table_id" uuid NOT NULL,
    "meal_slot_timing_id" uuid,
    "previous_slot_id" uuid,
    "customer_id" uuid NOT NULL,
    "occasion_id" uuid,
    "party_size" integer,
    "booking_date" date,
    "booking_time" time without time zone,
    "booking_status" character varying(20),
    "special_request" text,
    "cancellation_reason" text,
    "is_advance_booking" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "table_booking_info_pkey" PRIMARY KEY ("table_booking_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "table_booking_occasion_info";
CREATE TABLE "public"."table_booking_occasion_info" (
    "occasion_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "occasion_type" character varying(255) NOT NULL,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "table_booking_occasion_info_pkey" PRIMARY KEY ("occasion_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "table_info";
CREATE TABLE "public"."table_info" (
    "table_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "table_number" integer,
    "table_capacity" integer,
    "table_type" character varying(255),
    "is_active" boolean DEFAULT true,
    "floor_location" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "table_info_pkey" PRIMARY KEY ("table_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "table_special_features";
CREATE TABLE "public"."table_special_features" (
    "table_feature_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "table_id" uuid NOT NULL,
    "feature_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "table_special_features_pkey" PRIMARY KEY ("table_feature_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "tag";
CREATE TABLE "public"."tag" (
    "tag_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "tag_name" character varying(255),
    "tag_type" character varying(20),
    "tag_description" text,
    "tag_color" character varying(255),
    "tag_status" character varying(20),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "tag_pkey" PRIMARY KEY ("tag_id")
)
WITH (oids = false);

INSERT INTO "tag" ("tag_id", "tag_name", "tag_type", "tag_description", "tag_color", "tag_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('75b8f8eb-637a-402e-9db9-eec107a11a37',	'Popular',	'menu',	'Popular menu items',	'#FF5722',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('1fbde7f3-7230-4ac9-b8ae-b7ba3173a70f',	'Bestseller',	'menu',	'Top selling items',	'#4CAF50',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('00e7afca-004c-4055-924e-ba1367b38fec',	'New',	'menu',	'Newly added items',	'#2196F3',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('89ba0e99-5d3d-479f-9cdd-ed6c80b15cf9',	'Spicy',	'menu',	'Spicy food items',	'#F44336',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('27542a58-a84c-4b00-9a11-e914f6637530',	'Chef Special',	'menu',	'Chef recommended items',	'#9C27B0',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('54e72c35-9610-499a-9e41-b99ac5d00c69',	'Healthy',	'menu',	'Healthy food options',	'#8BC34A',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('35e77ba0-cebb-46bc-90ca-18d0a99f1511',	'Kids Favorite',	'menu',	'Kids favorite items',	'#FF9800',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('4f6ea9eb-e6da-4dd7-a1ae-dd1fa12e5847',	'Limited Time',	'menu',	'Limited time offer',	'#E91E63',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('700348d7-e85e-473d-b998-ab6092d49c59',	'Seasonal',	'menu',	'Seasonal specials',	'#00BCD4',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('d0cccde4-2e56-459a-bddb-896e07b9397a',	'Must Try',	'menu',	'Must try items',	'#FFEB3B',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('cca7c0ec-d0e8-4d94-a1d0-b40a422da22d',	'Urgent',	'order',	'Urgent orders',	'#F44336',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('a6f7ebfa-dbb9-4d12-8416-d0d98c70ca56',	'VIP Order',	'order',	'VIP customer orders',	'#9C27B0',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('c60f26e2-02e6-4442-bfc2-368476107871',	'Large Order',	'order',	'Bulk or large orders',	'#FF9800',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('9e2f530d-3395-47b6-872c-d9cab324aed0',	'Catering',	'order',	'Catering orders',	'#3F51B5',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('3d519aae-ed64-463f-97e6-d23729fb6b1c',	'Food Quality',	'feedback',	'Feedback about food quality',	'#4CAF50',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('49b08c64-97b5-44f1-ab6b-a2e58bf285e3',	'Taste',	'feedback',	'Feedback about taste',	'#8BC34A',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('3c31e750-a6bb-4331-83c1-6ce41e92aa49',	'Portion Size',	'feedback',	'Feedback about portion size',	'#CDDC39',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('1889d82f-f4b6-463f-a1be-002dd3b22aa8',	'Freshness',	'feedback',	'Feedback about freshness',	'#009688',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('395a5d1a-feda-4cea-8c7c-c5cccffb8750',	'Presentation',	'feedback',	'Feedback about presentation',	'#00BCD4',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('ca0d0e06-ed52-4c34-bb25-a0bafda30fd5',	'Staff Behavior',	'feedback',	'Feedback about staff',	'#2196F3',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('2c18bb65-23df-4d57-af16-913ce96827bc',	'Speed of Service',	'feedback',	'Feedback about service speed',	'#3F51B5',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('b9fd8ca7-cb5a-4b53-8ebd-2a543423a81d',	'Ambiance',	'feedback',	'Feedback about ambiance',	'#673AB7',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('d01451fd-b1d2-474f-b188-79efa39f0ff3',	'Cleanliness',	'feedback',	'Feedback about cleanliness',	'#9C27B0',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('7a3907f5-821c-4aba-8da9-c1ccf5be9e99',	'Value for Money',	'feedback',	'Feedback about value',	'#E91E63',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('a759e453-5121-4842-83ec-6e6680ae5d84',	'Delivery Time',	'feedback',	'Feedback about delivery time',	'#F44336',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('6650f6a5-8d20-45bc-842c-55e69d9bf2ac',	'Packaging',	'feedback',	'Feedback about packaging',	'#FF5722',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f'),
('fefef0e3-1ad2-4721-9a65-dd5b43e2f048',	'Order Accuracy',	'feedback',	'Feedback about order accuracy',	'#FF9800',	'active',	'2025-12-19 16:39:41.321147+05:30',	'2025-12-19 16:39:41.321147+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "tags_feedback";
CREATE TABLE "public"."tags_feedback" (
    "tag_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "tag_name" character varying(255) NOT NULL,
    "description" text,
    "color_code" character varying(255),
    "usage_count" integer DEFAULT '0',
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "tags_feedback_pkey" PRIMARY KEY ("tag_id")
)
WITH (oids = false);

CREATE UNIQUE INDEX tags_feedback_tag_name_key ON public.tags_feedback USING btree (tag_name);


DROP TABLE IF EXISTS "tax_calculation_type";
CREATE TABLE "public"."tax_calculation_type" (
    "tax_calculation_type_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "tax_calculation_type_code" character varying(255),
    "tax_calculation_type_name" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "tax_calculation_type_pkey" PRIMARY KEY ("tax_calculation_type_id")
)
WITH (oids = false);

INSERT INTO "tax_calculation_type" ("tax_calculation_type_id", "tax_calculation_type_code", "tax_calculation_type_name", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('8e8add66-b58f-42a9-b02c-b7c4f74bae26',	'INCLUSIVE',	'Tax Inclusive',	'2025-12-19 16:39:41.336448+05:30',	'2025-12-19 16:39:41.336448+05:30',	NULL,	NULL,	NULL,	'f'),
('5d20219f-9115-4ce1-a516-afbe021864c8',	'EXCLUSIVE',	'Tax Exclusive',	'2025-12-19 16:39:41.336448+05:30',	'2025-12-19 16:39:41.336448+05:30',	NULL,	NULL,	NULL,	'f');

DROP TABLE IF EXISTS "taxes";
CREATE TABLE "public"."taxes" (
    "tax_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "tax_name" character varying(255),
    "tax_percentage" numeric(5,2),
    "tax_type" character varying(50),
    "tax_status" character varying(20),
    "tax_ordertype" character varying(50),
    "tax_total" numeric(12,2),
    "tax_rank" integer,
    "tax_description" text,
    "tax_consider_in_core_amount" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "ext_petpooja_tax_id" bigint,
    CONSTRAINT "taxes_pkey" PRIMARY KEY ("tax_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user";
CREATE TABLE "public"."user" (
    "user_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_email" character varying(255),
    "user_mobile_no" character varying(255),
    "user_password_hash" text,
    "user_status" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "reporting_to" uuid,
    CONSTRAINT "user_pkey" PRIMARY KEY ("user_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_audit_trail";
CREATE TABLE "public"."user_audit_trail" (
    "user_audit_trail_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "user_audit_trail_table_name" character varying(255),
    "user_audit_trail_record_id" uuid,
    "user_audit_trail_action" text,
    "user_audit_trail_old_values" jsonb,
    "user_audit_trail_new_values" jsonb,
    "user_audit_trail_changed_by" uuid,
    "user_audit_trail_changed_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_audit_trail_pkey" PRIMARY KEY ("user_audit_trail_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_contact";
CREATE TABLE "public"."user_contact" (
    "user_contact_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "user_contact_type" character varying(255),
    "user_contact_value" character varying(255),
    "user_contact_is_primary" boolean DEFAULT false,
    "user_contact_is_verified" boolean DEFAULT false,
    "user_contact_verified_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_contact_pkey" PRIMARY KEY ("user_contact_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_department";
CREATE TABLE "public"."user_department" (
    "user_department_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "department_id" uuid,
    "user_department_is_primary" boolean DEFAULT false,
    "user_department_assigned_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "user_department_assigned_by" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    "restaurant_id" uuid,
    CONSTRAINT "user_department_pkey" PRIMARY KEY ("user_department_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_login_history";
CREATE TABLE "public"."user_login_history" (
    "user_login_history_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "user_login_history_login_at" timestamptz,
    "user_login_history_logout_at" timestamptz,
    "user_login_history_ip_address" character varying(255),
    "user_login_history_user_agent" character varying(255),
    "user_login_history_device_type" character varying(255),
    "user_login_history_location_data" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_login_history_pkey" PRIMARY KEY ("user_login_history_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_profile";
CREATE TABLE "public"."user_profile" (
    "user_profile_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "user_profile_first_name" character varying(255),
    "user_profile_last_name" character varying(255),
    "user_profile_display_name" character varying(255),
    "user_profile_gender" character varying(255),
    "user_profile_date_of_birth" date,
    "user_profile_profile_picture_url" text,
    "user_profile_bio" text,
    "user_profile_address_line1" text,
    "user_profile_address_line2" text,
    "user_profile_city" character varying(255),
    "user_profile_state" character varying(255),
    "user_profile_country" character varying(255),
    "user_profile_postal_code" character varying(255),
    "user_profile_timezone" character varying(255),
    "user_profile_language_preference" text,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_profile_pkey" PRIMARY KEY ("user_profile_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_role";
CREATE TABLE "public"."user_role" (
    "user_role_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "role_id" uuid,
    "user_role_assigned_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "user_role_assigned_by" uuid,
    "user_role_expires_at" timestamptz,
    "user_role_is_primary" boolean DEFAULT false,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_role_pkey" PRIMARY KEY ("user_role_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_session";
CREATE TABLE "public"."user_session" (
    "user_session_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "user_session_token" character varying(255),
    "user_session_refresh_token" character varying(255),
    "user_session_ip_address" character varying(255),
    "user_session_user_agent" character varying(255),
    "user_session_device_info" text,
    "user_session_expires_at" timestamptz,
    "user_session_last_activity_at" timestamptz,
    "user_session_logged_out_at" timestamptz,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_session_pkey" PRIMARY KEY ("user_session_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_shift_assignment";
CREATE TABLE "public"."user_shift_assignment" (
    "user_shift_assignment_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "shift_timing_id" uuid,
    "user_shift_assignment_effective_from" date,
    "user_shift_assignment_effective_to" date,
    "user_shift_assignment_assigned_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "user_shift_assignment_assigned_by" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_shift_assignment_pkey" PRIMARY KEY ("user_shift_assignment_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "user_tag";
CREATE TABLE "public"."user_tag" (
    "user_tag_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "tag_id" uuid,
    "user_tag_added_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "user_tag_added_by" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "user_tag_pkey" PRIMARY KEY ("user_tag_id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "variation_groups";
CREATE TABLE "public"."variation_groups" (
    "variation_group_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "restaurant_id" uuid,
    "variation_group_name" character varying(255),
    "variation_group_selection_type" character varying(255),
    "variation_group_min_selection" integer,
    "variation_group_max_selection" integer,
    "variation_group_status" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "variation_groups_pkey" PRIMARY KEY ("variation_group_id")
)
WITH (oids = false);

-- [INSERT data for variation_groups removed - populated by PetPooja API sync]

DROP TABLE IF EXISTS "variation_options";
CREATE TABLE "public"."variation_options" (
    "variation_option_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "variation_group_id" uuid,
    "menu_item_id" uuid,
    "option_name" character varying(255),
    "option_price_modifier" numeric(10,2),
    "option_rank" integer,
    "option_status" character varying(255),
    "dietary_type_id" uuid,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "variation_options_pkey" PRIMARY KEY ("variation_option_id")
)
WITH (oids = false);


ALTER TABLE ONLY "public"."branch_contact_table" ADD CONSTRAINT "fk_branch_contact_table_branch_id" FOREIGN KEY (branch_id) REFERENCES branch_info_table(branch_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."branch_info_table" ADD CONSTRAINT "fk_branch_info_table_chain_id" FOREIGN KEY (chain_id) REFERENCES chain_info_table(chain_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."branch_location_table" ADD CONSTRAINT "fk_branch_location_table_branch_id" FOREIGN KEY (branch_id) REFERENCES branch_info_table(branch_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."branch_location_table" ADD CONSTRAINT "fk_branch_location_table_pincode_id" FOREIGN KEY (pincode_id) REFERENCES pincode_table(pincode_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."branch_policy" ADD CONSTRAINT "fk_branch_timing_policy_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."chain_contact_table" ADD CONSTRAINT "fk_chain_contact_table_chain_id" FOREIGN KEY (chain_id) REFERENCES chain_info_table(chain_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."chain_location_table" ADD CONSTRAINT "fk_chain_location_table_chain_id" FOREIGN KEY (chain_id) REFERENCES chain_info_table(chain_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."chain_location_table" ADD CONSTRAINT "fk_chain_location_table_pincode_id" FOREIGN KEY (pincode_id) REFERENCES pincode_table(pincode_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."city_table" ADD CONSTRAINT "fk_city_table_state_id" FOREIGN KEY (state_id) REFERENCES state_table(state_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."combo_item" ADD CONSTRAINT "fk_combo_item_combo_item_component_id" FOREIGN KEY (combo_item_component_id) REFERENCES combo_item_components(combo_item_component_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."combo_item" ADD CONSTRAINT "fk_combo_item_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."combo_item_components" ADD CONSTRAINT "fk_combo_item_components_combo_item_id" FOREIGN KEY (combo_item_id) REFERENCES combo_item(combo_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."combo_item_components" ADD CONSTRAINT "fk_combo_item_components_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_activity_log" ADD CONSTRAINT "customer_activity_log_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_address_table" ADD CONSTRAINT "customer_address_table_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_allergens" ADD CONSTRAINT "customer_allergens_allergen_id_fkey" FOREIGN KEY (allergen_id) REFERENCES allergens(allergen_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."customer_allergens" ADD CONSTRAINT "fk_customer_allergens_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_authentication" ADD CONSTRAINT "fk_customer_authentication_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_consent" ADD CONSTRAINT "fk_customer_consent_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_contact_table" ADD CONSTRAINT "customer_contact_table_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_devices" ADD CONSTRAINT "customer_devices_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_dietary_restrictions" ADD CONSTRAINT "fk_customer_dietary_restrictions_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."customer_dietary_restrictions" ADD CONSTRAINT "fk_customer_dietary_restrictions_dietary_restriction_id" FOREIGN KEY (dietary_restriction_id) REFERENCES dietary_restrictions(dietary_restriction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_favorite_items" ADD CONSTRAINT "customer_favorite_items_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."customer_favorite_items" ADD CONSTRAINT "fk_customer_favorite_items_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_preferences" ADD CONSTRAINT "fk_customer_preferences_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_profile_table" ADD CONSTRAINT "fk_customer_profile_table_customer_gender_id" FOREIGN KEY (customer_gender_id) REFERENCES customer_gender(customer_gender_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."customer_profile_table" ADD CONSTRAINT "fk_customer_profile_table_language_id" FOREIGN KEY (language_id) REFERENCES languages(language_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_search_queries" ADD CONSTRAINT "fk_customer_search_queries_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_sessions" ADD CONSTRAINT "fk_customer_sessions_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."customer_tag_mapping" ADD CONSTRAINT "fk_customer_tag_mapping_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."customer_tag_mapping" ADD CONSTRAINT "fk_customer_tag_mapping_tag_id" FOREIGN KEY (tag_id) REFERENCES customer_tags(tag_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."discount" ADD CONSTRAINT "fk_discount_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."discount_schedule" ADD CONSTRAINT "fk_discount_schedule_discount_id" FOREIGN KEY (discount_id) REFERENCES discount(discount_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."email_verification" ADD CONSTRAINT "fk_email_verification_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."entity_slot_config" ADD CONSTRAINT "fk_entity_slot_config_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_category_id" FOREIGN KEY (category_id) REFERENCES feedback_categories(category_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_feedback_type_id" FOREIGN KEY (feedback_type_id) REFERENCES feedback_types(type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_platform_id" FOREIGN KEY (platform_id) REFERENCES feedback_platforms(platform_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_priority_id" FOREIGN KEY (priority_id) REFERENCES feedback_priorities(priority_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback" ADD CONSTRAINT "fk_feedback_status_id" FOREIGN KEY (status_id) REFERENCES feedback_statuses(status_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_attachments" ADD CONSTRAINT "fk_feedback_attachments_feedback_id" FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_categories" ADD CONSTRAINT "feedback_categories_parent_category_id_fkey" FOREIGN KEY (parent_category_id) REFERENCES feedback_categories(category_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_notifications" ADD CONSTRAINT "fk_feedback_notifications_feedback_id" FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_priority_history" ADD CONSTRAINT "feedback_priority_history_new_priority_id_fkey" FOREIGN KEY (new_priority_id) REFERENCES feedback_priorities(priority_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback_priority_history" ADD CONSTRAINT "feedback_priority_history_old_priority_id_fkey" FOREIGN KEY (old_priority_id) REFERENCES feedback_priorities(priority_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback_priority_history" ADD CONSTRAINT "fk_feedback_priority_history_feedback_id" FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_responses" ADD CONSTRAINT "fk_feedback_responses_feedback_id" FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_status_history" ADD CONSTRAINT "feedback_status_history_new_status_id_fkey" FOREIGN KEY (new_status_id) REFERENCES feedback_statuses(status_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback_status_history" ADD CONSTRAINT "feedback_status_history_old_status_id_fkey" FOREIGN KEY (old_status_id) REFERENCES feedback_statuses(status_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."feedback_status_history" ADD CONSTRAINT "fk_feedback_status_history_feedback_id" FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."feedback_tags" ADD CONSTRAINT "fk_feedback_tags_tag_id" FOREIGN KEY (tag_id) REFERENCES tags_feedback(tag_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."integration_config_table" ADD CONSTRAINT "fk_integration_config_table_provider_id" FOREIGN KEY (provider_id) REFERENCES integration_provider_table(provider_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."integration_config_table" ADD CONSTRAINT "integration_config_table_restaurant_id_fkey" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."integration_credentials_table" ADD CONSTRAINT "fk_integration_credentials_table_integration_config_id" FOREIGN KEY (integration_config_id) REFERENCES integration_config_table(integration_config_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."integration_metadata_table" ADD CONSTRAINT "fk_integration_metadata_table_integration_config_id" FOREIGN KEY (integration_config_id) REFERENCES integration_config_table(integration_config_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."login_attempt" ADD CONSTRAINT "fk_login_attempt_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."loyalty_transaction" ADD CONSTRAINT "fk_loyalty_transaction_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."loyalty_transaction" ADD CONSTRAINT "fk_loyalty_transaction_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."loyalty_transaction" ADD CONSTRAINT "fk_loyalty_transaction_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."meal_slot_timing" ADD CONSTRAINT "fk_meal_slot_timing_meal_type_id" FOREIGN KEY (meal_type_id) REFERENCES meal_type(meal_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."meal_slot_timing" ADD CONSTRAINT "fk_meal_slot_timing_slot_config_id" FOREIGN KEY (slot_config_id) REFERENCES entity_slot_config(slot_config_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_categories" ADD CONSTRAINT "fk_menu_categories_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item" ADD CONSTRAINT "fk_menu_item_menu_item_attribute_id" FOREIGN KEY (menu_item_attribute_id) REFERENCES menu_item_attribute(menu_item_attribute_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item" ADD CONSTRAINT "fk_menu_item_menu_sub_category_id" FOREIGN KEY (menu_sub_category_id) REFERENCES menu_sub_categories(menu_sub_category_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item" ADD CONSTRAINT "fk_menu_item_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_addon_group" ADD CONSTRAINT "fk_menu_item_addon_group_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_addon_item" ADD CONSTRAINT "fk_menu_item_addon_item_menu_item_addon_group_id" FOREIGN KEY (menu_item_addon_group_id) REFERENCES menu_item_addon_group(menu_item_addon_group_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_addon_item" ADD CONSTRAINT "fk_menu_item_addon_item_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_addon_mapping" ADD CONSTRAINT "fk_menu_item_addon_mapping_menu_item_addon_group_id" FOREIGN KEY (menu_item_addon_group_id) REFERENCES menu_item_addon_group(menu_item_addon_group_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_addon_mapping" ADD CONSTRAINT "fk_menu_item_addon_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_addon_mapping" ADD CONSTRAINT "fk_menu_item_addon_mapping_menu_item_variation_id" FOREIGN KEY (menu_item_variation_id) REFERENCES menu_item_variation(menu_item_variation_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_addon_mapping" ADD CONSTRAINT "fk_menu_item_addon_mapping_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_availability_schedule" ADD CONSTRAINT "fk_menu_item_availability_schedule_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_cuisine_mapping" ADD CONSTRAINT "fk_menu_item_cuisine_mapping_cuisine_id" FOREIGN KEY (cuisine_id) REFERENCES cuisines(cuisine_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_cuisine_mapping" ADD CONSTRAINT "fk_menu_item_cuisine_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_discount_mapping" ADD CONSTRAINT "fk_menu_item_discount_mapping_discount_id" FOREIGN KEY (discount_id) REFERENCES discount(discount_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_discount_mapping" ADD CONSTRAINT "fk_menu_item_discount_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_discount_mapping" ADD CONSTRAINT "fk_menu_item_discount_mapping_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_option" ADD CONSTRAINT "fk_menu_item_option_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_ordertype_mapping" ADD CONSTRAINT "fk_menu_item_ordertype_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_ordertype_mapping" ADD CONSTRAINT "fk_menu_item_ordertype_mapping_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_ordertype_mapping" ADD CONSTRAINT "menu_item_ordertype_mapping_menu_item_ordertype_id_fkey" FOREIGN KEY (menu_item_ordertype_id) REFERENCES order_type_table(order_type_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_tag_mapping" ADD CONSTRAINT "fk_menu_item_tag_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_tag_mapping" ADD CONSTRAINT "fk_menu_item_tag_mapping_menu_item_tag_id" FOREIGN KEY (menu_item_tag_id) REFERENCES menu_item_tag(menu_item_tag_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_tax_mapping" ADD CONSTRAINT "fk_menu_item_tax_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_tax_mapping" ADD CONSTRAINT "fk_menu_item_tax_mapping_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_tax_mapping" ADD CONSTRAINT "fk_menu_item_tax_mapping_tax_id" FOREIGN KEY (tax_id) REFERENCES taxes(tax_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_variation" ADD CONSTRAINT "fk_menu_item_variation_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_variation" ADD CONSTRAINT "fk_menu_item_variation_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_variation" ADD CONSTRAINT "fk_menu_item_variation_variation_group_id" FOREIGN KEY (variation_group_id) REFERENCES variation_groups(variation_group_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_item_variation_mapping" ADD CONSTRAINT "fk_menu_item_variation_mapping_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_item_variation_mapping" ADD CONSTRAINT "menu_item_variation_mapping_menu_item_variation_group_id_fkey" FOREIGN KEY (menu_item_variation_group_id) REFERENCES variation_groups(variation_group_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_sections" ADD CONSTRAINT "fk_menu_sections_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_sub_categories" ADD CONSTRAINT "fk_menu_sub_categories_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_sub_categories" ADD CONSTRAINT "menu_sub_categories_category_id_fkey" FOREIGN KEY (category_id) REFERENCES menu_categories(menu_category_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."menu_sub_categories" ADD CONSTRAINT "menu_sub_categories_menu_section_id_fkey" FOREIGN KEY (menu_section_id) REFERENCES menu_sections(menu_section_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_sync_log" ADD CONSTRAINT "fk_menu_sync_log_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."menu_version_history" ADD CONSTRAINT "fk_menu_version_history_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_audit" ADD CONSTRAINT "fk_order_audit_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_audit" ADD CONSTRAINT "fk_order_audit_session_id" FOREIGN KEY (session_id) REFERENCES customer_sessions(session_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_charges" ADD CONSTRAINT "fk_order_charges_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_charges" ADD CONSTRAINT "fk_order_charges_order_item_id" FOREIGN KEY (order_item_id) REFERENCES order_item(order_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_customer_details" ADD CONSTRAINT "fk_order_customer_details_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_customer_details" ADD CONSTRAINT "fk_order_customer_details_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_customer_details" ADD CONSTRAINT "fk_order_customer_details_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_delivery_info" ADD CONSTRAINT "fk_order_delivery_info_delivery_address_id" FOREIGN KEY (delivery_address_id) REFERENCES customer_address_table(customer_address_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_delivery_info" ADD CONSTRAINT "fk_order_delivery_info_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_dining_info" ADD CONSTRAINT "fk_order_dining_info_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_dining_info" ADD CONSTRAINT "fk_order_dining_info_table_id" FOREIGN KEY (table_id) REFERENCES table_info(table_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_discount" ADD CONSTRAINT "fk_order_discount_order_discount_type_id" FOREIGN KEY (order_discount_type_id) REFERENCES discount_type(discount_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_discount" ADD CONSTRAINT "fk_order_discount_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_discount" ADD CONSTRAINT "fk_order_discount_order_item_id" FOREIGN KEY (order_item_id) REFERENCES order_item(order_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_instruction" ADD CONSTRAINT "fk_order_instruction_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_integration_sync" ADD CONSTRAINT "fk_order_integration_sync_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_invoice" ADD CONSTRAINT "fk_order_invoice_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_item" ADD CONSTRAINT "fk_order_item_category_id" FOREIGN KEY (category_id) REFERENCES feedback_categories(category_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_item" ADD CONSTRAINT "fk_order_item_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_item" ADD CONSTRAINT "fk_order_item_menu_item_variation_id" FOREIGN KEY (menu_item_variation_id) REFERENCES menu_item_variation(menu_item_variation_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_item" ADD CONSTRAINT "fk_order_item_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_kitchen_detail" ADD CONSTRAINT "fk_order_kitchen_detail_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_kitchen_detail" ADD CONSTRAINT "fk_order_kitchen_detail_order_item_id" FOREIGN KEY (order_item_id) REFERENCES order_item(order_item_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_note" ADD CONSTRAINT "fk_order_note_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_payment" ADD CONSTRAINT "fk_order_payment_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_payment" ADD CONSTRAINT "fk_order_payment_order_payment_method_id" FOREIGN KEY (order_payment_method_id) REFERENCES order_payment_method(order_payment_method_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_payment" ADD CONSTRAINT "fk_order_payment_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_payment" ADD CONSTRAINT "fk_order_payment_tax_calculation_type_id" FOREIGN KEY (tax_calculation_type_id) REFERENCES tax_calculation_type(tax_calculation_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_payment" ADD CONSTRAINT "order_payment_primary_transaction_id_fkey" FOREIGN KEY (primary_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_priority" ADD CONSTRAINT "fk_order_priority_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_scheduling" ADD CONSTRAINT "fk_order_scheduling_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_security_detail" ADD CONSTRAINT "fk_order_security_detail_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_status_history" ADD CONSTRAINT "fk_order_status_history_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_status_history" ADD CONSTRAINT "fk_order_status_history_order_status_type_id" FOREIGN KEY (order_status_type_id) REFERENCES order_status_type(order_status_type_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_tax_line" ADD CONSTRAINT "fk_order_tax_line_order_item_id" FOREIGN KEY (order_item_id) REFERENCES order_item(order_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."order_tax_line" ADD CONSTRAINT "order_tax_line_order_tax_line_charge_id_fkey" FOREIGN KEY (order_tax_line_charge_id) REFERENCES order_charges(order_charges_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."order_total" ADD CONSTRAINT "fk_order_total_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "fk_orders_order_source_type_id" FOREIGN KEY (order_source_type_id) REFERENCES order_source_type(order_source_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "fk_orders_order_status_type_id" FOREIGN KEY (order_status_type_id) REFERENCES order_status_type(order_status_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "fk_orders_order_type_id" FOREIGN KEY (order_type_id) REFERENCES order_type_table(order_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "fk_orders_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "fk_orders_table_booking_id" FOREIGN KEY (table_booking_id) REFERENCES table_booking_info(table_booking_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."password_reset" ADD CONSTRAINT "fk_password_reset_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_audit_log" ADD CONSTRAINT "fk_payment_audit_log_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_audit_log" ADD CONSTRAINT "fk_payment_audit_log_payment_refund_id" FOREIGN KEY (payment_refund_id) REFERENCES payment_refund(payment_refund_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_audit_log" ADD CONSTRAINT "fk_payment_audit_log_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_external_mapping" ADD CONSTRAINT "fk_payment_external_mapping_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_external_mapping" ADD CONSTRAINT "fk_payment_external_mapping_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_order" ADD CONSTRAINT "fk_payment_order_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_order" ADD CONSTRAINT "fk_payment_order_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_order" ADD CONSTRAINT "fk_payment_order_payment_gateway_id" FOREIGN KEY (payment_gateway_id) REFERENCES payment_gateway(payment_gateway_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_order" ADD CONSTRAINT "fk_payment_order_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_order_item_id" FOREIGN KEY (order_item_id) REFERENCES order_item(order_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_payment_gateway_id" FOREIGN KEY (payment_gateway_id) REFERENCES payment_gateway(payment_gateway_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_refund_reason_type_id" FOREIGN KEY (refund_reason_type_id) REFERENCES refund_reason_type(refund_reason_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_refund" ADD CONSTRAINT "fk_payment_refund_refund_status_type_id" FOREIGN KEY (refund_status_type_id) REFERENCES refund_status_type(refund_status_type_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_retry_attempt" ADD CONSTRAINT "fk_payment_retry_attempt_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_retry_attempt" ADD CONSTRAINT "fk_payment_retry_attempt_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_split" ADD CONSTRAINT "fk_payment_split_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_split" ADD CONSTRAINT "fk_payment_split_payment_transaction_id" FOREIGN KEY (payment_transaction_id) REFERENCES payment_transaction(payment_transaction_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_order_id" FOREIGN KEY (order_id) REFERENCES orders(order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_order_payment_method_id" FOREIGN KEY (order_payment_method_id) REFERENCES order_payment_method(order_payment_method_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_payment_gateway_id" FOREIGN KEY (payment_gateway_id) REFERENCES payment_gateway(payment_gateway_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_payment_order_id" FOREIGN KEY (payment_order_id) REFERENCES payment_order(payment_order_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_payment_status_type_id" FOREIGN KEY (payment_status_type_id) REFERENCES payment_status_type(payment_status_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."payment_transaction" ADD CONSTRAINT "fk_payment_transaction_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."payment_webhook_log" ADD CONSTRAINT "fk_payment_webhook_log_payment_gateway_id" FOREIGN KEY (payment_gateway_id) REFERENCES payment_gateway(payment_gateway_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."pincode_table" ADD CONSTRAINT "fk_pincode_table_city_id" FOREIGN KEY (city_id) REFERENCES city_table(city_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."restaurant_faq" ADD CONSTRAINT "fk_restaurant_faq_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."restaurant_policy" ADD CONSTRAINT "fk_restaurant_policy_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."restaurant_table" ADD CONSTRAINT "fk_restaurant_table_branch_id" FOREIGN KEY (branch_id) REFERENCES branch_info_table(branch_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."restaurant_table" ADD CONSTRAINT "fk_restaurant_table_chain_id" FOREIGN KEY (chain_id) REFERENCES chain_info_table(chain_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."round_robin_pool" ADD CONSTRAINT "fk_round_robin_pool_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."round_robin_pool_member" ADD CONSTRAINT "fk_round_robin_pool_member_round_robin_pool_id" FOREIGN KEY (round_robin_pool_id) REFERENCES round_robin_pool(round_robin_pool_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."round_robin_pool_member" ADD CONSTRAINT "fk_round_robin_pool_member_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."shift_timing" ADD CONSTRAINT "fk_shift_timing_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."state_table" ADD CONSTRAINT "fk_state_table_country_id" FOREIGN KEY (country_id) REFERENCES country_table(country_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."table_booking_info" ADD CONSTRAINT "fk_table_booking_info_customer_id" FOREIGN KEY (customer_id) REFERENCES customer_table(customer_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."table_booking_info" ADD CONSTRAINT "fk_table_booking_info_meal_slot_timing_id" FOREIGN KEY (meal_slot_timing_id) REFERENCES meal_slot_timing(meal_slot_timing_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."table_booking_info" ADD CONSTRAINT "fk_table_booking_info_occasion_id" FOREIGN KEY (occasion_id) REFERENCES table_booking_occasion_info(occasion_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."table_booking_info" ADD CONSTRAINT "fk_table_booking_info_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."table_booking_info" ADD CONSTRAINT "fk_table_booking_info_table_id" FOREIGN KEY (table_id) REFERENCES table_info(table_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."table_info" ADD CONSTRAINT "fk_table_info_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."table_special_features" ADD CONSTRAINT "fk_table_special_features_table_id" FOREIGN KEY (table_id) REFERENCES table_info(table_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."taxes" ADD CONSTRAINT "fk_taxes_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user" ADD CONSTRAINT "user_reporting_to_fkey" FOREIGN KEY (reporting_to) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_audit_trail" ADD CONSTRAINT "fk_user_audit_trail_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_contact" ADD CONSTRAINT "fk_user_contact_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_department" ADD CONSTRAINT "fk_user_department_department_id" FOREIGN KEY (department_id) REFERENCES department(department_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."user_department" ADD CONSTRAINT "fk_user_department_restaurant" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) ON DELETE SET NULL NOT DEFERRABLE;
ALTER TABLE ONLY "public"."user_department" ADD CONSTRAINT "fk_user_department_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_login_history" ADD CONSTRAINT "fk_user_login_history_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_profile" ADD CONSTRAINT "fk_user_profile_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_role" ADD CONSTRAINT "fk_user_role_role_id" FOREIGN KEY (role_id) REFERENCES role(role_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."user_role" ADD CONSTRAINT "fk_user_role_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_session" ADD CONSTRAINT "fk_user_session_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_shift_assignment" ADD CONSTRAINT "fk_user_shift_assignment_shift_timing_id" FOREIGN KEY (shift_timing_id) REFERENCES shift_timing(shift_timing_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."user_shift_assignment" ADD CONSTRAINT "fk_user_shift_assignment_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user_tag" ADD CONSTRAINT "fk_user_tag_user_id" FOREIGN KEY (user_id) REFERENCES "user"(user_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."user_tag" ADD CONSTRAINT "user_tag_tag_id_fkey" FOREIGN KEY (tag_id) REFERENCES tag(tag_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."variation_groups" ADD CONSTRAINT "fk_variation_groups_restaurant_id" FOREIGN KEY (restaurant_id) REFERENCES restaurant_table(restaurant_id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."variation_options" ADD CONSTRAINT "fk_variation_options_dietary_type_id" FOREIGN KEY (dietary_type_id) REFERENCES dietary_types(dietary_type_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."variation_options" ADD CONSTRAINT "fk_variation_options_menu_item_id" FOREIGN KEY (menu_item_id) REFERENCES menu_item(menu_item_id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."variation_options" ADD CONSTRAINT "fk_variation_options_variation_group_id" FOREIGN KEY (variation_group_id) REFERENCES variation_groups(variation_group_id) NOT DEFERRABLE;

-- 2025-12-19 11:51:38 UTC


-- =============================================================================
-- SECTION: App-specific tables (restaurant_config, users, sessions)
-- Source: restaurant-chatbot/db/03-app-tables.sql
-- =============================================================================

-- =============================================================================
-- App Tables - Additional tables required by Python SQLAlchemy models
-- =============================================================================
-- These tables are used by the Python application but were not in the original
-- restaurant schema. They handle user authentication, sessions, and messaging.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Users Table (Python model expects 'users', not 'customer_table')
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    password_hash VARCHAR(255),
    status VARCHAR(20),
    is_anonymous BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    failure_login_attempt INTEGER DEFAULT 0,
    is_user_temporary_locked BOOLEAN DEFAULT false,
    temporary_lock_until TIMESTAMP WITH TIME ZONE,
    gender VARCHAR(50),
    address TEXT,
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT user_contact_check CHECK (phone_number IS NOT NULL OR email IS NOT NULL OR is_anonymous = true)
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- -----------------------------------------------------------------------------
-- OTP Verification Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS otp_verification (
    id VARCHAR(20) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    is_verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_otp_phone ON otp_verification(phone_number);
CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_verification(expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_code ON otp_verification(otp_code);
CREATE INDEX IF NOT EXISTS idx_otp_purpose ON otp_verification(purpose);

-- -----------------------------------------------------------------------------
-- Auth Sessions Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_sessions (
    id VARCHAR(20) PRIMARY KEY,
    device_id VARCHAR(255),
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(20),
    otp_send_count INTEGER DEFAULT 0,
    last_otp_sent_at TIMESTAMP,
    otp_verification_attempts INTEGER DEFAULT 0,
    phone_validation_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    lockout_reason VARCHAR(100),
    previous_phone_numbers TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    CONSTRAINT auth_session_identifier_check CHECK (device_id IS NOT NULL OR user_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_device_id ON auth_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_phone_number ON auth_sessions(phone_number);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_locked_until ON auth_sessions(locked_until);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at);

-- -----------------------------------------------------------------------------
-- OTP Rate Limits Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS otp_rate_limits (
    id VARCHAR(20) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    send_count INTEGER DEFAULT 0,
    first_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_otp_rate_limit_phone_date UNIQUE (phone_number, date)
);

CREATE INDEX IF NOT EXISTS idx_otp_rate_limits_phone_date ON otp_rate_limits(phone_number, date);

-- -----------------------------------------------------------------------------
-- User Preferences Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id),
    dietary_restrictions TEXT[],
    allergies TEXT[],
    favorite_cuisines TEXT[],
    spice_level VARCHAR(20),
    preferred_seating VARCHAR(50),
    special_occasions JSONB,
    notification_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- -----------------------------------------------------------------------------
-- User Devices Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    device_fingerprint JSONB,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_order_items JSONB,
    preferred_items JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_devices_device_id ON user_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_device_user ON user_devices(device_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_last_seen ON user_devices(last_seen_at);

-- -----------------------------------------------------------------------------
-- Session Tokens Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(512) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    device_id VARCHAR(255) REFERENCES user_devices(device_id),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(255),
    usage_count INTEGER DEFAULT 0,
    issued_ip VARCHAR(50),
    last_used_ip VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_session_token_expiry_valid CHECK (expires_at > issued_at)
);

CREATE INDEX IF NOT EXISTS idx_session_tokens_token ON session_tokens(token);
CREATE INDEX IF NOT EXISTS idx_session_tokens_user_id ON session_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_session_tokens_device_id ON session_tokens(device_id);
CREATE INDEX IF NOT EXISTS idx_session_tokens_expires_at ON session_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_tokens_token_user ON session_tokens(token, user_id);

-- -----------------------------------------------------------------------------
-- Sessions Table (Chat Sessions)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    device_id VARCHAR(255),
    session_type VARCHAR(50),
    context JSONB,
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_device_id ON sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity_at);

-- -----------------------------------------------------------------------------
-- Conversations Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    context JSONB,
    metadata JSONB,
    message_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at);

-- -----------------------------------------------------------------------------
-- Messages Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB,
    tokens_used INTEGER,
    is_hidden BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- -----------------------------------------------------------------------------
-- Message Templates Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    template_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_message_templates_name ON message_templates(name);
CREATE INDEX IF NOT EXISTS idx_message_templates_type ON message_templates(template_type);

-- -----------------------------------------------------------------------------
-- Message Logs Table (SMS/WhatsApp logs)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(100) NOT NULL,
    content TEXT,
    template_id UUID REFERENCES message_templates(id),
    status VARCHAR(50) DEFAULT 'pending',
    external_id VARCHAR(255),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_message_logs_user_id ON message_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_message_logs_channel ON message_logs(channel);
CREATE INDEX IF NOT EXISTS idx_message_logs_status ON message_logs(status);
CREATE INDEX IF NOT EXISTS idx_message_logs_sent_at ON message_logs(sent_at);

-- -----------------------------------------------------------------------------
-- Email Logs Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    template_id UUID REFERENCES message_templates(id),
    status VARCHAR(50) DEFAULT 'pending',
    external_id VARCHAR(255),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_logs_user_id ON email_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

-- -----------------------------------------------------------------------------
-- Agent Memory Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    user_id UUID REFERENCES users(id),
    memory_type VARCHAR(50) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_session_id ON agent_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_user_id ON agent_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_key ON agent_memory(key);
CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory(memory_type);

-- -----------------------------------------------------------------------------
-- System Logs Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,
    logger VARCHAR(255),
    message TEXT NOT NULL,
    exception TEXT,
    context JSONB,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    request_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_logger ON system_logs(logger);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);

-- -----------------------------------------------------------------------------
-- Knowledge Base Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT[],
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_keywords ON knowledge_base USING GIN(keywords);

-- -----------------------------------------------------------------------------
-- FAQ Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faq (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    keywords TEXT[],
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faq_category ON faq(category);
CREATE INDEX IF NOT EXISTS idx_faq_keywords ON faq USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_faq_priority ON faq(priority);

-- -----------------------------------------------------------------------------
-- Restaurant Policies Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS restaurant_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    effective_from DATE,
    effective_until DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_restaurant_policies_type ON restaurant_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_restaurant_policies_active ON restaurant_policies(is_active);

-- -----------------------------------------------------------------------------
-- Query Analytics Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    user_id UUID REFERENCES users(id),
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    intent VARCHAR(100),
    entities JSONB,
    response_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(100),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_analytics_session_id ON query_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_query_analytics_user_id ON query_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_query_analytics_intent ON query_analytics(intent);
CREATE INDEX IF NOT EXISTS idx_query_analytics_created_at ON query_analytics(created_at);

-- -----------------------------------------------------------------------------
-- API Key Usage Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_key_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id VARCHAR(100) NOT NULL,
    account_name VARCHAR(100),
    model VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    date DATE NOT NULL,
    hour INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_key_usage_key_date ON api_key_usage(api_key_id, date);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_model ON api_key_usage(model);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_date ON api_key_usage(date);

-- -----------------------------------------------------------------------------
-- Restaurant Config Table (if not exists - maps to Python Restaurant model)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS restaurant_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    logo_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    currency VARCHAR(10) DEFAULT 'INR',
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    service_charge_rate DECIMAL(5, 2) DEFAULT 0,
    opening_time TIME,
    closing_time TIME,
    is_open BOOLEAN DEFAULT true,
    settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Tables (Restaurant Tables for booking)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID,
    table_number VARCHAR(20) NOT NULL,
    capacity INTEGER NOT NULL,
    location VARCHAR(100),
    table_type VARCHAR(50),
    is_available BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tables_restaurant_id ON tables(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_tables_is_available ON tables(is_available);

-- -----------------------------------------------------------------------------
-- menu_item_category_mapping (many-to-many: menu items <-> categories)
-- Required by chatbot preloader for category-based menu queries
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "menu_item_category_mapping" (
    "mapping_id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "restaurant_id" uuid NOT NULL,
    "menu_item_id" uuid NOT NULL,
    "menu_category_id" uuid NOT NULL,
    "menu_sub_category_id" uuid,
    "is_primary" boolean DEFAULT false,
    "display_rank" integer DEFAULT 0,
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "menu_item_category_mapping_pkey" PRIMARY KEY ("mapping_id"),
    CONSTRAINT "unique_item_category_subcategory" UNIQUE ("menu_item_id", "menu_category_id", "menu_sub_category_id")
);

CREATE INDEX IF NOT EXISTS "idx_mapping_menu_item" ON "menu_item_category_mapping" ("menu_item_id") WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS "idx_mapping_category" ON "menu_item_category_mapping" ("menu_category_id") WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS "idx_mapping_restaurant" ON "menu_item_category_mapping" ("restaurant_id") WHERE is_deleted = false;

-- -----------------------------------------------------------------------------
-- Log initialization complete
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    RAISE NOTICE 'App tables (users, auth, sessions, messaging) created successfully!';
END $$;


-- =============================================================================
-- Database initialization complete
-- =============================================================================
