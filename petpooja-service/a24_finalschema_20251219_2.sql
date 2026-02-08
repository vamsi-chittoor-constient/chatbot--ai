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
('a2f85907-c48a-47ca-b96c-89de28ed2483',	'Aswins sweets',	'aswinssweets.com',	'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGgAAAB4CAYAAAAeyrc6AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAB59SURBVHgB7V1rcFzFlT7dfUcSbBLkVG0V+2PRmNoHyWbxmBCCMUQzTsxiMFiDH7ENWDNgSFzLYjkPQthNNIJkoZJULO3yCstmRnb8wBjPKAFswLGueBizECSx2bx2KY3yKz+2InkrCbY1t3vP6b73zow0elmasUbRVzUe6z567u3T59HnnO7DYJq4793LYoyJ7UqxesZYEL9BAcczbEhKNshAZKVi/Y5g3Tsv7e6BBcwIDKaJ+//r8lYlWSsAZ0Qc/AYJTIFi+A8eUpzRMf1/yU6C4hkpVWf7J47a8EeCT6f/tQmE2C4ldjATSupRrAdxmx29055OWxZME9JhgwDiXSTtpYohIaQmDAA9A9MPAUoBfRgwXo/P2IwP27z9J9cN5hQkHr38SCfMcyjOd2KnBBnj1BXYETiYGR+wm7baME1Mm4MKcV/v1WHJWQwHSCPSwxV31KThJI/D9HGiIx0Dnh0ZGYk8sexIFuYhPp1+rEkJdkiLFSKQFi+C6NTZE90ah2mCwwzw8NLX7G8teTUmFI8gBdp80UZiziMOEYw4C49JekzFgpZVO7DtRFMLzEMgPWKuNCERj1JEAAk6BiNtcBaYEQeNxpfe+kw4h6MHn2qRx00qTygknKun6MGN7ko88clDZ/XgcxHh9ONBHJoDRooII+oND6R6ondMm3sIM+Kg0fgOGgIceISI4nIL+CKOiEN/GzHnWX6tn39zXSvME3DGWs2g5IY4yEXEAyzHz1rvziqBCN+97MV+kHwHoxHkEcflJJeLgHSUZl4tCkVi6xsbwzAPgO8XVmi1afEGRsThH1l7fdyGs8SsE4jQ/onD7TgXsl3O0YRBPYT/E0wzkksw0p+SBppi6Tte39wAVYxw+skYEqWBrCEw0oIkhULLdUYivCwEIggrEMcHHNbPSmINR5PU5neeq8ATe6AnvSmoYuBrbDGiwtO7+h2Ha/4PMjADlI1A7UszWfrSBkHezNZEKZzkemIQz4Xjr29ZA1WIcDoZxHcJa8NHGfHtSo8uOx4fhhmgbAQiWBbvwIcc0gOLOMjXRSSjkamKjAb9//ZYd6weqg3KSZC8loZzfCNI1YkEzBBlJRByEYo4JJI2CrjxNnhuIXeuhN/DpEhJZ+Hr2aw2sASqCMg99fg6a1yiKJWfUtjHb7hlEGaIabt6pou6Gtnx/ulAC+kZ35ugWA+6P9I4ret5avmuPqhiOFI2of6sJ+Jo7lHMEIlb7TALmNWJ6ni468Rnd+JsoAWfOoUOxI5/W753DFFItJ2COi3e8Hs4E2mfkeyuFBrTyQEkStCblGruATF4fO3mxTALKDsHEdDA7hC1vP3Ry/b6LH/HO5sbnPdrYmhih/EFQ/hiF9SqnPZfBeT77NaebUNI0H4KXaApntkfecSGOYZrfvj9RnQeN7gWm3In36iO1Kx5RyrCQYWIvXprWAjRim/T6M0VPD8den8BY0rg+fD8cAZ5JdDJisdSyF6d+1e1Z2EO4Op0Mswk6/bEm1TmG86rDR6/Ye2M9Q+hYgQiESZqnTR2ehjcSSp6EXrwfbrwYwMXw6llT2TNtS31Z+BMEN1GQcnEGiRm2POWIzGzI45qO3Ttd1MwB3D1oV1DFLz05j+S8dSJdZvOyu9WChXloNtf2zJkrDnokB+A9tTS1JT1zMYffyGmjK+rwThbRWpkBNoyqx7OwjnAVQeSoeMb4n1XPbu7FQdNqxuwRIdJTfD42tnhHkJlCfR6LCY52Kllqax37NZXP7cE/SERfLMlfnhCT/VI/1i9+1bs7ClsY8PL9yZQCrYac11kUTpGDn36m7PWIVPFNc/uGlDSiVsW9J2Rdb81E1PoObF+YwRmERXXQQQSd9KytuPIQ/Ob148JTRQ5WPkA6qWOkRGnK+Pqno3d9wVHcvwYPv5iKXmWWTJcSSJdc6hzDf5uBh2JHcc33Nay7Jl93UCOUsXjJzZsSMEsoqwT1VK47ZU7G5UI9CJxEiS7pRsd9zzdhV5vM8FlixlnOwOBmmNrj97bTG3sjzycDVg1K1ApZ/HWoMxZM/J3TRdInBbddVw0h5M4UVXQicTJzjZxCBUl0JZXt7Yif9gorhvy3gXjl9MWnefpBi90zgsSUZBQwFM3v3y/jh/tjySyyhERnHOgXmOhm15M7IQKILwvGdRhBcPh9X84vzZcF6ijATJrpnUhKibiiDjY24kCbwI5FknX4DfvwRfuQ6stS5kwaOFhJ4gQ3kamOJnfWUdRhhBbQnMNHMHtmb97cAe123Q4gTEYbeqSOR55btXXbCgjlj/zgxT+VrOOR5Lzl3H7xPoNs6p3ClERAm159U7UN6q9UL+QZxtfMoUs07E38tgYz8L6l74QQxGSVEpEDq582DbHEqEcc7rxxnq05Foy1z3QQcdvOvwgdhprxkmu/dx195etswhXHdzreg5MrgV5r8///e8+PFOv9Xgou4hDgyCIVEnQJFR5kVTgQ/hesT3hx+KliENQwroH50ApjziEZ65N9CFhtPMVidF+/fOJkH6JU04Lshk5XRtX/+ihMJQJVx3YQxlMQYACowbZ93d1HwhBmVB2AjkiQEmO9dpD4HoOLAkr9jQ+3jnhjQo+rBzoGX2YMQstJqE94eiR0HonE00MK4lxf2zfYbx8MSUmthvicD9kgqJ44O1N620oE8pKoI3IPUiWmB9hRD8bqpi21DhcUwwxxBUPjj6ac+RiP1sGPQyrDz8YpuMOiLRJ8WLNUAZcdeAA+gsh5EWE3ZAJKcwHoIwoK4FqeG2LUm62qckTG9zb+NjUrB3FO5Hp7ln/0v2++ECDIMjIm+Cb4BwcJTTHHL7+3h68B/UAX3Tdj74dhlmGA3I7eJyjfPE2+NamaArKiLISCAfZEhpo0s2Fwzebsil6cOU321GkdOZAvLPmyNe617yY6MUmBrwwuSsu0RDPizQkmu3qp1nVCVfu24eSgMek8qYBXLnhbRvKjPLqIBRBoHMSTEL9CNRMKNqiR76yZP1LX/Y799DKB3fgXGeFYqIPOdFGkRfhtc5Sb0WFGck8GE7v1HEkB011w7FidqOyQoRdzmFuarP+DsxiWGE8lC0eFOv+fHCE0pOZzughkxqeibSPS6Cbf3xfK7ruEw4+UtORf0IT+hvahM6sStj4ZRdee8ML/zyIDV9kzHZggZqRIB7uw98YJDZibHbHHc6vaHKsBxnkFwt0ndjUlIUyo8xWnJ6MmoGHk9AJr0TieAEv7OIJs011xqY0bgfiIiGZSTRx6H7SSxCEWcKyAwcaUbwFzbuA7y/Ez6yEtCdDGQlUR5MZI9505g67YKKrFc2N8h1wcsKmC4wEwy1WYTvKpHbNDtA6bJFavBnia0tUQfbtTTfaUAGUk4OGfUeoCbQtasJA3HgXK1GLHgDUNcBt7PXoRA3rDE7Iu4sgB1l9HPWR5wGHWUAIjQO0cJrA1z1uXp+EsuseD2XTQalI+/CmYy2/xv66yOvMWqhtxFNdpa5Pr/h6P34tnazdVS98t5GS7PIhCT78YrQlS+fQmAi6rJWFWUAAahOmXWNaE3FwQAzV8pwNFUK5rbiMZ/loc1vKGa8JoiCZ72oBPfG182f5pVrsSdYPswFGC9OEWYTlzn3QAkHjIJqFCqG88yBpZfzYjlkTFF738n1hOEtcd/ihIDoom6WXnUop+dLEgtDUJu7RJrgD59kwQ3z86a5mkwcBvnhTOmOHV0y8AZSZQPtXfsdGH1m/WSdDC7aA0n2TTYfvC8I0EU4n0INd052PuhILiYGX1txtfHq8ttEVeT12dOaeZRxWMdffZjzvxmLs6du0KgsVRNmdpfhiO/y5A/0cBuuYEGly20y1DSJObeAD3aA9yZ4+wLYc5fvB0KeQMKNcpmCGCO1Jhyj7SOlk8oIUMMaSUGGUnUAHkYvwPTuVv7BYexVCistjN73YNqljk/xqdTUf7MXZTsiLvOr5CLDMy9F7UnTNivRjLTrbhxZLRbelYIYQXLQUijXNSRg07Nu8qhMqjIpkljqirkXkRpYgB4Qgb3ZjCBtSNx55sFVx3gGO7MeQxIA8I5g6j13AcxTOZmtMMgZzl1OazkL/xKCQQkdUaV2oZHy7Gy+fsX4I7TscVCy3Jb8Q2ASxWIV1j4eKECgTSQyjSIsyIbt1NNJ4C4zTU7LF+Nmp8FEYOWlq8bhjzkNRIgkYIhniRI5Et2XpEGMUZoAGStqwo1tTMENwKcO02NQ14z3RjI/q2HAOULGkEfSpZVWA4zyHtXtZmMZHxwriK0WLjrU4c90q+BH4l8iMyD9Z6hFnRebJJBIHOZM8DyMRmAUoyrkrXLppCNRZaePAQ8WSRgpx48vfWAM51o5vH4S8l1i5E0Hw4i76b+PS6VE5aDsa/Qeb7qc1OQCnMZrKY3oVtRJN3Tff3gUzRGjP8zFk4u8b043nTXkRWNy3KZKFc4BzQiAPqw8/FJboSkHOWOKucKg31pIYwuODSKEeFH2ZozcawhBI55BYw94LGfGj4nb0rhTMAkJ7X+jWIZKC5H3k8p7/3LIyDOcI55RA04HmGn4GjQEwi8EUo7lOdLqbE42HUPJwEGrUQH5zKL2/DoVL4u9ujlTcevNQESPhbEGBOAuskASrCfipZuy0endnrR70kMZsVxfNCgKqCQnfg8aGztbTYk6q4Xe3nDviEOY0B32m61GMEfk5CPgRfaiUEt033zljfVMtmNMEIrEm+Okh6e09x3if0pmnehs0yo0G7T8iV5K2MvJhaeUuppKSedvOmDmUWUeKTgh9DyUfmogvE/pvbVp7iS56HRNBmN+jXUTw4Gl1XjQbX1qRJZpzXgdFup7MoPcz5Lv8vSUqJIEcMEveGVeemW5MY70FmOlUE9V1CeCu6AM3F1yLS6I+byhYTUFEo2tPopg7SYR2iaavlUz0/ip2ZRQqhKoxEsqFj+1+OYzOp25llll6MSZwHBH5RfwaG84x5rSR4CGcfqpJupk6UnsfuPtNufcYE9JyyPytxV9OZd66ZcOUlvfjCN3ur6bwdB1jfXOBOISqIBASpwFoZYS2r7ReUK57GUgnsfyujqaTBaPI7aSehUvItAZochPhvX0O0EBkHTBHUPEFXGcDfMhOvTGTSRZ0lT739iWA0QmFqMwbL9+XDk/WbiCg88Y1cdytw6jdgZ/FP5WCOYKqIBAF4FAvdPgj3YSglbuEH7yRX5gSjNc3TdRmKNldTxFeb18338sOrAfmEKqCQASLWylvAyaXU7zdI6AgV9ok4Rl3eXMomR43i+iMkE2eZ70ondcRbTCHUDUEsqObsgzD2YZFPJOaF4o15eU/GGXP63mNNX6SiqIJMBiPuR8IZKlfxJdlYQ6haghEwGlPm97iOL8KXE9MtcTz98rxd5zCy6ySEduP7e4Oc86DxVt2AmVMnFO3TilUFYFOrN9kY2eeLNi1kRVMUl0zjjF/iQiwYGj34fDodpBTmr2N98C/VmTnimldiKoiEAHN7HbPk6AKYkf5IJ+X+mvcQchFRXnelyS7g9hGDFzvgAL3WgYJmIOoOgKdsqwO5JphWRR99QJszEuP8pYoksEXNhabAdcbObHCfVPp2uwZWTcnHbBVR6C+aHQYHWI9fihcizZeZIn5lpnr9MxZsN27392YyeU6Q2CpwK6U83O6qEpfHE1CsYO7iyKfkPdAK1VALOMUHQrk1MVnoCaouOwtEI362jMgF2fnmPXmoeo4iPD2pqiNj2778x9w90NVRetHmfJL5rBFp7nV/LP48j7QkVjXI2E+PXOVOISqJBABO7Yrv1YUijODGC8wnf15TpO5T3T4RgbpKFmZhVhni6oNN5CXgNWeNyBpYZjMJ7jLwphRgTGgiclYxHGsk0jGd/SeCopn37v98sUwh1G1HNQXjw7TLlMecUz00w3Gmf1DVcEaIuMpcFjkv+NX0ELjHiMa56ZpXYiqJZABT/kWmdnYghXqIC3qlJf4qI0C15pjGU1QyW2Y46j6iOrf7j5qNtMDf0Nx8PdRyOdz62+Tn2CFc4z1CyUT793+8TlfZKrqCUQhawDRrZS7WZPPOUbkFawncje/YPb/3H75pMG8uYKqJxDhb3bZQ+hduAAKvApSFYSwfaeosfocBh+eqxPT0ahyHWTAGCXkg+8oNftXexNR7lcCAy9W5FB6b3VgXhDIyskOQxhXxPnxIm9O5Lt/iHgD2a1LK7rH6UwwLwjUF4/QfnE9ec8CGz0PUiaRkdPO4w9AFWFeEEjDlAllZk9T30udNxw8z4JzbhZinS3mDYEwVI2+Od5XyEHeIjD/G0Qqu21pFqoI84eDQG9Yn3IrMIKp/lvo6daJjXMm322qmFcEGoFAp8mpdl0/BX45HfO562NVV0xqXhGI5jZUfcQYCHo+5O+poKRIQRViXhGIIHPQ5Wf2eLkJimV//bmPdEIVYt4RKHvnUtp+pgegKGehauY9ozHvCKTBVIf0VypwJUTdnA7KTYT5SSCBcx1FOzhqY6FzYOvFg7CABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABcxBsLvfXnWIKb5IKZFRVi7z6GUvTCu4FeveGLRqeOyp5XsT8EeEcDJZn/uQ3C447bmggm4u3hAG2rtGpJM4vnbrtIOEl+35YQy4ohoUdu/mm/SmTvyRyw/frCDQA4y3q1xN37Y3105a8KIQImAl8P4G72+qPtz8ytZu/OyEWcDao189tu7oV3vPpqRNuXB1evf23If4AJV9Y8DiDKgOBYsqxU86ksc4BLJXPdvZOp02Q3tfaAFuJUFZCcZE2DuuQ96PfCKTcHKiU0qrXkq+847Xb26YSqNUSF2CtcWRAT9jJiDqwngsLJVo2fzK52ZUV5tK2CBnR7CtENc1wc89lj29u0k5rF0C2/HauniLHY3b+MniJyOYXCqROPhR1NFXPrM7PJU2ac9ufM9WSTtJKgtyMp+J4P8PuSCh8CR+FjFWO6WVZ47gYSkDg6lrnrL9Yw7vww5VVCxDOYEZrT+ieg9Siiy2B46cI+kTrKbZASt1fO2W1OhTurAUC7RIB0klLWBOoGkqTTqBQDf2+7CjAoreFaTl95v/1k8s25/NgejWF4DVjNxRP2nLKtCquJUoPLQ38lgfctTFIAORfZFHZp7uJFkEHBZh77MdMAcgQdTDSG3buOdPW/3EBfRxCkT/ePjoD175Og7CIBc8oiRnjrJUDizlnS/as5TlAg84nMo780Vgtk8Z90Fu7b47jHxcL0YCY/a42R9pz8IklRivSz8UZLVCv8D7p//Qb0cTJVe8ERfBFKo6aqV9gdUATm6R9Tvos+PTK5NGy/oDNRAEpi4YOc36aRV5qescKfrenqDIIBUgvHw/jUudxD/hIL9k1/FGkLINRWZb35Zrsh/d9SroekV6eYbBGBHU/Nqdv0V5t0gq1rv7U09eNl7jm47dk2KMqb2Rjjj9ve7Yl9ZwVJDYYiNlreP9GUec3pGJtBe96Krnvk21F1CfqHrG+LDe5w07Bb/7JZPxl2+4t68pvbN+pPYMynloZApQPrO+HAN9bvRzEGGcD6KBw6gYlMIO0TUd6pHzaJf6tlc/e5vPxVfsTTehpIyh4FiDPzsM9IynnB38fGs79kwLp5oQZuEK7YRlO5CL902z4mMona7np2p+S/9HefXD3ltWlxRzlyTfwMEA3VRS9JexZXrN7F+n3jCbAyjZ9ov48gT9d4xgV474F5KfKBOXEpeUanzj4ZagZGILEtvnsIMrvtN14DPfiqKiu1kqWi/KY2KktsgivPb5jlY8R8WciDCRF2744qLDq7+4CLi4mIHoZ8o6RvUaMtEdw89f/5VY7ekaVLrWkAI0EkCMMRLC+5LBkQ/W9EpmbUHxkLK4XPTa2i2LUAzFJeMNqCMPXfnMHv++/9gczby9MdqUUzKCBEBisBirC7yDsijCFY9aylmMojmO4ilLNey4DPQu3fP8lAwmD877f7IERRYjEYfv2T3udYonSK+eVhD3jhldK1CM5gXbGAJxWdfuylCUhaKk5SQtKyZz1iuuKCvCwZUP22g46AdEeRosvlElaEd4pH78yI1ftr3DR1btyB5ZvSOGg6K/Bi1A7zgRCl+2R7+sY4VG/9YpUYsjkAelw/pfX3/rDq/64/G1t6Swgx9QVKoa3+HKffvCxTdCH54D/QHR887mG8NU+pnE0082r+qUwCNIZGRCUY/XTG+pvsPj+t1Rn+CcpuQWZ3/57z+J4TXN+G6Jwn2CtJEGASAG8TCGQFRBGDvWluYFGkuVd3aY1eyo8VcLIBcNamNDBfx7r0vvJFMSTLuBknW9cVS354Qq+j0lrZP4IkhsUXTtsoNPo+gQQTJNFQuMMSDeWL8ZB5oY0iUCRPGmfmaXEnoWWo03tgg8VdvC0W+btnkYpgjaLBDvayZFj52cKlW1K5jsDaIR0Eq7GL+39fKihH5HEmGFmpBAhFxOtOFFZCoyK1ezvfDc2hf/ESkfgEPXPpyCcSBVQHMgjQgPp1Dmo3k6RAQakaKdCjWNvu/oTXd3HbvpnqJ2kTCKRrMaRSDHEU0oCvCcNXxi/Xq79HPwTrKMkEiNoWSyftQ53aYcz3zXhLPo/IRF4gvBmJWkwaQHqKhJlLpG5QJJ6he8bMx5c69guckIpEtrqsAwdQCyXBGLOzwQwxe2YQI4yvuhfKfaJK6UaFPahORBNBAGqAZdKUIVPbQyLC8LTE/9olS1CzsfjZFxy0KjmOlH4uKI5CxQUx8sbpeDmVJwVvp3qW2unCluzv9XnW+2Kj1BR52JU4yf37J8jKvnou/9EnUweglGeKTUPg2SBZTRPyUmqmMudqwOTVFl1a8+nAjTMSrVjJOwMCrVcc1vAhHBk/GFsNfc1aEke0CLObzGUeTHCgw0pp9KXvXsUw2l22KuWLRY8fOJRdTJIMUET0IVUHTtVnr5JaOfURNvFOE9OI5esk+7OU462f6L5FskslpxYA5Jh0dKbe184eM/R6+LSCiHt2W3fSRbqh28V09wc1BTeh5UdHENmq5n+Nd1zR0GJMNt7IpW5IrMC9d/LQsTgEasrqig6yEUw47emQink6jEqdoi7fyOjkbGmrH7Y1c/25l4bW1zW3FbAV3mR41qyaxBBaXUBM+Bs3MScNqU52K4+JwwOy8VzDmK2mcWUxImxcXJXjTRVQKbGebOyIpf3fXJkhzNoK6bioCgRBi48PGBmC5MxIhDaRi5z+TVpJAQuvDRX8fo/LgEotqnq49808YnjeAnrGtpE3sqNqlVg6PAlCCVpUcf+a7wK46ECjqShZGRW/HRguhwTCw/2Jl9fV2zrzxRHjPTSjEpqEOo7DR+Lhr3QZTVIN0STXj7yaJTuny1txNWiVuVLuY04WY5wad+2qwcp93BuZeSTuS9u64Ydw0sciy6rFSWnKu6DBszxYuE3lbaTH/MWKHX5CE8q3XmxAJW1aA4UhG6vxb9RdTAkdVfnHR3XDIzTTGk4uNX4rzlxCZNHA2XUKkr00lbqEAv9gZNWKl4kk8gpfVA/iXyvyFsPBDC/l9Mu/rSZhajn8ORaimnKl0KhvtvXWkXnaO6rEqzuSr9Du7gGodDL/oeEgdYEvVNlqErKrvt0uzoa4KP/jQ0fP5Idhj1zW+2/XkEJsGfPvobSeMQ3zT1v3//Z1qSTOiBfG7Vl200/bJkkSEtsTOmVi5ZkQVIeqNAP+BcBP1NNSW57wQSiuJR0ozq0Wa2NjikEWk+sAO76Df0fCWQi5V8ELDWaA8xWGN9gjhHIhN8PCvOmxKMNu8JqOyb0bRH4liDhjildUrOEk31p+om92mC907GGJrUzC56UAfDEKigybYHp86GKUBbf2ai6h+rq6sbpq36iVAl70GHoWv29ha35c6dZLFn/Ke3rbRp/1HynOdk4J7CvbEJH9vdQ16LejyfFSNjjRq6T3/G6QLpbsRkNgTM48LvDZA3G81pa1DwQHg84qCeCUpV23wK6mCqoAFqBmO+3ya1Ic9I2Y5G6j0or7qOTLEspjZ/R4kOOxod/uSBgxklxLErnn62E4WwjfKb4Vz/AsU5mu4qTKux0Z9XtNkEuuB1k6V+x8pB4owQDUi5pjMcei/Z9UoMZ9HkIkTOgRZ0H5FuiKL4y455Rt35tP0IK6llqAgh1+tc8wgmB+pPn2IpNPHJirDfPy3jFz4+qHxDg7tGEcNnwt9FeYWiLZiFKcNtpsBwmZRANH8Jp5/sgRzrhCkCY0IZRZu9suItJ9/csC5+xdOHmnHYxvFN4oxbF5GCRWtqkLy655/i7fYoLzK5erT+4Xxo9O+4eif60V2vo+tENaPeTePAX4TEHsT/t/1ent8+3r5w2Ae7TEkAp7RiZ+RJ0KUm87+LLTl1PMV1KTaqUiCCuhA72WFa45KulKYsGIiugIRpLV5GtZfieL9kyn+m/wdfwGdQV90n3wAAAABJRU5ErkJggg==',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	'Restaurant');

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

