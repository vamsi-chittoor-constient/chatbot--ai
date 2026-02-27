-- Migration: Add customer_info_table
-- Date: 2025-12-03
-- Description: Creates customer_info_table for simplified customer data storage during order processing

DROP TABLE IF EXISTS "customer_info_table";
CREATE TABLE "public"."customer_info_table" (
    "customer_id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "customer_name" character varying(255),
    "customer_phone" character varying(50),
    "customer_email" character varying(255),
    "created_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP,
    "created_by" uuid,
    "updated_by" uuid,
    "deleted_at" timestamptz,
    "is_deleted" boolean DEFAULT false,
    CONSTRAINT "customer_info_table_pkey" PRIMARY KEY ("customer_id")
)
WITH (oids = false);

-- Index on customer_id for faster lookups
CREATE INDEX "customer_info_table_customer_id_idx" ON "public"."customer_info_table" USING btree ("customer_id");

-- Index on phone for lookups
CREATE INDEX "customer_info_table_phone_idx" ON "public"."customer_info_table" USING btree ("customer_phone");

-- Index on email for lookups
CREATE INDEX "customer_info_table_email_idx" ON "public"."customer_info_table" USING btree ("customer_email");

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_customer_info_table_updated_at
    BEFORE UPDATE ON "public"."customer_info_table"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
