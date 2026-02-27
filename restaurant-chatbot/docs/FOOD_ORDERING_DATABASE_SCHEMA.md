# Food Ordering Database Schema Documentation

> **Database:** A24_localdb
> **Generated:** 2025-11-27
> **Total Tables:** 65 tables across Menu, Order, and Payment domains

---

## Table of Contents

1. [Overview](#overview)
2. [Menu Tables](#1-menu-tables-30-tables)
   - [Lookup Tables](#11-lookup-tables)
   - [Menu Hierarchy Tables](#12-menu-hierarchy-tables)
   - [Core Menu Item Table](#13-core-menu-item-table)
   - [Menu Mapping Tables](#14-menu-mapping-tables)
   - [Menu Extended Tables](#15-menu-extended-tables)
3. [Order Tables](#2-order-tables-24-tables)
   - [Order Lookup Tables](#21-order-lookup-tables)
   - [Core Order Tables](#22-core-order-tables)
   - [Order Detail Tables](#23-order-detail-tables)
4. [Payment Tables](#3-payment-tables-11-tables)
   - [Payment Lookup Tables](#31-payment-lookup-tables)
   - [Core Payment Tables](#32-core-payment-tables)
   - [Payment Supporting Tables](#33-payment-supporting-tables)
5. [Entity Relationships](#4-entity-relationships)

---

## Overview

| Domain | Table Count | Description |
|--------|-------------|-------------|
| **Menu** | 30 | Menu structure, items, attributes, and mappings |
| **Order** | 24 | Order lifecycle, items, and details |
| **Payment** | 11 | Payment processing, transactions, and refunds |

### Common Audit Fields (Present in all tables)

| Column | Data Type | Nullable | Default | Description |
|--------|-----------|----------|---------|-------------|
| `created_at` | TIMESTAMP WITH TIME ZONE | YES | CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | YES | CURRENT_TIMESTAMP | Last update timestamp |
| `created_by` | UUID | YES | - | User who created the record |
| `updated_by` | UUID | YES | - | User who last updated the record |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | YES | - | Soft delete timestamp |
| `is_deleted` | BOOLEAN | YES | false | Soft delete flag |

---

## 1. Menu Tables (30 Tables)

### 1.1 Lookup Tables

#### `meal_type`
> Meal type classifications (Breakfast, Lunch, Dinner, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `meal_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `meal_type_name` | VARCHAR | 255 | YES | - | Meal type name |
| `display_order` | INTEGER | - | YES | - | Display order |

---

#### `cuisines`
> Cuisine types (Indian, Chinese, Italian, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `cuisine_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `cuisine_name` | VARCHAR | 255 | YES | - | Cuisine name |
| `cuisine_status` | VARCHAR | 20 | YES | - | Status (active/inactive) |

---

#### `allergens`
> Allergen definitions (Peanuts, Gluten, Dairy, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `allergen_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `allergen_name` | VARCHAR | 255 | NO | - | Allergen name |
| `allergen_description` | TEXT | - | YES | - | Allergen description |

---

#### `dietary_types`
> Dietary type definitions (Vegetarian, Vegan, Keto, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `dietary_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `dietary_type_name` | VARCHAR | 255 | YES | - | Dietary type name |
| `dietary_type_label` | VARCHAR | 255 | YES | - | Display label |
| `dietary_type_description` | TEXT | - | YES | - | Description |

---

#### `dietary_restrictions`
> Dietary restriction definitions

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `dietary_restriction_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `dietary_restriction_name` | VARCHAR | 255 | NO | - | Restriction name |
| `dietary_restriction_description` | TEXT | - | YES | - | Description |

---

#### `customer_allergens`
> Customer allergen preferences (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `customer_id` | UUID | - | NO | - | FK → customer_table |
| `allergen_id` | UUID | - | NO | - | FK → allergens |
| `customer_allergen_severity` | VARCHAR | 255 | YES | - | Severity level |
| `customer_allergen_notes` | TEXT | - | YES | - | Additional notes |

---

#### `customer_dietary_restrictions`
> Customer dietary restriction preferences (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `customer_id` | UUID | - | NO | - | FK → customer_table |
| `dietary_restriction_id` | UUID | - | NO | - | FK → dietary_restrictions |
| `customer_dietary_restriction_severity` | VARCHAR | 255 | YES | - | Severity level |
| `customer_dietary_restriction_notes` | TEXT | - | YES | - | Additional notes |

---

### 1.2 Menu Hierarchy Tables

#### `menu_sections`
> Top-level dietary classification (Veg/Non-Veg/Vegan)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_section_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `section_name` | VARCHAR | 100 | YES | - | Section name |
| `section_description` | TEXT | - | YES | - | Description |
| `section_status` | VARCHAR | 20 | YES | - | Status (active/inactive) |
| `section_rank` | INTEGER | - | YES | - | Display order |
| `section_image_url` | TEXT | - | YES | - | Image URL |

---

#### `menu_categories`
> Course-based categories (Tiffin, Main Course, Beverages, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_category_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_section_id` | UUID | - | YES | - | FK → menu_sections |
| `menu_category_name` | VARCHAR | 255 | YES | - | Category name |
| `menu_category_description` | TEXT | - | YES | - | Description |
| `menu_category_status` | VARCHAR | 20 | YES | - | Status (active/inactive) |
| `menu_category_rank` | INTEGER | - | YES | - | Display order |
| `menu_category_timings` | TEXT | - | YES | - | Availability timings |
| `menu_category_image_url` | TEXT | - | YES | - | Image URL |

---

#### `menu_sub_categories`
> Sub-categories under categories (Dosas, Breads, Juices, etc.)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_sub_category_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `category_id` | UUID | - | YES | - | FK → menu_categories |
| `sub_category_name` | VARCHAR | 100 | YES | - | Sub-category name |
| `sub_category_description` | TEXT | - | YES | - | Description |
| `sub_category_status` | VARCHAR | 20 | YES | - | Status (active/inactive) |
| `sub_category_rank` | INTEGER | - | YES | - | Display order |
| `sub_category_timings` | TEXT | - | YES | - | Availability timings |
| `sub_category_image_url` | TEXT | - | YES | - | Image URL |

---

### 1.3 Core Menu Item Table

#### `menu_item`
> Individual menu items (dishes) - Core product data (38 columns)

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| **Primary Key** |
| `menu_item_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| **Foreign Keys** |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_sub_category_id` | UUID | - | YES | - | FK → menu_sub_categories (DEPRECATED) |
| `menu_item_attribute_id` | UUID | - | YES | - | FK → menu_item_attribute |
| `menu_item_tax_id` | UUID | - | YES | - | Tax reference |
| **Basic Info** |
| `menu_item_name` | VARCHAR | 255 | YES | - | Item name |
| `menu_item_description` | TEXT | - | YES | - | Item description |
| `menu_item_image_url` | VARCHAR | 500 | YES | - | Image URL |
| **Pricing** |
| `menu_item_price` | NUMERIC | (12,2) | YES | 0 | Base price |
| `menu_item_markup_price` | NUMERIC | (12,2) | YES | - | Markup price |
| `menu_item_packaging_charges` | NUMERIC | (10,2) | YES | 0 | Packaging charges |
| **Tax** |
| `menu_item_tax_cgst` | NUMERIC | (8,2) | YES | - | CGST percentage |
| `menu_item_tax_sgst` | NUMERIC | (8,2) | YES | - | SGST percentage |
| `menu_item_ignore_taxes` | BOOLEAN | - | YES | false | Ignore tax calculation |
| **Status & Availability** |
| `menu_item_status` | VARCHAR | 20 | YES | - | Status (active/inactive/discontinued) |
| `menu_item_in_stock` | BOOLEAN | - | YES | true | In stock flag |
| `menu_item_quantity` | INTEGER | - | YES | 0 | Available quantity |
| **Attributes** |
| `menu_item_spice_level` | VARCHAR | 50 | YES | - | Spice level (none/mild/medium/hot/extra_hot) |
| `menu_item_is_recommended` | BOOLEAN | - | YES | false | Recommended item flag |
| `menu_item_favorite` | BOOLEAN | - | YES | false | Popular/favorite flag |
| `menu_item_is_seasonal` | BOOLEAN | - | YES | false | Seasonal item flag |
| `menu_item_calories` | INTEGER | - | YES | - | Calorie count |
| `menu_item_serving_unit` | VARCHAR | 20 | YES | - | Serving unit |
| **Operational** |
| `menu_item_minimum_preparation_time` | INTEGER | - | YES | - | Prep time in minutes |
| `menu_item_rank` | INTEGER | - | YES | - | Display order |
| `menu_item_timings` | TEXT | - | YES | - | Availability timings (DEPRECATED) |
| **Variations & Addons** |
| `menu_item_allow_variation` | BOOLEAN | - | YES | false | Allow variations |
| `menu_item_allow_addon` | BOOLEAN | - | YES | false | Allow addons |
| `menu_item_addon_based_on` | TEXT | - | YES | - | Addon basis |
| **Combo** |
| `menu_item_is_combo` | BOOLEAN | - | YES | false | Is combo item |
| `menu_item_is_combo_parent` | BOOLEAN | - | YES | false | Is parent combo item |
| **Discount** |
| `menu_item_ignore_discounts` | BOOLEAN | - | YES | false | Ignore discounts |

---

### 1.4 Menu Mapping Tables

#### `menu_item_category_mapping`
> Maps menu items to categories (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `mapping_id` | UUID | - | NO | gen_random_uuid() | Primary Key |
| `restaurant_id` | UUID | - | NO | - | FK → restaurant_table |
| `menu_item_id` | UUID | - | NO | - | FK → menu_item |
| `menu_category_id` | UUID | - | NO | - | FK → menu_categories |
| `menu_sub_category_id` | UUID | - | YES | - | FK → menu_sub_categories |
| `is_primary` | BOOLEAN | - | YES | false | Primary category flag |
| `display_rank` | INTEGER | - | YES | 0 | Display order |

---

#### `menu_item_cuisine_mapping`
> Maps menu items to cuisines (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_cuisine_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `cuisine_id` | UUID | - | YES | - | FK → cuisines |

---

#### `menu_item_dietary_mapping`
> Maps menu items to dietary types (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `mapping_id` | UUID | - | NO | gen_random_uuid() | Primary Key |
| `menu_item_id` | UUID | - | NO | - | FK → menu_item |
| `dietary_type_id` | UUID | - | NO | - | FK → dietary_types |
| `restaurant_id` | UUID | - | NO | - | FK → restaurant_table |

---

#### `menu_item_allergen_mapping`
> Maps menu items to allergens (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `mapping_id` | UUID | - | NO | gen_random_uuid() | Primary Key |
| `menu_item_id` | UUID | - | NO | - | FK → menu_item |
| `allergen_id` | UUID | - | NO | - | FK → allergens |
| `restaurant_id` | UUID | - | NO | - | FK → restaurant_table |

---

#### `menu_item_ingredient`
> Menu item ingredients list

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `ingredient_id` | UUID | - | NO | gen_random_uuid() | Primary Key |
| `menu_item_id` | UUID | - | NO | - | FK → menu_item |
| `restaurant_id` | UUID | - | NO | - | FK → restaurant_table |
| `ingredient_name` | VARCHAR | 200 | NO | - | Ingredient name |
| `ingredient_quantity` | NUMERIC | (10,2) | YES | - | Quantity |
| `ingredient_unit` | VARCHAR | 50 | YES | - | Unit of measurement |
| `ingredient_rank` | INTEGER | - | YES | 0 | Display order |
| `is_primary` | BOOLEAN | - | YES | false | Primary ingredient flag |

---

#### `menu_item_availability_schedule`
> Time-based item availability

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `schedule_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `meal_type_id` | UUID | - | YES | - | FK → meal_type |
| `day_of_week` | VARCHAR | 255 | YES | - | Day of week |
| `time_from` | TIME | - | YES | - | Start time |
| `time_to` | TIME | - | YES | - | End time |
| `is_available` | BOOLEAN | - | YES | true | Availability flag |

---

#### `menu_item_tag_mapping`
> Maps menu items to tags (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_tag_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_tag_id` | UUID | - | YES | - | FK → menu_item_tag |

---

#### `menu_item_tax_mapping`
> Maps menu items to tax rules (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_tax_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `tax_id` | UUID | - | YES | - | FK → tax table |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

#### `menu_item_discount_mapping`
> Maps menu items to discounts (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_discount_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `discount_id` | UUID | - | YES | - | FK → discount table |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

#### `menu_item_ordertype_mapping`
> Maps menu items to order types (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_ordertype_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_ordertype_id` | UUID | - | YES | - | FK → order_type_table |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

#### `menu_item_addon_mapping`
> Maps menu items to addon groups (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_addon_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_variation_id` | UUID | - | YES | - | FK → menu_item_variation |
| `menu_item_addon_group_id` | UUID | - | YES | - | FK → menu_item_addon_group |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

#### `menu_item_variation_mapping`
> Maps menu items to variations (many-to-many)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_variation_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_variation_id` | UUID | - | YES | - | FK → menu_item_variation |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

### 1.5 Menu Extended Tables

#### `menu_item_addon_group`
> Addon group definitions

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_addon_group_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_item_addon_group_name` | VARCHAR | 255 | YES | - | Group name |
| `menu_item_addon_group_rank` | INTEGER | - | YES | - | Display order |
| `menu_item_addon_group_status` | VARCHAR | 20 | YES | - | Status |
| `menu_item_addon_group_selection_min` | INTEGER | - | YES | - | Minimum selections |
| `menu_item_addon_group_selection_max` | INTEGER | - | YES | - | Maximum selections |

---

#### `menu_item_addon_item`
> Individual addon items

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `menu_item_addon_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_addon_group_id` | UUID | - | YES | - | FK → menu_item_addon_group |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_item_addon_item_name` | VARCHAR | 255 | YES | - | Addon name |
| `menu_item_addon_item_price` | NUMERIC | (10,2) | YES | - | Addon price |
| `menu_item_addon_item_status` | VARCHAR | 20 | YES | - | Status |
| `menu_item_addon_item_rank` | INTEGER | - | YES | - | Display order |
| `menu_item_addon_item_attribute_id` | UUID | - | YES | - | FK → menu_item_attribute |

---

#### `menu_item_variation`
> Item variation definitions (size, etc.)

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `menu_item_variation_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_item_variation_name` | VARCHAR | 255 | YES | - | Variation name |
| `menu_item_variation_price` | NUMERIC | (10,2) | YES | - | Variation price |
| `menu_item_variation_status` | VARCHAR | 20 | YES | - | Status |
| `menu_item_variation_rank` | INTEGER | - | YES | - | Display order |

---

#### `menu_item_attribute`
> Custom attributes for menu items (Veg/Non-Veg indicators)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_attribute_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_attribute_name` | VARCHAR | 255 | YES | - | Attribute name |
| `menu_item_attribute_status` | VARCHAR | 20 | YES | - | Status |

---

#### `menu_item_tag`
> Tag definitions for menu items

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_tag_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_tag_name` | VARCHAR | 255 | YES | - | Tag name |
| `menu_item_tag_status` | VARCHAR | 20 | YES | - | Status |

---

#### `menu_item_option`
> Additional options for menu items

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `menu_item_option_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_option_name` | VARCHAR | 255 | YES | - | Option name |
| `menu_item_option_description` | TEXT | - | YES | - | Option description |

---

#### `menu_sync_log`
> External menu synchronization tracking

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `sync_log_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `sync_status` | VARCHAR | 20 | YES | - | Sync status |
| `sync_started_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Start time |
| `sync_completed_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Completion time |
| `sync_errors` | TEXT | - | YES | - | Error details |
| `items_synced` | INTEGER | - | YES | - | Items count |

---

#### `menu_version_history`
> Menu change history tracking

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `version_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `version_number` | INTEGER | - | YES | - | Version number |
| `change_type` | VARCHAR | 20 | YES | - | Type of change |
| `previous_data` | JSONB | - | YES | - | Previous state |
| `new_data` | JSONB | - | YES | - | New state |

---

## 2. Order Tables (24 Tables)

### 2.1 Order Lookup Tables

#### `order_type_table`
> Order type definitions (dine_in, takeout, delivery)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_type_code` | VARCHAR | 20 | YES | - | Type code |
| `order_type_name` | VARCHAR | 255 | YES | - | Type name |

---

#### `order_source_type`
> Order source definitions (app, web, pos, phone, walk_in)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_source_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_source_type_code` | VARCHAR | 20 | YES | - | Source code |
| `order_source_type_name` | VARCHAR | 255 | YES | - | Source name |

---

#### `order_status_type`
> Order status definitions (draft, pending, confirmed, preparing, ready, completed, cancelled)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_status_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_status_code` | VARCHAR | 20 | YES | - | Status code |
| `order_status_name` | VARCHAR | 255 | YES | - | Status name |
| `order_status_description` | TEXT | - | YES | - | Description |
| `order_status_is_active` | BOOLEAN | - | YES | true | Active flag |

---

### 2.2 Core Order Tables

#### `orders`
> Main order table (16 columns)

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `table_booking_id` | UUID | - | YES | - | FK → table_booking_info |
| `order_type_id` | UUID | - | YES | - | FK → order_type_table |
| `order_source_type_id` | UUID | - | YES | - | FK → order_source_type |
| `order_status_type_id` | UUID | - | YES | - | FK → order_status_type |
| `order_number` | BIGINT | - | YES | - | Sequential order number |
| `order_invoice_number` | VARCHAR | 20 | YES | - | Invoice number |
| `order_vr_order_id` | VARCHAR | 255 | YES | - | External VR system ID |
| `order_external_reference_id` | VARCHAR | 255 | YES | - | External reference |

---

#### `order_item`
> Individual items within an order (29 columns)

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_item_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `menu_item_id` | UUID | - | YES | - | FK → menu_item |
| `menu_item_variation_id` | UUID | - | YES | - | FK → menu_item_variation |
| `category_id` | UUID | - | YES | - | Category reference |
| `substitute_item_id` | UUID | - | YES | - | Substitute item reference |
| **Item Details** |
| `sku` | VARCHAR | 100 | YES | - | SKU code |
| `hsn_code` | VARCHAR | 20 | YES | - | HSN code |
| `category_name` | VARCHAR | 100 | YES | - | Category name snapshot |
| **Pricing** |
| `base_price` | NUMERIC | (10,2) | YES | - | Base price |
| `discount_amount` | NUMERIC | (10,2) | YES | - | Discount amount |
| `tax_amount` | NUMERIC | (10,2) | YES | - | Tax amount |
| `addon_total` | NUMERIC | (10,2) | YES | - | Addon total |
| **Availability** |
| `is_available` | BOOLEAN | - | YES | true | Availability flag |
| `unavailable_reason` | TEXT | - | YES | - | Unavailability reason |
| **Customization** |
| `cooking_instructions` | TEXT | - | YES | - | Cooking instructions |
| `spice_level` | VARCHAR | 20 | YES | - | Spice level |
| `customizations` | JSONB | - | YES | - | Customization details |
| **Status Tracking** |
| `item_status` | VARCHAR | 50 | YES | - | Item status |
| `prepared_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Preparation timestamp |
| `served_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Serving timestamp |
| `cancelled_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Cancellation timestamp |
| `cancellation_reason` | TEXT | - | YES | - | Cancellation reason |

---

#### `order_total`
> Order totals and calculations

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_total_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `items_total` | NUMERIC | (12,2) | YES | - | Sum of item prices |
| `addons_total` | NUMERIC | (12,2) | YES | - | Sum of addon prices |
| `charges_total` | NUMERIC | (12,2) | YES | - | Sum of charges |
| `discount_total` | NUMERIC | (12,2) | YES | - | Total discounts |
| `tax_total` | NUMERIC | (12,2) | YES | - | Total taxes |
| `platform_fee` | NUMERIC | (10,2) | YES | - | Platform fee |
| `convenience_fee` | NUMERIC | (10,2) | YES | - | Convenience fee |
| `subtotal` | NUMERIC | (12,2) | YES | - | Subtotal |
| `roundoff_amount` | NUMERIC | (10,2) | YES | - | Round-off amount |
| `total_before_tip` | NUMERIC | (12,2) | YES | - | Total before tip |
| `tip_amount` | NUMERIC | (10,2) | YES | - | Tip amount |
| `final_amount` | NUMERIC | (12,2) | YES | - | Final payable amount |

---

### 2.3 Order Detail Tables

#### `order_status_history`
> Tracks order status changes over time

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_status_history_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_status_type_id` | UUID | - | YES | - | FK → order_status_type |
| `order_status_changed_by` | UUID | - | YES | - | User who changed status |
| `order_status_changed_at` | TIMESTAMP WITH TIME ZONE | - | YES | CURRENT_TIMESTAMP | Change timestamp |
| `order_status_notes` | TEXT | - | YES | - | Status change notes |

---

#### `order_charges`
> Additional charges on orders

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_charges_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_item_id` | UUID | - | YES | - | FK → order_item |
| `order_charges_type` | VARCHAR | 20 | YES | - | Charge type |
| `order_charges_base_amount` | NUMERIC | (10,2) | YES | - | Base amount |
| `order_charges_taxable_amount` | NUMERIC | (10,2) | YES | - | Taxable amount |
| `order_charges_metadata_json` | JSONB | - | YES | - | Additional metadata |

---

#### `order_discount`
> Discounts applied to orders

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_discount_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_discount_type_id` | UUID | - | YES | - | Discount type reference |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_item_id` | UUID | - | YES | - | FK → order_item |
| `order_discount_amount` | NUMERIC | (10,2) | YES | - | Discount amount |
| `order_discount_percentage` | NUMERIC | (5,2) | YES | - | Discount percentage |
| `order_discount_code` | VARCHAR | 20 | YES | - | Discount code |

---

#### `order_tax_line`
> Tax breakdown for orders

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_tax_line_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_item_id` | UUID | - | YES | - | FK → order_item |
| `tax_id` | UUID | - | YES | - | Tax reference |
| `tax_name` | VARCHAR | 100 | YES | - | Tax name |
| `tax_rate` | NUMERIC | (5,2) | YES | - | Tax rate |
| `tax_amount` | NUMERIC | (10,2) | YES | - | Tax amount |

---

#### `order_customer_details`
> Customer info snapshot for orders

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_customer_details_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `customer_id` | UUID | - | YES | - | FK → customer_table |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |

---

#### `order_dining_info`
> Dine-in specific information

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_dining_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `table_id` | UUID | - | YES | - | Table reference |
| `table_no` | INTEGER | - | YES | - | Table number |
| `table_area` | VARCHAR | 255 | YES | - | Table area/section |
| `no_of_persons` | INTEGER | - | YES | - | Number of covers |

---

#### `order_delivery_info`
> Delivery specific information

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `order_delivery_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `delivery_partner_id` | UUID | - | YES | - | Delivery partner reference |
| `enable_delivery` | BOOLEAN | - | YES | false | Delivery enabled flag |
| `delivery_type` | VARCHAR | 20 | YES | - | Delivery type |
| `delivery_slot` | TEXT | - | YES | - | Delivery slot |
| `delivery_address_id` | UUID | - | YES | - | Address reference |
| `delivery_distance_km` | NUMERIC | (10,2) | YES | - | Distance in km |
| `delivery_estimated_time` | TIMESTAMP WITH TIME ZONE | - | YES | - | Estimated delivery time |
| `delivery_actual_time` | TIMESTAMP WITH TIME ZONE | - | YES | - | Actual delivery time |
| `delivery_person_id` | UUID | - | YES | - | Delivery person reference |
| `delivery_started_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Delivery start time |
| `delivery_completed_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Delivery completion time |
| `delivery_otp` | VARCHAR | 20 | YES | - | Delivery OTP |
| `delivery_verification_method` | VARCHAR | 255 | YES | - | Verification method |
| `delivery_tracking_url` | TEXT | - | YES | - | Tracking URL |
| `delivery_proof_url` | TEXT | - | YES | - | Proof of delivery URL |

---

#### `order_kitchen_detail`
> Kitchen tracking information

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_kitchen_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_item_id` | UUID | - | YES | - | FK → order_item |
| `estimated_ready_time` | TIMESTAMP WITH TIME ZONE | - | YES | - | Estimated ready time |
| `actual_ready_time` | TIMESTAMP WITH TIME ZONE | - | YES | - | Actual ready time |
| `preparation_start_time` | TIMESTAMP WITH TIME ZONE | - | YES | - | Preparation start |
| `minimum_preparation_time` | INTEGER | - | YES | - | Min prep time in minutes |

---

#### `order_instruction`
> Order instructions and notes

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_instruction_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `special_instructions` | TEXT | - | YES | - | Special instructions |
| `kitchen_notes` | TEXT | - | YES | - | Kitchen notes |
| `delivery_notes` | TEXT | - | YES | - | Delivery notes |
| `allergen_warning` | TEXT | - | YES | - | Allergen warnings |
| `dietary_preferences` | TEXT | - | YES | - | Dietary preferences |

---

#### `order_note`
> General order notes

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_note_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_note_type` | VARCHAR | 20 | YES | - | Note type |
| `order_note_text` | TEXT | - | YES | - | Note text |
| `order_note_visibility` | BOOLEAN | - | YES | true | Visibility flag |
| `order_note_added_by` | UUID | - | YES | - | Added by user |
| `is_important` | BOOLEAN | - | YES | false | Important flag |

---

#### `order_scheduling`
> Scheduled order information

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_scheduling_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `scheduled_date` | DATE | - | YES | - | Scheduled date |
| `scheduled_time` | TIME | - | YES | - | Scheduled time |
| `is_asap` | BOOLEAN | - | YES | true | ASAP flag |

---

#### `order_priority`
> Order priority settings

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_priority_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `priority_level` | INTEGER | - | YES | - | Priority level |
| `priority_reason` | TEXT | - | YES | - | Priority reason |

---

#### `order_invoice`
> Invoice generation tracking

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_invoice_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `is_invoice_generated` | BOOLEAN | - | YES | false | Generated flag |
| `invoice_url` | TEXT | - | YES | - | Invoice URL |
| `invoice_generated_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Generation timestamp |
| `gstin` | VARCHAR | 255 | YES | - | GSTIN number |
| `is_business_order` | BOOLEAN | - | YES | false | Business order flag |
| `business_name` | VARCHAR | 255 | YES | - | Business name |

---

#### `order_audit`
> Order change audit log

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_audit_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `session_id` | UUID | - | YES | - | Session reference |
| `order_version` | INTEGER | - | YES | - | Order version |
| `modified_by` | UUID | - | YES | - | Modified by user |
| `modification_reason` | TEXT | - | YES | - | Modification reason |

---

#### `order_integration_sync`
> External system sync status

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_integration_sync_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `sync_status` | VARCHAR | 20 | YES | - | Sync status |
| `sync_errors` | TEXT | - | YES | - | Sync errors |
| `last_synced_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Last sync timestamp |

---

#### `order_security_detail`
> Security and fraud detection information

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_security_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `ip_address` | VARCHAR | 255 | YES | - | IP address |
| `device_id` | VARCHAR | 255 | YES | - | Device ID |
| `user_agent` | TEXT | - | YES | - | User agent |
| `fraud_score` | NUMERIC | (5,2) | YES | - | Fraud score |

---

#### `order_payment`
> Links orders to payment orders

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_payment_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `is_primary` | BOOLEAN | - | YES | true | Primary payment flag |

---

#### `order_payment_method`
> Payment method preferences

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `order_payment_method_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `payment_method_type` | VARCHAR | 50 | YES | - | Payment method type |
| `is_default` | BOOLEAN | - | YES | false | Default flag |

---

## 3. Payment Tables (11 Tables)

### 3.1 Payment Lookup Tables

#### `payment_gateway`
> Payment gateway configurations

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `payment_gateway_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_gateway_code` | VARCHAR | 20 | YES | - | Gateway code (razorpay, stripe) |
| `payment_gateway_name` | VARCHAR | 255 | YES | - | Gateway name |
| `payment_gateway_is_active` | BOOLEAN | - | YES | true | Active flag |
| `payment_gateway_config` | JSONB | - | YES | - | Gateway configuration |

---

#### `payment_status_type`
> Payment status definitions

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `payment_status_type_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_status_code` | VARCHAR | 20 | YES | - | Status code |
| `payment_status_name` | VARCHAR | 255 | YES | - | Status name |
| `payment_status_description` | TEXT | - | YES | - | Description |
| `payment_status_is_terminal` | BOOLEAN | - | YES | false | Terminal state flag |

---

### 3.2 Core Payment Tables

#### `payment_order`
> Payment order linking restaurant orders to payment gateway orders

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `payment_order_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `order_id` | UUID | - | YES | - | FK → orders |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `customer_id` | UUID | - | YES | - | FK → customer_table |
| `payment_gateway_id` | UUID | - | YES | - | FK → payment_gateway |
| **Gateway Details** |
| `gateway_order_id` | TEXT | - | YES | - | Gateway order ID |
| `payment_order_status` | VARCHAR | 20 | YES | - | Order status |
| **Amount** |
| `order_amount` | NUMERIC | (12,2) | YES | - | Order amount |
| `order_currency` | VARCHAR | 3 | YES | 'INR' | Currency code |
| **Payment Link** |
| `payment_link_url` | TEXT | - | YES | - | Payment link URL |
| `payment_link_id` | VARCHAR | 255 | YES | - | Payment link ID |
| `payment_link_short_url` | TEXT | - | YES | - | Short URL |
| `payment_link_expires_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Link expiry time |
| **Retry Logic** |
| `retry_count` | INTEGER | - | YES | 0 | Current retry count |
| `max_retry_attempts` | INTEGER | - | YES | 3 | Max retries allowed |
| **Additional** |
| `notes` | TEXT | - | YES | - | Notes |
| `metadata` | JSONB | - | YES | - | Additional metadata |

---

#### `payment_transaction`
> Individual payment transaction records

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `payment_transaction_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `order_id` | UUID | - | YES | - | FK → orders |
| `restaurant_id` | UUID | - | YES | - | FK → restaurant_table |
| `customer_id` | UUID | - | YES | - | FK → customer_table |
| `payment_gateway_id` | UUID | - | YES | - | FK → payment_gateway |
| `order_payment_method_id` | UUID | - | YES | - | FK → order_payment_method |
| `payment_status_type_id` | UUID | - | YES | - | FK → payment_status_type |
| **Gateway IDs** |
| `gateway_payment_id` | TEXT | - | YES | - | Gateway payment ID |
| `gateway_transaction_id` | TEXT | - | YES | - | Gateway transaction ID |
| `gateway_signature` | TEXT | - | YES | - | Gateway signature |
| **Payment Method Details** |
| `payment_method_details` | JSONB | - | YES | - | Payment method details |
| **Amounts** |
| `transaction_amount` | NUMERIC | (12,2) | YES | - | Transaction amount |
| `amount_paid` | NUMERIC | (12,2) | YES | - | Amount paid |
| `amount_due` | NUMERIC | (12,2) | YES | - | Amount due |
| `transaction_currency` | VARCHAR | 3 | YES | 'INR' | Currency code |
| `gateway_fee` | NUMERIC | (10,2) | YES | - | Gateway fee |
| `gateway_tax` | NUMERIC | (10,2) | YES | - | Gateway tax |
| `net_amount` | NUMERIC | (12,2) | YES | - | Net amount |
| **Failure Details** |
| `failure_reason` | TEXT | - | YES | - | Failure reason |
| `failure_code` | VARCHAR | 20 | YES | - | Failure code |
| `error_description` | TEXT | - | YES | - | Error description |
| **Payment Method Info** |
| `bank_name` | TEXT | - | YES | - | Bank name |
| `card_network` | TEXT | - | YES | - | Card network |
| `card_type` | TEXT | - | YES | - | Card type |
| `card_last4` | VARCHAR | 4 | YES | - | Last 4 digits |
| `wallet_provider` | TEXT | - | YES | - | Wallet provider |
| `upi_vpa` | TEXT | - | YES | - | UPI VPA |
| **Customer Contact** |
| `customer_email` | TEXT | - | YES | - | Customer email |
| `customer_contact` | TEXT | - | YES | - | Customer phone |
| **Gateway Response** |
| `gateway_response` | JSONB | - | YES | - | Full gateway response |
| **Timestamps** |
| `attempted_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Attempt timestamp |
| `authorized_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Authorization timestamp |
| `captured_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Capture timestamp |
| `settled_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Settlement timestamp |

---

### 3.3 Payment Supporting Tables

#### `payment_refund`
> Refund records

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `payment_refund_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_transaction_id` | UUID | - | YES | - | FK → payment_transaction |
| `order_id` | UUID | - | YES | - | FK → orders |
| `order_item_id` | UUID | - | YES | - | FK → order_item |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `payment_gateway_id` | UUID | - | YES | - | FK → payment_gateway |
| **Gateway Details** |
| `gateway_refund_id` | VARCHAR | 255 | YES | - | Gateway refund ID |
| `gateway_payment_id` | VARCHAR | 255 | YES | - | Gateway payment ID |
| **Amount** |
| `refund_amount` | NUMERIC | (12,2) | YES | - | Refund amount |
| `refund_currency` | VARCHAR | 3 | YES | 'INR' | Currency code |
| **Refund Details** |
| `refund_reason_type_id` | UUID | - | YES | - | Reason type reference |
| `refund_reason_notes` | TEXT | - | YES | - | Reason notes |
| `refund_status_type_id` | UUID | - | YES | - | Status type reference |
| **Processing** |
| `initiated_by` | UUID | - | YES | - | Initiated by user |
| `approved_by` | UUID | - | YES | - | Approved by user |
| `processing_notes` | TEXT | - | YES | - | Processing notes |
| `gateway_response` | JSONB | - | YES | - | Gateway response |
| **Timestamps** |
| `refund_initiated_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Initiation timestamp |
| `refund_processed_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Processing timestamp |
| `refund_completed_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Completion timestamp |

---

#### `payment_split`
> Split payment handling

| Column | Data Type | Length/Precision | Nullable | Default | Description |
|--------|-----------|------------------|----------|---------|-------------|
| `payment_split_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_transaction_id` | UUID | - | YES | - | FK → payment_transaction |
| `order_id` | UUID | - | YES | - | FK → orders |
| `split_party_type` | VARCHAR | 20 | YES | - | Party type |
| `split_party_id` | UUID | - | YES | - | Party reference |
| `split_amount` | NUMERIC | (12,2) | YES | - | Split amount |
| `split_percentage` | NUMERIC | (5,2) | YES | - | Split percentage |
| `split_currency` | VARCHAR | 3 | YES | 'INR' | Currency code |
| `delivery_partner_id` | UUID | - | YES | - | Delivery partner reference |
| `is_settled` | BOOLEAN | - | YES | false | Settled flag |
| `settled_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Settlement timestamp |
| `settlement_reference` | VARCHAR | 255 | YES | - | Settlement reference |

---

#### `payment_retry_attempt`
> Payment retry tracking

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `retry_attempt_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `payment_transaction_id` | UUID | - | YES | - | FK → payment_transaction |
| `attempt_number` | INTEGER | - | YES | - | Attempt number |
| `gateway_payment_id` | TEXT | - | YES | - | Gateway payment ID |
| `attempt_status` | VARCHAR | 20 | YES | - | Attempt status |
| `failure_reason` | TEXT | - | YES | - | Failure reason |
| `failure_code` | VARCHAR | 20 | YES | - | Failure code |
| `retry_metadata` | JSONB | - | YES | - | Retry metadata |
| `attempted_at` | TIMESTAMP WITH TIME ZONE | - | YES | CURRENT_TIMESTAMP | Attempt timestamp |

---

#### `payment_audit_log`
> Payment change audit log

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `audit_log_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `payment_transaction_id` | UUID | - | YES | - | FK → payment_transaction |
| `payment_refund_id` | UUID | - | YES | - | FK → payment_refund |
| `event_type` | TEXT | - | YES | - | Event type |
| `event_source` | TEXT | - | YES | - | Event source |
| `request_payload` | JSONB | - | YES | - | Request payload |
| `response_payload` | JSONB | - | YES | - | Response payload |
| `gateway_event_id` | TEXT | - | YES | - | Gateway event ID |
| `gateway_event_type` | TEXT | - | YES | - | Gateway event type |
| `initiated_by` | UUID | - | YES | - | Initiated by user |
| `ip_address` | VARCHAR | 255 | YES | - | IP address |
| `user_agent` | VARCHAR | 255 | YES | - | User agent |
| `event_status` | VARCHAR | 20 | YES | - | Event status |
| `error_message` | TEXT | - | YES | - | Error message |

---

#### `payment_webhook_log`
> Gateway webhook logs

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `webhook_log_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_gateway_id` | UUID | - | YES | - | FK → payment_gateway |
| `webhook_event_id` | TEXT | - | YES | - | Webhook event ID |
| `webhook_event_type` | TEXT | - | YES | - | Webhook event type |
| `webhook_payload` | JSONB | - | YES | - | Webhook payload |
| `webhook_signature` | TEXT | - | YES | - | Webhook signature |
| `is_verified` | BOOLEAN | - | YES | false | Verification flag |
| `processing_status` | VARCHAR | 20 | YES | - | Processing status |
| `processing_error` | TEXT | - | YES | - | Processing error |
| `received_at` | TIMESTAMP WITH TIME ZONE | - | YES | CURRENT_TIMESTAMP | Received timestamp |
| `processed_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Processing timestamp |

---

#### `payment_external_mapping`
> External system payment mappings

| Column | Data Type | Length | Nullable | Default | Description |
|--------|-----------|--------|----------|---------|-------------|
| `external_mapping_id` | UUID | - | NO | uuid_generate_v4() | Primary Key |
| `payment_order_id` | UUID | - | YES | - | FK → payment_order |
| `payment_transaction_id` | UUID | - | YES | - | FK → payment_transaction |
| `external_system` | TEXT | - | YES | - | External system name |
| `external_payment_id` | TEXT | - | YES | - | External payment ID |
| `external_order_id` | TEXT | - | YES | - | External order ID |
| `sync_status` | VARCHAR | 20 | YES | - | Sync status |
| `sync_attempts` | INTEGER | - | YES | 0 | Sync attempts |
| `last_synced_at` | TIMESTAMP WITH TIME ZONE | - | YES | - | Last sync timestamp |
| `sync_error` | TEXT | - | YES | - | Sync error |
| `external_response` | JSONB | - | YES | - | External response |

---

## 4. Entity Relationships

### Menu Domain Relationships

```
restaurant_table
    │
    ├── 1:N ──► menu_sections
    │               │
    │               └── 1:N ──► menu_categories
    │                               │
    │                               └── 1:N ──► menu_sub_categories
    │
    └── 1:N ──► menu_item
                    │
                    ├── N:M ──► menu_item_category_mapping ──► menu_categories
                    ├── N:M ──► menu_item_cuisine_mapping ──► cuisines
                    ├── N:M ──► menu_item_dietary_mapping ──► dietary_types
                    ├── N:M ──► menu_item_allergen_mapping ──► allergens
                    ├── 1:N ──► menu_item_ingredient
                    ├── 1:N ──► menu_item_availability_schedule
                    ├── N:M ──► menu_item_addon_mapping ──► menu_item_addon_group
                    └── N:M ──► menu_item_variation_mapping ──► menu_item_variation
```

### Order Domain Relationships

```
orders
    │
    ├── N:1 ──► restaurant_table
    ├── N:1 ──► order_type_table
    ├── N:1 ──► order_source_type
    ├── N:1 ──► order_status_type
    │
    ├── 1:N ──► order_item ──► menu_item
    ├── 1:1 ──► order_total
    ├── 1:N ──► order_status_history
    ├── 1:N ──► order_charges
    ├── 1:N ──► order_discount
    ├── 1:N ──► order_tax_line
    ├── 1:1 ──► order_customer_details
    ├── 1:1 ──► order_dining_info
    ├── 1:1 ──► order_delivery_info
    ├── 1:N ──► order_kitchen_detail
    ├── 1:1 ──► order_instruction
    ├── 1:N ──► order_note
    ├── 1:1 ──► order_scheduling
    ├── 1:1 ──► order_priority
    ├── 1:1 ──► order_invoice
    ├── 1:N ──► order_audit
    └── 1:1 ──► order_integration_sync
```

### Payment Domain Relationships

```
payment_gateway
    │
    └── 1:N ──► payment_order
                    │
                    ├── N:1 ──► orders
                    ├── 1:N ──► payment_transaction
                    │               │
                    │               ├── N:1 ──► payment_status_type
                    │               ├── 1:N ──► payment_refund
                    │               └── 1:N ──► payment_split
                    │
                    ├── 1:N ──► payment_retry_attempt
                    ├── 1:N ──► payment_audit_log
                    └── 1:N ──► payment_external_mapping

payment_webhook_log ──► payment_gateway
```

---

## Appendix: Table Summary

| # | Table Name | Domain | Columns | Description |
|---|------------|--------|---------|-------------|
| 1 | meal_type | Menu | 9 | Meal type definitions |
| 2 | cuisines | Menu | 9 | Cuisine definitions |
| 3 | allergens | Menu | 9 | Allergen definitions |
| 4 | dietary_types | Menu | 10 | Dietary type definitions |
| 5 | dietary_restrictions | Menu | 9 | Dietary restriction definitions |
| 6 | customer_allergens | Menu | 10 | Customer allergen preferences |
| 7 | customer_dietary_restrictions | Menu | 10 | Customer dietary preferences |
| 8 | menu_sections | Menu | 13 | Top-level menu sections |
| 9 | menu_categories | Menu | 15 | Menu categories |
| 10 | menu_sub_categories | Menu | 15 | Menu sub-categories |
| 11 | menu_item | Menu | 38 | Core menu items |
| 12 | menu_item_category_mapping | Menu | 12 | Item-category mapping |
| 13 | menu_item_cuisine_mapping | Menu | 9 | Item-cuisine mapping |
| 14 | menu_item_dietary_mapping | Menu | 10 | Item-dietary mapping |
| 15 | menu_item_allergen_mapping | Menu | 10 | Item-allergen mapping |
| 16 | menu_item_ingredient | Menu | 14 | Item ingredients |
| 17 | menu_item_availability_schedule | Menu | 12 | Item availability |
| 18 | menu_item_addon_group | Menu | 13 | Addon groups |
| 19 | menu_item_addon_item | Menu | 14 | Addon items |
| 20 | menu_item_addon_mapping | Menu | 11 | Item-addon mapping |
| 21 | menu_item_variation | Menu | 12 | Item variations |
| 22 | menu_item_variation_mapping | Menu | 10 | Item-variation mapping |
| 23 | menu_item_attribute | Menu | 9 | Item attributes |
| 24 | menu_item_tag | Menu | 9 | Tag definitions |
| 25 | menu_item_tag_mapping | Menu | 9 | Item-tag mapping |
| 26 | menu_item_tax_mapping | Menu | 10 | Item-tax mapping |
| 27 | menu_item_discount_mapping | Menu | 10 | Item-discount mapping |
| 28 | menu_item_ordertype_mapping | Menu | 10 | Item-ordertype mapping |
| 29 | menu_item_option | Menu | 10 | Item options |
| 30 | menu_sync_log | Menu | 12 | Menu sync tracking |
| 31 | menu_version_history | Menu | 12 | Menu version history |
| 32 | order_type_table | Order | 9 | Order type definitions |
| 33 | order_source_type | Order | 9 | Order source definitions |
| 34 | order_status_type | Order | 11 | Order status definitions |
| 35 | orders | Order | 16 | Main orders table |
| 36 | order_item | Order | 29 | Order items |
| 37 | order_total | Order | 20 | Order totals |
| 38 | order_status_history | Order | 12 | Status history |
| 39 | order_charges | Order | 14 | Order charges |
| 40 | order_discount | Order | 13 | Order discounts |
| 41 | order_tax_line | Order | 13 | Order tax lines |
| 42 | order_customer_details | Order | 10 | Customer details |
| 43 | order_dining_info | Order | 12 | Dining info |
| 44 | order_delivery_info | Order | 23 | Delivery info |
| 45 | order_kitchen_detail | Order | 13 | Kitchen details |
| 46 | order_instruction | Order | 12 | Order instructions |
| 47 | order_note | Order | 13 | Order notes |
| 48 | order_scheduling | Order | 10 | Order scheduling |
| 49 | order_priority | Order | 10 | Order priority |
| 50 | order_invoice | Order | 14 | Invoice info |
| 51 | order_audit | Order | 12 | Order audit |
| 52 | order_integration_sync | Order | 11 | Integration sync |
| 53 | order_security_detail | Order | 12 | Security details |
| 54 | order_payment | Order | 10 | Order-payment link |
| 55 | order_payment_method | Order | 10 | Payment methods |
| 56 | payment_gateway | Payment | 10 | Gateway config |
| 57 | payment_status_type | Payment | 11 | Status definitions |
| 58 | payment_order | Payment | 23 | Payment orders |
| 59 | payment_transaction | Payment | 40 | Payment transactions |
| 60 | payment_refund | Payment | 25 | Refund records |
| 61 | payment_split | Payment | 18 | Split payments |
| 62 | payment_retry_attempt | Payment | 16 | Retry attempts |
| 63 | payment_audit_log | Payment | 21 | Audit logs |
| 64 | payment_webhook_log | Payment | 17 | Webhook logs |
| 65 | payment_external_mapping | Payment | 17 | External mappings |

---

*Document generated from A24_localdb database schema*
