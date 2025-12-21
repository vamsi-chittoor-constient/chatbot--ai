# Restaurant Onboarding Guide

## Overview

The restaurant onboarding system allows you to register new restaurants with their PetPooja credentials. The system will:

1. **Encrypt and store** PetPooja credentials (app-key, app-secret, access-token)
2. **Fetch menu data** from PetPooja API automatically
3. **Save all data** to database (menu items, categories, taxes, addons, variations, etc.)
4. **Return sync summary** showing what was saved

## Security

All sensitive credentials are encrypted using **Fernet (AES-128-CBC)** encryption before storage. The encryption key is stored in the `.env` file as `ENCRYPTION_KEY`.

⚠️ **IMPORTANT**:
- Never commit the `ENCRYPTION_KEY` to git
- Use different keys for dev/staging/production
- Store production key in a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)

## API Endpoint

### POST `/api/restaurants/onboard`

Onboard a new restaurant with PetPooja credentials.

**Request Body:**
```json
{
  "restaurant_name": "A24 Restaurant",
  "email": "contact@a24restaurant.com",
  "phone_no": "9876543210",
  "app-key": "3b9pon1v6jgdhar7fxkmi8c0t54yewsz",
  "app-secret": "e6ce04ec5ce5f9e166f42c486d12c23c06c3af2b",
  "access-token": "7520a7d6cebbe30362b2bc0feca78c2d430a589f",
  "vendor_restaurant_id": "czw6b9ykas",
  "sandbox_enabled": true
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Restaurant onboarded successfully and menu data synced",
  "restaurant_id": 1,
  "vendor_restaurant_id": "czw6b9ykas",
  "menu_items_synced": 45,
  "categories_synced": 8,
  "taxes_synced": 4,
  "addons_synced": 12,
  "variations_synced": 6,
  "created_at": "2024-11-18T10:00:00Z"
}
```

**Response (Error):**
```json
{
  "detail": "Failed to fetch menu from PetPooja: Missing Authentication Token"
}
```

## Other Endpoints

### GET `/api/restaurants/list`
List all onboarded restaurants (credentials are NOT included in response)

**Query Parameters:**
- `status` (optional): Filter by status (active/inactive)

**Response:**
```json
[
  {
    "id": 1,
    "name": "A24 Restaurant",
    "email": "contact@a24restaurant.com",
    "phone_no": "9876543210",
    "vendor_restaurant_id": "czw6b9ykas",
    "sandbox_enabled": true,
    "is_active": true,
    "status": "active",
    "created_at": "2024-11-18T10:00:00Z",
    "last_sync_at": "2024-11-18T10:00:05Z"
  }
]
```

### GET `/api/restaurants/{restaurant_id}`
Get details of a specific restaurant

### DELETE `/api/restaurants/{restaurant_id}`
Soft delete a restaurant (sets status to inactive)

## Using Credentials in Code

When you need to use the credentials in your code, they will be automatically decrypted:

```python
from app.services.restaurant_service import get_decrypted_credentials
from app.core.db_session import get_db

# Get credentials for a restaurant
db = next(get_db())
credentials = await get_decrypted_credentials(
    db,
    restaurant_id=1  # or vendor_restaurant_id="czw6b9ykas"
)

# Use decrypted credentials
app_key = credentials["app-key"]
app_secret = credentials["app-secret"]
access_token = credentials["access-token"]
```

## Database Storage

Credentials are stored in the `restaurant_petpooja_credentials` table with the following columns:

- `app_key` - **ENCRYPTED** PetPooja app key
- `app_secret` - **ENCRYPTED** PetPooja app secret
- `access_token` - **ENCRYPTED** PetPooja access token
- `vendor_restaurant_id` - Plain text (not sensitive)
- `sandbox_enabled` - Boolean flag
- `is_active` - Active/inactive status

## Menu Data Saved

The onboarding process fetches and saves the following data:

