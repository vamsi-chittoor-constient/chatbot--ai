-- ============================================================================
-- Migration: Setup Petpooja Integration Configuration
-- ============================================================================
-- Purpose: Configure Petpooja integration for automatic menu sync
-- Date: 2025-12-28
-- ============================================================================

DO $$
DECLARE
    v_provider_id UUID;
    v_integration_config_id UUID;
    v_branch_id UUID;
    v_restaurant_id UUID;
    v_encryption_key TEXT := 'KsyO0fVY6eb4ZFE5r1GQY0TbUobTEQbbT0GZs4YBqXg='; -- From petpooja-service .env
BEGIN
    -- Get existing branch and restaurant IDs
    SELECT branch_id INTO v_branch_id
    FROM branch_info_table
    WHERE branch_name = 'Main Branch' AND is_deleted = FALSE;

    SELECT restaurant_id INTO v_restaurant_id
    FROM restaurant_table
    WHERE branch_id = v_branch_id AND is_deleted = FALSE;

    IF v_branch_id IS NULL OR v_restaurant_id IS NULL THEN
        RAISE EXCEPTION 'Branch or Restaurant not found';
    END IF;

    -- 1. Create Petpooja Integration Provider
    INSERT INTO integration_provider_table (
        provider_id, provider_name, provider_description,
        provider_base_url, created_at, updated_at, is_deleted
    )
    VALUES (
        gen_random_uuid(),
        'Petpooja',
        'Petpooja Restaurant Management System',
        'https://qle1yy2ydc.execute-api.ap-southeast-1.amazonaws.com/V1',
        NOW(),
        NOW(),
        FALSE
    )
    RETURNING provider_id INTO v_provider_id;

    RAISE NOTICE 'Created integration provider: %', v_provider_id;

    -- 2. Create Integration Config for the branch
    v_integration_config_id := gen_random_uuid();

    INSERT INTO integration_config_table (
        integration_config_id, chain_id, branch_id, provider_id,
        is_enabled, api_key, created_at, updated_at, is_deleted
    )
    VALUES (
        v_integration_config_id,
        NULL, -- chain_id is NULL when branch_id is set
        v_branch_id,
        v_provider_id,
        TRUE, -- Enable integration
        NULL, -- api_key not used for Petpooja
        NOW(),
        NOW(),
        FALSE
    );

    RAISE NOTICE 'Created integration config: %', v_integration_config_id;

    -- 3. Store Petpooja credentials (encrypted in production)
    -- Note: Using plaintext for now. In production, these should be encrypted.

    INSERT INTO integration_credentials_table (
        credential_id, integration_config_id, credential_key, credential_value,
        created_at, updated_at, is_deleted
    )
    VALUES
        (gen_random_uuid(), v_integration_config_id, 'app_key',
         '3b9pon1v6jgdhar7fxkmi8c0t54yewsz', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'app_secret',
         'e6ce04ec5ce5f9e166f42c486d12c23c06c3af2b', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'access_token',
         '7520a7d6cebbe30362b2bc0feca78c2d430a589f', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'restaurant_mapping_id',
         'czw6b9ykas', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'petpooja_restaurantid',
         'czw6b9ykas', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'restID',
         'czw6b9ykas', NOW(), NOW(), FALSE);

    RAISE NOTICE 'Stored Petpooja credentials';

    -- 4. Store integration metadata
    INSERT INTO integration_metadata_table (
        metadata_id, integration_config_id, metadata_key, metadata_value,
        created_at, updated_at, is_deleted
    )
    VALUES
        (gen_random_uuid(), v_integration_config_id, 'sandbox_enabled', 'true', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'business_type', 'restaurant', NOW(), NOW(), FALSE),
        (gen_random_uuid(), v_integration_config_id, 'system_provider', 'Petpooja', NOW(), NOW(), FALSE);

    RAISE NOTICE 'Stored integration metadata';

    -- 5. Update branch with Petpooja restaurant ID
    UPDATE branch_info_table
    SET updated_at = NOW()
    WHERE branch_id = v_branch_id;

    RAISE NOTICE 'Updated branch info';

    -- Summary
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Petpooja Integration Setup Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Provider ID: %', v_provider_id;
    RAISE NOTICE 'Integration Config ID: %', v_integration_config_id;
    RAISE NOTICE 'Branch ID: %', v_branch_id;
    RAISE NOTICE 'Restaurant ID: %', v_restaurant_id;
    RAISE NOTICE 'Restaurant Mapping ID: czw6b9ykas';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Next Step: Call Petpooja menu sync API';
    RAISE NOTICE '========================================';

END $$;

-- Verification
SELECT
    ip.provider_name,
    ic.integration_config_id,
    ic.is_enabled,
    b.branch_name,
    COUNT(icred.credential_id) as credential_count,
    COUNT(imeta.metadata_id) as metadata_count
FROM integration_config_table ic
JOIN integration_provider_table ip ON ic.provider_id = ip.provider_id
JOIN branch_info_table b ON ic.branch_id = b.branch_id
LEFT JOIN integration_credentials_table icred ON ic.integration_config_id = icred.integration_config_id
LEFT JOIN integration_metadata_table imeta ON ic.integration_config_id = imeta.integration_config_id
WHERE ic.is_deleted = FALSE
GROUP BY ip.provider_name, ic.integration_config_id, ic.is_enabled, b.branch_name;
