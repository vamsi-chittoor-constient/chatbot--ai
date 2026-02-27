# User Management Feature

Modern authentication and identity management system with specialized sub-agents.

## Overview

The user_management feature handles:
- User authentication (phone → OTP → verify → login/register)
- Session and device management
- User identity updates (name, email, phone)
- Device data migration

## Architecture

### Hierarchical Sub-Agent System

```
user_management_node (Entry Point)
    ↓
sub_intent_classifier
    ↓
┌──────────────────────────────────────────┐
│         Sub-Agent Router                 │
├──────────────────────────────────────────┤
│  authenticate → authenticator            │
│  manage_sessions → session_manager       │
│  migrate_identity → identity_migrator    │
│  update_identity → identity_manager      │
└──────────────────────────────────────────┘
```

### Sub-Agents

| Sub-Agent | Responsibility | Sub-Intents |
|-----------|---------------|-------------|
| **authenticator** | Complete authentication flow (phone → OTP → verify → create session) | authenticate |
| **session_manager** | Session/device management (view, revoke, rename) | manage_sessions |
| **identity_migrator** | Migrate anonymous device data to user account | migrate_identity |
| **identity_manager** | Update user identity information (name, email, phone) | update_identity |

## Sub-Intent Classification

The feature uses LLM-based classification to determine user intent:

```python
class SubIntentClassification(BaseModel):
    sub_intent: Literal[
        "authenticate",
        "manage_sessions",
        "migrate_identity",
        "update_identity"
    ]
    confidence: float
    entities: Dict[str, Any]
    missing_entities: List[str]
    reasoning: str
```

### Classification Examples

| User Message | Sub-Intent | Entities Extracted |
|--------------|------------|-------------------|
| "I want to login" | authenticate | - |
| "Send me an OTP" | authenticate | phone (if provided) |
| "My code is 1234" | authenticate | otp_code: "1234" |
| "Show my logged in devices" | manage_sessions | action: view |
| "Logout from all devices" | manage_sessions | action: revoke, revoke_all: true |
| "Transfer my cart after login" | migrate_identity | migration_type: cart |
| "Change my name to John" | update_identity | field: name, value: "John" |

## State Management

### AuthProgress Tracker

Central progress tracker for authentication flows:

```python
class AuthProgress(BaseModel):
    # User identification (3-tier)
    user_id: Optional[str] = None
    phone: Optional[str] = None
    device_id: Optional[str] = None

    # Authentication flow state
    phone_collected: bool = False
    otp_sent: bool = False
    otp_verified: bool = False
    user_authenticated: bool = False
    session_created: bool = False

    # OTP details
    otp_code: Optional[str] = None
    otp_send_count: int = 0
    otp_verification_attempts: int = 0
    locked_until: Optional[datetime] = None

    # User identity data
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_new_user: bool = False

    # Session management
    session_token: Optional[str] = None
    active_sessions: List[Dict[str, Any]] = []
    selected_session_id: Optional[str] = None

    # Identity migration
    migration_completed: bool = False
    migrated_data: Dict[str, Any] = {}
```

### Helper Methods

```python
# Check if phone is ready
if auth_progress.is_phone_ready():
    await send_otp(...)

# Check if OTP can be sent
if auth_progress.can_retry_otp():
    await send_otp(...)

# Check if locked
if auth_progress.is_locked():
    return error_message

# Mark as authenticated
auth_progress.mark_authenticated(user_id, session_token)

# Get user identifier (3-tier fallback)
user_identifier = auth_progress.get_user_identifier()
# Returns: user_id, phone, or device_id (first available)
```

## Tools

### OTP Tools (`tools/otp_tools.py`)

```python
# Send OTP to phone
await send_otp(
    phone_number="+1234567890",
    purpose="login"
)

# Verify OTP code
await verify_otp(
    phone_number="+1234567890",
    otp_code="123456",
    purpose="login"
)

# Check if user exists
await check_user_exists(
    phone_number="+1234567890"
)

# Create new user
await create_user(
    phone_number="+1234567890",
    full_name="John Doe",
    email="john@example.com"
)
```

### Session Tools (`tools/session_tools.py`)

```python
# Get active sessions
await get_active_sessions(user_id="user123")

# Revoke specific session
await revoke_session(
    user_id="user123",
    session_token="token456"
)

# Revoke all sessions
await revoke_session(
    user_id="user123",
    revoke_all=True
)

# Create new session
await create_session(
    user_id="user123",
    device_id="device456"
)

# Get user devices
await get_user_devices(user_id="user123")

# Update device name
await update_device_name(
    device_id="device456",
    device_name="iPhone 13",
    user_id="user123"
)
```

