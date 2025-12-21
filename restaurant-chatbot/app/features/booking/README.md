# Booking Feature

## Overview

Complete table booking system with availability checking, creation, viewing, modification, and cancellation.

**Team Responsibilities:**
- Table availability management
- Booking creation with confirmation
- Booking viewing and history
- Booking modifications
- Booking cancellations

---

## Feature Structure

```
booking/
├── README.md              # This file
├── __init__.py           # Package exports
├── graph.py              # Sub-agent orchestration
├── state.py              # BookingState with BookingProgress tracker
├── node.py               # State wrapper for main orchestrator
├── cache.py              # Feature cache instance
├── logger.py             # Feature logger instance
│
├── agents/               # Sub-agents
│   ├── availability_checker/    # Check table availability
│   ├── booking_creator/         # Create new bookings
│   ├── booking_viewer/          # View existing bookings
│   ├── booking_modifier/        # Modify booking details
│   └── booking_canceller/       # Cancel bookings
│
├── tools/                # Booking tools (7 tools)
│   └── booking_tools.py
│
├── services/             # Booking services
│   └── (future services)
│
└── tests/                # Feature tests
```

---

## Database Models Used

From `app.shared.models`:
- **Booking**: Main booking record
- **Table**: Restaurant tables
- **User**: User information
- **Restaurant**: Restaurant configuration

---

## BookingProgress Tracker

**Location**: `state.py` → `BookingProgress` model

### Tracked Data:
```python
# Collected from user
- party_size: int
- date: str
- time: str
- special_requests: str

# Progress flags
- availability_checked: bool
- user_confirmed: bool
- booking_created: bool
- sms_sent: bool
- email_sent: bool

# Authentication
- phone: str
- user_id: str
- device_id: str
- user_name: str

# Results
- booking_id: str
- confirmation_code: str
- availability_result: dict
```

### Helper Methods:
- `is_ready_to_check_availability()` - Has party_size, date, time?
- `is_ready_to_create_booking()` - Has all required info + confirmed?
- `is_booking_complete()` - Booking created with confirmation?
- `get_missing_fields()` - List of missing required fields

---

## Sub-Agents

### 1. **availability_checker**
**Sub-intent**: `check_availability`

**Purpose**: Check if tables are available

**Flow**:
1. Collect party_size, date, time
2. Call `CheckAvailabilityTool`
3. Update `booking_progress.availability_result`
4. Present available tables

### 2. **booking_creator**
**Sub-intent**: `create_booking`

**Purpose**: Create new reservation

**Flow**:
1. Collect all required info (party_size, date, time, phone, name)
2. Check readiness via `booking_progress.is_ready_to_create_booking()`
3. Call `CreateBookingTool`
4. Update `booking_progress` with booking_id, confirmation_code
5. Mark `booking_created = True`, `sms_sent = True`

### 3. **booking_viewer**
**Sub-intent**: `view_bookings`

**Purpose**: View existing bookings

**Flow**:
1. Get user_id or phone from `booking_progress`
2. Call `GetBookingTool`
3. Display booking list

### 4. **booking_modifier**
**Sub-intent**: `modify_booking`

**Purpose**: Modify booking details

**Flow**:
1. Get `target_booking_id` from state
2. Get modifications from `modification_context`
3. Call `ModifyBookingTool`
4. Confirm changes

### 5. **booking_canceller**
**Sub-intent**: `cancel_booking`

**Purpose**: Cancel booking

**Flow**:
1. Get `target_booking_id` from state
2. Call `CancelBookingTool`
3. Confirm cancellation

---

## Tools (7 Tools)

| Tool | Purpose | Key Inputs | Output |
|------|---------|------------|--------|
| `CheckAvailabilityTool` | Check table availability | booking_date, party_size | Available tables list |
| `CreateBookingTool` | Create booking | booking_date, party_size, contact_phone | Booking with confirmation_code |
| `GetBookingTool` | Get bookings | booking_id/user_id/phone | Booking details |
| `UpdateBookingStatusTool` | Update status | booking_id, status | Updated booking |
| `CancelBookingTool` | Cancel booking | booking_id | Cancelled booking |
| `ModifyBookingTool` | Modify booking | booking_id, modifications | Modified booking |
| `GetBookingsByPhoneTool` | Get by phone | phone | Booking list |

---

## State Management

### BookingState Fields

```python
# Intent
current_intent: "booking"
current_sub_intent: str  # check_availability, create_booking, etc.

# Progress tracker (THE CORE!)
booking_progress: BookingProgress

# Contexts
booking_context: dict
availability_context: dict
modification_context: dict

# Operation
operation: str  # "create", "view", "modify", "cancel"
target_booking_id: str  # For view/modify/cancel
```

### Using BookingProgress

```python
# In sub-agent
booking_progress = state["booking_progress"]

# Check readiness
if booking_progress.is_ready_to_check_availability():
    # Call availability tool
    pass

# Update progress
booking_progress.availability_checked = True
booking_progress.availability_result = result.data

# Check completion
if booking_progress.is_booking_complete():
    # Flow ends
    pass
```

---

## Graph Orchestration

**Flow**:
```
User message
↓
classify_booking_sub_intent()  # Determine operation
↓
route_to_sub_agent()          # Route to appropriate agent
↓
Sub-agent executes            # Uses booking_progress
↓
should_continue_booking()     # Check if complete
↓
If complete → END
If not → Route again
```

---

## Cache Usage

```python
from app.features.booking.cache import booking_cache

# Cache availability
await booking_cache.set(
    entity="availability",
    identifier="2024-01-15:6pm",
    value=availability_data,
    ttl=1800  # 30 minutes
)

# Get cached availability
data = await booking_cache.get(
    entity="availability",
    identifier="2024-01-15:6pm"
)
```

---

## Logging

```python
from app.features.booking.logger import booking_logger

# All logs tagged with feature="booking"
booking_logger.info(
    "Booking created",
    booking_id=booking_id,
    confirmation_code=confirmation_code
)
```

---

## Development Guide

### Adding New Sub-Agent

1. Create folder: `agents/new_agent/`
2. Create `node.py` with `new_agent_node(state: BookingState)`
3. Add to `graph.py` routing
4. Add sub-intent to `BOOKING_SUB_INTENTS`

### Modifying BookingProgress

Edit `state.py` → `BookingProgress` model:
- Add new fields
- Add new helper methods
- Update `reset()` method

### Adding New Tool

1. Add to `tools/booking_tools.py`
2. Follow `ToolBase` pattern
3. Export in `tools/__init__.py`
4. Use in sub-agents

---

## Team Contacts

**Lead**: @booking-team-lead
**Developers**: @dev1, @dev2
**Production Support**: @production-team

---

## Related Documentation

- [Food Ordering Feature](../food_ordering/README.md) - Reference implementation
- [Agent State Documentation](../../../docs/AGENT_STATE.md)
- [Tools Documentation](../../../docs/TOOLS.md)