INSERT INTO "menu_categories" ("menu_category_id", "restaurant_id", "menu_category_status", "menu_category_rank", "menu_category_name", "menu_category_description", "menu_category_timings", "menu_category_image_url", "menu_parent_category_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_group_category_id") VALUES
('994cba8a-76ea-4c57-8d07-275acfd0f307',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	1,	'Group1inGroup',	NULL,	NULL,	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	382),
('06a09633-b820-4dbf-960f-6ebd2141aec1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	1,	'South Indian Group',	NULL,	NULL,	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	383),
('1f8881cd-3e2f-484d-9ae4-2f3376c40907',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	1,	'Non-Veg Specials',	NULL,	NULL,	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	384),
('aa6ce4eb-6317-42f6-b3b2-d2769adeac36',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	1,	'Combo Meal Group',	NULL,	NULL,	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	385);

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

INSERT INTO "menu_item" ("menu_item_id", "restaurant_id", "menu_sub_category_id", "menu_item_name", "menu_item_status", "menu_item_description", "menu_item_price", "menu_item_allow_variation", "menu_item_allow_addon", "menu_item_minimum_preparation_time", "menu_item_tax_id", "menu_item_tax_cgst", "menu_item_tax_sgst", "menu_item_timings", "menu_item_packaging_charges", "menu_item_attribute_id", "menu_item_rank", "menu_item_favorite", "menu_item_ignore_taxes", "menu_item_ignore_discounts", "menu_item_in_stock", "menu_item_is_combo", "menu_item_is_recommended", "menu_item_spice_level", "menu_item_addon_based_on", "menu_item_markup_price", "menu_item_is_combo_parent", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_item_id", "menu_item_quantity", "menu_item_calories", "menu_item_is_seasonal", "menu_item_image_url", "menu_item_serving_unit") VALUES
('b138efbe-95c0-46c0-9e3d-493c0468f9b7',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Double Chicken Burger Combo',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	439.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584270,	0,	NULL,	'f',	NULL,	NULL),
('c01c6fd1-8ffe-4298-b062-b88313b33dfd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Nugget Snack',	'active',	'chicken fillet  nuggets come with a sauce of your choice (nugget/garlic sauce). Bite-sized pieces of tender all breast chicken fillets, marinated in our unique & signature blend, breaded and seasoned to perfection, then deep-fried until deliciously tender, crispy with a golden crust',	319.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584216,	0,	NULL,	'f',	NULL,	NULL),
('1ef1e318-ce3f-4ec5-8eb6-42316b1834a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Fish Fillet Sandwich Comboo',	'active',	'',	299.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584227,	0,	NULL,	'f',	NULL,	NULL),
('5ac17a93-67a9-4bdd-8ef7-dadcbea38d83',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Sandwich Combo',	'active',	'Chicken fillet sandwich, fries and choice of soft drink. Prepared with care ensuring each and every bite is packed with Mmmm',	289.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584219,	0,	NULL,	'f',	NULL,	NULL),
('4ad4ad2a-50b7-4498-956c-4c5ac66dce9c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Fish Fillet Burger Combo',	'active',	'',	269.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584266,	0,	NULL,	'f',	NULL,	NULL),
('d1652219-e03c-4789-b1e5-4f2c1924dbeb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Burger Combo',	'active',	'2 Chicken Fillet burgers, fries and choice of  soft drink. 2 Crispy chicken fillet burgers, topped with tangy sliced pickles ,lettuce and Albaik International''s signature garlic sauce, placed between a freshly baked bun  served with a portion of fries and a soft drink',	269.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584221,	0,	NULL,	'f',	NULL,	NULL),
('e53d05d3-447e-4e38-bba7-bd8a856b4dbe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Spicy Double Baik',	'active',	'',	259.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584259,	0,	NULL,	'f',	NULL,	NULL),
('48bec079-e48a-4e49-ae41-ef06cf1bf431',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Double Baik',	'active',	'2 Pcs of Chicken fillet steak & cheese stacked in a bun with  pickles , lettuce ,our special sauce and some frie. Two of Albaik International''s juicy chicken fillets topped with double the cheesy goodness and our signature cocktail sauce & garlic sauce  in our new unique bread. Experience an Mmmm with every bite',	259.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584222,	0,	NULL,	'f',	NULL,	NULL),
('a4591e03-f6ef-4101-9148-550af7d501f5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Spicy Shrimp Sandwich',	'active',	'',	229.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584263,	0,	NULL,	'f',	NULL,	NULL),
('1494edbc-1c05-4247-a198-f33aff9623a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Shrimp Sandwich',	'active',	'',	229.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584230,	0,	NULL,	'f',	NULL,	NULL),
('36cb1f23-cc55-4098-86ed-2322ce4818aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Big Baik Spicy Sandwich',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	209.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584224,	0,	NULL,	'f',	NULL,	NULL),
('bf0193e5-5f87-4e87-8382-8173d3385053',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Fish Fillet Sandwich',	'active',	'',	209.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584226,	0,	NULL,	'f',	NULL,	NULL),
('5c4e0a45-857b-4842-a13b-515cd01de0df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Big Baik Sandwich',	'active',	'Chicken fillet in a bun with coleslaw,lettuce, pickles and our special cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	209.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584223,	0,	NULL,	'f',	NULL,	NULL),
('4ef99f19-4110-4f84-9b0a-cf1dcbd0eae1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Sandwich',	'active',	'Chicken fillet wrapped in Arabic bread with our signature garlic sauce, lettuce ,pickles and fries inside. Prepared with care ensuring each and every bite is packed with Mmmm',	209.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584218,	0,	NULL,	'f',	NULL,	NULL),
('f267185f-84e8-45a9-8cfd-14972f0cd49b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Fish Fillet Burger Anand',	'active',	'',	189.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584267,	0,	NULL,	'f',	NULL,	NULL),
('92600ad6-b38f-4221-b97e-06e34fea9b5c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Burger',	'active',	'Chicken fillet steak in a bun with  pickles,lettuce  ,our signature garlic sauce and some frie. Crispy  chicken fillet burger , topped with tangy sliced pickles ,lettuce and Albaik International''s signature garlic sauce, placed between a freshly baked bun',	189.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584220,	0,	NULL,	'f',	NULL,	NULL),
('b98b877a-8e9b-40c0-95fc-0d1640c8f28f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Hommos',	'active',	'Creamy, rich Albaik International''s hommos is prepared with crushed chickpeas mixed with tahini sauce and drizzled with pure olive oil and topped with a green olive; served with our signature saj bread',	169.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584233,	0,	NULL,	'f',	NULL,	NULL),
('cf40bccd-9026-4b46-8a69-c5cf39b3ea61',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Double Espresso',	'active',	'',	149.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584285,	0,	NULL,	'f',	NULL,	NULL),
('878bd16d-a8d5-4099-bcbc-2d65a4a02c00',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Fries With Garlic Sauce',	'active',	'Golden crispy French fries served with Albaik International''s signature garlic sauce',	109.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584235,	0,	NULL,	'f',	NULL,	NULL),
('e6eb00e7-1efb-49af-88bc-bff85615d98f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Corn On The Cob',	'active',	'Served piping hot with a pack of butter on the side to spread on top',	99.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584232,	0,	NULL,	'f',	NULL,	NULL),
('f8ce9487-c3db-4da3-ac2d-755f89db76e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Panner Onion',	'active',	'',	90.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584295,	0,	NULL,	'f',	NULL,	NULL),
('06903eeb-11e1-42e6-a69f-f0769cf95017',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'French Fries',	'active',	'Golden crispy French fries served with  Ketchup',	89.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584234,	0,	NULL,	'f',	NULL,	NULL),
('66628bb4-9012-4cae-82c0-81ee0906bbc3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Coleslaw Salad',	'active',	'Freshly prepared shredded cabbage and carrots mixed with our special salad dressing',	89.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584231,	0,	NULL,	'f',	NULL,	NULL),
('3f45544a-40e8-479d-9065-997223315e52',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Fries',	'active',	'',	79.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584254,	0,	NULL,	'f',	NULL,	NULL),
('221b101e-c8f9-4091-b5e0-ffc03c8fa9cf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Coke Big',	'active',	'',	57.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584281,	0,	NULL,	'f',	NULL,	NULL),
('9652467e-b486-4615-9a73-fdb7b99c4833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Thumsup Big',	'active',	'',	57.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584282,	0,	NULL,	'f',	NULL,	NULL),
('dcfb949f-7d3a-4fe0-b133-d25d3d33d0ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Demo Add Irish Coffee',	'active',	'',	49.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584294,	0,	NULL,	'f',	NULL,	NULL),
('22a03b92-0b79-418e-a1a5-c9398d6eddb0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Demo Add Hazelnut',	'active',	'',	49.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584291,	0,	NULL,	'f',	NULL,	NULL),
('4f401bbb-352f-4db0-adf6-ee2c9111566d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Add Caramel',	'active',	'',	49.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584293,	0,	NULL,	'f',	NULL,	NULL),
('8d2e0206-2850-43e9-b8d9-f0830e489226',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Add Cinnamon',	'active',	'',	49.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584292,	0,	NULL,	'f',	NULL,	NULL),
('ac10fc4b-d9b2-40fc-8806-5ecdaab14db4',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Fanta',	'active',	'',	38.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584278,	0,	NULL,	'f',	NULL,	NULL),
('9640e9ea-fbf5-4234-b715-d403c0764479',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Thumsup',	'active',	'',	38.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584274,	0,	NULL,	'f',	NULL,	NULL),
('dd5a4ecc-f519-4398-b4df-bbf72504c286',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Coke',	'active',	'',	38.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584248,	0,	NULL,	'f',	NULL,	NULL),
('1d476b6c-3598-4430-a22a-59c432a191ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Diet Coke',	'active',	'',	38.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584249,	0,	NULL,	'f',	NULL,	NULL),
('774c01d4-b3b3-4d30-8ac9-024f14a11683',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Sprite',	'active',	'',	38.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584250,	0,	NULL,	'f',	NULL,	NULL),
('fad988c7-6f92-4115-88bc-28f3b970fc16',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Nescafe Intense',	'active',	'',	33.25,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584243,	0,	NULL,	'f',	NULL,	NULL),
('58815835-847b-4cd2-b288-a8b00e689c20',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Nescafe Latte',	'active',	'',	33.25,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584244,	0,	NULL,	'f',	NULL,	NULL),
('83edf401-fc18-43c1-b730-d4cc60765a90',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Nescafe Hazelnut',	'active',	'',	33.25,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584258,	0,	NULL,	'f',	NULL,	NULL),
('1e418113-cb85-401b-b24e-f2223202d5df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'59887de6-a3bf-4bf9-ac00-bc6089fff3ee',	'Icecream With Chocolate Syrup',	'active',	'demo 2 demo demo2 demo 2 demo',	29.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584273,	0,	NULL,	'f',	NULL,	NULL),
('22121a37-58e3-4c86-be99-f07c833b09f0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'59887de6-a3bf-4bf9-ac00-bc6089fff3ee',	'Icecream With Strawberry Syrup',	'active',	'demo 3 demo demo 3 demo 3 demo',	29.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584272,	0,	NULL,	'f',	NULL,	NULL),
('6ca371d0-69f5-4eeb-a74e-18d2c9689153',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'7"Up',	'active',	'',	28.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584252,	0,	NULL,	'f',	NULL,	NULL),
('9f3799db-bd91-475a-a391-b2d42f9f9cef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Diet Pepsi',	'active',	'',	28.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584280,	0,	NULL,	'f',	NULL,	NULL),
('7122fc9e-1388-4928-a7ce-eb05440bf411',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Pepsi',	'active',	'',	28.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584251,	0,	NULL,	'f',	NULL,	NULL),
('d8f56a16-5780-4cb1-807d-1f0e8360ce49',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Miranda',	'active',	'',	28.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584247,	0,	NULL,	'f',	NULL,	NULL),
('8d7e2339-8bae-4b8d-9041-07457b74a8c8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Mounain Dew',	'active',	'',	28.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584275,	0,	NULL,	'f',	NULL,	NULL),
('93576a56-e2d6-4a85-bf60-e17996efe135',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Spicy Cocktail Sauce',	'active',	'',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584268,	0,	NULL,	'f',	NULL,	NULL),
('92d09059-47b9-4cba-96aa-165c5cb831dc',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Saj Bread',	'active',	'',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584269,	0,	NULL,	'f',	NULL,	NULL),
('3ea87341-2850-446f-8e7e-8f74dc536061',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'59887de6-a3bf-4bf9-ac00-bc6089fff3ee',	'Vanilla Icecream',	'active',	'demo 4 demo 4 demo 4 dmwo 4',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584271,	0,	NULL,	'f',	NULL,	NULL),
('43dd1e57-b32e-47ce-ab42-7fff14442392',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Juices',	'active',	'Pomogranate,Orange,Apple And Mixed Fruit Juice',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584241,	0,	NULL,	'f',	NULL,	NULL),
('91dda6f8-780d-4b6b-96f3-4f1b4c1c3902',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Bun',	'active',	'A pieces of seasame bun baked fresh daily from the best bakeries in town. Soft and delicious',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584236,	0,	NULL,	'f',	NULL,	NULL),
('4cccc120-afaf-4187-abae-b5f0323493ef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Garlic Sauce',	'active',	'Our signature garlic sauce will always have you asking for more.',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584237,	0,	NULL,	'f',	NULL,	NULL),
('0b8d698b-1770-4bdf-b34e-d199747ca995',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Cocktaill Sauce',	'active',	'Albaik International''s special blend makes a delicious addition to any of our specialties',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584238,	0,	NULL,	'f',	NULL,	NULL),
('3cd8f798-70cb-41de-b79c-db089f791aa3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Demo Dill Pickles',	'active',	'',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584257,	0,	NULL,	'f',	NULL,	NULL),
('0d8428dd-14e4-4084-88b9-ca8b015053db',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Cheese Slice',	'active',	'',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584256,	0,	NULL,	'f',	NULL,	NULL),
('e7e98cdf-5e51-42d0-b694-896c1881b56a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Nugget Sauce',	'active',	'Hot & spicy nugget sauce won''t surely let you down.',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584239,	0,	NULL,	'f',	NULL,	NULL),
('1847e275-3d07-45b9-8b4d-d88bd32a6cff',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Tartar Sauce',	'active',	'A Treat for your taste buds with this  sauce made with mayonnaise , parsley ,carrot, gherkins  & lime juice',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584240,	0,	NULL,	'f',	NULL,	NULL),
('b69dfe6e-f702-4d5f-818c-16d32e4561d2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Bisleri 1000ml',	'active',	'',	19.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584242,	0,	NULL,	'f',	NULL,	NULL),
('81f473ad-acf1-42f7-9b65-4ef3a075abf5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Sauce',	'active',	'',	10.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584255,	0,	NULL,	'f',	NULL,	NULL),
('37383633-9aa4-4bbd-b60e-37098f98b8fd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Spicy',	'active',	'',	10.00,	't',	't',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584246,	0,	NULL,	'f',	NULL,	NULL),
('4d190d71-e10a-4aed-98a2-4485f74cb43d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Water',	'active',	'',	9.50,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584253,	0,	NULL,	'f',	NULL,	NULL),
('c5e59250-10a9-44ea-9539-a1615e04b3a3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd6524dcd-3279-4a31-aa7c-dd42024e4906',	'Demo Brown Bag',	'active',	'',	1.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584276,	0,	NULL,	'f',	NULL,	NULL),
('31a2b366-ee53-4a7e-8e18-58d7a647b39f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'59887de6-a3bf-4bf9-ac00-bc6089fff3ee',	'Promotion Ice',	'active',	'demo 1 demo1 demo 1',	0.95,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584277,	0,	NULL,	'f',	NULL,	NULL),
('eef9b0b6-fad0-4b33-9566-05ac24c46f92',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Macchiato',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584284,	0,	NULL,	'f',	NULL,	NULL),
('8d9d66b3-7e6e-4c9e-9481-f71054454878',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Drumsticks',	'active',	'Crispy chicken drumsticks come with some fries and garlic sauce. Albaik International''s Chicken drumsticks are marinated in our signature marinade - a unique and tantalizing blend of 18 herbs and spices',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584215,	0,	NULL,	'f',	NULL,	NULL),
('e74ee574-fdf1-440d-afb7-6958fe388f22',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'03b2f2fe-d114-4ed9-985e-2f82a3715669',	'Flat White',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584286,	0,	NULL,	'f',	NULL,	NULL),
('2b50afaa-e73c-4e86-93f7-4bf06abc6d0d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Cappuccino',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584287,	0,	NULL,	'f',	NULL,	NULL),
('d47ae63a-ad96-4311-9e1d-fff7e6df18a9',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Mochacinno',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584288,	0,	NULL,	'f',	NULL,	NULL),
('6fd61c08-24c3-4f88-a59e-2423a6be6619',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Caramel Affogatto',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584289,	0,	NULL,	'f',	NULL,	NULL),
('0db147db-79bd-4943-81a8-62a2257af888',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'c1a71129-8263-44c3-b1f0-c602a5bd564f',	'Hot Chocolate',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584290,	0,	NULL,	'f',	NULL,	NULL),
('4752e0dd-4b55-4941-a41e-e919b8930321',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Soft Drinks',	'active',	'Coke , Diet Coke , Thums Up , Fanta , Nescafe Cold Coffee',	0.00,	't',	't',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'1',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584279,	0,	NULL,	'f',	NULL,	NULL),
('d20dfcb6-ec10-41a2-a255-df4380f264e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'95206d03-5227-4913-a100-29fbdda4031f',	'Americano',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584283,	0,	NULL,	'f',	NULL,	NULL),
('e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Albaik International Chicken Meal',	'active',	'Chicken meal comes with fries, a bun and  garlic sauce.The first bite will have you going Mmmmm - Every piece of Albaik International''s Chicken is marinated in our signature marinade - a unique and tantalizing blend of 18 herbs and spices',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584214,	0,	NULL,	'f',	NULL,	NULL),
('0b4f1a68-a7ca-4ce1-ad83-ab06f4fc9baf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Fillet Nuggets Meal',	'active',	'chicken fillet nuggets come with fries, a bun and a sauce of your choice   (nuggets sauce/garlic sauce) Tender all breast chicken fillets pieces marinated in our unique & signature blend then breaded, seasoned to perfection and deep-fried in 100% pure vegetable oil until each piece is moist, tender and juicy from the inside, crispy and perfectly golden on the outside allowing for the Mmmm sensation with every bite',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584217,	0,	NULL,	'f',	NULL,	NULL),
('076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Fish Fillet Meal',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584225,	0,	NULL,	'f',	NULL,	NULL),
('b24d4fee-15a3-4905-841d-1f91304a16aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Value Shrimp Meal',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584228,	0,	NULL,	'f',	NULL,	NULL),
('5fa2b9f6-cad8-40ed-a0e8-ad16c0e71c41',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Shrimp Meal',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584229,	0,	NULL,	'f',	NULL,	NULL),
('661ec707-d1d5-4a33-bdad-e57fc207f9d5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Drumstick Spicy',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584245,	0,	NULL,	'f',	NULL,	NULL),
('2520329c-cfae-4508-b989-4d675272febe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Wings',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584260,	0,	NULL,	'f',	NULL,	NULL),
('50e9690b-79dc-4c67-8008-71c0abfdcde2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Spicy Chicken Wings',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584261,	0,	NULL,	'f',	NULL,	NULL),
('4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Meal 1',	'active',	'Chicken fillet in a bun  with coleslaw,lettuce, pickles and our  spicy cocktail sauce. This sandwich is made with care to make sure that each and every bite is packed with Mmmm',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584262,	0,	NULL,	'f',	NULL,	NULL),
('dde8f4f6-bbc4-4e19-aa0d-99111cc544c0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Spicy Shrimp Meal',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584264,	0,	NULL,	'f',	NULL,	NULL),
('716142d8-d8a3-4206-853b-7f27f96e7623',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'ed759647-26b7-4b52-85ca-29c66310159e',	'Spicy Value Shrimp Meal',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584265,	0,	NULL,	'f',	NULL,	NULL),
('c87fee4b-b1ee-47a8-9003-96923fcead27',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Kosha With Polau',	'active',	'',	300.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584306,	0,	NULL,	'f',	NULL,	NULL),
('6b0735d2-6671-4457-b190-d5f06a564e8d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken Istooooo',	'active',	'',	91.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584297,	0,	NULL,	'f',	NULL,	NULL),
('66ca988f-16a5-432a-8d3f-413684dee734',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'e1639f72-fca0-43f9-b1fe-9193cb5c970e',	'Abu Special Chicke',	'active',	'Long chicken',	0.00,	't',	't',	25,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	't',	'f',	't',	't',	'f',	't',	'not-applicable',	'1',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10587996,	0,	NULL,	'f',	NULL,	NULL),
('fcedaa98-6973-4c2f-a1b2-c239491e6658',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'A24-chicken',	'active',	'A24-chicken,A24-chicken',	0.00,	't',	't',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'1',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10587463,	0,	NULL,	'f',	NULL,	NULL),
('86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Tikka',	'active',	'',	0.00,	't',	't',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'1',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584298,	0,	NULL,	'f',	NULL,	NULL),
('01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'Chicken',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	1,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584296,	0,	NULL,	'f',	NULL,	NULL),
('59e4ed30-c29b-4bcf-afc6-5a6b017e2f0c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Loppypop',	'active',	'',	120.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	2,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584299,	0,	NULL,	'f',	NULL,	NULL),
('52ce20ea-7a18-41c0-a1fb-b75c9d05e398',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Hnadi',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	3,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584300,	0,	NULL,	'f',	NULL,	NULL),
('cc350737-de7b-4dfe-a3ca-e1d34a203541',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Soup Bowl',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	4,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584301,	0,	NULL,	'f',	NULL,	NULL),
('2fb8d0a2-9018-4c87-9cb6-8532626a588c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Fry',	'active',	'',	120.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	5,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584302,	0,	NULL,	'f',	NULL,	NULL),
('733a1265-faab-4b2a-8ed1-124856124f5a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Ukkad',	'active',	'',	160.00,	'f',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	6,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584303,	0,	NULL,	'f',	NULL,	NULL),
('3e2c1e69-0ffc-493f-92a7-e37e3dee3e12',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Thali',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	7,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584304,	0,	NULL,	'f',	NULL,	NULL),
('1b7deb00-7ddd-4a7e-8aa9-23125db6e320',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'Chicken Kaleji Fry',	'active',	'',	0.00,	't',	'f',	NULL,	NULL,	NULL,	NULL,	NULL,	0.00,	'd3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	8,	'f',	'f',	'f',	't',	'f',	'f',	'not-applicable',	'0',	NULL,	'f',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	10584305,	0,	NULL,	'f',	NULL,	NULL);

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

INSERT INTO "menu_item_addon_group" ("menu_item_addon_group_id", "restaurant_id", "menu_item_addon_group_name", "menu_item_addon_group_rank", "menu_item_addon_group_status", "menu_item_addon_group_selection_min", "menu_item_addon_group_selection_max", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_addon_group_id") VALUES
('4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Soft Drinks',	1,	'active',	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12871),
('9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Chicken',	2,	'active',	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12872),
('f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Salad',	3,	'active',	NULL,	NULL,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12873);

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

INSERT INTO "menu_item_addon_item" ("menu_item_addon_id", "menu_item_addon_group_id", "restaurant_id", "menu_item_addon_item_name", "menu_item_addon_item_price", "menu_item_addon_item_status", "menu_item_addon_item_rank", "menu_item_addon_item_attribute_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_addon_item_id") VALUES
('650bb423-59c3-4afd-b183-78d050430f26',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Coke',	10.00,	'active',	1,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('611b0907-b9d7-48f3-b2b8-747c6e8f7f4e',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Diet Coke',	20.00,	'active',	2,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('4b72ea14-713f-4dc1-a2ba-992741c79ea3',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Thumps Up',	30.00,	'active',	3,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('237b5886-391a-4b8d-a5e9-0b5dfa9e78fe',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Fanta',	40.00,	'active',	4,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('aa0442d8-f1d0-450c-9f31-20dfa222f2b6',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Nescafe Cold Coffee',	50.00,	'active',	5,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('5157cc60-6548-4fd6-af6b-9391dc151033',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Some Chutny',	5.00,	'active',	1,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('54c036ba-73b3-4f97-9982-bc8861b9268b',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Add Tamato',	10.00,	'active',	2,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('ce088fb8-00dc-41ec-a5d7-8ae1caa6e104',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Add Green Chutny',	5.00,	'active',	3,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('030bf16e-c890-4ded-94b3-cd7cf1a0040d',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Add Lemon',	10.00,	'active',	4,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('2baa83b8-166d-4a0d-b631-f2cd859e04cb',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Provide Salad Extra',	20.00,	'active',	5,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('62095eb6-b43c-498e-914a-54c76d75affb',	'f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Add Green Chutny',	5.00,	'active',	1,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL),
('01be9a97-e95e-4477-9578-fc3e4c882a8e',	'f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Add Chilly',	5.00,	'active',	2,	'9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	NULL);

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

INSERT INTO "menu_item_addon_mapping" ("menu_item_addon_mapping_id", "menu_item_id", "menu_item_variation_id", "menu_item_addon_group_id", "restaurant_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('6a2d9167-b10e-4337-bfc7-fdeb25cca8d8',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'a8e7c72b-4926-4129-abb3-85404f507832',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4d048959-f0ea-436d-b728-d9e1377c24ee',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'a8e7c72b-4926-4129-abb3-85404f507832',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('489d4148-64b6-4987-8225-28d6bbdb495e',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'd0c878e7-1c9e-4c07-9b30-fe65c80df0b3',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('31360bea-5b0f-431b-9b34-e8026fac6348',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'd0c878e7-1c9e-4c07-9b30-fe65c80df0b3',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('ba7da6f1-0e70-402b-9589-c936c9f7f1fb',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'29759346-c6c9-4a05-97cb-9a9580d12854',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('e7ee84e7-2bf6-4765-a002-79d95dfc5d77',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'1fb84aff-e670-4d05-aebd-ce40895f284b',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6ef8eb40-84d9-48cc-9e6b-ca1d74acfdd5',	'66ca988f-16a5-432a-8d3f-413684dee734',	'd0ede37c-cd3e-4000-bb61-2c412a8b7efc',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a2996642-f439-4bf2-86ab-3ad6cd48f82b',	'66ca988f-16a5-432a-8d3f-413684dee734',	'd0ede37c-cd3e-4000-bb61-2c412a8b7efc',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2f0e3965-17f5-4ded-b934-c3f4128310c2',	'66ca988f-16a5-432a-8d3f-413684dee734',	'd0ede37c-cd3e-4000-bb61-2c412a8b7efc',	'f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('dec5e1e4-e943-49d0-bddc-4a5ddb1b6e25',	'fcedaa98-6973-4c2f-a1b2-c239491e6658',	'f84b90a7-ff4f-4a07-b2dc-99ecd3f6820b',	'4728faeb-8bd2-4778-b701-661a6dc4178b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('84625709-8ff8-47a3-b1c4-2298ce1900a1',	'fcedaa98-6973-4c2f-a1b2-c239491e6658',	'f84b90a7-ff4f-4a07-b2dc-99ecd3f6820b',	'f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f84b25d5-0206-4bec-a533-7d589b49bedf',	'86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'8d1bfe5f-1131-4cf3-9794-7aaa6fef98fb',	'9d04a3ea-65c5-4a8b-ada7-24f18cf82382',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('622373c3-1af3-4934-a505-2a6a861df33f',	'86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'8d1bfe5f-1131-4cf3-9794-7aaa6fef98fb',	'f3ae4db2-378e-4e59-ab90-339a6d127a8f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

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

INSERT INTO "menu_item_attribute" ("menu_item_attribute_id", "menu_item_attribute_name", "menu_item_attribute_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_attributes_id", "restaurant_id") VALUES
('9ce11905-18ff-4cdd-8cb2-74eb350bc95c',	'veg',	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	1,	NULL),
('d3a1ad7e-874f-4b8b-ae82-0af81adc06e8',	'non-veg',	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	2,	NULL),
('a5fa2867-d9e6-4011-911c-4b0808256cf0',	'egg',	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	24,	NULL);

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

INSERT INTO "menu_item_tag" ("menu_item_tag_id", "menu_item_tag_name", "menu_item_tag_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('4bf34633-80ed-40e8-bf7c-7867d452f48b',	'chef-special',	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

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

INSERT INTO "menu_item_tag_mapping" ("menu_item_tag_mapping_id", "menu_item_id", "menu_item_tag_id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('6722fcad-af11-49ae-8147-183b3357da98',	'66ca988f-16a5-432a-8d3f-413684dee734',	'4bf34633-80ed-40e8-bf7c-7867d452f48b',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

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

INSERT INTO "menu_item_tax_mapping" ("menu_item_tax_mapping_id", "menu_item_id", "restaurant_id", "tax_id", "is_tax_inclusive", "gst_liability", "gst_type", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('bbf3b681-b720-4a39-8b86-3c63d3ed85d4',	'b138efbe-95c0-46c0-9e3d-493c0468f9b7',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1910211a-b597-4c23-9424-281cb4560848',	'b138efbe-95c0-46c0-9e3d-493c0468f9b7',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2561dd48-42ec-4af7-8006-f2cc9d44e695',	'c01c6fd1-8ffe-4298-b062-b88313b33dfd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4f377a38-c2e3-4fcc-8d89-45d1797a37a7',	'c01c6fd1-8ffe-4298-b062-b88313b33dfd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('64a31458-f7d8-4c66-b797-f68199a35833',	'1ef1e318-ce3f-4ec5-8eb6-42316b1834a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3b425af3-3d74-48a9-8e49-e6bb516948a0',	'1ef1e318-ce3f-4ec5-8eb6-42316b1834a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('42d89de2-1aa1-40f0-99ee-c2e4922efe41',	'5ac17a93-67a9-4bdd-8ef7-dadcbea38d83',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2556730e-9be1-4e1d-966d-380f2d86e36c',	'5ac17a93-67a9-4bdd-8ef7-dadcbea38d83',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3e18fed9-cf2e-43d0-824a-8fac74f36fc6',	'4ad4ad2a-50b7-4498-956c-4c5ac66dce9c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('03d4509f-e5f4-449e-b077-ec11d33172b6',	'4ad4ad2a-50b7-4498-956c-4c5ac66dce9c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('92ebfea3-1e3d-4f95-b72d-46e210677b5b',	'd1652219-e03c-4789-b1e5-4f2c1924dbeb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('378f1c91-87c2-4da6-92a9-d1fc2d336ebf',	'd1652219-e03c-4789-b1e5-4f2c1924dbeb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5647dccf-aa80-4628-93c7-1f09b2adf1d8',	'e53d05d3-447e-4e38-bba7-bd8a856b4dbe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('be560e94-1f27-432f-b37d-75717884ed12',	'e53d05d3-447e-4e38-bba7-bd8a856b4dbe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3a936a21-b941-43e1-9390-5d493f4ccd12',	'48bec079-e48a-4e49-ae41-ef06cf1bf431',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('00f16ec6-c54f-46b9-82e1-2a26c4e4ea08',	'48bec079-e48a-4e49-ae41-ef06cf1bf431',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('37e62ad6-bf8f-4f37-a94f-ff57d74e498c',	'a4591e03-f6ef-4101-9148-550af7d501f5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a38259ad-1a8e-4a1e-8f3e-55aad2ba4d45',	'a4591e03-f6ef-4101-9148-550af7d501f5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1ca9fc42-7d66-4d61-9191-64bf08fba1b3',	'1494edbc-1c05-4247-a198-f33aff9623a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d4aefd05-8440-4e26-a6c4-a7646adbf3a9',	'1494edbc-1c05-4247-a198-f33aff9623a1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3dc7d24a-f8a9-48ab-84b4-3397417d4b28',	'36cb1f23-cc55-4098-86ed-2322ce4818aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f4ac1810-f546-4a52-8875-d173f8034426',	'36cb1f23-cc55-4098-86ed-2322ce4818aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6826cd7d-29af-43c7-9703-3b90aa860eb6',	'bf0193e5-5f87-4e87-8382-8173d3385053',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c83f57e7-f870-4fc8-adf3-5788ba7d98e9',	'bf0193e5-5f87-4e87-8382-8173d3385053',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6a96bf36-82c7-473f-94b3-32c7dad77160',	'5c4e0a45-857b-4842-a13b-515cd01de0df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('70206360-10b7-4142-8cb5-ecdf48301429',	'5c4e0a45-857b-4842-a13b-515cd01de0df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3722b1ff-bee9-4d85-88bd-fbe7ae98db4a',	'4ef99f19-4110-4f84-9b0a-cf1dcbd0eae1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b4e9f54b-e516-44c7-a855-9e48cf0c05c7',	'4ef99f19-4110-4f84-9b0a-cf1dcbd0eae1',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a83251bf-e4a8-4213-b7e5-c2ef20d4be14',	'f267185f-84e8-45a9-8cfd-14972f0cd49b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c2c2390c-76f3-4845-b61d-c067b4cbd7ee',	'f267185f-84e8-45a9-8cfd-14972f0cd49b',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('7425ff12-7d6c-4d40-80bd-f7897b0e5f0a',	'92600ad6-b38f-4221-b97e-06e34fea9b5c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('ecd5c92c-ed3e-4ed1-8953-f6a094fed889',	'92600ad6-b38f-4221-b97e-06e34fea9b5c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('78589b31-1248-4f3e-ba03-beb2cd3c880d',	'b98b877a-8e9b-40c0-95fc-0d1640c8f28f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('26952040-8843-425b-a191-4c45227cfbb0',	'b98b877a-8e9b-40c0-95fc-0d1640c8f28f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('73105a1a-32d6-4929-b6b0-4c3a0b0803f8',	'cf40bccd-9026-4b46-8a69-c5cf39b3ea61',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('17a8ecd2-1b4f-4aad-b350-f33906af3060',	'cf40bccd-9026-4b46-8a69-c5cf39b3ea61',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('e7c8cb00-b1d6-4d1b-a7c0-b80d18616f75',	'878bd16d-a8d5-4099-bcbc-2d65a4a02c00',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('17b37859-a9b5-4a8a-9843-b503c9234a39',	'878bd16d-a8d5-4099-bcbc-2d65a4a02c00',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6bf6e746-9273-4d02-ac9a-f5d703c95d51',	'e6eb00e7-1efb-49af-88bc-bff85615d98f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('79d3d0e4-432a-475b-a324-ee2773738a52',	'e6eb00e7-1efb-49af-88bc-bff85615d98f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('192c3bb7-71aa-4708-84b9-9d9dd27f4260',	'f8ce9487-c3db-4da3-ac2d-755f89db76e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3f4e545a-5cd3-43aa-b899-1d334be90774',	'f8ce9487-c3db-4da3-ac2d-755f89db76e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('8902c577-6a18-4875-a72f-a85d40449d0f',	'06903eeb-11e1-42e6-a69f-f0769cf95017',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('e001ce87-b82c-42b8-ba0b-c81bb006be64',	'06903eeb-11e1-42e6-a69f-f0769cf95017',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('565c2b9a-ece5-48df-962c-248f4a2a0cef',	'66628bb4-9012-4cae-82c0-81ee0906bbc3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6deff1e6-e20d-4905-96b2-da5ac48ce824',	'66628bb4-9012-4cae-82c0-81ee0906bbc3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('41ca5e40-d043-4956-8182-a8185afbc0a5',	'3f45544a-40e8-479d-9065-997223315e52',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5e06209b-6de5-4392-81af-852735bb12cb',	'3f45544a-40e8-479d-9065-997223315e52',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f8d69be5-9810-4635-b848-7e08aca2f490',	'221b101e-c8f9-4091-b5e0-ffc03c8fa9cf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('333cdc4d-852b-45a8-aea4-6fc8ab3b1cf1',	'221b101e-c8f9-4091-b5e0-ffc03c8fa9cf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1a2ec612-3cb3-4c2e-be51-9fc9aff80958',	'9652467e-b486-4615-9a73-fdb7b99c4833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('fbef9ddc-1910-43c1-b909-282ec3ed5de1',	'9652467e-b486-4615-9a73-fdb7b99c4833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('058ec8d0-731d-48ea-ba75-ecd585bfa07e',	'dcfb949f-7d3a-4fe0-b133-d25d3d33d0ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c8cb3aa6-699c-4ea5-a8aa-bbcd8a7c26c3',	'dcfb949f-7d3a-4fe0-b133-d25d3d33d0ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('28575a0f-915d-44d4-8a3c-3478d3be4e5d',	'22a03b92-0b79-418e-a1a5-c9398d6eddb0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b3e9471b-5ec0-406f-bc95-1d8581f13675',	'22a03b92-0b79-418e-a1a5-c9398d6eddb0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('52722359-35f3-4807-9855-3fca7cd69966',	'4f401bbb-352f-4db0-adf6-ee2c9111566d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b98e2b27-8806-444b-b56e-cb7375e820f9',	'4f401bbb-352f-4db0-adf6-ee2c9111566d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('da789b67-a5c1-43ba-8b8f-a758bbd93594',	'8d2e0206-2850-43e9-b8d9-f0830e489226',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('368d2686-6783-4360-8db0-f0c18df44f4a',	'8d2e0206-2850-43e9-b8d9-f0830e489226',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('7911b8f3-7cfe-4741-9f3d-f7917a27a70d',	'ac10fc4b-d9b2-40fc-8806-5ecdaab14db4',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4a4cecff-eb5a-4427-b918-2b78572d7739',	'ac10fc4b-d9b2-40fc-8806-5ecdaab14db4',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('16b2643e-6e04-421e-9228-f5842d635149',	'9640e9ea-fbf5-4234-b715-d403c0764479',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('893635c3-7bd7-4ff4-beda-528a2d5f16ab',	'9640e9ea-fbf5-4234-b715-d403c0764479',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6181f936-535f-4ff2-9d0d-448007809cec',	'dd5a4ecc-f519-4398-b4df-bbf72504c286',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6945e7a3-362f-41e5-9a2f-e06cb1556dd9',	'dd5a4ecc-f519-4398-b4df-bbf72504c286',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('aafe6bda-62ec-4ec2-b7f0-bdf786b0547a',	'1d476b6c-3598-4430-a22a-59c432a191ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('14b28f78-71d0-4f52-ac85-0809be5401dc',	'1d476b6c-3598-4430-a22a-59c432a191ca',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('53686b71-de6c-4fbf-b8e9-7581c9c096d8',	'774c01d4-b3b3-4d30-8ac9-024f14a11683',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('567b57d7-4426-41cf-b05d-33f8339fb4e5',	'774c01d4-b3b3-4d30-8ac9-024f14a11683',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('8319233c-7343-422c-8b90-3e3d13d2bf9c',	'fad988c7-6f92-4115-88bc-28f3b970fc16',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d48487ab-c4c6-48cb-9bc4-d81f246bd5db',	'fad988c7-6f92-4115-88bc-28f3b970fc16',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4b2e9db9-980c-468c-b917-702fc77d5f71',	'58815835-847b-4cd2-b288-a8b00e689c20',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d0a24a27-707c-4a0d-9ee6-0e4ed6e1a1ac',	'58815835-847b-4cd2-b288-a8b00e689c20',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('30badac3-fae5-4e68-97b2-19e5de76a15d',	'83edf401-fc18-43c1-b730-d4cc60765a90',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('617ad856-3076-4a43-95dc-ed68dbd0a5c1',	'83edf401-fc18-43c1-b730-d4cc60765a90',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0c5d4cc8-a85e-4f4f-a1dd-009643b491af',	'1e418113-cb85-401b-b24e-f2223202d5df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a09c62ba-ed16-4977-b711-abd9f935b360',	'1e418113-cb85-401b-b24e-f2223202d5df',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d844a472-0041-457d-bd70-791948a6e695',	'22121a37-58e3-4c86-be99-f07c833b09f0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2cbd72f8-9de9-4ac4-ad91-af1e6d2fa8a9',	'22121a37-58e3-4c86-be99-f07c833b09f0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b8a3f624-19b2-469e-8360-9acdc5c25bd1',	'6ca371d0-69f5-4eeb-a74e-18d2c9689153',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('8f72d430-37c8-4f46-a6a4-da7528ec95fe',	'6ca371d0-69f5-4eeb-a74e-18d2c9689153',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9024926a-8c5e-47f8-912c-7f32c876fafb',	'9f3799db-bd91-475a-a391-b2d42f9f9cef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c1602d73-cf86-45ca-b9f9-157ccaeda6b6',	'9f3799db-bd91-475a-a391-b2d42f9f9cef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a9708308-c0f0-4592-9843-91c0b3934915',	'7122fc9e-1388-4928-a7ce-eb05440bf411',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a407e659-657d-455f-abe6-3e9448978cfe',	'7122fc9e-1388-4928-a7ce-eb05440bf411',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4a218e46-9978-4d78-aa7e-16c18a033d2f',	'd8f56a16-5780-4cb1-807d-1f0e8360ce49',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d3887e7d-aecb-4997-9d02-b855f753ea5e',	'd8f56a16-5780-4cb1-807d-1f0e8360ce49',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3c031004-3b1d-4a67-aefe-f9ada8865d85',	'8d7e2339-8bae-4b8d-9041-07457b74a8c8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('bb04823d-d78b-4636-b70f-f28c9a570dcb',	'8d7e2339-8bae-4b8d-9041-07457b74a8c8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('42464520-235a-4ea0-acde-fd1726b84e5e',	'93576a56-e2d6-4a85-bf60-e17996efe135',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('107c282c-309c-4b1b-9929-3d09d13ed5bc',	'93576a56-e2d6-4a85-bf60-e17996efe135',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('dfdc10bd-822c-4dd7-8da7-4583cbc6f842',	'92d09059-47b9-4cba-96aa-165c5cb831dc',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('bd054c46-2bb8-48d8-91e1-2f29842e4771',	'92d09059-47b9-4cba-96aa-165c5cb831dc',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('910c417d-d802-458a-92cd-00038290b4ab',	'3ea87341-2850-446f-8e7e-8f74dc536061',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1897bb00-c7c9-4804-b432-523fc523320f',	'3ea87341-2850-446f-8e7e-8f74dc536061',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f56af616-6c36-41ee-a9b5-6c8b190cc79b',	'43dd1e57-b32e-47ce-ab42-7fff14442392',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9435b633-4ef8-45cf-96b2-01953b5752f4',	'43dd1e57-b32e-47ce-ab42-7fff14442392',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2aed555d-e6c2-41ae-87ae-01a04d570b52',	'91dda6f8-780d-4b6b-96f3-4f1b4c1c3902',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c1598102-19da-4c94-bbe5-70120874d94c',	'91dda6f8-780d-4b6b-96f3-4f1b4c1c3902',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f1d4e15b-4c54-4eab-982c-8fdd7c1d177c',	'4cccc120-afaf-4187-abae-b5f0323493ef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9af06cdb-0d37-40b5-9e36-ecfa565e01ec',	'4cccc120-afaf-4187-abae-b5f0323493ef',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('514d351e-c771-442d-b305-63e833bfdb07',	'0b8d698b-1770-4bdf-b34e-d199747ca995',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('ac7db1c0-bd81-41d6-82cb-bd0ae42f192d',	'0b8d698b-1770-4bdf-b34e-d199747ca995',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('447453f9-0f0e-4c9b-b8dc-958576493ec6',	'3cd8f798-70cb-41de-b79c-db089f791aa3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('07485ba5-8f43-4689-b921-67fff3b1daa1',	'3cd8f798-70cb-41de-b79c-db089f791aa3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('bfb15fa0-3d86-4b18-8d9b-6bfc5e105909',	'0d8428dd-14e4-4084-88b9-ca8b015053db',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1bfbc4b1-1cb8-4fa6-abcd-e7f5335d5570',	'0d8428dd-14e4-4084-88b9-ca8b015053db',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('77b53845-ee9e-4c6c-ad13-ba25b7c13e9d',	'e7e98cdf-5e51-42d0-b694-896c1881b56a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2838cfbf-4e3c-4c3b-ad24-28a0765492f9',	'e7e98cdf-5e51-42d0-b694-896c1881b56a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4840f2e2-c5bc-4f73-99d3-73fb4992604e',	'1847e275-3d07-45b9-8b4d-d88bd32a6cff',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3bd259eb-9316-4476-bef7-18376f530935',	'1847e275-3d07-45b9-8b4d-d88bd32a6cff',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('aa82e9fd-ffa2-44c1-972c-3657a9c145b7',	'b69dfe6e-f702-4d5f-818c-16d32e4561d2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6b5515b9-ae32-4fc4-89ee-353ed542c764',	'b69dfe6e-f702-4d5f-818c-16d32e4561d2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a721fada-753d-40a5-83cb-a79c4c078991',	'81f473ad-acf1-42f7-9b65-4ef3a075abf5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('31167916-a618-422c-bd55-8173f568ab4c',	'81f473ad-acf1-42f7-9b65-4ef3a075abf5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('00acf000-2125-4580-a472-7686edaff4d5',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4d7b4fd4-d24f-4090-810e-40c92e18e153',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('50172b70-27b8-4075-831e-d480b7b507d8',	'4d190d71-e10a-4aed-98a2-4485f74cb43d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('11d97c8e-9049-4a8c-bf46-2f4cd9a46120',	'4d190d71-e10a-4aed-98a2-4485f74cb43d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('444ceb1c-822f-4d9d-bb26-da9f4f4c1d54',	'c5e59250-10a9-44ea-9539-a1615e04b3a3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a0484b26-7ce6-4bfb-8b08-6c070032f5b5',	'c5e59250-10a9-44ea-9539-a1615e04b3a3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5b5d77f0-4348-4c10-963f-48250da9f837',	'31a2b366-ee53-4a7e-8e18-58d7a647b39f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('7fe41e40-4adb-4669-9ea4-3c31bc8773bd',	'31a2b366-ee53-4a7e-8e18-58d7a647b39f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b761cafb-b9ee-4c35-a59d-f04a8e446795',	'eef9b0b6-fad0-4b33-9566-05ac24c46f92',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a73ce03e-3927-427a-9260-f7da6ee3b667',	'eef9b0b6-fad0-4b33-9566-05ac24c46f92',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a083359f-ccfd-492d-a8e7-3b8a5666c57d',	'8d9d66b3-7e6e-4c9e-9481-f71054454878',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('8607eb4a-74d7-441f-a943-5b8a33abc7a0',	'8d9d66b3-7e6e-4c9e-9481-f71054454878',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0939e244-3237-41b2-809c-974995c92387',	'e74ee574-fdf1-440d-afb7-6958fe388f22',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3763c66c-1218-4aaf-8bf9-8d4d4eb212ed',	'e74ee574-fdf1-440d-afb7-6958fe388f22',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a1072499-0856-473d-a418-a4e54a606436',	'2b50afaa-e73c-4e86-93f7-4bf06abc6d0d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0ffbb30c-0f2a-40c2-8af2-90e0bdeb6679',	'2b50afaa-e73c-4e86-93f7-4bf06abc6d0d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('951f9333-ad52-48ee-b37a-5ed53a2c8009',	'd47ae63a-ad96-4311-9e1d-fff7e6df18a9',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b8784f40-8cfe-480a-a9d0-e347112c8866',	'd47ae63a-ad96-4311-9e1d-fff7e6df18a9',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a31dae98-463f-4c60-981e-240d1db6127d',	'6fd61c08-24c3-4f88-a59e-2423a6be6619',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('277e502e-25b8-457b-a0cd-50925e544bdc',	'6fd61c08-24c3-4f88-a59e-2423a6be6619',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6481e2ec-4ec5-4e78-95d3-91633afd8c1a',	'0db147db-79bd-4943-81a8-62a2257af888',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c07f2ad0-4375-4fb1-a301-f55ed963b881',	'0db147db-79bd-4943-81a8-62a2257af888',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0e72a956-9bd3-41ea-a314-9ec500fb2ad5',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9f29f9c0-e6df-4cd0-a886-3aaca76d3789',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a99027a9-0d53-4d66-9d08-263cd97d9494',	'd20dfcb6-ec10-41a2-a255-df4380f264e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2a187421-ee9b-4ed9-a306-bbe50f057710',	'd20dfcb6-ec10-41a2-a255-df4380f264e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5cd8fd4b-5776-45a1-848d-1af009d02643',	'e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('8d8475e2-8c99-46e9-bd8a-97e8de50c02f',	'e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('113c3455-0548-4319-a5af-c7f389d08bef',	'0b4f1a68-a7ca-4ce1-ad83-ab06f4fc9baf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('56334485-3512-481c-994a-86a1be3da97d',	'0b4f1a68-a7ca-4ce1-ad83-ab06f4fc9baf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b7cfe627-e50a-4d4c-9278-0bf2c0f6e87c',	'076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c776c569-e844-4515-926f-bbe901ced3e5',	'076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('e6937122-4138-415b-aefd-a21def5db82d',	'b24d4fee-15a3-4905-841d-1f91304a16aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5113d674-0607-45bd-9cb7-bc4bb73da080',	'b24d4fee-15a3-4905-841d-1f91304a16aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('53467d67-313e-4c9d-8f39-be51f946f04b',	'5fa2b9f6-cad8-40ed-a0e8-ad16c0e71c41',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('a3ef3cd5-b253-474d-930c-40df7cdd0bb9',	'5fa2b9f6-cad8-40ed-a0e8-ad16c0e71c41',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('ae093aff-4edb-43b0-ba24-37c250a32ace',	'661ec707-d1d5-4a33-bdad-e57fc207f9d5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('49ce88ee-7e8c-48f0-b27a-c0ed4782ea6f',	'661ec707-d1d5-4a33-bdad-e57fc207f9d5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('eed5425d-3573-4f2f-a0cc-67be54562e01',	'2520329c-cfae-4508-b989-4d675272febe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2af24be3-c71d-41df-9101-fef22ee69124',	'2520329c-cfae-4508-b989-4d675272febe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('5affe7a3-3b6b-4b15-a027-9644de0319bf',	'50e9690b-79dc-4c67-8008-71c0abfdcde2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('95df57b6-28dc-449a-96be-26e85c27065d',	'50e9690b-79dc-4c67-8008-71c0abfdcde2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('3ba54e16-7c8f-4dc6-822f-2010357e1c0a',	'4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4cc3c783-f615-4589-b281-f3c003708809',	'4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4bfd300f-fdc0-4f7e-978e-db76f5902f1a',	'dde8f4f6-bbc4-4e19-aa0d-99111cc544c0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('70d35e2d-d3b0-4092-bb7a-dea833a1bc2a',	'dde8f4f6-bbc4-4e19-aa0d-99111cc544c0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('aba5dc04-c83e-4af4-b8fe-5bb897a39d57',	'716142d8-d8a3-4206-853b-7f27f96e7623',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9a7840d8-842e-4898-bc22-8053fa1610bc',	'716142d8-d8a3-4206-853b-7f27f96e7623',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('db1bd489-700c-4050-8e57-91531db92d50',	'c87fee4b-b1ee-47a8-9003-96923fcead27',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d960f33b-42a8-427a-974a-7b2f35799a63',	'c87fee4b-b1ee-47a8-9003-96923fcead27',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c3001697-b8da-485c-ba46-a0542030848d',	'6b0735d2-6671-4457-b190-d5f06a564e8d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6fc9f46f-8140-48a4-91e1-34160c381b6f',	'6b0735d2-6671-4457-b190-d5f06a564e8d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0d0f1ce7-91bf-4b6b-878e-2bf4d41133e3',	'66ca988f-16a5-432a-8d3f-413684dee734',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('987e65bb-7a44-4cc1-a0fc-a3e21a199b05',	'66ca988f-16a5-432a-8d3f-413684dee734',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6e38f5f9-01c9-47b3-bbbc-87f48000a461',	'fcedaa98-6973-4c2f-a1b2-c239491e6658',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('c14dfaf4-2da9-4006-b398-506c7bd655cb',	'fcedaa98-6973-4c2f-a1b2-c239491e6658',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('957a686e-b38a-44a1-bf3d-4e91e70b47c3',	'86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('680af315-0d71-4b79-a35d-20681a81a03b',	'86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('4df52b17-f2e7-46d0-9c82-e3a684f6ead7',	'01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0a2a4c44-734e-4b7c-b828-1a4ea6539924',	'01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9f462c76-6520-4ece-b7a1-0296d00502ba',	'59e4ed30-c29b-4bcf-afc6-5a6b017e2f0c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('846306f6-7f55-45af-999b-a992fd3f4631',	'59e4ed30-c29b-4bcf-afc6-5a6b017e2f0c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('ef139c1f-b89b-4864-adca-1119cd935ef9',	'52ce20ea-7a18-41c0-a1fb-b75c9d05e398',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9ac104d8-cb84-417c-9963-bfe9adaae8ee',	'52ce20ea-7a18-41c0-a1fb-b75c9d05e398',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('6778543a-ecb5-4a67-a898-ee3d37551698',	'cc350737-de7b-4dfe-a3ca-e1d34a203541',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('f571254c-949d-4c29-95aa-eab8298641bb',	'cc350737-de7b-4dfe-a3ca-e1d34a203541',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('917350ee-5b14-45fc-99ce-9e2e7560e61b',	'2fb8d0a2-9018-4c87-9cb6-8532626a588c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('1f432bf0-0e99-42b7-9d9c-c8e0bf95bb84',	'2fb8d0a2-9018-4c87-9cb6-8532626a588c',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('9aea98a7-78f0-4438-8580-06ad23a552a9',	'733a1265-faab-4b2a-8ed1-124856124f5a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('b26353dd-4496-4ce8-b105-d2018d941971',	'733a1265-faab-4b2a-8ed1-124856124f5a',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('29e7ae48-4d46-499e-ba84-7dc0838263eb',	'3e2c1e69-0ffc-493f-92a7-e37e3dee3e12',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('0eb9f058-3a46-4b4f-a065-f78c51b7a9c6',	'3e2c1e69-0ffc-493f-92a7-e37e3dee3e12',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d2c8781e-085c-48e1-aa26-dfdd98eb800e',	'1b7deb00-7ddd-4a7e-8aa9-23125db6e320',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('2aaf5420-0158-4e6e-acb4-65180a23d70d',	'1b7deb00-7ddd-4a7e-8aa9-23125db6e320',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	NULL,	'f',	NULL,	'services',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

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

INSERT INTO "menu_item_variation" ("menu_item_variation_id", "menu_item_id", "restaurant_id", "variation_group_id", "menu_item_variation_name", "menu_item_variation_price", "menu_item_variation_markup_price", "menu_item_variation_status", "menu_item_variation_rank", "menu_item_variation_allow_addon", "menu_item_variation_packaging_charges", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_variation_id") VALUES
('a8e7c72b-4926-4129-abb3-85404f507832',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'2 Pieces',	300.00,	NULL,	'active',	1,	't',	30.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12237),
('d0c878e7-1c9e-4c07-9b30-fe65c80df0b3',	'37383633-9aa4-4bbd-b60e-37098f98b8fd',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	600.00,	NULL,	'active',	5,	't',	20.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('74a99dc9-416f-4d01-94c4-2ac1986f2b7b',	'eef9b0b6-fad0-4b33-9566-05ac24c46f92',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	139.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('273963a3-e6e8-4542-9947-76b5fe4fed9e',	'eef9b0b6-fad0-4b33-9566-05ac24c46f92',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	159.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('ffda4f43-c6bd-4843-baf4-786e9e82979b',	'8d9d66b3-7e6e-4c9e-9481-f71054454878',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'3 Pieces',	359.00,	NULL,	'active',	4,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12240),
('02587cc7-0f37-4068-a06f-695f1ef61566',	'8d9d66b3-7e6e-4c9e-9481-f71054454878',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	699.00,	NULL,	'active',	5,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('a3284925-426e-4a9c-a76d-0a671b514f15',	'e74ee574-fdf1-440d-afb7-6958fe388f22',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	149.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('6c74e7af-0f2f-4266-8bee-2f79fe29e61d',	'e74ee574-fdf1-440d-afb7-6958fe388f22',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	169.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('20d04a79-922d-4a1c-8860-0d098425fea4',	'2b50afaa-e73c-4e86-93f7-4bf06abc6d0d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	149.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('25e88bfc-224a-4415-8be1-1e71dd720ce4',	'2b50afaa-e73c-4e86-93f7-4bf06abc6d0d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	169.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('0319c264-e645-4631-8bd6-4c9df01a1faa',	'd47ae63a-ad96-4311-9e1d-fff7e6df18a9',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	159.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('89191987-4f37-4c65-8f29-da9d445257bd',	'd47ae63a-ad96-4311-9e1d-fff7e6df18a9',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	179.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('25fb76d1-f9ef-4008-98d9-81b2e4d45285',	'6fd61c08-24c3-4f88-a59e-2423a6be6619',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	169.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('d99ba16d-5cdf-4c86-bf0a-8b52cf7296d4',	'6fd61c08-24c3-4f88-a59e-2423a6be6619',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	189.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('70811254-c241-4590-aa33-2ca712b2be12',	'0db147db-79bd-4943-81a8-62a2257af888',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	149.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('806439d9-d909-4b63-919a-4928bcfccb89',	'0db147db-79bd-4943-81a8-62a2257af888',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	169.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('29759346-c6c9-4a05-97cb-9a9580d12854',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	40.00,	NULL,	'active',	7,	't',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('1fb84aff-e670-4d05-aebd-ce40895f284b',	'4752e0dd-4b55-4941-a41e-e919b8930321',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	45.00,	NULL,	'active',	8,	't',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('b9560b82-d4df-4c91-aba0-ec9e27c02a20',	'd20dfcb6-ec10-41a2-a255-df4380f264e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Small',	139.00,	NULL,	'active',	7,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12243),
('2498560d-d340-4c72-90f4-1c4778aad299',	'd20dfcb6-ec10-41a2-a255-df4380f264e3',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'd8187f2f-1671-472a-99eb-7a1ca2c319af',	'Large',	159.00,	NULL,	'active',	8,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12244),
('d4322f3c-edff-4b7e-8a20-90a09a7ed833',	'e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'2 Pieces',	239.00,	NULL,	'active',	1,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12237),
('4474b665-a54b-459c-904b-e0a880a8a418',	'e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'4 Pieces',	439.00,	NULL,	'active',	2,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12238),
('06aa62ce-d017-4fa8-810e-4d4d3e6f1bdd',	'e22459ed-2160-4641-87e7-2a4684604495',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	799.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('025f2ca1-55a5-4b1f-8986-7c8d11f30f91',	'0b4f1a68-a7ca-4ce1-ad83-ab06f4fc9baf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	409.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('ced41251-aa89-4a9e-a9ea-0b1c8eb3523e',	'0b4f1a68-a7ca-4ce1-ad83-ab06f4fc9baf',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	469.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('ccd63c6b-37fc-4e72-a964-ffba8dc194ee',	'076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	349.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('30aa4f52-deaf-4c54-9bcb-a70400b7e5a7',	'076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	299.00,	NULL,	'active',	5,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('bdf0641a-676a-4b0a-b6c9-df6549a29249',	'076c8ac7-08ca-4171-9120-70e5c3a186e8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	399.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('b1086003-5ede-49b9-8f89-6abf8a83d5ac',	'b24d4fee-15a3-4905-841d-1f91304a16aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	399.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('decf35b0-ee53-4c79-bc7c-a2b56e1a6a53',	'b24d4fee-15a3-4905-841d-1f91304a16aa',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	459.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('a9445b3d-de9f-482b-a279-0c79d9491015',	'5fa2b9f6-cad8-40ed-a0e8-ad16c0e71c41',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	419.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('855f37bd-f2fc-4d4d-ac75-08f7eefb1212',	'5fa2b9f6-cad8-40ed-a0e8-ad16c0e71c41',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	479.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('8eac2aef-90fb-49be-8ca0-d1c94298c48a',	'661ec707-d1d5-4a33-bdad-e57fc207f9d5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'3 Pieces',	359.00,	NULL,	'active',	4,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12240),
('17e9c5c1-7210-4018-a0e0-27ed2d7e9ed8',	'661ec707-d1d5-4a33-bdad-e57fc207f9d5',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	699.00,	NULL,	'active',	5,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('906377f0-a50b-49f0-9540-457c0f7e78d6',	'2520329c-cfae-4508-b989-4d675272febe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'3 Pieces',	269.00,	NULL,	'active',	4,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12240),
('7e1de46d-b4e5-4221-b02b-2e5088ba8b89',	'2520329c-cfae-4508-b989-4d675272febe',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	499.00,	NULL,	'active',	5,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('46556103-2670-4a5e-b830-572f2a781cfc',	'50e9690b-79dc-4c67-8008-71c0abfdcde2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'3 Pieces',	269.00,	NULL,	'active',	4,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12240),
('679f5cfe-b0ee-47cc-8008-dd14b6b95b06',	'50e9690b-79dc-4c67-8008-71c0abfdcde2',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'6 Pieces',	499.00,	NULL,	'active',	5,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12241),
('4779be42-3e6e-4af6-8813-bd466cb08ffb',	'4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'2 Pieces',	239.00,	NULL,	'active',	1,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12237),
('0529e386-174f-4dfd-bd0f-4c6b090574f2',	'4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'4 Pieces',	439.00,	NULL,	'active',	2,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12238),
('0db5d2d6-ca7f-42f0-afd5-49af5fd067c1',	'4eb90f2f-2971-4396-81c9-0a28eb5e2ceb',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	799.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('271746cb-44b3-4fb1-8325-c75fc4bc1fcc',	'dde8f4f6-bbc4-4e19-aa0d-99111cc544c0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	419.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('4f3d78f5-751b-40e5-92dc-6ee7615e10d3',	'dde8f4f6-bbc4-4e19-aa0d-99111cc544c0',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	479.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('8370af0c-e1af-47a5-bebe-17abd99923d1',	'716142d8-d8a3-4206-853b-7f27f96e7623',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	399.00,	NULL,	'active',	3,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('778511f2-d751-4755-b66f-818dd73dbb93',	'716142d8-d8a3-4206-853b-7f27f96e7623',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'10 Pieces',	459.00,	NULL,	'active',	6,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12242),
('d0ede37c-cd3e-4000-bb61-2c412a8b7efc',	'66ca988f-16a5-432a-8d3f-413684dee734',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'8 Pieces',	725.00,	NULL,	'active',	3,	't',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12239),
('f84b90a7-ff4f-4a07-b2dc-99ecd3f6820b',	'fcedaa98-6973-4c2f-a1b2-c239491e6658',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'2 Pieces',	200.00,	NULL,	'active',	1,	't',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12237),
('8d1bfe5f-1131-4cf3-9794-7aaa6fef98fb',	'86c22cfb-e115-4a8e-a73d-3fbea4251ca8',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'23dae662-f7d4-4f38-b6c2-edf47240404d',	'Chicken',	70.00,	NULL,	'active',	12,	't',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12248),
('229b9c09-a635-4483-9a21-2666775019ff',	'01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'250 Gm',	50.00,	NULL,	'active',	9,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12245),
('1a42bc16-b670-4860-a784-16c7fb378928',	'01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'500 Gm',	100.00,	NULL,	'active',	10,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12246),
('4cd72bbf-89d2-4a39-a077-e3103105178e',	'01d009b3-8700-4889-b89f-9f30d96a8833',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'a39329b4-1738-4a82-b12e-212c7d1bb694',	'1 Kg',	200.00,	NULL,	'active',	11,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12247),
('82e12928-f202-486a-810d-53cb62443b22',	'52ce20ea-7a18-41c0-a1fb-b75c9d05e398',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'23dae662-f7d4-4f38-b6c2-edf47240404d',	'Chicken',	70.00,	NULL,	'active',	12,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12248),
('aaa2be6c-aee9-413a-a4bb-aec667dbc21e',	'cc350737-de7b-4dfe-a3ca-e1d34a203541',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'23dae662-f7d4-4f38-b6c2-edf47240404d',	'Chicken',	65.00,	NULL,	'active',	12,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12248),
('78e48177-42c8-4865-9957-b225bd25424f',	'3e2c1e69-0ffc-493f-92a7-e37e3dee3e12',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'23dae662-f7d4-4f38-b6c2-edf47240404d',	'Chicken',	100.00,	NULL,	'active',	12,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12248),
('85ddf7b2-2324-4d23-9788-7eaafb07af9f',	'1b7deb00-7ddd-4a7e-8aa9-23125db6e320',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'23dae662-f7d4-4f38-b6c2-edf47240404d',	'Chicken',	50.00,	NULL,	'active',	12,	'f',	0.00,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	12248);

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

INSERT INTO "menu_sections" ("menu_section_id", "restaurant_id", "menu_section_status", "menu_section_name", "menu_section_description", "menu_section_image_url", "menu_section_rank", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_parent_categories_id") VALUES
('cc055fa1-4b1e-4bae-9e8e-54a41a2b3d67',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	'Parent',	NULL,	NULL,	1,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	722),
('b5443602-58ed-42a5-a3d9-52b1d47f2453',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	'Tandoori',	NULL,	'',	2,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	734),
('ac97a61c-e60b-4ec9-98bd-395d05f08364',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	'Breakfast',	NULL,	'',	3,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	735),
('2c0f8031-a7e8-458e-8e49-4deb95a498e4',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'active',	'Combos',	NULL,	'',	4,	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	736);

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

INSERT INTO "menu_sub_categories" ("menu_sub_category_id", "restaurant_id", "category_id", "sub_category_status", "sub_category_rank", "sub_category_name", "sub_category_description", "sub_category_timings", "sub_category_image_url", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted", "ext_petpooja_categories_id", "menu_section_id") VALUES
('52d100cc-4cce-4124-aa64-8cb0e7e9e787',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'1f8881cd-3e2f-484d-9ae4-2f3376c40907',	'active',	1,	'Chicken',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80728,	'cc055fa1-4b1e-4bae-9e8e-54a41a2b3d67'),
('8664f6d0-fb7b-4eb0-85b1-c810290302bc',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'1f8881cd-3e2f-484d-9ae4-2f3376c40907',	'active',	1,	'Chicken Meal',	NULL,	'',	'https://online-logo-staging.s3.ap-southeast-1.amazonaws.com/category_logo/4878/thumb_2025_09_19_18_04_50_Chicken_Tikka_Combo.jpg?X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA263UXGOMJKV7JGOO%2F20251219%2Fap-southeast-1%2Fs3%2Faws4_request&X-Amz-Date=20251219T112824Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Signature=8a9114801e0eb435d2625e2ec8009632f41ef7c43c0ae0d80a6e554a55b73898',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80721,	'cc055fa1-4b1e-4bae-9e8e-54a41a2b3d67'),
('95206d03-5227-4913-a100-29fbdda4031f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'06a09633-b820-4dbf-960f-6ebd2141aec1',	'active',	1,	'Beverages',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80724,	'b5443602-58ed-42a5-a3d9-52b1d47f2453'),
('ed759647-26b7-4b52-85ca-29c66310159e',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'1f8881cd-3e2f-484d-9ae4-2f3376c40907',	'active',	1,	'Seafood Meal',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80722,	'b5443602-58ed-42a5-a3d9-52b1d47f2453'),
('03b2f2fe-d114-4ed9-985e-2f82a3715669',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'aa6ce4eb-6317-42f6-b3b2-d2769adeac36',	'active',	1,	'Side Orders',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80723,	'b5443602-58ed-42a5-a3d9-52b1d47f2453'),
('d6524dcd-3279-4a31-aa7c-dd42024e4906',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'aa6ce4eb-6317-42f6-b3b2-d2769adeac36',	'active',	1,	'Add Ons',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80726,	'ac97a61c-e60b-4ec9-98bd-395d05f08364'),
('59887de6-a3bf-4bf9-ac00-bc6089fff3ee',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'06a09633-b820-4dbf-960f-6ebd2141aec1',	'active',	1,	'Desserts',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80727,	'ac97a61c-e60b-4ec9-98bd-395d05f08364'),
('c1a71129-8263-44c3-b1f0-c602a5bd564f',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'06a09633-b820-4dbf-960f-6ebd2141aec1',	'active',	1,	'Hot Coffees',	NULL,	'',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	80725,	'ac97a61c-e60b-4ec9-98bd-395d05f08364'),
('e1639f72-fca0-43f9-b1fe-9193cb5c970e',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'994cba8a-76ea-4c57-8d07-275acfd0f307',	'active',	2,	'Group1',	NULL,	'[{"schedule_name":"Group1Schedule","schedule_day":"All","schedule_time_slots":[{"start_time":"07:00","end_time":"07:30"},{"start_time":"11:30","end_time":"12:00"}]}]',	'',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f',	81155,	'2c0f8031-a7e8-458e-8e49-4deb95a498e4');

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

INSERT INTO "variation_groups" ("variation_group_id", "restaurant_id", "variation_group_name", "variation_group_selection_type", "variation_group_min_selection", "variation_group_max_selection", "variation_group_status", "created_at", "updated_at", "created_by", "updated_by", "deleted_at", "is_deleted") VALUES
('a39329b4-1738-4a82-b12e-212c7d1bb694',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Quantity',	NULL,	NULL,	NULL,	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('d8187f2f-1671-472a-99eb-7a1ca2c319af',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Portion',	NULL,	NULL,	NULL,	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f'),
('23dae662-f7d4-4f38-b6c2-edf47240404d',	'58d98970-fe89-406a-a0fd-94581cb5a94c',	'Size',	NULL,	NULL,	NULL,	'active',	'2025-12-19 16:59:53.542163+05:30',	'2025-12-19 16:59:53.542163+05:30',	NULL,	NULL,	NULL,	'f');

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