### Identity Tools (`tools/identity_tools.py`)

```python
# Get user identity
await get_user_identity(user_id="user123")

# Update user name
await update_user_name(
    user_id="user123",
    full_name="Jane Doe"
)

# Update email
await update_user_email(
    user_id="user123",
    email="jane@example.com"
)

# Update phone (requires verification)
await update_user_phone(
    user_id="user123",
    phone_number="+1234567890"
)

# Batch update
await update_user_profile(
    user_id="user123",
    full_name="Jane Doe",
    email="jane@example.com",
    phone_number="+1234567890"
)
```

### Migration Tools (`tools/migration_tools.py`)

```python
# Migrate device data
await migrate_device_data(
    user_id="user123",
    device_id="device456",
    migration_type="all"  # all, cart, favorites, history
)

# Get device data summary
await get_device_data_summary(device_id="device456")

# Link device to user
await link_device_to_user(
    user_id="user123",
    device_id="device456"
)
```

## Integration

### Orchestrator Routing

**Router Configuration** (`app/orchestration/nodes/router.py`):
```python
intent_agent_mapping = {
    "login": "user_management_agent",
    "register": "user_management_agent",
    "logout": "user_management_agent",
    "session_management": "user_management_agent",
    "update_identity": "user_management_agent",
    "migrate_data": "user_management_agent",
    # ...
}
```

**Graph Configuration** (`app/orchestration/graph.py`):
```python
from app.features.user_management import user_management_node as user_management_agent_node

workflow.add_node("user_management_agent", user_management_agent_node)
workflow.add_edge("user_management_agent", "response_agent")
```

### Entry Point

```python
from app.features.user_management import user_management_node

# Called by orchestrator
result = await user_management_node(state)

# Returns:
{
    "action": "login_successful",
    "success": True,
    "data": {
        "message": "Welcome back! You're now logged in.",
        "user_id": "user123",
        "session_token": "token456"
    },
    "context": {
        "authenticated": True,
        "is_new_user": False,
        "sub_intent": "authenticate",
        "confidence": 0.95
    }
}
```

## Sub-Agent Details

### 1. Authenticator

**File**: `agents/authenticator/node.py`

**Responsibility**: Complete authentication flow

**Features**:
- Phone number collection and validation
- OTP send with rate limiting
- OTP verification
- User lookup/creation
- Session creation
- New user registration

**Flow**:
```
1. Collect phone number
2. Send OTP (with rate limit check)
3. Verify OTP code
4. Check if user exists
   - Yes → Login (create session)
   - No → Register (collect name, create user, create session)
5. Return authentication result
```

**Example**:
```python
Input: "I want to login, my phone is +1234567890"
Entities: {"phone": "+1234567890"}

Output: {
    "action": "otp_sent",
    "success": True,
    "data": {
        "message": "Verification code sent to +1234567890. Please enter the code.",
        "phone": "+1234567890"
    }
}
```

### 2. Session Manager

**File**: `agents/session_manager/node.py`

**Responsibility**: Manage sessions and devices

**Features**:
- View all active sessions
- Revoke specific session (logout)
- Revoke all sessions (logout from all devices)
- View all user devices
- Rename devices

**Actions**:
- `view` - List all active sessions
- `devices` - List all registered devices
- `revoke` - Logout from specific session/device
- `rename` - Rename device for easier identification

**Example**:
```python
Input: "Show my logged in devices"
Entities: {"action": "view"}

Output: {
    "action": "sessions_listed",
    "success": True,
    "data": {
        "message": "You have 3 active sessions.",
        "sessions": [
            {
                "session_id": "sess1",
                "device_name": "iPhone 13",
                "created_at": "2025-01-15",
                "is_current": True
            },
            ...
        ],
        "count": 3
    }
}
```

### 3. Identity Migrator

**File**: `agents/identity_migrator/node.py`

**Responsibility**: Migrate anonymous device data

**Features**:
- Migrate shopping cart items
- Migrate favorite items
- Migrate browsing history
- Migrate device preferences
- Show migration summary

**Migration Types**:
- `all` - Migrate everything
- `cart` - Cart items only
- `favorites` - Favorites only
- `history` - Browsing history only

**Example**:
```python
Input: "Transfer my cart to my account"
Entities: {"migration_type": "cart"}

Output: {
    "action": "migration_successful",
    "success": True,
    "data": {
        "message": "Successfully migrated 5 cart item(s) to your account.",
        "migration_results": {
            "cart_items": 5,
            "favorites": 0,
            "history": 0
        },
        "total_items": 5
    }
}
```

### 4. Identity Manager