| Data Type | Table | Description |
|-----------|-------|-------------|
| Restaurant | `restaurants` | Main restaurant record |
| Credentials | `restaurant_petpooja_credentials` | Encrypted PetPooja credentials |
| Branches | `restaurant_branches` | Restaurant branch/vendor details |
| Categories | `restaurants_item_categories_master` | Menu categories |
| Taxes | `restaurants_taxes_master` | Tax configurations |
| Attributes | `restaurants_item_attributes_master` | Item attributes (Veg/Non-Veg) |
| Order Types | `restaurants_item_order_types_master` | Order types (Delivery/Takeaway/Dine-in) |
| Variations | `restaurants_item_variations_master` | Item variations (Small/Medium/Large) |
| Addon Groups | `restaurants_addon_groups_master` | Addon groups |
| Addon Items | `restaurants_addon_groups_items` | Individual addon items |
| Discounts | `restaurants_discounts_master` | Discount configurations |
| Menu Items | `restaurants_menu_items` | All menu items with prices |
| Sync Logs | `petpooja_sync_logs` | Sync operation logs |

## Testing with cURL

```bash
# Onboard a restaurant
curl -X POST http://localhost:8001/api/restaurants/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_name": "A24 Restaurant",
    "email": "contact@a24restaurant.com",
    "phone_no": "9876543210",
    "app-key": "3b9pon1v6jgdhar7fxkmi8c0t54yewsz",
    "app-secret": "e6ce04ec5ce5f9e166f42c486d12c23c06c3af2b",
    "access-token": "7520a7d6cebbe30362b2bc0feca78c2d430a589f",
    "vendor_restaurant_id": "czw6b9ykas",
    "sandbox_enabled": true
  }'

# List all restaurants
curl http://localhost:8001/api/restaurants/list

# Get specific restaurant
curl http://localhost:8001/api/restaurants/1

# Delete restaurant
curl -X DELETE http://localhost:8001/api/restaurants/1
```

## Testing with Postman

1. Import the existing `A24_PetPooja_Integration.postman_collection.json`
2. Add a new request to the "Restaurants" folder
3. Set method to `POST`
4. URL: `{{base_url}}/api/restaurants/onboard`
5. Body: JSON with restaurant details (see example above)

## Error Handling

The system handles various errors:

| Error | Reason | Solution |
|-------|--------|----------|
| `Restaurant with vendor_restaurant_id 'xxx' already exists` | Duplicate restaurant | Use different vendor_restaurant_id |
| `Failed to fetch menu from PetPooja: Missing Authentication Token` | Invalid credentials or API issue | Check credentials, try production mode |
| `Database error` | Database connection issue | Check database connection in .env |
| `Failed to encrypt data` | Encryption key issue | Check ENCRYPTION_KEY in .env |

## Best Practices

1. **Always use HTTPS** in production for API requests
2. **Never log decrypted credentials** in production logs
3. **Rotate encryption keys** periodically
4. **Use environment-specific keys** (different for dev/staging/prod)
5. **Store production encryption key** in a secrets manager
6. **Monitor sync logs** for failures
7. **Set sandbox_enabled=false** when ready for production

## Encryption Key Management

### Generate New Key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Rotate Encryption Key

⚠️ **WARNING**: Changing the encryption key will make existing encrypted data unreadable!

If you need to rotate the key:

1. Export all decrypted credentials
2. Update `ENCRYPTION_KEY` in .env
3. Re-encrypt and save all credentials
4. Or run a migration script to decrypt with old key and re-encrypt with new key

## Troubleshooting

### Problem: "Invalid encryption key or data corrupted"
**Solution**: The ENCRYPTION_KEY was changed after data was encrypted. Restore the original key or re-onboard the restaurant.

### Problem: "Failed to fetch menu from PetPooja"
**Solution**:
1. Check if credentials are correct
2. Try switching `sandbox_enabled` to `false` for production API
3. Check PetPooja dashboard for API access status
4. Verify restaurant ID is correct

### Problem: "Database error"
**Solution**:
1. Check PostgreSQL is running
2. Verify database credentials in .env
3. Ensure database schema is up to date (run migrations)

## Support

For issues or questions:
1. Check application logs: `logs/petpooja_microservice.log`
2. Review sync logs in database: `petpooja_sync_logs` table
3. Test with Postman collection for debugging
4. Contact A24 development team
