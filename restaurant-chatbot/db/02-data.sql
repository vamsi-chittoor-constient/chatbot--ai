--
-- PostgreSQL database dump
--

\restrict QmurM6u0XzoY6jgF9TSr1qVg3Gzr7cZ6UEJNouSvHD6AHmtAk7MQUhx9X7GoDEo

-- Dumped from database version 18.1 (Ubuntu 18.1-1.pgdg24.04+2)
-- Dumped by pg_dump version 18.1 (Ubuntu 18.1-1.pgdg24.04+2)

-- Started on 2025-11-27 06:22:45 IST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
-- SET transaction_timeout = 0;  -- Removed for PG15 compatibility
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS "A24_restaurant_dev";
--
-- TOC entry 5506 (class 1262 OID 18576)
-- Name: A24_restaurant_dev; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "A24_restaurant_dev" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.UTF-8';


\unrestrict QmurM6u0XzoY6jgF9TSr1qVg3Gzr7cZ6UEJNouSvHD6AHmtAk7MQUhx9X7GoDEo
\connect "A24_restaurant_dev"
\restrict QmurM6u0XzoY6jgF9TSr1qVg3Gzr7cZ6UEJNouSvHD6AHmtAk7MQUhx9X7GoDEo

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
-- SET transaction_timeout = 0;  -- Removed for PG15 compatibility
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 18580)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 5507 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 18591)
-- Name: account_lock; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_lock (
    account_lock_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    account_lock_at timestamp with time zone,
    account_lock_until timestamp with time zone,
    account_lock_reason text,
    account_lock_failed_attempts integer,
    account_lock_unlocked_at timestamp with time zone,
    account_lock_unlocked_by uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 221 (class 1259 OID 18603)
-- Name: allergens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.allergens (
    allergen_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    allergen_name character varying(255) NOT NULL,
    allergen_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 222 (class 1259 OID 18616)
-- Name: branch_contact_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branch_contact_table (
    branch_contact_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    branch_id uuid,
    contact_type character varying(255),
    contact_value character varying(255),
    is_primary boolean DEFAULT false,
    contact_label character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 223 (class 1259 OID 18629)
-- Name: branch_info_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branch_info_table (
    branch_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chain_id uuid,
    branch_name character varying(255) NOT NULL,
    branch_website_url text,
    branch_logo_url text,
    branch_personalized_greeting text,
    order_type character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 224 (class 1259 OID 18642)
-- Name: branch_location_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branch_location_table (
    branch_location_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    branch_id uuid,
    address_line text,
    landmark text,
    pincode_id uuid,
    latitude numeric(10,8),
    longitude numeric(11,8),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 225 (class 1259 OID 18654)
-- Name: branch_timing_policy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branch_timing_policy (
    branch_timing_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    opening_time time without time zone,
    closing_time time without time zone,
    food_ordering_start_time time without time zone,
    food_ordering_closing_time time without time zone,
    table_booking_open_time time without time zone,
    table_booking_close_time time without time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 226 (class 1259 OID 18664)
-- Name: chain_contact_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chain_contact_table (
    chain_contact_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chain_id uuid,
    contact_type character varying(255),
    contact_value character varying(255),
    is_primary boolean DEFAULT false,
    contact_label text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 227 (class 1259 OID 18677)
-- Name: chain_info_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chain_info_table (
    chain_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chain_name character varying(255) NOT NULL,
    chain_website_url text,
    chain_logo_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 228 (class 1259 OID 18690)
-- Name: chain_location_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chain_location_table (
    chain_location_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chain_id uuid,
    address_line text,
    landmark text,
    pincode_id uuid,
    latitude numeric(10,8),
    longitude numeric(11,8),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 229 (class 1259 OID 18702)
-- Name: city_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.city_table (
    city_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    city_name character varying(255) NOT NULL,
    state_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 230 (class 1259 OID 18713)
-- Name: combo_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.combo_item (
    combo_item_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    combo_item_component_id uuid,
    restaurant_id uuid,
    combo_type character varying(255),
    is_available boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 231 (class 1259 OID 18724)
-- Name: combo_item_components; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.combo_item_components (
    combo_item_component_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    combo_item_id uuid,
    menu_item_id uuid,
    quantity integer DEFAULT 1,
    is_optional boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 232 (class 1259 OID 18736)
-- Name: country_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_table (
    country_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    country_name character varying(255) NOT NULL,
    iso_code character varying(8),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 233 (class 1259 OID 18748)
-- Name: cuisines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuisines (
    cuisine_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    cuisine_name character varying(255),
    cuisine_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 234 (class 1259 OID 18758)
-- Name: customer_activity_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_activity_log (
    log_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    activity_type character varying(255),
    activity_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address character varying(255),
    user_agent character varying(255),
    details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 235 (class 1259 OID 18771)
-- Name: customer_address_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_address_table (
    customer_address_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    customer_address_type character varying(255),
    customer_address_label character varying(255),
    customer_street_address_1 text,
    customer_street_address_2 text,
    customer_city text,
    customer_state_province text,
    customer_postal_code text,
    customer_country text,
    customer_latitude numeric(10,8),
    customer_longitude numeric(11,8),
    customer_is_default boolean DEFAULT false,
    customer_delivery_instructions text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 236 (class 1259 OID 18784)
-- Name: customer_allergens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_allergens (
    customer_id uuid NOT NULL,
    allergen_id uuid NOT NULL,
    customer_allergen_severity character varying(255),
    customer_allergen_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 237 (class 1259 OID 18796)
-- Name: customer_authentication; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_authentication (
    auth_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    auth_method character varying(255),
    auth_provider character varying(255),
    password_hash text,
    last_login timestamp with time zone,
    failed_attempts integer DEFAULT 0,
    locked_until timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 238 (class 1259 OID 18809)
-- Name: customer_consent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_consent (
    consent_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    consent_type character varying(255),
    consent_given boolean DEFAULT true,
    consent_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    consent_withdrawn_at timestamp with time zone,
    consent_method character varying(255),
    ip_address character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 239 (class 1259 OID 18823)
-- Name: customer_contact_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_contact_table (
    contact_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    customer_contact_type character varying(255),
    customer_contact_value character varying(255),
    customer_is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 240 (class 1259 OID 18836)
-- Name: customer_devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_devices (
    device_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    device_type character varying(255),
    device_name character varying(255),
    os character varying(255),
    browser character varying(255),
    first_seen timestamp with time zone,
    last_seen timestamp with time zone,
    is_trusted boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 241 (class 1259 OID 18849)
-- Name: customer_dietary_restrictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_dietary_restrictions (
    customer_id uuid NOT NULL,
    dietary_restriction_id uuid NOT NULL,
    customer_dietary_restriction_severity character varying(255),
    customer_dietary_restriction_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 242 (class 1259 OID 18861)
-- Name: customer_favorite_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_favorite_items (
    favorite_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    menu_item_id uuid,
    added_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 243 (class 1259 OID 18872)
-- Name: customer_gender; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_gender (
    customer_gender_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_gender_name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 244 (class 1259 OID 18883)
-- Name: customer_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_preferences (
    customer_preference_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 245 (class 1259 OID 18893)
-- Name: customer_profile_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_profile_table (
    customer_id uuid NOT NULL,
    customer_first_name character varying(255),
    customer_last_name character varying(255),
    customer_display_name character varying(255),
    customer_date_of_birth date,
    customer_gender_id uuid,
    language_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 246 (class 1259 OID 18904)
-- Name: customer_search_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_search_queries (
    query_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    conversation_id uuid,
    search_query text,
    search_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 247 (class 1259 OID 18917)
-- Name: customer_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_sessions (
    session_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    session_token text,
    expires_at timestamp with time zone,
    ip_address character varying(255),
    user_agent character varying(255),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 248 (class 1259 OID 18930)
-- Name: customer_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_table (
    customer_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_account_status character varying(20),
    customer_type character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 249 (class 1259 OID 18940)
-- Name: customer_tag_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_tag_mapping (
    customer_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    tagged_by uuid,
    tagged_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 250 (class 1259 OID 18951)
-- Name: customer_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_tags (
    tag_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tag_name character varying(255) NOT NULL,
    tag_category character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 251 (class 1259 OID 18964)
-- Name: department; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.department (
    department_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    department_name character varying(255),
    department_unique_code character varying(20),
    department_description text,
    parent_department_id uuid,
    department_manager_id uuid,
    department_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 252 (class 1259 OID 18976)
-- Name: dietary_restrictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dietary_restrictions (
    dietary_restriction_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    dietary_restriction_name character varying(255) NOT NULL,
    dietary_restriction_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 253 (class 1259 OID 18989)
-- Name: dietary_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dietary_types (
    dietary_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    dietary_type_name character varying(255),
    dietary_type_label character varying(255),
    dietary_type_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 254 (class 1259 OID 19001)
-- Name: discount; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discount (
    discount_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    discount_name character varying(255),
    discount_description text,
    discount_type character varying(20),
    discount_value numeric(10,2),
    discount_ordertype character varying(20),
    discount_applicable_on text,
    discount_days text,
    discount_status character varying(20),
    discount_rank integer,
    discount_on_total boolean DEFAULT false,
    discount_starts_at timestamp with time zone,
    discount_time_from time without time zone,
    discount_time_to time without time zone,
    discount_min_amount numeric(10,2),
    discount_max_amount numeric(10,2),
    discount_has_coupon boolean DEFAULT false,
    discount_max_limit integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 255 (class 1259 OID 19015)
-- Name: discount_schedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discount_schedule (
    discount_schedule_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    discount_id uuid,
    discount_schedule_day_of_week integer,
    discount_schedule_start_time time without time zone,
    discount_schedule_end_time time without time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 256 (class 1259 OID 19025)
-- Name: discount_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discount_type (
    discount_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    discount_type_code character varying(20),
    discount_type_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 257 (class 1259 OID 19035)
-- Name: email_verification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_verification (
    email_verification_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    email_verification_email character varying(255),
    email_verification_otp character varying(255),
    email_verification_expires_at timestamp with time zone,
    email_verification_verified_at timestamp with time zone,
    email_verification_attempts integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 258 (class 1259 OID 19048)
-- Name: entity_slot_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_slot_config (
    slot_config_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    slot_capacity integer,
    slot_duration integer,
    slot_frequency integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 259 (class 1259 OID 19058)
-- Name: feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback (
    feedback_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    is_anonymous boolean DEFAULT false,
    contact_email character varying(255),
    order_id uuid,
    booking_id uuid,
    product_id uuid,
    service_id uuid,
    title character varying(255),
    feedback_text text NOT NULL,
    rating integer,
    category_id uuid,
    feedback_type_id uuid,
    sentiment text,
    priority_id uuid,
    status_id uuid,
    assigned_to uuid,
    assigned_at timestamp with time zone,
    platform_id uuid,
    device_info character varying(255),
    ip_address character varying(255),
    user_agent character varying(255),
    page_url text,
    is_urgent boolean DEFAULT false,
    is_featured boolean DEFAULT false,
    requires_followup boolean DEFAULT false,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false,
    CONSTRAINT feedback_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


--
-- TOC entry 260 (class 1259 OID 19077)
-- Name: feedback_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_attachments (
    attachment_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    feedback_id uuid,
    file_name character varying(255) NOT NULL,
    file_path text NOT NULL,
    file_type character varying(20),
    file_size bigint,
    uploaded_by uuid,
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 261 (class 1259 OID 19092)
-- Name: feedback_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_categories (
    category_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    category_name character varying(255) NOT NULL,
    description text,
    icon text,
    display_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    parent_category_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 262 (class 1259 OID 19108)
-- Name: feedback_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_notifications (
    notification_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    feedback_id uuid,
    recipient_email character varying(255) NOT NULL,
    notification_type character varying(20),
    subject text,
    sent_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    opened_at timestamp with time zone,
    clicked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 263 (class 1259 OID 19122)
-- Name: feedback_platforms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_platforms (
    platform_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    platform_name character varying(255) NOT NULL,
    platform_type character varying(20),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 264 (class 1259 OID 19135)
-- Name: feedback_priorities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_priorities (
    priority_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    priority_name character varying(255) NOT NULL,
    priority_level integer,
    color_code character varying(20),
    response_sla_hours integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 265 (class 1259 OID 19147)
-- Name: feedback_priority_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_priority_history (
    history_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    feedback_id uuid,
    old_priority_id uuid,
    new_priority_id uuid,
    changed_by uuid,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    change_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 266 (class 1259 OID 19160)
-- Name: feedback_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_responses (
    response_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    feedback_id uuid,
    responded_by uuid,
    response_text text NOT NULL,
    is_internal boolean DEFAULT false,
    is_automated boolean DEFAULT false,
    is_public boolean DEFAULT false,
    response_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    edited_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 267 (class 1259 OID 19177)
-- Name: feedback_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_status_history (
    history_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    feedback_id uuid,
    old_status_id uuid,
    new_status_id uuid,
    changed_by uuid,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    change_reason text,
    is_automated boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 268 (class 1259 OID 19191)
-- Name: feedback_statuses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_statuses (
    status_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    status_name character varying(255) NOT NULL,
    description text,
    color_code character varying(255),
    is_initial boolean DEFAULT false,
    is_final boolean DEFAULT false,
    display_order integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 269 (class 1259 OID 19208)
-- Name: feedback_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_tags (
    feedback_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    added_by uuid,
    added_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 270 (class 1259 OID 19219)
-- Name: feedback_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_types (
    type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    type_name character varying(255) NOT NULL,
    description text,
    color_code character varying(20),
    icon text,
    requires_response boolean DEFAULT true,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 271 (class 1259 OID 19235)
-- Name: integration_config_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integration_config_table (
    integration_config_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chain_id uuid,
    branch_id uuid,
    provider_id uuid,
    is_enabled boolean DEFAULT false,
    api_key text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false,
    CONSTRAINT integration_config_table_check CHECK ((((chain_id IS NOT NULL) AND (branch_id IS NULL)) OR ((chain_id IS NULL) AND (branch_id IS NOT NULL))))
);


--
-- TOC entry 272 (class 1259 OID 19249)
-- Name: integration_credentials_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integration_credentials_table (
    credential_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    integration_config_id uuid,
    credential_key character varying(255),
    credential_value text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 273 (class 1259 OID 19261)
-- Name: integration_metadata_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integration_metadata_table (
    metadata_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    integration_config_id uuid,
    metadata_key character varying(255),
    metadata_value text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 274 (class 1259 OID 19273)
-- Name: integration_provider_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integration_provider_table (
    provider_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    provider_name character varying(255) NOT NULL,
    provider_description text,
    provider_base_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 275 (class 1259 OID 19286)
-- Name: languages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.languages (
    language_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    language_iso character varying(10) NOT NULL,
    language_name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 276 (class 1259 OID 19298)
-- Name: login_attempt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_attempt (
    login_attempt_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    login_attempt_email character varying(255),
    login_attempt_success boolean DEFAULT false,
    login_attempt_ip_address character varying(255),
    login_attempt_user_agent character varying(255),
    login_attempt_failure_reason text,
    login_attempt_attempted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 277 (class 1259 OID 19312)
-- Name: loyalty_transaction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.loyalty_transaction (
    loyalty_txn_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    customer_id uuid,
    order_id uuid,
    payment_transaction_id uuid,
    points_used integer DEFAULT 0,
    points_earned integer DEFAULT 0,
    points_balance_after integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 278 (class 1259 OID 19325)
-- Name: meal_slot_timing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meal_slot_timing (
    meal_slot_timing_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    slot_config_id uuid,
    meal_type_id uuid,
    opening_time time without time zone,
    closing_time time without time zone,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 279 (class 1259 OID 19336)
-- Name: meal_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meal_type (
    meal_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    meal_type_name character varying(255),
    display_order integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 280 (class 1259 OID 19346)
-- Name: menu_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_categories (
    menu_category_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_section_id uuid,
    menu_category_status character varying(20),
    menu_category_rank integer,
    menu_category_name character varying(255),
    menu_category_description text,
    menu_category_timings text,
    menu_category_image_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 5508 (class 0 OID 0)
-- Dependencies: 280
-- Name: COLUMN menu_categories.menu_section_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.menu_categories.menu_section_id IS 'Links to dietary section (Veg/Non-Veg/Vegan). Category hierarchy: menu_sections → menu_categories → menu_sub_categories';


--
-- TOC entry 281 (class 1259 OID 19358)
-- Name: menu_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item (
    menu_item_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_sub_category_id uuid,
    menu_item_name character varying(255),
    menu_item_status character varying(20),
    menu_item_description text,
    menu_item_price numeric(12,2) DEFAULT '0'::numeric,
    menu_item_quantity integer DEFAULT 0,
    menu_item_allow_variation boolean DEFAULT false,
    menu_item_allow_addon boolean DEFAULT false,
    menu_item_minimum_preparation_time integer,
    menu_item_tax_id uuid,
    menu_item_tax_cgst numeric(8,2),
    menu_item_tax_sgst numeric(8,2),
    menu_item_timings text,
    menu_item_packaging_charges numeric(10,2) DEFAULT '0'::numeric,
    menu_item_attribute_id uuid,
    menu_item_rank integer,
    menu_item_favorite boolean DEFAULT false,
    menu_item_ignore_taxes boolean DEFAULT false,
    menu_item_ignore_discounts boolean DEFAULT false,
    menu_item_in_stock boolean DEFAULT true,
    menu_item_is_combo boolean DEFAULT false,
    menu_item_is_recommended boolean DEFAULT false,
    menu_item_spice_level character varying(50),
    menu_item_addon_based_on text,
    menu_item_markup_price numeric(12,2),
    menu_item_is_combo_parent boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false,
    menu_item_calories integer,
    menu_item_is_seasonal boolean DEFAULT false,
    menu_item_image_url character varying(500),
    menu_item_serving_unit character varying(20)
);


--
-- TOC entry 5509 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN menu_item.menu_sub_category_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.menu_item.menu_sub_category_id IS 'DEPRECATED: Use menu_item_category_mapping table instead. Kept for backward compatibility during migration. New code should NOT populate this field.';


--
-- TOC entry 366 (class 1259 OID 21492)
-- Name: menu_item_category_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_category_mapping (
    mapping_id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    menu_item_id uuid NOT NULL,
    menu_category_id uuid NOT NULL,
    menu_sub_category_id uuid,
    is_primary boolean DEFAULT false,
    display_rank integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 5510 (class 0 OID 0)
-- Dependencies: 366
-- Name: TABLE menu_item_category_mapping; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.menu_item_category_mapping IS 'Maps menu items to multiple categories/sub-categories. Enables filtering by category hierarchy and supports items in multiple categories.';


--
-- TOC entry 5511 (class 0 OID 0)
-- Dependencies: 366
-- Name: COLUMN menu_item_category_mapping.menu_sub_category_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.menu_item_category_mapping.menu_sub_category_id IS 'Links to sub-category if item belongs to one. NULL if item has < 10 siblings and links directly to parent category.';


--
-- TOC entry 5512 (class 0 OID 0)
-- Dependencies: 366
-- Name: COLUMN menu_item_category_mapping.is_primary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.menu_item_category_mapping.is_primary IS 'Indicates the primary category for this item. Each item should have exactly one primary category.';


--
-- TOC entry 296 (class 1259 OID 19529)
-- Name: menu_sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_sections (
    menu_section_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_section_status character varying(20),
    menu_section_name character varying(255),
    menu_section_description text,
    menu_section_image_url text,
    menu_section_rank integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 297 (class 1259 OID 19541)
-- Name: menu_sub_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_sub_categories (
    menu_sub_category_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    category_id uuid,
    sub_category_status character varying(20),
    sub_category_rank integer,
    sub_category_name character varying(255),
    sub_category_description text,
    sub_category_timings text,
    sub_category_image_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 371 (class 1259 OID 21664)
-- Name: menu_hierarchy_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.menu_hierarchy_view AS
 WITH category_counts AS (
         SELECT micm.menu_category_id,
            count(DISTINCT mi.menu_item_id) AS item_count
           FROM (public.menu_item_category_mapping micm
             JOIN public.menu_item mi ON ((micm.menu_item_id = mi.menu_item_id)))
          WHERE ((mi.is_deleted = false) AND (mi.menu_item_in_stock = true) AND (micm.is_deleted = false))
          GROUP BY micm.menu_category_id
        ), subcategory_counts AS (
         SELECT micm.menu_sub_category_id,
            count(DISTINCT mi.menu_item_id) AS item_count
           FROM (public.menu_item_category_mapping micm
             JOIN public.menu_item mi ON ((micm.menu_item_id = mi.menu_item_id)))
          WHERE ((mi.is_deleted = false) AND (mi.menu_item_in_stock = true) AND (micm.is_deleted = false) AND (micm.menu_sub_category_id IS NOT NULL))
          GROUP BY micm.menu_sub_category_id
        )
 SELECT ms.menu_section_id,
    ms.menu_section_name,
    ms.menu_section_description,
    ms.menu_section_rank,
    ms.restaurant_id AS section_restaurant_id,
    mc.menu_category_id,
    mc.menu_category_name,
    mc.menu_category_description,
    mc.menu_category_rank,
    msc.menu_sub_category_id,
    msc.sub_category_name,
    msc.sub_category_description,
    msc.sub_category_rank,
    COALESCE(cc.item_count, (0)::bigint) AS category_item_count,
    COALESCE(sc.item_count, (0)::bigint) AS subcategory_item_count
   FROM ((((public.menu_sections ms
     LEFT JOIN public.menu_categories mc ON (((ms.menu_section_id = mc.menu_section_id) AND (mc.is_deleted = false))))
     LEFT JOIN category_counts cc ON ((mc.menu_category_id = cc.menu_category_id)))
     LEFT JOIN public.menu_sub_categories msc ON (((mc.menu_category_id = msc.category_id) AND (msc.is_deleted = false))))
     LEFT JOIN subcategory_counts sc ON ((msc.menu_sub_category_id = sc.menu_sub_category_id)))
  WHERE (ms.is_deleted = false)
  ORDER BY ms.menu_section_rank, mc.menu_category_rank, msc.sub_category_rank;


--
-- TOC entry 282 (class 1259 OID 19382)
-- Name: menu_item_addon_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_addon_group (
    menu_item_addon_group_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_item_addon_group_name character varying(255),
    menu_item_addon_group_rank integer,
    menu_item_addon_group_status character varying(20),
    menu_item_addon_group_selection_min integer,
    menu_item_addon_group_selection_max integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 283 (class 1259 OID 19392)
-- Name: menu_item_addon_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_addon_item (
    menu_item_addon_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_addon_group_id uuid,
    restaurant_id uuid,
    menu_item_addon_item_name character varying(255),
    menu_item_addon_item_price numeric(10,2),
    menu_item_addon_item_status character varying(20),
    menu_item_addon_item_rank integer,
    menu_item_addon_item_attribute_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 284 (class 1259 OID 19402)
-- Name: menu_item_addon_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_addon_mapping (
    menu_item_addon_mapping_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    menu_item_variation_id uuid,
    menu_item_addon_group_id uuid,
    restaurant_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 368 (class 1259 OID 21592)
-- Name: menu_item_allergen_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_allergen_mapping (
    mapping_id uuid DEFAULT gen_random_uuid() NOT NULL,
    menu_item_id uuid NOT NULL,
    allergen_id uuid NOT NULL,
    restaurant_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 285 (class 1259 OID 19412)
-- Name: menu_item_attribute; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_attribute (
    menu_item_attribute_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_attribute_name character varying(255),
    menu_item_attribute_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 286 (class 1259 OID 19422)
-- Name: menu_item_availability_schedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_availability_schedule (
    schedule_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    day_of_week character varying(255),
    time_from time without time zone,
    time_to time without time zone,
    is_available boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false,
    meal_type_id uuid
);


--
-- TOC entry 5513 (class 0 OID 0)
-- Dependencies: 286
-- Name: COLUMN menu_item_availability_schedule.meal_type_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.menu_item_availability_schedule.meal_type_id IS 'Direct link to meal type (Breakfast/Lunch/Dinner/All Day). Simplifies meal timing queries.';


--
-- TOC entry 287 (class 1259 OID 19433)
-- Name: menu_item_cuisine_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_cuisine_mapping (
    menu_item_cuisine_mapping_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    cuisine_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 369 (class 1259 OID 21625)
-- Name: menu_item_dietary_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_dietary_mapping (
    mapping_id uuid DEFAULT gen_random_uuid() NOT NULL,
    menu_item_id uuid NOT NULL,
    dietary_type_id uuid NOT NULL,
    restaurant_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 288 (class 1259 OID 19443)
-- Name: menu_item_discount_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_discount_mapping (
    menu_item_discount_mapping_id uuid DEFAULT public.uuid_generate_v4() CONSTRAINT menu_item_discount_mapping_menu_item_discount_mapping__not_null NOT NULL,
    menu_item_id uuid,
    discount_id uuid,
    restaurant_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 367 (class 1259 OID 21564)
-- Name: menu_item_ingredient; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_ingredient (
    ingredient_id uuid DEFAULT gen_random_uuid() NOT NULL,
    menu_item_id uuid NOT NULL,
    restaurant_id uuid NOT NULL,
    ingredient_name character varying(200) NOT NULL,
    ingredient_quantity numeric(10,2),
    ingredient_unit character varying(50),
    ingredient_rank integer DEFAULT 0,
    is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 289 (class 1259 OID 19453)
-- Name: menu_item_option; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_option (
    menu_item_option_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    menu_item_option_name character varying(255),
    menu_item_option_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 290 (class 1259 OID 19465)
-- Name: menu_item_ordertype_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_ordertype_mapping (
    menu_item_ordertype_mapping_id uuid DEFAULT public.uuid_generate_v4() CONSTRAINT menu_item_ordertype_mapping_menu_item_ordertype_mappin_not_null NOT NULL,
    menu_item_id uuid,
    menu_item_ordertype_id uuid,
    restaurant_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 291 (class 1259 OID 19475)
-- Name: menu_item_tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_tag (
    menu_item_tag_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_tag_name character varying(255),
    menu_item_tag_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 292 (class 1259 OID 19485)
-- Name: menu_item_tag_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_tag_mapping (
    menu_item_tag_mapping_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    menu_item_tag_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 293 (class 1259 OID 19495)
-- Name: menu_item_tax_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_tax_mapping (
    menu_item_tax_mapping_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    restaurant_id uuid,
    tax_id uuid,
    is_tax_inclusive boolean DEFAULT false,
    gst_liability text,
    gst_type character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 294 (class 1259 OID 19508)
-- Name: menu_item_variation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_variation (
    menu_item_variation_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    menu_item_id uuid,
    restaurant_id uuid,
    variation_group_id uuid,
    menu_item_variation_name character varying(255),
    menu_item_variation_price numeric(12,2),
    menu_item_variation_markup_price numeric(12,2),
    menu_item_variation_status character varying(20),
    menu_item_variation_rank integer,
    menu_item_variation_allow_addon boolean DEFAULT false,
    menu_item_variation_packaging_charges numeric(10,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 295 (class 1259 OID 19519)
-- Name: menu_item_variation_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_variation_mapping (
    menu_item_variation_mapping_id uuid DEFAULT public.uuid_generate_v4() CONSTRAINT menu_item_variation_mapping_menu_item_variation_mappin_not_null NOT NULL,
    menu_item_id uuid,
    menu_item_variation_group_id uuid,
    menu_item_variation_rank integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 370 (class 1259 OID 21658)
-- Name: menu_items_enriched_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.menu_items_enriched_view AS
SELECT
    NULL::uuid AS menu_item_id,
    NULL::uuid AS restaurant_id,
    NULL::character varying(255) AS menu_item_name,
    NULL::text AS menu_item_description,
    NULL::numeric(12,2) AS menu_item_price,
    NULL::integer AS menu_item_quantity,
    NULL::character varying(20) AS menu_item_status,
    NULL::character varying(50) AS menu_item_spice_level,
    NULL::boolean AS menu_item_in_stock,
    NULL::boolean AS menu_item_is_recommended,
    NULL::boolean AS menu_item_favorite,
    NULL::integer AS menu_item_minimum_preparation_time,
    NULL::boolean AS menu_item_allow_variation,
    NULL::boolean AS menu_item_allow_addon,
    NULL::boolean AS menu_item_is_combo,
    NULL::boolean AS menu_item_is_combo_parent,
    NULL::integer AS menu_item_rank,
    NULL::integer AS menu_item_calories,
    NULL::boolean AS menu_item_is_seasonal,
    NULL::character varying(500) AS menu_item_image_url,
    NULL::character varying(20) AS menu_item_serving_unit,
    NULL::character varying(255) AS section,
    NULL::character varying[] AS categories,
    NULL::character varying[] AS subcategories,
    NULL::character varying[] AS cuisines,
    NULL::character varying[] AS meal_timings,
    NULL::character varying[] AS ingredients,
    NULL::character varying[] AS allergens,
    NULL::character varying[] AS dietary_types,
    NULL::timestamp with time zone AS created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::boolean AS is_deleted;


--
-- TOC entry 298 (class 1259 OID 19553)
-- Name: menu_sync_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_sync_log (
    menu_sync_log_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_sync_source text,
    menu_sync_status character varying(20),
    menu_sync_started_at timestamp with time zone,
    menu_sync_completed_at timestamp with time zone,
    menu_items_synced jsonb,
    menu_errors jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 299 (class 1259 OID 19565)
-- Name: menu_version_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_version_history (
    menu_version_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    menu_version_number integer,
    menu_version_changed_by uuid,
    menu_version_change_summary text,
    menu_version_snapshot_data jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 300 (class 1259 OID 19577)
-- Name: order_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_audit (
    order_audit_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    session_id uuid,
    order_version integer,
    modified_by uuid,
    modification_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 301 (class 1259 OID 19589)
-- Name: order_charges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_charges (
    order_charges_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    order_item_id uuid,
    order_charges_type character varying(20),
    order_charges_base_amount numeric(10,2),
    order_charges_taxable_amount numeric(10,2),
    order_charges_metadata_json jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 302 (class 1259 OID 19601)
-- Name: order_customer_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_customer_details (
    order_customer_details_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    customer_id uuid,
    restaurant_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 303 (class 1259 OID 19611)
-- Name: order_delivery_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_delivery_info (
    order_delivery_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    delivery_partner_id uuid,
    enable_delivery boolean DEFAULT false,
    delivery_type character varying(20),
    delivery_slot text,
    delivery_address_id uuid,
    delivery_distance_km numeric(10,2),
    delivery_estimated_time timestamp with time zone,
    delivery_actual_time timestamp with time zone,
    delivery_person_id uuid,
    delivery_started_at timestamp with time zone,
    delivery_completed_at timestamp with time zone,
    delivery_otp character varying(20),
    delivery_verification_method character varying(255),
    delivery_tracking_url text,
    delivery_proof_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 304 (class 1259 OID 19624)
-- Name: order_dining_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_dining_info (
    order_dining_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    table_id uuid,
    table_no integer,
    table_area character varying(255),
    no_of_persons integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 305 (class 1259 OID 19634)
-- Name: order_discount; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_discount (
    order_discount_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_discount_type_id uuid,
    order_id uuid,
    order_item_id uuid,
    order_discount_amount numeric(10,2),
    order_discount_percentage numeric(5,2),
    order_discount_code character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 306 (class 1259 OID 19644)
-- Name: order_instruction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_instruction (
    order_instruction_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    special_instructions text,
    kitchen_notes text,
    delivery_notes text,
    allergen_warning text,
    dietary_preferences text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 307 (class 1259 OID 19656)
-- Name: order_integration_sync; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_integration_sync (
    order_integration_sync_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    sync_status character varying(20),
    sync_errors text,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 308 (class 1259 OID 19668)
-- Name: order_invoice; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_invoice (
    order_invoice_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    is_invoice_generated boolean DEFAULT false,
    invoice_url text,
    invoice_generated_at timestamp with time zone,
    gstin character varying(255),
    is_business_order boolean DEFAULT false,
    business_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 309 (class 1259 OID 19682)
-- Name: order_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_item (
    order_item_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    menu_item_id uuid,
    menu_item_variation_id uuid,
    sku character varying(100),
    hsn_code character varying(20),
    category_id uuid,
    category_name character varying(100),
    base_price numeric(10,2),
    discount_amount numeric(10,2),
    tax_amount numeric(10,2),
    addon_total numeric(10,2),
    is_available boolean DEFAULT true,
    unavailable_reason text,
    substitute_item_id uuid,
    cooking_instructions text,
    spice_level character varying(20),
    customizations jsonb,
    item_status character varying(50),
    prepared_at timestamp with time zone,
    served_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    cancellation_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 310 (class 1259 OID 19695)
-- Name: order_kitchen_detail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_kitchen_detail (
    order_kitchen_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    order_item_id uuid,
    estimated_ready_time timestamp with time zone,
    actual_ready_time timestamp with time zone,
    preparation_start_time timestamp with time zone,
    minimum_preparation_time integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 311 (class 1259 OID 19705)
-- Name: order_note; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_note (
    order_note_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    order_note_type character varying(20),
    order_note_text text,
    order_note_visibility boolean DEFAULT true,
    order_note_added_by uuid,
    is_important boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 312 (class 1259 OID 19719)
-- Name: order_payment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_payment (
    order_payment_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_order_id uuid,
    primary_transaction_id uuid,
    order_id uuid,
    order_payment_method_id uuid,
    tax_calculation_type_id uuid,
    paid_amount numeric(12,2),
    refund_amount numeric(12,2),
    wallet_amount_used numeric(12,2),
    loyalty_points_used integer,
    loyalty_points_earned integer,
    collect_cash boolean DEFAULT false,
    order_payment_status character varying(20),
    order_payment_transaction_reference character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 313 (class 1259 OID 19730)
-- Name: order_payment_method; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_payment_method (
    order_payment_method_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_payment_method_code character varying(20),
    order_payment_method_name character varying(255),
    order_payment_method_is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 314 (class 1259 OID 19741)
-- Name: order_priority; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_priority (
    order_priority_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    is_urgent boolean DEFAULT false,
    priority_level integer,
    is_vip_order boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 315 (class 1259 OID 19753)
-- Name: order_scheduling; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_scheduling (
    order_scheduling_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    is_preorder boolean DEFAULT false,
    is_scheduled boolean DEFAULT false,
    preorder_date date,
    preorder_time time without time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 316 (class 1259 OID 19765)
-- Name: order_security_detail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_security_detail (
    order_security_detail_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    otp character varying(255),
    callback_url text,
    callback_received_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 317 (class 1259 OID 19777)
-- Name: order_source_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_source_type (
    order_source_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_source_type_code character varying(20),
    order_source_type_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 318 (class 1259 OID 19787)
-- Name: order_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_status_history (
    order_status_history_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    order_status_type_id uuid,
    order_status_changed_by uuid,
    order_status_changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    order_status_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 319 (class 1259 OID 19800)
-- Name: order_status_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_status_type (
    order_status_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_status_code character varying(20),
    order_status_name character varying(255),
    order_status_description text,
    order_status_is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 320 (class 1259 OID 19813)
-- Name: order_tax_line; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_tax_line (
    order_tax_line_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_tax_line_charge_id uuid,
    order_item_id uuid,
    order_tax_line_tax_type character varying(20),
    order_tax_line_percentage numeric(5,2),
    order_tax_line_amount numeric(10,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 321 (class 1259 OID 19823)
-- Name: order_total; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_total (
    order_total_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    items_total numeric(12,2),
    addons_total numeric(12,2),
    charges_total numeric(12,2),
    discount_total numeric(12,2),
    tax_total numeric(12,2),
    platform_fee numeric(10,2),
    convenience_fee numeric(10,2),
    subtotal numeric(12,2),
    roundoff_amount numeric(10,2),
    total_before_tip numeric(12,2),
    tip_amount numeric(10,2),
    final_amount numeric(12,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 322 (class 1259 OID 19833)
-- Name: order_type_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_type_table (
    order_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_type_code character varying(20),
    order_type_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 323 (class 1259 OID 19843)
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    order_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    table_booking_id uuid,
    order_number bigint,
    order_invoice_number character varying(20),
    order_vr_order_id character varying(255),
    order_external_reference_id character varying(255),
    order_type_id uuid,
    order_source_type_id uuid,
    order_status_type_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 324 (class 1259 OID 19855)
-- Name: password_reset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.password_reset (
    password_reset_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    password_reset_token character varying(255),
    password_reset_expires_at timestamp with time zone,
    password_reset_used_at timestamp with time zone,
    password_reset_ip_address text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 325 (class 1259 OID 19867)
-- Name: payment_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_audit_log (
    audit_log_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_order_id uuid,
    payment_transaction_id uuid,
    payment_refund_id uuid,
    event_type text,
    event_source text,
    request_payload jsonb,
    response_payload jsonb,
    gateway_event_id text,
    gateway_event_type text,
    initiated_by uuid,
    ip_address character varying(255),
    user_agent character varying(255),
    event_status character varying(20),
    error_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 326 (class 1259 OID 19879)
-- Name: payment_external_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_external_mapping (
    external_mapping_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_order_id uuid,
    payment_transaction_id uuid,
    external_system text,
    external_payment_id text,
    external_order_id text,
    sync_status character varying(20),
    sync_attempts integer DEFAULT 0,
    last_synced_at timestamp with time zone,
    sync_error text,
    external_response jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 327 (class 1259 OID 19892)
-- Name: payment_gateway; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_gateway (
    payment_gateway_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_gateway_code character varying(20),
    payment_gateway_name character varying(255),
    payment_gateway_is_active boolean DEFAULT true,
    payment_gateway_config jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 328 (class 1259 OID 19905)
-- Name: payment_order; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_order (
    payment_order_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    order_id uuid,
    restaurant_id uuid,
    customer_id uuid,
    payment_gateway_id uuid,
    gateway_order_id text,
    payment_order_status character varying(20),
    order_amount numeric(12,2),
    order_currency character varying(3) DEFAULT 'INR'::character varying,
    payment_link_url text,
    payment_link_id character varying(255),
    payment_link_short_url text,
    payment_link_expires_at timestamp with time zone,
    retry_count integer DEFAULT 0,
    max_retry_attempts integer DEFAULT 3,
    notes text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 329 (class 1259 OID 19920)
-- Name: payment_refund; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_refund (
    payment_refund_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_transaction_id uuid,
    order_id uuid,
    order_item_id uuid,
    payment_order_id uuid,
    payment_gateway_id uuid,
    gateway_refund_id character varying(255),
    gateway_payment_id character varying(255),
    refund_amount numeric(12,2),
    refund_currency character varying(3) DEFAULT 'INR'::character varying,
    refund_reason_type_id uuid,
    refund_reason_notes text,
    refund_status_type_id uuid,
    initiated_by uuid,
    approved_by uuid,
    processing_notes text,
    gateway_response jsonb,
    refund_initiated_at timestamp with time zone,
    refund_processed_at timestamp with time zone,
    refund_completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 330 (class 1259 OID 19933)
-- Name: payment_retry_attempt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_retry_attempt (
    retry_attempt_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_order_id uuid,
    payment_transaction_id uuid,
    attempt_number integer,
    gateway_payment_id text,
    attempt_status character varying(20),
    failure_reason text,
    failure_code character varying(20),
    retry_metadata jsonb,
    attempted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 331 (class 1259 OID 19946)
-- Name: payment_split; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_split (
    payment_split_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_transaction_id uuid,
    order_id uuid,
    split_party_type character varying(20),
    split_party_id uuid,
    split_amount numeric(12,2),
    split_percentage numeric(5,2),
    split_currency character varying(3) DEFAULT 'INR'::character varying,
    delivery_partner_id uuid,
    is_settled boolean DEFAULT false,
    settled_at timestamp with time zone,
    settlement_reference character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 332 (class 1259 OID 19958)
-- Name: payment_status_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_status_type (
    payment_status_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_status_code character varying(20),
    payment_status_name character varying(255),
    payment_status_description text,
    payment_status_is_terminal boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 333 (class 1259 OID 19971)
-- Name: payment_transaction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_transaction (
    payment_transaction_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_order_id uuid,
    order_id uuid,
    restaurant_id uuid,
    customer_id uuid,
    payment_gateway_id uuid,
    gateway_payment_id text,
    gateway_transaction_id text,
    gateway_signature text,
    order_payment_method_id uuid,
    payment_method_details jsonb,
    transaction_amount numeric(12,2),
    amount_paid numeric(12,2),
    amount_due numeric(12,2),
    transaction_currency character varying(3) DEFAULT 'INR'::character varying,
    gateway_fee numeric(10,2),
    gateway_tax numeric(10,2),
    net_amount numeric(12,2),
    payment_status_type_id uuid,
    failure_reason text,
    failure_code character varying(20),
    error_description text,
    bank_name text,
    card_network text,
    card_type text,
    card_last4 character varying(4),
    wallet_provider text,
    upi_vpa text,
    customer_email text,
    customer_contact text,
    gateway_response jsonb,
    attempted_at timestamp with time zone,
    authorized_at timestamp with time zone,
    captured_at timestamp with time zone,
    settled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 334 (class 1259 OID 19984)
-- Name: payment_webhook_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_webhook_log (
    webhook_log_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    payment_gateway_id uuid,
    webhook_event_id text,
    webhook_event_type text,
    webhook_payload jsonb,
    webhook_signature text,
    signature_verified boolean DEFAULT false,
    processing_status character varying(20),
    processing_attempts integer DEFAULT 0,
    processing_error text,
    extracted_payment_id text,
    extracted_order_id text,
    matched_payment_transaction_id text,
    source_ip text,
    received_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 335 (class 1259 OID 19999)
-- Name: pincode_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pincode_table (
    pincode_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    pincode character varying(255) NOT NULL,
    city_id uuid,
    area_name text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 336 (class 1259 OID 20012)
-- Name: refund_reason_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refund_reason_type (
    refund_reason_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    refund_reason_code character varying(20),
    refund_reason_name character varying(255),
    refund_reason_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 337 (class 1259 OID 20024)
-- Name: refund_status_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refund_status_type (
    refund_status_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    refund_status_code character varying(20) NOT NULL,
    refund_status_name character varying(255) NOT NULL,
    refund_status_description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 338 (class 1259 OID 20038)
-- Name: restaurant_faq; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_faq (
    restaurant_faq_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    restaurant_faq_question text NOT NULL,
    restaurant_faq_answer text NOT NULL,
    restaurant_faq_category character varying(100),
    restaurant_faq_display_order integer DEFAULT 0,
    restaurant_faq_is_active boolean DEFAULT true,
    restaurant_faq_view_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 339 (class 1259 OID 20056)
-- Name: restaurant_policy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_policy (
    restaurant_policy_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    restaurant_policy_category character varying(100) NOT NULL,
    restaurant_policy_title text NOT NULL,
    restaurant_policy_description text,
    restaurant_is_active boolean DEFAULT true,
    restaurant_effective_from date,
    restaurant_effective_until date,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 340 (class 1259 OID 20072)
-- Name: restaurant_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_table (
    restaurant_id uuid DEFAULT gen_random_uuid() NOT NULL,
    chain_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false,
    deleted_at timestamp with time zone
);


--
-- TOC entry 341 (class 1259 OID 20084)
-- Name: role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role (
    role_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    role_name character varying(255) NOT NULL,
    role_unique_code character varying(20) NOT NULL,
    role_description text,
    role_level integer,
    is_system_role boolean DEFAULT false,
    role_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 342 (class 1259 OID 20099)
-- Name: round_robin_pool; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.round_robin_pool (
    round_robin_pool_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    round_robin_pool_name character varying(255),
    round_robin_pool_type character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 343 (class 1259 OID 20110)
-- Name: round_robin_pool_member; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.round_robin_pool_member (
    round_robin_pool_member_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    round_robin_pool_id uuid NOT NULL,
    user_id uuid NOT NULL,
    round_robin_pool_member_priority integer,
    round_robin_pool_member_is_active boolean DEFAULT true,
    round_robin_pool_member_last_assigned_at timestamp with time zone,
    round_robin_pool_member_total_assignments integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 344 (class 1259 OID 20124)
-- Name: shift_timing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift_timing (
    shift_timing_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    shift_timing_name character varying(255),
    shift_timing_shift_code character varying(20),
    shift_timing_start_time time without time zone,
    shift_timing_end_time time without time zone,
    shift_timing_break_duration_minutes integer,
    shift_timing_is_overnight boolean DEFAULT false,
    shift_timing_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 345 (class 1259 OID 20136)
-- Name: state_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.state_table (
    state_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    state_name character varying(255) NOT NULL,
    country_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 346 (class 1259 OID 20147)
-- Name: table_booking_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_booking_info (
    table_booking_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_id uuid NOT NULL,
    meal_slot_timing_id uuid,
    previous_slot_id uuid,
    customer_id uuid NOT NULL,
    occasion_id uuid,
    party_size integer,
    booking_date date,
    booking_time time without time zone,
    booking_status character varying(20),
    special_request text,
    cancellation_reason text,
    is_advance_booking boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 347 (class 1259 OID 20163)
-- Name: table_booking_occasion_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_booking_occasion_info (
    occasion_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    occasion_type character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 348 (class 1259 OID 20174)
-- Name: table_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_info (
    table_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_number integer,
    table_capacity integer,
    table_type character varying(255),
    is_active boolean DEFAULT true,
    floor_location character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 349 (class 1259 OID 20188)
-- Name: table_special_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_special_features (
    table_feature_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    table_id uuid NOT NULL,
    feature_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 350 (class 1259 OID 20199)
-- Name: tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tag (
    tag_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tag_name character varying(255),
    tag_type character varying(20),
    tag_description text,
    tag_color character varying(255),
    tag_status character varying(20),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 351 (class 1259 OID 20211)
-- Name: tags_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tags_feedback (
    tag_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tag_name character varying(255) NOT NULL,
    description text,
    color_code character varying(255),
    usage_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 352 (class 1259 OID 20226)
-- Name: tax_calculation_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tax_calculation_type (
    tax_calculation_type_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tax_calculation_type_code character varying(255),
    tax_calculation_type_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 353 (class 1259 OID 20238)
-- Name: taxes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.taxes (
    tax_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid NOT NULL,
    tax_name character varying(255),
    tax_percentage numeric(5,2),
    tax_type character varying(50),
    tax_status character varying(20),
    tax_ordertype character varying(50),
    tax_total numeric(12,2),
    tax_rank integer,
    tax_description text,
    tax_consider_in_core_amount boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 354 (class 1259 OID 20252)
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    user_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_email character varying(255),
    user_mobile_no character varying(255),
    user_password_hash text,
    user_status character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 355 (class 1259 OID 20264)
-- Name: user_audit_trail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_audit_trail (
    user_audit_trail_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    user_audit_trail_table_name character varying(255),
    user_audit_trail_record_id uuid,
    user_audit_trail_action text,
    user_audit_trail_old_values jsonb,
    user_audit_trail_new_values jsonb,
    user_audit_trail_changed_by uuid,
    user_audit_trail_changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 356 (class 1259 OID 20277)
-- Name: user_contact; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_contact (
    user_contact_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    user_contact_type character varying(255),
    user_contact_value character varying(255),
    user_contact_is_primary boolean DEFAULT false,
    user_contact_is_verified boolean DEFAULT false,
    user_contact_verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 357 (class 1259 OID 20291)
-- Name: user_department; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_department (
    user_department_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    department_id uuid,
    user_department_is_primary boolean DEFAULT false,
    user_department_assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_department_assigned_by uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 358 (class 1259 OID 20303)
-- Name: user_login_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_login_history (
    user_login_history_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    user_login_history_login_at timestamp with time zone,
    user_login_history_logout_at timestamp with time zone,
    user_login_history_ip_address character varying(255),
    user_login_history_user_agent character varying(255),
    user_login_history_device_type character varying(255),
    user_login_history_location_data text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 359 (class 1259 OID 20315)
-- Name: user_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profile (
    user_profile_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    user_profile_first_name character varying(255),
    user_profile_last_name character varying(255),
    user_profile_display_name character varying(255),
    user_profile_gender character varying(255),
    user_profile_date_of_birth date,
    user_profile_profile_picture_url text,
    user_profile_bio text,
    user_profile_address_line1 text,
    user_profile_address_line2 text,
    user_profile_city character varying(255),
    user_profile_state character varying(255),
    user_profile_country character varying(255),
    user_profile_postal_code character varying(255),
    user_profile_timezone character varying(255),
    user_profile_language_preference text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 360 (class 1259 OID 20327)
-- Name: user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_role (
    user_role_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    role_id uuid,
    user_role_assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_role_assigned_by uuid,
    user_role_expires_at timestamp with time zone,
    user_role_is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 361 (class 1259 OID 20339)
-- Name: user_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_session (
    user_session_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    user_session_token character varying(255),
    user_session_refresh_token character varying(255),
    user_session_ip_address character varying(255),
    user_session_user_agent character varying(255),
    user_session_device_info text,
    user_session_expires_at timestamp with time zone,
    user_session_last_activity_at timestamp with time zone,
    user_session_logged_out_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 362 (class 1259 OID 20351)
-- Name: user_shift_assignment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_shift_assignment (
    user_shift_assignment_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    shift_timing_id uuid,
    user_shift_assignment_effective_from date,
    user_shift_assignment_effective_to date,
    user_shift_assignment_assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_shift_assignment_assigned_by uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 363 (class 1259 OID 20362)
-- Name: user_tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_tag (
    user_tag_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    tag_id uuid,
    user_tag_added_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_tag_added_by uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 364 (class 1259 OID 20373)
-- Name: variation_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.variation_groups (
    variation_group_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    restaurant_id uuid,
    variation_group_name character varying(255),
    variation_group_selection_type character varying(255),
    variation_group_min_selection integer,
    variation_group_max_selection integer,
    variation_group_status character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 365 (class 1259 OID 20385)
-- Name: variation_options; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.variation_options (
    variation_option_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    variation_group_id uuid,
    menu_item_id uuid,
    option_name character varying(255),
    option_price_modifier numeric(10,2),
    option_rank integer,
    option_status character varying(255),
    dietary_type_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    is_deleted boolean DEFAULT false
);


--
-- TOC entry 5351 (class 0 OID 18591)
-- Dependencies: 220
-- Data for Name: account_lock; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.account_lock (account_lock_id, user_id, account_lock_at, account_lock_until, account_lock_reason, account_lock_failed_attempts, account_lock_unlocked_at, account_lock_unlocked_by, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5352 (class 0 OID 18603)
-- Dependencies: 221
-- Data for Name: allergens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.allergens (allergen_id, allergen_name, allergen_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5353 (class 0 OID 18616)
-- Dependencies: 222
-- Data for Name: branch_contact_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branch_contact_table (branch_contact_id, branch_id, contact_type, contact_value, is_primary, contact_label, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5354 (class 0 OID 18629)
-- Dependencies: 223
-- Data for Name: branch_info_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branch_info_table (branch_id, chain_id, branch_name, branch_website_url, branch_logo_url, branch_personalized_greeting, order_type, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
ccd77567-41db-49e0-9f55-ca646cf040ad	d9d9c09b-1ee8-48dc-a62e-c6928f4ecbe4	Main Branch	\N	\N	\N	\N	2025-11-26 17:17:25.782412+05:30	2025-11-26 17:17:25.782412+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5355 (class 0 OID 18642)
-- Dependencies: 224
-- Data for Name: branch_location_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branch_location_table (branch_location_id, branch_id, address_line, landmark, pincode_id, latitude, longitude, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5356 (class 0 OID 18654)
-- Dependencies: 225
-- Data for Name: branch_timing_policy; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branch_timing_policy (branch_timing_id, restaurant_id, opening_time, closing_time, food_ordering_start_time, food_ordering_closing_time, table_booking_open_time, table_booking_close_time, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5357 (class 0 OID 18664)
-- Dependencies: 226
-- Data for Name: chain_contact_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chain_contact_table (chain_contact_id, chain_id, contact_type, contact_value, is_primary, contact_label, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5358 (class 0 OID 18677)
-- Dependencies: 227
-- Data for Name: chain_info_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chain_info_table (chain_id, chain_name, chain_website_url, chain_logo_url, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
d9d9c09b-1ee8-48dc-a62e-c6928f4ecbe4	Default Restaurant Chain	\N	\N	2025-11-26 17:17:25.782412+05:30	2025-11-26 17:17:25.782412+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5359 (class 0 OID 18690)
-- Dependencies: 228
-- Data for Name: chain_location_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chain_location_table (chain_location_id, chain_id, address_line, landmark, pincode_id, latitude, longitude, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5360 (class 0 OID 18702)
-- Dependencies: 229
-- Data for Name: city_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.city_table (city_id, city_name, state_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5361 (class 0 OID 18713)
-- Dependencies: 230
-- Data for Name: combo_item; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.combo_item (combo_item_id, combo_item_component_id, restaurant_id, combo_type, is_available, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5362 (class 0 OID 18724)
-- Dependencies: 231
-- Data for Name: combo_item_components; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.combo_item_components (combo_item_component_id, combo_item_id, menu_item_id, quantity, is_optional, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5363 (class 0 OID 18736)
-- Dependencies: 232
-- Data for Name: country_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.country_table (country_id, country_name, iso_code, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5364 (class 0 OID 18748)
-- Dependencies: 233
-- Data for Name: cuisines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cuisines (cuisine_id, cuisine_name, cuisine_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
55fbe002-1965-46d7-820a-c60e90731fbb	South Indian	active	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
45472f72-7a6d-4b2a-8bfb-86f919acb727	North Indian	active	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
4d4e1276-0726-4e4d-a0ef-8093dda415bd	Street Food / Chaat	active	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
0c320b3b-4489-4b4a-ab86-07f4288ad0da	Chinese / Indo-Chinese	active	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
f3692e61-a88d-4c94-a9c0-ea5124812283	Continental	active	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5365 (class 0 OID 18758)
-- Dependencies: 234
-- Data for Name: customer_activity_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_activity_log (log_id, customer_id, activity_type, activity_timestamp, ip_address, user_agent, details, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5366 (class 0 OID 18771)
-- Dependencies: 235
-- Data for Name: customer_address_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_address_table (customer_address_id, customer_id, customer_address_type, customer_address_label, customer_street_address_1, customer_street_address_2, customer_city, customer_state_province, customer_postal_code, customer_country, customer_latitude, customer_longitude, customer_is_default, customer_delivery_instructions, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5367 (class 0 OID 18784)
-- Dependencies: 236
-- Data for Name: customer_allergens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_allergens (customer_id, allergen_id, customer_allergen_severity, customer_allergen_notes, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5368 (class 0 OID 18796)
-- Dependencies: 237
-- Data for Name: customer_authentication; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_authentication (auth_id, customer_id, auth_method, auth_provider, password_hash, last_login, failed_attempts, locked_until, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5369 (class 0 OID 18809)
-- Dependencies: 238
-- Data for Name: customer_consent; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_consent (consent_id, customer_id, consent_type, consent_given, consent_date, consent_withdrawn_at, consent_method, ip_address, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5370 (class 0 OID 18823)
-- Dependencies: 239
-- Data for Name: customer_contact_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_contact_table (contact_id, customer_id, customer_contact_type, customer_contact_value, customer_is_primary, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5371 (class 0 OID 18836)
-- Dependencies: 240
-- Data for Name: customer_devices; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_devices (device_id, customer_id, device_type, device_name, os, browser, first_seen, last_seen, is_trusted, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5372 (class 0 OID 18849)
-- Dependencies: 241
-- Data for Name: customer_dietary_restrictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_dietary_restrictions (customer_id, dietary_restriction_id, customer_dietary_restriction_severity, customer_dietary_restriction_notes, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5373 (class 0 OID 18861)
-- Dependencies: 242
-- Data for Name: customer_favorite_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_favorite_items (favorite_id, customer_id, menu_item_id, added_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5374 (class 0 OID 18872)
-- Dependencies: 243
-- Data for Name: customer_gender; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_gender (customer_gender_id, customer_gender_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5375 (class 0 OID 18883)
-- Dependencies: 244
-- Data for Name: customer_preferences; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_preferences (customer_preference_id, customer_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5376 (class 0 OID 18893)
-- Dependencies: 245
-- Data for Name: customer_profile_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_profile_table (customer_id, customer_first_name, customer_last_name, customer_display_name, customer_date_of_birth, customer_gender_id, language_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5377 (class 0 OID 18904)
-- Dependencies: 246
-- Data for Name: customer_search_queries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_search_queries (query_id, customer_id, conversation_id, search_query, search_timestamp, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5378 (class 0 OID 18917)
-- Dependencies: 247
-- Data for Name: customer_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_sessions (session_id, customer_id, session_token, expires_at, ip_address, user_agent, is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5379 (class 0 OID 18930)
-- Dependencies: 248
-- Data for Name: customer_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_table (customer_id, customer_account_status, customer_type, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5380 (class 0 OID 18940)
-- Dependencies: 249
-- Data for Name: customer_tag_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_tag_mapping (customer_id, tag_id, tagged_by, tagged_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5381 (class 0 OID 18951)
-- Dependencies: 250
-- Data for Name: customer_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_tags (tag_id, tag_name, tag_category, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5382 (class 0 OID 18964)
-- Dependencies: 251
-- Data for Name: department; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.department (department_id, restaurant_id, department_name, department_unique_code, department_description, parent_department_id, department_manager_id, department_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5383 (class 0 OID 18976)
-- Dependencies: 252
-- Data for Name: dietary_restrictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dietary_restrictions (dietary_restriction_id, dietary_restriction_name, dietary_restriction_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5384 (class 0 OID 18989)
-- Dependencies: 253
-- Data for Name: dietary_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dietary_types (dietary_type_id, dietary_type_name, dietary_type_label, dietary_type_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5385 (class 0 OID 19001)
-- Dependencies: 254
-- Data for Name: discount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.discount (discount_id, restaurant_id, discount_name, discount_description, discount_type, discount_value, discount_ordertype, discount_applicable_on, discount_days, discount_status, discount_rank, discount_on_total, discount_starts_at, discount_time_from, discount_time_to, discount_min_amount, discount_max_amount, discount_has_coupon, discount_max_limit, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5386 (class 0 OID 19015)
-- Dependencies: 255
-- Data for Name: discount_schedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.discount_schedule (discount_schedule_id, discount_id, discount_schedule_day_of_week, discount_schedule_start_time, discount_schedule_end_time, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5387 (class 0 OID 19025)
-- Dependencies: 256
-- Data for Name: discount_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.discount_type (discount_type_id, discount_type_code, discount_type_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5388 (class 0 OID 19035)
-- Dependencies: 257
-- Data for Name: email_verification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.email_verification (email_verification_id, user_id, email_verification_email, email_verification_otp, email_verification_expires_at, email_verification_verified_at, email_verification_attempts, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5389 (class 0 OID 19048)
-- Dependencies: 258
-- Data for Name: entity_slot_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.entity_slot_config (slot_config_id, restaurant_id, slot_capacity, slot_duration, slot_frequency, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5390 (class 0 OID 19058)
-- Dependencies: 259
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback (feedback_id, customer_id, is_anonymous, contact_email, order_id, booking_id, product_id, service_id, title, feedback_text, rating, category_id, feedback_type_id, sentiment, priority_id, status_id, assigned_to, assigned_at, platform_id, device_info, ip_address, user_agent, page_url, is_urgent, is_featured, requires_followup, submitted_at, resolved_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5391 (class 0 OID 19077)
-- Dependencies: 260
-- Data for Name: feedback_attachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_attachments (attachment_id, feedback_id, file_name, file_path, file_type, file_size, uploaded_by, uploaded_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5392 (class 0 OID 19092)
-- Dependencies: 261
-- Data for Name: feedback_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_categories (category_id, category_name, description, icon, display_order, is_active, parent_category_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5393 (class 0 OID 19108)
-- Dependencies: 262
-- Data for Name: feedback_notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_notifications (notification_id, feedback_id, recipient_email, notification_type, subject, sent_at, opened_at, clicked_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5394 (class 0 OID 19122)
-- Dependencies: 263
-- Data for Name: feedback_platforms; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_platforms (platform_id, platform_name, platform_type, is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5395 (class 0 OID 19135)
-- Dependencies: 264
-- Data for Name: feedback_priorities; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_priorities (priority_id, priority_name, priority_level, color_code, response_sla_hours, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5396 (class 0 OID 19147)
-- Dependencies: 265
-- Data for Name: feedback_priority_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_priority_history (history_id, feedback_id, old_priority_id, new_priority_id, changed_by, changed_at, change_reason, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5397 (class 0 OID 19160)
-- Dependencies: 266
-- Data for Name: feedback_responses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_responses (response_id, feedback_id, responded_by, response_text, is_internal, is_automated, is_public, response_at, edited_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5398 (class 0 OID 19177)
-- Dependencies: 267
-- Data for Name: feedback_status_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_status_history (history_id, feedback_id, old_status_id, new_status_id, changed_by, changed_at, change_reason, is_automated, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5399 (class 0 OID 19191)
-- Dependencies: 268
-- Data for Name: feedback_statuses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_statuses (status_id, status_name, description, color_code, is_initial, is_final, display_order, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5400 (class 0 OID 19208)
-- Dependencies: 269
-- Data for Name: feedback_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_tags (feedback_id, tag_id, added_by, added_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5401 (class 0 OID 19219)
-- Dependencies: 270
-- Data for Name: feedback_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_types (type_id, type_name, description, color_code, icon, requires_response, is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5402 (class 0 OID 19235)
-- Dependencies: 271
-- Data for Name: integration_config_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.integration_config_table (integration_config_id, chain_id, branch_id, provider_id, is_enabled, api_key, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5403 (class 0 OID 19249)
-- Dependencies: 272
-- Data for Name: integration_credentials_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.integration_credentials_table (credential_id, integration_config_id, credential_key, credential_value, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5404 (class 0 OID 19261)
-- Dependencies: 273
-- Data for Name: integration_metadata_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.integration_metadata_table (metadata_id, integration_config_id, metadata_key, metadata_value, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5405 (class 0 OID 19273)
-- Dependencies: 274
-- Data for Name: integration_provider_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.integration_provider_table (provider_id, provider_name, provider_description, provider_base_url, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5406 (class 0 OID 19286)
-- Dependencies: 275
-- Data for Name: languages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.languages (language_id, language_iso, language_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5407 (class 0 OID 19298)
-- Dependencies: 276
-- Data for Name: login_attempt; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.login_attempt (login_attempt_id, user_id, login_attempt_email, login_attempt_success, login_attempt_ip_address, login_attempt_user_agent, login_attempt_failure_reason, login_attempt_attempted_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5408 (class 0 OID 19312)
-- Dependencies: 277
-- Data for Name: loyalty_transaction; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.loyalty_transaction (loyalty_txn_id, customer_id, order_id, payment_transaction_id, points_used, points_earned, points_balance_after, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5409 (class 0 OID 19325)
-- Dependencies: 278
-- Data for Name: meal_slot_timing; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.meal_slot_timing (meal_slot_timing_id, slot_config_id, meal_type_id, opening_time, closing_time, is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5410 (class 0 OID 19336)
-- Dependencies: 279
-- Data for Name: meal_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.meal_type (meal_type_id, meal_type_name, display_order, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d	Breakfast	1	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
871a4f82-77b0-4209-9805-41364b6fcbf9	Lunch	2	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
78f1d95f-fbda-414c-aa18-d1a5dc1f1be1	Dinner	3	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
00bc0862-4a2e-4cf4-b80c-12167bed1638	All Day	4	2025-11-26 17:25:41.502811+05:30	2025-11-26 17:25:41.502811+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5411 (class 0 OID 19346)
-- Dependencies: 280
-- Data for Name: menu_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_categories (menu_category_id, restaurant_id, menu_section_id, menu_category_status, menu_category_rank, menu_category_name, menu_category_description, menu_category_timings, menu_category_image_url, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
185d5e4a-83a1-422d-8f56-4c90dd7e4705	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	1	tiffin	Traditional South Indian breakfast items	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	2	main course	Main dishes for lunch and dinner	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8c333a67-81f4-43e4-a1cd-5419eac29225	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	3	beverages	Refreshing drinks and beverages	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	4	desserts	Sweet treats and desserts	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
59dc05b5-869f-4bd1-b43d-13d437f10d14	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	5	snacks	Light snacks and street food	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
011b96d9-146c-47ba-ae1b-fd693e5ef559	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	6	rice dishes	Rice-based dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
20406bbb-4d2d-44eb-82c9-97d049082d98	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	7	starters	Appetizers and starters	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
09af9996-8431-46ea-aa3c-de863550af06	6eb89f66-661c-4294-85b4-044519fdec1b	f0aebec7-a377-4e22-ba52-cace2b15a8f8	active	8	add-ons	Sides and add-ons	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5412 (class 0 OID 19358)
-- Dependencies: 281
-- Data for Name: menu_item; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item (menu_item_id, restaurant_id, menu_sub_category_id, menu_item_name, menu_item_status, menu_item_description, menu_item_price, menu_item_quantity, menu_item_allow_variation, menu_item_allow_addon, menu_item_minimum_preparation_time, menu_item_tax_id, menu_item_tax_cgst, menu_item_tax_sgst, menu_item_timings, menu_item_packaging_charges, menu_item_attribute_id, menu_item_rank, menu_item_favorite, menu_item_ignore_taxes, menu_item_ignore_discounts, menu_item_in_stock, menu_item_is_combo, menu_item_is_recommended, menu_item_spice_level, menu_item_addon_based_on, menu_item_markup_price, menu_item_is_combo_parent, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted, menu_item_calories, menu_item_is_seasonal, menu_item_image_url, menu_item_serving_unit) FROM stdin;
010c83a6-d7e3-4f48-880e-c85137fb39e2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Curd Vadai	active	Crispy lentil fritters soaked in creamy spiced yogurt, topped with chutneys and sev for a refreshing taste	40.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a601a7f8-5d30-4347-bb02-94526f4f413a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Idiyappam	active	Delicate steamed rice noodles made from rice flour, served with coconut milk or flavorful kurma	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
18d0f888-ae4a-4071-a6be-ab7e467c6472	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Idly	active	Soft, fluffy steamed rice cakes made from fermented rice and lentil batter, served with sambar and chutney	35.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3f32641e-2154-45f9-ba9b-4840865e04d5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Khichdi	active	Comforting one-pot rice and lentil dish with mild spices, easy to digest and nutritious	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9d63daef-e702-4908-9df5-d54c07335256	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Methu Vadai	active	Classic South Indian crispy lentil donuts with soft center, served with sambar and coconut chutney	25.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4d7a637f-1360-458e-95da-d4bb74c5c99c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mini Breakfast	active	Complete breakfast combo with mini portions of popular tiffin items, perfect for light eaters	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bdc6318f-5da2-4907-bab4-cf4838d80988	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Sambar Mini Idly	active	Fluffy steamed rice cakes immersed in flavorful lentil-vegetable stew, a wholesome South Indian comfort food	60.00	8	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a2a30d42-28a9-4050-b157-0227e4a539c5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Podi Idly	active	Soft steamed rice cakes tossed with aromatic gun powder spice mix, offering a flavorful kick to the traditional idly	50.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
eff3d4e3-726b-4170-9d2e-5894b0a70ad5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pongal	active	Comforting rice and lentil porridge tempered with cumin, pepper, curry leaves and ghee, a breakfast classic	65.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f4abc59c-b7de-4de0-9e12-bcbb3a7fa1f1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Poori Masala	active	Golden fried wheat bread served with aromatic potato masala curry and accompaniments	60.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
57c06b53-155f-4b54-b420-a4605b0badc8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sambar Idly	active	Fluffy steamed rice cakes immersed in flavorful lentil-vegetable stew, a wholesome South Indian comfort food	45.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a66b87c2-03a2-47e8-a9da-37904dbe30b9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sambar Vadai	active	Golden crispy lentil donuts immersed in aromatic sambar, combining crispy and soft textures perfectly	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
278a9ee5-f497-4297-a6cb-e8f8e9ca9faf	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aloo Poori	active	Fluffy deep-fried wheat bread served with spiced potato curry, a North Indian breakfast favorite	75.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
be6fab0b-7648-4c86-914b-7ba63acf9bf2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Bhel Pori	active	Puffed rice mixed with sev, onions, tomatoes, chutneys and spices, tangy Mumbai snack	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
44cc830b-0ae9-4aa0-a2ed-57ac80e0b4fb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Bread Channa Chat	active	Bread pieces topped with chickpeas, yogurt, chutneys and crispy sev	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b0d208c9-a2e9-40d1-a263-42962f53ca7a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Channa Masala	active	Chickpeas cooked in tangy tomato-onion gravy with authentic Punjabi spices	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
60b5673e-9d4a-41b1-8383-05932a7395ae	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cheese Pav Bhaji	active	Mumbai street food with spicy mashed vegetables topped with cheese, served with buttered pav	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
27afa12a-791f-495f-91be-dce580504f4c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cutlet Channa Chat	active	Vegetable cutlet topped with chickpeas, yogurt and tangy chutneys	70.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
42917c7d-09af-4ae7-91a9-3b65b0c654a3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dahi Pappadi Chat	active	Tangy savory street food with yogurt, chutneys and spices	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3953ae28-900d-42b9-92c3-6b97102aada0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dahi Poori	active	Soft puffy deep-fried wheat bread, light and fluffy, served with flavorful curry	60.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c92904fa-2ba8-4e5d-9abc-73d3ce7a66bb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dahi Samosa Chat	active	Crispy samosa topped with chickpeas, yogurt, chutneys and sev, loaded street food	70.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8b78ab34-c265-4577-9c86-21a4d09cdc52	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pav	active	Delicious dish prepared with fresh ingredients and authentic spices	10.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
70ee9dbf-1477-42f9-9359-f1f40fb79ea2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	French Fries	active	Crispy golden potato fries, perfect snack or side dish	90.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
544e1530-13e3-4a9f-8186-1889b0004c40	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Masala Pav Bhaji	active	Iconic Mumbai street food - spicy mashed vegetables served with buttered pav bread	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b269c7ba-3584-49b4-b3c2-09c4a390688e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Masala Poori	active	Golden fried wheat bread served with aromatic potato masala curry and accompaniments	60.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
006c6e95-b04b-4bc1-9bc6-68202e92d1af	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paani Poori	active	Soft puffy deep-fried wheat bread, light and fluffy, served with flavorful curry	60.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
299f9d53-9f76-4c85-a2bc-337d53055cd2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Pav Bhaji	active	Spicy vegetable mash with mushrooms, served with soft buttered bread	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e31406b2-d66e-44ab-bff0-73fba95ad51e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Pav Bhaji	active	Spicy mashed vegetables with cottage cheese cubes, served with buttered pav	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
12c9297b-83ec-4782-b024-46edad03e261	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pav Bhaji	active	Iconic Mumbai street food - spicy mashed vegetables served with buttered pav bread	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c30a6a90-4ce5-4917-9e62-4972d4e1ee19	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Samosa	active	Crispy triangular pastry filled with spiced potato and peas, classic Indian snack	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9c2ddc01-f7c7-4451-a595-d665830b062a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Samosa Channa Chaat	active	Crispy samosa topped with chickpeas, yogurt, chutneys and sev, loaded street food	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8f2d8131-94a6-4331-841e-1031150bd63e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sev Poori	active	Soft puffy deep-fried wheat bread, light and fluffy, served with flavorful curry	60.00	5	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2abf9654-d5e5-490e-b96f-0b7b2b426283	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Amla Juice	active	Vitamin C rich Indian gooseberry juice, immunity booster with tangy taste	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ccfd7416-c0a3-4329-a4c1-a95603e27da6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Badam Gheer	active	Rich almond-based sweet drink, thick and creamy traditional beverage	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Badam Kulfi	active	Traditional Indian frozen dessert with almonds, denser and creamier than ice cream	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
28ef3fa2-c237-4c93-b411-82f0001e6492	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cold Coffee	active	Chilled coffee beverage with milk and ice, refreshing and energizing	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5f1b450b-391d-4208-b336-53e192baa578	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ilaneer Payasam	active	Tender coconut payasam, unique and refreshing South Indian dessert	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b3e70ef0-d8b4-42af-80c4-8ee78031befd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mini Jigardhanda	active	Famous Madurai cooling drink with milk, almond gum and ice cream, sweet and refreshing	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1f3c418f-548c-4aeb-99c1-86f784f1c9e1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Lassi	active	Creamy yogurt-based drink, cooling and probiotic-rich	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1461d06d-72a8-46b5-8090-b0bad1c2646a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Nannari Juice	active	Traditional South Indian sarsaparilla root drink, cooling and refreshing	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a172152e-4a5c-439b-bb67-8c41414bb799	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rose Milk	active	Sweet rose-flavored milk drink, cooling and refreshing	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
87a9c9c7-5315-457e-918e-10aed9d46911	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Noodles	active	Aromatic noodles infused with crispy burnt garlic and vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8fb74061-258a-429a-b2dd-2628cce88d86	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Rice	active	Flavorful rice preparation cooked to perfection	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1e81be0c-c4cf-4970-a53a-505eb92e87bd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Gobi	active	Crispy cauliflower florets tossed in spicy chilli sauce with peppers	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
acff3dd5-e388-4060-b2f7-38fd24021c68	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Idly Fry	active	Crispy fried idly pieces tossed in spicy Indo-Chinese sauce with capsicum and onions	35.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
67148a4a-35f9-414e-b58c-c2ac18104782	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Mushroom	active	Stir-fried mushrooms in spicy chilli sauce with capsicum and onions	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2075e9ed-f702-4fb6-84f1-16eb3917b5f1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Paneer	active	Cottage cheese cubes tossed with onions, capsicum in spicy Indo-Chinese sauce	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4aab1431-eab8-4c5f-9202-92a916cd0966	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Parota	active	Shredded parotta tossed with vegetables in spicy chilli sauce, fusion favorite	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
09aa6db4-7502-4dc4-b889-14fff6e4d482	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Soy	active	Crispy soya chunks tossed in spicy chilli sauce	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4b0a1e8a-d96e-46ad-ba49-1b17a02cccbf	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Creamy Vegetable Soup	active	Creamy mixed vegetable soup, smooth and nourishing	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0d5ffcb1-b741-42e0-aba8-a09b4f2c7cfc	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dragon Paneer	active	Delicious appetizer to begin your meal	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
14ef9cd7-4fe2-4b27-970e-773e959f05d8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Drumstick Mushroom Garlic Soup	active	Nutritious soup with drumstick, mushrooms and garlic, healthy and flavorful	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bdbcddb6-5725-4e59-8a2c-7a3d463ed820	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Gobi 65	active	Crispy cauliflower florets coated in spicy masala, addictive Indo-Chinese starter	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
052f6175-66a2-4b84-ad4b-047cccec298d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Gobi Manchurian Dry	active	Crispy cauliflower florets in tangy Indo-Chinese sauce, perfect appetizer	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9a29e77f-f13a-4128-bc24-2f122891a487	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Gobi Manchurian Gravy	active	Crispy cauliflower in tangy sweet manchurian gravy, pairs well with rice	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4a652f79-d0fa-402b-b134-b53ee5b5076e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Gobi Pepper Fry	active	Cauliflower florets tossed with black pepper and South Indian spices	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f5e1ea70-3e91-4df5-9c55-9669c9e62872	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Idly Pepper Fry	active	Soft, fluffy steamed rice cakes made from fermented rice and lentil batter, served with sambar and chutney	35.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c2ad9384-1f73-4f8f-8f62-7bae9e2aad59	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Herbs Fried Rice	active	Fragrant fried rice seasoned with fresh herbs and aromatic spices	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
54ee838c-f191-4dab-a861-8bbf24ed8b70	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Honey Chilli Paneer	active	Sweet and spicy cottage cheese tossed with honey, capsicum and onions in Chinese sauce	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1e5a0a42-ea87-4bf8-8aa7-5e871ca49904	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Honey Chilli Potato	active	Sweet and spicy honey chilli potato fingers, crispy and addictive	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b3584fe8-58b9-4eed-9daf-81af7c5c2597	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kaima Parota	active	Flaky layered parotta served with flavorful potato kurma	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1180b173-548f-4fa0-b566-64cdc0b1dfd5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Manchow Crispy Noodle Soup	active	Indo-Chinese noodles with tangy manchow flavors and vegetables	85.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bad85a08-06e2-4bc7-b864-6b177112df70	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Manchow Fried Rice	active	Indo-Chinese fried rice with tangy manchow flavors and crispy noodles on top	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0a4d265a-8b56-408c-89b2-d9cdc54982f8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom 65	active	Spicy deep-fried mushroom bites with curry leaves and aromatic spices	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
987066f3-edd3-454f-9f5d-0cfb5e55c1e0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Fried Rice	active	Wok-tossed rice with mushrooms, vegetables and aromatic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
62aad12b-d9fd-4fa1-8d80-3f93bd42d2b6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Manchurian Dry	active	Crispy mushroom balls in sweet and tangy manchurian sauce	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fd85f52e-0065-4fbc-bb94-1465b1d154ee	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Manchurian Gravy	active	Mushroom balls in flavorful manchurian gravy, rich and saucy	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5cbddda4-b4af-45d7-b913-de01a9a72cd5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Noodles	active	Stir-fried noodles with mushrooms and mixed vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ce3bf15e-84fe-4ce7-a10e-1a26ec8acf05	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Pepper Fry	active	Mushrooms stir-fried with crushed pepper, curry leaves and spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bf98b52e-f41b-4308-906b-3ab72d075a9a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer 65	active	Spicy cottage cheese bites marinated and deep fried until crispy, a popular Indo-Chinese appetizer	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
57ba4cb0-d12f-4e87-81b2-b384cf4e8cb7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Fried Rice	active	Stir-fried rice with cottage cheese cubes, vegetables and soy-based seasoning	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
553ac569-2406-4dba-b5f2-dcd928b95787	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Manchurian Dry	active	Crispy cottage cheese balls tossed in tangy manchurian sauce, served dry	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
59985ea0-e5ff-4cf2-9858-7ba48ee722be	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Manchurian Gravy	active	Cottage cheese balls in rich Indo-Chinese gravy with capsicum and onions	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
59e2aa6a-bb1c-4f29-86e6-d7980d954d46	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Noodles	active	Hakka noodles tossed with cottage cheese cubes and crisp vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fe1cc623-5749-4759-bb79-c08f0e00d4b3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Pepper Fry	active	Cottage cheese cubes stir-fried with crushed pepper, onions and spices, aromatic and spicy	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a658600f-95be-4f25-aaa5-e0cc280ec8ba	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pepper Soup	active	Traditional South Indian rasam-style pepper soup, spicy and soothing	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
18f5b5c1-e9df-4769-9ec2-38abffd9fa3c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Fried Rice	active	Spicy fried rice tossed in fiery Schezwan sauce with vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
62c2253a-293e-4954-806a-f893f400e55d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Mushroom Fried Rice	active	Fiery Schezwan fried rice with mushrooms and spicy red sauce	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f390a5a5-476c-4a52-89cc-bae5384a9ab1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Mushroom Noodles	active	Fiery Schezwan noodles loaded with mushrooms and spicy sauce	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
96787c99-a0ce-4332-8f26-f2297f87dcd8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Noodles	active	Spicy noodles tossed in fiery red Schezwan sauce with vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e6608ce5-674e-4c3a-ba90-6772391d4949	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Paneer Fried Rice	active	Spicy Schezwan-style fried rice with cottage cheese, bold and fiery Indo-Chinese favorite	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8f49b43c-be61-4c6f-95dc-4e8a7d10e7da	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Paneer Noodles	active	Spicy Schezwan noodles with cottage cheese, fiery and flavorful	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b128ec84-8ee0-470c-a38c-7ed96269ee68	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Soy	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
82657f8f-f8ad-49ec-bc2b-bb8fa993f67d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Shanghai Rice	active	Flavorful rice preparation cooked to perfection	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3b91dfb2-fd88-45f2-928f-0c9a02394b62	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Soy 65	active	Crispy soya chunks marinated in spicy batter and deep fried, protein-packed starter	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9ad814cd-f7ba-4d29-a113-805dbc651c60	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Soy Manchurian	active	Soya balls in tangy gravy, perfect accompaniment to fried rice or noodles	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
efb317af-7eac-4f9f-8f63-7883c2982ede	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mixed Fried Rice	active	Premium fried rice loaded with assorted vegetables, paneer and mushrooms	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1021ee4c-7743-4e51-a5a4-164a2ea3d842	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mixed Noodles	active	Premium mixed noodles loaded with assorted vegetables and protein	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
43301ae3-93ac-4bb3-b023-dd39d37de9f6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Steamed Vegetable Momos	active	Soft steamed vegetable dumplings, healthy and delicious Tibetan treat	35.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
30c26e10-38c4-4254-aa2e-0d42f352c023	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Thukpa Soupy Noodles	active	Hearty Tibetan noodle soup with vegetables in flavorful broth	130.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
29de49e9-c12d-4c5f-9de6-18aac4973fa5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tomato Soup	active	Smooth tomato soup with herbs and cream, comforting and classic	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
199afe79-6431-46a4-a0a1-1add114881ef	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Soup	active	Clear vegetable soup with fresh vegetables and mild seasonings	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a0ebae73-9f25-48b3-8fd5-b05ba844d222	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Fried Rice	active	Classic vegetable fried rice tossed with mixed veggies and soy-based seasoning	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
41fd61ae-6fe9-42b0-9c0e-4818f153ffa0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Noodles	active	Classic hakka noodles stir-fried with fresh vegetables and sauces	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
74e0df2b-4c04-4518-b484-d6425e13ea74	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Pulav	active	Mildly spiced rice cooked with mixed vegetables and aromatic spices	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
089157e1-3de5-4c32-9c69-6445d78edc1f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sizzling Brownie With Ice Cream	active	Warm chocolate brownie served on sizzling platter with vanilla ice cream, dramatic and delicious	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
feca6731-d1ec-48de-952a-aba8ad404db3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vada Curry	active	Golden crispy lentil fritters made from urad dal, perfect accompaniment to sambar and chutney	25.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
957c1e64-7e5a-4c17-8f27-1a4944de6a3c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Masala Dosai	active	Crispy ghee-roasted dosa filled with spiced potato masala, served with sambar and chutney	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
18a6da15-b4b6-4225-b473-c5c0eeddd5ce	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Onion Dosai	active	Crispy dosa layered with caramelized onions and roasted in pure ghee	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1c1054e1-1106-4a8b-8230-f9bbe7b2e4d8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Onion Rava	active	Traditional South Indian delicacy	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
458c8f44-4178-4ad1-82aa-e1fafd1df65c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Onion Rava Masala Dosai	active	Crispy ghee-roasted dosa filled with spiced potato masala, served with sambar and chutney	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
cf42f76f-bfc1-410f-8cd2-f6b1a32f94e8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Podi Dosai	active	Crispy dosa brushed with ghee and sprinkled with aromatic gun powder spice mix	95.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0b171841-6ee4-4fc5-8ac9-2b19d4a2c65d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Podi Masala Dosai	active	Crispy ghee-roasted dosa filled with spiced potato masala, served with sambar and chutney	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
baaaefc8-3ba7-414d-ace8-650ade2f98db	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Podi Onion Dosai	active	Ghee-roasted dosa topped with gun powder spice mix and caramelized onions	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0aaa74f5-6f91-4b5d-9dd3-5b7ed925964e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chola Poori	active	Puffy fried wheat bread paired with spicy chickpea curry, protein-rich and satisfying	75.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
17bb19b4-e16b-4a51-8531-b7da9cbff8f0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Podi Onion Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
409b244f-7dfb-4c7b-8686-a079379ded1c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Rava Dosai	active	Lacy crispy semolina dosa roasted in aromatic ghee, light and delicious	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
52f4509d-b071-4aa4-930e-e01e97e4302f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Rava Masala Dosa	active	Crispy ghee-roasted dosa filled with spiced potato masala, served with sambar and chutney	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
531f9c5f-5fce-4446-bfe8-ce270e4f629c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Roast	active	Traditional South Indian delicacy	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b76156d6-7d71-47c8-aa45-a951287ebd9b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	75.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
20dd1625-14f7-477f-8f1c-5c929edb9956	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Madurai Mushroom Kari Dosa	active	Madurai special dosa with spicy mushroom curry filling, bold and flavorful	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
83070134-6fdd-4816-b2a3-6c37e96e22fe	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Madurai Paneer Kari Dosa	active	Signature Madurai-style dosa filled with spicy paneer curry, a regional specialty	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
44d0cc09-3bd3-4408-a54b-fa2840a6d5f3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Masala Dosai	active	Classic crispy dosa filled with spiced potato masala, the most beloved South Indian dish	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
dd5dbea6-ee71-47b6-b10e-cd736d5988aa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cashewnut Rava Dosai	active	Premium rava dosa topped with crunchy cashew nuts for added richness	75.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ac156f84-4748-4ce8-a4f6-4bb26b4839a9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Dosai	active	Traditional dosa topped with generous helping of sautéed onions	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
68d16bc7-866e-41e2-9f90-79086232128f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Podi Dosai	active	Dosa topped with aromatic podi spice mix and sautéed onions	65.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a4e76dd4-4d79-44f4-96c6-fc4eb6391677	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Rava Dosai	active	Crispy semolina dosa studded with caramelized onions and spices	65.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
28c1d342-6d69-4c31-8afd-693ac1d32db5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
70afac5e-7487-494c-9737-9ba5323e9a7e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Kozhukattai	active	Sweet rice dumplings filled with jaggery and coconut, festival special	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b15d206c-d5ef-4d69-b660-1f06272c10e4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Plain Dosai	active	Simple crispy fermented rice crepe, light and healthy, served with sambar and chutney	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5073e567-0d72-4e94-b697-79e1cd408def	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Plain Roast	active	Traditional South Indian delicacy	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
936473d2-bdc9-4727-92d1-6e8762ad2b65	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Plain Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
10bef495-7255-4638-bdfb-7b8df9c37423	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Podi Dosai	active	Crispy dosa sprinkled with aromatic gun powder spice blend for fiery flavor	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
197d1458-b83a-455c-8db5-267a616501a7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Podi Masala Dosai	active	Crispy dosa sprinkled with spicy gun powder and filled with potato masala	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2c88e468-33fb-4346-a92b-b514a7e3797b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Podi Onion Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	65.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
842e1d5a-feda-4096-ae06-5bf538545e31	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Podi Uthappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bf821156-45fe-4ab3-a13e-8d7aab0d3869	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rava Dosai	active	Thin crispy semolina crepe with lacy texture, lighter alternative to regular dosa	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f7112f63-6f6d-4a33-9362-d4ffafcf339b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rava Masala Dosai	active	Lacy semolina dosa with crispy texture, filled with spiced potato masala	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
17639dfd-b136-44c4-9284-232bdc865000	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Ginger Capsicum Masala Dosai	active	Spicy dosa with ginger-capsicum masala filling, zesty and aromatic	95.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
888933f7-ca51-41b1-90d9-45ceed3a99ca	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Ginger Gobi Masala Dosai	active	Crispy dosa filled with spiced cauliflower masala, nutritious and tasty	95.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b73cb807-821d-4f6e-8c71-78b5c5310bed	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Gobi Masala Dosai	active	Crispy dosa filled with spiced cauliflower masala, nutritious and tasty	95.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
907dad10-e38e-4af2-90fe-d41212bf51cd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Maharaja Masala Dosai	active	Royal dosa loaded with mixed vegetable masala, paneer and special spices	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
05893119-03f8-41ea-88c4-bd840e95c2ac	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mushroom Masala Dosai	active	Crispy dosa stuffed with savory mushroom masala filling	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9e20a739-67ac-4085-b5b0-1d3540deddde	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Paneer Masala Dosai	active	Crispy dosa filled with spiced cottage cheese masala, protein-rich and satisfying	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3abc05b6-c5ea-459f-b7b3-68a93ceb0ed3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Vegetable Masala Dosai	active	Crispy dosa stuffed with mixed vegetable masala curry	90.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0e0dbf1e-b47a-4db1-9c9b-4aa4500722eb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Venthaya Dosai With Vada Curry	active	Golden crispy lentil fritters made from urad dal, perfect accompaniment to sambar and chutney	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c7e79fd6-9cb0-4527-ba8a-09da1d2f918c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aappam	active	Soft lacy rice pancakes with crispy edges and fluffy center, perfect with vegetable stew or coconut milk	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8f8f3c91-2d26-4ded-9225-395ae9042f11	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Adai Aviyal	active	Protein-rich savory pancake made from mixed lentils and rice, served with aviyal and jaggery	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d571b7dc-eeb9-453d-bdfe-33c2ba653cdd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Banana Bajji	active	Sweet plantain slices coated in spiced gram flour batter and deep fried until golden	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
31f83c6b-72a9-4c79-b1e9-6bdef5b894e8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Keerai Vadai	active	Nutritious spinach and lentil fritters packed with greens, herbs and spices, crispy and healthy	50.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6b9f3fa5-d64a-4023-9f83-f0bf27bdb0e2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kuzhi Paniyaram	active	Savory rice dumplings made from fermented idly batter, crispy exterior with soft fluffy interior	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
27e673a4-366a-46f7-be9d-409e61e48a7b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Masala Vadai	active	Spiced lentil fritters made with chana dal, onions, curry leaves and spices, crispy outside and soft inside	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3dd5f85d-f466-479a-ad01-2f45c32fc196	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mixed Paniyaram	active	Savory rice dumplings made from fermented idly batter, crispy exterior with soft fluffy interior	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
564de578-2d66-4c50-8163-ab02b5a10663	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mysore Bonda	active	Spiced potato balls coated in gram flour batter and deep fried, crispy and delicious	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
42b8e3b1-90ca-416a-a471-1f851ad03abc	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Bajji	active	Crispy gram flour fritters with onion slices, perfect tea-time snack served with chutney	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b73de201-00ce-40ec-947c-f1159a500794	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Potato Bajji	active	Potato slices dipped in spiced chickpea batter and fried crispy, a popular evening snack	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e434f5a9-2005-4d7d-aa4e-051a7c10fa17	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Paniyaram	active	Sweet rice dumplings made from fermented batter with jaggery, crispy outside and soft inside	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ba8f6800-1286-42c7-b362-c24844b700ea	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vazhaipoo Vadai	active	Unique banana flower fritters combined with lentils and spices, a traditional Kerala delicacy	50.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2147a1de-ca25-43c4-adb1-7219bda6216f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Apple Juice	active	Fresh apple juice, crisp and refreshing	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9726018c-4bfc-472f-8033-bb15a844772d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ginger Lemon	active	Refreshing beverage to quench your thirst	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a08f430c-116b-4eb3-841d-d8d09c2f743c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Lemon Juice	active	Fresh lime juice with water and sugar, classic refresher	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3a3e183d-acd5-4e33-88e4-243fb0d99faf	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mathulai Juice	active	Fresh pomegranate juice, ruby red and nutritious	90.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mint Lemon	active	Refreshing beverage to quench your thirst	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
af6a1c14-e2af-435a-9a9d-bac3d66c35b7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mulam Juice	active	Fresh carrot juice, sweet and healthy	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
74f3ed80-98af-440a-a347-3f32e4be27aa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Orange Juice	active	Fresh orange juice, tangy and refreshing	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
72602fd8-2dd5-4d51-8280-4408e4a138a5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pineapple Juice	active	Fresh apple juice, crisp and refreshing	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
495c9a9e-6d98-440d-850d-3791071e4e95	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sathukudi Juice	active	Fresh sweet lime juice, mildly sweet and refreshing	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2f9da69e-71b4-4b2c-919e-1500bc55a630	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Watermelon Juice	active	Fresh watermelon juice, cooling and hydrating	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b4a855a2-bfa8-41ee-9173-998bee08316f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Black Coffee	active	Strong black coffee without milk, bold and energizing	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7249055c-e681-4d1f-ae2f-28c471a3af05	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Black Tea	active	Plain black tea without milk, strong and refreshing	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e440b879-0e0f-4692-8c4b-4b10c6d0cf01	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Boost	active	Nutritious malted health drink with milk, energy-boosting and tasty	50.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b7aefd26-9f98-454d-a476-ae7c9ce54387	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Coffee	active	Traditional South Indian filter coffee - strong decoction with frothy milk, aromatic and perfect	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2aa2f082-a408-4c05-b518-dd2ce8ad640b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paruthippaal	active	Traditional cotton seed milk, unique South Indian health drink	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c824e963-ab76-4ae7-af4b-8976832f6fec	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ginger Tea	active	Tea infused with fresh ginger, warming and soothing	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Green Tea	active	Healthy green tea rich in antioxidants, light and refreshing	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
846c440c-57b3-4d15-98e8-9d3ea4d01392	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Horlicks	active	Nutritious malted health drink with milk, energy-boosting and tasty	50.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5646f259-9143-4afe-823e-a993ad4c16ae	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Hot Badam Milk	active	Warm almond-flavored milk with nuts, nutritious and comforting	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c69dd883-7035-4781-92d5-e12b0b0bf97f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Karkandu Milk	active	Milk sweetened with rock sugar, cooling and soothing	50.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
da7f5c17-06eb-45e3-b48c-90ab6ae078f1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Lemon Honey Tea	active	Soothing tea with fresh lemon and honey, great for throat	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
63b03555-2ec3-4271-a8d5-43f8e1a92a6d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Milk	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5567dd12-02bc-47df-b4e6-88b58026bfa2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Nattusakkarai Coffee	active	Coffee sweetened with organic jaggery, natural and healthy	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
78ac9d50-be7c-4701-af65-e8e4ea0e2276	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Nattusakkarai Ginger Tea	active	Tea infused with fresh ginger, warming and soothing	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0c646133-3a61-494d-8779-db533c0980d5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Nattusakkarai Milk	active	Milk sweetened with organic jaggery, traditional and healthy	50.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6acecc37-452e-41cf-bbfa-fa29139985c1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Nattusakkarai Tea	active	Tea sweetened with natural jaggery, healthier alternative	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sukku Coffee	active	Traditional South Indian coffee with dry ginger, warming and therapeutic	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a7bbba94-e82b-4749-8101-c65fd8ff3449	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sukku Milk	active	Milk infused with dry ginger powder, warming and digestive	50.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c609e1c5-2949-4d3c-bfc3-b61c164c9192	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sukku Tea	active	Traditional tea with dry ginger powder, excellent for digestion	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tea	active	Classic Indian chai - black tea with milk, sugar and aromatic spices	35.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Scotch Ice Cream	active	Butterscotch flavored ice cream with caramel bits, crunchy and creamy	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b5394775-5207-4242-84c5-6917d840bc4c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Scotch Milk Shake	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
94063735-6495-4abf-91e3-e0eb80aa13b7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chocolate Ice Cream	active	Rich chocolate ice cream, classic and indulgent	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fa97e202-e534-4210-ac26-29a34f1f38fc	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chocolate Milk Shake	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bcb56064-a124-44a7-8649-79970c8b6758	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pista Ice Cream	active	Pistachio flavored ice cream with real nuts, aromatic and premium	90.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
64faab0b-643b-4a14-8c5d-c5718dd127b0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pista Milk Shake	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
89aee119-46f9-4a9b-afd7-6551885362ac	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Strawberry Ice Cream	active	Fresh strawberry ice cream, fruity and refreshing	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Strawberry Milk Shake	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e81df99b-a120-4110-8f48-0c5cbdbec19b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vanilla Ice Cream	active	Classic vanilla ice cream, smooth and timeless	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d5d5b1b0-97b5-42e8-ad5c-467225669d07	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vanilla Milk Shake	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7c954edb-f3b0-45b1-a0de-1b20a086d060	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aloo Gobi Masala	active	Cauliflower and potato curry cooked with aromatic spices and herbs	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9f608fd0-bde7-48da-a77f-c78ff68bd777	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aloo Parota	active	Flaky layered parotta served with flavorful potato kurma	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b460dc4d-a2a1-4ef3-bc68-172a30959cf4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Kulcha	active	Soft leavened bread brushed with butter, fluffy and delicious	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7ed15acb-1b78-444d-afb0-c9cabfd76b12	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Naan	active	Soft leavened flatbread brushed with butter, perfect with curries	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4ff69e50-609f-4f1e-a804-2d631ecc1b44	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Roti	active	Soft whole wheat flatbread brushed with butter or ghee, healthy and delicious	50.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b3520f26-f8cf-4933-aff2-1e8303f483d9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chappathi	active	Whole wheat flatbread, light and healthy, perfect with any curry	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ab6a60e1-0283-48dc-b606-544963dde3b5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chettinadu Vegetable Curry	active	Assorted seasonal vegetables in mildly spiced curry, wholesome and nutritious	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
892c73ce-28dd-4546-a0fc-cebb44769bd9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dhal Fry	active	Dry preparation of lentils tempered with spices, onions and tomatoes	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
da969ef4-1721-4442-a71d-3db403d42fe9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dhal Makani	active	Creamy black lentils slow-cooked with butter, cream and aromatic spices	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
34aeac9b-bdda-4d8f-bbc6-41a089862e6a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dhal Tadka	active	Yellow lentils tempered with cumin, garlic and ghee, comfort food classic	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f41a672d-54ff-457a-88ea-4a8427177b75	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Garlic Kulcha	active	Soft kulcha topped with garlic and herbs, aromatic accompaniment	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d318b34e-2e38-44fc-8583-a25e6633fe34	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Garlic Naan	active	Soft naan topped with garlic and butter, aromatic and flavorful	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0b90507a-d4ea-4f8f-908a-eca651ed29d6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Rice	active	Fragrant basmati rice cooked in pure ghee with whole spices, rich and aromatic	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
200af72d-ada6-4ad9-a2a9-8ac90c9ee26d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Gobi Masala	active	Cauliflower and potato curry cooked with aromatic spices and herbs	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a9fc938e-3eda-4477-9261-e13687c777fd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Green Peas Masala	active	Green peas cooked with spices in flavorful curry, simple and delicious	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d3a30467-6180-45d0-8f97-0516a39191e4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Jeera Rice	active	Fluffy basmati rice tempered with cumin seeds and ghee, simple yet elegant	95.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
89397364-5cd1-44ea-8ea7-68a8c0cc5fe6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kadaai Mushroom	active	Fresh mushrooms cooked in spicy onion-tomato gravy with aromatic spices	190.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3ea54e45-7aac-4cf2-b790-cf68417159f5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kadaai Paneer	active	Cottage cheese cooked with bell peppers, onions and tomatoes in kadai-style spicy gravy	210.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
aa5f3b2d-ae8a-40d2-81f0-68878ae09721	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kadaai Vegetable	active	Mixed vegetables cooked kadai-style with bell peppers and spicy tomato gravy	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fc885a0f-9531-475e-a49e-1aa26cecbb5e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kulcha	active	Soft leavened flatbread similar to naan, pairs well with curries	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8dde0f7e-7023-4469-9240-e9e428b1640c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mixed Vegetable Curry	active	Assorted seasonal vegetables in mildly spiced curry, wholesome and nutritious	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f163594e-9c10-4c15-8184-183411d6dcfa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Biryani	active	Aromatic rice layered with mushrooms, spices and herbs in traditional dum style	220.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c5618b42-8182-4dca-868d-edf91bbd5249	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Masala	active	Fresh mushrooms cooked in spicy onion-tomato gravy with aromatic spices	190.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a1514e63-efa6-4ab5-8068-aa531ddcc480	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Naan	active	Soft leavened flatbread baked in tandoor, classic North Indian bread	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
afbc58c3-c001-42cb-a2b9-01204baa60f6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mango Drink	active	Refreshing beverage to quench your thirst	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
80900d89-757f-45f1-8df1-574a5e4f38c7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Biryani	active	Fragrant basmati rice cooked with cottage cheese, aromatic spices, herbs and saffron	230.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b51b7764-5d21-47c2-aaa2-a54ef06e695b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Butter Masala	active	Cottage cheese cubes in rich creamy tomato gravy with butter and aromatic spices	220.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1e0d6501-b15a-4c5b-8856-e0668473540e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Tikka Masala	active	Marinated cottage cheese grilled in tandoor with peppers and onions, smoky and flavorful	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
db5f2886-4e5f-46e9-86ee-9eec449e4845	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Parota	active	Crispy flaky layered bread made from refined flour, South Indian favorite	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2cbd132b-f48c-4282-b637-eae87931d57c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pulka	active	Puffed whole wheat bread, soft and light, traditional accompaniment to curries	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
32bf89c1-cc50-4e3b-a578-7342f0a98052	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Roti	active	Whole wheat flatbread, light and healthy, perfect with any curry	45.00	3	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
53bbe15d-011a-453c-8c75-da4e0201bca0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Soy Chukka	active	Dry soya chunks preparation with South Indian spices, protein-rich side dish	170.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f4b8d658-d725-45fc-93b0-038fda5d7b3d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tandoori Parota	active	Flaky layered bread cooked in tandoor, crispy and aromatic	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
860edeb4-f127-4442-8362-7e0eb45d26ec	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tandoori Tikka Paneer	active	Marinated cottage cheese grilled in tandoor with peppers and onions, smoky and flavorful	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3aed2bdb-cc98-41f1-b690-f4665163a2eb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tandoori Tikka Soy	active	Marinated soya chunks grilled in tandoor with Indian spices	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8a60ac28-8785-495b-b891-7cb5e051043e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Stuffed Parota	active	Layered flatbread stuffed with spiced vegetables, complete meal in itself	75.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c3142cd7-e447-4ac7-a995-e49aa1c1c5fa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheat Parota	active	Multi-layered whole wheat flatbread, flaky and nutritious	55.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d0ce2e68-aff0-480b-b966-ee2de6d73e98	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Appalam	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
62643175-94cf-441a-8b44-dd4855b9d689	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Beeda	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ea5d0570-7042-4fa6-a6b3-c24833d2581f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Curd	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
733d05f9-efba-4218-b6aa-d0cd89bac606	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kootu	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
74727645-5f46-49e5-9644-3b3d73950cf4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Payasam	active	Traditional South Indian sweet pudding made with milk, jaggery and vermicelli or rice	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d880bd2d-f77b-4456-91fd-79e2f207f255	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Poriyal	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
445e368f-5795-4ecb-a085-0a1f7cba64d7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rasam	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
21f5887f-0d44-4145-9ea3-7bd6bbcd64e9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rice	active	Delicious dish prepared with fresh ingredients and authentic spices	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
444af49d-152e-4a78-8cf4-7b8a69d039c6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sambar	active	Delicious dish prepared with fresh ingredients and authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d8193183-10c9-42c9-bcc1-fc012e110627	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Meals	active	Traditional unlimited South Indian meal with rice, sambar, rasam, curries, served on banana leaf	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5553c740-38e4-43f3-898a-5d59b5a0320b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mini Meals	active	Smaller portion of traditional meal with rice, sambar, rasam, curries and accompaniments	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b1f7769a-5711-4944-b359-43a02ce6b82c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	North Indian Meals	active	North Indian complete meal with rice, dal, curries, raita, breads and sweet	250.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4502d2e6-f45f-4f50-b1cd-1f905e9cc518	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Meals	active	Premium unlimited meal with special curries, varieties and dessert on banana leaf	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0080a492-5c32-4048-9f36-95788b5271ce	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Capsicum Pizza	active	Pizza loaded with bell peppers, vegetables and cheese	240.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
559abe90-0de6-43d3-8dd2-932712b78a62	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cheese Pizza	active	Simple cheese pizza with tomato sauce and loads of mozzarella	220.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
dae5f7b5-abd0-4afd-ba03-739065d56b35	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Cheese Sandwich	active	Simple cheese sandwich with vegetables and sauces	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
59570f9a-8658-4f5c-b326-6bd30b07d043	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilly Cheese Sandwich	active	Spicy sandwich with cheese, chilies and vegetables	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
dbfda102-ce20-4cde-be8b-e8df65c9f7db	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Club Sandwich	active	Triple-decker sandwich with vegetables, cheese and sauces, hearty and filling	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
478355a4-a104-478a-9161-38812c682f28	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Grilled Sandwich	active	Grilled sandwich with vegetables and cheese, crispy and warm	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
dee24566-d8cf-46c2-8ea7-0ea7bcd982df	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Masala Sandwich	active	Sandwich with spiced potato filling and vegetables	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0009b8a7-676d-497b-92e5-1c9f19a6a9dc	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Pizza	active	Pizza topped with mushrooms, vegetables, herbs and mozzarella cheese	260.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
61592f67-7a2a-4060-8f95-6ff7aaf552a4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Sandwich	active	Sandwich with sautéed mushrooms, cheese and vegetables	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
32dce3db-9b6c-41de-ac5b-db2f1f7cf1b3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Pizza	active	Italian-style pizza topped with cottage cheese, vegetables, herbs and cheese	280.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c6c82907-0a2b-4424-8cff-e0d399e82e76	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Sandwich	active	Sandwich with spiced cottage cheese and vegetables	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e5b62ff6-5d19-4041-bce2-51eff5619079	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Punjabi Pizza	active	Fusion pizza with Punjabi-style spiced toppings and Indian flavors	280.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
37706f7f-3212-45bf-bbde-a9bd58d7d93b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Burger	active	Vegetable patty burger with fresh vegetables, cheese and sauces	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
dbc10961-9d8a-46f5-8635-d611caac9351	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Cutlet	active	Crispy vegetable cutlet made with potatoes, vegetables and spices	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
df1246cc-bae0-4d4e-8674-fb6af39b15bb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Pizza	active	Classic vegetable pizza with assorted veggies and cheese	240.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8449c926-5c66-43b3-9321-40108f2884a1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Sandwich	active	Fresh vegetable sandwich with chutneys and seasonings	100.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d78ace28-ecba-444b-b9de-cee545cef5fa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Curd Rice	active	Soothing rice mixed with yogurt, tempered with mustard, curry leaves and ginger, cooling and digestive	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f3245aa9-e6a6-408a-b9ac-a82c54845984	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Lemon Rice	active	Tangy rice seasoned with lemon juice, turmeric, peanuts and curry leaves, refreshing and light	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
29768ea2-2372-4fac-afa4-8025fe024c78	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sambar Rice	active	Steamed rice mixed with flavorful lentil-vegetable stew, wholesome one-pot meal	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4d6a444e-3a91-4914-a852-50c6748c5862	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tamarind Rice	active	Tangy rice flavored with tamarind paste, peanuts and aromatic South Indian spices	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3987c83b-d17b-47d0-86c9-2ca24d25f4ee	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tomato Rice	active	Mildly spiced rice cooked with tomatoes, herbs and warm spices, comforting and flavorful	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7ce551ca-251a-4082-b60c-f615b8f08c77	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Vegetable Biryani	active	Fragrant basmati rice cooked with mixed vegetables, aromatic spices and herbs	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8435ee66-9b87-47b6-9af4-0700ce6186fd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onam Sadhya	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ee0d0a1f-a784-4df7-9212-aa576b3ad098	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Delicious Grape	active	Refreshing beverage to quench your thirst	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1cffcfc9-cc80-4014-be79-9b20ddc76d9e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chilli Parota Fried	active	Shredded parotta tossed with vegetables in spicy chilli sauce, fusion favorite	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bee9a02e-7117-453f-aca2-8a99fb44d5c3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rose Falooda	active	Rose-flavored sweet drink with vermicelli, basil seeds and ice cream	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
88dc009b-c5b7-4978-800c-4a8202048808	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chocolate Falooda	active	Chocolate flavored falooda with vermicelli, ice cream and basil seeds	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
e9b3a60b-1ce7-4899-8831-11f827406d5e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Roast	active	Traditional South Indian delicacy	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
de10a61a-584a-4b95-91f1-bdf96a5eaeb3	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dry Fruit Mastani Falooda	active	Rich dessert drink with milk, ice cream, dry fruits and nuts	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
356bdd13-82cc-469a-8fd6-24e597857090	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Herbs Rice With Chilli Cauliflower	active	Crispy cauliflower florets tossed in spicy chilli sauce with peppers	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fac18465-28ba-445b-8706-1a10898fd2ad	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Herbs Noodles With Chilli Cauliflower	active	Fresh herb-flavored noodles with vegetables and aromatic seasonings	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
83e3428a-9624-4e01-9da7-ce22aa31ef65	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Rice With Chilli Mushroom	active	Stir-fried mushrooms in spicy chilli sauce with capsicum and onions	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
58e26d7a-ffac-41b9-a737-cfb6ec994ead	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Noodles With Chilli Mushroom	active	Stir-fried noodles with mushrooms and mixed vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
531b944e-619e-42a0-b734-5a30d57fa47c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Noodles With Mushroom Munchurian	active	Fiery Schezwan noodles loaded with mushrooms and spicy sauce	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8fcc6740-2404-4b3c-b7be-45c0be463f55	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Classic Veg Fried Rice With Pepper Mushroom	active	Wok-tossed rice with mushrooms, vegetables and aromatic spices	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
992b02e7-c182-4538-a8d0-0fb2137c76dc	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Classic Veg Noodles With Pepper Mushroom	active	Stir-fried noodles with mushrooms and mixed vegetables	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
97ec196e-cceb-46ec-ac63-c62595539b16	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Rice With Chilli Cauliflower	active	Crispy cauliflower florets tossed in spicy chilli sauce with peppers	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
178d2213-60e3-4cd7-85bb-8e22b99b6092	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burnt Garlic Noodles With Chilli Cauliflower	active	Aromatic noodles infused with crispy burnt garlic and vegetables	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5578ce19-d473-4631-bceb-3529208a9c1c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Manchow Rice With Chilli Mushroom	active	Stir-fried mushrooms in spicy chilli sauce with capsicum and onions	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fe289baf-6a53-4818-81a1-782090b7847d	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Schezwan Rice With Mushroom Munchurian	active	Flavorful rice preparation cooked to perfection	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
26ef163d-a3af-4fa2-a80a-edd775cbb216	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Shangai Rice With Cauliflower Munchurian	active	Flavorful rice preparation cooked to perfection	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
14522968-2fd2-49dd-85ed-98d7a3a54be5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Shangai Noodles With Cauliflower Munchurian	active	Classic hakka noodles stir-fried with fresh vegetables and sauces	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
addec80d-d00b-43b0-9b5e-356b6f03e0ba	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Manchow Noodles With Chilli Mushroom	active	Stir-fried noodles with mushrooms and mixed vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d20538d2-915a-442e-be5f-70cdb8aa98d2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Pepper And Salt	active	Delicious appetizer to begin your meal	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6164e6ee-b364-4c7c-aa62-091897b67081	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Buttermilk	active	Fresh dairy milk, pure and nutritious	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Momos	active	Cottage cheese dumplings served with spicy sauce, popular street food	140.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a0328182-d2b7-43e4-809e-8eb9e174005b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ebony	active	Refreshing palm fruit drink, cooling and unique	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a75a9442-6377-4684-8683-893cc195c342	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ivory	active	Cooling tender coconut-based beverage, naturally sweet	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f403036f-e8fd-453f-98c3-d7696e67a106	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Malai Kulfi	active	Creamy malai kulfi, rich and traditional frozen dessert	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
cf7e849a-85ae-4b70-b1d4-9f03c4c0c897	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Millet Dosai	active	Healthy dosa made from nutritious millet flour, crispy and wholesome	75.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Kesari	active	Sweet semolina pudding with ghee, sugar, cashews and cardamom, festival favorite	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
cf63f961-d290-435c-a2ff-26a52c42668a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Pulao	active	Fragrant basmati rice cooked with mushrooms, spices and herbs	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
543762be-87ca-4453-bc0e-d796cdb49468	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Pulao	active	Aromatic rice preparation with cottage cheese, vegetables and whole spices	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0e4d1341-be89-4026-9fc7-27ade0581b0f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Stuffed Kulcha	active	Kulcha stuffed with spiced potato or paneer filling	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
df6d9e7c-c3a1-4eb4-a96b-5cc1bbf63b28	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Stuffed Naan	active	Naan stuffed with spiced filling, hearty and satisfying	85.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b85124df-46c7-40cc-adb7-805d3eaf31b5	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kambu Koozh	active	Traditional fermented pearl millet porridge, cooling and nutritious	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
3f613c84-1af5-440d-a4b7-360d4a16bd63	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Lassi	active	Sweet yogurt-based drink, creamy and refreshing Punjabi beverage	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
44926a74-6f9a-463f-b299-9eda88ebaaa7	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ragi Koozh	active	Fermented finger millet porridge, rich in calcium and cooling	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b3a99f7d-c02c-4e12-a912-d321c59ae865	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Momos Platter	active	Assorted momos platter with steamed and fried varieties, served with multiple sauces	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1d691b66-954e-4867-9d81-8eea2b6eb667	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Burger Cutlet	active	Vegetable cutlet burger with lettuce, tomatoes and sauces	90.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0fdb6422-757a-459d-ad43-23543ffe4bfb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rose Kulfi	active	Rose-flavored kulfi, aromatic and refreshing Indian ice cream	65.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
878c91b8-4212-4329-bc67-60d136abb4f1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kara Kozhukattai	active	Savory steamed rice dumplings with spiced lentil filling, traditional South Indian snack	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0dac449c-636e-44d5-ab72-eeac8052f70a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Pasunthi	active	Traditional herbal drink, cooling and medicinal	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
135b1582-0468-4070-9c91-fda08116d3cb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rasamalai	active	Soft cottage cheese dumplings in sweet thickened milk with saffron and cardamom	70.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8f2bbc56-0ba0-4d25-85a1-b1941234b95f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Black Forest Cake 	active	Classic Black Forest cake (1kg) with chocolate, cherry and cream layers	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b465a967-aaa5-47bf-9239-9b496b63d66a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Cream Butterscocth Cake 	active	Single piece of fresh cream cake	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
52850cd6-d674-43fe-9c1a-a0a148a18ae8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Butter Cream Chocolate Cake	active	Single slice of chocolate buttercream cake	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
199d709f-8ea0-43f2-8b3f-eb4d389d1042	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Chocolate Truffle Cake	active	Rich chocolate truffle cake (1kg), decadent and indulgent	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
b444bc41-4bb0-4110-be04-0d286487041e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Blackcurrent Cake	active	Fresh cream cake (1kg) with blackcurrant fruit flavor	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f7ef8034-f74d-42d5-a631-e92d106f4dd0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Butterscotch Cake	active	Fresh cream butterscotch cake (1kg) with caramel bits	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
22e1c682-dbe2-4839-86dc-8d47125fa4b6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Mango Cake	active	Fresh cream mango cake (1kg), tropical and delicious	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9400f238-0457-4883-ad18-6a6b645277e8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Orange Cake	active	Fresh cream orange cake (1kg) with citrus flavor	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
194cd19e-fd2e-4e4c-8964-a24886ed04a8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Pineapple Cake	active	Fresh cream pineapple cake (1kg), classic favorite	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c32aa732-a66a-4828-8bcd-a63cb7bff676	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Fresh Cream Strawberry Cake	active	Fresh cream strawberry cake (1kg) with fresh fruit	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c0ca83a0-7b7f-44fa-81b2-da82fac41eee	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Rainbow Cake	active	Colorful rainbow cake (1kg) with multiple vibrant layers	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fa0609aa-5f55-490f-9bb8-26f66d8870d6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Red Velvet Cake	active	Red velvet cake (1kg) with cream cheese frosting, elegant and delicious	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c36d0d21-f428-41d8-9deb-6dda00bfc260	6eb89f66-661c-4294-85b4-044519fdec1b	\N	White Forest Cake	active	White forest cake (1kg) with vanilla, cherry and white chocolate	650.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fdb20829-c90a-47f4-98c8-95b4682c0740	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Mini Puff	active	Bite-sized vegetable puff, perfect tea-time snack	30.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ae6f5b04-c9d4-4e4b-8d39-17734093addd	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Puff	active	Flaky puff pastry filled with spiced vegetable mixture	35.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
97bd0f73-7ee2-48dd-abfa-09c7753dc12c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Puff	active	Sweet flaky pastry filled with jam or cream	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
70c5863a-aef9-4592-970e-9aae14a18687	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Panner Roll Puff	active	Flaky puff pastry filled with spiced cottage cheese	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
961b398d-db41-481b-9cc4-c7986a2722de	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Mushroom Puff	active	Crispy puff pastry with spiced mushroom filling	45.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
43f7d824-cf0d-42e1-b819-7d7479db89be	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Fried Peri Peri Momos	active	Four fried vegetable momos tossed in zesty peri peri spice	90.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
40633d5a-6b1a-4d89-b124-12150e904a1a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Fried Peri Peri Momos	active	Six crispy fried vegetable momos with fiery peri peri coating	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0a180055-c1d9-4d42-b344-d7593601da8c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Fried Momos	active	Four crispy fried momos stuffed with vegetables	90.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
614c9539-b9ba-440d-a170-4b9f51e15d47	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Fried Momos	active	Six golden fried vegetable dumplings served with tangy sauce	130.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2241f9b6-28a8-4f2f-8d71-a678485a9f9a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Fried Peri Peri Momos	active	Four crispy fried paneer momos with tangy peri peri spice	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6a0dd8bc-58de-47a6-8965-b3789c26af78	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Fried Peri Peri Momos	active	Six crispy fried paneer momos tossed in spicy peri peri seasoning	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
4775bce7-7719-4bea-8c12-0d77f29b97e6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Fried Momos	active	Four crispy fried paneer dumplings, Indo-Chinese favorite	110.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7a0a920e-b87e-4d6f-948d-cbae1152f4e6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Fried Momos	active	Six golden fried cottage cheese dumplings served with spicy sauce	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
0d9ecc80-994a-4c15-a1a0-9b1794178170	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Dragon Paneer + Lemon Juice	active	Combo meal with Indo-Chinese starter and refreshing fresh juice	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
de254fc5-4f3f-4f96-8c3d-99c2b9e50ba1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Honey Chilli Paneer + Lemon Juice	active	Sweet and spicy cottage cheese tossed with honey, capsicum and onions in Chinese sauce	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2d593c56-cbda-4743-a2eb-7e1d3e6e20ab	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Tandoori Tikka Paneer + Lemon Juice	active	Marinated cottage cheese grilled in tandoor with peppers and onions, smoky and flavorful	40.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
85afe928-267f-4407-8d28-ff3050657f6e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mixed Fried Rice + Paneer 651	active	Stir-fried rice with cottage cheese cubes, vegetables and soy-based seasoning	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5df84a57-775a-484c-99e0-8e835002136b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mixed Noodles + Paneer 651	active	Hakka noodles tossed with cottage cheese cubes and crisp vegetables	180.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	hot	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
29f6fa6d-4615-4bfe-a397-c022ff9da6a0	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheat Veg Puff	active	Flaky whole wheat pastry with spiced vegetable filling, healthier option	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
198c3575-5f88-4dae-ba7a-62228de49786	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aloo Peas Masala	active	Green peas cooked with spices in flavorful curry, simple and delicious	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
93e71daf-8b70-43ab-b90f-1b6ddaae29de	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Paneer Peas Masala	active	Spiced cottage cheese curry cooked with onions, tomatoes and aromatic Indian spices	200.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
9b978bf0-4011-40ea-9652-2c9fa5206ba6	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheat Chilli Parota	active	Wheat parotta pieces tossed in spicy sauce with vegetables, fusion dish	120.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
fc70e8e0-f228-41ec-bdf6-64670531a7a4	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Pongal	active	Traditional sweet rice pudding cooked with moong dal, jaggery, ghee, cashews and cardamom, a festive delight	60.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8351ca74-0e99-40de-b002-07c11aeb6310	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Ghee Chappathi	active	Soft whole wheat flatbread brushed with butter or ghee, healthy and delicious	50.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
cd4eb692-ef70-4a72-9714-3de375eefdaf	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Sweet Bread	active	Sweet bread loaf, soft and mildly sweet	30.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1239093d-96ed-4ba5-a8fa-880415cd4f95	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheelocity Breakfast	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
ef1e9112-3119-4056-b090-3a33a5177dfa	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheelocity Lunch	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1b550734-244c-4690-82d6-f0d208ace1e9	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Wheelocity Dinner	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
f0bf6b79-e92e-4c97-83bd-0e7ca50ebb21	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Onion Samosa	active	Crispy pastry filled with spiced onion stuffing, popular evening snack	45.00	2	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	mild	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1c09cd8c-42a6-46ea-9012-c2384e14888c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Veg Roll	active	Vegetables wrapped in soft parotta or roti, portable street food	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
140b2eeb-8a4b-4ff0-a0c4-f49c4359da21	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Boiled Millet	active	Healthy millet-based preparation, nutritious and wholesome	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2206ea8c-f2a1-451e-9459-a2cf64a49834	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Choco Chip Cookies	active	Crunchy chocolate chip cookies, perfect with tea or coffee	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
29add6f6-967c-4751-8ae5-839feafaeacb	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Choco Chip Muffin	active	Soft chocolate chip muffin, perfect tea-time treat	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
31cc85e8-1169-45c8-a8b9-53538b4f2dff	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Veggie Ribbon Noodles	active	Premium mixed noodles loaded with assorted vegetables and protein	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7d48f0b6-c447-4df1-aeb8-65dda435d11f	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mushroom Ribbon Noodles	active	Wide ribbon noodles wok-tossed with mushrooms and sauces	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2e3f87a1-4cf4-401f-b98d-2b308232adf8	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Paneer Ribbon Noodles	active	Flat ribbon noodles stir-fried with paneer and vegetables	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6fa74f7b-29ad-48de-b78b-d1222d6dd7d1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Special Mixed Ribbon Noodles	active	Premium mixed noodles loaded with assorted vegetables and protein	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
7fe30758-442d-4866-9718-87f891523ece	6eb89f66-661c-4294-85b4-044519fdec1b	\N	White Channa	active	White chickpeas curry in mildly spiced gravy, protein-rich and wholesome	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
6bdc30f9-3749-4b11-9eee-d57bdc90135a	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Black Channa	active	Black chickpeas in spicy curry, nutritious and flavorful North Indian dish	160.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
2d9ab94e-0d56-430f-a034-3b49db6da031	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Indo Chinese Thali	active	Wholesome main course dish prepared with authentic spices	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
bb8e4681-419d-45d0-a8ed-001457b83a8e	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Milk Kova Bun	active	Fresh dairy milk based bread roll, pure and nutritious	40.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
c0d7deb2-37cd-4269-b335-a34d3b38ecb2	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Kids Thali	active	Wholesome main course dish prepared with authentic spices in small portions	150.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	medium	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
998ee5c0-cd53-4db4-befc-851c1b703f7b	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Rose Milk	active	Sweet rose-flavored milk drink, cooling and refreshing	80.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
1555fa16-107b-4d37-b844-8467ad706a65	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Nannari Juice	active	Traditional South Indian sarsaparilla root drink, cooling and refreshing	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
54c0db7b-d22a-49d6-b27d-a40d7722ca31	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Mini Jigardhanda	active	Famous Madurai cooling drink with milk, almond gum and ice cream, sweet and refreshing	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
61553ec6-3eb4-43e0-85ac-b41756946a58	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Mango Drink	active	Refreshing mango beverage to quench your thirst	60.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Ilaneer Payasam	active	Tender coconut payasam, unique and refreshing South Indian dessert	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
a156e08b-2e02-4e4b-9ea8-82e9921061c1	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Cold Coffee	active	Chilled coffee beverage with milk and ice, refreshing and energizing	80.00	1	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
8acb9f4c-25ef-44d4-8ff2-21b28d883997	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Badam Gheer	active	Rich almond-based sweet drink, thick and creamy traditional beverage	150.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
d1974a06-a43f-4fde-8bb9-771bf9617c92	6eb89f66-661c-4294-85b4-044519fdec1b	\N	Aswins Amla Juice	active	Vitamin C rich Indian gooseberry juice, immunity booster with tangy taste	70.00	250	f	f	30	\N	\N	\N	\N	0.00	\N	0	f	f	f	t	f	f	none	\N	\N	f	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	\N	f	\N	\N
\.


--
-- TOC entry 5413 (class 0 OID 19382)
-- Dependencies: 282
-- Data for Name: menu_item_addon_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_addon_group (menu_item_addon_group_id, restaurant_id, menu_item_addon_group_name, menu_item_addon_group_rank, menu_item_addon_group_status, menu_item_addon_group_selection_min, menu_item_addon_group_selection_max, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5414 (class 0 OID 19392)
-- Dependencies: 283
-- Data for Name: menu_item_addon_item; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_addon_item (menu_item_addon_id, menu_item_addon_group_id, restaurant_id, menu_item_addon_item_name, menu_item_addon_item_price, menu_item_addon_item_status, menu_item_addon_item_rank, menu_item_addon_item_attribute_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5415 (class 0 OID 19402)
-- Dependencies: 284
-- Data for Name: menu_item_addon_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_addon_mapping (menu_item_addon_mapping_id, menu_item_id, menu_item_variation_id, menu_item_addon_group_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5499 (class 0 OID 21592)
-- Dependencies: 368
-- Data for Name: menu_item_allergen_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_allergen_mapping (mapping_id, menu_item_id, allergen_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5416 (class 0 OID 19412)
-- Dependencies: 285
-- Data for Name: menu_item_attribute; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_attribute (menu_item_attribute_id, menu_item_attribute_name, menu_item_attribute_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5417 (class 0 OID 19422)
-- Dependencies: 286
-- Data for Name: menu_item_availability_schedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_availability_schedule (schedule_id, menu_item_id, day_of_week, time_from, time_to, is_available, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted, meal_type_id) FROM stdin;
c6798a5c-b6d2-4d2c-a60c-fee548ba8791	d1974a06-a43f-4fde-8bb9-771bf9617c92	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d9f03826-3c4d-4c83-b638-e044defb7aec	8acb9f4c-25ef-44d4-8ff2-21b28d883997	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
6a7a32d8-4f25-463f-925b-0ef564d73916	a156e08b-2e02-4e4b-9ea8-82e9921061c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
6de3fad8-e177-45b4-a6a0-407c831f8a0d	5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
01edcef2-d399-4c20-b02b-e3733df91d4f	61553ec6-3eb4-43e0-85ac-b41756946a58	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
13de5dc9-cb90-4788-baab-e6ed8d687a93	54c0db7b-d22a-49d6-b27d-a40d7722ca31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
41e745b2-113f-46d6-a6d2-fbec600deeb9	1555fa16-107b-4d37-b844-8467ad706a65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d7b9ae95-37b4-43a8-9672-78e82763b240	998ee5c0-cd53-4db4-befc-851c1b703f7b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
600b966c-0387-4084-9029-ad6059d35329	bb8e4681-419d-45d0-a8ed-001457b83a8e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a7dae9fc-9a0a-4b54-8ef4-2bb0a4b857c3	6bdc30f9-3749-4b11-9eee-d57bdc90135a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
66a2fddf-75cb-4ae8-9770-33e81221f13a	7fe30758-442d-4866-9718-87f891523ece	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
fac15aba-056e-4735-94da-007cf2d40a15	29add6f6-967c-4751-8ae5-839feafaeacb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ef63f9c7-ac1a-44a0-8818-f5a2072be1fd	2206ea8c-f2a1-451e-9459-a2cf64a49834	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
17547524-4a99-4915-a46e-c9ab4e56320a	f0bf6b79-e92e-4c97-83bd-0e7ca50ebb21	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
aeb54a0b-7e12-4cce-b1d6-d2f8ae1aafd9	1239093d-96ed-4ba5-a8fa-880415cd4f95	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
252c6163-2abe-44b6-a48f-94b12cb3fc87	cd4eb692-ef70-4a72-9714-3de375eefdaf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9bc76735-0370-4442-8864-302a8cadb6c1	fc70e8e0-f228-41ec-bdf6-64670531a7a4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
78482a50-d959-4bff-a139-542812d71de5	4775bce7-7719-4bea-8c12-0d77f29b97e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d54182e0-642b-41ee-861a-db7d21193832	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
15b9e330-4875-4ce7-b61f-2c7c6488fca3	4775bce7-7719-4bea-8c12-0d77f29b97e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
258b1198-0cb6-43c7-8bc2-4b22ce65b01f	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
fabe3887-ca16-4525-9f26-c3b5cb22883e	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2542a3ed-86b8-48fb-a013-a392f3dd1a2a	6a0dd8bc-58de-47a6-8965-b3789c26af78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f736dc9e-694e-4657-8f71-7ea6b8be006e	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d7fab7e6-f07c-4f19-96f2-7820fc0f43a2	6a0dd8bc-58de-47a6-8965-b3789c26af78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
34529788-d316-44d4-97e9-74f4cfb7da0c	0a180055-c1d9-4d42-b344-d7593601da8c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8fe0dbcf-7883-48aa-b73f-b78d50ebd750	614c9539-b9ba-440d-a170-4b9f51e15d47	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
56c67ace-294e-41a9-9e53-fea4b6685cca	0a180055-c1d9-4d42-b344-d7593601da8c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c517b390-9ff7-4d02-a021-57937dce1edc	614c9539-b9ba-440d-a170-4b9f51e15d47	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c0fcc804-dd7f-470d-96f4-8aa471a83399	43f7d824-cf0d-42e1-b819-7d7479db89be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8d4e1cc2-753c-4396-b79a-696ea90ce46a	40633d5a-6b1a-4d89-b124-12150e904a1a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3b7570ae-78e7-4736-a55f-3d737826790b	43f7d824-cf0d-42e1-b819-7d7479db89be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3aac65ed-a9b2-4346-98e9-7346392554b7	40633d5a-6b1a-4d89-b124-12150e904a1a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5cd3576c-dbc1-4673-a88b-596bd51207ac	c36d0d21-f428-41d8-9deb-6dda00bfc260	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4db5e5b9-67a8-4ac0-8912-8f118f2a2c31	fa0609aa-5f55-490f-9bb8-26f66d8870d6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ee891774-7b21-4329-8bcb-ecc7669ca5e9	c0ca83a0-7b7f-44fa-81b2-da82fac41eee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0faf0f34-bfc5-42e2-9db4-06a3b0126d17	c32aa732-a66a-4828-8bcd-a63cb7bff676	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7f1c96e8-4bb1-4a2f-8646-6e52911dc799	194cd19e-fd2e-4e4c-8964-a24886ed04a8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f9f77f9d-7242-4b4c-b92c-d1f729c155b5	9400f238-0457-4883-ad18-6a6b645277e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7db4e64b-c06d-44c9-aeb8-f6bcf3016960	22e1c682-dbe2-4839-86dc-8d47125fa4b6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d628b2f1-61bc-448a-a8f0-513a69cfad4f	f7ef8034-f74d-42d5-a631-e92d106f4dd0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b162fe65-0f56-4fa6-aef6-db528aca9d7e	b444bc41-4bb0-4110-be04-0d286487041e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c8ce39ce-012a-4d98-8804-147f0fbb3b1f	199d709f-8ea0-43f2-8b3f-eb4d389d1042	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
79c3d197-0c48-4c1e-a0bc-7303e8ffc1bf	52850cd6-d674-43fe-9c1a-a0a148a18ae8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b756c74f-9cb7-4fe1-a9a3-035fd2c5eb11	b465a967-aaa5-47bf-9239-9b496b63d66a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
99301b29-c524-4784-8e6d-567a01bbd5b3	8f2bbc56-0ba0-4d25-85a1-b1941234b95f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d32c4abc-d218-4cdf-a926-99bb8d90e7af	135b1582-0468-4070-9c91-fda08116d3cb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
743768ca-5d8b-4214-8b50-098132a27b8f	0dac449c-636e-44d5-ab72-eeac8052f70a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
30f35c30-3ade-411b-9ac2-6137510132f7	0fdb6422-757a-459d-ad43-23543ffe4bfb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
994cca85-2269-45b7-963a-02dbecfde180	1d691b66-954e-4867-9d81-8eea2b6eb667	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
00710a18-54e5-4de2-b2eb-1b5a1fe444e5	44926a74-6f9a-463f-b299-9eda88ebaaa7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
e19e208a-6270-479e-9028-e38f0b96457d	3f613c84-1af5-440d-a4b7-360d4a16bd63	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
1ed221af-bcaf-4162-a23e-141d5a669c29	b85124df-46c7-40cc-adb7-805d3eaf31b5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3bff0ee2-61fc-4d52-a577-1f257b366349	5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
47437340-a9e4-4d24-a101-8f8eef3a0a67	cf7e849a-85ae-4b70-b1d4-9f03c4c0c897	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a2da9a36-1d09-45d4-aa0d-df1b26b2f4af	f403036f-e8fd-453f-98c3-d7696e67a106	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4cec0f20-dc43-47fa-bdee-2c59e57d4115	a75a9442-6377-4684-8683-893cc195c342	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a1043ac2-0f2c-4dff-a3ab-8f02936bb15a	a0328182-d2b7-43e4-809e-8eb9e174005b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
e46f20d6-05ba-4ae5-b14d-9dc99cb09a8b	afbc58c3-c001-42cb-a2b9-01204baa60f6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
356aeeab-8ae2-4ec1-b8d9-65919d2e1e6b	8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a03be381-a439-4719-8af2-4b66c95a7822	6164e6ee-b364-4c7c-aa62-091897b67081	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
90da4fc2-f592-498f-91b0-a145c24953ee	de10a61a-584a-4b95-91f1-bdf96a5eaeb3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
04a7644c-df67-4069-b2b7-ace8be2de656	e9b3a60b-1ce7-4899-8831-11f827406d5e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
12ecc497-7379-4c28-8f9a-2c3da29910f6	88dc009b-c5b7-4978-800c-4a8202048808	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b0185be7-a980-471f-a125-69dc0e0e240b	bee9a02e-7117-453f-aca2-8a99fb44d5c3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f3c008bb-10a9-407e-ad2b-1eca8b85ab9a	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2497d028-dda3-4aa0-8925-4647f05f4acf	ee0d0a1f-a784-4df7-9212-aa576b3ad098	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
867751e6-f4c7-4fe6-a1fa-7f33edbaf7bd	8449c926-5c66-43b3-9321-40108f2884a1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9ed4c477-6fad-4e65-af88-e422bf5fc834	dbc10961-9d8a-46f5-8635-d611caac9351	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
afc87b35-20da-408a-8326-de8226271ce7	37706f7f-3212-45bf-bbde-a9bd58d7d93b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f69517b9-8de7-46e7-8fe8-bc1f7ffa05dc	c6c82907-0a2b-4424-8cff-e0d399e82e76	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0dc8f317-eae6-404c-9884-c519b04edf46	61592f67-7a2a-4060-8f95-6ff7aaf552a4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
62dad78b-99ee-4163-a8c8-4b26d95421b8	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9c108e09-061f-4223-864f-074f02681dec	478355a4-a104-478a-9161-38812c682f28	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
11a6b4fa-3f6b-427c-a2a6-760a61045d39	dbfda102-ce20-4cde-be8b-e8df65c9f7db	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d064237b-471e-411f-93d9-fe8c8b91c06a	59570f9a-8658-4f5c-b326-6bd30b07d043	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3fce786c-abd1-4ce3-b366-85bb7eb63cfe	dae5f7b5-abd0-4afd-ba03-739065d56b35	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
987dbed7-5376-48a9-b9cf-ff2a5cd5de96	444af49d-152e-4a78-8cf4-7b8a69d039c6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
47f2a0d2-e6bf-4b56-ac97-b5446d0bdedc	d5d5b1b0-97b5-42e8-ad5c-467225669d07	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d157e623-8a88-4da2-b0e5-b7c4bee25f88	e81df99b-a120-4110-8f48-0c5cbdbec19b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
dec318f7-2558-4b0d-8b63-c0e8f790aa9f	4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a9c2ed3b-77f3-4f17-af3a-d285dcfd106b	89aee119-46f9-4a9b-afd7-6551885362ac	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
593480a9-ac32-478d-8c3d-6717e673e307	64faab0b-643b-4a14-8c5d-c5718dd127b0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
80836263-cf6f-4213-9afa-1c017cd1a83b	bcb56064-a124-44a7-8649-79970c8b6758	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
881654ea-4a3b-4010-affc-57aeb0a184c5	fa97e202-e534-4210-ac26-29a34f1f38fc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8f0de558-854b-4626-9a40-1afbfae66fd7	94063735-6495-4abf-91e3-e0eb80aa13b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ce8f4ebf-51cd-4d88-8172-5d80ab1aaca2	b5394775-5207-4242-84c5-6917d840bc4c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
1febc6cd-227b-4719-9b71-7be3481f8864	461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f3f6891a-58b1-4ff7-bf63-49ddedb54310	3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b6d7ce54-5f2a-44aa-9c4d-9a1d86d6faa0	c609e1c5-2949-4d3c-bfc3-b61c164c9192	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c251e1c9-21eb-4f59-b5be-eb045901de5d	a7bbba94-e82b-4749-8101-c65fd8ff3449	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2f8d0b2e-a5be-4571-99d6-005725e60d37	521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0b122fcf-18b9-44de-acc0-d02e4a4d6069	6acecc37-452e-41cf-bbfa-fa29139985c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ce7a1d69-b5f8-4cad-81af-52d49c0b2210	0c646133-3a61-494d-8779-db533c0980d5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ad03cc54-6fba-451f-ab15-cc603969d33b	78ac9d50-be7c-4701-af65-e8e4ea0e2276	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
63a39945-1071-4c6a-9cfc-03cbb4ce994e	5567dd12-02bc-47df-b4e6-88b58026bfa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2ed05078-7175-48b1-bb87-b154297fe5dd	63b03555-2ec3-4271-a8d5-43f8e1a92a6d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
04f344f2-45f6-4716-900a-0c8f7368d47e	da7f5c17-06eb-45e3-b48c-90ab6ae078f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c9d74879-29c2-4174-b929-46c43e8812d5	c69dd883-7035-4781-92d5-e12b0b0bf97f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4b32c1d5-645e-4557-a56d-78c656222fe0	5646f259-9143-4afe-823e-a993ad4c16ae	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
eaec859c-1e61-4a1c-8025-9b473473ccd6	846c440c-57b3-4d15-98e8-9d3ea4d01392	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
64d1e38f-8aaf-45af-ae91-54066990e894	a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
24aadea0-7e20-415d-aa4e-e0a11af2133c	c824e963-ab76-4ae7-af4b-8976832f6fec	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
62605eab-0b12-473b-bb44-ba15fbb4cdd3	2aa2f082-a408-4c05-b518-dd2ce8ad640b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
85273f9a-b01e-4890-8a35-bd16cf88281e	b7aefd26-9f98-454d-a476-ae7c9ce54387	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8b821b81-99be-44d6-92d7-463f13cdab9b	e440b879-0e0f-4692-8c4b-4b10c6d0cf01	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8bbab5af-1d71-4811-b896-df4ae6d1551c	7249055c-e681-4d1f-ae2f-28c471a3af05	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d6b21f77-1582-4cd0-b03a-63c9e350cd52	b4a855a2-bfa8-41ee-9173-998bee08316f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
37e191fb-30f0-4265-b31f-4d592954d30a	2f9da69e-71b4-4b2c-919e-1500bc55a630	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5ec09f5c-cc25-40de-aaf5-cdb061ec903d	495c9a9e-6d98-440d-850d-3791071e4e95	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
44975949-6deb-446e-82d1-3c3bd6d1cb78	72602fd8-2dd5-4d51-8280-4408e4a138a5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
143de3ed-3361-49c8-b2d2-9f82ced661b2	74f3ed80-98af-440a-a347-3f32e4be27aa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9472e984-536d-4f96-9a75-b1a4f6a325b0	af6a1c14-e2af-435a-9a9d-bac3d66c35b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
75b79821-221a-401f-9116-d23d3c2cd4e8	c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
572aa8f1-c35c-434e-a223-f59a1a541978	3a3e183d-acd5-4e33-88e4-243fb0d99faf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4bee16cd-1bb2-4889-b1eb-26e17871d24d	a08f430c-116b-4eb3-841d-d8d09c2f743c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
32147336-472f-493b-bbf3-0914806c9c55	9726018c-4bfc-472f-8033-bb15a844772d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
91279916-3129-4121-b22b-982aee8c3cba	2147a1de-ca25-43c4-adb1-7219bda6216f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
48fb1f0a-7545-45c9-a5f3-beb7f8e4ca11	e434f5a9-2005-4d7d-aa4e-051a7c10fa17	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0f114bc8-0f7e-4e31-8afa-1f34a711ae3a	564de578-2d66-4c50-8163-ab02b5a10663	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
1b0fe290-fd08-4317-a067-0519e30e2349	3dd5f85d-f466-479a-ad01-2f45c32fc196	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
eb1d8685-3111-4d3f-b53e-505af832fc4d	27e673a4-366a-46f7-be9d-409e61e48a7b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
12c271c6-4bb0-4573-afd8-c863eba5cd90	6b9f3fa5-d64a-4023-9f83-f0bf27bdb0e2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9995eea3-fb6d-4406-886e-4f90f8a997a6	31f83c6b-72a9-4c79-b1e9-6bdef5b894e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
1875751a-05ef-494a-adcf-5332fec6e542	0aaa74f5-6f91-4b5d-9dd3-5b7ed925964e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7f6577ec-5601-44b7-b5ea-5da3d91ba397	8f8f3c91-2d26-4ded-9225-395ae9042f11	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b7f6f2f6-376e-432c-a9f6-c2dd721faf84	c7e79fd6-9cb0-4527-ba8a-09da1d2f918c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b1a40614-64ec-41a5-b682-c1b1fd61b63b	0e0dbf1e-b47a-4db1-9c9b-4aa4500722eb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a8a20b67-dcc3-40bc-8d56-d622f2097e7c	3abc05b6-c5ea-459f-b7b3-68a93ceb0ed3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2b194ef2-db09-4e7b-97c7-1b892cf05c6b	9e20a739-67ac-4085-b5b0-1d3540deddde	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
01cf3880-1c67-4f80-9e7e-5b5be5eca052	05893119-03f8-41ea-88c4-bd840e95c2ac	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8113a716-b3ba-4bcd-bc16-69da860f26ee	907dad10-e38e-4af2-90fe-d41212bf51cd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2b44376c-4022-4eb3-93b4-71a9ae44f979	b73cb807-821d-4f6e-8c71-78b5c5310bed	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
e6b7b2c8-2ac0-417d-8a59-589d36cc5e34	888933f7-ca51-41b1-90d9-45ceed3a99ca	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5f76fbfe-8e3c-4649-b962-1f5637fde158	17639dfd-b136-44c4-9284-232bdc865000	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
443ecdda-2456-44a4-8743-eeb862f81236	f7112f63-6f6d-4a33-9362-d4ffafcf339b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3e3e0502-fc78-4c0e-9872-050276d74945	bf821156-45fe-4ab3-a13e-8d7aab0d3869	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f475aa81-2056-4b83-98b9-011f68f85b69	842e1d5a-feda-4096-ae06-5bf538545e31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7ba041a7-db18-49a1-9e3b-921674ffcd36	2c88e468-33fb-4346-a92b-b514a7e3797b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a813ec34-fa6a-4f87-a4b9-ae19d12089e8	197d1458-b83a-455c-8db5-267a616501a7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
2229b0cb-0e7b-48ea-b3a9-252959b5d510	10bef495-7255-4638-bdfb-7b8df9c37423	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
238aaac9-acb6-4e61-a1af-c18e79b2298f	936473d2-bdc9-4727-92d1-6e8762ad2b65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d6b29305-da4a-44f2-835d-b8da154f667f	5073e567-0d72-4e94-b697-79e1cd408def	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c3fbf698-4b93-4670-bfdf-06e67f02f344	b15d206c-d5ef-4d69-b660-1f06272c10e4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a6771059-d33d-4a33-bb88-b074dbbc19ba	70afac5e-7487-494c-9737-9ba5323e9a7e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
06eae265-38dd-44c1-b1a3-f966659d9719	28c1d342-6d69-4c31-8afd-693ac1d32db5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
90866bd0-01b4-4975-88ce-7d68623057e7	a4e76dd4-4d79-44f4-96c6-fc4eb6391677	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
e2eed44c-eb96-44ec-9c21-d88e11425e85	68d16bc7-866e-41e2-9f90-79086232128f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
83297efa-d5b7-47c2-b2eb-7ae5c6a80e91	ac156f84-4748-4ce8-a4f6-4bb26b4839a9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
938233b9-6d2a-4de5-bc54-d7e56c607f83	dd5dbea6-ee71-47b6-b10e-cd736d5988aa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
be99f570-63b8-42b2-b39d-9abb3a8857d3	44d0cc09-3bd3-4408-a54b-fa2840a6d5f3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
66be6ac5-b355-4c1c-837d-436adec8fd72	83070134-6fdd-4816-b2a3-6c37e96e22fe	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7b304a76-11c2-42a4-9804-5eb5cb30d547	20dd1625-14f7-477f-8f1c-5c929edb9956	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f39d186b-a18e-465e-aaa2-7e498bb0ba31	b76156d6-7d71-47c8-aa45-a951287ebd9b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
9939d7e8-b886-417a-b103-d13b4c7e78e5	531f9c5f-5fce-4446-bfe8-ce270e4f629c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
3f4858fa-8b0a-4982-96cf-3841f2b37e0c	52f4509d-b071-4aa4-930e-e01e97e4302f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
95e377cc-4914-4a3e-92a9-afa0f63cfd0c	409b244f-7dfb-4c7b-8686-a079379ded1c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c4cf7af3-8248-446e-9466-342a87e8751a	17bb19b4-e16b-4a51-8531-b7da9cbff8f0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
256e1048-4c6e-45d5-8854-bd89c1f0ac69	baaaefc8-3ba7-414d-ace8-650ade2f98db	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
cbfe5f21-6776-4905-952e-068f18a7c5a0	0b171841-6ee4-4fc5-8ac9-2b19d4a2c65d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4f2c419a-7022-4bb5-9b2e-50af5b6fcf48	cf42f76f-bfc1-410f-8cd2-f6b1a32f94e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f0ea4260-ab89-4d4b-aa6f-460554f1f009	458c8f44-4178-4ad1-82aa-e1fafd1df65c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
078d4ce0-2089-47e9-88bd-31de7f9b08a6	1c1054e1-1106-4a8b-8230-f9bbe7b2e4d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a275b65c-5392-4a62-9b35-123f888674a4	18a6da15-b4b6-4225-b473-c5c0eeddd5ce	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5ac6b8bf-1437-4b46-a7ad-82f45073d828	957c1e64-7e5a-4c17-8f27-1a4944de6a3c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f0b43b41-f389-44de-af73-e08313f15c64	feca6731-d1ec-48de-952a-aba8ad404db3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5e431316-ae52-4f95-b455-7a0242476d26	199afe79-6431-46a4-a0a1-1add114881ef	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ad9ed1db-57ae-42d3-bb37-e799740595d9	29de49e9-c12d-4c5f-9de6-18aac4973fa5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4ecccb6c-ab8d-47e9-b521-a4d7071d66ac	a658600f-95be-4f25-aaa5-e0cc280ec8ba	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
03e04135-6438-4410-8f4e-8489ab3cc1ca	b3584fe8-58b9-4eed-9daf-81af7c5c2597	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
da779d98-cf4f-477a-8d08-36e632914c38	f5e1ea70-3e91-4df5-9c55-9669c9e62872	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
fa267615-f2ed-4679-867e-50a38b16700f	acff3dd5-e388-4060-b2f7-38fd24021c68	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b890bfc7-407f-4d43-9b6a-78c43bcc6115	a172152e-4a5c-439b-bb67-8c41414bb799	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f7aabb05-4fa9-4fd0-8eda-e149294d9085	1461d06d-72a8-46b5-8090-b0bad1c2646a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
bbff212d-c404-4ef9-abcc-80210394b28c	1f3c418f-548c-4aeb-99c1-86f784f1c9e1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
48223075-037a-41a4-9386-7f7778125fa4	b3e70ef0-d8b4-42af-80c4-8ee78031befd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
e8741603-b408-4103-a4f3-05b8e2352f1e	28ef3fa2-c237-4c93-b411-82f0001e6492	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4dc7b47b-84a9-4629-a500-b677e901e6f5	1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
4da5bf6f-7f06-41f7-931c-151cebf5cefe	ccfd7416-c0a3-4329-a4c1-a95603e27da6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
ebf0f217-c40a-402d-9cce-fae3685d5b55	2abf9654-d5e5-490e-b96f-0b7b2b426283	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
f6205804-c001-4192-856b-dd80600b021b	8f2d8131-94a6-4331-841e-1031150bd63e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b16d1061-24eb-4484-92e4-f74e26c2fcda	9c2ddc01-f7c7-4451-a595-d665830b062a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
c44608e4-5dde-4871-8381-25475921abaa	c30a6a90-4ce5-4917-9e62-4972d4e1ee19	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a9ef5fff-d699-4baf-b137-7b16104cd6e4	12c9297b-83ec-4782-b024-46edad03e261	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
6162ef95-d64a-4210-912f-387f34368fda	e31406b2-d66e-44ab-bff0-73fba95ad51e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
95e19ac8-2ddb-4299-9d50-814ad884a4fb	299f9d53-9f76-4c85-a2bc-337d53055cd2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d4359707-0bb4-4bfc-a5a5-fb72a5c32639	006c6e95-b04b-4bc1-9bc6-68202e92d1af	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
73cef813-b62a-4315-b2de-364700125dd4	b269c7ba-3584-49b4-b3c2-09c4a390688e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
beab1bee-effb-4c36-8f7c-75fcf577ac98	544e1530-13e3-4a9f-8186-1889b0004c40	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
114434ec-1d63-4e96-bb37-fd28fa7fc556	8b78ab34-c265-4577-9c86-21a4d09cdc52	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
12ee59a1-3cec-4977-821d-85ec5088f43b	c92904fa-2ba8-4e5d-9abc-73d3ce7a66bb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
acc5f9fc-7c2f-48ab-8194-75196a1fff87	3953ae28-900d-42b9-92c3-6b97102aada0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8a148cc5-b9a9-4f33-853e-a068814f2e79	42917c7d-09af-4ae7-91a9-3b65b0c654a3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5dff9165-ce7a-4d0f-b76d-4bc6dd20790f	27afa12a-791f-495f-91be-dce580504f4c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
40ed5405-a9e0-4755-8725-862b6bce8116	60b5673e-9d4a-41b1-8383-05932a7395ae	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
a0c52d4e-3831-4d1d-9ba9-199aa3f9337b	44cc830b-0ae9-4aa0-a2ed-57ac80e0b4fb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
244a1ff5-4241-4d2e-a9f5-2a7a67671e1d	278a9ee5-f497-4297-a6cb-e8f8e9ca9faf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
379b796a-beb7-404d-9c01-9b2d30010240	a66b87c2-03a2-47e8-a9da-37904dbe30b9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
b1c4b7f1-001d-463d-98d3-223ad1f9fb0f	57c06b53-155f-4b54-b420-a4605b0badc8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
7d7d169d-a37c-45f8-ae57-7c95490f5683	f4abc59c-b7de-4de0-9e12-bcbb3a7fa1f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0bf81870-8bd4-4e6e-b96c-eb7af88e2221	eff3d4e3-726b-4170-9d2e-5894b0a70ad5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
5fb92705-975d-4ae5-9b4e-19b2ba19f956	a2a30d42-28a9-4050-b157-0227e4a539c5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
444a7983-8ef6-4e9d-b221-b4b54d2c2414	bdc6318f-5da2-4907-bab4-cf4838d80988	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
8e4333c5-a390-4b02-94dc-3125a059365a	4d7a637f-1360-458e-95da-d4bb74c5c99c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
1637fd82-d1c7-4d2e-9f09-db47acc81aee	9d63daef-e702-4908-9df5-d54c07335256	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
24efd7a6-11ec-4573-8314-2810e9d6e992	3f32641e-2154-45f9-ba9b-4840865e04d5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
6123878d-f4ec-4092-af26-68125aaa8293	18d0f888-ae4a-4071-a6be-ab7e467c6472	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
92ebcfbb-3076-41cc-aaf4-97d2c0a5fb2a	a601a7f8-5d30-4347-bb02-94526f4f413a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
0004f84d-26c4-444f-bb52-6cf121d2595e	010c83a6-d7e3-4f48-880e-c85137fb39e2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
d12f4172-66b8-4698-b3b2-3439449cb651	d1974a06-a43f-4fde-8bb9-771bf9617c92	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ed9cce5d-6da4-4dff-9827-716e7aaa9454	8acb9f4c-25ef-44d4-8ff2-21b28d883997	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3018eaad-7d6e-4d82-98fc-f8bb7db8513e	a156e08b-2e02-4e4b-9ea8-82e9921061c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8624810d-e295-48c4-bd6b-1cdb395568ff	5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a8a7a4af-a9b9-4cc6-a78c-11bcef3d58bb	61553ec6-3eb4-43e0-85ac-b41756946a58	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b224ff66-2e81-4257-addd-295b9ca35dd0	54c0db7b-d22a-49d6-b27d-a40d7722ca31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b11e7a96-e84a-43fb-8fe8-2803c630ef8b	1555fa16-107b-4d37-b844-8467ad706a65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4c2ccb56-caac-43f8-9fa0-887113d47b69	998ee5c0-cd53-4db4-befc-851c1b703f7b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
266caefa-cd7a-45e6-a275-330425f55a3f	c0d7deb2-37cd-4269-b335-a34d3b38ecb2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8adede9b-c16e-49eb-bd5c-d295da4cdf75	bb8e4681-419d-45d0-a8ed-001457b83a8e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
bf848a9c-5751-4f3f-9409-79f6aab06431	2d9ab94e-0d56-430f-a034-3b49db6da031	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
00a6b7fa-1954-4cf8-b641-addd72c29452	6bdc30f9-3749-4b11-9eee-d57bdc90135a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fdd2e6c4-2b9f-4ae3-9ca4-5ab8e55d6e36	7fe30758-442d-4866-9718-87f891523ece	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9af0871e-a50f-43cf-86ce-04f4b6f46c36	6fa74f7b-29ad-48de-b78b-d1222d6dd7d1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
496ac246-1e83-45da-a95b-5258afe7a9c5	2e3f87a1-4cf4-401f-b98d-2b308232adf8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0e20076b-30a0-4e08-81a6-10fabaa1f333	7d48f0b6-c447-4df1-aeb8-65dda435d11f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
807b8a9a-ee24-4de8-9532-add13fb71202	31cc85e8-1169-45c8-a8b9-53538b4f2dff	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2fb36da9-a462-41e6-b8d3-7fcea3da1c04	29add6f6-967c-4751-8ae5-839feafaeacb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
856b688d-5ba5-4bd8-93f6-9b44d4cae214	2206ea8c-f2a1-451e-9459-a2cf64a49834	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
31311b88-09ff-49fa-b0b2-b5fa7acb0858	140b2eeb-8a4b-4ff0-a0c4-f49c4359da21	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
29ca7d85-7632-423f-aec4-2d2fca3155d0	1c09cd8c-42a6-46ea-9012-c2384e14888c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
241a846a-f29d-49f3-997a-64e991f70787	ef1e9112-3119-4056-b090-3a33a5177dfa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
04e690e6-d6b9-4503-b2f9-d39e37b1017b	cd4eb692-ef70-4a72-9714-3de375eefdaf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
673fdd9f-a123-4484-b263-fb4377a8c95e	8351ca74-0e99-40de-b002-07c11aeb6310	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b6de61ce-f2c9-4405-a4dc-42b226374f50	9b978bf0-4011-40ea-9652-2c9fa5206ba6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
99620fb6-8659-4768-bafc-e2f1a6c51b30	93e71daf-8b70-43ab-b90f-1b6ddaae29de	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
893dc121-9666-4c07-9764-b5c79500b08d	198c3575-5f88-4dae-ba7a-62228de49786	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e0557d40-3061-4304-bcbc-3a7644d1e574	5df84a57-775a-484c-99e0-8e835002136b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
988d190e-cb2e-4ebb-bbaf-670f89774ac7	85afe928-267f-4407-8d28-ff3050657f6e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5b1caa33-e011-49d7-b0d0-cc364fb2fbd1	2d593c56-cbda-4743-a2eb-7e1d3e6e20ab	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9df4da56-0214-4c8f-9fb2-269d7ac018bc	de254fc5-4f3f-4f96-8c3d-99c2b9e50ba1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
22b6d8ca-fe12-4223-8be8-d04339088de4	0d9ecc80-994a-4c15-a1a0-9b1794178170	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d5dee9ff-ce0d-47f9-9a97-8996b66d2edf	c36d0d21-f428-41d8-9deb-6dda00bfc260	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d5205501-b105-4e07-8645-328d6d5fcc5a	fa0609aa-5f55-490f-9bb8-26f66d8870d6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c5ddda08-f5b7-4d19-8be3-7ebf7622c8c5	c0ca83a0-7b7f-44fa-81b2-da82fac41eee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8c3c4469-6834-458b-80f8-f6e2657a12e9	c32aa732-a66a-4828-8bcd-a63cb7bff676	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
28847d84-9ff6-44bb-b9a6-135127c845d7	194cd19e-fd2e-4e4c-8964-a24886ed04a8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5aa7d33c-e804-409f-9e5a-55ad99358ca0	9400f238-0457-4883-ad18-6a6b645277e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
dbdac4b2-5fb2-4414-8e09-fce69de16c10	22e1c682-dbe2-4839-86dc-8d47125fa4b6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ee3600e9-44aa-45b8-8b5c-e46ab859c3fa	f7ef8034-f74d-42d5-a631-e92d106f4dd0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4e40cf02-2528-48d1-aa84-766d210dc6ed	b444bc41-4bb0-4110-be04-0d286487041e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4a54d434-0519-458c-a22b-00ca0aa506c8	199d709f-8ea0-43f2-8b3f-eb4d389d1042	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4039d6af-7155-4a86-98f3-9f0c1ee2b612	52850cd6-d674-43fe-9c1a-a0a148a18ae8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2f7fb76b-8bb1-4b99-9c0b-3127a25bc907	b465a967-aaa5-47bf-9239-9b496b63d66a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b7034e48-6182-4363-94f0-16d6557852ed	8f2bbc56-0ba0-4d25-85a1-b1941234b95f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c89deceb-3734-440c-a893-b061727e9416	135b1582-0468-4070-9c91-fda08116d3cb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
83ba9b1d-c621-4ce0-8e75-c767b5b69a16	0dac449c-636e-44d5-ab72-eeac8052f70a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3b9247f8-0c23-429f-9a8f-642a04213d6a	878c91b8-4212-4329-bc67-60d136abb4f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d9afcf58-129d-4b3c-a755-941c7b726e2c	0fdb6422-757a-459d-ad43-23543ffe4bfb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
06321faf-f07e-45a7-bd62-897ca5eedb77	1d691b66-954e-4867-9d81-8eea2b6eb667	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d86a35f3-8adb-4643-918b-090ff2f5624b	44926a74-6f9a-463f-b299-9eda88ebaaa7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9b665f49-f9d7-4ee4-adc2-b6267fa50fef	3f613c84-1af5-440d-a4b7-360d4a16bd63	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
dcc1b1d8-7402-42f0-83d7-1fd4ea0bf6c5	b85124df-46c7-40cc-adb7-805d3eaf31b5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
14ebc230-39de-4761-9f60-cc4b80c575fa	df6d9e7c-c3a1-4eb4-a96b-5cc1bbf63b28	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f93dfbed-dbe8-4c9a-bd68-3abcdc135c2c	0e4d1341-be89-4026-9fc7-27ade0581b0f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
81adf317-88e5-4838-bc01-70544a9d6d27	543762be-87ca-4453-bc0e-d796cdb49468	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3f3cda11-ff3b-4d78-a880-423a7f945bd4	cf63f961-d290-435c-a2ff-26a52c42668a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
540d9775-138a-429d-81b6-58d04bf413c3	5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e6ee9aec-ea96-428e-9681-d22f1099cb0b	f403036f-e8fd-453f-98c3-d7696e67a106	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
1588bc01-07a5-4200-87fc-4de41e659b82	a75a9442-6377-4684-8683-893cc195c342	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f349b64c-e06e-4cac-a994-08b1fae10293	a0328182-d2b7-43e4-809e-8eb9e174005b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4ff6a88a-53c3-481f-93eb-861924ad3d54	afbc58c3-c001-42cb-a2b9-01204baa60f6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7ce50b20-b87d-46b1-84c9-f7fb6a683de6	8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4f007ca3-2b03-43ed-8ca3-a13acb89f2a8	6164e6ee-b364-4c7c-aa62-091897b67081	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8cea82e8-e9d0-48c2-be4b-65544bcd8b02	d20538d2-915a-442e-be5f-70cdb8aa98d2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a3607ea1-88b3-45b7-83e9-0d773c37188b	addec80d-d00b-43b0-9b5e-356b6f03e0ba	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2547502a-183c-47e5-a472-4ac6fd5d2c48	14522968-2fd2-49dd-85ed-98d7a3a54be5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ed9e11c1-e89c-4768-9e32-bee04d71ccdd	26ef163d-a3af-4fa2-a80a-edd775cbb216	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a95a7399-07a6-45ea-83da-89ccbb1c4fda	fe289baf-6a53-4818-81a1-782090b7847d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b44a6788-5f0d-4ca9-b448-db120153f9cd	5578ce19-d473-4631-bceb-3529208a9c1c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
669ef58d-dd43-4cda-8508-12eaa685ed36	178d2213-60e3-4cd7-85bb-8e22b99b6092	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9d0bec11-bf4b-4db3-bdb6-13ab3aa5dc40	97ec196e-cceb-46ec-ac63-c62595539b16	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
06d85785-3909-4e79-a19e-2c855bbe59c7	992b02e7-c182-4538-a8d0-0fb2137c76dc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
41455aca-e48d-4f21-be6f-b18481d525de	8fcc6740-2404-4b3c-b7be-45c0be463f55	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b68ed787-50f2-43bf-8734-65664dfefadf	531b944e-619e-42a0-b734-5a30d57fa47c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
76895ae1-3596-44fe-8f6e-3588cb448677	58e26d7a-ffac-41b9-a737-cfb6ec994ead	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f885c719-464a-437c-8ec1-f9ac7033e110	83e3428a-9624-4e01-9da7-ce22aa31ef65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fe68ff22-e0be-4f98-b258-3c81e6650de1	fac18465-28ba-445b-8706-1a10898fd2ad	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2a7d7287-1099-4b07-813a-014b19574473	356bdd13-82cc-469a-8fd6-24e597857090	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
52b60120-d9c5-4c8b-ae1f-f1751447da98	de10a61a-584a-4b95-91f1-bdf96a5eaeb3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a349963d-3f5f-49a8-a813-3a9113e99268	88dc009b-c5b7-4978-800c-4a8202048808	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8057da50-3823-46d8-a89b-69291fb86220	bee9a02e-7117-453f-aca2-8a99fb44d5c3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4bbde4df-c00d-48d8-a65d-85f7119ad37b	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5da76138-d08c-44a3-a3f9-3441c6a6d559	ee0d0a1f-a784-4df7-9212-aa576b3ad098	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5272ea59-d1ae-4834-a0a8-d190502405b2	8435ee66-9b87-47b6-9af4-0700ce6186fd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
cf6c6876-4e84-4ed5-81fa-f5b795b42684	7ce551ca-251a-4082-b60c-f615b8f08c77	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
279eb5f4-5b20-4701-afe6-1d7626cfab6c	3987c83b-d17b-47d0-86c9-2ca24d25f4ee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
81f03041-1db6-4793-ae2d-65e45a6da1c1	4d6a444e-3a91-4914-a852-50c6748c5862	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
73aca785-a78e-4953-a5b0-3b74200f5717	29768ea2-2372-4fac-afa4-8025fe024c78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ef9e5e22-db40-4bad-b319-8a1df7ae8009	f3245aa9-e6a6-408a-b9ac-a82c54845984	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
17f8b86d-5e6a-419d-8f2c-8740fb352434	d78ace28-ecba-444b-b9de-cee545cef5fa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0a87e54e-c1d0-47ec-9727-a72587ee5b1b	8449c926-5c66-43b3-9321-40108f2884a1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a8ecb1ca-ad37-400a-89ae-b76906602a3d	df1246cc-bae0-4d4e-8674-fb6af39b15bb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c9563afb-c04a-45cd-9c16-d478af71c182	dbc10961-9d8a-46f5-8635-d611caac9351	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ad041481-1138-46ec-987b-8ebd9e0405fa	37706f7f-3212-45bf-bbde-a9bd58d7d93b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5fcd8967-2a1f-403d-862d-3b28a7e4a23a	e5b62ff6-5d19-4041-bce2-51eff5619079	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5c88616d-c4ba-4d6c-9996-c390f71adec5	c6c82907-0a2b-4424-8cff-e0d399e82e76	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
aafd9129-80ed-4ffa-8d93-289a1d921765	32dce3db-9b6c-41de-ac5b-db2f1f7cf1b3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2a11190b-0f46-4c11-a1ff-869ae6cec65e	61592f67-7a2a-4060-8f95-6ff7aaf552a4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6dbe63af-6939-4767-a28c-3827d5ab973e	0009b8a7-676d-497b-92e5-1c9f19a6a9dc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
74ad84c6-6f25-4aac-8011-12f409999d93	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5798a3f9-cdc7-4246-aff6-c354cb83ea69	478355a4-a104-478a-9161-38812c682f28	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2880b415-bf34-4219-87e3-ddacb415ecfd	dbfda102-ce20-4cde-be8b-e8df65c9f7db	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
831d8b82-fc20-43ec-b91c-e2e4c829474e	59570f9a-8658-4f5c-b326-6bd30b07d043	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5fc9bb95-ad28-4ee9-8294-86439f5ac98d	dae5f7b5-abd0-4afd-ba03-739065d56b35	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
09f16ffc-8800-4a39-b7a4-17ae1dbd9cdd	559abe90-0de6-43d3-8dd2-932712b78a62	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6fe88b55-f74b-43a6-8402-b1c167fd1063	0080a492-5c32-4048-9f36-95788b5271ce	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
503197a5-854f-450e-8ecc-2accfc9b3228	4502d2e6-f45f-4f50-b1cd-1f905e9cc518	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c952ef81-dd5f-4352-8e4e-f9e67fa00d1e	b1f7769a-5711-4944-b359-43a02ce6b82c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6e44698c-f911-46cf-ac9e-3b04795eb1ba	5553c740-38e4-43f3-898a-5d59b5a0320b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0398008e-1be8-4de1-8154-f73e8802131e	d8193183-10c9-42c9-bcc1-fc012e110627	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8532c0db-8d21-4e4c-b94c-82ae69a99425	444af49d-152e-4a78-8cf4-7b8a69d039c6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4bdac9bc-6eaa-417e-b294-1fdb92222192	21f5887f-0d44-4145-9ea3-7bd6bbcd64e9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ca8dd9c3-29e1-430a-96e2-809bf3135937	445e368f-5795-4ecb-a085-0a1f7cba64d7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c975a6db-8295-4ae1-a7e2-94687396c0a5	d880bd2d-f77b-4456-91fd-79e2f207f255	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3700a228-d778-47d7-b919-fbdd7261f53d	74727645-5f46-49e5-9644-3b3d73950cf4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a22d3512-30d0-4b1f-bee7-dc16e42ec3c9	733d05f9-efba-4218-b6aa-d0cd89bac606	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d6cc55fd-171c-46c8-b8aa-568c1a925f9d	ea5d0570-7042-4fa6-a6b3-c24833d2581f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0673b6a1-d370-48cd-ab0e-a3cf718a12e4	62643175-94cf-441a-8b44-dd4855b9d689	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
28555534-6bb8-4c82-96dc-17898c3fa931	d0ce2e68-aff0-480b-b966-ee2de6d73e98	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
406ae27f-52df-47fa-90dc-26f35302eb8e	c3142cd7-e447-4ac7-a995-e49aa1c1c5fa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
dcfb64d4-8232-4f31-aea1-612c0cf49111	8a60ac28-8785-495b-b891-7cb5e051043e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
025292a8-5ef8-404e-8baa-122c7b007b28	3aed2bdb-cc98-41f1-b690-f4665163a2eb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8818ef1c-bc34-4aaa-b39d-b47ae30b32e1	860edeb4-f127-4442-8362-7e0eb45d26ec	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
adb2edd0-f057-4964-8e04-f200cff8be99	f4b8d658-d725-45fc-93b0-038fda5d7b3d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
31e27af5-a57f-4a14-9218-a756cbe02cda	53bbe15d-011a-453c-8c75-da4e0201bca0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
575868fa-a1eb-433c-89f0-42f2892c1a65	32bf89c1-cc50-4e3b-a578-7342f0a98052	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9502759c-114f-4508-8370-dd40a2977bf5	2cbd132b-f48c-4282-b637-eae87931d57c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e064693a-cace-44ba-b0c7-e2bdbeae884e	db5f2886-4e5f-46e9-86ee-9eec449e4845	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
289e002e-ecdc-4209-be1d-70703d75cc5e	1e0d6501-b15a-4c5b-8856-e0668473540e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3e929d56-91d2-4567-bbac-5e82040e94ac	b51b7764-5d21-47c2-aaa2-a54ef06e695b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f30af9d0-f545-44ce-8777-a564b46c08ba	80900d89-757f-45f1-8df1-574a5e4f38c7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
05432754-315b-4597-b10c-006e404623a3	a1514e63-efa6-4ab5-8068-aa531ddcc480	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
89f65cc7-22d8-451c-827e-5c3d5603b298	c5618b42-8182-4dca-868d-edf91bbd5249	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
4551491f-6cef-4937-bd9f-acd499f347e9	f163594e-9c10-4c15-8184-183411d6dcfa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fa9a440e-b79f-4fdd-b38e-ce321525bcc7	8dde0f7e-7023-4469-9240-e9e428b1640c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
93e51228-badd-4cca-a616-bc4b39d39a44	fc885a0f-9531-475e-a49e-1aa26cecbb5e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6417ddac-8020-41b0-873b-9b6f0da7cb5d	aa5f3b2d-ae8a-40d2-81f0-68878ae09721	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b477997d-f81c-4d79-b2e4-11bd3e1d774e	3ea54e45-7aac-4cf2-b790-cf68417159f5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b37617c0-05af-4f78-b38d-e7664b079e2c	89397364-5cd1-44ea-8ea7-68a8c0cc5fe6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
80d6b133-d5ac-4dd9-aba5-f6f129ba8d0e	d3a30467-6180-45d0-8f97-0516a39191e4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a6dc47f9-76c2-4416-bcf6-857e7ef71971	a9fc938e-3eda-4477-9261-e13687c777fd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d93b2b88-7614-47a3-8ac6-083c306d0369	200af72d-ada6-4ad9-a2a9-8ac90c9ee26d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
04aee762-3dbc-4ff4-bde4-40e6d5f2fcfa	0b90507a-d4ea-4f8f-908a-eca651ed29d6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
55a18eed-046a-48ba-878f-063caffb2247	d318b34e-2e38-44fc-8583-a25e6633fe34	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
53ef4e59-5206-4457-9ac9-9dd0b6272173	f41a672d-54ff-457a-88ea-4a8427177b75	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fcca26a9-184e-4a0d-9b40-b371cae791fb	34aeac9b-bdda-4d8f-bbc6-41a089862e6a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d8b362a0-b56f-461b-bbf3-3f3c273a19f3	da969ef4-1721-4442-a71d-3db403d42fe9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ff6109ab-8094-4570-ac7a-d94201fceaf2	892c73ce-28dd-4546-a0fc-cebb44769bd9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3912313f-e0a8-4d4f-b3f1-f7763d267805	ab6a60e1-0283-48dc-b606-544963dde3b5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b069d40d-7d20-4263-92d4-4eaf1f9d2a14	b3520f26-f8cf-4933-aff2-1e8303f483d9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
48e12853-bb4d-49ca-bce8-e41190a40f9b	4ff69e50-609f-4f1e-a804-2d631ecc1b44	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c1330d7f-78e0-4300-903b-d726b2040383	7ed15acb-1b78-444d-afb0-c9cabfd76b12	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a189f9a7-ad0f-44ff-a46d-b44f1464ec6b	b460dc4d-a2a1-4ef3-bc68-172a30959cf4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c2c5738b-b0f0-4c5d-96da-35bb28371245	9f608fd0-bde7-48da-a77f-c78ff68bd777	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c0b2c3f9-5e51-4122-9571-007cd732423b	7c954edb-f3b0-45b1-a0de-1b20a086d060	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3d5043bc-fee9-41f6-80ec-63b814a44601	d5d5b1b0-97b5-42e8-ad5c-467225669d07	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9fcf50bf-1ee2-4ec0-a35b-087421b2274e	e81df99b-a120-4110-8f48-0c5cbdbec19b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7465d4ce-4294-4831-a842-7bf1dded74fd	4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
cd59cb4c-63b7-4ba8-8e6f-86c96bf72057	89aee119-46f9-4a9b-afd7-6551885362ac	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6a6f500e-a7a4-49d9-a4a0-1b56b4a8c286	64faab0b-643b-4a14-8c5d-c5718dd127b0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0ee9518b-727d-430d-8506-21fdf7bdbaf1	bcb56064-a124-44a7-8649-79970c8b6758	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
73b1d5c1-605e-48af-9f26-50dd6b07943e	fa97e202-e534-4210-ac26-29a34f1f38fc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7e962e4c-650a-49f3-9898-1758b19b1362	94063735-6495-4abf-91e3-e0eb80aa13b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ceed0b0b-50cf-4d85-80a2-957b1ced88f1	b5394775-5207-4242-84c5-6917d840bc4c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
50eef998-fd1b-4e3a-bc0d-2be9f354af4c	461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0a07ed5c-68e6-4044-8b6b-bc21496e4d9e	3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c9bac4d6-1013-418a-b6e5-51a412e76c70	c609e1c5-2949-4d3c-bfc3-b61c164c9192	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
be2ce878-337b-49b9-af4d-7709f0d67755	a7bbba94-e82b-4749-8101-c65fd8ff3449	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
579aefe6-c010-4afb-bbe3-47887e0b0a8b	521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
dcaa425c-cdec-4c2c-9203-c196d37fbd1e	6acecc37-452e-41cf-bbfa-fa29139985c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
1b3f821a-807f-44b0-a8aa-c347357c059b	0c646133-3a61-494d-8779-db533c0980d5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
1ddcb532-3ae7-41fb-84ca-23a4108f56eb	78ac9d50-be7c-4701-af65-e8e4ea0e2276	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
15fa2412-b5ef-481a-83c1-1743d8c7e6e3	5567dd12-02bc-47df-b4e6-88b58026bfa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d609a863-916e-461d-bb29-1b1ca4114e4a	63b03555-2ec3-4271-a8d5-43f8e1a92a6d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
a127f114-4e23-483b-90b4-00cd6db7c6d4	da7f5c17-06eb-45e3-b48c-90ab6ae078f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
753ba0cf-5805-4fa5-9f68-117deb103037	c69dd883-7035-4781-92d5-e12b0b0bf97f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c921f8d8-2b71-4df2-8be5-e6eea7eb79d8	5646f259-9143-4afe-823e-a993ad4c16ae	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7ff706ec-a230-4916-bfe4-24732a8267c6	846c440c-57b3-4d15-98e8-9d3ea4d01392	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
020ba545-ed3f-43fa-9bfd-0ccf258e509d	a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
41156627-70f9-4f4d-9afc-e649cf92e502	c824e963-ab76-4ae7-af4b-8976832f6fec	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e80dea61-bbc5-486a-a116-f4b92571d3a5	2aa2f082-a408-4c05-b518-dd2ce8ad640b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3d7bfaef-4fdf-4d50-81f5-af3e48c134ec	b7aefd26-9f98-454d-a476-ae7c9ce54387	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
582f3b3b-45c0-4f8f-bcdf-8fe55481f0a2	e440b879-0e0f-4692-8c4b-4b10c6d0cf01	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f83aa6d0-f0d7-49dd-9873-90e081010d7a	7249055c-e681-4d1f-ae2f-28c471a3af05	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0fc1c93e-55a4-44c9-a3a3-74a384212245	b4a855a2-bfa8-41ee-9173-998bee08316f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f575ec50-3400-4b70-949e-d4f989d95482	2f9da69e-71b4-4b2c-919e-1500bc55a630	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f497600e-281e-4d40-9209-4520595d7bbd	495c9a9e-6d98-440d-850d-3791071e4e95	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
dbaafacb-3108-4693-aba6-1fb725a2c2ad	72602fd8-2dd5-4d51-8280-4408e4a138a5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ec292b8c-207e-4bf8-9f94-afa25b4fe2d6	74f3ed80-98af-440a-a347-3f32e4be27aa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ff5b8ce3-b8b9-4a1a-bcaf-ef380625e000	af6a1c14-e2af-435a-9a9d-bac3d66c35b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
63d9b25b-f5c0-402f-88d7-0183ace2697a	c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
1c4865ea-cfe7-4ba4-8297-ccd09cc8f559	3a3e183d-acd5-4e33-88e4-243fb0d99faf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7bb89722-c885-4510-af21-7af7c5ed755a	a08f430c-116b-4eb3-841d-d8d09c2f743c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0941e8f4-57b5-43a7-8469-9c9f701189ca	9726018c-4bfc-472f-8033-bb15a844772d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3b7ae017-e2c8-4c13-b5eb-d2918eb540e4	2147a1de-ca25-43c4-adb1-7219bda6216f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
56fd284c-0812-4698-a006-1df750c31f80	70afac5e-7487-494c-9737-9ba5323e9a7e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f521a88c-361a-4a8a-a54a-8eb94c2c8e06	089157e1-3de5-4c32-9c69-6445d78edc1f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
49d6b535-e531-4480-a57c-88e69bbc1bc9	74e0df2b-4c04-4518-b484-d6425e13ea74	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b884d704-0515-4b4c-91a3-bf5f9ca391ee	41fd61ae-6fe9-42b0-9c0e-4818f153ffa0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
111b2170-df8a-4374-b81c-72f835744c9a	a0ebae73-9f25-48b3-8fd5-b05ba844d222	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e984c8e5-7ba9-40c1-b91d-21c2110a2099	199afe79-6431-46a4-a0a1-1add114881ef	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
346eb241-d25f-4377-a310-544f5dea0d45	29de49e9-c12d-4c5f-9de6-18aac4973fa5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c3e50f75-f05b-43fa-b017-769659923b53	30c26e10-38c4-4254-aa2e-0d42f352c023	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6c7f8671-eaa3-49f0-a9df-6fc2fc6ffa50	43301ae3-93ac-4bb3-b023-dd39d37de9f6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
db6aced7-9868-427b-aa74-052d5cbe58be	1021ee4c-7743-4e51-a5a4-164a2ea3d842	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
48e100d1-f2ec-4ccc-aab6-15fcf8422e5b	efb317af-7eac-4f9f-8f63-7883c2982ede	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
03a7ae6c-f8a7-4e90-a319-d59615aae9e9	9ad814cd-f7ba-4d29-a113-805dbc651c60	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
781e3d6a-45cd-4de8-b11f-31ce8841d162	3b91dfb2-fd88-45f2-928f-0c9a02394b62	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e886afb5-3926-4841-becf-dca2a70e0906	82657f8f-f8ad-49ec-bc2b-bb8fa993f67d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d03201d3-2f56-48a9-b455-64bc325436a5	b128ec84-8ee0-470c-a38c-7ed96269ee68	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
d8a21483-56b7-435e-bbcc-c525265df271	8f49b43c-be61-4c6f-95dc-4e8a7d10e7da	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
1415ce42-9871-45c9-bbda-cdd82cde8696	e6608ce5-674e-4c3a-ba90-6772391d4949	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
979e1fa7-a717-4b3a-87b5-b55771a4a2e3	96787c99-a0ce-4332-8f26-f2297f87dcd8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
87b44718-0dcb-47e6-8151-77beb2a9c71c	f390a5a5-476c-4a52-89cc-bae5384a9ab1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ff3cda3c-8eb7-438b-88bb-901963ced801	62c2253a-293e-4954-806a-f893f400e55d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
058b0167-d0c6-4c02-9844-636b3e9be535	18f5b5c1-e9df-4769-9ec2-38abffd9fa3c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ac1f343e-6e9e-494e-b1cc-8d9e921f5450	a658600f-95be-4f25-aaa5-e0cc280ec8ba	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
ad7a7b0a-8dc6-422e-b7a5-4e740a65caec	fe1cc623-5749-4759-bb79-c08f0e00d4b3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3cc15128-16c6-4008-919a-f4f6e424e6b9	59e2aa6a-bb1c-4f29-86e6-d7980d954d46	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2411fb6a-9ab8-4139-acd2-b26f25feb3ca	59985ea0-e5ff-4cf2-9858-7ba48ee722be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
767f6c0d-f1e3-46e9-868b-243f2252b1b2	553ac569-2406-4dba-b5f2-dcd928b95787	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
007b19b6-229c-4abb-b199-4a027d2ae21f	57ba4cb0-d12f-4e87-81b2-b384cf4e8cb7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8927410e-5fde-4e15-91b6-88e9555a095f	bf98b52e-f41b-4308-906b-3ab72d075a9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
778b8537-83b1-49a1-849f-e716abbf51bb	ce3bf15e-84fe-4ce7-a10e-1a26ec8acf05	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8892658a-12d0-4eb3-8f25-7adce40152b2	5cbddda4-b4af-45d7-b913-de01a9a72cd5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
af28d6ae-f20d-4f05-b903-8c989164b9ae	fd85f52e-0065-4fbc-bb94-1465b1d154ee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3ccc066e-2c21-437a-bbdc-3e50ebd2e84c	62aad12b-d9fd-4fa1-8d80-3f93bd42d2b6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
02c30e90-6d30-4f10-967e-8103266d364c	987066f3-edd3-454f-9f5d-0cfb5e55c1e0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fad09297-c89c-460b-b870-763b1d454d68	0a4d265a-8b56-408c-89b2-d9cdc54982f8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8559827e-f4d6-433f-a898-ed185bc86aa2	bad85a08-06e2-4bc7-b864-6b177112df70	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c3545d6b-0f11-47bb-9615-b35101ed1e03	1180b173-548f-4fa0-b566-64cdc0b1dfd5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e7a2e7d5-e7a0-42e6-857d-172ee8d1980d	b3584fe8-58b9-4eed-9daf-81af7c5c2597	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
e7057626-7379-4eec-9716-5f16cc9fc04c	1e5a0a42-ea87-4bf8-8aa7-5e871ca49904	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
7ef5ed0a-664f-449a-b0dd-057836278532	54ee838c-f191-4dab-a861-8bbf24ed8b70	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
557f95e0-bcff-49e3-9797-a10909b6f638	c2ad9384-1f73-4f8f-8f62-7bae9e2aad59	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
226689ba-2887-45ca-8a35-205fc5fc9e13	4a652f79-d0fa-402b-b134-b53ee5b5076e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
858c906d-8918-4599-9516-f51071935857	9a29e77f-f13a-4128-bc24-2f122891a487	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
6b0d83ec-53fe-4c12-94c0-fda90f78c7df	052f6175-66a2-4b84-ad4b-047cccec298d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
678bc322-a0e9-481e-bdfd-ad107e686790	bdbcddb6-5725-4e59-8a2c-7a3d463ed820	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c9a2cd8d-46d5-4420-88b3-ac6d056f80f3	14ef9cd7-4fe2-4b27-970e-773e959f05d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
3f29e53f-c5af-44bb-8f4e-8b4728913236	0d5ffcb1-b741-42e0-aba8-a09b4f2c7cfc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b043f753-29e0-4c36-85a6-f2be6c7dcba9	4b0a1e8a-d96e-46ad-ba49-1b17a02cccbf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
8248efd6-7b16-486e-a340-792dfa9643b3	09aa6db4-7502-4dc4-b889-14fff6e4d482	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9eb3bab6-1fb6-4af6-8769-da0ec6630d53	4aab1431-eab8-4c5f-9202-92a916cd0966	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
63692bbd-a494-462b-ae2a-723ed7b3f1ea	2075e9ed-f702-4fb6-84f1-16eb3917b5f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
fb44a75b-ecfa-4b9f-9e5e-a3b81c25dbbe	67148a4a-35f9-414e-b58c-c2ac18104782	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
867e8104-1328-4b75-b192-c7e1ea803c7b	1e81be0c-c4cf-4970-a53a-505eb92e87bd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c77d29f8-8e7b-4454-8c83-969ab0b65bec	8fb74061-258a-429a-b2dd-2628cce88d86	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
50ca55c9-62af-4e95-b880-26c89a5b7dbd	87a9c9c7-5315-457e-918e-10aed9d46911	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
90dcdc0f-0f92-469e-b769-2c68a6e2c0b2	a172152e-4a5c-439b-bb67-8c41414bb799	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
57a6fcc4-517b-454c-9c80-7d6890ec2c94	1461d06d-72a8-46b5-8090-b0bad1c2646a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f446a15e-406c-427b-87bb-beba1a8db6fc	1f3c418f-548c-4aeb-99c1-86f784f1c9e1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
9c1f7e81-cd0b-4b33-92d9-218405e943de	b3e70ef0-d8b4-42af-80c4-8ee78031befd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
b91b0e86-7934-4ff9-856b-f49bb1422570	5f1b450b-391d-4208-b336-53e192baa578	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
c5121cf3-7e63-4294-ac64-2b372c562baf	28ef3fa2-c237-4c93-b411-82f0001e6492	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
da182b91-840c-4edb-828b-c96c6b0c38ab	1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
2412d9ba-56a5-47d9-98e6-cc7568fe35ad	ccfd7416-c0a3-4329-a4c1-a95603e27da6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
63a9431b-978d-44e9-89bb-486b98e441b9	2abf9654-d5e5-490e-b96f-0b7b2b426283	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
5e3d3b28-4dc7-47aa-908b-8e947be2a36c	70ee9dbf-1477-42f9-9359-f1f40fb79ea2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
0d1c95e7-1a50-446b-9084-849792b20489	b0d208c9-a2e9-40d1-a263-42962f53ca7a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	871a4f82-77b0-4209-9805-41364b6fcbf9
f22830d2-2b7c-41f7-baa1-f3e2ccea1c73	d1974a06-a43f-4fde-8bb9-771bf9617c92	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c62dc0da-cd2a-453c-ad2d-31cc854f31d8	8acb9f4c-25ef-44d4-8ff2-21b28d883997	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5a64020d-6b47-4d55-a611-86ddb2789423	a156e08b-2e02-4e4b-9ea8-82e9921061c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7bd64c67-98ad-4984-91ea-3faf0be7ff2b	5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
dd8b6f98-92b9-4efe-948e-8217cb66fb16	61553ec6-3eb4-43e0-85ac-b41756946a58	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bebf32af-4731-4f61-90e0-6f44a63bb5c0	54c0db7b-d22a-49d6-b27d-a40d7722ca31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b8862a05-381f-4d45-a4a5-6566bdc4ccdf	1555fa16-107b-4d37-b844-8467ad706a65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
32e8863b-e131-4107-92d4-cccf5f17a20d	998ee5c0-cd53-4db4-befc-851c1b703f7b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
59239988-fdbe-4642-abf7-2cd071340d45	bb8e4681-419d-45d0-a8ed-001457b83a8e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f6c36bc1-3cd2-48fc-94c3-de5e47ce85c7	6fa74f7b-29ad-48de-b78b-d1222d6dd7d1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9d31ed6e-1bcf-4d67-b42f-33a5496ba50a	2e3f87a1-4cf4-401f-b98d-2b308232adf8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1e2f37d5-76bc-4f98-a68c-868ca42ada9a	7d48f0b6-c447-4df1-aeb8-65dda435d11f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e57b7d6f-eb7d-44d9-b504-36a8b0748d58	31cc85e8-1169-45c8-a8b9-53538b4f2dff	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1476b9ef-2bc0-4bdf-8802-3fce050367a2	29add6f6-967c-4751-8ae5-839feafaeacb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7c41aaa8-f1c2-47da-b132-6542fc42c7e6	2206ea8c-f2a1-451e-9459-a2cf64a49834	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
73a4e421-328f-4327-876e-676641ad41e9	140b2eeb-8a4b-4ff0-a0c4-f49c4359da21	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
49631207-2f99-4e51-850e-86446096797c	1c09cd8c-42a6-46ea-9012-c2384e14888c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
31f358be-553a-44d9-8381-b40382295900	f0bf6b79-e92e-4c97-83bd-0e7ca50ebb21	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ff1d439b-879d-45a7-ad00-76dcf9b0e974	1b550734-244c-4690-82d6-f0d208ace1e9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e4abb03a-37b0-48d8-b0b7-0aa972daa849	ef1e9112-3119-4056-b090-3a33a5177dfa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5de49cd6-3241-405b-af0b-931c557e555c	cd4eb692-ef70-4a72-9714-3de375eefdaf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b13d8ddb-112d-46d0-87cc-99e6d0ea6364	8351ca74-0e99-40de-b002-07c11aeb6310	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7faa0712-47f4-484f-9c0c-e3b371453d1b	9b978bf0-4011-40ea-9652-2c9fa5206ba6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
58bec39b-9166-48ba-9b88-213fef054008	93e71daf-8b70-43ab-b90f-1b6ddaae29de	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e16f8251-a05d-4be2-abd9-c7311642bf1f	198c3575-5f88-4dae-ba7a-62228de49786	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1e290ca5-659f-4ef9-90fc-c85b8aa2f648	29f6fa6d-4615-4bfe-a397-c022ff9da6a0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1f72bdf5-85d4-452d-95c0-ad2b931772a3	5df84a57-775a-484c-99e0-8e835002136b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7c05ceff-ab86-42e8-b2ae-0f6704e60c19	85afe928-267f-4407-8d28-ff3050657f6e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4be56572-c414-4a7a-a5ac-977057281f82	2d593c56-cbda-4743-a2eb-7e1d3e6e20ab	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
357f7fff-a012-4b9a-8406-282bc4e1f3cd	de254fc5-4f3f-4f96-8c3d-99c2b9e50ba1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
86b73608-31f1-47d3-86cb-49124a6b9c1f	0d9ecc80-994a-4c15-a1a0-9b1794178170	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a609dfe5-77e3-407c-a432-7456db4d5020	4775bce7-7719-4bea-8c12-0d77f29b97e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
224c2168-a8aa-4ddc-b32e-58ba0fbdb485	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8fda31a5-7070-43e9-8635-7f9d717ef419	4775bce7-7719-4bea-8c12-0d77f29b97e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
97ddd2ff-abb6-4778-9649-9ecbf6325a00	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bff4bb29-ca99-477c-8f09-7e930c2b1fd5	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
032a7e1f-50ed-43ae-953f-eb1a0589dbcb	6a0dd8bc-58de-47a6-8965-b3789c26af78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bca548d7-a88a-4ecf-acc7-8987fa479edb	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d978be8b-1618-4a33-a472-d8535b1b5bce	6a0dd8bc-58de-47a6-8965-b3789c26af78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
968e683a-b30a-4cb1-8540-f218c99b8b2a	0a180055-c1d9-4d42-b344-d7593601da8c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
faa6812b-2b47-4217-b9bd-342936890607	614c9539-b9ba-440d-a170-4b9f51e15d47	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1f28c71e-a509-404a-9b3a-1cf7f36ba927	0a180055-c1d9-4d42-b344-d7593601da8c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2af9c3ae-c0ce-4c1e-b723-baf76de55f31	614c9539-b9ba-440d-a170-4b9f51e15d47	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
82ad8a52-c759-4572-b0a1-21e3dc6aed78	43f7d824-cf0d-42e1-b819-7d7479db89be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
45326ba9-6a25-454c-a974-f95427e18a95	40633d5a-6b1a-4d89-b124-12150e904a1a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9309ab17-b45f-4b8f-afdb-0b7ebf903475	43f7d824-cf0d-42e1-b819-7d7479db89be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8167ba3c-4199-4cc1-8b8a-11a3bf95de51	40633d5a-6b1a-4d89-b124-12150e904a1a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9775a3d1-10b7-4bb4-86a9-30fb19d0ae58	961b398d-db41-481b-9cc4-c7986a2722de	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8f5340c6-a4a1-4368-8341-19209f8cd0b5	70c5863a-aef9-4592-970e-9aae14a18687	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
03526a25-b968-4db1-80d4-60e39d3a878a	97bd0f73-7ee2-48dd-abfa-09c7753dc12c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
565b90b4-e634-48f0-b78a-9ad1f82dcda3	ae6f5b04-c9d4-4e4b-8d39-17734093addd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
100d4007-aa5a-4fce-813f-b2785725c84b	fdb20829-c90a-47f4-98c8-95b4682c0740	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b8cac6cf-092a-484d-a9b1-2a8c54098974	c36d0d21-f428-41d8-9deb-6dda00bfc260	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c5af3898-33fe-470e-bfd0-876bd981cb1e	fa0609aa-5f55-490f-9bb8-26f66d8870d6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5b56aedf-0e3a-47e5-80a3-2b25c205341b	c0ca83a0-7b7f-44fa-81b2-da82fac41eee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
efdb3dff-eef7-46c6-97ab-7c457bb40288	c32aa732-a66a-4828-8bcd-a63cb7bff676	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8011909b-66d3-4fe7-97c4-55ac1e6cd565	194cd19e-fd2e-4e4c-8964-a24886ed04a8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
13fb5918-034f-42f7-8b98-e10827ce619b	9400f238-0457-4883-ad18-6a6b645277e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
dab4afaa-9c50-4818-bd67-e81e1c96725f	22e1c682-dbe2-4839-86dc-8d47125fa4b6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b3070360-2bc9-4e8c-8127-22b1f84b5a82	f7ef8034-f74d-42d5-a631-e92d106f4dd0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
aa6289d9-f6fd-46e1-af04-6cadc25a505b	b444bc41-4bb0-4110-be04-0d286487041e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c6c1d51e-7744-4d22-8ef4-ad305411a0f5	199d709f-8ea0-43f2-8b3f-eb4d389d1042	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b05de4de-c1e8-44be-a368-88ee89b01f73	52850cd6-d674-43fe-9c1a-a0a148a18ae8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d0b7c9e0-5bac-4662-8d1c-d5286dc7a6b5	b465a967-aaa5-47bf-9239-9b496b63d66a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9d667bb7-1391-492b-9a4a-187c1d7ce45f	8f2bbc56-0ba0-4d25-85a1-b1941234b95f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ea0584d5-e2b6-4e98-b067-a7df191b2d61	135b1582-0468-4070-9c91-fda08116d3cb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
306f9ecd-a314-456d-b69d-98059bea2e3b	0dac449c-636e-44d5-ab72-eeac8052f70a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
49de5790-53ad-4dd9-b793-b1968e388c28	0fdb6422-757a-459d-ad43-23543ffe4bfb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9c47636a-ba32-4815-b670-e78f8b1ba1c5	1d691b66-954e-4867-9d81-8eea2b6eb667	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2ac361b3-d2cd-4701-b261-e1f68949583e	b3a99f7d-c02c-4e12-a912-d321c59ae865	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
902dc3e6-0e56-4c23-80b1-52459b74944e	3f613c84-1af5-440d-a4b7-360d4a16bd63	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5e06dc4d-799b-499f-a817-24da696a73b6	df6d9e7c-c3a1-4eb4-a96b-5cc1bbf63b28	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4957f61f-19c7-4bbb-90fa-cfb7d408ccfa	0e4d1341-be89-4026-9fc7-27ade0581b0f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
692e5e14-95ea-4451-819a-df69f9057bc0	543762be-87ca-4453-bc0e-d796cdb49468	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5b8bf08e-746c-47bc-9886-cc76033bdb63	cf63f961-d290-435c-a2ff-26a52c42668a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2887e3ae-a1c0-4bff-b9b4-d32cc4e7ab75	5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ff31280b-ef60-431d-81b5-8b0d5acdf338	cf7e849a-85ae-4b70-b1d4-9f03c4c0c897	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fc923396-304b-4be5-b903-95201b7a1ce4	f403036f-e8fd-453f-98c3-d7696e67a106	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6a5d2e1c-0567-4f6e-8ecd-d85c7a9629b5	a75a9442-6377-4684-8683-893cc195c342	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3af85dcc-60ce-42f1-b0ac-e6cee9b2c456	a0328182-d2b7-43e4-809e-8eb9e174005b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
04c35d71-137d-4985-aef5-a12a136e1687	afbc58c3-c001-42cb-a2b9-01204baa60f6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
21545d8d-094f-43e8-8132-853c7d84f2ce	8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e471ca18-2c11-4034-af9c-90b27de2d443	6164e6ee-b364-4c7c-aa62-091897b67081	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9dc78c71-d04f-4ffe-a800-ab5bf1818a41	d20538d2-915a-442e-be5f-70cdb8aa98d2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1fd8fc73-cbed-4458-b9c0-0038ef552c46	addec80d-d00b-43b0-9b5e-356b6f03e0ba	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
483a8c99-6060-40f6-800f-48097547b1a8	14522968-2fd2-49dd-85ed-98d7a3a54be5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d9676a98-12b9-4785-b568-3eec67544af0	26ef163d-a3af-4fa2-a80a-edd775cbb216	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e805516e-5d74-444b-98ee-e5f0cf3993c3	fe289baf-6a53-4818-81a1-782090b7847d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
317d53f4-263c-425b-83b1-840dd4404561	5578ce19-d473-4631-bceb-3529208a9c1c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9887011c-660f-46e2-9a98-528385535cc3	178d2213-60e3-4cd7-85bb-8e22b99b6092	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4ccf8087-a75a-42ed-b04b-44b15ab0d7e2	97ec196e-cceb-46ec-ac63-c62595539b16	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bde292b8-5d96-4dbd-840d-ae9ed30715a2	992b02e7-c182-4538-a8d0-0fb2137c76dc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
302359ee-1464-4e03-9515-5469e1b13b90	8fcc6740-2404-4b3c-b7be-45c0be463f55	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
220f6936-025c-4a7a-b529-88504093d923	531b944e-619e-42a0-b734-5a30d57fa47c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7f3b1212-6942-4751-b09d-04469bbf8ab1	58e26d7a-ffac-41b9-a737-cfb6ec994ead	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
62e87510-194b-4af0-b9f6-49b11acb39b0	83e3428a-9624-4e01-9da7-ce22aa31ef65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4f4b14ba-f90e-4592-95ff-ea7b82477c7e	fac18465-28ba-445b-8706-1a10898fd2ad	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
95045532-e241-450c-a5c7-fba8567458b5	356bdd13-82cc-469a-8fd6-24e597857090	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5fe3e98d-5927-44c7-98a9-6964525f5d55	de10a61a-584a-4b95-91f1-bdf96a5eaeb3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7da9d2a4-5108-47ba-8ebd-1789c9c2875b	e9b3a60b-1ce7-4899-8831-11f827406d5e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a65db356-3521-498a-bc78-993a81b106e4	88dc009b-c5b7-4978-800c-4a8202048808	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b78d234a-17f8-480a-af6c-a2f6e800c96e	bee9a02e-7117-453f-aca2-8a99fb44d5c3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
99311317-c3c6-45ce-99b6-d684737ac36d	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1b0073e2-27c0-4b32-b553-26f31f12ca41	ee0d0a1f-a784-4df7-9212-aa576b3ad098	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
57f1d044-7b35-41ab-b12d-daac52520b02	8435ee66-9b87-47b6-9af4-0700ce6186fd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5508c948-fbdc-4e38-bc8e-58f4cd75fa61	7ce551ca-251a-4082-b60c-f615b8f08c77	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
65ad086e-1072-4c79-aca5-3cbf53a865e6	3987c83b-d17b-47d0-86c9-2ca24d25f4ee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fc1c20ac-e7d9-44b0-867d-d5bc1dc83b1d	4d6a444e-3a91-4914-a852-50c6748c5862	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
aefc4894-3989-4d81-86bd-e85e2fab71e4	29768ea2-2372-4fac-afa4-8025fe024c78	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6e826301-a911-4360-915b-f76a29a8c0fe	f3245aa9-e6a6-408a-b9ac-a82c54845984	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
411c581e-78fd-4251-9a05-668f3f461cd9	d78ace28-ecba-444b-b9de-cee545cef5fa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d2f1188f-6e29-41b9-994f-ce52985011e1	8449c926-5c66-43b3-9321-40108f2884a1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6af8cec9-7e84-4bf6-a32d-feac7e5eda60	df1246cc-bae0-4d4e-8674-fb6af39b15bb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
62ce9631-6c4a-4e31-8dae-644a829a59d7	dbc10961-9d8a-46f5-8635-d611caac9351	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
88018551-068f-48e8-b01f-6d93c29ea5b6	37706f7f-3212-45bf-bbde-a9bd58d7d93b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
92dc2c3f-91ea-42ea-8296-19ec93bded0f	e5b62ff6-5d19-4041-bce2-51eff5619079	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5ed8e292-7af0-45d7-9cc8-453182cb9812	c6c82907-0a2b-4424-8cff-e0d399e82e76	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1ba90824-e770-4a11-b074-bd138e34664e	32dce3db-9b6c-41de-ac5b-db2f1f7cf1b3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
540944d0-f631-4e79-9bcf-9bdbf30fd86f	61592f67-7a2a-4060-8f95-6ff7aaf552a4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fa42471d-36b0-4f6e-8a2f-13da8ed3b174	0009b8a7-676d-497b-92e5-1c9f19a6a9dc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8988425c-5478-4703-be71-968cfdf3fa7b	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b5a98a2a-9f86-4e49-9ab0-c3524afddd58	478355a4-a104-478a-9161-38812c682f28	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8731996c-c8f3-4b26-9053-27a4fd2c0544	dbfda102-ce20-4cde-be8b-e8df65c9f7db	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
497b1577-2849-444f-83be-1a4ea1366c3c	59570f9a-8658-4f5c-b326-6bd30b07d043	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d2c5ac81-4878-42ed-982f-aa55df227804	dae5f7b5-abd0-4afd-ba03-739065d56b35	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a82a81ba-fe11-4aaa-aed6-91fee9dfbc4f	559abe90-0de6-43d3-8dd2-932712b78a62	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
56beafa7-bb73-4e30-a458-7e59f3721d1d	0080a492-5c32-4048-9f36-95788b5271ce	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2ab09197-b614-4ca1-9333-3e7d1d98ad81	b1f7769a-5711-4944-b359-43a02ce6b82c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
00392688-1828-46f0-baaf-a99d11868731	444af49d-152e-4a78-8cf4-7b8a69d039c6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e3a5bf42-ab9f-4b29-82ad-e217951abf96	c3142cd7-e447-4ac7-a995-e49aa1c1c5fa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fb2b4970-161a-4772-85a0-041bd1cf5d50	8a60ac28-8785-495b-b891-7cb5e051043e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7e7399b1-c03d-49f2-b287-1d8783611d95	3aed2bdb-cc98-41f1-b690-f4665163a2eb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
751beb22-d96c-4f89-ac86-71d2c3bd0208	860edeb4-f127-4442-8362-7e0eb45d26ec	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
73d8c70d-b509-46f3-a40b-3265e3a8124a	f4b8d658-d725-45fc-93b0-038fda5d7b3d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5d287be7-9534-45b5-b683-082b8182e299	53bbe15d-011a-453c-8c75-da4e0201bca0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
724c3003-66d7-4880-9cb3-401d11df654f	32bf89c1-cc50-4e3b-a578-7342f0a98052	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
72c4d31c-70f6-4791-b5fe-4b7e40969658	2cbd132b-f48c-4282-b637-eae87931d57c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0e01d51d-4ac0-4a8d-b935-28ca18c291c8	db5f2886-4e5f-46e9-86ee-9eec449e4845	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f49ebc1f-b60c-47d3-b548-01cc85aa02d9	1e0d6501-b15a-4c5b-8856-e0668473540e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3b866c7b-7f2b-4736-8c2b-d84a9de1a8ef	b51b7764-5d21-47c2-aaa2-a54ef06e695b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
09a5baf8-4bf6-4dfb-825c-1fa7838d5fb5	80900d89-757f-45f1-8df1-574a5e4f38c7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
13b51929-e492-46f6-9a68-48b11792ad80	a1514e63-efa6-4ab5-8068-aa531ddcc480	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
22db4e08-a802-4775-aa3d-fcbe97f9e84c	c5618b42-8182-4dca-868d-edf91bbd5249	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
287f7097-1976-485a-9e3b-6e6058cfcc0a	f163594e-9c10-4c15-8184-183411d6dcfa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
74376f18-1284-42be-bfdd-ed9914974307	8dde0f7e-7023-4469-9240-e9e428b1640c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
32a8e488-6b9b-47a4-8660-2ffe4fa2ac01	fc885a0f-9531-475e-a49e-1aa26cecbb5e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
104b0f59-962a-45e0-8c9f-cea45793b172	aa5f3b2d-ae8a-40d2-81f0-68878ae09721	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1036a614-84d4-4db5-9cbf-015a7839318b	3ea54e45-7aac-4cf2-b790-cf68417159f5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6183c87b-fd05-4269-859f-98356d2e1de3	89397364-5cd1-44ea-8ea7-68a8c0cc5fe6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
eb443819-1b3d-46d5-b896-2422db2acdd8	d3a30467-6180-45d0-8f97-0516a39191e4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4c52f2d3-8311-443d-80bb-c53aa902283a	a9fc938e-3eda-4477-9261-e13687c777fd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2219c936-4466-43d1-9e8e-2a2d5352b501	200af72d-ada6-4ad9-a2a9-8ac90c9ee26d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e8406041-2e3d-4f64-91ec-73d1628efb4e	0b90507a-d4ea-4f8f-908a-eca651ed29d6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f41a274b-5ff9-4042-9b37-0617162eb712	d318b34e-2e38-44fc-8583-a25e6633fe34	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5d11b13e-4f66-4a10-8ecd-5a6c53909a97	f41a672d-54ff-457a-88ea-4a8427177b75	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e4c264dd-d711-421e-a3c0-5638f887746c	34aeac9b-bdda-4d8f-bbc6-41a089862e6a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2c5d661e-4d28-4afb-bef8-906edc099998	da969ef4-1721-4442-a71d-3db403d42fe9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
73e0ff44-375f-428b-bb5c-1db1c1ee3fcb	892c73ce-28dd-4546-a0fc-cebb44769bd9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
58ae9456-91b8-4998-afef-6fd5618f143d	ab6a60e1-0283-48dc-b606-544963dde3b5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
865e22fd-f7de-4447-baf0-6a9c8b5fe7d4	b3520f26-f8cf-4933-aff2-1e8303f483d9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
709f30b4-f37f-4eb4-ac46-cfb8b5c4bf52	4ff69e50-609f-4f1e-a804-2d631ecc1b44	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
aa56298e-a619-4d0f-a16c-da625f58c11f	7ed15acb-1b78-444d-afb0-c9cabfd76b12	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
71c63fb7-c411-495e-af17-0a8c147d57f4	b460dc4d-a2a1-4ef3-bc68-172a30959cf4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ea7abad1-a7a3-45a8-9f98-4db518b4ac63	9f608fd0-bde7-48da-a77f-c78ff68bd777	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a1e39641-0964-4ef8-b1e3-a92efda4971b	7c954edb-f3b0-45b1-a0de-1b20a086d060	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3f5d5333-5263-4511-a3a7-98732890b57c	d5d5b1b0-97b5-42e8-ad5c-467225669d07	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
aa836171-ccf8-4dd8-ae74-4b2fb5cde876	e81df99b-a120-4110-8f48-0c5cbdbec19b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2f457c58-ffb4-4d29-9541-4f1f966c86ae	4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
eb003cae-e50b-43a2-b321-d04f9a548da8	89aee119-46f9-4a9b-afd7-6551885362ac	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d445998f-15ff-4f32-bad5-961f8b967624	64faab0b-643b-4a14-8c5d-c5718dd127b0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
94a30520-5c95-4968-8f13-c4d7ffdb1438	bcb56064-a124-44a7-8649-79970c8b6758	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
35d4ac86-032c-4537-a69d-db2e78aa7907	fa97e202-e534-4210-ac26-29a34f1f38fc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7d9441a0-9039-48ed-ad09-67fa3000fdb0	94063735-6495-4abf-91e3-e0eb80aa13b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ca2ff150-3752-4ae0-b8f5-3d57f9ef8b91	b5394775-5207-4242-84c5-6917d840bc4c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
57122591-c15e-4af2-8681-95a60b0c2779	461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
781cd12f-b394-45ce-ba3d-6da3e12173cf	3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
eee0259d-41d5-4d37-9d34-a1f27be91125	c609e1c5-2949-4d3c-bfc3-b61c164c9192	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3bf2574a-686b-4605-976c-0da057255c1e	a7bbba94-e82b-4749-8101-c65fd8ff3449	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9e7a9126-e689-4d0b-85e4-504e05c3b8e8	521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
cf325e95-cfe1-443c-8918-1e5d348ba5bc	6acecc37-452e-41cf-bbfa-fa29139985c1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c141c51f-5379-439f-adbd-7e2dac32b85c	0c646133-3a61-494d-8779-db533c0980d5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
2698c17f-8e15-4ce8-adfc-5d6d1f5e9e1e	78ac9d50-be7c-4701-af65-e8e4ea0e2276	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7d6055a5-331c-4a8a-9e95-7fd5ce64a4d6	5567dd12-02bc-47df-b4e6-88b58026bfa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
28466f8e-6524-4e31-913b-dc006cff50ca	63b03555-2ec3-4271-a8d5-43f8e1a92a6d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c041affd-173d-412d-a718-fc25ca9487eb	da7f5c17-06eb-45e3-b48c-90ab6ae078f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
46e0e2ce-647b-41cd-b4b8-1f771d6e728d	c69dd883-7035-4781-92d5-e12b0b0bf97f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e1ae6f83-6008-4e34-a57d-3f0360e9e8c0	5646f259-9143-4afe-823e-a993ad4c16ae	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d157d325-6502-4631-9d66-14452b082a45	846c440c-57b3-4d15-98e8-9d3ea4d01392	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c2ea8df2-3ccc-4cd7-9736-b9ea2f1d60a2	a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
57eaa31a-b364-4a55-a410-9310ea5c2a58	c824e963-ab76-4ae7-af4b-8976832f6fec	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
515a6226-966d-40e3-a790-91f9b3eaf460	2aa2f082-a408-4c05-b518-dd2ce8ad640b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b121a470-b6bb-45c6-9529-c365ff5ebe1c	b7aefd26-9f98-454d-a476-ae7c9ce54387	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fcf4bda5-b6dd-49e3-9502-bdc4754edcc5	e440b879-0e0f-4692-8c4b-4b10c6d0cf01	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4ddea297-fe01-4055-b597-7d0d755f65f3	7249055c-e681-4d1f-ae2f-28c471a3af05	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0f0a1e44-03cb-451f-aafe-7aebf5c440c5	b4a855a2-bfa8-41ee-9173-998bee08316f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
83abb0c2-1c20-4c7f-9269-b0adef5767fa	2f9da69e-71b4-4b2c-919e-1500bc55a630	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e9ab5ebb-c094-44c7-9a79-bfeb9d977e72	495c9a9e-6d98-440d-850d-3791071e4e95	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9c2b8484-b508-4150-a5f8-d1af5a96a3bf	72602fd8-2dd5-4d51-8280-4408e4a138a5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e92e7080-db6e-4fa0-a1b0-4d569ca3fc4a	74f3ed80-98af-440a-a347-3f32e4be27aa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
afc0b356-e087-433b-a71c-671baaa5a315	af6a1c14-e2af-435a-9a9d-bac3d66c35b7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
59208092-b39b-41f9-8fb8-9d3ca1c9bf6e	c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
47ba3ef3-2a26-4069-9891-9ca960071397	3a3e183d-acd5-4e33-88e4-243fb0d99faf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4c8e351a-f315-4ddf-b667-307052990237	a08f430c-116b-4eb3-841d-d8d09c2f743c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
03bd7c1d-48a0-4c64-b0b3-ab6a5f6020d6	9726018c-4bfc-472f-8033-bb15a844772d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0d17eaa3-6dd6-4aed-9975-68acb29058a2	2147a1de-ca25-43c4-adb1-7219bda6216f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0da67c54-c2d8-467f-a596-10b6729f4818	ba8f6800-1286-42c7-b362-c24844b700ea	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
29e41216-d233-4c69-b781-e33e02ec2f41	e434f5a9-2005-4d7d-aa4e-051a7c10fa17	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fa0d35e0-cd61-48e0-b91d-7b9a77e5d798	b73de201-00ce-40ec-947c-f1159a500794	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
015a931d-9408-42ee-8134-d3adc7d8a05d	42b8e3b1-90ca-416a-a471-1f851ad03abc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9604a654-4f4c-407c-a788-d18234f4317c	564de578-2d66-4c50-8163-ab02b5a10663	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
96faab4f-0d9d-42f8-a375-816b509b9ad6	3dd5f85d-f466-479a-ad01-2f45c32fc196	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
cd9cc2cf-83d2-4643-bc1b-293893c840d6	27e673a4-366a-46f7-be9d-409e61e48a7b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
768b3b28-1f18-4e1d-bac7-b93011546b0a	6b9f3fa5-d64a-4023-9f83-f0bf27bdb0e2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5eb93a7b-2aec-4f1c-9f63-4ba75d45a322	31f83c6b-72a9-4c79-b1e9-6bdef5b894e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
92fd3fe3-6f5e-4564-9933-9086de072906	0aaa74f5-6f91-4b5d-9dd3-5b7ed925964e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
af31b470-cd7d-45b3-bdfc-fc0f2311dcca	d571b7dc-eeb9-453d-bdfe-33c2ba653cdd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
90e2b1fd-e4e2-47b8-9a12-1c666b9bf054	8f8f3c91-2d26-4ded-9225-395ae9042f11	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f7b530de-dbb1-42a0-8cc0-5112f05bac56	c7e79fd6-9cb0-4527-ba8a-09da1d2f918c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b13e8660-28b1-4ffd-ab7d-5eecbbc4c61b	0e0dbf1e-b47a-4db1-9c9b-4aa4500722eb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0e8a3bb0-06d5-42a4-9738-cc28af9b3aba	3abc05b6-c5ea-459f-b7b3-68a93ceb0ed3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
762c9883-1965-4557-b178-461e233af73a	9e20a739-67ac-4085-b5b0-1d3540deddde	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9b18f03c-acd1-4373-9641-a5d5da2501b7	05893119-03f8-41ea-88c4-bd840e95c2ac	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
18d9936b-88e9-4e3c-ae92-051823f2461e	907dad10-e38e-4af2-90fe-d41212bf51cd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
57592541-ef8b-43f4-aeeb-c0b061f41dea	b73cb807-821d-4f6e-8c71-78b5c5310bed	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1ef4bb23-ed8f-4db6-b7e6-c982230f5bd3	888933f7-ca51-41b1-90d9-45ceed3a99ca	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0d5d1f51-90d9-4e9b-8cf6-851cb51164ff	17639dfd-b136-44c4-9284-232bdc865000	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e44543f9-432a-4655-afc6-77df1e566ced	f7112f63-6f6d-4a33-9362-d4ffafcf339b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c67ba5d7-7152-46f1-9143-2fcdf35fd4e9	bf821156-45fe-4ab3-a13e-8d7aab0d3869	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7834d937-9552-46b5-bdf1-a74d0f05cefe	842e1d5a-feda-4096-ae06-5bf538545e31	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a3a69109-a541-4ae0-8576-2e51f6bc504b	2c88e468-33fb-4346-a92b-b514a7e3797b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6a085f12-9187-4878-97ec-6c9983a304a4	197d1458-b83a-455c-8db5-267a616501a7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d72d2313-ed65-4159-89d9-ce5660790e0f	10bef495-7255-4638-bdfb-7b8df9c37423	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a5ba6537-8163-4b52-a614-f48789562cf9	936473d2-bdc9-4727-92d1-6e8762ad2b65	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e1137eec-0adf-4e54-8834-fd8acf209f64	5073e567-0d72-4e94-b697-79e1cd408def	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c5facafe-d52f-4525-81a4-cde20c60ac40	b15d206c-d5ef-4d69-b660-1f06272c10e4	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d9bb4fcf-6b04-4d47-ad20-66c9147e76d1	70afac5e-7487-494c-9737-9ba5323e9a7e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e1572d2a-5e76-43a5-a82b-ffafd99e2d6d	28c1d342-6d69-4c31-8afd-693ac1d32db5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
47aba539-5d4d-4c02-bec3-364a1308258f	a4e76dd4-4d79-44f4-96c6-fc4eb6391677	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d222fc51-d31b-4b15-8640-d0a7db465ed5	68d16bc7-866e-41e2-9f90-79086232128f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
4a157cda-da60-413b-a218-271d8c2f78bf	ac156f84-4748-4ce8-a4f6-4bb26b4839a9	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a0078d2a-5227-4fec-9a6b-cff5f8c12649	dd5dbea6-ee71-47b6-b10e-cd736d5988aa	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
431c4dca-e57c-4165-82a8-2a8b8705e426	44d0cc09-3bd3-4408-a54b-fa2840a6d5f3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1d2c5318-c1c9-435c-a115-08c3b019e0c1	83070134-6fdd-4816-b2a3-6c37e96e22fe	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a0955456-2c2e-4224-b8e6-c260657f45a5	20dd1625-14f7-477f-8f1c-5c929edb9956	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
40504544-b7d8-4d78-8bb6-010ae134f3e8	b76156d6-7d71-47c8-aa45-a951287ebd9b	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
eda75fad-7a21-4631-b165-52bd987acf18	531f9c5f-5fce-4446-bfe8-ce270e4f629c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5cbc7733-18e3-458e-acb2-4cfcd8b58fc6	52f4509d-b071-4aa4-930e-e01e97e4302f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
930a0c6a-ef41-46c7-9d9d-38f19d9306c0	409b244f-7dfb-4c7b-8686-a079379ded1c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6052b144-f30f-4b91-81c0-b46fa484b5c6	17bb19b4-e16b-4a51-8531-b7da9cbff8f0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
10cad5fd-9b29-4500-b5a8-42d65a33cf80	baaaefc8-3ba7-414d-ace8-650ade2f98db	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
b917e3c4-5b92-4c51-b59d-5909c822c3a0	0b171841-6ee4-4fc5-8ac9-2b19d4a2c65d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
efc5a9e6-b37b-4e0f-b4d3-26de27c297ec	cf42f76f-bfc1-410f-8cd2-f6b1a32f94e8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
543255df-aadb-4cda-9d11-5fc26a6f4f3b	458c8f44-4178-4ad1-82aa-e1fafd1df65c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8513ea23-df6b-4490-a49e-672e3df83c7f	1c1054e1-1106-4a8b-8230-f9bbe7b2e4d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ba5697f5-373d-4d45-80ea-aee63259e5cb	18a6da15-b4b6-4225-b473-c5c0eeddd5ce	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
625aa80c-310f-41c8-9f44-97b50af47c89	957c1e64-7e5a-4c17-8f27-1a4944de6a3c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
074ab145-1c2b-4301-87aa-f6ac9d064884	feca6731-d1ec-48de-952a-aba8ad404db3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3b4295a4-7895-4a74-9a02-a24b824a5ecb	089157e1-3de5-4c32-9c69-6445d78edc1f	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
84480f25-5bb6-4b48-8f40-250a1946fb97	74e0df2b-4c04-4518-b484-d6425e13ea74	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
be509ef8-c46c-4268-a1ab-8e3f750ec42a	41fd61ae-6fe9-42b0-9c0e-4818f153ffa0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9d7c495a-265d-4889-a7c9-ea62bd5c5e1a	a0ebae73-9f25-48b3-8fd5-b05ba844d222	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7edced11-153b-4cc4-8f16-6652f037963c	199afe79-6431-46a4-a0a1-1add114881ef	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
dcf36dd3-00cb-4ca9-8b28-7d029cb84661	29de49e9-c12d-4c5f-9de6-18aac4973fa5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
655109a1-89ea-4bab-990b-b8c20cd8402c	30c26e10-38c4-4254-aa2e-0d42f352c023	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7d3ad4e6-d3e0-468c-a2a6-627fbfab0493	43301ae3-93ac-4bb3-b023-dd39d37de9f6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d3ea1a32-36bc-4bdf-abb3-bc530d261fbf	1021ee4c-7743-4e51-a5a4-164a2ea3d842	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
40f744ca-c4f1-46bf-87d0-4a54004b264d	efb317af-7eac-4f9f-8f63-7883c2982ede	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a102b5bc-9da4-4dbd-835b-b9e5f67c745f	9ad814cd-f7ba-4d29-a113-805dbc651c60	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ac6901a7-b769-4da9-b29b-e8ac710e7108	3b91dfb2-fd88-45f2-928f-0c9a02394b62	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3d2f714d-1406-4d88-8b3b-bd9532b55072	82657f8f-f8ad-49ec-bc2b-bb8fa993f67d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
327aea26-073f-416c-9598-02b3bab55ce9	b128ec84-8ee0-470c-a38c-7ed96269ee68	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ac77d811-bc2b-4aa0-813c-93b52cc90bbe	8f49b43c-be61-4c6f-95dc-4e8a7d10e7da	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d8123a24-9ca6-45e9-aa46-df3c4d6fef61	e6608ce5-674e-4c3a-ba90-6772391d4949	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c5b42097-99a6-4d17-b68b-5471a9fbdb88	96787c99-a0ce-4332-8f26-f2297f87dcd8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
69ab918f-81b1-489a-8abf-998e0f6a959b	f390a5a5-476c-4a52-89cc-bae5384a9ab1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
91473bb0-5fe1-495b-918d-a116a366a90d	62c2253a-293e-4954-806a-f893f400e55d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e7569bdf-7d87-4f23-83a2-98ec612a7858	18f5b5c1-e9df-4769-9ec2-38abffd9fa3c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
31dc72d5-7dcb-48c4-b277-16621fda8074	a658600f-95be-4f25-aaa5-e0cc280ec8ba	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
582660b6-2e2b-4d2d-9f8e-c4b35cae212e	fe1cc623-5749-4759-bb79-c08f0e00d4b3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
cac68cae-dc3c-4140-bc14-4a5ef0c58fb1	59e2aa6a-bb1c-4f29-86e6-d7980d954d46	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9349608e-48d0-447f-9cc4-167b1afaabd9	59985ea0-e5ff-4cf2-9858-7ba48ee722be	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
62f9b29b-f139-4ad1-a2dd-e39eab4eaf75	553ac569-2406-4dba-b5f2-dcd928b95787	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
321401b3-241f-4012-b596-f42134f36e5f	57ba4cb0-d12f-4e87-81b2-b384cf4e8cb7	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ccfb0ef7-8b84-487a-9b3f-4b144069ff5d	bf98b52e-f41b-4308-906b-3ab72d075a9a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
27e818cd-4aae-43d0-8644-4179bf77e2dc	ce3bf15e-84fe-4ce7-a10e-1a26ec8acf05	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
0aaef255-ee6e-4fdc-82b1-c1dd313dbc17	5cbddda4-b4af-45d7-b913-de01a9a72cd5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
32d1c1ca-49da-4290-95b6-d0fc4bf4fc0e	fd85f52e-0065-4fbc-bb94-1465b1d154ee	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7a243199-b9c2-4daf-9823-aec3360fdc33	62aad12b-d9fd-4fa1-8d80-3f93bd42d2b6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f56f5d72-ce8e-4dd4-8462-05b0fe09c0fb	987066f3-edd3-454f-9f5d-0cfb5e55c1e0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3295a16c-074b-493a-ac9d-ceb637dbab32	0a4d265a-8b56-408c-89b2-d9cdc54982f8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3fbc8ce5-868e-4b48-90c6-e88e48c3b903	bad85a08-06e2-4bc7-b864-6b177112df70	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
905331cf-e26e-440d-9961-ba3a94f34594	1180b173-548f-4fa0-b566-64cdc0b1dfd5	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
423473e6-e0a7-4120-8b51-b738e45f110f	b3584fe8-58b9-4eed-9daf-81af7c5c2597	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3a1ef4b1-6dc5-4db0-a44b-8a84e5ee887c	1e5a0a42-ea87-4bf8-8aa7-5e871ca49904	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
18d258b7-9fe5-4196-8ab5-c23031129c71	54ee838c-f191-4dab-a861-8bbf24ed8b70	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d4c42c77-1d92-4ae7-8633-a2c12078d08c	c2ad9384-1f73-4f8f-8f62-7bae9e2aad59	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8194b1ec-fa94-4d9a-9bf2-ca35df75e5e9	f5e1ea70-3e91-4df5-9c55-9669c9e62872	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fffcca6e-c246-4b03-bc1f-cb1b8bcd8bed	4a652f79-d0fa-402b-b134-b53ee5b5076e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
64762879-7af4-43d7-85f9-b177f1b13aa7	9a29e77f-f13a-4128-bc24-2f122891a487	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ce058a00-7b1e-4db1-b7e1-27b86840c837	052f6175-66a2-4b84-ad4b-047cccec298d	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e3e5d07c-77f1-4063-9b0b-facec3e2c58f	bdbcddb6-5725-4e59-8a2c-7a3d463ed820	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
11d1ac97-9be6-48fc-a941-50e378476d7b	14ef9cd7-4fe2-4b27-970e-773e959f05d8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a2b1399b-d4b3-4611-99b0-32a94a2c3326	0d5ffcb1-b741-42e0-aba8-a09b4f2c7cfc	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5fedec51-6ce5-4fc9-92cc-ce93ba4a7c0d	4b0a1e8a-d96e-46ad-ba49-1b17a02cccbf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
63a1a4b3-4837-46f9-a26b-2f10aa8574a1	09aa6db4-7502-4dc4-b889-14fff6e4d482	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c4be0064-8024-4e2c-8dd7-98d9d53dea24	4aab1431-eab8-4c5f-9202-92a916cd0966	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
76bf0dcd-6d1e-418b-b55f-0a1dd63ca1a9	2075e9ed-f702-4fb6-84f1-16eb3917b5f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
11332436-f230-49b9-a937-53c08ccb3a2d	67148a4a-35f9-414e-b58c-c2ac18104782	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6132a42d-a7dd-462b-9528-91f773977635	acff3dd5-e388-4060-b2f7-38fd24021c68	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
52388f4d-43e7-4284-9a2e-59594a0bbbed	1e81be0c-c4cf-4970-a53a-505eb92e87bd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
5150aeb7-3d8f-4ead-b0c0-dbbefb4d58b2	8fb74061-258a-429a-b2dd-2628cce88d86	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c99dce8b-5e47-4df6-aa42-b8f37fed8d4c	87a9c9c7-5315-457e-918e-10aed9d46911	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
1f95dbb7-6bbe-4f9c-878e-4412338092a4	a172152e-4a5c-439b-bb67-8c41414bb799	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7c65f738-6e33-4bae-b43e-ffbebda2b307	1461d06d-72a8-46b5-8090-b0bad1c2646a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
00eb13f3-9305-42a6-82e3-d8a90a770b1f	1f3c418f-548c-4aeb-99c1-86f784f1c9e1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
3e192f88-cd15-484e-a166-2610a50f332d	b3e70ef0-d8b4-42af-80c4-8ee78031befd	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
aae207b9-1f00-4a67-9ac6-03b225659570	5f1b450b-391d-4208-b336-53e192baa578	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a0da998a-55af-49c3-a8e8-006143b66dda	28ef3fa2-c237-4c93-b411-82f0001e6492	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
75c53bcf-7edf-48a9-ba9e-38a29f264a33	1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
e0b693bd-d8c5-4e9e-9ca2-77017ab19e16	ccfd7416-c0a3-4329-a4c1-a95603e27da6	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
fad6c144-b7aa-4713-8e24-18e0610a8f2e	2abf9654-d5e5-490e-b96f-0b7b2b426283	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
905cbb88-9160-430e-85c4-180c44bc76f3	8f2d8131-94a6-4331-841e-1031150bd63e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ac3087f6-ee7e-4234-bb0e-f93394a4bb26	9c2ddc01-f7c7-4451-a595-d665830b062a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
f4ab4f5a-1ec3-40c7-9289-56f9b64a432e	c30a6a90-4ce5-4917-9e62-4972d4e1ee19	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
00f31fb8-5159-4782-aa5e-bce8495a38a2	12c9297b-83ec-4782-b024-46edad03e261	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d7140c98-4d6a-41d2-bc87-b4c5ad360f61	e31406b2-d66e-44ab-bff0-73fba95ad51e	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
64df82c6-4668-4d48-b751-0f3aa2a7a10c	299f9d53-9f76-4c85-a2bc-337d53055cd2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
7eae2f03-08ce-4529-b7c1-0418678b2cba	006c6e95-b04b-4bc1-9bc6-68202e92d1af	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
8805127e-7e82-4251-bfcd-9dfe0ed31cf9	544e1530-13e3-4a9f-8186-1889b0004c40	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a83ef302-b42d-440f-96a9-0aec29f67215	70ee9dbf-1477-42f9-9359-f1f40fb79ea2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
00298677-c1bb-4307-a8de-46273c3222bd	8b78ab34-c265-4577-9c86-21a4d09cdc52	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
66211908-5c7f-4ff1-990f-8b17825b3e56	c92904fa-2ba8-4e5d-9abc-73d3ce7a66bb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
9bee6b9d-5f6d-4390-aa09-b19edada0274	3953ae28-900d-42b9-92c3-6b97102aada0	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c62c0ccf-af1a-47a4-930d-cf425be3eec9	42917c7d-09af-4ae7-91a9-3b65b0c654a3	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
a7e8f08e-e445-4c3c-8da5-66cf9491ac0f	27afa12a-791f-495f-91be-dce580504f4c	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
99c12cea-f359-43da-8509-f0e4fd7b58e4	60b5673e-9d4a-41b1-8383-05932a7395ae	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
c1c9a85f-68ef-4d2c-bf5c-9e0289790d48	b0d208c9-a2e9-40d1-a263-42962f53ca7a	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
6c7d2dca-8bf7-4a2a-95b8-77b9585fe803	44cc830b-0ae9-4aa0-a2ed-57ac80e0b4fb	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bd8a9069-14f3-4c17-a128-461ab13f45f2	be6fab0b-7648-4c86-914b-7ba63acf9bf2	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bc8fb0ea-3bc2-4d4f-9ba9-9ceee3a4962d	278a9ee5-f497-4297-a6cb-e8f8e9ca9faf	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
d0b3e4ce-5046-4d2e-acb8-334b1f409727	57c06b53-155f-4b54-b420-a4605b0badc8	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
bf9b1894-f1f7-4ced-92a1-3a05fdf09583	f4abc59c-b7de-4de0-9e12-bcbb3a7fa1f1	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
ab814985-2887-4c19-ab3a-7a07e16135af	bdc6318f-5da2-4907-bab4-cf4838d80988	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
629fe71b-d20d-41ca-a0e9-91c56835653b	18d0f888-ae4a-4071-a6be-ab7e467c6472	\N	\N	\N	t	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f	78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
\.


--
-- TOC entry 5497 (class 0 OID 21492)
-- Dependencies: 366
-- Data for Name: menu_item_category_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_category_mapping (mapping_id, restaurant_id, menu_item_id, menu_category_id, menu_sub_category_id, is_primary, display_rank, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
9673ca6b-56ac-473c-8807-1dc426cb740f	6eb89f66-661c-4294-85b4-044519fdec1b	010c83a6-d7e3-4f48-880e-c85137fb39e2	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ee9cacf6-4563-47db-8d9f-749e3415e57b	6eb89f66-661c-4294-85b4-044519fdec1b	a601a7f8-5d30-4347-bb02-94526f4f413a	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
619d48be-c049-4a78-bee6-8632937e1ff0	6eb89f66-661c-4294-85b4-044519fdec1b	18d0f888-ae4a-4071-a6be-ab7e467c6472	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
67cb709e-1d51-4b34-9a3a-0107c151b6e0	6eb89f66-661c-4294-85b4-044519fdec1b	3f32641e-2154-45f9-ba9b-4840865e04d5	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
832a28d1-fa64-4f93-9a6a-e53ce6e3e2e3	6eb89f66-661c-4294-85b4-044519fdec1b	9d63daef-e702-4908-9df5-d54c07335256	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
46b89902-8277-4a24-a095-cd9c56293cac	6eb89f66-661c-4294-85b4-044519fdec1b	9d63daef-e702-4908-9df5-d54c07335256	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f7ea622e-3d25-49d2-8025-13cd2ec65386	6eb89f66-661c-4294-85b4-044519fdec1b	4d7a637f-1360-458e-95da-d4bb74c5c99c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
80920dc2-ee68-4ad4-8347-26215b8959b2	6eb89f66-661c-4294-85b4-044519fdec1b	bdc6318f-5da2-4907-bab4-cf4838d80988	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3b61effc-8a0e-456b-b91f-d835a5053dcc	6eb89f66-661c-4294-85b4-044519fdec1b	a2a30d42-28a9-4050-b157-0227e4a539c5	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d30288f3-f5d7-429c-9721-2a665343463d	6eb89f66-661c-4294-85b4-044519fdec1b	eff3d4e3-726b-4170-9d2e-5894b0a70ad5	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4121f53b-2f7d-45b2-9f6e-9e379d5b2e70	6eb89f66-661c-4294-85b4-044519fdec1b	f4abc59c-b7de-4de0-9e12-bcbb3a7fa1f1	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4ceaf088-e544-403f-8b50-a75cf2e89e90	6eb89f66-661c-4294-85b4-044519fdec1b	57c06b53-155f-4b54-b420-a4605b0badc8	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
95b35556-2125-4187-9384-de200c8462cd	6eb89f66-661c-4294-85b4-044519fdec1b	a66b87c2-03a2-47e8-a9da-37904dbe30b9	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
120faf95-2234-463c-a794-057e267904a0	6eb89f66-661c-4294-85b4-044519fdec1b	a66b87c2-03a2-47e8-a9da-37904dbe30b9	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8ea9a5ae-50db-4cc6-b1fd-08c2c911fb87	6eb89f66-661c-4294-85b4-044519fdec1b	278a9ee5-f497-4297-a6cb-e8f8e9ca9faf	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
40a93eb0-f112-4508-bfad-1e23e6fee88b	6eb89f66-661c-4294-85b4-044519fdec1b	be6fab0b-7648-4c86-914b-7ba63acf9bf2	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
29bb6384-0a0c-4027-bfe1-65678524311d	6eb89f66-661c-4294-85b4-044519fdec1b	44cc830b-0ae9-4aa0-a2ed-57ac80e0b4fb	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c8c1986c-18cb-48d6-a8d0-bddae6ece81e	6eb89f66-661c-4294-85b4-044519fdec1b	b0d208c9-a2e9-40d1-a263-42962f53ca7a	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2f5939c5-8658-4bc2-ba41-3d960aa21809	6eb89f66-661c-4294-85b4-044519fdec1b	60b5673e-9d4a-41b1-8383-05932a7395ae	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bc523656-0062-4fae-9daa-da7faefb2b7a	6eb89f66-661c-4294-85b4-044519fdec1b	27afa12a-791f-495f-91be-dce580504f4c	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
16809ca3-2167-417c-aa40-532ebdca2ab7	6eb89f66-661c-4294-85b4-044519fdec1b	42917c7d-09af-4ae7-91a9-3b65b0c654a3	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
04826837-90d6-47ee-b21a-c4f38aa3f20f	6eb89f66-661c-4294-85b4-044519fdec1b	3953ae28-900d-42b9-92c3-6b97102aada0	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2a555419-1fcc-47dc-9ad7-e49ed1bf23bb	6eb89f66-661c-4294-85b4-044519fdec1b	c92904fa-2ba8-4e5d-9abc-73d3ce7a66bb	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d82bfef8-862a-469f-8b7e-d47935e94e14	6eb89f66-661c-4294-85b4-044519fdec1b	8b78ab34-c265-4577-9c86-21a4d09cdc52	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
962beaf9-2516-48d1-883b-937b27e4bcf3	6eb89f66-661c-4294-85b4-044519fdec1b	70ee9dbf-1477-42f9-9359-f1f40fb79ea2	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
72464fea-c0a2-492b-bda2-ce805fe2ec6a	6eb89f66-661c-4294-85b4-044519fdec1b	544e1530-13e3-4a9f-8186-1889b0004c40	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
979f7985-8887-4408-9c20-bce39e5ceada	6eb89f66-661c-4294-85b4-044519fdec1b	b269c7ba-3584-49b4-b3c2-09c4a390688e	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f0114142-5d57-48b0-849b-041ebd676cc3	6eb89f66-661c-4294-85b4-044519fdec1b	006c6e95-b04b-4bc1-9bc6-68202e92d1af	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7fdacbfe-8a8d-4eca-95fa-d55d53795edb	6eb89f66-661c-4294-85b4-044519fdec1b	299f9d53-9f76-4c85-a2bc-337d53055cd2	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
71aaa25f-0858-44d4-b53b-e1e5e66ea1f6	6eb89f66-661c-4294-85b4-044519fdec1b	e31406b2-d66e-44ab-bff0-73fba95ad51e	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e09cf4a2-e4d9-47b9-a328-edd777b14077	6eb89f66-661c-4294-85b4-044519fdec1b	12c9297b-83ec-4782-b024-46edad03e261	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4816a578-a595-4cd5-850c-e470f5e578c8	6eb89f66-661c-4294-85b4-044519fdec1b	c30a6a90-4ce5-4917-9e62-4972d4e1ee19	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a8dc6ea6-ee4f-4f40-bec8-7c001b1b8f22	6eb89f66-661c-4294-85b4-044519fdec1b	9c2ddc01-f7c7-4451-a595-d665830b062a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
011d2dba-af1e-487b-a4b9-262c7aa15c19	6eb89f66-661c-4294-85b4-044519fdec1b	8f2d8131-94a6-4331-841e-1031150bd63e	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a28aed82-1405-4a5f-b3d2-510015a50a55	6eb89f66-661c-4294-85b4-044519fdec1b	2abf9654-d5e5-490e-b96f-0b7b2b426283	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3835e6c8-2217-49ff-8add-9b736114f38d	6eb89f66-661c-4294-85b4-044519fdec1b	ccfd7416-c0a3-4329-a4c1-a95603e27da6	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d28a9777-46fa-49c2-81b8-05e7bd2ae4fa	6eb89f66-661c-4294-85b4-044519fdec1b	1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2eafa2ae-b3c1-4796-a211-44fdaed27d0a	6eb89f66-661c-4294-85b4-044519fdec1b	28ef3fa2-c237-4c93-b411-82f0001e6492	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
075d3882-bc94-42d0-b281-056125c1b4d7	6eb89f66-661c-4294-85b4-044519fdec1b	5f1b450b-391d-4208-b336-53e192baa578	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a56fa94a-fce4-43d9-bc17-131fd6e9b345	6eb89f66-661c-4294-85b4-044519fdec1b	b3e70ef0-d8b4-42af-80c4-8ee78031befd	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
095469bd-d591-48b7-8195-8f93585c3164	6eb89f66-661c-4294-85b4-044519fdec1b	1f3c418f-548c-4aeb-99c1-86f784f1c9e1	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1b88f843-0eee-4d0d-9850-9e0f53b8df71	6eb89f66-661c-4294-85b4-044519fdec1b	1461d06d-72a8-46b5-8090-b0bad1c2646a	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
aa499129-bc94-442f-8429-012869a999d0	6eb89f66-661c-4294-85b4-044519fdec1b	a172152e-4a5c-439b-bb67-8c41414bb799	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b2bfce51-64f4-4a92-8f0b-5acb305e3dfb	6eb89f66-661c-4294-85b4-044519fdec1b	87a9c9c7-5315-457e-918e-10aed9d46911	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f715e4f7-f61a-4690-9494-b9fb06fdf76e	6eb89f66-661c-4294-85b4-044519fdec1b	8fb74061-258a-429a-b2dd-2628cce88d86	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d91852f3-8400-46e2-8b69-64c1a739f794	6eb89f66-661c-4294-85b4-044519fdec1b	1e81be0c-c4cf-4970-a53a-505eb92e87bd	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b2788052-256c-44e5-b5e4-9c59ab7fd2a2	6eb89f66-661c-4294-85b4-044519fdec1b	acff3dd5-e388-4060-b2f7-38fd24021c68	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
31de6bd1-0bd7-400a-845c-d5f7f8ef1f2a	6eb89f66-661c-4294-85b4-044519fdec1b	67148a4a-35f9-414e-b58c-c2ac18104782	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
46daf2ba-bad2-4eb8-ab0c-083acc713a9b	6eb89f66-661c-4294-85b4-044519fdec1b	2075e9ed-f702-4fb6-84f1-16eb3917b5f1	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0ac34d40-fb28-4674-9b4d-1401196da53a	6eb89f66-661c-4294-85b4-044519fdec1b	4aab1431-eab8-4c5f-9202-92a916cd0966	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6e7649a8-9e3d-4952-9a5b-6b78a354a763	6eb89f66-661c-4294-85b4-044519fdec1b	09aa6db4-7502-4dc4-b889-14fff6e4d482	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b3c86bb5-332b-466d-8510-cc4879c8e881	6eb89f66-661c-4294-85b4-044519fdec1b	0d5ffcb1-b741-42e0-aba8-a09b4f2c7cfc	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8bb88210-7b2f-4006-b5d1-10d9313a394c	6eb89f66-661c-4294-85b4-044519fdec1b	bdbcddb6-5725-4e59-8a2c-7a3d463ed820	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
63b55726-9212-4a78-a2cd-06df721523a6	6eb89f66-661c-4294-85b4-044519fdec1b	052f6175-66a2-4b84-ad4b-047cccec298d	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dadc688f-a894-4615-893f-69e473e6ffce	6eb89f66-661c-4294-85b4-044519fdec1b	9a29e77f-f13a-4128-bc24-2f122891a487	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ff3fdc23-c592-4d34-8d1d-bab466f920c1	6eb89f66-661c-4294-85b4-044519fdec1b	4a652f79-d0fa-402b-b134-b53ee5b5076e	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
06b6f875-99f2-45bf-ac97-de6b304f3165	6eb89f66-661c-4294-85b4-044519fdec1b	f5e1ea70-3e91-4df5-9c55-9669c9e62872	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c3aba731-aede-4120-b3c6-811c367ebffc	6eb89f66-661c-4294-85b4-044519fdec1b	c2ad9384-1f73-4f8f-8f62-7bae9e2aad59	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e1118181-9e17-4f9e-abde-9fed05ce4c0a	6eb89f66-661c-4294-85b4-044519fdec1b	54ee838c-f191-4dab-a861-8bbf24ed8b70	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3feec915-9c06-4f40-9452-9d6adda67a76	6eb89f66-661c-4294-85b4-044519fdec1b	1e5a0a42-ea87-4bf8-8aa7-5e871ca49904	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
033b7125-3c59-4cb7-a543-21d31369761d	6eb89f66-661c-4294-85b4-044519fdec1b	b3584fe8-58b9-4eed-9daf-81af7c5c2597	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e4ff4ba-a660-4c96-882d-9ff35705e98e	6eb89f66-661c-4294-85b4-044519fdec1b	bad85a08-06e2-4bc7-b864-6b177112df70	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
626963a3-cd97-4f13-a04a-28d1af2bf3dd	6eb89f66-661c-4294-85b4-044519fdec1b	0a4d265a-8b56-408c-89b2-d9cdc54982f8	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
28d02615-b8c4-4a69-a354-55c356693ce7	6eb89f66-661c-4294-85b4-044519fdec1b	987066f3-edd3-454f-9f5d-0cfb5e55c1e0	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
26b0770a-4737-49ed-8302-daffbdf011c1	6eb89f66-661c-4294-85b4-044519fdec1b	62aad12b-d9fd-4fa1-8d80-3f93bd42d2b6	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
68091736-63d7-426e-a284-6060a9bdfb52	6eb89f66-661c-4294-85b4-044519fdec1b	fd85f52e-0065-4fbc-bb94-1465b1d154ee	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4ded6a6f-8c80-42e7-888a-3c77497624eb	6eb89f66-661c-4294-85b4-044519fdec1b	5cbddda4-b4af-45d7-b913-de01a9a72cd5	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4be270f9-e5ae-426b-83b1-3eab16d00156	6eb89f66-661c-4294-85b4-044519fdec1b	ce3bf15e-84fe-4ce7-a10e-1a26ec8acf05	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0ab87110-3e91-4981-8239-ae4d8809bcf1	6eb89f66-661c-4294-85b4-044519fdec1b	bf98b52e-f41b-4308-906b-3ab72d075a9a	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9212bee0-09cd-402f-bb4b-5a5c54f58b08	6eb89f66-661c-4294-85b4-044519fdec1b	57ba4cb0-d12f-4e87-81b2-b384cf4e8cb7	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
87b9386f-92a0-40f9-9247-6b24ee791d1d	6eb89f66-661c-4294-85b4-044519fdec1b	553ac569-2406-4dba-b5f2-dcd928b95787	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
806d87ee-0ef8-4b19-8594-5b64898b651c	6eb89f66-661c-4294-85b4-044519fdec1b	59985ea0-e5ff-4cf2-9858-7ba48ee722be	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7098f665-1e27-4288-a647-49c2f37be594	6eb89f66-661c-4294-85b4-044519fdec1b	59e2aa6a-bb1c-4f29-86e6-d7980d954d46	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8f010548-9234-41ed-a71b-f0b7f4908459	6eb89f66-661c-4294-85b4-044519fdec1b	fe1cc623-5749-4759-bb79-c08f0e00d4b3	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
baad2577-9b59-4189-89c7-c7d637ca0511	6eb89f66-661c-4294-85b4-044519fdec1b	18f5b5c1-e9df-4769-9ec2-38abffd9fa3c	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
24b63274-c15c-47e5-9f25-5ff7b177b8cf	6eb89f66-661c-4294-85b4-044519fdec1b	62c2253a-293e-4954-806a-f893f400e55d	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b2707e24-29bf-44bc-9566-95e2fdefe440	6eb89f66-661c-4294-85b4-044519fdec1b	f390a5a5-476c-4a52-89cc-bae5384a9ab1	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bb91f33c-8ee1-4051-97f2-ae8b40aa9364	6eb89f66-661c-4294-85b4-044519fdec1b	96787c99-a0ce-4332-8f26-f2297f87dcd8	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
95bd72d8-0de1-4302-acc4-e88c4ac0cf06	6eb89f66-661c-4294-85b4-044519fdec1b	e6608ce5-674e-4c3a-ba90-6772391d4949	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
35c1fab6-aa36-4b8a-bd76-c87eeb94b813	6eb89f66-661c-4294-85b4-044519fdec1b	8f49b43c-be61-4c6f-95dc-4e8a7d10e7da	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8b6cddb1-12c7-4644-9b48-68e11de95f7d	6eb89f66-661c-4294-85b4-044519fdec1b	b128ec84-8ee0-470c-a38c-7ed96269ee68	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
31a31064-2f64-4f80-a81a-30c642396915	6eb89f66-661c-4294-85b4-044519fdec1b	82657f8f-f8ad-49ec-bc2b-bb8fa993f67d	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
47d4b3e0-74f9-4475-8707-7e76e8cb3908	6eb89f66-661c-4294-85b4-044519fdec1b	3b91dfb2-fd88-45f2-928f-0c9a02394b62	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ebd5d373-d85f-4c1e-999b-c26005334292	6eb89f66-661c-4294-85b4-044519fdec1b	9ad814cd-f7ba-4d29-a113-805dbc651c60	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ceca7019-197e-4e29-afc6-ab2b0366369c	6eb89f66-661c-4294-85b4-044519fdec1b	efb317af-7eac-4f9f-8f63-7883c2982ede	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9e5d5404-b6ee-4aeb-872b-c93eb2e6ba9c	6eb89f66-661c-4294-85b4-044519fdec1b	1021ee4c-7743-4e51-a5a4-164a2ea3d842	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb78347e-b440-4f34-a189-9cec18e8eebb	6eb89f66-661c-4294-85b4-044519fdec1b	43301ae3-93ac-4bb3-b023-dd39d37de9f6	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e8fc9ac5-cda5-4859-b4a4-d2ec678c09c4	6eb89f66-661c-4294-85b4-044519fdec1b	30c26e10-38c4-4254-aa2e-0d42f352c023	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8f1e3820-7885-4208-8841-e014425d582b	6eb89f66-661c-4294-85b4-044519fdec1b	a0ebae73-9f25-48b3-8fd5-b05ba844d222	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f275e8aa-61e2-4211-8200-6a6373163674	6eb89f66-661c-4294-85b4-044519fdec1b	41fd61ae-6fe9-42b0-9c0e-4818f153ffa0	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b2d127b1-82f8-4b54-a199-559959cd5dc2	6eb89f66-661c-4294-85b4-044519fdec1b	74e0df2b-4c04-4518-b484-d6425e13ea74	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
30a3b30a-efed-451d-bdea-09bde2989dea	6eb89f66-661c-4294-85b4-044519fdec1b	089157e1-3de5-4c32-9c69-6445d78edc1f	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
362ffb34-ae60-485c-838d-fc8db39f6b1e	6eb89f66-661c-4294-85b4-044519fdec1b	feca6731-d1ec-48de-952a-aba8ad404db3	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
377ce9e5-a5e7-4c63-8633-1609c8481664	6eb89f66-661c-4294-85b4-044519fdec1b	957c1e64-7e5a-4c17-8f27-1a4944de6a3c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3c1dec46-2632-441a-9850-e6fd45f6bc57	6eb89f66-661c-4294-85b4-044519fdec1b	18a6da15-b4b6-4225-b473-c5c0eeddd5ce	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
964b7dd7-643c-404f-9e70-1afd317a5f99	6eb89f66-661c-4294-85b4-044519fdec1b	1c1054e1-1106-4a8b-8230-f9bbe7b2e4d8	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c7ca845f-47ef-4ab6-8345-f490cb7fb7f7	6eb89f66-661c-4294-85b4-044519fdec1b	458c8f44-4178-4ad1-82aa-e1fafd1df65c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5053a3e2-099c-4f51-8250-bc43dc225da1	6eb89f66-661c-4294-85b4-044519fdec1b	cf42f76f-bfc1-410f-8cd2-f6b1a32f94e8	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
73cd9195-08db-4b44-af82-276b3b61c86d	6eb89f66-661c-4294-85b4-044519fdec1b	0b171841-6ee4-4fc5-8ac9-2b19d4a2c65d	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9198b225-a0f1-4ba2-b774-dfe376f6af53	6eb89f66-661c-4294-85b4-044519fdec1b	baaaefc8-3ba7-414d-ace8-650ade2f98db	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6907cde8-1789-4bae-89e0-1c1f34f7904f	6eb89f66-661c-4294-85b4-044519fdec1b	17bb19b4-e16b-4a51-8531-b7da9cbff8f0	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e28b03cf-931e-4430-ab58-ef5ae3d08497	6eb89f66-661c-4294-85b4-044519fdec1b	409b244f-7dfb-4c7b-8686-a079379ded1c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
46ab8d60-1f0c-43bf-9c2a-61fddeb05e7c	6eb89f66-661c-4294-85b4-044519fdec1b	52f4509d-b071-4aa4-930e-e01e97e4302f	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
40e80cc8-3360-4e65-aafd-d91f8df053e2	6eb89f66-661c-4294-85b4-044519fdec1b	531f9c5f-5fce-4446-bfe8-ce270e4f629c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
da17c999-042b-489d-be07-368263237546	6eb89f66-661c-4294-85b4-044519fdec1b	b76156d6-7d71-47c8-aa45-a951287ebd9b	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
897afbc1-e522-46a5-8611-c9e15507d3ba	6eb89f66-661c-4294-85b4-044519fdec1b	20dd1625-14f7-477f-8f1c-5c929edb9956	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c7bc321b-9a7e-409c-9c11-fb2032096d31	6eb89f66-661c-4294-85b4-044519fdec1b	83070134-6fdd-4816-b2a3-6c37e96e22fe	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4450bd08-97b0-4ce2-a997-f80575fa0650	6eb89f66-661c-4294-85b4-044519fdec1b	44d0cc09-3bd3-4408-a54b-fa2840a6d5f3	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d9b0be7d-f189-4be4-9e34-50737795c88d	6eb89f66-661c-4294-85b4-044519fdec1b	dd5dbea6-ee71-47b6-b10e-cd736d5988aa	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
40568fcd-3488-4295-a151-8d2744767057	6eb89f66-661c-4294-85b4-044519fdec1b	ac156f84-4748-4ce8-a4f6-4bb26b4839a9	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ae0afc89-12a8-4935-a13a-eecebe046457	6eb89f66-661c-4294-85b4-044519fdec1b	68d16bc7-866e-41e2-9f90-79086232128f	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
478510c5-5f35-49e6-a3db-696166003f3e	6eb89f66-661c-4294-85b4-044519fdec1b	a4e76dd4-4d79-44f4-96c6-fc4eb6391677	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f50638ec-2552-497d-ac61-c6f257468d42	6eb89f66-661c-4294-85b4-044519fdec1b	28c1d342-6d69-4c31-8afd-693ac1d32db5	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00c03b36-4b7f-437a-b150-6a8b705a6704	6eb89f66-661c-4294-85b4-044519fdec1b	70afac5e-7487-494c-9737-9ba5323e9a7e	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cbba7fe8-b457-4a8d-8d0f-694998d9f78d	6eb89f66-661c-4294-85b4-044519fdec1b	b15d206c-d5ef-4d69-b660-1f06272c10e4	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
78127e82-ecba-448b-865a-6d92d26d293d	6eb89f66-661c-4294-85b4-044519fdec1b	5073e567-0d72-4e94-b697-79e1cd408def	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
376b6abf-1eb6-44ee-afe8-0c0168744115	6eb89f66-661c-4294-85b4-044519fdec1b	936473d2-bdc9-4727-92d1-6e8762ad2b65	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
35cca11d-d422-47d9-a209-afc6ec8f8be3	6eb89f66-661c-4294-85b4-044519fdec1b	10bef495-7255-4638-bdfb-7b8df9c37423	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
25635fa4-f6f3-4a52-b730-e5a220ffba32	6eb89f66-661c-4294-85b4-044519fdec1b	197d1458-b83a-455c-8db5-267a616501a7	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b754498c-5913-4ce2-b0d5-11fba13e8fbf	6eb89f66-661c-4294-85b4-044519fdec1b	2c88e468-33fb-4346-a92b-b514a7e3797b	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9ee3d1f3-3258-4125-bac2-5b2273141bc6	6eb89f66-661c-4294-85b4-044519fdec1b	842e1d5a-feda-4096-ae06-5bf538545e31	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
19d44d19-493c-45e8-95c2-8da472b81a9d	6eb89f66-661c-4294-85b4-044519fdec1b	bf821156-45fe-4ab3-a13e-8d7aab0d3869	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7cf156bf-d649-44d1-8c92-1d51c756a687	6eb89f66-661c-4294-85b4-044519fdec1b	f7112f63-6f6d-4a33-9362-d4ffafcf339b	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9b998677-76b6-4d9a-88dd-c508d2b41e92	6eb89f66-661c-4294-85b4-044519fdec1b	17639dfd-b136-44c4-9284-232bdc865000	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
45258962-e3a4-4584-95af-8c8cef3ba585	6eb89f66-661c-4294-85b4-044519fdec1b	888933f7-ca51-41b1-90d9-45ceed3a99ca	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4bc40904-bc44-4035-997a-bf13bdbe1149	6eb89f66-661c-4294-85b4-044519fdec1b	b73cb807-821d-4f6e-8c71-78b5c5310bed	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1751d540-79c4-4f70-99f3-e7bfd9cf93a6	6eb89f66-661c-4294-85b4-044519fdec1b	907dad10-e38e-4af2-90fe-d41212bf51cd	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c54fbb85-52f1-43c3-a6e5-f2d8a257efd9	6eb89f66-661c-4294-85b4-044519fdec1b	05893119-03f8-41ea-88c4-bd840e95c2ac	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4db610d4-0910-4a1b-98f6-c623c3aa56ad	6eb89f66-661c-4294-85b4-044519fdec1b	9e20a739-67ac-4085-b5b0-1d3540deddde	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
295c2c61-3a20-4e28-a63a-3ff24ffcae65	6eb89f66-661c-4294-85b4-044519fdec1b	3abc05b6-c5ea-459f-b7b3-68a93ceb0ed3	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5d2785b0-1206-4e87-af50-649adab8726a	6eb89f66-661c-4294-85b4-044519fdec1b	0e0dbf1e-b47a-4db1-9c9b-4aa4500722eb	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9b4c9262-37fa-4b02-9ffa-618dc3f4aa45	6eb89f66-661c-4294-85b4-044519fdec1b	c7e79fd6-9cb0-4527-ba8a-09da1d2f918c	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
25974117-ca85-4c4c-96ec-8c1b3161c907	6eb89f66-661c-4294-85b4-044519fdec1b	8f8f3c91-2d26-4ded-9225-395ae9042f11	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d3f8ec9c-3bb9-4182-8055-30f7d4cc2d09	6eb89f66-661c-4294-85b4-044519fdec1b	d571b7dc-eeb9-453d-bdfe-33c2ba653cdd	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b9d3c372-7560-494a-9157-0402e87d106f	6eb89f66-661c-4294-85b4-044519fdec1b	0aaa74f5-6f91-4b5d-9dd3-5b7ed925964e	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b8e394e1-9491-4f52-b558-bf12b093c24f	6eb89f66-661c-4294-85b4-044519fdec1b	31f83c6b-72a9-4c79-b1e9-6bdef5b894e8	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
79727737-b71a-4625-83ae-0bcc0ff961fa	6eb89f66-661c-4294-85b4-044519fdec1b	6b9f3fa5-d64a-4023-9f83-f0bf27bdb0e2	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7bee6cb2-dbf4-4ebc-88df-f1ff534978d8	6eb89f66-661c-4294-85b4-044519fdec1b	27e673a4-366a-46f7-be9d-409e61e48a7b	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2b39ee27-f388-48e4-8321-f568b5c0b247	6eb89f66-661c-4294-85b4-044519fdec1b	27e673a4-366a-46f7-be9d-409e61e48a7b	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d750a096-1d32-469f-b5b1-bf8164ff7079	6eb89f66-661c-4294-85b4-044519fdec1b	3dd5f85d-f466-479a-ad01-2f45c32fc196	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4047ef6d-c2a9-4fc3-bb06-f895e7c27b63	6eb89f66-661c-4294-85b4-044519fdec1b	564de578-2d66-4c50-8163-ab02b5a10663	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2d422a41-3940-47c7-87e2-8e57987edfbe	6eb89f66-661c-4294-85b4-044519fdec1b	564de578-2d66-4c50-8163-ab02b5a10663	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
62b355fa-92a6-4e92-b44e-3f46bbdb2ead	6eb89f66-661c-4294-85b4-044519fdec1b	42b8e3b1-90ca-416a-a471-1f851ad03abc	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
352696ed-4653-4e3c-8d63-62c300fb3fc8	6eb89f66-661c-4294-85b4-044519fdec1b	b73de201-00ce-40ec-947c-f1159a500794	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f4f88bba-f719-4ae3-b51e-0e3ec57dafab	6eb89f66-661c-4294-85b4-044519fdec1b	e434f5a9-2005-4d7d-aa4e-051a7c10fa17	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a8ccab40-b41c-4869-81f6-2b8b98fb6e31	6eb89f66-661c-4294-85b4-044519fdec1b	ba8f6800-1286-42c7-b362-c24844b700ea	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2575c807-19cf-4bcf-a291-97197e7eb99a	6eb89f66-661c-4294-85b4-044519fdec1b	2147a1de-ca25-43c4-adb1-7219bda6216f	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d12c310a-8a2a-4d3e-a869-0862b2601d5c	6eb89f66-661c-4294-85b4-044519fdec1b	9726018c-4bfc-472f-8033-bb15a844772d	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0bd7b024-ec4a-477b-bd91-164766ee2c67	6eb89f66-661c-4294-85b4-044519fdec1b	a08f430c-116b-4eb3-841d-d8d09c2f743c	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
25163081-d737-4336-a02f-b7e1ffc70e83	6eb89f66-661c-4294-85b4-044519fdec1b	3a3e183d-acd5-4e33-88e4-243fb0d99faf	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a2a953fd-8f6c-4bdb-b136-93d6413a1ceb	6eb89f66-661c-4294-85b4-044519fdec1b	c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b918cf81-13e6-43a0-92be-9cca6f5d3fe1	6eb89f66-661c-4294-85b4-044519fdec1b	af6a1c14-e2af-435a-9a9d-bac3d66c35b7	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b124a3b5-44a9-410c-8eaf-1acc7c94d0fd	6eb89f66-661c-4294-85b4-044519fdec1b	74f3ed80-98af-440a-a347-3f32e4be27aa	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e6bead6-fcba-4f68-b531-6cfe393817b4	6eb89f66-661c-4294-85b4-044519fdec1b	72602fd8-2dd5-4d51-8280-4408e4a138a5	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cfd457d4-5a99-4258-9a23-2458f1a4871f	6eb89f66-661c-4294-85b4-044519fdec1b	495c9a9e-6d98-440d-850d-3791071e4e95	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a4abc93a-9963-4b38-86ad-467649085f69	6eb89f66-661c-4294-85b4-044519fdec1b	2f9da69e-71b4-4b2c-919e-1500bc55a630	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a8edca23-91f6-4c48-9327-911f22f1d641	6eb89f66-661c-4294-85b4-044519fdec1b	b4a855a2-bfa8-41ee-9173-998bee08316f	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e75341d5-6877-4ce2-9c3c-d6577c0f8e07	6eb89f66-661c-4294-85b4-044519fdec1b	7249055c-e681-4d1f-ae2f-28c471a3af05	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
edbca1ef-da7c-4d2f-9878-d3479463ffe6	6eb89f66-661c-4294-85b4-044519fdec1b	e440b879-0e0f-4692-8c4b-4b10c6d0cf01	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8aed30fb-3a5f-40fc-a3f0-ec24237382a1	6eb89f66-661c-4294-85b4-044519fdec1b	b7aefd26-9f98-454d-a476-ae7c9ce54387	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
37dd9722-22bd-4661-a45b-7531c3b5b8b0	6eb89f66-661c-4294-85b4-044519fdec1b	2aa2f082-a408-4c05-b518-dd2ce8ad640b	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
87551bb8-b76a-43b8-8074-e062baffa788	6eb89f66-661c-4294-85b4-044519fdec1b	c824e963-ab76-4ae7-af4b-8976832f6fec	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a1583bfe-8909-4c82-abaa-85d6258acdf2	6eb89f66-661c-4294-85b4-044519fdec1b	a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e2d7a238-3a4d-40fc-9480-8f84cbc6c1d6	6eb89f66-661c-4294-85b4-044519fdec1b	846c440c-57b3-4d15-98e8-9d3ea4d01392	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6d62cc02-9000-4713-9af1-526b2606d35d	6eb89f66-661c-4294-85b4-044519fdec1b	5646f259-9143-4afe-823e-a993ad4c16ae	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
badf461e-2846-4de5-a79f-7ec4da7d3424	6eb89f66-661c-4294-85b4-044519fdec1b	c69dd883-7035-4781-92d5-e12b0b0bf97f	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5d235658-7378-4153-8987-ff2d7e117b90	6eb89f66-661c-4294-85b4-044519fdec1b	da7f5c17-06eb-45e3-b48c-90ab6ae078f1	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b252a99c-279e-42c4-942e-1c2841faa4b6	6eb89f66-661c-4294-85b4-044519fdec1b	63b03555-2ec3-4271-a8d5-43f8e1a92a6d	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ad4f7d37-69e6-47c0-be6c-cbed461b72c0	6eb89f66-661c-4294-85b4-044519fdec1b	5567dd12-02bc-47df-b4e6-88b58026bfa2	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1425d3f2-5e4b-45de-80d8-ad2bb54e67be	6eb89f66-661c-4294-85b4-044519fdec1b	78ac9d50-be7c-4701-af65-e8e4ea0e2276	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
91be4448-fc88-4135-8b32-444691ed92dc	6eb89f66-661c-4294-85b4-044519fdec1b	0c646133-3a61-494d-8779-db533c0980d5	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fd29bd95-c161-402b-856a-b2faa4f086de	6eb89f66-661c-4294-85b4-044519fdec1b	6acecc37-452e-41cf-bbfa-fa29139985c1	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f0044ebb-c7f6-487a-9f66-1947437cb008	6eb89f66-661c-4294-85b4-044519fdec1b	521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5a42ba64-0c4d-4666-b0b9-9ec9203f2d96	6eb89f66-661c-4294-85b4-044519fdec1b	a7bbba94-e82b-4749-8101-c65fd8ff3449	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fc18105a-396b-4118-a72f-54685238ebd0	6eb89f66-661c-4294-85b4-044519fdec1b	c609e1c5-2949-4d3c-bfc3-b61c164c9192	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0b622f66-598d-4717-8da7-1775c425acef	6eb89f66-661c-4294-85b4-044519fdec1b	3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2d1124b2-c48b-4659-87e3-3c67714295c9	6eb89f66-661c-4294-85b4-044519fdec1b	461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1628dc16-7878-4aa0-ac86-03dcd2ac7dba	6eb89f66-661c-4294-85b4-044519fdec1b	b5394775-5207-4242-84c5-6917d840bc4c	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3312f484-f269-49ab-bfa2-0d79c2a94cff	6eb89f66-661c-4294-85b4-044519fdec1b	94063735-6495-4abf-91e3-e0eb80aa13b7	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b3c78702-11b8-4a03-8f27-f2da9f27497f	6eb89f66-661c-4294-85b4-044519fdec1b	fa97e202-e534-4210-ac26-29a34f1f38fc	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
12e6adf3-deb9-47af-80b4-4cab7ee6f63d	6eb89f66-661c-4294-85b4-044519fdec1b	bcb56064-a124-44a7-8649-79970c8b6758	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d10fdff0-1449-44df-b676-a7d6389ae8a4	6eb89f66-661c-4294-85b4-044519fdec1b	64faab0b-643b-4a14-8c5d-c5718dd127b0	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f89dc314-d063-4ebe-8bb9-c348dd3a577e	6eb89f66-661c-4294-85b4-044519fdec1b	89aee119-46f9-4a9b-afd7-6551885362ac	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8757c0a2-ec56-46d8-9aed-a030c35350b4	6eb89f66-661c-4294-85b4-044519fdec1b	4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ae18d74e-d790-477e-a35f-885fc8b17656	6eb89f66-661c-4294-85b4-044519fdec1b	e81df99b-a120-4110-8f48-0c5cbdbec19b	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
35a1ce49-4cc5-42ba-9555-e9afc4b51d60	6eb89f66-661c-4294-85b4-044519fdec1b	d5d5b1b0-97b5-42e8-ad5c-467225669d07	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2a89906a-fdd4-4c88-87fb-8c604368bf4e	6eb89f66-661c-4294-85b4-044519fdec1b	7c954edb-f3b0-45b1-a0de-1b20a086d060	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
baf0c0c3-5526-4992-a858-3ae0379c2b73	6eb89f66-661c-4294-85b4-044519fdec1b	9f608fd0-bde7-48da-a77f-c78ff68bd777	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ff663679-0853-4622-979e-ca6b0efdae66	6eb89f66-661c-4294-85b4-044519fdec1b	b460dc4d-a2a1-4ef3-bc68-172a30959cf4	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6b346e4d-f7d8-408b-baad-c7e3c4c68877	6eb89f66-661c-4294-85b4-044519fdec1b	7ed15acb-1b78-444d-afb0-c9cabfd76b12	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
30abba56-4efc-44f4-9b10-c9ee1e66a71b	6eb89f66-661c-4294-85b4-044519fdec1b	4ff69e50-609f-4f1e-a804-2d631ecc1b44	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
83ff8da0-bc8d-45f6-bcae-dd9ba8ab6501	6eb89f66-661c-4294-85b4-044519fdec1b	b3520f26-f8cf-4933-aff2-1e8303f483d9	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f78c5346-541d-408b-a444-93f9472f5628	6eb89f66-661c-4294-85b4-044519fdec1b	ab6a60e1-0283-48dc-b606-544963dde3b5	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e2da7c83-aa80-4129-8ada-3b19af8c32d3	6eb89f66-661c-4294-85b4-044519fdec1b	892c73ce-28dd-4546-a0fc-cebb44769bd9	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bdc2fe55-3e5e-4059-8cc5-14288fb42b13	6eb89f66-661c-4294-85b4-044519fdec1b	da969ef4-1721-4442-a71d-3db403d42fe9	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5f5146ca-3e62-4bab-bbaf-8a34152c5135	6eb89f66-661c-4294-85b4-044519fdec1b	34aeac9b-bdda-4d8f-bbc6-41a089862e6a	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
aec5eec7-c4a8-42be-9032-9187afd4596a	6eb89f66-661c-4294-85b4-044519fdec1b	f41a672d-54ff-457a-88ea-4a8427177b75	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e295dc30-f0d6-4bb9-b335-d048e12176e9	6eb89f66-661c-4294-85b4-044519fdec1b	d318b34e-2e38-44fc-8583-a25e6633fe34	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
53782a1d-39f4-43f7-8c33-e7b969523769	6eb89f66-661c-4294-85b4-044519fdec1b	0b90507a-d4ea-4f8f-908a-eca651ed29d6	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a20b1a3a-0e00-45f0-a6c9-730f80dd1f3d	6eb89f66-661c-4294-85b4-044519fdec1b	200af72d-ada6-4ad9-a2a9-8ac90c9ee26d	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f780ef72-7c5b-4a6b-806a-61d13ee82ff8	6eb89f66-661c-4294-85b4-044519fdec1b	a9fc938e-3eda-4477-9261-e13687c777fd	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4567cf30-d314-4d45-b3b2-8ff6e2cd9ef3	6eb89f66-661c-4294-85b4-044519fdec1b	d3a30467-6180-45d0-8f97-0516a39191e4	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1861ffcc-8a23-4735-8857-3d56aaf1d9c2	6eb89f66-661c-4294-85b4-044519fdec1b	89397364-5cd1-44ea-8ea7-68a8c0cc5fe6	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ca1ab563-1f3e-498f-bd60-3ca74b49b575	6eb89f66-661c-4294-85b4-044519fdec1b	3ea54e45-7aac-4cf2-b790-cf68417159f5	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2d9fac7d-611e-4cc7-acea-25c7633427b2	6eb89f66-661c-4294-85b4-044519fdec1b	aa5f3b2d-ae8a-40d2-81f0-68878ae09721	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
07a898d6-a120-4532-81c7-7af0ba39e3e5	6eb89f66-661c-4294-85b4-044519fdec1b	fc885a0f-9531-475e-a49e-1aa26cecbb5e	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
265d2200-617d-437c-bbc0-e8b949d46b08	6eb89f66-661c-4294-85b4-044519fdec1b	8dde0f7e-7023-4469-9240-e9e428b1640c	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
262fd200-a3a0-4ac3-90c9-efe14c8f641c	6eb89f66-661c-4294-85b4-044519fdec1b	f163594e-9c10-4c15-8184-183411d6dcfa	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
77f0c8e7-f41f-4646-91f0-6bef736cd980	6eb89f66-661c-4294-85b4-044519fdec1b	c5618b42-8182-4dca-868d-edf91bbd5249	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7fbbd834-3f0b-48e5-b12a-9b40b2a85321	6eb89f66-661c-4294-85b4-044519fdec1b	a1514e63-efa6-4ab5-8068-aa531ddcc480	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9a479616-a876-4299-b185-b6355bc4c04c	6eb89f66-661c-4294-85b4-044519fdec1b	80900d89-757f-45f1-8df1-574a5e4f38c7	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
80d74c8c-6aaa-4180-b22a-f8d8841ff0de	6eb89f66-661c-4294-85b4-044519fdec1b	b51b7764-5d21-47c2-aaa2-a54ef06e695b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ec9cdb28-c4b4-441f-a69f-a66d7123ac81	6eb89f66-661c-4294-85b4-044519fdec1b	1e0d6501-b15a-4c5b-8856-e0668473540e	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b8ff2d1b-b54c-465a-ade2-67a922734aad	6eb89f66-661c-4294-85b4-044519fdec1b	db5f2886-4e5f-46e9-86ee-9eec449e4845	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
407d4e4f-ad08-45c5-810b-ebe2bf2ef703	6eb89f66-661c-4294-85b4-044519fdec1b	2cbd132b-f48c-4282-b637-eae87931d57c	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a2652d28-a9e9-41a0-b9d5-89911a7767ea	6eb89f66-661c-4294-85b4-044519fdec1b	32bf89c1-cc50-4e3b-a578-7342f0a98052	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
452ec1c1-70eb-4358-9042-967b086650e6	6eb89f66-661c-4294-85b4-044519fdec1b	53bbe15d-011a-453c-8c75-da4e0201bca0	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d60ea764-0c34-46bb-8bb3-47776af188aa	6eb89f66-661c-4294-85b4-044519fdec1b	f4b8d658-d725-45fc-93b0-038fda5d7b3d	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
379a0248-b397-4490-8209-e21d84b718c5	6eb89f66-661c-4294-85b4-044519fdec1b	860edeb4-f127-4442-8362-7e0eb45d26ec	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
226b0ba4-96f7-409f-ab8b-e3d362972542	6eb89f66-661c-4294-85b4-044519fdec1b	3aed2bdb-cc98-41f1-b690-f4665163a2eb	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
628b7aea-3038-47ae-97db-33b3ab44eb91	6eb89f66-661c-4294-85b4-044519fdec1b	8a60ac28-8785-495b-b891-7cb5e051043e	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
82878e43-1e53-447b-860d-31514809cddf	6eb89f66-661c-4294-85b4-044519fdec1b	c3142cd7-e447-4ac7-a995-e49aa1c1c5fa	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bec32565-239a-4eb6-a756-2376e3d075eb	6eb89f66-661c-4294-85b4-044519fdec1b	d0ce2e68-aff0-480b-b966-ee2de6d73e98	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
88deb253-d498-473b-b411-7ad8e9b8b109	6eb89f66-661c-4294-85b4-044519fdec1b	62643175-94cf-441a-8b44-dd4855b9d689	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5f851f8a-7448-4b3f-9a61-6fcee9aabb7b	6eb89f66-661c-4294-85b4-044519fdec1b	ea5d0570-7042-4fa6-a6b3-c24833d2581f	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f2fca901-a4fc-4129-966c-e7de536df252	6eb89f66-661c-4294-85b4-044519fdec1b	733d05f9-efba-4218-b6aa-d0cd89bac606	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fe473866-c735-4042-8d76-ddea5b95da5b	6eb89f66-661c-4294-85b4-044519fdec1b	74727645-5f46-49e5-9644-3b3d73950cf4	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
063a82fd-c002-47c4-be08-d464b1e955f6	6eb89f66-661c-4294-85b4-044519fdec1b	d880bd2d-f77b-4456-91fd-79e2f207f255	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0d7d4131-ce62-4ef1-8654-33f9c755f186	6eb89f66-661c-4294-85b4-044519fdec1b	445e368f-5795-4ecb-a085-0a1f7cba64d7	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6ee0fb81-8615-4fbe-9d43-1ee6ca1f8466	6eb89f66-661c-4294-85b4-044519fdec1b	21f5887f-0d44-4145-9ea3-7bd6bbcd64e9	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3b5f0597-56f1-421f-a0ee-2c22fe412b78	6eb89f66-661c-4294-85b4-044519fdec1b	444af49d-152e-4a78-8cf4-7b8a69d039c6	09af9996-8431-46ea-aa3c-de863550af06	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c8d31348-8ae7-47e6-bc84-8bb2caf702ad	6eb89f66-661c-4294-85b4-044519fdec1b	d8193183-10c9-42c9-bcc1-fc012e110627	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1f9dc7e1-36b3-4148-8150-0fe2a9a78590	6eb89f66-661c-4294-85b4-044519fdec1b	5553c740-38e4-43f3-898a-5d59b5a0320b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
715e8efa-5d91-4cb1-99d6-da99e40f8d4d	6eb89f66-661c-4294-85b4-044519fdec1b	b1f7769a-5711-4944-b359-43a02ce6b82c	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
99c8bfeb-48ee-42ec-9467-8820478cae1a	6eb89f66-661c-4294-85b4-044519fdec1b	4502d2e6-f45f-4f50-b1cd-1f905e9cc518	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d1670b1d-3a51-4cc1-815d-01c7e3626f3d	6eb89f66-661c-4294-85b4-044519fdec1b	0080a492-5c32-4048-9f36-95788b5271ce	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
48566537-924c-487c-86b9-116e56073759	6eb89f66-661c-4294-85b4-044519fdec1b	559abe90-0de6-43d3-8dd2-932712b78a62	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8b6043c3-d46c-4d8f-85e6-1a27fa56c367	6eb89f66-661c-4294-85b4-044519fdec1b	dae5f7b5-abd0-4afd-ba03-739065d56b35	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b2483d3e-65e0-48e0-8cc8-d602fcfa8084	6eb89f66-661c-4294-85b4-044519fdec1b	dae5f7b5-abd0-4afd-ba03-739065d56b35	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2fa86b02-5556-4168-98b4-cfa2949d0caa	6eb89f66-661c-4294-85b4-044519fdec1b	59570f9a-8658-4f5c-b326-6bd30b07d043	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
249d4966-0237-41d1-adb0-3be5a5de57d0	6eb89f66-661c-4294-85b4-044519fdec1b	59570f9a-8658-4f5c-b326-6bd30b07d043	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
49a10958-c756-4567-9ff4-6c330c719a47	6eb89f66-661c-4294-85b4-044519fdec1b	dbfda102-ce20-4cde-be8b-e8df65c9f7db	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
79ad809f-d83e-487f-ae56-41f30124ba18	6eb89f66-661c-4294-85b4-044519fdec1b	dbfda102-ce20-4cde-be8b-e8df65c9f7db	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8ef4ee10-2094-47be-94b1-c677511a0435	6eb89f66-661c-4294-85b4-044519fdec1b	478355a4-a104-478a-9161-38812c682f28	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cccc2212-54b1-4680-a92a-a0784c0f273c	6eb89f66-661c-4294-85b4-044519fdec1b	478355a4-a104-478a-9161-38812c682f28	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c0c125a8-05c9-4a2e-86cf-7dca25f840a8	6eb89f66-661c-4294-85b4-044519fdec1b	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2f5509ec-2551-40aa-bb87-7690b33b7802	6eb89f66-661c-4294-85b4-044519fdec1b	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d794282b-6955-494e-a2ed-70398a1d5cf9	6eb89f66-661c-4294-85b4-044519fdec1b	0009b8a7-676d-497b-92e5-1c9f19a6a9dc	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2fdfa669-3456-4947-acc0-75fa1d85a42c	6eb89f66-661c-4294-85b4-044519fdec1b	61592f67-7a2a-4060-8f95-6ff7aaf552a4	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
527bc2d1-d838-46b3-94ef-591118420cb1	6eb89f66-661c-4294-85b4-044519fdec1b	61592f67-7a2a-4060-8f95-6ff7aaf552a4	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9af4d545-5b84-4045-9f39-c8c552ccfbb3	6eb89f66-661c-4294-85b4-044519fdec1b	32dce3db-9b6c-41de-ac5b-db2f1f7cf1b3	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e1771bee-0f63-4310-abcb-f6bca7ed9612	6eb89f66-661c-4294-85b4-044519fdec1b	c6c82907-0a2b-4424-8cff-e0d399e82e76	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2c33931f-5484-46dd-a45d-34be8966185e	6eb89f66-661c-4294-85b4-044519fdec1b	c6c82907-0a2b-4424-8cff-e0d399e82e76	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
945e0aa2-e3ca-4f34-9e5f-4129d63dfafd	6eb89f66-661c-4294-85b4-044519fdec1b	e5b62ff6-5d19-4041-bce2-51eff5619079	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7f2842ae-9eab-4307-91d1-da9c33a7c378	6eb89f66-661c-4294-85b4-044519fdec1b	37706f7f-3212-45bf-bbde-a9bd58d7d93b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
134fe13a-499e-463a-859c-64e1cce87127	6eb89f66-661c-4294-85b4-044519fdec1b	dbc10961-9d8a-46f5-8635-d611caac9351	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cda35c17-8c0c-4e62-b9fa-9a23a1b23798	6eb89f66-661c-4294-85b4-044519fdec1b	df1246cc-bae0-4d4e-8674-fb6af39b15bb	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
592df5b2-b3de-45ea-98f5-03e544c8abe6	6eb89f66-661c-4294-85b4-044519fdec1b	8449c926-5c66-43b3-9321-40108f2884a1	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e53dd22-857a-4a33-9bdd-ade7cbadadd6	6eb89f66-661c-4294-85b4-044519fdec1b	8449c926-5c66-43b3-9321-40108f2884a1	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6988db58-25d8-4420-9a2b-0187a26505c9	6eb89f66-661c-4294-85b4-044519fdec1b	d78ace28-ecba-444b-b9de-cee545cef5fa	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7b6f4155-0160-4a7a-9b45-1fddaa80994e	6eb89f66-661c-4294-85b4-044519fdec1b	f3245aa9-e6a6-408a-b9ac-a82c54845984	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
34faaf3b-cc7c-4f01-a977-fcec74b8374f	6eb89f66-661c-4294-85b4-044519fdec1b	29768ea2-2372-4fac-afa4-8025fe024c78	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1eafa00d-0ed5-4599-b7d5-bd8a79fb2d5d	6eb89f66-661c-4294-85b4-044519fdec1b	4d6a444e-3a91-4914-a852-50c6748c5862	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
770a1af4-5ccb-4d89-9073-b747230b5a4d	6eb89f66-661c-4294-85b4-044519fdec1b	3987c83b-d17b-47d0-86c9-2ca24d25f4ee	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3579b7d2-eb3a-42a1-bc61-95bb15f17d59	6eb89f66-661c-4294-85b4-044519fdec1b	7ce551ca-251a-4082-b60c-f615b8f08c77	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a0eaf4c5-1a4a-47e5-a47c-d4993bf6bc2c	6eb89f66-661c-4294-85b4-044519fdec1b	8435ee66-9b87-47b6-9af4-0700ce6186fd	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dd9ed15f-2d12-435b-82e9-3a55a4ce008a	6eb89f66-661c-4294-85b4-044519fdec1b	ee0d0a1f-a784-4df7-9212-aa576b3ad098	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
05194778-1e0c-4185-bfdd-f83e183028f2	6eb89f66-661c-4294-85b4-044519fdec1b	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cdd54fa2-9d1a-4a56-aa2b-f01517147958	6eb89f66-661c-4294-85b4-044519fdec1b	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d2fac192-9280-400f-bd35-d864ec167d6a	6eb89f66-661c-4294-85b4-044519fdec1b	bee9a02e-7117-453f-aca2-8a99fb44d5c3	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ed448855-db3f-4a5b-ae88-3e259152a242	6eb89f66-661c-4294-85b4-044519fdec1b	88dc009b-c5b7-4978-800c-4a8202048808	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8746b791-b61d-4420-b645-a8dc6e1f8d1f	6eb89f66-661c-4294-85b4-044519fdec1b	e9b3a60b-1ce7-4899-8831-11f827406d5e	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5226cd5d-a2bb-47b8-bdad-6ffc3614a5c9	6eb89f66-661c-4294-85b4-044519fdec1b	de10a61a-584a-4b95-91f1-bdf96a5eaeb3	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cc586850-7307-446f-a90e-e40a2288635d	6eb89f66-661c-4294-85b4-044519fdec1b	356bdd13-82cc-469a-8fd6-24e597857090	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b1d89a84-28a1-486e-8d49-b82d8e9f3e56	6eb89f66-661c-4294-85b4-044519fdec1b	fac18465-28ba-445b-8706-1a10898fd2ad	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7d0b2867-4293-4a23-9fbc-1ee5a3bc91f4	6eb89f66-661c-4294-85b4-044519fdec1b	83e3428a-9624-4e01-9da7-ce22aa31ef65	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
31f74ca1-9a0f-4772-b14b-c9539ed094e0	6eb89f66-661c-4294-85b4-044519fdec1b	58e26d7a-ffac-41b9-a737-cfb6ec994ead	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
178515d7-223d-4423-9e0a-3fea428f50e8	6eb89f66-661c-4294-85b4-044519fdec1b	531b944e-619e-42a0-b734-5a30d57fa47c	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f8a490c0-b33f-44d2-95b1-95b8fedb65a7	6eb89f66-661c-4294-85b4-044519fdec1b	8fcc6740-2404-4b3c-b7be-45c0be463f55	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
81f32cc7-fc53-49b0-b6bc-21b5b86445d4	6eb89f66-661c-4294-85b4-044519fdec1b	992b02e7-c182-4538-a8d0-0fb2137c76dc	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
70621206-98f9-4a0a-9ba1-b5f93dca81f8	6eb89f66-661c-4294-85b4-044519fdec1b	97ec196e-cceb-46ec-ac63-c62595539b16	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
12bfa223-a123-4506-baef-2a7043cfa6e7	6eb89f66-661c-4294-85b4-044519fdec1b	178d2213-60e3-4cd7-85bb-8e22b99b6092	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
309d71b9-e6f3-4f5d-8063-32dba03f8e24	6eb89f66-661c-4294-85b4-044519fdec1b	5578ce19-d473-4631-bceb-3529208a9c1c	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1d66aba7-e8e0-439c-9dc6-f818aab4b112	6eb89f66-661c-4294-85b4-044519fdec1b	fe289baf-6a53-4818-81a1-782090b7847d	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4523193a-b663-4e66-85ff-5a5777db6c8a	6eb89f66-661c-4294-85b4-044519fdec1b	26ef163d-a3af-4fa2-a80a-edd775cbb216	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3256de7b-63d2-4652-8b71-dfcfe9c1c612	6eb89f66-661c-4294-85b4-044519fdec1b	14522968-2fd2-49dd-85ed-98d7a3a54be5	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7fc37a74-0475-4608-8e4d-8d9fcf2847ad	6eb89f66-661c-4294-85b4-044519fdec1b	addec80d-d00b-43b0-9b5e-356b6f03e0ba	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5fe8e380-4084-4503-a752-27b11fd8237b	6eb89f66-661c-4294-85b4-044519fdec1b	d20538d2-915a-442e-be5f-70cdb8aa98d2	20406bbb-4d2d-44eb-82c9-97d049082d98	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cd2957c1-fd2c-4e61-a643-af8dc31003fa	6eb89f66-661c-4294-85b4-044519fdec1b	6164e6ee-b364-4c7c-aa62-091897b67081	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2c722cbf-6e64-44b7-a18b-df30cb5938c4	6eb89f66-661c-4294-85b4-044519fdec1b	8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7e568eea-b9e3-47b2-b408-9a57982a25ac	6eb89f66-661c-4294-85b4-044519fdec1b	afbc58c3-c001-42cb-a2b9-01204baa60f6	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bb54af3a-c136-44fa-89fc-a218171085d0	6eb89f66-661c-4294-85b4-044519fdec1b	a0328182-d2b7-43e4-809e-8eb9e174005b	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0879404d-88dd-4a64-b6a5-cf70c8319187	6eb89f66-661c-4294-85b4-044519fdec1b	a75a9442-6377-4684-8683-893cc195c342	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6aca8275-7f84-4355-971e-476e8dc9cc70	6eb89f66-661c-4294-85b4-044519fdec1b	f403036f-e8fd-453f-98c3-d7696e67a106	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
de27fd73-ca19-4529-9a03-430b498fbd41	6eb89f66-661c-4294-85b4-044519fdec1b	cf7e849a-85ae-4b70-b1d4-9f03c4c0c897	185d5e4a-83a1-422d-8f56-4c90dd7e4705	9b1e87d1-4988-416f-9aec-5acd7b67d194	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e3934846-288a-488e-b782-5c417e0e8567	6eb89f66-661c-4294-85b4-044519fdec1b	5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8f2a564f-a248-4ba2-bc18-c5c24feb7944	6eb89f66-661c-4294-85b4-044519fdec1b	cf63f961-d290-435c-a2ff-26a52c42668a	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a7e04327-daea-459d-b69a-c6622038a0bc	6eb89f66-661c-4294-85b4-044519fdec1b	543762be-87ca-4453-bc0e-d796cdb49468	011b96d9-146c-47ba-ae1b-fd693e5ef559	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
831993d2-5c7a-4920-99a3-1175918e9246	6eb89f66-661c-4294-85b4-044519fdec1b	0e4d1341-be89-4026-9fc7-27ade0581b0f	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
72b6e618-77ab-4faf-8c1c-a1979b65f49e	6eb89f66-661c-4294-85b4-044519fdec1b	df6d9e7c-c3a1-4eb4-a96b-5cc1bbf63b28	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	82022199-653b-48e6-9f45-1d7e74d9d740	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
53a46c60-874d-4fd9-82ef-58c40640d38b	6eb89f66-661c-4294-85b4-044519fdec1b	b85124df-46c7-40cc-adb7-805d3eaf31b5	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
28b69bdf-3d25-4a4a-81ad-966abfc76088	6eb89f66-661c-4294-85b4-044519fdec1b	b85124df-46c7-40cc-adb7-805d3eaf31b5	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fc520fb1-48fe-4047-bfdf-cd2f5ed396a8	6eb89f66-661c-4294-85b4-044519fdec1b	3f613c84-1af5-440d-a4b7-360d4a16bd63	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bb09bec4-3015-4594-951b-fc343b3fc648	6eb89f66-661c-4294-85b4-044519fdec1b	44926a74-6f9a-463f-b299-9eda88ebaaa7	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4d784e4d-6525-470f-b5e1-fcd360138c9b	6eb89f66-661c-4294-85b4-044519fdec1b	44926a74-6f9a-463f-b299-9eda88ebaaa7	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
597c9bcd-4c93-4608-a23e-275072e64dd8	6eb89f66-661c-4294-85b4-044519fdec1b	b3a99f7d-c02c-4e12-a912-d321c59ae865	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dcfdd4d3-638f-42b6-9a8d-cb79415603dc	6eb89f66-661c-4294-85b4-044519fdec1b	1d691b66-954e-4867-9d81-8eea2b6eb667	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
47d6f96e-dfdd-43ae-b12c-2165173d972d	6eb89f66-661c-4294-85b4-044519fdec1b	0fdb6422-757a-459d-ad43-23543ffe4bfb	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a0785535-1107-4baa-b1c5-6792611cf062	6eb89f66-661c-4294-85b4-044519fdec1b	878c91b8-4212-4329-bc67-60d136abb4f1	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00b1eebe-ea22-474f-8b66-3207dca1969b	6eb89f66-661c-4294-85b4-044519fdec1b	0dac449c-636e-44d5-ab72-eeac8052f70a	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
54dd0962-c6bc-41c5-ac07-7d889d51c323	6eb89f66-661c-4294-85b4-044519fdec1b	135b1582-0468-4070-9c91-fda08116d3cb	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
30367fe7-7e1e-4bc3-a477-d5e479a32f56	6eb89f66-661c-4294-85b4-044519fdec1b	8f2bbc56-0ba0-4d25-85a1-b1941234b95f	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1a8d9b60-3162-469b-93ad-a71f37da99e6	6eb89f66-661c-4294-85b4-044519fdec1b	b465a967-aaa5-47bf-9239-9b496b63d66a	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ce0cd266-0565-4d80-ad13-e1c85ef10edb	6eb89f66-661c-4294-85b4-044519fdec1b	52850cd6-d674-43fe-9c1a-a0a148a18ae8	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dc153a14-5848-4c50-9c1e-b7ae372f0c4b	6eb89f66-661c-4294-85b4-044519fdec1b	199d709f-8ea0-43f2-8b3f-eb4d389d1042	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5bf6965b-11da-4c03-8e12-1f1972fa31ef	6eb89f66-661c-4294-85b4-044519fdec1b	b444bc41-4bb0-4110-be04-0d286487041e	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb7a2fd0-4466-4ede-9d26-b5e71ad5c2c1	6eb89f66-661c-4294-85b4-044519fdec1b	f7ef8034-f74d-42d5-a631-e92d106f4dd0	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9fd88f10-0a24-4a96-b145-2d8d6280b4e8	6eb89f66-661c-4294-85b4-044519fdec1b	22e1c682-dbe2-4839-86dc-8d47125fa4b6	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c22c1068-4554-460c-8bf5-d9973db070a7	6eb89f66-661c-4294-85b4-044519fdec1b	9400f238-0457-4883-ad18-6a6b645277e8	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
106eb704-ed23-42fe-b8d6-ebe2471f1bb0	6eb89f66-661c-4294-85b4-044519fdec1b	194cd19e-fd2e-4e4c-8964-a24886ed04a8	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
571ac489-e6f4-4160-8cf1-e7515f466bba	6eb89f66-661c-4294-85b4-044519fdec1b	c32aa732-a66a-4828-8bcd-a63cb7bff676	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a3f4a9a0-7207-4aed-8597-54e793e10e8a	6eb89f66-661c-4294-85b4-044519fdec1b	c0ca83a0-7b7f-44fa-81b2-da82fac41eee	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ad0ebdd2-f11b-40cb-ac62-1a6655ee8916	6eb89f66-661c-4294-85b4-044519fdec1b	fa0609aa-5f55-490f-9bb8-26f66d8870d6	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
46bce6af-9e30-4371-985d-24d2f825bfa6	6eb89f66-661c-4294-85b4-044519fdec1b	c36d0d21-f428-41d8-9deb-6dda00bfc260	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
10fdcc2e-d090-4fa1-8d5b-e1f25afae269	6eb89f66-661c-4294-85b4-044519fdec1b	fdb20829-c90a-47f4-98c8-95b4682c0740	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9a770823-9e07-41ac-b84f-3a021f3bcec2	6eb89f66-661c-4294-85b4-044519fdec1b	ae6f5b04-c9d4-4e4b-8d39-17734093addd	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c531c591-1c00-4319-ba84-eb18d259a3c2	6eb89f66-661c-4294-85b4-044519fdec1b	97bd0f73-7ee2-48dd-abfa-09c7753dc12c	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e354761f-f73c-43a8-9b4e-a7d55895289a	6eb89f66-661c-4294-85b4-044519fdec1b	70c5863a-aef9-4592-970e-9aae14a18687	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4ada709a-be85-4da3-ba4b-ee8665377af8	6eb89f66-661c-4294-85b4-044519fdec1b	961b398d-db41-481b-9cc4-c7986a2722de	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
96227fe0-8037-4a59-a9a8-ca74925c4a61	6eb89f66-661c-4294-85b4-044519fdec1b	43f7d824-cf0d-42e1-b819-7d7479db89be	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
16b01420-170f-4970-a3a0-20f5840de0c6	6eb89f66-661c-4294-85b4-044519fdec1b	40633d5a-6b1a-4d89-b124-12150e904a1a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1b98d889-4447-47b0-bfd9-a2454eae4920	6eb89f66-661c-4294-85b4-044519fdec1b	43f7d824-cf0d-42e1-b819-7d7479db89be	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
aaceb4a3-f3ef-4a14-8f8e-155d55d2c3af	6eb89f66-661c-4294-85b4-044519fdec1b	40633d5a-6b1a-4d89-b124-12150e904a1a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
784dcf3f-b6f3-421c-bafd-a6179916b312	6eb89f66-661c-4294-85b4-044519fdec1b	0a180055-c1d9-4d42-b344-d7593601da8c	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2171d449-6af6-4c29-a4a4-0717ec15075c	6eb89f66-661c-4294-85b4-044519fdec1b	614c9539-b9ba-440d-a170-4b9f51e15d47	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e2a6df67-7eaa-49dc-815a-1e8e37249ca7	6eb89f66-661c-4294-85b4-044519fdec1b	0a180055-c1d9-4d42-b344-d7593601da8c	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
98a2480a-fd9b-4b00-b928-bc0dbc0c75b8	6eb89f66-661c-4294-85b4-044519fdec1b	614c9539-b9ba-440d-a170-4b9f51e15d47	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
37fd45c5-3e2c-4495-88c5-4ae6c334cae6	6eb89f66-661c-4294-85b4-044519fdec1b	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7faa21ec-bcfc-46de-8258-07415ddc28cc	6eb89f66-661c-4294-85b4-044519fdec1b	6a0dd8bc-58de-47a6-8965-b3789c26af78	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5ff9db34-43ff-4a9f-b86c-5bcf8d2675f3	6eb89f66-661c-4294-85b4-044519fdec1b	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ef3e8298-625e-4edc-9697-2ed454ce7433	6eb89f66-661c-4294-85b4-044519fdec1b	6a0dd8bc-58de-47a6-8965-b3789c26af78	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb28ad22-9ab8-4bb6-aedf-725ba76ce6b4	6eb89f66-661c-4294-85b4-044519fdec1b	4775bce7-7719-4bea-8c12-0d77f29b97e6	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
28bd5a8b-48ec-467e-bc09-f96a7320b204	6eb89f66-661c-4294-85b4-044519fdec1b	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
38d382c4-986a-4f1d-b445-2757f63b82f2	6eb89f66-661c-4294-85b4-044519fdec1b	4775bce7-7719-4bea-8c12-0d77f29b97e6	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
031aadcf-a5cd-4212-85d2-c692b73ca526	6eb89f66-661c-4294-85b4-044519fdec1b	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
53dd1dc4-5c3f-4f3d-8d92-3877dda2c208	6eb89f66-661c-4294-85b4-044519fdec1b	85afe928-267f-4407-8d28-ff3050657f6e	011b96d9-146c-47ba-ae1b-fd693e5ef559	2f81ac0b-1c12-48a1-8922-ddd4a8af597c	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6aafdc73-78f1-48e6-bc1b-a64aa5bf7931	6eb89f66-661c-4294-85b4-044519fdec1b	5df84a57-775a-484c-99e0-8e835002136b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
91004fef-9117-4387-9e1b-65cf391e0d84	6eb89f66-661c-4294-85b4-044519fdec1b	29f6fa6d-4615-4bfe-a397-c022ff9da6a0	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c032890e-2369-418f-91e4-8b6105b00c4a	6eb89f66-661c-4294-85b4-044519fdec1b	198c3575-5f88-4dae-ba7a-62228de49786	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fe2e9c53-5af0-47b5-8736-202f360e98dc	6eb89f66-661c-4294-85b4-044519fdec1b	93e71daf-8b70-43ab-b90f-1b6ddaae29de	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	f49af786-e4bf-44ad-be9f-82b6a20384c7	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1f28acc1-1aff-494b-8334-8f80b16018b8	6eb89f66-661c-4294-85b4-044519fdec1b	9b978bf0-4011-40ea-9652-2c9fa5206ba6	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7c3e110f-5bc4-42b6-a4ed-4594b9da8c97	6eb89f66-661c-4294-85b4-044519fdec1b	fc70e8e0-f228-41ec-bdf6-64670531a7a4	185d5e4a-83a1-422d-8f56-4c90dd7e4705	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
abf1dc74-79a3-4ee8-999d-51e7443799ae	6eb89f66-661c-4294-85b4-044519fdec1b	fc70e8e0-f228-41ec-bdf6-64670531a7a4	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d19832ec-c5d0-46f9-8aa7-cc78a30f57ae	6eb89f66-661c-4294-85b4-044519fdec1b	8351ca74-0e99-40de-b002-07c11aeb6310	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5e287575-f367-4095-8e99-91cb575f1e31	6eb89f66-661c-4294-85b4-044519fdec1b	cd4eb692-ef70-4a72-9714-3de375eefdaf	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0caa82ef-f927-4fe7-9aa5-5ec29cec33d2	6eb89f66-661c-4294-85b4-044519fdec1b	cd4eb692-ef70-4a72-9714-3de375eefdaf	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	f	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ee5c4c39-1442-42fc-9a41-48cb19979198	6eb89f66-661c-4294-85b4-044519fdec1b	1239093d-96ed-4ba5-a8fa-880415cd4f95	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
73caa98e-86bf-4d4b-930c-99c6fe6505c4	6eb89f66-661c-4294-85b4-044519fdec1b	ef1e9112-3119-4056-b090-3a33a5177dfa	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9c4785a6-2733-45be-953f-b528ed56c1d3	6eb89f66-661c-4294-85b4-044519fdec1b	1b550734-244c-4690-82d6-f0d208ace1e9	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
362cdc67-acdf-40e3-87b1-6b7f6fe8a8f1	6eb89f66-661c-4294-85b4-044519fdec1b	f0bf6b79-e92e-4c97-83bd-0e7ca50ebb21	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f27ee97f-3cb0-43c9-9e0e-7a8e9500031e	6eb89f66-661c-4294-85b4-044519fdec1b	1c09cd8c-42a6-46ea-9012-c2384e14888c	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e13552d-57da-428b-a979-08658c4ae6ce	6eb89f66-661c-4294-85b4-044519fdec1b	140b2eeb-8a4b-4ff0-a0c4-f49c4359da21	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00771105-c7c8-4057-8a74-bcaed4315072	6eb89f66-661c-4294-85b4-044519fdec1b	2206ea8c-f2a1-451e-9459-a2cf64a49834	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fefecef3-bc69-4ab7-9f85-5d51b7ba3de0	6eb89f66-661c-4294-85b4-044519fdec1b	29add6f6-967c-4751-8ae5-839feafaeacb	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2ad44a8b-b480-4a70-b99a-73d09f0ec033	6eb89f66-661c-4294-85b4-044519fdec1b	31cc85e8-1169-45c8-a8b9-53538b4f2dff	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d3469d1e-4761-4d26-b751-874db22cf67c	6eb89f66-661c-4294-85b4-044519fdec1b	7d48f0b6-c447-4df1-aeb8-65dda435d11f	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
85935881-2ec1-4209-a0c5-285cffbecad6	6eb89f66-661c-4294-85b4-044519fdec1b	2e3f87a1-4cf4-401f-b98d-2b308232adf8	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c806f019-fce4-45df-9008-e0301a1da231	6eb89f66-661c-4294-85b4-044519fdec1b	6fa74f7b-29ad-48de-b78b-d1222d6dd7d1	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	5c04995a-905a-440c-a586-e09761c4c114	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dcb0e919-6419-4a83-9d0b-3fc4a779f863	6eb89f66-661c-4294-85b4-044519fdec1b	7fe30758-442d-4866-9718-87f891523ece	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
495b1931-3ee9-4943-980d-2dafd1a14022	6eb89f66-661c-4294-85b4-044519fdec1b	6bdc30f9-3749-4b11-9eee-d57bdc90135a	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
81733f11-f14c-4d20-b35e-4abda0b3ba4d	6eb89f66-661c-4294-85b4-044519fdec1b	2d9ab94e-0d56-430f-a034-3b49db6da031	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
009c8d95-8b8c-4f80-9c1a-8b7cc19a118f	6eb89f66-661c-4294-85b4-044519fdec1b	bb8e4681-419d-45d0-a8ed-001457b83a8e	59dc05b5-869f-4bd1-b43d-13d437f10d14	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
91395ad5-4621-4955-b2ef-5521b3241323	6eb89f66-661c-4294-85b4-044519fdec1b	c0d7deb2-37cd-4269-b335-a34d3b38ecb2	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
26870c7e-5181-4adf-8677-e53e94e93883	6eb89f66-661c-4294-85b4-044519fdec1b	998ee5c0-cd53-4db4-befc-851c1b703f7b	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
249ea225-5f71-4e5d-b111-5993270967c4	6eb89f66-661c-4294-85b4-044519fdec1b	1555fa16-107b-4d37-b844-8467ad706a65	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3c3cfa04-7950-4077-8725-8a96ab9e1b65	6eb89f66-661c-4294-85b4-044519fdec1b	54c0db7b-d22a-49d6-b27d-a40d7722ca31	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2ac0b194-d083-4877-acae-af6916e890ce	6eb89f66-661c-4294-85b4-044519fdec1b	61553ec6-3eb4-43e0-85ac-b41756946a58	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
94f0f5eb-42c9-41be-8e46-d324c868e940	6eb89f66-661c-4294-85b4-044519fdec1b	5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	2961f8a0-f724-46e2-9f9f-2f064b7a5dcf	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7ad613a4-b6fe-43b9-af5a-9392a2fdfc54	6eb89f66-661c-4294-85b4-044519fdec1b	a156e08b-2e02-4e4b-9ea8-82e9921061c1	8c333a67-81f4-43e4-a1cd-5419eac29225	901bb2e3-d49e-4053-9ee6-371c887e44e8	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2493e3a8-1fcf-42c1-ab9c-d42ccf0c456a	6eb89f66-661c-4294-85b4-044519fdec1b	8acb9f4c-25ef-44d4-8ff2-21b28d883997	8c333a67-81f4-43e4-a1cd-5419eac29225	\N	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7d85c5ad-5b41-4081-8dec-bfbeb7610f66	6eb89f66-661c-4294-85b4-044519fdec1b	d1974a06-a43f-4fde-8bb9-771bf9617c92	8c333a67-81f4-43e4-a1cd-5419eac29225	f15e39b0-054e-46de-ae6a-ee92e5701bad	t	0	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5418 (class 0 OID 19433)
-- Dependencies: 287
-- Data for Name: menu_item_cuisine_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_cuisine_mapping (menu_item_cuisine_mapping_id, menu_item_id, cuisine_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
01598750-dad8-4925-9d3c-6c8eaedcc551	d1974a06-a43f-4fde-8bb9-771bf9617c92	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5ab48144-da62-4ba9-8bf1-0e0e94dca916	8acb9f4c-25ef-44d4-8ff2-21b28d883997	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c1161d99-0690-4447-8817-8f6830e7032c	a156e08b-2e02-4e4b-9ea8-82e9921061c1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
40fefb1c-97d8-4807-b732-11cb6a5a4e01	5f3f7a85-bf51-4c8d-87b3-b93c6aee281c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c0438524-f727-4bee-b78a-08926f2d8945	61553ec6-3eb4-43e0-85ac-b41756946a58	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
377691b2-e78f-4e96-9d7f-b4ade651dfc6	54c0db7b-d22a-49d6-b27d-a40d7722ca31	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
643e25c2-3ed7-4a70-9481-75fb2306dda5	1555fa16-107b-4d37-b844-8467ad706a65	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
13c892ed-c616-4488-a3ee-c8b69d2dc8d5	998ee5c0-cd53-4db4-befc-851c1b703f7b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6963c996-c626-45e3-baf1-08993d3a69b0	c0d7deb2-37cd-4269-b335-a34d3b38ecb2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
caa22f23-0bd0-43ab-b259-9d10f7a9f302	bb8e4681-419d-45d0-a8ed-001457b83a8e	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
165ed7f1-fb40-4434-a672-e7b31451a3b9	2d9ab94e-0d56-430f-a034-3b49db6da031	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
979fb20d-b867-421c-b1a2-4ffe8379b622	29add6f6-967c-4751-8ae5-839feafaeacb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b86011ba-480a-4cdf-bb42-70078b3e8a4b	2206ea8c-f2a1-451e-9459-a2cf64a49834	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e092594a-2937-477a-91ef-90405e5fa289	140b2eeb-8a4b-4ff0-a0c4-f49c4359da21	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
db304759-9a1f-41fe-ab9b-55fba231223a	1b550734-244c-4690-82d6-f0d208ace1e9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b793e0dd-095f-453b-a934-3052c63e09ae	ef1e9112-3119-4056-b090-3a33a5177dfa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
15105821-032c-4069-a1b8-cd4f89135189	1239093d-96ed-4ba5-a8fa-880415cd4f95	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b57b545a-bba1-459d-ab42-ae29cdaa08c6	cd4eb692-ef70-4a72-9714-3de375eefdaf	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
be813c1e-a606-4258-b020-d02e176551ff	8351ca74-0e99-40de-b002-07c11aeb6310	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9dc072ab-7524-4df8-850a-854b0a10d1cf	fc70e8e0-f228-41ec-bdf6-64670531a7a4	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0c049268-e955-4a09-9d0d-54fdb57edc26	29f6fa6d-4615-4bfe-a397-c022ff9da6a0	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7a3ee281-86b9-48ad-af26-e07066eb17ee	0a180055-c1d9-4d42-b344-d7593601da8c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
74e6dc49-97e8-41a4-b636-cc03a3b422ca	614c9539-b9ba-440d-a170-4b9f51e15d47	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6a862138-609a-42bd-be3b-0b27f723c774	0a180055-c1d9-4d42-b344-d7593601da8c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c4a4e2c7-78ea-4ba3-86c2-78f4da00c09a	614c9539-b9ba-440d-a170-4b9f51e15d47	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6b3470c3-c820-4645-af78-2beace151a38	43f7d824-cf0d-42e1-b819-7d7479db89be	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e5755b77-9abf-4f05-81aa-bd5fe2665f7a	40633d5a-6b1a-4d89-b124-12150e904a1a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
820b59b8-73a0-43ce-8d92-6ad0e96129a7	43f7d824-cf0d-42e1-b819-7d7479db89be	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d28fde12-59d7-4121-a23d-18e8cd34a424	40633d5a-6b1a-4d89-b124-12150e904a1a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7a9bdc95-6e5c-43f1-8dad-9fc20208cc20	961b398d-db41-481b-9cc4-c7986a2722de	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d6a482f2-e382-4ac5-a6b8-c332061cc687	70c5863a-aef9-4592-970e-9aae14a18687	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5c2864ec-d929-4ce2-819a-e1f7b5a0012b	97bd0f73-7ee2-48dd-abfa-09c7753dc12c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e58fe6c5-35eb-4660-88bc-02b604904710	ae6f5b04-c9d4-4e4b-8d39-17734093addd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0c0487b5-3a5c-4428-aee4-8ae589638729	fdb20829-c90a-47f4-98c8-95b4682c0740	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5153f1fc-a917-415a-93c0-94f4788ac96f	c36d0d21-f428-41d8-9deb-6dda00bfc260	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c5abc484-1238-4a38-9a3c-dc3868e4dce4	fa0609aa-5f55-490f-9bb8-26f66d8870d6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d0017e1f-401a-4085-8759-3fc3164c61db	c0ca83a0-7b7f-44fa-81b2-da82fac41eee	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
051a8da5-2a4f-4450-abe8-5a2befb74e0d	c32aa732-a66a-4828-8bcd-a63cb7bff676	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f8e9a743-59f3-4dda-befa-ffb8c3570c6e	194cd19e-fd2e-4e4c-8964-a24886ed04a8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e8bbd413-5c1d-43b2-b28b-4fb5058f56cb	9400f238-0457-4883-ad18-6a6b645277e8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8f133192-ab2c-4f34-95e2-62dfc144350d	22e1c682-dbe2-4839-86dc-8d47125fa4b6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7ea56928-4e78-4ceb-abcc-543b4e7d3adc	f7ef8034-f74d-42d5-a631-e92d106f4dd0	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
27bdf9b8-9882-42a7-903d-74ecf19e7df9	b444bc41-4bb0-4110-be04-0d286487041e	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e8d5bd2c-8efe-4fdf-b943-bf1cc11cf9e2	199d709f-8ea0-43f2-8b3f-eb4d389d1042	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8a524945-b8f9-4d01-b580-0c49417ecbd1	52850cd6-d674-43fe-9c1a-a0a148a18ae8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0803d0f8-0004-4469-aa4b-2eebba594d23	b465a967-aaa5-47bf-9239-9b496b63d66a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9881a67c-b6d9-4fa1-a6ff-c9623136a64d	8f2bbc56-0ba0-4d25-85a1-b1941234b95f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
97b81cf7-643b-4fa5-9193-26c391d744f2	135b1582-0468-4070-9c91-fda08116d3cb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
83dfd974-eb0e-4bc7-b617-927fa649feca	0dac449c-636e-44d5-ab72-eeac8052f70a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
47e02781-310a-4056-8328-e388757e278c	878c91b8-4212-4329-bc67-60d136abb4f1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00f67c02-32d9-4295-9b77-7b96d388c398	0fdb6422-757a-459d-ad43-23543ffe4bfb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7bcbeede-377a-4f18-84f7-662166a008d6	b3a99f7d-c02c-4e12-a912-d321c59ae865	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c690692b-2f64-46c9-b557-47eaaeeb29d2	44926a74-6f9a-463f-b299-9eda88ebaaa7	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f5c2ce9c-58da-4a36-9d62-6d35d06b0682	3f613c84-1af5-440d-a4b7-360d4a16bd63	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e23478fb-8333-4e35-9ef2-a545fcd3cf29	b85124df-46c7-40cc-adb7-805d3eaf31b5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5ca9fe2c-d2c6-4a90-97c3-43ec8222f940	cf63f961-d290-435c-a2ff-26a52c42668a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
234929cf-16d3-4762-9cb8-9dcb7cd7a577	5be4e196-88ea-4c5a-a9f9-f43fdedf1a31	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a2589bc0-8ff0-4028-bc66-de074887d44b	cf7e849a-85ae-4b70-b1d4-9f03c4c0c897	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1a1e3f3b-7919-4a6b-8a01-9830ba332448	f403036f-e8fd-453f-98c3-d7696e67a106	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ce6e36cd-a1e0-4d0d-82ad-8f50227bec86	a75a9442-6377-4684-8683-893cc195c342	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b14611bf-b3be-43a9-a739-f15d4e6ed8ea	a0328182-d2b7-43e4-809e-8eb9e174005b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f063d784-f373-48db-8344-68e26ef817da	afbc58c3-c001-42cb-a2b9-01204baa60f6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fc67a997-4380-416b-a90b-913b651b4d31	6164e6ee-b364-4c7c-aa62-091897b67081	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
59783d7c-a4e5-42d4-abfa-853dd4089e47	d20538d2-915a-442e-be5f-70cdb8aa98d2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
884741a9-38d0-47da-ad25-57ca965519d2	26ef163d-a3af-4fa2-a80a-edd775cbb216	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bf4c3b16-7f15-44eb-94fd-44f71ef0a168	e9b3a60b-1ce7-4899-8831-11f827406d5e	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0e6d50f3-9c31-493c-974f-f19c8c035db3	ee0d0a1f-a784-4df7-9212-aa576b3ad098	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c53eb104-f542-46b7-ade0-b703be596fa4	8435ee66-9b87-47b6-9af4-0700ce6186fd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a6f9b4ba-7c5a-460e-8351-5019eaf737ed	7ce551ca-251a-4082-b60c-f615b8f08c77	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8a183bd1-2c7a-48a9-8e15-241081f2b5fb	3987c83b-d17b-47d0-86c9-2ca24d25f4ee	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a3c8483f-349b-45dd-a7ee-f2c0670f31da	4d6a444e-3a91-4914-a852-50c6748c5862	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3edf08da-dfdf-4689-b447-b596a75c7c5f	29768ea2-2372-4fac-afa4-8025fe024c78	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9ec3a49c-f738-41aa-b578-017203c2c49c	f3245aa9-e6a6-408a-b9ac-a82c54845984	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
888bf3f0-be04-4ac9-9273-d4af5b1b69d4	d78ace28-ecba-444b-b9de-cee545cef5fa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7f9c6506-972f-4432-aaf9-a695c99f5af0	8449c926-5c66-43b3-9321-40108f2884a1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
862ad65d-48e0-4ee1-98f4-2cecd548615b	dbc10961-9d8a-46f5-8635-d611caac9351	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ee230821-cb9f-473d-aca4-c8e7c49a1c17	4502d2e6-f45f-4f50-b1cd-1f905e9cc518	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e4f7a6b2-8af5-4bc1-b176-1cd6c738fd3f	5553c740-38e4-43f3-898a-5d59b5a0320b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cd0ee583-e3d0-4720-b7c6-6bfa153d270c	d8193183-10c9-42c9-bcc1-fc012e110627	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e3018eaa-c8e6-421b-aeff-c4b478974604	444af49d-152e-4a78-8cf4-7b8a69d039c6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d3e88d4e-2d1b-47dd-a2d8-944bf185723a	21f5887f-0d44-4145-9ea3-7bd6bbcd64e9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
40c34da2-265c-409f-98c4-11d3dc910a8d	445e368f-5795-4ecb-a085-0a1f7cba64d7	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
df2377d9-bd8d-44ef-9167-2fd740b5cc27	d880bd2d-f77b-4456-91fd-79e2f207f255	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7ec29f3a-ca78-44d4-a763-609356ab6557	74727645-5f46-49e5-9644-3b3d73950cf4	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d27041fc-759d-4779-92d8-15c2c5471529	733d05f9-efba-4218-b6aa-d0cd89bac606	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2536e654-66d0-4e13-973e-6740f290fda8	ea5d0570-7042-4fa6-a6b3-c24833d2581f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6a759426-461a-4ef7-9d98-fd6f609c1c54	62643175-94cf-441a-8b44-dd4855b9d689	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6cbb5c19-cddc-4f48-afc4-c19ee1275fbd	d0ce2e68-aff0-480b-b966-ee2de6d73e98	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b50d2654-cbf7-48e4-bda3-c5efa0488af8	c3142cd7-e447-4ac7-a995-e49aa1c1c5fa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fed99dea-b608-4cd6-8c3b-89b4b0103ad4	8a60ac28-8785-495b-b891-7cb5e051043e	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e62e5d31-880c-44ed-9fc7-a4284cfbe339	3aed2bdb-cc98-41f1-b690-f4665163a2eb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
baf569a2-c15d-4bfd-8d60-e0bb49bfbc9e	f4b8d658-d725-45fc-93b0-038fda5d7b3d	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e9306a9b-3e84-4e3e-b5b7-93633709cf73	53bbe15d-011a-453c-8c75-da4e0201bca0	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3b5e6227-9e3c-4fb3-852e-b30d4c9e9416	2cbd132b-f48c-4282-b637-eae87931d57c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5fd7a077-c525-4dcd-9104-2358675533b6	db5f2886-4e5f-46e9-86ee-9eec449e4845	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2c264bfb-d43a-4fce-9714-bd109569315c	c5618b42-8182-4dca-868d-edf91bbd5249	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6960149b-8cba-440b-a105-5d41783fec36	f163594e-9c10-4c15-8184-183411d6dcfa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7df395c7-de11-43f3-bff7-372fa8609b1b	8dde0f7e-7023-4469-9240-e9e428b1640c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6a340570-d541-489b-b01c-cbc3aa9ead13	aa5f3b2d-ae8a-40d2-81f0-68878ae09721	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
736f633f-b2de-4622-9497-551167f596e4	89397364-5cd1-44ea-8ea7-68a8c0cc5fe6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dc0a718c-169e-4986-8713-2e5e90245f1e	d3a30467-6180-45d0-8f97-0516a39191e4	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
45884c90-ffe1-4c87-b8da-feeb514e710f	a9fc938e-3eda-4477-9261-e13687c777fd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c211f035-67d0-4a34-b942-417be21c1b54	0b90507a-d4ea-4f8f-908a-eca651ed29d6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
26296b19-024a-4020-86bc-95779154b363	34aeac9b-bdda-4d8f-bbc6-41a089862e6a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9e84eec9-7465-4348-80c6-f30bef18b0f9	da969ef4-1721-4442-a71d-3db403d42fe9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
300c1be1-a056-4bf9-9680-2b59527103ac	892c73ce-28dd-4546-a0fc-cebb44769bd9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f82af7da-8bca-4a7f-bf40-f97be1c9e611	ab6a60e1-0283-48dc-b606-544963dde3b5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
628222f3-5c26-4d3e-8bdb-16d9c319f02a	b3520f26-f8cf-4933-aff2-1e8303f483d9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fdcbab84-e82a-4088-8e4c-0fe8622e768b	d5d5b1b0-97b5-42e8-ad5c-467225669d07	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b1d61ea9-19e0-4258-a7bb-eb3fc49e361b	e81df99b-a120-4110-8f48-0c5cbdbec19b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d0c882e9-7660-44dd-8d49-81fa02f52c21	4c4e7447-ad61-4ccd-b1d7-8ebd15a87d15	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
928b48d1-c3d4-43a1-a101-6bd474d5f4ea	89aee119-46f9-4a9b-afd7-6551885362ac	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5e155dba-db3f-4e23-987a-a65288427a2b	64faab0b-643b-4a14-8c5d-c5718dd127b0	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cc544247-1550-48c9-9e64-d1c9813ab1cd	bcb56064-a124-44a7-8649-79970c8b6758	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a494af72-a77d-4be3-a5df-db60c7a9ccd6	fa97e202-e534-4210-ac26-29a34f1f38fc	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
af2c0dd5-5609-4635-97cd-28f7747b38db	94063735-6495-4abf-91e3-e0eb80aa13b7	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0939c09a-8b35-48e1-93f3-9dd5084ec1e9	b5394775-5207-4242-84c5-6917d840bc4c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a2a7f1b7-fddc-4a35-828d-48748cda08db	461c5d9f-5e6e-4d0d-be8c-e2f8b0cafa24	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
84e2a920-cf51-465b-adde-c5fe02c1f414	3e7e8bc4-53f2-4c03-81e0-a117f8d3406b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9d0ecef5-996c-4310-9915-553a1ba1d443	c609e1c5-2949-4d3c-bfc3-b61c164c9192	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4ab93ddc-26bc-4cbd-bd89-0a62281eb26b	a7bbba94-e82b-4749-8101-c65fd8ff3449	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
19695336-181c-45b6-9b84-bd5ecab720e8	521f5bc9-1c57-4f3e-a9bb-c0a76abd65d8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e60c427-81b7-43a5-9827-7e5441acec90	6acecc37-452e-41cf-bbfa-fa29139985c1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c2e96345-1a2d-42c5-9806-5703dcc841c2	0c646133-3a61-494d-8779-db533c0980d5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c5fcb052-0c92-4d7c-a1d9-fda0ca5f5974	78ac9d50-be7c-4701-af65-e8e4ea0e2276	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
996c0df4-49e2-4373-a558-551e6ea9cd1e	5567dd12-02bc-47df-b4e6-88b58026bfa2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8f132829-d638-48fe-b7a4-ae071fe4c2fe	63b03555-2ec3-4271-a8d5-43f8e1a92a6d	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2e455cbd-751c-417c-89b2-2bb593e7b46d	da7f5c17-06eb-45e3-b48c-90ab6ae078f1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a991e4ac-0ee1-4037-ac15-373740ea7d9b	c69dd883-7035-4781-92d5-e12b0b0bf97f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a5fe9436-255d-4e90-9a14-4f98ac5736d6	5646f259-9143-4afe-823e-a993ad4c16ae	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
860493a8-e029-4ba9-8278-5c7b31555978	846c440c-57b3-4d15-98e8-9d3ea4d01392	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e9eb903d-c454-4364-a60a-dc4570c6114d	a8be8a0c-8c06-4577-8f2c-2fb60c28bd30	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
26f75f14-4c62-4b8b-bdba-7a98a5cbde15	c824e963-ab76-4ae7-af4b-8976832f6fec	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8ab4723c-b223-4091-bd45-ed0a4cff9e99	2aa2f082-a408-4c05-b518-dd2ce8ad640b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00be8a01-4e5a-4403-bbc6-5136aeb53aeb	b7aefd26-9f98-454d-a476-ae7c9ce54387	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6faf820f-3c8a-4b5f-9b07-84b9a1434f64	e440b879-0e0f-4692-8c4b-4b10c6d0cf01	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2fb8fdd1-43f6-4d64-bf2a-83b34b750b4d	7249055c-e681-4d1f-ae2f-28c471a3af05	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4cdb6fbd-cc24-4c4f-a216-870ef9997ed8	b4a855a2-bfa8-41ee-9173-998bee08316f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
843bb84e-d6b4-42a0-b3d3-47daa3a4342c	2f9da69e-71b4-4b2c-919e-1500bc55a630	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6e3b9c33-1438-4ddc-bf0a-0b9ae8fc33cc	495c9a9e-6d98-440d-850d-3791071e4e95	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
75570a27-5cec-4c14-949f-33652631c5f6	72602fd8-2dd5-4d51-8280-4408e4a138a5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
11402aa6-d3b8-42f7-b1b1-36c2f05e9b1e	74f3ed80-98af-440a-a347-3f32e4be27aa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
78529e98-34b0-4b92-920e-f61b64143cc7	af6a1c14-e2af-435a-9a9d-bac3d66c35b7	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ce4405e3-894f-4525-be19-89f61bec7b10	c9f1e63f-86d5-4721-8c79-f8f8bf09a7a6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d49e6dc4-7dd9-41f1-a25e-b00e47f08116	3a3e183d-acd5-4e33-88e4-243fb0d99faf	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
09b8c8fa-9c98-4821-9224-aef705e56cc4	a08f430c-116b-4eb3-841d-d8d09c2f743c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cc5aeaf4-38ab-4865-a359-387038596e34	9726018c-4bfc-472f-8033-bb15a844772d	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2306c6d8-df0d-430d-a8e0-bd0afb0a84d9	2147a1de-ca25-43c4-adb1-7219bda6216f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a40fa7f4-597b-433f-8201-9ab716a90697	ba8f6800-1286-42c7-b362-c24844b700ea	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fd327d9f-2e8f-4e7e-b36d-b7c8d3363f96	e434f5a9-2005-4d7d-aa4e-051a7c10fa17	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7e1a65ef-4afd-47ce-af31-c22a924a6fac	b73de201-00ce-40ec-947c-f1159a500794	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
34be0687-5331-4284-a4fb-243fd2be5528	42b8e3b1-90ca-416a-a471-1f851ad03abc	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cdb83e14-6a75-44f5-a740-a73e19eb9261	564de578-2d66-4c50-8163-ab02b5a10663	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
bcef8350-22fe-47c5-96f6-fe04d729093e	3dd5f85d-f466-479a-ad01-2f45c32fc196	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
33fd1dbb-e3f1-4544-b31f-a8e4a3579da5	27e673a4-366a-46f7-be9d-409e61e48a7b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e3f68fc0-4c35-405a-bc4e-5cb4d7299cbb	6b9f3fa5-d64a-4023-9f83-f0bf27bdb0e2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb2f605d-3ad0-4247-93cb-b84654989fee	31f83c6b-72a9-4c79-b1e9-6bdef5b894e8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
261fa8a8-9b43-4fb8-8da0-fc23e443e0c9	d571b7dc-eeb9-453d-bdfe-33c2ba653cdd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
24daa2ab-404f-449b-a76f-86706ed1f7d8	8f8f3c91-2d26-4ded-9225-395ae9042f11	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00bcab1d-8f2e-41a6-ae87-4d67463e9ceb	c7e79fd6-9cb0-4527-ba8a-09da1d2f918c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0ab0db0b-16d8-4a61-9735-3a94e5716859	0e0dbf1e-b47a-4db1-9c9b-4aa4500722eb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00378dfc-c4d6-4049-9b13-450d8bab5d8a	3abc05b6-c5ea-459f-b7b3-68a93ceb0ed3	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
782af924-7bd6-486a-bdf3-bd106d2b1424	9e20a739-67ac-4085-b5b0-1d3540deddde	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e661dfa-43d1-43ff-a388-b7795799b7d4	05893119-03f8-41ea-88c4-bd840e95c2ac	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
53d5a6ec-b992-49af-9a95-b187b094b304	907dad10-e38e-4af2-90fe-d41212bf51cd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fe4ba588-37be-4080-b9a6-22c06716cc4d	b73cb807-821d-4f6e-8c71-78b5c5310bed	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7ce71ae2-bd50-460d-ad23-9e6fd71d0a38	888933f7-ca51-41b1-90d9-45ceed3a99ca	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1905ae46-e2db-418b-aa42-165480b416a9	17639dfd-b136-44c4-9284-232bdc865000	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
00ee975a-d58f-42a5-9cde-3ecd1c387b47	f7112f63-6f6d-4a33-9362-d4ffafcf339b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5d1f4f2e-b890-4310-b6db-424ee61a7d1f	bf821156-45fe-4ab3-a13e-8d7aab0d3869	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9c23f89c-3bcc-4190-af7e-7ff82ae6a950	842e1d5a-feda-4096-ae06-5bf538545e31	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9bb293e4-421d-41b6-a88d-9eccd31752e2	2c88e468-33fb-4346-a92b-b514a7e3797b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b7b558c4-2941-4894-899e-c002b9640796	197d1458-b83a-455c-8db5-267a616501a7	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b5eceb70-6d18-49ad-911b-f66ad3f71093	10bef495-7255-4638-bdfb-7b8df9c37423	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
115dcee2-8e3e-41d5-a4d9-1ad344ac515d	936473d2-bdc9-4727-92d1-6e8762ad2b65	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b3b273fb-1a5b-48a0-ab33-05bf8abfe467	5073e567-0d72-4e94-b697-79e1cd408def	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a92c715c-e50f-4e43-9df9-888e56b36b7d	b15d206c-d5ef-4d69-b660-1f06272c10e4	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ac6c321e-f934-4242-908d-c13fb5ae294c	70afac5e-7487-494c-9737-9ba5323e9a7e	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2e1cd465-1ded-4431-84b9-37840ad8fa66	28c1d342-6d69-4c31-8afd-693ac1d32db5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f193db6c-2da9-4f09-8fc1-d9c3377339dd	a4e76dd4-4d79-44f4-96c6-fc4eb6391677	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9729bd4b-3948-422a-a46b-c67602710313	68d16bc7-866e-41e2-9f90-79086232128f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ef2ef144-b233-4a7b-b45e-0b559fcbdeee	ac156f84-4748-4ce8-a4f6-4bb26b4839a9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ecc76d19-4441-4383-9a8c-68cdc5ee47d8	dd5dbea6-ee71-47b6-b10e-cd736d5988aa	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e5bf95e8-48ff-41cf-a396-404a9165ab23	44d0cc09-3bd3-4408-a54b-fa2840a6d5f3	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b65a0890-514f-4b1d-b79b-ebbc48297783	83070134-6fdd-4816-b2a3-6c37e96e22fe	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7678808c-aade-4af1-9d9f-c2aa620fca4b	20dd1625-14f7-477f-8f1c-5c929edb9956	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a6a123cc-f77c-4828-8678-52ff243ac514	b76156d6-7d71-47c8-aa45-a951287ebd9b	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
171d938f-3405-44b5-84bc-bda9204e4e12	531f9c5f-5fce-4446-bfe8-ce270e4f629c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5752c9e7-6ffd-4b31-b2b9-5d7193cf6112	52f4509d-b071-4aa4-930e-e01e97e4302f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
158c629d-5b64-4b23-93a3-cab53d0ebb5b	409b244f-7dfb-4c7b-8686-a079379ded1c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
38d6193a-8eeb-47f3-b396-9cc5cc7347d0	17bb19b4-e16b-4a51-8531-b7da9cbff8f0	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2df63ef9-fbc8-4ec1-8ebb-b2689802c45e	baaaefc8-3ba7-414d-ace8-650ade2f98db	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6824f4ae-7203-4781-8dc6-1862e5c0be00	0b171841-6ee4-4fc5-8ac9-2b19d4a2c65d	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
75bebe9e-6e6d-4418-898e-dc5c14193951	cf42f76f-bfc1-410f-8cd2-f6b1a32f94e8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6f49d8f8-6188-412e-8ab5-a9f0bd81ed7b	458c8f44-4178-4ad1-82aa-e1fafd1df65c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b7229a5e-9662-46df-ae0e-2c26c0d19240	1c1054e1-1106-4a8b-8230-f9bbe7b2e4d8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9a9150b7-379c-4e8b-bade-1ff0e72e728a	18a6da15-b4b6-4225-b473-c5c0eeddd5ce	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
353fdea8-05df-4d9f-8203-0c17879adefd	957c1e64-7e5a-4c17-8f27-1a4944de6a3c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b5476581-0d71-4702-8656-d8b5d8aaf19d	feca6731-d1ec-48de-952a-aba8ad404db3	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7bf03597-8416-4edc-9685-0d07f3fbfe08	089157e1-3de5-4c32-9c69-6445d78edc1f	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4f0d8960-65a3-4967-9e4b-ec27eab556af	74e0df2b-4c04-4518-b484-d6425e13ea74	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
adbb2e73-9f4b-4ad8-9c97-3424e4b70e9a	199afe79-6431-46a4-a0a1-1add114881ef	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e42e485e-d119-4614-b663-2b1e00f26e91	29de49e9-c12d-4c5f-9de6-18aac4973fa5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
71caf14c-bce9-4bce-b63a-5e0f36188a83	43301ae3-93ac-4bb3-b023-dd39d37de9f6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
68459a13-b325-49e2-8886-96778fba8ea8	3b91dfb2-fd88-45f2-928f-0c9a02394b62	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
87be9c1a-fdd3-4efb-99e7-d71330a6ef76	82657f8f-f8ad-49ec-bc2b-bb8fa993f67d	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4ccf8258-7d13-4002-9514-ad63cf1fd8bf	a658600f-95be-4f25-aaa5-e0cc280ec8ba	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9883b68f-644d-405e-92bb-69616c8141ff	ce3bf15e-84fe-4ce7-a10e-1a26ec8acf05	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
03b79fd8-1af2-4e4e-b132-34f15df6f447	0a4d265a-8b56-408c-89b2-d9cdc54982f8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1eba133a-51ed-4875-a126-9fd5afb61d9d	b3584fe8-58b9-4eed-9daf-81af7c5c2597	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
56937e0f-bb9d-482c-8694-ea210e2b7a83	f5e1ea70-3e91-4df5-9c55-9669c9e62872	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
869bf34d-dcdc-4711-8ba9-3fd3dd6a64e1	14ef9cd7-4fe2-4b27-970e-773e959f05d8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b8cf8974-909f-4ad5-b41a-1fdd61039c10	4b0a1e8a-d96e-46ad-ba49-1b17a02cccbf	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a4fedc67-a395-4751-ba5f-d8baa03038e2	acff3dd5-e388-4060-b2f7-38fd24021c68	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
452f3892-0ff6-403c-ab1f-cfd5e48e5344	8fb74061-258a-429a-b2dd-2628cce88d86	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
08f00486-3e29-4fc1-bc59-c806ac25a048	a172152e-4a5c-439b-bb67-8c41414bb799	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b0bc174c-9d76-42b1-b143-d767ff76478b	1461d06d-72a8-46b5-8090-b0bad1c2646a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
41a0a731-d90a-477b-8349-70ad4b2e8802	1f3c418f-548c-4aeb-99c1-86f784f1c9e1	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8d2b0bbe-c0e1-4adf-901f-965d471dc72b	b3e70ef0-d8b4-42af-80c4-8ee78031befd	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2ee6acc6-0d96-4c6a-9267-293cb02745de	5f1b450b-391d-4208-b336-53e192baa578	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
65dd1707-99ea-4738-916a-bf084a496faa	28ef3fa2-c237-4c93-b411-82f0001e6492	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7377672c-eab0-4c30-849c-0f85b2f043cb	1c59b0d5-c8a0-40c6-87ad-b727b5276aa2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6cac1fe7-ee97-478f-85df-06f9b1c56353	ccfd7416-c0a3-4329-a4c1-a95603e27da6	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5c95acd5-fb29-4143-935f-eba77c30301c	2abf9654-d5e5-490e-b96f-0b7b2b426283	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c7812f21-c246-498e-93a7-9eeed01d181d	9c2ddc01-f7c7-4451-a595-d665830b062a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
542a2149-d049-453b-896d-750f703a731a	70ee9dbf-1477-42f9-9359-f1f40fb79ea2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
56c0c921-faee-4512-bbb3-76796e551fed	8b78ab34-c265-4577-9c86-21a4d09cdc52	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
58198196-db5a-4f92-8452-b3bb5d9a751d	c92904fa-2ba8-4e5d-9abc-73d3ce7a66bb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
baeaba16-ab4b-4184-a49a-ddf4b6d9ceb4	42917c7d-09af-4ae7-91a9-3b65b0c654a3	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
84ccb545-a37d-4cf5-9146-8200acf46cef	27afa12a-791f-495f-91be-dce580504f4c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ed458068-18d3-428a-8cc7-9a0702f1c91a	44cc830b-0ae9-4aa0-a2ed-57ac80e0b4fb	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3a619e05-7a49-44af-848e-8700aa37fbcf	be6fab0b-7648-4c86-914b-7ba63acf9bf2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
aa280f7a-c2e4-438c-a8b4-d74e849d0a2a	a66b87c2-03a2-47e8-a9da-37904dbe30b9	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d83a2671-b511-4076-bb3d-8f9b3b5b2c0b	57c06b53-155f-4b54-b420-a4605b0badc8	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
06f528f0-a595-4dc8-97d0-36ede9f67f01	eff3d4e3-726b-4170-9d2e-5894b0a70ad5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
755f981c-d314-4ab4-a822-e7e030e99a24	a2a30d42-28a9-4050-b157-0227e4a539c5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
193e5770-0157-4bc1-99e8-87e645ea8e0d	bdc6318f-5da2-4907-bab4-cf4838d80988	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a1067bb2-09db-4cb1-a727-4000aa1882d8	4d7a637f-1360-458e-95da-d4bb74c5c99c	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d7479ed8-c1f0-41a2-a61d-686d24c010bf	9d63daef-e702-4908-9df5-d54c07335256	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
99badfc5-39fe-41e4-b558-bc06cc92dbf8	3f32641e-2154-45f9-ba9b-4840865e04d5	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d3e4b7c2-5b66-41db-a299-eb167a250788	18d0f888-ae4a-4071-a6be-ab7e467c6472	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d3ee8589-3544-4c50-89db-dff325cc0030	a601a7f8-5d30-4347-bb02-94526f4f413a	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c51cf87a-474e-44b3-b245-3f31f06139c1	010c83a6-d7e3-4f48-880e-c85137fb39e2	55fbe002-1965-46d7-820a-c60e90731fbb	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb2ea8e1-9411-4802-9ca1-7c4892f39f92	6bdc30f9-3749-4b11-9eee-d57bdc90135a	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
cb09b75f-a08d-47bd-a8d8-25ebea346287	7fe30758-442d-4866-9718-87f891523ece	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fcaa49da-49ee-4a8d-be25-db590f8c2b2b	2e3f87a1-4cf4-401f-b98d-2b308232adf8	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
117d2044-c824-4cdd-b537-bcd0ebcf0e47	1c09cd8c-42a6-46ea-9012-c2384e14888c	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3c7892b8-54f4-405c-bbbf-798b2b8377af	93e71daf-8b70-43ab-b90f-1b6ddaae29de	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3bbc8fc7-1155-4d27-a465-766c504d8807	198c3575-5f88-4dae-ba7a-62228de49786	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2afb5061-ffd3-4a8e-80ef-454f76cf9a30	5df84a57-775a-484c-99e0-8e835002136b	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
df35fe9b-22c1-49b3-b035-fbc6cf1049ca	85afe928-267f-4407-8d28-ff3050657f6e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6eb49b43-9b6a-4259-8b9a-ac8c3870052b	2d593c56-cbda-4743-a2eb-7e1d3e6e20ab	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
36d56d74-c1de-48d3-9073-c49593a26bbb	de254fc5-4f3f-4f96-8c3d-99c2b9e50ba1	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b9a04f6d-51b5-4806-83b0-8c4b17cc3932	0d9ecc80-994a-4c15-a1a0-9b1794178170	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ad879eba-db54-4ff5-86cb-261bfd594c6b	4775bce7-7719-4bea-8c12-0d77f29b97e6	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6a1de91e-0950-4819-aea7-7c86a621d99d	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
eb9652be-aea4-4eb6-a3c6-fa21944e103f	4775bce7-7719-4bea-8c12-0d77f29b97e6	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
82585bc7-fb9d-4d4e-b1d0-fb7446320fe7	7a0a920e-b87e-4d6f-948d-cbae1152f4e6	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ae5551dd-9c26-4039-9d13-6b6a19dd90ad	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
26224af7-12c9-48f3-ba42-577c4ca5bb1a	6a0dd8bc-58de-47a6-8965-b3789c26af78	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
77047d17-7e66-4682-8913-0fbb3e853a10	2241f9b6-28a8-4f2f-8d71-a678485a9f9a	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2aec02fc-bd44-4356-9664-413db0be9e9a	6a0dd8bc-58de-47a6-8965-b3789c26af78	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
93debad1-d447-4efc-8408-89cf3f684d8f	df6d9e7c-c3a1-4eb4-a96b-5cc1bbf63b28	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f516961c-1d78-4602-861b-328d24719469	0e4d1341-be89-4026-9fc7-27ade0581b0f	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
221eb1e3-4dba-419e-8e65-e07d8e9c0946	543762be-87ca-4453-bc0e-d796cdb49468	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f4228e5c-11d7-4e7e-8701-d0ed7e3694fa	8c55aca4-de0d-422c-aa8b-3b11fb37e1ab	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
963ee049-780d-4f6c-8c5b-12f44726ca75	de10a61a-584a-4b95-91f1-bdf96a5eaeb3	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
524bf3ac-a240-4a93-8b06-eac3d341a472	88dc009b-c5b7-4978-800c-4a8202048808	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3ac36e7d-5a29-44dc-a1e2-b72c93151697	bee9a02e-7117-453f-aca2-8a99fb44d5c3	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
43bf9462-e2d1-4182-985b-4af861834110	c6c82907-0a2b-4424-8cff-e0d399e82e76	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b0d6318d-257c-4989-a2f9-ee8e13f74725	32dce3db-9b6c-41de-ac5b-db2f1f7cf1b3	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6f78dd60-b9ea-4690-bba9-8fcf04a97df9	b1f7769a-5711-4944-b359-43a02ce6b82c	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
dddaa6e0-e6f7-4d3a-8fd8-d38a7080e1b4	860edeb4-f127-4442-8362-7e0eb45d26ec	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
34540a0f-0482-41ce-b498-25fb17f3f211	32bf89c1-cc50-4e3b-a578-7342f0a98052	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
23e5bd08-ad8a-4ffa-9240-906d07d12ac7	1e0d6501-b15a-4c5b-8856-e0668473540e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
53cb8e98-00dd-47df-9770-92b0495a8d3c	b51b7764-5d21-47c2-aaa2-a54ef06e695b	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e2f800f4-cdae-45a6-ac41-b5e6392c90ed	80900d89-757f-45f1-8df1-574a5e4f38c7	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
02fa3673-138e-4390-ae34-1dce36fc256a	a1514e63-efa6-4ab5-8068-aa531ddcc480	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
fca12a1b-4bdf-4c8b-81aa-9c193ef38d85	fc885a0f-9531-475e-a49e-1aa26cecbb5e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
aaff3704-511c-4698-ad02-559cbaa29b75	3ea54e45-7aac-4cf2-b790-cf68417159f5	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e56af2d9-6768-49db-b47e-5e75c123ca88	200af72d-ada6-4ad9-a2a9-8ac90c9ee26d	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2b366426-f809-43d9-91c4-cafed915be4f	d318b34e-2e38-44fc-8583-a25e6633fe34	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
003551d6-01a4-4eb6-a890-06eb61f8876b	f41a672d-54ff-457a-88ea-4a8427177b75	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f685a572-40ae-49ca-abe0-1b8952f4a37b	4ff69e50-609f-4f1e-a804-2d631ecc1b44	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6ab63f95-2f9e-410a-8e43-754eb30a39ad	7ed15acb-1b78-444d-afb0-c9cabfd76b12	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8e34290b-b2f3-448a-b3cd-f01ee0bb4886	b460dc4d-a2a1-4ef3-bc68-172a30959cf4	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
10192aaf-68c5-440f-899c-c5df43edd60f	9f608fd0-bde7-48da-a77f-c78ff68bd777	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
efd2b0dc-3ebc-43b4-832b-ac2e986d0113	7c954edb-f3b0-45b1-a0de-1b20a086d060	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
01223a1a-0d54-4cdd-8b2b-ebdf0e4170b3	0aaa74f5-6f91-4b5d-9dd3-5b7ed925964e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f2620848-1b02-4a81-91f0-94fc2a8e5bdb	efb317af-7eac-4f9f-8f63-7883c2982ede	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4fdcba34-3ae3-418f-973d-726bf2c80a97	8f49b43c-be61-4c6f-95dc-4e8a7d10e7da	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5177ed58-a9fe-4f86-bc5b-669d15bd6388	e6608ce5-674e-4c3a-ba90-6772391d4949	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
39942fe8-3b3b-4d06-87b6-74712e414142	fe1cc623-5749-4759-bb79-c08f0e00d4b3	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
12bd6ac2-b3e5-4715-a587-5273dcb555c0	59e2aa6a-bb1c-4f29-86e6-d7980d954d46	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
33235e30-105d-448b-9ffd-b4c04615b27a	59985ea0-e5ff-4cf2-9858-7ba48ee722be	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7333a5b8-8193-4599-91d1-de242f0ad444	553ac569-2406-4dba-b5f2-dcd928b95787	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9ade809f-c13b-4418-ba23-c935b1640655	57ba4cb0-d12f-4e87-81b2-b384cf4e8cb7	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
989245af-6499-45a0-a91b-dec6b9c6b4d5	bf98b52e-f41b-4308-906b-3ab72d075a9a	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
81e67cfd-cc7a-443f-8a35-bfaac1e0145e	54ee838c-f191-4dab-a861-8bbf24ed8b70	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b8eb4e4c-e900-4be8-84d6-e398cd6d1a9f	4a652f79-d0fa-402b-b134-b53ee5b5076e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0bc82af7-e12d-48de-8a8d-b5308e56ecf1	9a29e77f-f13a-4128-bc24-2f122891a487	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
04434c70-f8a0-4c5c-9a92-33d26b2ebd47	052f6175-66a2-4b84-ad4b-047cccec298d	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
57bb7b7c-f30a-483c-b336-4326c511a076	bdbcddb6-5725-4e59-8a2c-7a3d463ed820	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
136d2db7-f2fe-432b-a257-baeba3455af0	0d5ffcb1-b741-42e0-aba8-a09b4f2c7cfc	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
94ae92ab-47d9-473c-83df-c2e16e242532	2075e9ed-f702-4fb6-84f1-16eb3917b5f1	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
14e158af-5789-426e-9ea3-56285edcc6df	1e81be0c-c4cf-4970-a53a-505eb92e87bd	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f2836a70-0177-4471-af9d-b0d6cf073189	8f2d8131-94a6-4331-841e-1031150bd63e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2f585bb6-b68e-4d10-90e8-453b48bb6b76	e31406b2-d66e-44ab-bff0-73fba95ad51e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0b23949a-4c22-45c9-8c69-816499cbf8e5	006c6e95-b04b-4bc1-9bc6-68202e92d1af	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1aceebc0-a456-4053-81e1-5db0dfe60ffe	b269c7ba-3584-49b4-b3c2-09c4a390688e	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6210462e-8991-4647-8541-a48777bb4d24	3953ae28-900d-42b9-92c3-6b97102aada0	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
889aac64-4d05-487f-a595-da777b667c99	b0d208c9-a2e9-40d1-a263-42962f53ca7a	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e1c5abc2-1233-4e88-932a-b95d83f55c9e	278a9ee5-f497-4297-a6cb-e8f8e9ca9faf	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
6f8d6a2a-e090-4c9a-99f2-3284d7bef82c	f4abc59c-b7de-4de0-9e12-bcbb3a7fa1f1	45472f72-7a6d-4b2a-8bfb-86f919acb727	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
13ccc7e4-597b-41cc-93fb-e278efa132ae	f0bf6b79-e92e-4c97-83bd-0e7ca50ebb21	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9d7ad8ae-d563-4f4f-b284-a67acb50867c	c30a6a90-4ce5-4917-9e62-4972d4e1ee19	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3d7b73f1-d1bf-4ca5-b862-31f64c107e16	12c9297b-83ec-4782-b024-46edad03e261	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c2651a20-0bc2-4dde-a47c-9e18fee18a80	299f9d53-9f76-4c85-a2bc-337d53055cd2	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
03d9f335-1dca-47c7-99a7-477386c2e12a	544e1530-13e3-4a9f-8186-1889b0004c40	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
945c3eba-022b-4779-8ab0-7c17b8df3470	60b5673e-9d4a-41b1-8383-05932a7395ae	4d4e1276-0726-4e4d-a0ef-8093dda415bd	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d2b91eb8-46f6-4e63-8b94-014f34ca18cd	6fa74f7b-29ad-48de-b78b-d1222d6dd7d1	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d5fab554-66a6-4e26-ad41-74bbfedb8d09	7d48f0b6-c447-4df1-aeb8-65dda435d11f	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
04adff0b-1068-4a3b-a14c-896663992cca	31cc85e8-1169-45c8-a8b9-53538b4f2dff	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
16a4c8ed-f2c5-4c38-babc-e8bcbe2e7be4	9b978bf0-4011-40ea-9652-2c9fa5206ba6	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
911a66ce-ed7b-42d4-84f5-79bd83bc429f	addec80d-d00b-43b0-9b5e-356b6f03e0ba	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f51de58d-5b27-490e-b232-31e30790299c	14522968-2fd2-49dd-85ed-98d7a3a54be5	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
016f60c9-6580-4b65-ae1b-5d22530672a0	fe289baf-6a53-4818-81a1-782090b7847d	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2d755657-1f07-4419-b294-a33e7d08d158	5578ce19-d473-4631-bceb-3529208a9c1c	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
64bb49e1-f461-4eac-a967-acc69e06facc	178d2213-60e3-4cd7-85bb-8e22b99b6092	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0bb8d32b-2def-4186-b017-d7085c13e37a	97ec196e-cceb-46ec-ac63-c62595539b16	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
17eefcea-ed61-4dc9-8400-b6af53b476f8	992b02e7-c182-4538-a8d0-0fb2137c76dc	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
e3f79b9e-b7e6-44e7-b44d-7a50ad1c5f62	8fcc6740-2404-4b3c-b7be-45c0be463f55	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4fadb3ef-4bd0-4ddf-a8f9-0414b244872b	531b944e-619e-42a0-b734-5a30d57fa47c	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ca8f80fe-66e8-4a0b-8060-1f74de6b35f0	58e26d7a-ffac-41b9-a737-cfb6ec994ead	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
3cf2e80c-7fa5-4684-a589-4e2c7b7438da	83e3428a-9624-4e01-9da7-ce22aa31ef65	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
da997f77-b99d-4401-b3ee-3eee74db303d	fac18465-28ba-445b-8706-1a10898fd2ad	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
81858f65-3e4c-4da6-af15-81169f5f592f	356bdd13-82cc-469a-8fd6-24e597857090	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2c2e65cc-2bbf-44c8-bab2-632ab4190ce1	1cffcfc9-cc80-4014-be79-9b20ddc76d9e	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
634a4f7a-0d22-4951-a36b-0cdfd549572d	41fd61ae-6fe9-42b0-9c0e-4818f153ffa0	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b943dcb0-9e4c-4fb5-a156-fe67ce281254	a0ebae73-9f25-48b3-8fd5-b05ba844d222	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d7153656-6e53-44b2-86a5-6cafce3573e7	30c26e10-38c4-4254-aa2e-0d42f352c023	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
34a733e2-46b9-445d-8f19-731ae273724e	1021ee4c-7743-4e51-a5a4-164a2ea3d842	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
164501bc-c9c1-4f9c-9963-cdb105b855ba	9ad814cd-f7ba-4d29-a113-805dbc651c60	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9306ed11-e982-4547-a365-272c476c5fa0	b128ec84-8ee0-470c-a38c-7ed96269ee68	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d5d22815-79d6-4419-af00-1cae682b3c90	96787c99-a0ce-4332-8f26-f2297f87dcd8	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
315bf7d3-c31e-4b0a-97c3-e4432027367c	f390a5a5-476c-4a52-89cc-bae5384a9ab1	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
def648db-fe69-47e2-af07-7316abe664dc	62c2253a-293e-4954-806a-f893f400e55d	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c04d9e54-d8da-494a-9fd0-eddcf8b9667c	18f5b5c1-e9df-4769-9ec2-38abffd9fa3c	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
8435fc84-f145-4510-b35d-c15f3b5f4e8a	5cbddda4-b4af-45d7-b913-de01a9a72cd5	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
491841f1-f64c-4af3-b45f-d97e1788da55	fd85f52e-0065-4fbc-bb94-1465b1d154ee	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
1a6083ef-6531-4102-bc0d-fac87274304f	62aad12b-d9fd-4fa1-8d80-3f93bd42d2b6	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
d8935ace-b0cd-442f-88a9-9d74e1ebaf17	987066f3-edd3-454f-9f5d-0cfb5e55c1e0	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a438f251-9dd0-4581-9751-21cdd1e19574	bad85a08-06e2-4bc7-b864-6b177112df70	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9582b8de-2da4-4eae-ba8f-2e72101b1ec1	1180b173-548f-4fa0-b566-64cdc0b1dfd5	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
409c8dab-9e02-46f4-ac9e-cb01d0750228	1e5a0a42-ea87-4bf8-8aa7-5e871ca49904	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0743c90d-f00b-4600-a70d-a45fba2d788f	c2ad9384-1f73-4f8f-8f62-7bae9e2aad59	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c998888b-30e7-4119-b847-bf8ed124dd3e	09aa6db4-7502-4dc4-b889-14fff6e4d482	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
9b7f4fbc-ff28-498a-8b87-3177a99f8c6e	4aab1431-eab8-4c5f-9202-92a916cd0966	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
94cf708a-791a-48c0-8c19-d178272cc00f	67148a4a-35f9-414e-b58c-c2ac18104782	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
84bdb0e5-4bb9-4a4f-9259-15007ef99fbb	87a9c9c7-5315-457e-918e-10aed9d46911	0c320b3b-4489-4b4a-ab86-07f4288ad0da	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
29451d87-6141-45c4-8e6b-587d433264da	1d691b66-954e-4867-9d81-8eea2b6eb667	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0f0965c4-5b3e-411d-ae08-165bfb2a7d43	df1246cc-bae0-4d4e-8674-fb6af39b15bb	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c4013145-7f2b-41a9-af57-6a9c9d87456f	37706f7f-3212-45bf-bbde-a9bd58d7d93b	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
b68551bb-c843-4354-8c44-a8aecba3e7d5	e5b62ff6-5d19-4041-bce2-51eff5619079	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
4c67c7cb-1a8e-4ba5-9ae3-1dbd371b5815	61592f67-7a2a-4060-8f95-6ff7aaf552a4	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
957d8084-378e-44ea-8489-2a37d1d3ea83	0009b8a7-676d-497b-92e5-1c9f19a6a9dc	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
7c327757-5e2a-480e-82bb-310a11a96b4d	dee24566-d8cf-46c2-8ea7-0ea7bcd982df	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
c5bd7818-83af-4c44-b59a-27fd004b55ba	478355a4-a104-478a-9161-38812c682f28	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
ba0c6deb-da3e-4c5b-94f7-282474198ddd	dbfda102-ce20-4cde-be8b-e8df65c9f7db	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
a350b1a8-5581-4785-abaa-60c7cafdb6a4	59570f9a-8658-4f5c-b326-6bd30b07d043	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5f6e2d33-2524-4679-a12d-ba78fa41cd17	dae5f7b5-abd0-4afd-ba03-739065d56b35	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
55d4f631-5967-413a-9bf8-80f0666c018d	559abe90-0de6-43d3-8dd2-932712b78a62	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
0f4c9d68-ce05-4071-a84e-083878535fb9	0080a492-5c32-4048-9f36-95788b5271ce	f3692e61-a88d-4c94-a9c0-ea5124812283	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5500 (class 0 OID 21625)
-- Dependencies: 369
-- Data for Name: menu_item_dietary_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_dietary_mapping (mapping_id, menu_item_id, dietary_type_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5419 (class 0 OID 19443)
-- Dependencies: 288
-- Data for Name: menu_item_discount_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_discount_mapping (menu_item_discount_mapping_id, menu_item_id, discount_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5498 (class 0 OID 21564)
-- Dependencies: 367
-- Data for Name: menu_item_ingredient; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_ingredient (ingredient_id, menu_item_id, restaurant_id, ingredient_name, ingredient_quantity, ingredient_unit, ingredient_rank, is_primary, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5420 (class 0 OID 19453)
-- Dependencies: 289
-- Data for Name: menu_item_option; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_option (menu_item_option_id, menu_item_id, menu_item_option_name, menu_item_option_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5421 (class 0 OID 19465)
-- Dependencies: 290
-- Data for Name: menu_item_ordertype_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_ordertype_mapping (menu_item_ordertype_mapping_id, menu_item_id, menu_item_ordertype_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5422 (class 0 OID 19475)
-- Dependencies: 291
-- Data for Name: menu_item_tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_tag (menu_item_tag_id, menu_item_tag_name, menu_item_tag_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5423 (class 0 OID 19485)
-- Dependencies: 292
-- Data for Name: menu_item_tag_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_tag_mapping (menu_item_tag_mapping_id, menu_item_id, menu_item_tag_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5424 (class 0 OID 19495)
-- Dependencies: 293
-- Data for Name: menu_item_tax_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_tax_mapping (menu_item_tax_mapping_id, menu_item_id, restaurant_id, tax_id, is_tax_inclusive, gst_liability, gst_type, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5425 (class 0 OID 19508)
-- Dependencies: 294
-- Data for Name: menu_item_variation; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_variation (menu_item_variation_id, menu_item_id, restaurant_id, variation_group_id, menu_item_variation_name, menu_item_variation_price, menu_item_variation_markup_price, menu_item_variation_status, menu_item_variation_rank, menu_item_variation_allow_addon, menu_item_variation_packaging_charges, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5426 (class 0 OID 19519)
-- Dependencies: 295
-- Data for Name: menu_item_variation_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_variation_mapping (menu_item_variation_mapping_id, menu_item_id, menu_item_variation_group_id, menu_item_variation_rank, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5427 (class 0 OID 19529)
-- Dependencies: 296
-- Data for Name: menu_sections; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_sections (menu_section_id, restaurant_id, menu_section_status, menu_section_name, menu_section_description, menu_section_image_url, menu_section_rank, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
f0aebec7-a377-4e22-ba52-cace2b15a8f8	6eb89f66-661c-4294-85b4-044519fdec1b	active	Vegetarian	Pure vegetarian dishes made with fresh ingredients	\N	1	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5428 (class 0 OID 19541)
-- Dependencies: 297
-- Data for Name: menu_sub_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_sub_categories (menu_sub_category_id, restaurant_id, category_id, sub_category_status, sub_category_rank, sub_category_name, sub_category_description, sub_category_timings, sub_category_image_url, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
9b1e87d1-4988-416f-9aec-5acd7b67d194	6eb89f66-661c-4294-85b4-044519fdec1b	185d5e4a-83a1-422d-8f56-4c90dd7e4705	active	1	Dosas	Dosas dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
82022199-653b-48e6-9f45-1d7e74d9d740	6eb89f66-661c-4294-85b4-044519fdec1b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	active	2	Breads	Breads dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
5c04995a-905a-440c-a586-e09761c4c114	6eb89f66-661c-4294-85b4-044519fdec1b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	active	3	Noodles & Fried Rice	Noodles & Fried Rice dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f49af786-e4bf-44ad-be9f-82b6a20384c7	6eb89f66-661c-4294-85b4-044519fdec1b	eeb10d40-ab25-4dd8-8e31-08ec8c5dc090	active	4	Curries	Curries dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
f15e39b0-054e-46de-ae6a-ee92e5701bad	6eb89f66-661c-4294-85b4-044519fdec1b	8c333a67-81f4-43e4-a1cd-5419eac29225	active	5	Juices	Juices dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
901bb2e3-d49e-4053-9ee6-371c887e44e8	6eb89f66-661c-4294-85b4-044519fdec1b	8c333a67-81f4-43e4-a1cd-5419eac29225	active	6	Hot Beverages	Hot Beverages dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
2f81ac0b-1c12-48a1-8922-ddd4a8af597c	6eb89f66-661c-4294-85b4-044519fdec1b	011b96d9-146c-47ba-ae1b-fd693e5ef559	active	7	Fried Rice	Fried Rice dishes	\N	\N	2025-11-26 17:56:01.70166+05:30	2025-11-26 17:56:01.70166+05:30	\N	\N	\N	f
\.


--
-- TOC entry 5429 (class 0 OID 19553)
-- Dependencies: 298
-- Data for Name: menu_sync_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_sync_log (menu_sync_log_id, restaurant_id, menu_sync_source, menu_sync_status, menu_sync_started_at, menu_sync_completed_at, menu_items_synced, menu_errors, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5430 (class 0 OID 19565)
-- Dependencies: 299
-- Data for Name: menu_version_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_version_history (menu_version_id, restaurant_id, menu_version_number, menu_version_changed_by, menu_version_change_summary, menu_version_snapshot_data, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5431 (class 0 OID 19577)
-- Dependencies: 300
-- Data for Name: order_audit; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_audit (order_audit_id, order_id, session_id, order_version, modified_by, modification_reason, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5432 (class 0 OID 19589)
-- Dependencies: 301
-- Data for Name: order_charges; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_charges (order_charges_id, order_id, order_item_id, order_charges_type, order_charges_base_amount, order_charges_taxable_amount, order_charges_metadata_json, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5433 (class 0 OID 19601)
-- Dependencies: 302
-- Data for Name: order_customer_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_customer_details (order_customer_details_id, order_id, customer_id, restaurant_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5434 (class 0 OID 19611)
-- Dependencies: 303
-- Data for Name: order_delivery_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_delivery_info (order_delivery_id, order_id, delivery_partner_id, enable_delivery, delivery_type, delivery_slot, delivery_address_id, delivery_distance_km, delivery_estimated_time, delivery_actual_time, delivery_person_id, delivery_started_at, delivery_completed_at, delivery_otp, delivery_verification_method, delivery_tracking_url, delivery_proof_url, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5435 (class 0 OID 19624)
-- Dependencies: 304
-- Data for Name: order_dining_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_dining_info (order_dining_id, order_id, table_id, table_no, table_area, no_of_persons, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5436 (class 0 OID 19634)
-- Dependencies: 305
-- Data for Name: order_discount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_discount (order_discount_id, order_discount_type_id, order_id, order_item_id, order_discount_amount, order_discount_percentage, order_discount_code, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5437 (class 0 OID 19644)
-- Dependencies: 306
-- Data for Name: order_instruction; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_instruction (order_instruction_id, order_id, special_instructions, kitchen_notes, delivery_notes, allergen_warning, dietary_preferences, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5438 (class 0 OID 19656)
-- Dependencies: 307
-- Data for Name: order_integration_sync; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_integration_sync (order_integration_sync_id, order_id, sync_status, sync_errors, last_synced_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5439 (class 0 OID 19668)
-- Dependencies: 308
-- Data for Name: order_invoice; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_invoice (order_invoice_id, order_id, is_invoice_generated, invoice_url, invoice_generated_at, gstin, is_business_order, business_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5440 (class 0 OID 19682)
-- Dependencies: 309
-- Data for Name: order_item; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_item (order_item_id, order_id, menu_item_id, menu_item_variation_id, sku, hsn_code, category_id, category_name, base_price, discount_amount, tax_amount, addon_total, is_available, unavailable_reason, substitute_item_id, cooking_instructions, spice_level, customizations, item_status, prepared_at, served_at, cancelled_at, cancellation_reason, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5441 (class 0 OID 19695)
-- Dependencies: 310
-- Data for Name: order_kitchen_detail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_kitchen_detail (order_kitchen_id, order_id, order_item_id, estimated_ready_time, actual_ready_time, preparation_start_time, minimum_preparation_time, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5442 (class 0 OID 19705)
-- Dependencies: 311
-- Data for Name: order_note; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_note (order_note_id, order_id, order_note_type, order_note_text, order_note_visibility, order_note_added_by, is_important, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5443 (class 0 OID 19719)
-- Dependencies: 312
-- Data for Name: order_payment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_payment (order_payment_id, payment_order_id, primary_transaction_id, order_id, order_payment_method_id, tax_calculation_type_id, paid_amount, refund_amount, wallet_amount_used, loyalty_points_used, loyalty_points_earned, collect_cash, order_payment_status, order_payment_transaction_reference, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5444 (class 0 OID 19730)
-- Dependencies: 313
-- Data for Name: order_payment_method; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_payment_method (order_payment_method_id, order_payment_method_code, order_payment_method_name, order_payment_method_is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5445 (class 0 OID 19741)
-- Dependencies: 314
-- Data for Name: order_priority; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_priority (order_priority_id, order_id, is_urgent, priority_level, is_vip_order, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5446 (class 0 OID 19753)
-- Dependencies: 315
-- Data for Name: order_scheduling; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_scheduling (order_scheduling_id, order_id, is_preorder, is_scheduled, preorder_date, preorder_time, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5447 (class 0 OID 19765)
-- Dependencies: 316
-- Data for Name: order_security_detail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_security_detail (order_security_detail_id, order_id, otp, callback_url, callback_received_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5448 (class 0 OID 19777)
-- Dependencies: 317
-- Data for Name: order_source_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_source_type (order_source_type_id, order_source_type_code, order_source_type_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5449 (class 0 OID 19787)
-- Dependencies: 318
-- Data for Name: order_status_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_status_history (order_status_history_id, order_id, order_status_type_id, order_status_changed_by, order_status_changed_at, order_status_notes, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5450 (class 0 OID 19800)
-- Dependencies: 319
-- Data for Name: order_status_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_status_type (order_status_type_id, order_status_code, order_status_name, order_status_description, order_status_is_active, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5451 (class 0 OID 19813)
-- Dependencies: 320
-- Data for Name: order_tax_line; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_tax_line (order_tax_line_id, order_tax_line_charge_id, order_item_id, order_tax_line_tax_type, order_tax_line_percentage, order_tax_line_amount, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5452 (class 0 OID 19823)
-- Dependencies: 321
-- Data for Name: order_total; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_total (order_total_id, order_id, items_total, addons_total, charges_total, discount_total, tax_total, platform_fee, convenience_fee, subtotal, roundoff_amount, total_before_tip, tip_amount, final_amount, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5453 (class 0 OID 19833)
-- Dependencies: 322
-- Data for Name: order_type_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_type_table (order_type_id, order_type_code, order_type_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5454 (class 0 OID 19843)
-- Dependencies: 323
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orders (order_id, restaurant_id, table_booking_id, order_number, order_invoice_number, order_vr_order_id, order_external_reference_id, order_type_id, order_source_type_id, order_status_type_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5455 (class 0 OID 19855)
-- Dependencies: 324
-- Data for Name: password_reset; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.password_reset (password_reset_id, user_id, password_reset_token, password_reset_expires_at, password_reset_used_at, password_reset_ip_address, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5456 (class 0 OID 19867)
-- Dependencies: 325
-- Data for Name: payment_audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_audit_log (audit_log_id, payment_order_id, payment_transaction_id, payment_refund_id, event_type, event_source, request_payload, response_payload, gateway_event_id, gateway_event_type, initiated_by, ip_address, user_agent, event_status, error_message, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5457 (class 0 OID 19879)
-- Dependencies: 326
-- Data for Name: payment_external_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_external_mapping (external_mapping_id, payment_order_id, payment_transaction_id, external_system, external_payment_id, external_order_id, sync_status, sync_attempts, last_synced_at, sync_error, external_response, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5458 (class 0 OID 19892)
-- Dependencies: 327
-- Data for Name: payment_gateway; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_gateway (payment_gateway_id, payment_gateway_code, payment_gateway_name, payment_gateway_is_active, payment_gateway_config, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5459 (class 0 OID 19905)
-- Dependencies: 328
-- Data for Name: payment_order; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_order (payment_order_id, order_id, restaurant_id, customer_id, payment_gateway_id, gateway_order_id, payment_order_status, order_amount, order_currency, payment_link_url, payment_link_id, payment_link_short_url, payment_link_expires_at, retry_count, max_retry_attempts, notes, metadata, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5460 (class 0 OID 19920)
-- Dependencies: 329
-- Data for Name: payment_refund; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_refund (payment_refund_id, payment_transaction_id, order_id, order_item_id, payment_order_id, payment_gateway_id, gateway_refund_id, gateway_payment_id, refund_amount, refund_currency, refund_reason_type_id, refund_reason_notes, refund_status_type_id, initiated_by, approved_by, processing_notes, gateway_response, refund_initiated_at, refund_processed_at, refund_completed_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5461 (class 0 OID 19933)
-- Dependencies: 330
-- Data for Name: payment_retry_attempt; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_retry_attempt (retry_attempt_id, payment_order_id, payment_transaction_id, attempt_number, gateway_payment_id, attempt_status, failure_reason, failure_code, retry_metadata, attempted_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5462 (class 0 OID 19946)
-- Dependencies: 331
-- Data for Name: payment_split; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_split (payment_split_id, payment_transaction_id, order_id, split_party_type, split_party_id, split_amount, split_percentage, split_currency, delivery_partner_id, is_settled, settled_at, settlement_reference, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5463 (class 0 OID 19958)
-- Dependencies: 332
-- Data for Name: payment_status_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_status_type (payment_status_type_id, payment_status_code, payment_status_name, payment_status_description, payment_status_is_terminal, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5464 (class 0 OID 19971)
-- Dependencies: 333
-- Data for Name: payment_transaction; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_transaction (payment_transaction_id, payment_order_id, order_id, restaurant_id, customer_id, payment_gateway_id, gateway_payment_id, gateway_transaction_id, gateway_signature, order_payment_method_id, payment_method_details, transaction_amount, amount_paid, amount_due, transaction_currency, gateway_fee, gateway_tax, net_amount, payment_status_type_id, failure_reason, failure_code, error_description, bank_name, card_network, card_type, card_last4, wallet_provider, upi_vpa, customer_email, customer_contact, gateway_response, attempted_at, authorized_at, captured_at, settled_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5465 (class 0 OID 19984)
-- Dependencies: 334
-- Data for Name: payment_webhook_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_webhook_log (webhook_log_id, payment_gateway_id, webhook_event_id, webhook_event_type, webhook_payload, webhook_signature, signature_verified, processing_status, processing_attempts, processing_error, extracted_payment_id, extracted_order_id, matched_payment_transaction_id, source_ip, received_at, processed_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5466 (class 0 OID 19999)
-- Dependencies: 335
-- Data for Name: pincode_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pincode_table (pincode_id, pincode, city_id, area_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5467 (class 0 OID 20012)
-- Dependencies: 336
-- Data for Name: refund_reason_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.refund_reason_type (refund_reason_type_id, refund_reason_code, refund_reason_name, refund_reason_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5468 (class 0 OID 20024)
-- Dependencies: 337
-- Data for Name: refund_status_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.refund_status_type (refund_status_type_id, refund_status_code, refund_status_name, refund_status_description, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5469 (class 0 OID 20038)
-- Dependencies: 338
-- Data for Name: restaurant_faq; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.restaurant_faq (restaurant_faq_id, restaurant_id, restaurant_faq_question, restaurant_faq_answer, restaurant_faq_category, restaurant_faq_display_order, restaurant_faq_is_active, restaurant_faq_view_count, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5470 (class 0 OID 20056)
-- Dependencies: 339
-- Data for Name: restaurant_policy; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.restaurant_policy (restaurant_policy_id, restaurant_id, restaurant_policy_category, restaurant_policy_title, restaurant_policy_description, restaurant_is_active, restaurant_effective_from, restaurant_effective_until, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5471 (class 0 OID 20072)
-- Dependencies: 340
-- Data for Name: restaurant_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.restaurant_table (restaurant_id, chain_id, branch_id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
6eb89f66-661c-4294-85b4-044519fdec1b	d9d9c09b-1ee8-48dc-a62e-c6928f4ecbe4	ccd77567-41db-49e0-9f55-ca646cf040ad	2025-11-26 17:17:25.782412+05:30	2025-11-26 17:17:25.782412+05:30	f	\N
\.


--
-- TOC entry 5472 (class 0 OID 20084)
-- Dependencies: 341
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role (role_id, role_name, role_unique_code, role_description, role_level, is_system_role, role_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5473 (class 0 OID 20099)
-- Dependencies: 342
-- Data for Name: round_robin_pool; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.round_robin_pool (round_robin_pool_id, restaurant_id, round_robin_pool_name, round_robin_pool_type, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5474 (class 0 OID 20110)
-- Dependencies: 343
-- Data for Name: round_robin_pool_member; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.round_robin_pool_member (round_robin_pool_member_id, round_robin_pool_id, user_id, round_robin_pool_member_priority, round_robin_pool_member_is_active, round_robin_pool_member_last_assigned_at, round_robin_pool_member_total_assignments, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5475 (class 0 OID 20124)
-- Dependencies: 344
-- Data for Name: shift_timing; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shift_timing (shift_timing_id, restaurant_id, shift_timing_name, shift_timing_shift_code, shift_timing_start_time, shift_timing_end_time, shift_timing_break_duration_minutes, shift_timing_is_overnight, shift_timing_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5476 (class 0 OID 20136)
-- Dependencies: 345
-- Data for Name: state_table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.state_table (state_id, state_name, country_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5477 (class 0 OID 20147)
-- Dependencies: 346
-- Data for Name: table_booking_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_booking_info (table_booking_id, restaurant_id, table_id, meal_slot_timing_id, previous_slot_id, customer_id, occasion_id, party_size, booking_date, booking_time, booking_status, special_request, cancellation_reason, is_advance_booking, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5478 (class 0 OID 20163)
-- Dependencies: 347
-- Data for Name: table_booking_occasion_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_booking_occasion_info (occasion_id, occasion_type, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5479 (class 0 OID 20174)
-- Dependencies: 348
-- Data for Name: table_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_info (table_id, restaurant_id, table_number, table_capacity, table_type, is_active, floor_location, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5480 (class 0 OID 20188)
-- Dependencies: 349
-- Data for Name: table_special_features; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_special_features (table_feature_id, table_id, feature_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5481 (class 0 OID 20199)
-- Dependencies: 350
-- Data for Name: tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tag (tag_id, tag_name, tag_type, tag_description, tag_color, tag_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5482 (class 0 OID 20211)
-- Dependencies: 351
-- Data for Name: tags_feedback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tags_feedback (tag_id, tag_name, description, color_code, usage_count, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5483 (class 0 OID 20226)
-- Dependencies: 352
-- Data for Name: tax_calculation_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tax_calculation_type (tax_calculation_type_id, tax_calculation_type_code, tax_calculation_type_name, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5484 (class 0 OID 20238)
-- Dependencies: 353
-- Data for Name: taxes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.taxes (tax_id, restaurant_id, tax_name, tax_percentage, tax_type, tax_status, tax_ordertype, tax_total, tax_rank, tax_description, tax_consider_in_core_amount, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5485 (class 0 OID 20252)
-- Dependencies: 354
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."user" (user_id, user_email, user_mobile_no, user_password_hash, user_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5486 (class 0 OID 20264)
-- Dependencies: 355
-- Data for Name: user_audit_trail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_audit_trail (user_audit_trail_id, user_id, user_audit_trail_table_name, user_audit_trail_record_id, user_audit_trail_action, user_audit_trail_old_values, user_audit_trail_new_values, user_audit_trail_changed_by, user_audit_trail_changed_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5487 (class 0 OID 20277)
-- Dependencies: 356
-- Data for Name: user_contact; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_contact (user_contact_id, user_id, user_contact_type, user_contact_value, user_contact_is_primary, user_contact_is_verified, user_contact_verified_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5488 (class 0 OID 20291)
-- Dependencies: 357
-- Data for Name: user_department; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_department (user_department_id, user_id, department_id, user_department_is_primary, user_department_assigned_at, user_department_assigned_by, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5489 (class 0 OID 20303)
-- Dependencies: 358
-- Data for Name: user_login_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_login_history (user_login_history_id, user_id, user_login_history_login_at, user_login_history_logout_at, user_login_history_ip_address, user_login_history_user_agent, user_login_history_device_type, user_login_history_location_data, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5490 (class 0 OID 20315)
-- Dependencies: 359
-- Data for Name: user_profile; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_profile (user_profile_id, user_id, user_profile_first_name, user_profile_last_name, user_profile_display_name, user_profile_gender, user_profile_date_of_birth, user_profile_profile_picture_url, user_profile_bio, user_profile_address_line1, user_profile_address_line2, user_profile_city, user_profile_state, user_profile_country, user_profile_postal_code, user_profile_timezone, user_profile_language_preference, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5491 (class 0 OID 20327)
-- Dependencies: 360
-- Data for Name: user_role; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_role (user_role_id, user_id, role_id, user_role_assigned_at, user_role_assigned_by, user_role_expires_at, user_role_is_primary, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5492 (class 0 OID 20339)
-- Dependencies: 361
-- Data for Name: user_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_session (user_session_id, user_id, user_session_token, user_session_refresh_token, user_session_ip_address, user_session_user_agent, user_session_device_info, user_session_expires_at, user_session_last_activity_at, user_session_logged_out_at, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5493 (class 0 OID 20351)
-- Dependencies: 362
-- Data for Name: user_shift_assignment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_shift_assignment (user_shift_assignment_id, user_id, shift_timing_id, user_shift_assignment_effective_from, user_shift_assignment_effective_to, user_shift_assignment_assigned_at, user_shift_assignment_assigned_by, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5494 (class 0 OID 20362)
-- Dependencies: 363
-- Data for Name: user_tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_tag (user_tag_id, user_id, tag_id, user_tag_added_at, user_tag_added_by, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5495 (class 0 OID 20373)
-- Dependencies: 364
-- Data for Name: variation_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.variation_groups (variation_group_id, restaurant_id, variation_group_name, variation_group_selection_type, variation_group_min_selection, variation_group_max_selection, variation_group_status, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 5496 (class 0 OID 20385)
-- Dependencies: 365
-- Data for Name: variation_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.variation_options (variation_option_id, variation_group_id, menu_item_id, option_name, option_price_modifier, option_rank, option_status, dietary_type_id, created_at, updated_at, created_by, updated_by, deleted_at, is_deleted) FROM stdin;
\.


--
-- TOC entry 4635 (class 2606 OID 18602)
-- Name: account_lock account_lock_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lock
    ADD CONSTRAINT account_lock_pkey PRIMARY KEY (account_lock_id);


--
-- TOC entry 4637 (class 2606 OID 18615)
-- Name: allergens allergens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allergens
    ADD CONSTRAINT allergens_pkey PRIMARY KEY (allergen_id);


--
-- TOC entry 4639 (class 2606 OID 18628)
-- Name: branch_contact_table branch_contact_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_contact_table
    ADD CONSTRAINT branch_contact_table_pkey PRIMARY KEY (branch_contact_id);


--
-- TOC entry 4641 (class 2606 OID 18641)
-- Name: branch_info_table branch_info_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_info_table
    ADD CONSTRAINT branch_info_table_pkey PRIMARY KEY (branch_id);


--
-- TOC entry 4643 (class 2606 OID 18653)
-- Name: branch_location_table branch_location_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_location_table
    ADD CONSTRAINT branch_location_table_pkey PRIMARY KEY (branch_location_id);


--
-- TOC entry 4645 (class 2606 OID 18663)
-- Name: branch_timing_policy branch_timing_policy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_timing_policy
    ADD CONSTRAINT branch_timing_policy_pkey PRIMARY KEY (branch_timing_id);


--
-- TOC entry 4647 (class 2606 OID 18676)
-- Name: chain_contact_table chain_contact_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_contact_table
    ADD CONSTRAINT chain_contact_table_pkey PRIMARY KEY (chain_contact_id);


--
-- TOC entry 4649 (class 2606 OID 18689)
-- Name: chain_info_table chain_info_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_info_table
    ADD CONSTRAINT chain_info_table_pkey PRIMARY KEY (chain_id);


--
-- TOC entry 4651 (class 2606 OID 18701)
-- Name: chain_location_table chain_location_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_location_table
    ADD CONSTRAINT chain_location_table_pkey PRIMARY KEY (chain_location_id);


--
-- TOC entry 4653 (class 2606 OID 18712)
-- Name: city_table city_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.city_table
    ADD CONSTRAINT city_table_pkey PRIMARY KEY (city_id);


--
-- TOC entry 4657 (class 2606 OID 18735)
-- Name: combo_item_components combo_item_components_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item_components
    ADD CONSTRAINT combo_item_components_pkey PRIMARY KEY (combo_item_component_id);


--
-- TOC entry 4655 (class 2606 OID 18723)
-- Name: combo_item combo_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item
    ADD CONSTRAINT combo_item_pkey PRIMARY KEY (combo_item_id);


--
-- TOC entry 4660 (class 2606 OID 18746)
-- Name: country_table country_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_table
    ADD CONSTRAINT country_table_pkey PRIMARY KEY (country_id);


--
-- TOC entry 4662 (class 2606 OID 18757)
-- Name: cuisines cuisines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuisines
    ADD CONSTRAINT cuisines_pkey PRIMARY KEY (cuisine_id);


--
-- TOC entry 4664 (class 2606 OID 18770)
-- Name: customer_activity_log customer_activity_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_activity_log
    ADD CONSTRAINT customer_activity_log_pkey PRIMARY KEY (log_id);


--
-- TOC entry 4666 (class 2606 OID 18783)
-- Name: customer_address_table customer_address_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_address_table
    ADD CONSTRAINT customer_address_table_pkey PRIMARY KEY (customer_address_id);


--
-- TOC entry 4668 (class 2606 OID 18795)
-- Name: customer_allergens customer_allergens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_allergens
    ADD CONSTRAINT customer_allergens_pkey PRIMARY KEY (customer_id, allergen_id);


--
-- TOC entry 4670 (class 2606 OID 18808)
-- Name: customer_authentication customer_authentication_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_authentication
    ADD CONSTRAINT customer_authentication_pkey PRIMARY KEY (auth_id);


--
-- TOC entry 4672 (class 2606 OID 18822)
-- Name: customer_consent customer_consent_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_consent
    ADD CONSTRAINT customer_consent_pkey PRIMARY KEY (consent_id);


--
-- TOC entry 4674 (class 2606 OID 18835)
-- Name: customer_contact_table customer_contact_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_contact_table
    ADD CONSTRAINT customer_contact_table_pkey PRIMARY KEY (contact_id);


--
-- TOC entry 4676 (class 2606 OID 18848)
-- Name: customer_devices customer_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_devices
    ADD CONSTRAINT customer_devices_pkey PRIMARY KEY (device_id);


--
-- TOC entry 4678 (class 2606 OID 18860)
-- Name: customer_dietary_restrictions customer_dietary_restrictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_dietary_restrictions
    ADD CONSTRAINT customer_dietary_restrictions_pkey PRIMARY KEY (customer_id, dietary_restriction_id);


--
-- TOC entry 4680 (class 2606 OID 18871)
-- Name: customer_favorite_items customer_favorite_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_favorite_items
    ADD CONSTRAINT customer_favorite_items_pkey PRIMARY KEY (favorite_id);


--
-- TOC entry 4682 (class 2606 OID 18882)
-- Name: customer_gender customer_gender_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_gender
    ADD CONSTRAINT customer_gender_pkey PRIMARY KEY (customer_gender_id);


--
-- TOC entry 4684 (class 2606 OID 18892)
-- Name: customer_preferences customer_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_preferences
    ADD CONSTRAINT customer_preferences_pkey PRIMARY KEY (customer_preference_id);


--
-- TOC entry 4686 (class 2606 OID 18903)
-- Name: customer_profile_table customer_profile_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_profile_table
    ADD CONSTRAINT customer_profile_table_pkey PRIMARY KEY (customer_id);


--
-- TOC entry 4688 (class 2606 OID 18916)
-- Name: customer_search_queries customer_search_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_search_queries
    ADD CONSTRAINT customer_search_queries_pkey PRIMARY KEY (query_id);


--
-- TOC entry 4690 (class 2606 OID 18929)
-- Name: customer_sessions customer_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_pkey PRIMARY KEY (session_id);


--
-- TOC entry 4692 (class 2606 OID 18939)
-- Name: customer_table customer_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_table
    ADD CONSTRAINT customer_table_pkey PRIMARY KEY (customer_id);


--
-- TOC entry 4694 (class 2606 OID 18950)
-- Name: customer_tag_mapping customer_tag_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tag_mapping
    ADD CONSTRAINT customer_tag_mapping_pkey PRIMARY KEY (customer_id, tag_id);


--
-- TOC entry 4696 (class 2606 OID 18963)
-- Name: customer_tags customer_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tags
    ADD CONSTRAINT customer_tags_pkey PRIMARY KEY (tag_id);


--
-- TOC entry 4698 (class 2606 OID 18975)
-- Name: department department_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_pkey PRIMARY KEY (department_id);


--
-- TOC entry 4700 (class 2606 OID 18988)
-- Name: dietary_restrictions dietary_restrictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dietary_restrictions
    ADD CONSTRAINT dietary_restrictions_pkey PRIMARY KEY (dietary_restriction_id);


--
-- TOC entry 4702 (class 2606 OID 19000)
-- Name: dietary_types dietary_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dietary_types
    ADD CONSTRAINT dietary_types_pkey PRIMARY KEY (dietary_type_id);


--
-- TOC entry 4704 (class 2606 OID 19014)
-- Name: discount discount_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discount
    ADD CONSTRAINT discount_pkey PRIMARY KEY (discount_id);


--
-- TOC entry 4706 (class 2606 OID 19024)
-- Name: discount_schedule discount_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discount_schedule
    ADD CONSTRAINT discount_schedule_pkey PRIMARY KEY (discount_schedule_id);


--
-- TOC entry 4708 (class 2606 OID 19034)
-- Name: discount_type discount_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discount_type
    ADD CONSTRAINT discount_type_pkey PRIMARY KEY (discount_type_id);


--
-- TOC entry 4710 (class 2606 OID 19047)
-- Name: email_verification email_verification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_verification
    ADD CONSTRAINT email_verification_pkey PRIMARY KEY (email_verification_id);


--
-- TOC entry 4712 (class 2606 OID 19057)
-- Name: entity_slot_config entity_slot_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_slot_config
    ADD CONSTRAINT entity_slot_config_pkey PRIMARY KEY (slot_config_id);


--
-- TOC entry 4716 (class 2606 OID 19091)
-- Name: feedback_attachments feedback_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_attachments
    ADD CONSTRAINT feedback_attachments_pkey PRIMARY KEY (attachment_id);


--
-- TOC entry 4719 (class 2606 OID 19106)
-- Name: feedback_categories feedback_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_categories
    ADD CONSTRAINT feedback_categories_pkey PRIMARY KEY (category_id);


--
-- TOC entry 4721 (class 2606 OID 19121)
-- Name: feedback_notifications feedback_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_notifications
    ADD CONSTRAINT feedback_notifications_pkey PRIMARY KEY (notification_id);


--
-- TOC entry 4714 (class 2606 OID 19076)
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (feedback_id);


--
-- TOC entry 4729 (class 2606 OID 19159)
-- Name: feedback_priority_history feedback_priority_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_priority_history
    ADD CONSTRAINT feedback_priority_history_pkey PRIMARY KEY (history_id);


--
-- TOC entry 4731 (class 2606 OID 19176)
-- Name: feedback_responses feedback_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_responses
    ADD CONSTRAINT feedback_responses_pkey PRIMARY KEY (response_id);


--
-- TOC entry 4733 (class 2606 OID 19190)
-- Name: feedback_status_history feedback_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_status_history
    ADD CONSTRAINT feedback_status_history_pkey PRIMARY KEY (history_id);


--
-- TOC entry 4738 (class 2606 OID 19218)
-- Name: feedback_tags feedback_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_tags
    ADD CONSTRAINT feedback_tags_pkey PRIMARY KEY (feedback_id, tag_id);


--
-- TOC entry 4740 (class 2606 OID 19233)
-- Name: feedback_types feedback_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_types
    ADD CONSTRAINT feedback_types_pkey PRIMARY KEY (type_id);


--
-- TOC entry 4743 (class 2606 OID 19248)
-- Name: integration_config_table integration_config_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_config_table
    ADD CONSTRAINT integration_config_table_pkey PRIMARY KEY (integration_config_id);


--
-- TOC entry 4745 (class 2606 OID 19260)
-- Name: integration_credentials_table integration_credentials_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_credentials_table
    ADD CONSTRAINT integration_credentials_table_pkey PRIMARY KEY (credential_id);


--
-- TOC entry 4747 (class 2606 OID 19272)
-- Name: integration_metadata_table integration_metadata_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_metadata_table
    ADD CONSTRAINT integration_metadata_table_pkey PRIMARY KEY (metadata_id);


--
-- TOC entry 4749 (class 2606 OID 19285)
-- Name: integration_provider_table integration_provider_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_provider_table
    ADD CONSTRAINT integration_provider_table_pkey PRIMARY KEY (provider_id);


--
-- TOC entry 4751 (class 2606 OID 19297)
-- Name: languages languages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT languages_pkey PRIMARY KEY (language_id);


--
-- TOC entry 4753 (class 2606 OID 19311)
-- Name: login_attempt login_attempt_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_attempt
    ADD CONSTRAINT login_attempt_pkey PRIMARY KEY (login_attempt_id);


--
-- TOC entry 4755 (class 2606 OID 19324)
-- Name: loyalty_transaction loyalty_transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.loyalty_transaction
    ADD CONSTRAINT loyalty_transaction_pkey PRIMARY KEY (loyalty_txn_id);


--
-- TOC entry 4757 (class 2606 OID 19335)
-- Name: meal_slot_timing meal_slot_timing_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meal_slot_timing
    ADD CONSTRAINT meal_slot_timing_pkey PRIMARY KEY (meal_slot_timing_id);


--
-- TOC entry 4759 (class 2606 OID 19345)
-- Name: meal_type meal_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meal_type
    ADD CONSTRAINT meal_type_pkey PRIMARY KEY (meal_type_id);


--
-- TOC entry 4763 (class 2606 OID 19357)
-- Name: menu_categories menu_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT menu_categories_pkey PRIMARY KEY (menu_category_id);


--
-- TOC entry 4774 (class 2606 OID 19391)
-- Name: menu_item_addon_group menu_item_addon_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_group
    ADD CONSTRAINT menu_item_addon_group_pkey PRIMARY KEY (menu_item_addon_group_id);


--
-- TOC entry 4776 (class 2606 OID 19401)
-- Name: menu_item_addon_item menu_item_addon_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_item
    ADD CONSTRAINT menu_item_addon_item_pkey PRIMARY KEY (menu_item_addon_id);


--
-- TOC entry 4778 (class 2606 OID 19411)
-- Name: menu_item_addon_mapping menu_item_addon_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_mapping
    ADD CONSTRAINT menu_item_addon_mapping_pkey PRIMARY KEY (menu_item_addon_mapping_id);


--
-- TOC entry 4967 (class 2606 OID 21604)
-- Name: menu_item_allergen_mapping menu_item_allergen_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_allergen_mapping
    ADD CONSTRAINT menu_item_allergen_mapping_pkey PRIMARY KEY (mapping_id);


--
-- TOC entry 4780 (class 2606 OID 19421)
-- Name: menu_item_attribute menu_item_attribute_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_attribute
    ADD CONSTRAINT menu_item_attribute_pkey PRIMARY KEY (menu_item_attribute_id);


--
-- TOC entry 4785 (class 2606 OID 19432)
-- Name: menu_item_availability_schedule menu_item_availability_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_availability_schedule
    ADD CONSTRAINT menu_item_availability_schedule_pkey PRIMARY KEY (schedule_id);


--
-- TOC entry 4955 (class 2606 OID 21506)
-- Name: menu_item_category_mapping menu_item_category_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT menu_item_category_mapping_pkey PRIMARY KEY (mapping_id);


--
-- TOC entry 4789 (class 2606 OID 19442)
-- Name: menu_item_cuisine_mapping menu_item_cuisine_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_cuisine_mapping
    ADD CONSTRAINT menu_item_cuisine_mapping_pkey PRIMARY KEY (menu_item_cuisine_mapping_id);


--
-- TOC entry 4974 (class 2606 OID 21637)
-- Name: menu_item_dietary_mapping menu_item_dietary_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_dietary_mapping
    ADD CONSTRAINT menu_item_dietary_mapping_pkey PRIMARY KEY (mapping_id);


--
-- TOC entry 4791 (class 2606 OID 19452)
-- Name: menu_item_discount_mapping menu_item_discount_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_discount_mapping
    ADD CONSTRAINT menu_item_discount_mapping_pkey PRIMARY KEY (menu_item_discount_mapping_id);


--
-- TOC entry 4962 (class 2606 OID 21578)
-- Name: menu_item_ingredient menu_item_ingredient_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ingredient
    ADD CONSTRAINT menu_item_ingredient_pkey PRIMARY KEY (ingredient_id);


--
-- TOC entry 4793 (class 2606 OID 19464)
-- Name: menu_item_option menu_item_option_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_option
    ADD CONSTRAINT menu_item_option_pkey PRIMARY KEY (menu_item_option_id);


--
-- TOC entry 4795 (class 2606 OID 19474)
-- Name: menu_item_ordertype_mapping menu_item_ordertype_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ordertype_mapping
    ADD CONSTRAINT menu_item_ordertype_mapping_pkey PRIMARY KEY (menu_item_ordertype_mapping_id);


--
-- TOC entry 4772 (class 2606 OID 19381)
-- Name: menu_item menu_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item
    ADD CONSTRAINT menu_item_pkey PRIMARY KEY (menu_item_id);


--
-- TOC entry 4799 (class 2606 OID 19494)
-- Name: menu_item_tag_mapping menu_item_tag_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tag_mapping
    ADD CONSTRAINT menu_item_tag_mapping_pkey PRIMARY KEY (menu_item_tag_mapping_id);


--
-- TOC entry 4797 (class 2606 OID 19484)
-- Name: menu_item_tag menu_item_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tag
    ADD CONSTRAINT menu_item_tag_pkey PRIMARY KEY (menu_item_tag_id);


--
-- TOC entry 4801 (class 2606 OID 19507)
-- Name: menu_item_tax_mapping menu_item_tax_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tax_mapping
    ADD CONSTRAINT menu_item_tax_mapping_pkey PRIMARY KEY (menu_item_tax_mapping_id);


--
-- TOC entry 4805 (class 2606 OID 19528)
-- Name: menu_item_variation_mapping menu_item_variation_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation_mapping
    ADD CONSTRAINT menu_item_variation_mapping_pkey PRIMARY KEY (menu_item_variation_mapping_id);


--
-- TOC entry 4803 (class 2606 OID 19518)
-- Name: menu_item_variation menu_item_variation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation
    ADD CONSTRAINT menu_item_variation_pkey PRIMARY KEY (menu_item_variation_id);


--
-- TOC entry 4807 (class 2606 OID 19540)
-- Name: menu_sections menu_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sections
    ADD CONSTRAINT menu_sections_pkey PRIMARY KEY (menu_section_id);


--
-- TOC entry 4811 (class 2606 OID 19552)
-- Name: menu_sub_categories menu_sub_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sub_categories
    ADD CONSTRAINT menu_sub_categories_pkey PRIMARY KEY (menu_sub_category_id);


--
-- TOC entry 4813 (class 2606 OID 19564)
-- Name: menu_sync_log menu_sync_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sync_log
    ADD CONSTRAINT menu_sync_log_pkey PRIMARY KEY (menu_sync_log_id);


--
-- TOC entry 4815 (class 2606 OID 19576)
-- Name: menu_version_history menu_version_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_version_history
    ADD CONSTRAINT menu_version_history_pkey PRIMARY KEY (menu_version_id);


--
-- TOC entry 4817 (class 2606 OID 19588)
-- Name: order_audit order_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audit
    ADD CONSTRAINT order_audit_pkey PRIMARY KEY (order_audit_id);


--
-- TOC entry 4819 (class 2606 OID 19600)
-- Name: order_charges order_charges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_charges
    ADD CONSTRAINT order_charges_pkey PRIMARY KEY (order_charges_id);


--
-- TOC entry 4821 (class 2606 OID 19610)
-- Name: order_customer_details order_customer_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_customer_details
    ADD CONSTRAINT order_customer_details_pkey PRIMARY KEY (order_customer_details_id);


--
-- TOC entry 4823 (class 2606 OID 19623)
-- Name: order_delivery_info order_delivery_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_delivery_info
    ADD CONSTRAINT order_delivery_info_pkey PRIMARY KEY (order_delivery_id);


--
-- TOC entry 4825 (class 2606 OID 19633)
-- Name: order_dining_info order_dining_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_dining_info
    ADD CONSTRAINT order_dining_info_pkey PRIMARY KEY (order_dining_id);


--
-- TOC entry 4827 (class 2606 OID 19643)
-- Name: order_discount order_discount_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_discount
    ADD CONSTRAINT order_discount_pkey PRIMARY KEY (order_discount_id);


--
-- TOC entry 4829 (class 2606 OID 19655)
-- Name: order_instruction order_instruction_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_instruction
    ADD CONSTRAINT order_instruction_pkey PRIMARY KEY (order_instruction_id);


--
-- TOC entry 4831 (class 2606 OID 19667)
-- Name: order_integration_sync order_integration_sync_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_integration_sync
    ADD CONSTRAINT order_integration_sync_pkey PRIMARY KEY (order_integration_sync_id);


--
-- TOC entry 4833 (class 2606 OID 19681)
-- Name: order_invoice order_invoice_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_invoice
    ADD CONSTRAINT order_invoice_pkey PRIMARY KEY (order_invoice_id);


--
-- TOC entry 4835 (class 2606 OID 19694)
-- Name: order_item order_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT order_item_pkey PRIMARY KEY (order_item_id);


--
-- TOC entry 4837 (class 2606 OID 19704)
-- Name: order_kitchen_detail order_kitchen_detail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_kitchen_detail
    ADD CONSTRAINT order_kitchen_detail_pkey PRIMARY KEY (order_kitchen_id);


--
-- TOC entry 4839 (class 2606 OID 19718)
-- Name: order_note order_note_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_note
    ADD CONSTRAINT order_note_pkey PRIMARY KEY (order_note_id);


--
-- TOC entry 4843 (class 2606 OID 19740)
-- Name: order_payment_method order_payment_method_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment_method
    ADD CONSTRAINT order_payment_method_pkey PRIMARY KEY (order_payment_method_id);


--
-- TOC entry 4841 (class 2606 OID 19729)
-- Name: order_payment order_payment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT order_payment_pkey PRIMARY KEY (order_payment_id);


--
-- TOC entry 4845 (class 2606 OID 19752)
-- Name: order_priority order_priority_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_priority
    ADD CONSTRAINT order_priority_pkey PRIMARY KEY (order_priority_id);


--
-- TOC entry 4847 (class 2606 OID 19764)
-- Name: order_scheduling order_scheduling_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_scheduling
    ADD CONSTRAINT order_scheduling_pkey PRIMARY KEY (order_scheduling_id);


--
-- TOC entry 4849 (class 2606 OID 19776)
-- Name: order_security_detail order_security_detail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_security_detail
    ADD CONSTRAINT order_security_detail_pkey PRIMARY KEY (order_security_detail_id);


--
-- TOC entry 4851 (class 2606 OID 19786)
-- Name: order_source_type order_source_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_source_type
    ADD CONSTRAINT order_source_type_pkey PRIMARY KEY (order_source_type_id);


--
-- TOC entry 4853 (class 2606 OID 19799)
-- Name: order_status_history order_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT order_status_history_pkey PRIMARY KEY (order_status_history_id);


--
-- TOC entry 4855 (class 2606 OID 19812)
-- Name: order_status_type order_status_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_type
    ADD CONSTRAINT order_status_type_pkey PRIMARY KEY (order_status_type_id);


--
-- TOC entry 4857 (class 2606 OID 19822)
-- Name: order_tax_line order_tax_line_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_tax_line
    ADD CONSTRAINT order_tax_line_pkey PRIMARY KEY (order_tax_line_id);


--
-- TOC entry 4859 (class 2606 OID 19832)
-- Name: order_total order_total_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_total
    ADD CONSTRAINT order_total_pkey PRIMARY KEY (order_total_id);


--
-- TOC entry 4861 (class 2606 OID 19842)
-- Name: order_type_table order_type_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_type_table
    ADD CONSTRAINT order_type_table_pkey PRIMARY KEY (order_type_id);


--
-- TOC entry 4863 (class 2606 OID 19854)
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- TOC entry 4865 (class 2606 OID 19866)
-- Name: password_reset password_reset_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset
    ADD CONSTRAINT password_reset_pkey PRIMARY KEY (password_reset_id);


--
-- TOC entry 4867 (class 2606 OID 19878)
-- Name: payment_audit_log payment_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_audit_log
    ADD CONSTRAINT payment_audit_log_pkey PRIMARY KEY (audit_log_id);


--
-- TOC entry 4869 (class 2606 OID 19891)
-- Name: payment_external_mapping payment_external_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_external_mapping
    ADD CONSTRAINT payment_external_mapping_pkey PRIMARY KEY (external_mapping_id);


--
-- TOC entry 4871 (class 2606 OID 19904)
-- Name: payment_gateway payment_gateway_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_gateway
    ADD CONSTRAINT payment_gateway_pkey PRIMARY KEY (payment_gateway_id);


--
-- TOC entry 4873 (class 2606 OID 19919)
-- Name: payment_order payment_order_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_order
    ADD CONSTRAINT payment_order_pkey PRIMARY KEY (payment_order_id);


--
-- TOC entry 4875 (class 2606 OID 19932)
-- Name: payment_refund payment_refund_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT payment_refund_pkey PRIMARY KEY (payment_refund_id);


--
-- TOC entry 4877 (class 2606 OID 19945)
-- Name: payment_retry_attempt payment_retry_attempt_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_retry_attempt
    ADD CONSTRAINT payment_retry_attempt_pkey PRIMARY KEY (retry_attempt_id);


--
-- TOC entry 4879 (class 2606 OID 19957)
-- Name: payment_split payment_split_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_split
    ADD CONSTRAINT payment_split_pkey PRIMARY KEY (payment_split_id);


--
-- TOC entry 4881 (class 2606 OID 19970)
-- Name: payment_status_type payment_status_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_status_type
    ADD CONSTRAINT payment_status_type_pkey PRIMARY KEY (payment_status_type_id);


--
-- TOC entry 4883 (class 2606 OID 19983)
-- Name: payment_transaction payment_transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT payment_transaction_pkey PRIMARY KEY (payment_transaction_id);


--
-- TOC entry 4885 (class 2606 OID 19998)
-- Name: payment_webhook_log payment_webhook_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_webhook_log
    ADD CONSTRAINT payment_webhook_log_pkey PRIMARY KEY (webhook_log_id);


--
-- TOC entry 4887 (class 2606 OID 20011)
-- Name: pincode_table pincode_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pincode_table
    ADD CONSTRAINT pincode_table_pkey PRIMARY KEY (pincode_id);


--
-- TOC entry 4723 (class 2606 OID 19133)
-- Name: feedback_platforms platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (platform_id);


--
-- TOC entry 4726 (class 2606 OID 19145)
-- Name: feedback_priorities priorities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_priorities
    ADD CONSTRAINT priorities_pkey PRIMARY KEY (priority_id);


--
-- TOC entry 4889 (class 2606 OID 20023)
-- Name: refund_reason_type refund_reason_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refund_reason_type
    ADD CONSTRAINT refund_reason_type_pkey PRIMARY KEY (refund_reason_type_id);


--
-- TOC entry 4891 (class 2606 OID 20037)
-- Name: refund_status_type refund_status_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refund_status_type
    ADD CONSTRAINT refund_status_type_pkey PRIMARY KEY (refund_status_type_id);


--
-- TOC entry 4893 (class 2606 OID 20055)
-- Name: restaurant_faq restaurant_faq_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_faq
    ADD CONSTRAINT restaurant_faq_pkey PRIMARY KEY (restaurant_faq_id);


--
-- TOC entry 4895 (class 2606 OID 20071)
-- Name: restaurant_policy restaurant_policy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_policy
    ADD CONSTRAINT restaurant_policy_pkey PRIMARY KEY (restaurant_policy_id);


--
-- TOC entry 4897 (class 2606 OID 20083)
-- Name: restaurant_table restaurant_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table
    ADD CONSTRAINT restaurant_table_pkey PRIMARY KEY (restaurant_id);


--
-- TOC entry 4899 (class 2606 OID 20098)
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (role_id);


--
-- TOC entry 4903 (class 2606 OID 20123)
-- Name: round_robin_pool_member round_robin_pool_member_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.round_robin_pool_member
    ADD CONSTRAINT round_robin_pool_member_pkey PRIMARY KEY (round_robin_pool_member_id);


--
-- TOC entry 4901 (class 2606 OID 20109)
-- Name: round_robin_pool round_robin_pool_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.round_robin_pool
    ADD CONSTRAINT round_robin_pool_pkey PRIMARY KEY (round_robin_pool_id);


--
-- TOC entry 4905 (class 2606 OID 20135)
-- Name: shift_timing shift_timing_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_timing
    ADD CONSTRAINT shift_timing_pkey PRIMARY KEY (shift_timing_id);


--
-- TOC entry 4907 (class 2606 OID 20146)
-- Name: state_table state_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.state_table
    ADD CONSTRAINT state_table_pkey PRIMARY KEY (state_id);


--
-- TOC entry 4735 (class 2606 OID 19206)
-- Name: feedback_statuses statuses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_statuses
    ADD CONSTRAINT statuses_pkey PRIMARY KEY (status_id);


--
-- TOC entry 4909 (class 2606 OID 20162)
-- Name: table_booking_info table_booking_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT table_booking_info_pkey PRIMARY KEY (table_booking_id);


--
-- TOC entry 4911 (class 2606 OID 20173)
-- Name: table_booking_occasion_info table_booking_occasion_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_occasion_info
    ADD CONSTRAINT table_booking_occasion_info_pkey PRIMARY KEY (occasion_id);


--
-- TOC entry 4913 (class 2606 OID 20187)
-- Name: table_info table_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_info
    ADD CONSTRAINT table_info_pkey PRIMARY KEY (table_id);


--
-- TOC entry 4915 (class 2606 OID 20198)
-- Name: table_special_features table_special_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_special_features
    ADD CONSTRAINT table_special_features_pkey PRIMARY KEY (table_feature_id);


--
-- TOC entry 4917 (class 2606 OID 20210)
-- Name: tag tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (tag_id);


--
-- TOC entry 4919 (class 2606 OID 20224)
-- Name: tags_feedback tags_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags_feedback
    ADD CONSTRAINT tags_feedback_pkey PRIMARY KEY (tag_id);


--
-- TOC entry 4922 (class 2606 OID 20237)
-- Name: tax_calculation_type tax_calculation_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_calculation_type
    ADD CONSTRAINT tax_calculation_type_pkey PRIMARY KEY (tax_calculation_type_id);


--
-- TOC entry 4924 (class 2606 OID 20251)
-- Name: taxes taxes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxes
    ADD CONSTRAINT taxes_pkey PRIMARY KEY (tax_id);


--
-- TOC entry 4957 (class 2606 OID 21508)
-- Name: menu_item_category_mapping unique_item_category_subcategory; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT unique_item_category_subcategory UNIQUE (menu_item_id, menu_category_id, menu_sub_category_id);


--
-- TOC entry 4969 (class 2606 OID 21606)
-- Name: menu_item_allergen_mapping uq_menu_item_allergen; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_allergen_mapping
    ADD CONSTRAINT uq_menu_item_allergen UNIQUE (menu_item_id, allergen_id);


--
-- TOC entry 4976 (class 2606 OID 21639)
-- Name: menu_item_dietary_mapping uq_menu_item_dietary; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_dietary_mapping
    ADD CONSTRAINT uq_menu_item_dietary UNIQUE (menu_item_id, dietary_type_id);


--
-- TOC entry 4928 (class 2606 OID 20276)
-- Name: user_audit_trail user_audit_trail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_audit_trail
    ADD CONSTRAINT user_audit_trail_pkey PRIMARY KEY (user_audit_trail_id);


--
-- TOC entry 4930 (class 2606 OID 20290)
-- Name: user_contact user_contact_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_contact
    ADD CONSTRAINT user_contact_pkey PRIMARY KEY (user_contact_id);


--
-- TOC entry 4932 (class 2606 OID 20302)
-- Name: user_department user_department_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_department
    ADD CONSTRAINT user_department_pkey PRIMARY KEY (user_department_id);


--
-- TOC entry 4934 (class 2606 OID 20314)
-- Name: user_login_history user_login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_login_history
    ADD CONSTRAINT user_login_history_pkey PRIMARY KEY (user_login_history_id);


--
-- TOC entry 4926 (class 2606 OID 20263)
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4936 (class 2606 OID 20326)
-- Name: user_profile user_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_pkey PRIMARY KEY (user_profile_id);


--
-- TOC entry 4938 (class 2606 OID 20338)
-- Name: user_role user_role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_pkey PRIMARY KEY (user_role_id);


--
-- TOC entry 4940 (class 2606 OID 20350)
-- Name: user_session user_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT user_session_pkey PRIMARY KEY (user_session_id);


--
-- TOC entry 4942 (class 2606 OID 20361)
-- Name: user_shift_assignment user_shift_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_shift_assignment
    ADD CONSTRAINT user_shift_assignment_pkey PRIMARY KEY (user_shift_assignment_id);


--
-- TOC entry 4944 (class 2606 OID 20372)
-- Name: user_tag user_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tag
    ADD CONSTRAINT user_tag_pkey PRIMARY KEY (user_tag_id);


--
-- TOC entry 4946 (class 2606 OID 20384)
-- Name: variation_groups variation_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_groups
    ADD CONSTRAINT variation_groups_pkey PRIMARY KEY (variation_group_id);


--
-- TOC entry 4948 (class 2606 OID 20396)
-- Name: variation_options variation_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_options
    ADD CONSTRAINT variation_options_pkey PRIMARY KEY (variation_option_id);


--
-- TOC entry 4658 (class 1259 OID 18747)
-- Name: country_table_country_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX country_table_country_name_key ON public.country_table USING btree (country_name);


--
-- TOC entry 4717 (class 1259 OID 19107)
-- Name: feedback_categories_category_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX feedback_categories_category_name_key ON public.feedback_categories USING btree (category_name);


--
-- TOC entry 4741 (class 1259 OID 19234)
-- Name: feedback_types_type_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX feedback_types_type_name_key ON public.feedback_types USING btree (type_name);


--
-- TOC entry 4781 (class 1259 OID 21547)
-- Name: idx_availability_day_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_availability_day_time ON public.menu_item_availability_schedule USING btree (day_of_week, time_from, time_to) WHERE ((is_deleted = false) AND (is_available = true));


--
-- TOC entry 4782 (class 1259 OID 21539)
-- Name: idx_availability_meal_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_availability_meal_type ON public.menu_item_availability_schedule USING btree (meal_type_id) WHERE (is_deleted = false);


--
-- TOC entry 4783 (class 1259 OID 21546)
-- Name: idx_availability_menu_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_availability_menu_item ON public.menu_item_availability_schedule USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4786 (class 1259 OID 21549)
-- Name: idx_cuisine_mapping_cuisine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cuisine_mapping_cuisine ON public.menu_item_cuisine_mapping USING btree (cuisine_id) WHERE (is_deleted = false);


--
-- TOC entry 4787 (class 1259 OID 21548)
-- Name: idx_cuisine_mapping_menu_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cuisine_mapping_menu_item ON public.menu_item_cuisine_mapping USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4949 (class 1259 OID 21530)
-- Name: idx_mapping_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_category ON public.menu_item_category_mapping USING btree (menu_category_id) WHERE (is_deleted = false);


--
-- TOC entry 4950 (class 1259 OID 21529)
-- Name: idx_mapping_menu_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_menu_item ON public.menu_item_category_mapping USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4951 (class 1259 OID 21533)
-- Name: idx_mapping_primary; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_primary ON public.menu_item_category_mapping USING btree (menu_item_id, is_primary) WHERE ((is_deleted = false) AND (is_primary = true));


--
-- TOC entry 4952 (class 1259 OID 21532)
-- Name: idx_mapping_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_restaurant ON public.menu_item_category_mapping USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4953 (class 1259 OID 21531)
-- Name: idx_mapping_sub_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_sub_category ON public.menu_item_category_mapping USING btree (menu_sub_category_id) WHERE ((is_deleted = false) AND (menu_sub_category_id IS NOT NULL));


--
-- TOC entry 4760 (class 1259 OID 21551)
-- Name: idx_menu_categories_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_categories_restaurant ON public.menu_categories USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4761 (class 1259 OID 21550)
-- Name: idx_menu_categories_section; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_categories_section ON public.menu_categories USING btree (menu_section_id) WHERE (is_deleted = false);


--
-- TOC entry 4963 (class 1259 OID 21623)
-- Name: idx_menu_item_allergen_mapping_allergen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_allergen_mapping_allergen ON public.menu_item_allergen_mapping USING btree (allergen_id) WHERE (is_deleted = false);


--
-- TOC entry 4964 (class 1259 OID 21622)
-- Name: idx_menu_item_allergen_mapping_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_allergen_mapping_item ON public.menu_item_allergen_mapping USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4965 (class 1259 OID 21624)
-- Name: idx_menu_item_allergen_mapping_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_allergen_mapping_restaurant ON public.menu_item_allergen_mapping USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4970 (class 1259 OID 21656)
-- Name: idx_menu_item_dietary_mapping_dietary; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_dietary_mapping_dietary ON public.menu_item_dietary_mapping USING btree (dietary_type_id) WHERE (is_deleted = false);


--
-- TOC entry 4971 (class 1259 OID 21655)
-- Name: idx_menu_item_dietary_mapping_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_dietary_mapping_item ON public.menu_item_dietary_mapping USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4972 (class 1259 OID 21657)
-- Name: idx_menu_item_dietary_mapping_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_dietary_mapping_restaurant ON public.menu_item_dietary_mapping USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4764 (class 1259 OID 21543)
-- Name: idx_menu_item_favorite; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_favorite ON public.menu_item USING btree (menu_item_favorite) WHERE (is_deleted = false);


--
-- TOC entry 4765 (class 1259 OID 21541)
-- Name: idx_menu_item_in_stock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_in_stock ON public.menu_item USING btree (menu_item_in_stock) WHERE (is_deleted = false);


--
-- TOC entry 4958 (class 1259 OID 21589)
-- Name: idx_menu_item_ingredient_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_ingredient_item ON public.menu_item_ingredient USING btree (menu_item_id) WHERE (is_deleted = false);


--
-- TOC entry 4959 (class 1259 OID 21591)
-- Name: idx_menu_item_ingredient_primary; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_ingredient_primary ON public.menu_item_ingredient USING btree (is_primary) WHERE ((is_deleted = false) AND (is_primary = true));


--
-- TOC entry 4960 (class 1259 OID 21590)
-- Name: idx_menu_item_ingredient_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_ingredient_restaurant ON public.menu_item_ingredient USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4766 (class 1259 OID 21542)
-- Name: idx_menu_item_is_recommended; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_is_recommended ON public.menu_item USING btree (menu_item_is_recommended) WHERE (is_deleted = false);


--
-- TOC entry 4767 (class 1259 OID 21544)
-- Name: idx_menu_item_price; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_price ON public.menu_item USING btree (menu_item_price) WHERE (is_deleted = false);


--
-- TOC entry 4768 (class 1259 OID 21545)
-- Name: idx_menu_item_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_restaurant ON public.menu_item USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4769 (class 1259 OID 21663)
-- Name: idx_menu_item_restaurant_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_restaurant_active ON public.menu_item USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4770 (class 1259 OID 21540)
-- Name: idx_menu_item_spice_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_item_spice_level ON public.menu_item USING btree (menu_item_spice_level) WHERE (is_deleted = false);


--
-- TOC entry 4808 (class 1259 OID 21552)
-- Name: idx_menu_sub_categories_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_sub_categories_category ON public.menu_sub_categories USING btree (category_id) WHERE (is_deleted = false);


--
-- TOC entry 4809 (class 1259 OID 21553)
-- Name: idx_menu_sub_categories_restaurant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_menu_sub_categories_restaurant ON public.menu_sub_categories USING btree (restaurant_id) WHERE (is_deleted = false);


--
-- TOC entry 4724 (class 1259 OID 19134)
-- Name: platforms_platform_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX platforms_platform_name_key ON public.feedback_platforms USING btree (platform_name);


--
-- TOC entry 4727 (class 1259 OID 19146)
-- Name: priorities_priority_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX priorities_priority_name_key ON public.feedback_priorities USING btree (priority_name);


--
-- TOC entry 4736 (class 1259 OID 19207)
-- Name: statuses_status_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX statuses_status_name_key ON public.feedback_statuses USING btree (status_name);


--
-- TOC entry 4920 (class 1259 OID 20225)
-- Name: tags_feedback_tag_name_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX tags_feedback_tag_name_key ON public.tags_feedback USING btree (tag_name);


--
-- TOC entry 5349 (class 2618 OID 21661)
-- Name: menu_items_enriched_view _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.menu_items_enriched_view AS
 SELECT mi.menu_item_id,
    mi.restaurant_id,
    mi.menu_item_name,
    mi.menu_item_description,
    mi.menu_item_price,
    mi.menu_item_quantity,
    mi.menu_item_status,
    mi.menu_item_spice_level,
    mi.menu_item_in_stock,
    mi.menu_item_is_recommended,
    mi.menu_item_favorite,
    mi.menu_item_minimum_preparation_time,
    mi.menu_item_allow_variation,
    mi.menu_item_allow_addon,
    mi.menu_item_is_combo,
    mi.menu_item_is_combo_parent,
    mi.menu_item_rank,
    mi.menu_item_calories,
    mi.menu_item_is_seasonal,
    mi.menu_item_image_url,
    mi.menu_item_serving_unit,
    ms.menu_section_name AS section,
    array_agg(DISTINCT mc.menu_category_name) FILTER (WHERE (mc.menu_category_name IS NOT NULL)) AS categories,
    array_agg(DISTINCT msc.sub_category_name) FILTER (WHERE (msc.sub_category_name IS NOT NULL)) AS subcategories,
    array_agg(DISTINCT c.cuisine_name) FILTER (WHERE (c.cuisine_name IS NOT NULL)) AS cuisines,
    array_agg(DISTINCT mt.meal_type_name) FILTER (WHERE (mt.meal_type_name IS NOT NULL)) AS meal_timings,
    array_agg(DISTINCT mii.ingredient_name) FILTER (WHERE (mii.ingredient_name IS NOT NULL)) AS ingredients,
    array_agg(DISTINCT a.allergen_name) FILTER (WHERE (a.allergen_name IS NOT NULL)) AS allergens,
    array_agg(DISTINCT dt.dietary_type_name) FILTER (WHERE (dt.dietary_type_name IS NOT NULL)) AS dietary_types,
    mi.created_at,
    mi.updated_at,
    mi.is_deleted
   FROM (((((((((((((public.menu_item mi
     LEFT JOIN public.menu_item_category_mapping micm ON (((mi.menu_item_id = micm.menu_item_id) AND (micm.is_deleted = false))))
     LEFT JOIN public.menu_categories mc ON (((micm.menu_category_id = mc.menu_category_id) AND (mc.is_deleted = false))))
     LEFT JOIN public.menu_sub_categories msc ON (((micm.menu_sub_category_id = msc.menu_sub_category_id) AND (msc.is_deleted = false))))
     LEFT JOIN public.menu_sections ms ON (((mc.menu_section_id = ms.menu_section_id) AND (ms.is_deleted = false))))
     LEFT JOIN public.menu_item_cuisine_mapping mcm ON (((mi.menu_item_id = mcm.menu_item_id) AND (mcm.is_deleted = false))))
     LEFT JOIN public.cuisines c ON (((mcm.cuisine_id = c.cuisine_id) AND (c.is_deleted = false))))
     LEFT JOIN public.menu_item_availability_schedule mas ON (((mi.menu_item_id = mas.menu_item_id) AND (mas.is_deleted = false))))
     LEFT JOIN public.meal_type mt ON (((mas.meal_type_id = mt.meal_type_id) AND (mt.is_deleted = false))))
     LEFT JOIN public.menu_item_ingredient mii ON (((mi.menu_item_id = mii.menu_item_id) AND (mii.is_deleted = false))))
     LEFT JOIN public.menu_item_allergen_mapping mam ON (((mi.menu_item_id = mam.menu_item_id) AND (mam.is_deleted = false))))
     LEFT JOIN public.allergens a ON (((mam.allergen_id = a.allergen_id) AND (a.is_deleted = false))))
     LEFT JOIN public.menu_item_dietary_mapping mdm ON (((mi.menu_item_id = mdm.menu_item_id) AND (mdm.is_deleted = false))))
     LEFT JOIN public.dietary_types dt ON (((mdm.dietary_type_id = dt.dietary_type_id) AND (dt.is_deleted = false))))
  WHERE (mi.is_deleted = false)
  GROUP BY mi.menu_item_id, mi.restaurant_id, ms.menu_section_name, mi.created_at, mi.updated_at, mi.is_deleted;


--
-- TOC entry 4991 (class 2606 OID 20467)
-- Name: customer_activity_log customer_activity_log_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_activity_log
    ADD CONSTRAINT customer_activity_log_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4992 (class 2606 OID 20472)
-- Name: customer_address_table customer_address_table_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_address_table
    ADD CONSTRAINT customer_address_table_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4993 (class 2606 OID 20477)
-- Name: customer_allergens customer_allergens_allergen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_allergens
    ADD CONSTRAINT customer_allergens_allergen_id_fkey FOREIGN KEY (allergen_id) REFERENCES public.allergens(allergen_id);


--
-- TOC entry 4997 (class 2606 OID 20497)
-- Name: customer_contact_table customer_contact_table_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_contact_table
    ADD CONSTRAINT customer_contact_table_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4998 (class 2606 OID 20502)
-- Name: customer_devices customer_devices_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_devices
    ADD CONSTRAINT customer_devices_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5001 (class 2606 OID 20517)
-- Name: customer_favorite_items customer_favorite_items_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_favorite_items
    ADD CONSTRAINT customer_favorite_items_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5010 (class 2606 OID 20562)
-- Name: department department_department_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_department_manager_id_fkey FOREIGN KEY (department_manager_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5011 (class 2606 OID 20567)
-- Name: department department_parent_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_parent_department_id_fkey FOREIGN KEY (parent_department_id) REFERENCES public.department(department_id);


--
-- TOC entry 5025 (class 2606 OID 20637)
-- Name: feedback_categories feedback_categories_parent_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_categories
    ADD CONSTRAINT feedback_categories_parent_category_id_fkey FOREIGN KEY (parent_category_id) REFERENCES public.feedback_categories(category_id);


--
-- TOC entry 5027 (class 2606 OID 20647)
-- Name: feedback_priority_history feedback_priority_history_new_priority_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_priority_history
    ADD CONSTRAINT feedback_priority_history_new_priority_id_fkey FOREIGN KEY (new_priority_id) REFERENCES public.feedback_priorities(priority_id);


--
-- TOC entry 5028 (class 2606 OID 20652)
-- Name: feedback_priority_history feedback_priority_history_old_priority_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_priority_history
    ADD CONSTRAINT feedback_priority_history_old_priority_id_fkey FOREIGN KEY (old_priority_id) REFERENCES public.feedback_priorities(priority_id);


--
-- TOC entry 5031 (class 2606 OID 20667)
-- Name: feedback_status_history feedback_status_history_new_status_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_status_history
    ADD CONSTRAINT feedback_status_history_new_status_id_fkey FOREIGN KEY (new_status_id) REFERENCES public.feedback_statuses(status_id);


--
-- TOC entry 5032 (class 2606 OID 20672)
-- Name: feedback_status_history feedback_status_history_old_status_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_status_history
    ADD CONSTRAINT feedback_status_history_old_status_id_fkey FOREIGN KEY (old_status_id) REFERENCES public.feedback_statuses(status_id);


--
-- TOC entry 4977 (class 2606 OID 20397)
-- Name: account_lock fk_account_lock_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lock
    ADD CONSTRAINT fk_account_lock_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5058 (class 2606 OID 21534)
-- Name: menu_item_availability_schedule fk_availability_meal_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_availability_schedule
    ADD CONSTRAINT fk_availability_meal_type FOREIGN KEY (meal_type_id) REFERENCES public.meal_type(meal_type_id) ON DELETE SET NULL;


--
-- TOC entry 4978 (class 2606 OID 20402)
-- Name: branch_contact_table fk_branch_contact_table_branch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_contact_table
    ADD CONSTRAINT fk_branch_contact_table_branch_id FOREIGN KEY (branch_id) REFERENCES public.branch_info_table(branch_id);


--
-- TOC entry 4979 (class 2606 OID 20407)
-- Name: branch_info_table fk_branch_info_table_chain_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_info_table
    ADD CONSTRAINT fk_branch_info_table_chain_id FOREIGN KEY (chain_id) REFERENCES public.chain_info_table(chain_id);


--
-- TOC entry 4980 (class 2606 OID 20412)
-- Name: branch_location_table fk_branch_location_table_branch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_location_table
    ADD CONSTRAINT fk_branch_location_table_branch_id FOREIGN KEY (branch_id) REFERENCES public.branch_info_table(branch_id);


--
-- TOC entry 4981 (class 2606 OID 20417)
-- Name: branch_location_table fk_branch_location_table_pincode_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_location_table
    ADD CONSTRAINT fk_branch_location_table_pincode_id FOREIGN KEY (pincode_id) REFERENCES public.pincode_table(pincode_id);


--
-- TOC entry 4982 (class 2606 OID 20422)
-- Name: branch_timing_policy fk_branch_timing_policy_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch_timing_policy
    ADD CONSTRAINT fk_branch_timing_policy_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 4983 (class 2606 OID 20427)
-- Name: chain_contact_table fk_chain_contact_table_chain_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_contact_table
    ADD CONSTRAINT fk_chain_contact_table_chain_id FOREIGN KEY (chain_id) REFERENCES public.chain_info_table(chain_id);


--
-- TOC entry 4984 (class 2606 OID 20432)
-- Name: chain_location_table fk_chain_location_table_chain_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_location_table
    ADD CONSTRAINT fk_chain_location_table_chain_id FOREIGN KEY (chain_id) REFERENCES public.chain_info_table(chain_id);


--
-- TOC entry 4985 (class 2606 OID 20437)
-- Name: chain_location_table fk_chain_location_table_pincode_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_location_table
    ADD CONSTRAINT fk_chain_location_table_pincode_id FOREIGN KEY (pincode_id) REFERENCES public.pincode_table(pincode_id);


--
-- TOC entry 4986 (class 2606 OID 20442)
-- Name: city_table fk_city_table_state_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.city_table
    ADD CONSTRAINT fk_city_table_state_id FOREIGN KEY (state_id) REFERENCES public.state_table(state_id);


--
-- TOC entry 4987 (class 2606 OID 20447)
-- Name: combo_item fk_combo_item_combo_item_component_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item
    ADD CONSTRAINT fk_combo_item_combo_item_component_id FOREIGN KEY (combo_item_component_id) REFERENCES public.combo_item_components(combo_item_component_id);


--
-- TOC entry 4989 (class 2606 OID 20457)
-- Name: combo_item_components fk_combo_item_components_combo_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item_components
    ADD CONSTRAINT fk_combo_item_components_combo_item_id FOREIGN KEY (combo_item_id) REFERENCES public.combo_item(combo_item_id);


--
-- TOC entry 4990 (class 2606 OID 20462)
-- Name: combo_item_components fk_combo_item_components_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item_components
    ADD CONSTRAINT fk_combo_item_components_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 4988 (class 2606 OID 20452)
-- Name: combo_item fk_combo_item_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.combo_item
    ADD CONSTRAINT fk_combo_item_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 4994 (class 2606 OID 20482)
-- Name: customer_allergens fk_customer_allergens_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_allergens
    ADD CONSTRAINT fk_customer_allergens_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4995 (class 2606 OID 20487)
-- Name: customer_authentication fk_customer_authentication_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_authentication
    ADD CONSTRAINT fk_customer_authentication_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4996 (class 2606 OID 20492)
-- Name: customer_consent fk_customer_consent_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_consent
    ADD CONSTRAINT fk_customer_consent_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 4999 (class 2606 OID 20507)
-- Name: customer_dietary_restrictions fk_customer_dietary_restrictions_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_dietary_restrictions
    ADD CONSTRAINT fk_customer_dietary_restrictions_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5000 (class 2606 OID 20512)
-- Name: customer_dietary_restrictions fk_customer_dietary_restrictions_dietary_restriction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_dietary_restrictions
    ADD CONSTRAINT fk_customer_dietary_restrictions_dietary_restriction_id FOREIGN KEY (dietary_restriction_id) REFERENCES public.dietary_restrictions(dietary_restriction_id);


--
-- TOC entry 5002 (class 2606 OID 20522)
-- Name: customer_favorite_items fk_customer_favorite_items_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_favorite_items
    ADD CONSTRAINT fk_customer_favorite_items_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5003 (class 2606 OID 20527)
-- Name: customer_preferences fk_customer_preferences_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_preferences
    ADD CONSTRAINT fk_customer_preferences_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5004 (class 2606 OID 20532)
-- Name: customer_profile_table fk_customer_profile_table_customer_gender_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_profile_table
    ADD CONSTRAINT fk_customer_profile_table_customer_gender_id FOREIGN KEY (customer_gender_id) REFERENCES public.customer_gender(customer_gender_id);


--
-- TOC entry 5005 (class 2606 OID 20537)
-- Name: customer_profile_table fk_customer_profile_table_language_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_profile_table
    ADD CONSTRAINT fk_customer_profile_table_language_id FOREIGN KEY (language_id) REFERENCES public.languages(language_id);


--
-- TOC entry 5006 (class 2606 OID 20542)
-- Name: customer_search_queries fk_customer_search_queries_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_search_queries
    ADD CONSTRAINT fk_customer_search_queries_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5007 (class 2606 OID 20547)
-- Name: customer_sessions fk_customer_sessions_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT fk_customer_sessions_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5008 (class 2606 OID 20552)
-- Name: customer_tag_mapping fk_customer_tag_mapping_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tag_mapping
    ADD CONSTRAINT fk_customer_tag_mapping_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5009 (class 2606 OID 20557)
-- Name: customer_tag_mapping fk_customer_tag_mapping_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tag_mapping
    ADD CONSTRAINT fk_customer_tag_mapping_tag_id FOREIGN KEY (tag_id) REFERENCES public.customer_tags(tag_id);


--
-- TOC entry 5012 (class 2606 OID 20572)
-- Name: department fk_department_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT fk_department_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5013 (class 2606 OID 20577)
-- Name: discount fk_discount_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discount
    ADD CONSTRAINT fk_discount_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5014 (class 2606 OID 20582)
-- Name: discount_schedule fk_discount_schedule_discount_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discount_schedule
    ADD CONSTRAINT fk_discount_schedule_discount_id FOREIGN KEY (discount_id) REFERENCES public.discount(discount_id);


--
-- TOC entry 5015 (class 2606 OID 20587)
-- Name: email_verification fk_email_verification_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_verification
    ADD CONSTRAINT fk_email_verification_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5016 (class 2606 OID 20592)
-- Name: entity_slot_config fk_entity_slot_config_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_slot_config
    ADD CONSTRAINT fk_entity_slot_config_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5024 (class 2606 OID 20632)
-- Name: feedback_attachments fk_feedback_attachments_feedback_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_attachments
    ADD CONSTRAINT fk_feedback_attachments_feedback_id FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id);


--
-- TOC entry 5017 (class 2606 OID 20597)
-- Name: feedback fk_feedback_category_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_category_id FOREIGN KEY (category_id) REFERENCES public.feedback_categories(category_id);


--
-- TOC entry 5018 (class 2606 OID 20602)
-- Name: feedback fk_feedback_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5019 (class 2606 OID 20607)
-- Name: feedback fk_feedback_feedback_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_feedback_type_id FOREIGN KEY (feedback_type_id) REFERENCES public.feedback_types(type_id);


--
-- TOC entry 5026 (class 2606 OID 20642)
-- Name: feedback_notifications fk_feedback_notifications_feedback_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_notifications
    ADD CONSTRAINT fk_feedback_notifications_feedback_id FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id);


--
-- TOC entry 5020 (class 2606 OID 20612)
-- Name: feedback fk_feedback_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5021 (class 2606 OID 20617)
-- Name: feedback fk_feedback_platform_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_platform_id FOREIGN KEY (platform_id) REFERENCES public.feedback_platforms(platform_id);


--
-- TOC entry 5029 (class 2606 OID 20657)
-- Name: feedback_priority_history fk_feedback_priority_history_feedback_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_priority_history
    ADD CONSTRAINT fk_feedback_priority_history_feedback_id FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id);


--
-- TOC entry 5022 (class 2606 OID 20622)
-- Name: feedback fk_feedback_priority_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_priority_id FOREIGN KEY (priority_id) REFERENCES public.feedback_priorities(priority_id);


--
-- TOC entry 5030 (class 2606 OID 20662)
-- Name: feedback_responses fk_feedback_responses_feedback_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_responses
    ADD CONSTRAINT fk_feedback_responses_feedback_id FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id);


--
-- TOC entry 5033 (class 2606 OID 20677)
-- Name: feedback_status_history fk_feedback_status_history_feedback_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_status_history
    ADD CONSTRAINT fk_feedback_status_history_feedback_id FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id);


--
-- TOC entry 5023 (class 2606 OID 20627)
-- Name: feedback fk_feedback_status_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT fk_feedback_status_id FOREIGN KEY (status_id) REFERENCES public.feedback_statuses(status_id);


--
-- TOC entry 5034 (class 2606 OID 20682)
-- Name: feedback_tags fk_feedback_tags_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_tags
    ADD CONSTRAINT fk_feedback_tags_tag_id FOREIGN KEY (tag_id) REFERENCES public.tags_feedback(tag_id);


--
-- TOC entry 5035 (class 2606 OID 20687)
-- Name: integration_config_table fk_integration_config_table_branch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_config_table
    ADD CONSTRAINT fk_integration_config_table_branch_id FOREIGN KEY (branch_id) REFERENCES public.branch_info_table(branch_id);


--
-- TOC entry 5036 (class 2606 OID 20692)
-- Name: integration_config_table fk_integration_config_table_chain_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_config_table
    ADD CONSTRAINT fk_integration_config_table_chain_id FOREIGN KEY (chain_id) REFERENCES public.chain_info_table(chain_id);


--
-- TOC entry 5037 (class 2606 OID 20697)
-- Name: integration_config_table fk_integration_config_table_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_config_table
    ADD CONSTRAINT fk_integration_config_table_provider_id FOREIGN KEY (provider_id) REFERENCES public.integration_provider_table(provider_id);


--
-- TOC entry 5038 (class 2606 OID 20702)
-- Name: integration_credentials_table fk_integration_credentials_table_integration_config_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_credentials_table
    ADD CONSTRAINT fk_integration_credentials_table_integration_config_id FOREIGN KEY (integration_config_id) REFERENCES public.integration_config_table(integration_config_id);


--
-- TOC entry 5039 (class 2606 OID 20707)
-- Name: integration_metadata_table fk_integration_metadata_table_integration_config_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_metadata_table
    ADD CONSTRAINT fk_integration_metadata_table_integration_config_id FOREIGN KEY (integration_config_id) REFERENCES public.integration_config_table(integration_config_id);


--
-- TOC entry 5040 (class 2606 OID 20712)
-- Name: login_attempt fk_login_attempt_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_attempt
    ADD CONSTRAINT fk_login_attempt_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5041 (class 2606 OID 20717)
-- Name: loyalty_transaction fk_loyalty_transaction_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.loyalty_transaction
    ADD CONSTRAINT fk_loyalty_transaction_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5042 (class 2606 OID 20722)
-- Name: loyalty_transaction fk_loyalty_transaction_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.loyalty_transaction
    ADD CONSTRAINT fk_loyalty_transaction_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5043 (class 2606 OID 20727)
-- Name: loyalty_transaction fk_loyalty_transaction_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.loyalty_transaction
    ADD CONSTRAINT fk_loyalty_transaction_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5190 (class 2606 OID 21519)
-- Name: menu_item_category_mapping fk_mapping_category; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT fk_mapping_category FOREIGN KEY (menu_category_id) REFERENCES public.menu_categories(menu_category_id) ON DELETE CASCADE;


--
-- TOC entry 5191 (class 2606 OID 21514)
-- Name: menu_item_category_mapping fk_mapping_menu_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT fk_mapping_menu_item FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id) ON DELETE CASCADE;


--
-- TOC entry 5192 (class 2606 OID 21509)
-- Name: menu_item_category_mapping fk_mapping_restaurant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT fk_mapping_restaurant FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id) ON DELETE CASCADE;


--
-- TOC entry 5193 (class 2606 OID 21524)
-- Name: menu_item_category_mapping fk_mapping_sub_category; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_category_mapping
    ADD CONSTRAINT fk_mapping_sub_category FOREIGN KEY (menu_sub_category_id) REFERENCES public.menu_sub_categories(menu_sub_category_id) ON DELETE CASCADE;


--
-- TOC entry 5044 (class 2606 OID 20732)
-- Name: meal_slot_timing fk_meal_slot_timing_meal_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meal_slot_timing
    ADD CONSTRAINT fk_meal_slot_timing_meal_type_id FOREIGN KEY (meal_type_id) REFERENCES public.meal_type(meal_type_id);


--
-- TOC entry 5045 (class 2606 OID 20737)
-- Name: meal_slot_timing fk_meal_slot_timing_slot_config_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meal_slot_timing
    ADD CONSTRAINT fk_meal_slot_timing_slot_config_id FOREIGN KEY (slot_config_id) REFERENCES public.entity_slot_config(slot_config_id);


--
-- TOC entry 5046 (class 2606 OID 20742)
-- Name: menu_categories fk_menu_categories_menu_section_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT fk_menu_categories_menu_section_id FOREIGN KEY (menu_section_id) REFERENCES public.menu_sections(menu_section_id);


--
-- TOC entry 5047 (class 2606 OID 20747)
-- Name: menu_categories fk_menu_categories_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT fk_menu_categories_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5051 (class 2606 OID 20767)
-- Name: menu_item_addon_group fk_menu_item_addon_group_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_group
    ADD CONSTRAINT fk_menu_item_addon_group_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5052 (class 2606 OID 20772)
-- Name: menu_item_addon_item fk_menu_item_addon_item_menu_item_addon_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_item
    ADD CONSTRAINT fk_menu_item_addon_item_menu_item_addon_group_id FOREIGN KEY (menu_item_addon_group_id) REFERENCES public.menu_item_addon_group(menu_item_addon_group_id);


--
-- TOC entry 5053 (class 2606 OID 20777)
-- Name: menu_item_addon_item fk_menu_item_addon_item_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_item
    ADD CONSTRAINT fk_menu_item_addon_item_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5054 (class 2606 OID 20782)
-- Name: menu_item_addon_mapping fk_menu_item_addon_mapping_menu_item_addon_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_mapping
    ADD CONSTRAINT fk_menu_item_addon_mapping_menu_item_addon_group_id FOREIGN KEY (menu_item_addon_group_id) REFERENCES public.menu_item_addon_group(menu_item_addon_group_id);


--
-- TOC entry 5055 (class 2606 OID 20787)
-- Name: menu_item_addon_mapping fk_menu_item_addon_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_mapping
    ADD CONSTRAINT fk_menu_item_addon_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5056 (class 2606 OID 20792)
-- Name: menu_item_addon_mapping fk_menu_item_addon_mapping_menu_item_variation_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_mapping
    ADD CONSTRAINT fk_menu_item_addon_mapping_menu_item_variation_id FOREIGN KEY (menu_item_variation_id) REFERENCES public.menu_item_variation(menu_item_variation_id);


--
-- TOC entry 5057 (class 2606 OID 20797)
-- Name: menu_item_addon_mapping fk_menu_item_addon_mapping_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_addon_mapping
    ADD CONSTRAINT fk_menu_item_addon_mapping_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5196 (class 2606 OID 21612)
-- Name: menu_item_allergen_mapping fk_menu_item_allergen_mapping_allergen; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_allergen_mapping
    ADD CONSTRAINT fk_menu_item_allergen_mapping_allergen FOREIGN KEY (allergen_id) REFERENCES public.allergens(allergen_id) ON DELETE CASCADE;


--
-- TOC entry 5197 (class 2606 OID 21607)
-- Name: menu_item_allergen_mapping fk_menu_item_allergen_mapping_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_allergen_mapping
    ADD CONSTRAINT fk_menu_item_allergen_mapping_item FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id) ON DELETE CASCADE;


--
-- TOC entry 5198 (class 2606 OID 21617)
-- Name: menu_item_allergen_mapping fk_menu_item_allergen_mapping_restaurant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_allergen_mapping
    ADD CONSTRAINT fk_menu_item_allergen_mapping_restaurant FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id) ON DELETE CASCADE;


--
-- TOC entry 5059 (class 2606 OID 20802)
-- Name: menu_item_availability_schedule fk_menu_item_availability_schedule_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_availability_schedule
    ADD CONSTRAINT fk_menu_item_availability_schedule_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5060 (class 2606 OID 20807)
-- Name: menu_item_cuisine_mapping fk_menu_item_cuisine_mapping_cuisine_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_cuisine_mapping
    ADD CONSTRAINT fk_menu_item_cuisine_mapping_cuisine_id FOREIGN KEY (cuisine_id) REFERENCES public.cuisines(cuisine_id);


--
-- TOC entry 5061 (class 2606 OID 20812)
-- Name: menu_item_cuisine_mapping fk_menu_item_cuisine_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_cuisine_mapping
    ADD CONSTRAINT fk_menu_item_cuisine_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5199 (class 2606 OID 21645)
-- Name: menu_item_dietary_mapping fk_menu_item_dietary_mapping_dietary; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_dietary_mapping
    ADD CONSTRAINT fk_menu_item_dietary_mapping_dietary FOREIGN KEY (dietary_type_id) REFERENCES public.dietary_types(dietary_type_id) ON DELETE CASCADE;


--
-- TOC entry 5200 (class 2606 OID 21640)
-- Name: menu_item_dietary_mapping fk_menu_item_dietary_mapping_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_dietary_mapping
    ADD CONSTRAINT fk_menu_item_dietary_mapping_item FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id) ON DELETE CASCADE;


--
-- TOC entry 5201 (class 2606 OID 21650)
-- Name: menu_item_dietary_mapping fk_menu_item_dietary_mapping_restaurant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_dietary_mapping
    ADD CONSTRAINT fk_menu_item_dietary_mapping_restaurant FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id) ON DELETE CASCADE;


--
-- TOC entry 5062 (class 2606 OID 20817)
-- Name: menu_item_discount_mapping fk_menu_item_discount_mapping_discount_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_discount_mapping
    ADD CONSTRAINT fk_menu_item_discount_mapping_discount_id FOREIGN KEY (discount_id) REFERENCES public.discount(discount_id);


--
-- TOC entry 5063 (class 2606 OID 20822)
-- Name: menu_item_discount_mapping fk_menu_item_discount_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_discount_mapping
    ADD CONSTRAINT fk_menu_item_discount_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5064 (class 2606 OID 20827)
-- Name: menu_item_discount_mapping fk_menu_item_discount_mapping_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_discount_mapping
    ADD CONSTRAINT fk_menu_item_discount_mapping_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5194 (class 2606 OID 21579)
-- Name: menu_item_ingredient fk_menu_item_ingredient_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ingredient
    ADD CONSTRAINT fk_menu_item_ingredient_item FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id) ON DELETE CASCADE;


--
-- TOC entry 5195 (class 2606 OID 21584)
-- Name: menu_item_ingredient fk_menu_item_ingredient_restaurant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ingredient
    ADD CONSTRAINT fk_menu_item_ingredient_restaurant FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id) ON DELETE CASCADE;


--
-- TOC entry 5048 (class 2606 OID 20752)
-- Name: menu_item fk_menu_item_menu_item_attribute_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item
    ADD CONSTRAINT fk_menu_item_menu_item_attribute_id FOREIGN KEY (menu_item_attribute_id) REFERENCES public.menu_item_attribute(menu_item_attribute_id);


--
-- TOC entry 5049 (class 2606 OID 20757)
-- Name: menu_item fk_menu_item_menu_sub_category_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item
    ADD CONSTRAINT fk_menu_item_menu_sub_category_id FOREIGN KEY (menu_sub_category_id) REFERENCES public.menu_sub_categories(menu_sub_category_id);


--
-- TOC entry 5065 (class 2606 OID 20832)
-- Name: menu_item_option fk_menu_item_option_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_option
    ADD CONSTRAINT fk_menu_item_option_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5066 (class 2606 OID 20837)
-- Name: menu_item_ordertype_mapping fk_menu_item_ordertype_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ordertype_mapping
    ADD CONSTRAINT fk_menu_item_ordertype_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5067 (class 2606 OID 20842)
-- Name: menu_item_ordertype_mapping fk_menu_item_ordertype_mapping_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ordertype_mapping
    ADD CONSTRAINT fk_menu_item_ordertype_mapping_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5050 (class 2606 OID 20762)
-- Name: menu_item fk_menu_item_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item
    ADD CONSTRAINT fk_menu_item_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5069 (class 2606 OID 20852)
-- Name: menu_item_tag_mapping fk_menu_item_tag_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tag_mapping
    ADD CONSTRAINT fk_menu_item_tag_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5070 (class 2606 OID 20857)
-- Name: menu_item_tag_mapping fk_menu_item_tag_mapping_menu_item_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tag_mapping
    ADD CONSTRAINT fk_menu_item_tag_mapping_menu_item_tag_id FOREIGN KEY (menu_item_tag_id) REFERENCES public.menu_item_tag(menu_item_tag_id);


--
-- TOC entry 5071 (class 2606 OID 20862)
-- Name: menu_item_tax_mapping fk_menu_item_tax_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tax_mapping
    ADD CONSTRAINT fk_menu_item_tax_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5072 (class 2606 OID 20867)
-- Name: menu_item_tax_mapping fk_menu_item_tax_mapping_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tax_mapping
    ADD CONSTRAINT fk_menu_item_tax_mapping_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5073 (class 2606 OID 20872)
-- Name: menu_item_tax_mapping fk_menu_item_tax_mapping_tax_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_tax_mapping
    ADD CONSTRAINT fk_menu_item_tax_mapping_tax_id FOREIGN KEY (tax_id) REFERENCES public.taxes(tax_id);


--
-- TOC entry 5077 (class 2606 OID 20892)
-- Name: menu_item_variation_mapping fk_menu_item_variation_mapping_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation_mapping
    ADD CONSTRAINT fk_menu_item_variation_mapping_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5074 (class 2606 OID 20877)
-- Name: menu_item_variation fk_menu_item_variation_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation
    ADD CONSTRAINT fk_menu_item_variation_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5075 (class 2606 OID 20882)
-- Name: menu_item_variation fk_menu_item_variation_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation
    ADD CONSTRAINT fk_menu_item_variation_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5076 (class 2606 OID 20887)
-- Name: menu_item_variation fk_menu_item_variation_variation_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation
    ADD CONSTRAINT fk_menu_item_variation_variation_group_id FOREIGN KEY (variation_group_id) REFERENCES public.variation_groups(variation_group_id);


--
-- TOC entry 5079 (class 2606 OID 20902)
-- Name: menu_sections fk_menu_sections_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sections
    ADD CONSTRAINT fk_menu_sections_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5080 (class 2606 OID 21554)
-- Name: menu_sub_categories fk_menu_sub_categories_category_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sub_categories
    ADD CONSTRAINT fk_menu_sub_categories_category_id FOREIGN KEY (category_id) REFERENCES public.menu_categories(menu_category_id);


--
-- TOC entry 5081 (class 2606 OID 20912)
-- Name: menu_sub_categories fk_menu_sub_categories_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sub_categories
    ADD CONSTRAINT fk_menu_sub_categories_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5082 (class 2606 OID 20917)
-- Name: menu_sync_log fk_menu_sync_log_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_sync_log
    ADD CONSTRAINT fk_menu_sync_log_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5083 (class 2606 OID 20922)
-- Name: menu_version_history fk_menu_version_history_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_version_history
    ADD CONSTRAINT fk_menu_version_history_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5084 (class 2606 OID 20927)
-- Name: order_audit fk_order_audit_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audit
    ADD CONSTRAINT fk_order_audit_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5085 (class 2606 OID 20932)
-- Name: order_audit fk_order_audit_session_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audit
    ADD CONSTRAINT fk_order_audit_session_id FOREIGN KEY (session_id) REFERENCES public.customer_sessions(session_id);


--
-- TOC entry 5086 (class 2606 OID 20937)
-- Name: order_charges fk_order_charges_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_charges
    ADD CONSTRAINT fk_order_charges_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5087 (class 2606 OID 20942)
-- Name: order_charges fk_order_charges_order_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_charges
    ADD CONSTRAINT fk_order_charges_order_item_id FOREIGN KEY (order_item_id) REFERENCES public.order_item(order_item_id);


--
-- TOC entry 5088 (class 2606 OID 20947)
-- Name: order_customer_details fk_order_customer_details_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_customer_details
    ADD CONSTRAINT fk_order_customer_details_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5089 (class 2606 OID 20952)
-- Name: order_customer_details fk_order_customer_details_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_customer_details
    ADD CONSTRAINT fk_order_customer_details_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5090 (class 2606 OID 20957)
-- Name: order_customer_details fk_order_customer_details_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_customer_details
    ADD CONSTRAINT fk_order_customer_details_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5091 (class 2606 OID 20962)
-- Name: order_delivery_info fk_order_delivery_info_delivery_address_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_delivery_info
    ADD CONSTRAINT fk_order_delivery_info_delivery_address_id FOREIGN KEY (delivery_address_id) REFERENCES public.customer_address_table(customer_address_id);


--
-- TOC entry 5092 (class 2606 OID 20967)
-- Name: order_delivery_info fk_order_delivery_info_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_delivery_info
    ADD CONSTRAINT fk_order_delivery_info_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5093 (class 2606 OID 20972)
-- Name: order_dining_info fk_order_dining_info_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_dining_info
    ADD CONSTRAINT fk_order_dining_info_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5094 (class 2606 OID 20977)
-- Name: order_dining_info fk_order_dining_info_table_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_dining_info
    ADD CONSTRAINT fk_order_dining_info_table_id FOREIGN KEY (table_id) REFERENCES public.table_info(table_id);


--
-- TOC entry 5095 (class 2606 OID 20982)
-- Name: order_discount fk_order_discount_order_discount_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_discount
    ADD CONSTRAINT fk_order_discount_order_discount_type_id FOREIGN KEY (order_discount_type_id) REFERENCES public.discount_type(discount_type_id);


--
-- TOC entry 5096 (class 2606 OID 20987)
-- Name: order_discount fk_order_discount_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_discount
    ADD CONSTRAINT fk_order_discount_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5097 (class 2606 OID 20992)
-- Name: order_discount fk_order_discount_order_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_discount
    ADD CONSTRAINT fk_order_discount_order_item_id FOREIGN KEY (order_item_id) REFERENCES public.order_item(order_item_id);


--
-- TOC entry 5098 (class 2606 OID 20997)
-- Name: order_instruction fk_order_instruction_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_instruction
    ADD CONSTRAINT fk_order_instruction_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5099 (class 2606 OID 21002)
-- Name: order_integration_sync fk_order_integration_sync_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_integration_sync
    ADD CONSTRAINT fk_order_integration_sync_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5100 (class 2606 OID 21007)
-- Name: order_invoice fk_order_invoice_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_invoice
    ADD CONSTRAINT fk_order_invoice_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5101 (class 2606 OID 21012)
-- Name: order_item fk_order_item_category_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT fk_order_item_category_id FOREIGN KEY (category_id) REFERENCES public.feedback_categories(category_id);


--
-- TOC entry 5102 (class 2606 OID 21017)
-- Name: order_item fk_order_item_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT fk_order_item_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5103 (class 2606 OID 21022)
-- Name: order_item fk_order_item_menu_item_variation_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT fk_order_item_menu_item_variation_id FOREIGN KEY (menu_item_variation_id) REFERENCES public.menu_item_variation(menu_item_variation_id);


--
-- TOC entry 5104 (class 2606 OID 21027)
-- Name: order_item fk_order_item_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT fk_order_item_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5105 (class 2606 OID 21032)
-- Name: order_kitchen_detail fk_order_kitchen_detail_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_kitchen_detail
    ADD CONSTRAINT fk_order_kitchen_detail_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5106 (class 2606 OID 21037)
-- Name: order_kitchen_detail fk_order_kitchen_detail_order_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_kitchen_detail
    ADD CONSTRAINT fk_order_kitchen_detail_order_item_id FOREIGN KEY (order_item_id) REFERENCES public.order_item(order_item_id);


--
-- TOC entry 5107 (class 2606 OID 21042)
-- Name: order_note fk_order_note_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_note
    ADD CONSTRAINT fk_order_note_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5108 (class 2606 OID 21047)
-- Name: order_payment fk_order_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT fk_order_payment_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5109 (class 2606 OID 21052)
-- Name: order_payment fk_order_payment_order_payment_method_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT fk_order_payment_order_payment_method_id FOREIGN KEY (order_payment_method_id) REFERENCES public.order_payment_method(order_payment_method_id);


--
-- TOC entry 5110 (class 2606 OID 21057)
-- Name: order_payment fk_order_payment_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT fk_order_payment_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5111 (class 2606 OID 21062)
-- Name: order_payment fk_order_payment_tax_calculation_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT fk_order_payment_tax_calculation_type_id FOREIGN KEY (tax_calculation_type_id) REFERENCES public.tax_calculation_type(tax_calculation_type_id);


--
-- TOC entry 5113 (class 2606 OID 21072)
-- Name: order_priority fk_order_priority_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_priority
    ADD CONSTRAINT fk_order_priority_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5114 (class 2606 OID 21077)
-- Name: order_scheduling fk_order_scheduling_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_scheduling
    ADD CONSTRAINT fk_order_scheduling_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5115 (class 2606 OID 21082)
-- Name: order_security_detail fk_order_security_detail_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_security_detail
    ADD CONSTRAINT fk_order_security_detail_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5116 (class 2606 OID 21087)
-- Name: order_status_history fk_order_status_history_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT fk_order_status_history_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5117 (class 2606 OID 21092)
-- Name: order_status_history fk_order_status_history_order_status_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT fk_order_status_history_order_status_type_id FOREIGN KEY (order_status_type_id) REFERENCES public.order_status_type(order_status_type_id);


--
-- TOC entry 5118 (class 2606 OID 21097)
-- Name: order_tax_line fk_order_tax_line_order_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_tax_line
    ADD CONSTRAINT fk_order_tax_line_order_item_id FOREIGN KEY (order_item_id) REFERENCES public.order_item(order_item_id);


--
-- TOC entry 5120 (class 2606 OID 21107)
-- Name: order_total fk_order_total_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_total
    ADD CONSTRAINT fk_order_total_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5121 (class 2606 OID 21112)
-- Name: orders fk_orders_order_source_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_order_source_type_id FOREIGN KEY (order_source_type_id) REFERENCES public.order_source_type(order_source_type_id);


--
-- TOC entry 5122 (class 2606 OID 21117)
-- Name: orders fk_orders_order_status_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_order_status_type_id FOREIGN KEY (order_status_type_id) REFERENCES public.order_status_type(order_status_type_id);


--
-- TOC entry 5123 (class 2606 OID 21122)
-- Name: orders fk_orders_order_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_order_type_id FOREIGN KEY (order_type_id) REFERENCES public.order_type_table(order_type_id);


--
-- TOC entry 5124 (class 2606 OID 21127)
-- Name: orders fk_orders_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5125 (class 2606 OID 21132)
-- Name: orders fk_orders_table_booking_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_table_booking_id FOREIGN KEY (table_booking_id) REFERENCES public.table_booking_info(table_booking_id);


--
-- TOC entry 5126 (class 2606 OID 21137)
-- Name: password_reset fk_password_reset_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset
    ADD CONSTRAINT fk_password_reset_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5127 (class 2606 OID 21142)
-- Name: payment_audit_log fk_payment_audit_log_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_audit_log
    ADD CONSTRAINT fk_payment_audit_log_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5128 (class 2606 OID 21147)
-- Name: payment_audit_log fk_payment_audit_log_payment_refund_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_audit_log
    ADD CONSTRAINT fk_payment_audit_log_payment_refund_id FOREIGN KEY (payment_refund_id) REFERENCES public.payment_refund(payment_refund_id);


--
-- TOC entry 5129 (class 2606 OID 21152)
-- Name: payment_audit_log fk_payment_audit_log_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_audit_log
    ADD CONSTRAINT fk_payment_audit_log_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5130 (class 2606 OID 21157)
-- Name: payment_external_mapping fk_payment_external_mapping_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_external_mapping
    ADD CONSTRAINT fk_payment_external_mapping_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5131 (class 2606 OID 21162)
-- Name: payment_external_mapping fk_payment_external_mapping_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_external_mapping
    ADD CONSTRAINT fk_payment_external_mapping_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5132 (class 2606 OID 21167)
-- Name: payment_order fk_payment_order_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_order
    ADD CONSTRAINT fk_payment_order_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5133 (class 2606 OID 21172)
-- Name: payment_order fk_payment_order_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_order
    ADD CONSTRAINT fk_payment_order_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5134 (class 2606 OID 21177)
-- Name: payment_order fk_payment_order_payment_gateway_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_order
    ADD CONSTRAINT fk_payment_order_payment_gateway_id FOREIGN KEY (payment_gateway_id) REFERENCES public.payment_gateway(payment_gateway_id);


--
-- TOC entry 5135 (class 2606 OID 21182)
-- Name: payment_order fk_payment_order_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_order
    ADD CONSTRAINT fk_payment_order_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5136 (class 2606 OID 21187)
-- Name: payment_refund fk_payment_refund_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5137 (class 2606 OID 21192)
-- Name: payment_refund fk_payment_refund_order_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_order_item_id FOREIGN KEY (order_item_id) REFERENCES public.order_item(order_item_id);


--
-- TOC entry 5138 (class 2606 OID 21197)
-- Name: payment_refund fk_payment_refund_payment_gateway_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_payment_gateway_id FOREIGN KEY (payment_gateway_id) REFERENCES public.payment_gateway(payment_gateway_id);


--
-- TOC entry 5139 (class 2606 OID 21202)
-- Name: payment_refund fk_payment_refund_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5140 (class 2606 OID 21207)
-- Name: payment_refund fk_payment_refund_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5141 (class 2606 OID 21212)
-- Name: payment_refund fk_payment_refund_refund_reason_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_refund_reason_type_id FOREIGN KEY (refund_reason_type_id) REFERENCES public.refund_reason_type(refund_reason_type_id);


--
-- TOC entry 5142 (class 2606 OID 21217)
-- Name: payment_refund fk_payment_refund_refund_status_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund
    ADD CONSTRAINT fk_payment_refund_refund_status_type_id FOREIGN KEY (refund_status_type_id) REFERENCES public.refund_status_type(refund_status_type_id);


--
-- TOC entry 5143 (class 2606 OID 21222)
-- Name: payment_retry_attempt fk_payment_retry_attempt_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_retry_attempt
    ADD CONSTRAINT fk_payment_retry_attempt_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5144 (class 2606 OID 21227)
-- Name: payment_retry_attempt fk_payment_retry_attempt_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_retry_attempt
    ADD CONSTRAINT fk_payment_retry_attempt_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5145 (class 2606 OID 21232)
-- Name: payment_split fk_payment_split_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_split
    ADD CONSTRAINT fk_payment_split_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5146 (class 2606 OID 21237)
-- Name: payment_split fk_payment_split_payment_transaction_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_split
    ADD CONSTRAINT fk_payment_split_payment_transaction_id FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5147 (class 2606 OID 21242)
-- Name: payment_transaction fk_payment_transaction_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5148 (class 2606 OID 21247)
-- Name: payment_transaction fk_payment_transaction_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_order_id FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- TOC entry 5149 (class 2606 OID 21252)
-- Name: payment_transaction fk_payment_transaction_order_payment_method_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_order_payment_method_id FOREIGN KEY (order_payment_method_id) REFERENCES public.order_payment_method(order_payment_method_id);


--
-- TOC entry 5150 (class 2606 OID 21257)
-- Name: payment_transaction fk_payment_transaction_payment_gateway_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_payment_gateway_id FOREIGN KEY (payment_gateway_id) REFERENCES public.payment_gateway(payment_gateway_id);


--
-- TOC entry 5151 (class 2606 OID 21262)
-- Name: payment_transaction fk_payment_transaction_payment_order_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_payment_order_id FOREIGN KEY (payment_order_id) REFERENCES public.payment_order(payment_order_id);


--
-- TOC entry 5152 (class 2606 OID 21267)
-- Name: payment_transaction fk_payment_transaction_payment_status_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_payment_status_type_id FOREIGN KEY (payment_status_type_id) REFERENCES public.payment_status_type(payment_status_type_id);


--
-- TOC entry 5153 (class 2606 OID 21272)
-- Name: payment_transaction fk_payment_transaction_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transaction
    ADD CONSTRAINT fk_payment_transaction_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5154 (class 2606 OID 21277)
-- Name: payment_webhook_log fk_payment_webhook_log_payment_gateway_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_webhook_log
    ADD CONSTRAINT fk_payment_webhook_log_payment_gateway_id FOREIGN KEY (payment_gateway_id) REFERENCES public.payment_gateway(payment_gateway_id);


--
-- TOC entry 5155 (class 2606 OID 21282)
-- Name: pincode_table fk_pincode_table_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pincode_table
    ADD CONSTRAINT fk_pincode_table_city_id FOREIGN KEY (city_id) REFERENCES public.city_table(city_id);


--
-- TOC entry 5156 (class 2606 OID 21287)
-- Name: restaurant_faq fk_restaurant_faq_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_faq
    ADD CONSTRAINT fk_restaurant_faq_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5157 (class 2606 OID 21292)
-- Name: restaurant_policy fk_restaurant_policy_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_policy
    ADD CONSTRAINT fk_restaurant_policy_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5158 (class 2606 OID 21297)
-- Name: restaurant_table fk_restaurant_table_branch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table
    ADD CONSTRAINT fk_restaurant_table_branch_id FOREIGN KEY (branch_id) REFERENCES public.branch_info_table(branch_id);


--
-- TOC entry 5159 (class 2606 OID 21302)
-- Name: restaurant_table fk_restaurant_table_chain_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table
    ADD CONSTRAINT fk_restaurant_table_chain_id FOREIGN KEY (chain_id) REFERENCES public.chain_info_table(chain_id);


--
-- TOC entry 5161 (class 2606 OID 21312)
-- Name: round_robin_pool_member fk_round_robin_pool_member_round_robin_pool_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.round_robin_pool_member
    ADD CONSTRAINT fk_round_robin_pool_member_round_robin_pool_id FOREIGN KEY (round_robin_pool_id) REFERENCES public.round_robin_pool(round_robin_pool_id);


--
-- TOC entry 5162 (class 2606 OID 21317)
-- Name: round_robin_pool_member fk_round_robin_pool_member_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.round_robin_pool_member
    ADD CONSTRAINT fk_round_robin_pool_member_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5160 (class 2606 OID 21307)
-- Name: round_robin_pool fk_round_robin_pool_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.round_robin_pool
    ADD CONSTRAINT fk_round_robin_pool_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5163 (class 2606 OID 21322)
-- Name: shift_timing fk_shift_timing_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_timing
    ADD CONSTRAINT fk_shift_timing_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5164 (class 2606 OID 21327)
-- Name: state_table fk_state_table_country_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.state_table
    ADD CONSTRAINT fk_state_table_country_id FOREIGN KEY (country_id) REFERENCES public.country_table(country_id);


--
-- TOC entry 5165 (class 2606 OID 21332)
-- Name: table_booking_info fk_table_booking_info_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT fk_table_booking_info_customer_id FOREIGN KEY (customer_id) REFERENCES public.customer_table(customer_id);


--
-- TOC entry 5166 (class 2606 OID 21337)
-- Name: table_booking_info fk_table_booking_info_meal_slot_timing_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT fk_table_booking_info_meal_slot_timing_id FOREIGN KEY (meal_slot_timing_id) REFERENCES public.meal_slot_timing(meal_slot_timing_id);


--
-- TOC entry 5167 (class 2606 OID 21342)
-- Name: table_booking_info fk_table_booking_info_occasion_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT fk_table_booking_info_occasion_id FOREIGN KEY (occasion_id) REFERENCES public.table_booking_occasion_info(occasion_id);


--
-- TOC entry 5168 (class 2606 OID 21347)
-- Name: table_booking_info fk_table_booking_info_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT fk_table_booking_info_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5169 (class 2606 OID 21352)
-- Name: table_booking_info fk_table_booking_info_table_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_booking_info
    ADD CONSTRAINT fk_table_booking_info_table_id FOREIGN KEY (table_id) REFERENCES public.table_info(table_id);


--
-- TOC entry 5170 (class 2606 OID 21357)
-- Name: table_info fk_table_info_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_info
    ADD CONSTRAINT fk_table_info_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5171 (class 2606 OID 21362)
-- Name: table_special_features fk_table_special_features_table_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_special_features
    ADD CONSTRAINT fk_table_special_features_table_id FOREIGN KEY (table_id) REFERENCES public.table_info(table_id);


--
-- TOC entry 5172 (class 2606 OID 21367)
-- Name: taxes fk_taxes_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxes
    ADD CONSTRAINT fk_taxes_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5173 (class 2606 OID 21372)
-- Name: user_audit_trail fk_user_audit_trail_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_audit_trail
    ADD CONSTRAINT fk_user_audit_trail_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5174 (class 2606 OID 21377)
-- Name: user_contact fk_user_contact_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_contact
    ADD CONSTRAINT fk_user_contact_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5175 (class 2606 OID 21382)
-- Name: user_department fk_user_department_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_department
    ADD CONSTRAINT fk_user_department_department_id FOREIGN KEY (department_id) REFERENCES public.department(department_id);


--
-- TOC entry 5176 (class 2606 OID 21387)
-- Name: user_department fk_user_department_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_department
    ADD CONSTRAINT fk_user_department_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5177 (class 2606 OID 21392)
-- Name: user_login_history fk_user_login_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_login_history
    ADD CONSTRAINT fk_user_login_history_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5178 (class 2606 OID 21397)
-- Name: user_profile fk_user_profile_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT fk_user_profile_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5179 (class 2606 OID 21402)
-- Name: user_role fk_user_role_role_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT fk_user_role_role_id FOREIGN KEY (role_id) REFERENCES public.role(role_id);


--
-- TOC entry 5180 (class 2606 OID 21407)
-- Name: user_role fk_user_role_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT fk_user_role_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5181 (class 2606 OID 21412)
-- Name: user_session fk_user_session_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT fk_user_session_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5182 (class 2606 OID 21417)
-- Name: user_shift_assignment fk_user_shift_assignment_shift_timing_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_shift_assignment
    ADD CONSTRAINT fk_user_shift_assignment_shift_timing_id FOREIGN KEY (shift_timing_id) REFERENCES public.shift_timing(shift_timing_id);


--
-- TOC entry 5183 (class 2606 OID 21422)
-- Name: user_shift_assignment fk_user_shift_assignment_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_shift_assignment
    ADD CONSTRAINT fk_user_shift_assignment_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5184 (class 2606 OID 21427)
-- Name: user_tag fk_user_tag_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tag
    ADD CONSTRAINT fk_user_tag_user_id FOREIGN KEY (user_id) REFERENCES public."user"(user_id);


--
-- TOC entry 5186 (class 2606 OID 21437)
-- Name: variation_groups fk_variation_groups_restaurant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_groups
    ADD CONSTRAINT fk_variation_groups_restaurant_id FOREIGN KEY (restaurant_id) REFERENCES public.restaurant_table(restaurant_id);


--
-- TOC entry 5187 (class 2606 OID 21442)
-- Name: variation_options fk_variation_options_dietary_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_options
    ADD CONSTRAINT fk_variation_options_dietary_type_id FOREIGN KEY (dietary_type_id) REFERENCES public.dietary_types(dietary_type_id);


--
-- TOC entry 5188 (class 2606 OID 21447)
-- Name: variation_options fk_variation_options_menu_item_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_options
    ADD CONSTRAINT fk_variation_options_menu_item_id FOREIGN KEY (menu_item_id) REFERENCES public.menu_item(menu_item_id);


--
-- TOC entry 5189 (class 2606 OID 21452)
-- Name: variation_options fk_variation_options_variation_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variation_options
    ADD CONSTRAINT fk_variation_options_variation_group_id FOREIGN KEY (variation_group_id) REFERENCES public.variation_groups(variation_group_id);


--
-- TOC entry 5068 (class 2606 OID 20847)
-- Name: menu_item_ordertype_mapping menu_item_ordertype_mapping_menu_item_ordertype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_ordertype_mapping
    ADD CONSTRAINT menu_item_ordertype_mapping_menu_item_ordertype_id_fkey FOREIGN KEY (menu_item_ordertype_id) REFERENCES public.order_type_table(order_type_id);


--
-- TOC entry 5078 (class 2606 OID 20897)
-- Name: menu_item_variation_mapping menu_item_variation_mapping_menu_item_variation_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_variation_mapping
    ADD CONSTRAINT menu_item_variation_mapping_menu_item_variation_group_id_fkey FOREIGN KEY (menu_item_variation_group_id) REFERENCES public.variation_groups(variation_group_id);


--
-- TOC entry 5112 (class 2606 OID 21067)
-- Name: order_payment order_payment_primary_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_payment
    ADD CONSTRAINT order_payment_primary_transaction_id_fkey FOREIGN KEY (primary_transaction_id) REFERENCES public.payment_transaction(payment_transaction_id);


--
-- TOC entry 5119 (class 2606 OID 21102)
-- Name: order_tax_line order_tax_line_order_tax_line_charge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_tax_line
    ADD CONSTRAINT order_tax_line_order_tax_line_charge_id_fkey FOREIGN KEY (order_tax_line_charge_id) REFERENCES public.order_charges(order_charges_id);


--
-- TOC entry 5185 (class 2606 OID 21432)
-- Name: user_tag user_tag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tag
    ADD CONSTRAINT user_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag(tag_id);


-- Completed on 2025-11-27 06:22:45 IST

--
-- PostgreSQL database dump complete
--

\unrestrict QmurM6u0XzoY6jgF9TSr1qVg3Gzr7cZ6UEJNouSvHD6AHmtAk7MQUhx9X7GoDEo