**File**: `agents/identity_manager/node.py`

**Responsibility**: Update user identity information

**Features**:
- Update full name
- Update email address
- Update phone number (with verification)
- Batch update multiple fields
- View current identity

**Actions**:
- `view` - Show current identity information
- `update` - Update name, email, or phone

**Example**:
```python
Input: "Change my name to Jane Doe"
Entities: {"field": "name", "value": "Jane Doe"}

Output: {
    "action": "identity_updated",
    "success": True,
    "data": {
        "message": "Name updated to 'Jane Doe'",
        "field": "name",
        "updated_value": "Jane Doe"
    }
}
```

## Response Format

All agents return standardized responses:

```python
{
    "action": str,              # Action type identifier
    "success": bool,            # Operation success status
    "data": {                   # Response data
        "message": str,         # User-facing message
        # ... additional data
    },
    "context": {                # Metadata
        "sub_intent": str,      # Sub-intent classification
        "confidence": float,    # Classification confidence
        # ... additional context
    }
}
```

## Common Flows

### Login Flow

```
1. User: "I want to login"
2. Sub-intent: authenticate
3. Entities: {}
4. Agent: authenticator
5. Actions:
   - Request phone number
   - Send OTP
   - Verify OTP
   - Create session
6. Response: "Welcome back! You're now logged in."
```

### Registration Flow

```
1. User: "I want to register"
2. Sub-intent: authenticate
3. Entities: {}
4. Agent: authenticator
5. Actions:
   - Request phone number
   - Send OTP
   - Verify OTP
   - Request full name
   - Create user
   - Create session
6. Response: "Welcome, John! Your account has been created."
```

### Session Management Flow

```
1. User: "Logout from all devices"
2. Sub-intent: manage_sessions
3. Entities: {action: "revoke", revoke_all: true}
4. Agent: session_manager
5. Actions:
   - Revoke all sessions for user
6. Response: "You have been logged out from all devices."
```

## Best Practices

1. **Always validate OTP attempts** to prevent brute force attacks
2. **Use rate limiting** for OTP sends (max 5 per session)
3. **Lock accounts** after too many failed attempts
4. **Require re-verification** when changing phone/email
5. **Auto-migrate device data** after successful authentication
6. **Log all authentication events** for security audit
7. **Use 3-tier authentication** (user_id → phone → device_id)
8. **Create long-lived session tokens** (30 days expiry)

## Security Features

- **OTP Rate Limiting**: Max 5 OTP sends per session
- **Account Lockout**: Temporary lock after too many failed attempts
- **Session Token Expiry**: 30-day expiry with auto-refresh
- **Multi-Device Support**: Track and manage multiple devices
- **Device Fingerprinting**: Identify devices for security
- **IP Tracking**: Log IP addresses for audit trail
- **Secure OTP Delivery**: SMS/email verification codes

## Configuration

### Environment Variables

```bash
# OTP settings
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=3
OTP_SEND_LIMIT_PER_DAY=10

# Session settings
SESSION_TOKEN_EXPIRY_DAYS=30
MAX_ACTIVE_SESSIONS_PER_USER=5

# Account lockout
LOCKOUT_DURATION_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
```

## Migration Notes

### From Legacy authentication_agent

The user_management feature replaces the legacy `authentication_agent`:

**Changes**:
- ✅ Split into 4 specialized sub-agents
- ✅ Added AuthProgress tracker for state management
- ✅ Added identity management (name, email, phone updates)
- ✅ Added device data migration
- ✅ Added sub-intent classification
- ✅ Improved session management

**Deprecation Timeline**:
- Current: user_management_agent active, authentication_agent marked deprecated
- Future: Remove authentication_agent completely

## Troubleshooting

### Common Issues

**Issue**: OTP not received
**Solution**: Check rate limiting, verify phone number format

**Issue**: OTP verification fails
**Solution**: Check OTP expiry, verify code is correct, check attempt count

**Issue**: Account locked
**Solution**: Wait for lockout duration to expire, check locked_until timestamp

**Issue**: Session creation fails
**Solution**: Verify device_id is provided, check session limit

**Issue**: Migration fails
**Solution**: Verify device has data to migrate, check device_id validity

## Future Enhancements

- [ ] Email/password authentication
- [ ] Social login (Google, Facebook, Apple)
- [ ] Biometric authentication
- [ ] Two-factor authentication (2FA)
- [ ] Security question recovery
- [ ] Email verification flow
- [ ] Password reset functionality
- [ ] Account deletion/deactivation

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Authentication Best Practices](https://owasp.org/www-project-top-ten/)
- [Structlog](https://www.structlog.org/)
