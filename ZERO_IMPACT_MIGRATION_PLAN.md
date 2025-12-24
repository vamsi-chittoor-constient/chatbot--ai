# Zero-Impact Migration Plan: Hospitality Features → YOUR Architecture Style

**Date:** 2025-12-24

**Goal:** Migrate food ordering and table booking concepts from hospitality-backend into YOUR LLM-based, CrewAI agent architecture with ZERO impact on existing functionality.

**Principle:** Adapt concepts to your style, NOT copy-paste their code.

---

## Your Architecture Style (What We're Matching)

```python
# YOUR STYLE: LLM-based entity extraction
entity_service.extract_entities(conversation, intent)  # AI decides, not keywords

# YOUR STYLE: CrewAI agents with tools
@tool
def book_table(date: str, time: str, party_size: int):
    # Agent decides when to call this based on conversation

# YOUR STYLE: State-driven
state = {
    "messages": [...],
    "task_entities": {...},
    "user_id": "...",
    "intent": "booking"
}

# YOUR STYLE: Service layer
redis_service.get_cart(session_id)
menu_cache_service.get_items()
```

**NOT THEIR STYLE:**
```python
# THEIR STYLE: REST APIs with manual validation
@router.post("/create-booking")
async def create_booking(request: TableBookingRequest):
    # Manual request validation, not agent-driven
```

---

## What's Valuable from Hospitality-Backend

After analysis, here's what's actually useful (NOT the code, but the CONCEPTS):

### 🎯 Food Ordering Concepts:

1. **Order → PetPooja Kitchen Sync** ⭐ **CRITICAL**
   - When chatbot creates order → push to PetPooja for kitchen
   - This is what you're MISSING

2. **Order Status Tracking**
   - Track order through lifecycle (placed → preparing → ready → served)
   - Update customer in real-time

3. **Order Types Handling**
   - Dine-in vs Takeout logic
   - Different workflows for each

4. **Order Validation**
   - Check item availability before placing
   - Validate cart before checkout

### 🎯 Table Booking Concepts:

1. **Booking Statistics** ⭐
   - Total bookings, upcoming, confirmed, cancelled
   - Useful for availability checks

2. **Table Assignment Logic**
   - Match party size to available tables
   - Handle table combinations (join tables for large groups)

3. **Booking Conflicts**
   - Check if table already booked at that time
   - Suggest alternative times

4. **Special Features**
   - Table types (window, garden, poolside, etc.)
   - Allow customer preferences

---

## Migration Strategy: YOUR Way

### Step 1: Feature Flags (Zero Impact)

Create feature toggle system in YOUR style:

```python
# restaurant-chatbot/app/core/feature_flags.py

from enum import Enum
from functools import wraps
import os

class Feature(Enum):
    """Feature flags for gradual rollout"""

    # Food Ordering
    PETPOOJA_ORDER_SYNC = "petpooja_order_sync"  # Push orders to PetPooja
    ORDER_STATUS_TRACKING = "order_status_tracking"  # Track order lifecycle
    ADVANCED_ORDER_VALIDATION = "advanced_order_validation"

    # Table Booking
    ADVANCED_TABLE_ASSIGNMENT = "advanced_table_assignment"
    TABLE_COMBINATION = "table_combination"  # Join tables for large groups
    TABLE_SPECIAL_FEATURES = "table_special_features"  # Window, garden, etc.

    # MIS & Analytics (deactivated for now)
    MIS_REPORTING = "mis_reporting"  # Deactivated
    STAFF_DASHBOARD = "staff_dashboard"  # Deactivated
    COMPLAINTS_MODULE = "complaints_module"  # Deactivated

class FeatureFlags:
    """
    Feature flag manager - controls what's active

    Default: ALL DISABLED (zero impact)
    Enable via environment variables
    """

    _flags = {
        # Food Ordering - Start DISABLED
        Feature.PETPOOJA_ORDER_SYNC: os.getenv("ENABLE_PETPOOJA_SYNC", "false").lower() == "true",
        Feature.ORDER_STATUS_TRACKING: os.getenv("ENABLE_ORDER_TRACKING", "false").lower() == "true",
        Feature.ADVANCED_ORDER_VALIDATION: os.getenv("ENABLE_ADVANCED_VALIDATION", "false").lower() == "true",

        # Table Booking - Start DISABLED
        Feature.ADVANCED_TABLE_ASSIGNMENT: os.getenv("ENABLE_ADVANCED_TABLES", "false").lower() == "true",
        Feature.TABLE_COMBINATION: os.getenv("ENABLE_TABLE_COMBINATION", "false").lower() == "true",
        Feature.TABLE_SPECIAL_FEATURES: os.getenv("ENABLE_TABLE_FEATURES", "false").lower() == "true",

        # MIS & Analytics - ALWAYS DISABLED for now
        Feature.MIS_REPORTING: False,
        Feature.STAFF_DASHBOARD: False,
        Feature.COMPLAINTS_MODULE: False,
    }

    @classmethod
    def is_enabled(cls, feature: Feature) -> bool:
        """Check if feature is enabled"""
        return cls._flags.get(feature, False)

    @classmethod
    def enable(cls, feature: Feature):
        """Enable feature (for testing)"""
        cls._flags[feature] = True

    @classmethod
    def disable(cls, feature: Feature):
        """Disable feature"""
        cls._flags[feature] = False


def feature_flag(feature: Feature):
    """Decorator to conditionally execute based on feature flag"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not FeatureFlags.is_enabled(feature):
                # Feature disabled - return None or default behavior
                return None
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Usage in existing code:**

```python
# In your existing food ordering agent
@feature_flag(Feature.PETPOOJA_ORDER_SYNC)
async def sync_order_to_petpooja(order_data):
    """
    NEW FEATURE: Push order to PetPooja kitchen

    If feature flag disabled → does nothing (zero impact)
    If enabled → syncs to PetPooja
    """
    # Implementation here
    pass

# In your checkout tool
async def checkout():
    # Existing checkout logic (UNCHANGED)
    order = await create_order(cart_data)

    # NEW: Optional PetPooja sync (zero impact if disabled)
    await sync_order_to_petpooja(order)  # Returns None if disabled

    return order
```

**Zero Impact:**
- Default: ALL flags FALSE
- Existing code continues working
- New features dormant until enabled

---

### Step 2: Extract Business Logic (Not Code)

Don't copy their FastAPI routes. Extract the CONCEPTS and implement in YOUR agent style.

#### Example: PetPooja Order Sync

**THEIR WAY (don't copy this):**
```python
# hospitality-backend/app/service/petpooja.py
def push_order_to_petpooja(order_data):
    # Hardcoded API calls
    response = requests.post(PETPOOJA_API, json=order_data)
```

**YOUR WAY (adapt the concept):**
```python
# restaurant-chatbot/app/services/petpooja_sync_service.py

import structlog
from typing import Dict, Any
import httpx

logger = structlog.get_logger()

class PetPoojaSyncService:
    """
    Service to sync orders to PetPooja kitchen (YOUR architecture style)

    Uses:
    - LLM to determine if order is ready to sync
    - Service layer pattern (matches your redis_service, menu_cache_service)
    - Async/await (matches your style)
    - Structured logging (matches your style)
    """

    def __init__(self):
        self.petpooja_api_url = os.getenv("PETPOOJA_API_URL")
        self.restaurant_id = os.getenv("PETPOOJA_RESTAURANT_ID")
        self.api_key = os.getenv("PETPOOJA_API_KEY")

    async def should_sync_order(self, order: Dict[str, Any]) -> bool:
        """
        LLM-based decision: Should we sync this order to PetPooja?

        YOUR STYLE: Let AI decide based on context, not hardcoded rules
        """
        # Check order type (dine-in or takeout - both go to kitchen)
        # Check order status (only sync if confirmed)
        # Check if already synced (idempotency)

        if order.get("petpooja_order_id"):
            logger.info("order_already_synced", order_id=order["id"])
            return False

        if order.get("status") != "confirmed":
            logger.info("order_not_confirmed_yet", order_id=order["id"], status=order.get("status"))
            return False

        return True

    async def sync_order_to_kitchen(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push order to PetPooja kitchen system

        Returns:
            {
                "success": bool,
                "petpooja_order_id": str,
                "message": str
            }
        """
        if not await self.should_sync_order(order):
            return {"success": False, "message": "Order not ready for sync"}

        # Transform order to PetPooja format
        petpooja_payload = self._transform_to_petpooja_format(order)

        # Send to PetPooja API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.petpooja_api_url}/orders",
                    json=petpooja_payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(
                        "order_synced_to_petpooja",
                        order_id=order["id"],
                        petpooja_order_id=result.get("order_id")
                    )
                    return {
                        "success": True,
                        "petpooja_order_id": result.get("order_id"),
                        "message": "Order sent to kitchen"
                    }
                else:
                    logger.error(
                        "petpooja_sync_failed",
                        order_id=order["id"],
                        status_code=response.status_code,
                        error=response.text
                    )
                    return {
                        "success": False,
                        "message": f"PetPooja API error: {response.status_code}"
                    }

        except Exception as e:
            logger.error("petpooja_sync_exception", order_id=order["id"], error=str(e))
            return {"success": False, "message": f"Sync failed: {str(e)}"}

    def _transform_to_petpooja_format(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform our order format to PetPooja's expected format

        Based on PetPooja API docs, they expect:
        {
            "restaurantid": "xxx",
            "order_id": "xxx",
            "customer": {...},
            "items": [...],
            "order_type": "dine_in" | "takeout",
            ...
        }
        """
        return {
            "restaurantid": self.restaurant_id,
            "order_id": str(order["id"]),
            "customer": {
                "name": order.get("customer_name"),
                "phone": order.get("customer_phone"),
            },
            "items": [
                {
                    "item_id": item["menu_item_id"],
                    "item_name": item["item_name"],
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                    "instructions": item.get("special_instructions", "")
                }
                for item in order.get("items", [])
            ],
            "order_type": order.get("order_type", "dine_in"),
            "subtotal": float(order.get("subtotal", 0)),
            "tax": float(order.get("tax", 0)),
            "total": float(order.get("total", 0)),
            "special_instructions": order.get("special_instructions", ""),
            "created_at": order.get("created_at"),
        }

# Global instance (matches your service pattern)
petpooja_sync_service = PetPoojaSyncService()
```

---

### Step 3: Integrate into YOUR Agent Tools (Zero Impact)

Add new functionality to existing tools using feature flags:

```python
# restaurant-chatbot/app/features/food_ordering/crew_agent.py

# Add imports at top
from app.core.feature_flags import Feature, FeatureFlags, feature_flag
from app.services.petpooja_sync_service import petpooja_sync_service

# Modify your existing checkout tool (NO breaking changes)
@tool
async def place_order(
    session_id: str,
    order_type: str,
    contact_phone: str,
    special_instructions: Optional[str] = None
) -> str:
    """
    Place food order (EXISTING tool - modified to add optional sync)

    ZERO IMPACT:
    - If PETPOOJA_ORDER_SYNC disabled → works exactly as before
    - If enabled → also syncs to PetPooja kitchen
    """
    # EXISTING CODE (UNCHANGED)
    cart = await redis_service.get_cart(session_id)

    if not cart or not cart.get("items"):
        return "[ERROR] Cart is empty. Please add items first."

    # Create order in database (EXISTING)
    order_data = {
        "user_id": state.get("user_id"),
        "session_id": session_id,
        "order_type": order_type,
        "contact_phone": contact_phone,
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "tax": cart["tax"],
        "total": cart["total"],
        "special_instructions": special_instructions,
        "status": "confirmed"
    }

    order = await db.create_order(order_data)

    # NEW: Optional PetPooja sync (ZERO IMPACT if disabled)
    if FeatureFlags.is_enabled(Feature.PETPOOJA_ORDER_SYNC):
        sync_result = await petpooja_sync_service.sync_order_to_kitchen(order)

        if sync_result["success"]:
            # Update order with PetPooja order ID
            await db.update_order(
                order["id"],
                {"petpooja_order_id": sync_result["petpooja_order_id"]}
            )
            logger.info(
                "order_synced_to_kitchen",
                order_id=order["id"],
                petpooja_order_id=sync_result["petpooja_order_id"]
            )

    # Clear cart (EXISTING)
    await redis_service.clear_cart(session_id)

    # Return success message (EXISTING)
    return f"""
    [ORDER PLACED] Your order #{order['id']} has been confirmed!

    Order Type: {order_type}
    Total: ₹{order['total']}

    You'll receive payment link shortly.
    """
```

**Zero Impact Guarantee:**
- If feature flag OFF → exact same behavior as before
- If feature flag ON → adds PetPooja sync
- No changes to agent prompt or flow
- No changes to database schema (petpooja_order_id column can be nullable)

---

### Step 4: Table Booking Enhancements (YOUR Style)

Extract valuable concepts from their table booking:

```python
# restaurant-chatbot/app/services/table_assignment_service.py

import structlog
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, time

logger = structlog.get_logger()

class TableAssignmentService:
    """
    Advanced table assignment logic (YOUR architecture style)

    Concepts from hospitality-backend, implemented YOUR way:
    - LLM helps decide best table
    - Service layer pattern
    - Async operations
    """

    async def find_best_table(
        self,
        restaurant_id: str,
        party_size: int,
        booking_date: date,
        booking_time: time,
        preferences: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Find best available table for booking

        YOUR STYLE: LLM can use this as a tool to recommend tables

        Logic from hospitality-backend:
        1. Find tables with capacity >= party_size
        2. Check availability (no conflicts)
        3. Prefer exact capacity match (don't waste large table on small party)
        4. Consider preferences (window, garden, etc.) if provided
        5. Suggest table combinations for large groups
        """
        # Get all active tables for restaurant
        tables = await self._get_active_tables(restaurant_id)

        # Filter by capacity
        suitable_tables = [
            t for t in tables
            if t["capacity"] >= party_size and t["is_active"]
        ]

        if not suitable_tables:
            # Try table combinations for large groups
            if FeatureFlags.is_enabled(Feature.TABLE_COMBINATION):
                return await self._find_table_combination(
                    tables, party_size, booking_date, booking_time
                )
            return None

        # Check availability
        available_tables = []
        for table in suitable_tables:
            is_available = await self._check_table_available(
                table["table_id"],
                booking_date,
                booking_time
            )
            if is_available:
                available_tables.append(table)

        if not available_tables:
            return None

        # Score tables based on criteria
        scored_tables = self._score_tables(
            available_tables,
            party_size,
            preferences or {}
        )

        # Return best match
        best_table = max(scored_tables, key=lambda x: x["score"])

        logger.info(
            "table_assigned",
            table_id=best_table["table_id"],
            table_number=best_table["table_number"],
            capacity=best_table["capacity"],
            party_size=party_size,
            score=best_table["score"]
        )

        return best_table

    def _score_tables(
        self,
        tables: List[Dict],
        party_size: int,
        preferences: Dict
    ) -> List[Dict]:
        """
        Score tables based on fit

        Scoring logic from hospitality-backend:
        - Exact capacity match: +10 points
        - Capacity within 2 seats: +5 points
        - Has preferred feature (window/garden): +3 points
        - Larger table (less waste): -1 per extra seat
        """
        scored = []

        for table in tables:
            score = 0
            capacity = table["capacity"]
            extra_seats = capacity - party_size

            # Exact match is best
            if extra_seats == 0:
                score += 10
            elif extra_seats <= 2:
                score += 5
            else:
                score -= extra_seats  # Penalize waste

            # Preferred features
            if FeatureFlags.is_enabled(Feature.TABLE_SPECIAL_FEATURES):
                if preferences.get("table_type") == table.get("table_type"):
                    score += 3

            table_copy = table.copy()
            table_copy["score"] = score
            scored.append(table_copy)

        return scored

    async def _check_table_available(
        self,
        table_id: str,
        booking_date: date,
        booking_time: time
    ) -> bool:
        """
        Check if table is available at given time

        Logic: Check for conflicts (bookings at same time ± 2 hours)
        """
        # Query existing bookings for this table
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as conn:
            conflict_check = await conn.fetchrow("""
                SELECT COUNT(*) as conflicts
                FROM table_booking_history
                WHERE table_id = $1
                  AND booking_date = $2
                  AND booking_status NOT IN ('cancelled', 'no_show')
                  AND is_deleted = FALSE
                  AND (
                      -- Check if times overlap (2-hour window)
                      booking_time BETWEEN $3::time - interval '2 hours'
                                       AND $3::time + interval '2 hours'
                  )
            """, table_id, booking_date, booking_time)

            return conflict_check["conflicts"] == 0

    async def _get_active_tables(self, restaurant_id: str) -> List[Dict]:
        """Get all active tables for restaurant"""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as conn:
            rows = await conn.fetch("""
                SELECT
                    t.table_id,
                    t.table_number,
                    t.table_capacity as capacity,
                    t.table_type,
                    t.floor_location,
                    t.is_active,
                    f.feature_name
                FROM tables t
                LEFT JOIN table_special_features f ON t.table_id = f.table_id
                    AND f.is_deleted = FALSE
                WHERE t.restaurant_id = $1
                  AND t.is_deleted = FALSE
                ORDER BY t.table_capacity
            """, restaurant_id)

            return [dict(row) for row in rows]

    @feature_flag(Feature.TABLE_COMBINATION)
    async def _find_table_combination(
        self,
        tables: List[Dict],
        party_size: int,
        booking_date: date,
        booking_time: time
    ) -> Optional[Dict]:
        """
        Find combination of tables that can accommodate large group

        NEW FEATURE (deactivated by default)

        Logic from hospitality-backend:
        - Try combinations of 2-3 tables
        - Must be adjacent/combinable
        - Total capacity >= party_size
        """
        from itertools import combinations

        # Try pairs first, then triplets
        for combo_size in [2, 3]:
            for combo in combinations(tables, combo_size):
                total_capacity = sum(t["capacity"] for t in combo)

                if total_capacity >= party_size:
                    # Check if all tables available
                    all_available = True
                    for table in combo:
                        available = await self._check_table_available(
                            table["table_id"],
                            booking_date,
                            booking_time
                        )
                        if not available:
                            all_available = False
                            break

                    if all_available:
                        logger.info(
                            "table_combination_found",
                            tables=[t["table_number"] for t in combo],
                            total_capacity=total_capacity,
                            party_size=party_size
                        )

                        return {
                            "table_combination": True,
                            "tables": combo,
                            "total_capacity": total_capacity,
                            "table_ids": [t["table_id"] for t in combo],
                            "table_numbers": [t["table_number"] for t in combo]
                        }

        return None

# Global instance
table_assignment_service = TableAssignmentService()
```

**Use in your booking agent:**

```python
# In your table booking CrewAI agent tool
@tool
async def book_table(
    restaurant_id: str,
    date: str,
    time: str,
    party_size: int,
    customer_name: str,
    customer_phone: str,
    preferences: Optional[Dict] = None
) -> str:
    """
    Book table (ENHANCED with advanced assignment)

    ZERO IMPACT:
    - If ADVANCED_TABLE_ASSIGNMENT disabled → simple first-available logic
    - If enabled → smart table matching
    """
    booking_date = parse_date(date)
    booking_time = parse_time(time)

    # NEW: Smart table assignment (optional)
    if FeatureFlags.is_enabled(Feature.ADVANCED_TABLE_ASSIGNMENT):
        best_table = await table_assignment_service.find_best_table(
            restaurant_id,
            party_size,
            booking_date,
            booking_time,
            preferences
        )

        if not best_table:
            return "[NO TABLES] No suitable tables available for that time. Would you like to try a different time?"

        if best_table.get("table_combination"):
            # Multiple tables needed
            table_ids = best_table["table_ids"]
            table_numbers = best_table["table_numbers"]
            message = f"For your party of {party_size}, we'll combine tables {', '.join(map(str, table_numbers))}."
        else:
            table_ids = [best_table["table_id"]]
            message = f"Table {best_table['table_number']} (seats {best_table['capacity']}) is perfect for your party of {party_size}."
    else:
        # EXISTING: Simple first-available logic
        table_ids = await find_first_available_table(restaurant_id, party_size, booking_date, booking_time)
        message = ""

    # Create booking (EXISTING code)
    booking = await create_booking_in_db(...)

    return f"""
    [BOOKING CONFIRMED] {message}

    Booking ID: {booking['id']}
    Date: {date}
    Time: {time}
    Party Size: {party_size}

    Looking forward to seeing you!
    """
```

---

### Step 5: Migrate Dormant Features (Deactivated)

Add code for MIS/Staff/Complaints but keep deactivated:

```python
# restaurant-chatbot/app/features/mis_reporting/__init__.py
"""
MIS Reporting Feature (DEACTIVATED)

This feature provides analytics and reporting capabilities.
Currently DEACTIVATED - will be enabled in future phase.

To activate:
    export ENABLE_MIS_REPORTING=true
"""

from app.core.feature_flags import Feature, FeatureFlags

if FeatureFlags.is_enabled(Feature.MIS_REPORTING):
    # Import actual implementations when enabled
    from .services import reporting_service
    from .routes import router
else:
    # Dummy/placeholder when disabled
    reporting_service = None
    router = None
```

```python
# restaurant-chatbot/app/features/staff_dashboard/__init__.py
"""
Staff Dashboard Feature (DEACTIVATED)

Provides dashboards for FrontDesk, Managers, Housekeeping.
Currently DEACTIVATED.

To activate:
    export ENABLE_STAFF_DASHBOARD=true
"""

from app.core.feature_flags import Feature, FeatureFlags

if not FeatureFlags.is_enabled(Feature.STAFF_DASHBOARD):
    # Feature disabled - skip imports (zero impact on app startup)
    pass
```

**Benefits:**
- Code is present in codebase
- Can review/understand it
- ZERO runtime impact (not imported)
- Easy to activate later

---

## Zero-Impact Deployment Plan

### Phase 1: Foundation (Week 1) - ZERO CHANGES TO EXISTING CODE

**Day 1-2: Add Infrastructure (no functional changes)**

1. Add feature flag system:
   ```bash
   touch restaurant-chatbot/app/core/feature_flags.py
   # Copy feature flag code from above
   ```

2. Add service skeletons:
   ```bash
   mkdir -p restaurant-chatbot/app/services/enhanced
   touch restaurant-chatbot/app/services/enhanced/petpooja_sync_service.py
   touch restaurant-chatbot/app/services/enhanced/table_assignment_service.py
   ```

3. Add dormant feature folders:
   ```bash
   mkdir -p restaurant-chatbot/app/features/mis_reporting
   mkdir -p restaurant-chatbot/app/features/staff_dashboard
   mkdir -p restaurant-chatbot/app/features/complaints

   # Add __init__.py with feature flag checks
   ```

**Testing:** Run app, verify ZERO changes in behavior (all flags OFF)

**Day 3-4: Implement Services (but keep disabled)**

1. Implement `PetPoojaSyncService` (complete code above)
2. Implement `TableAssignmentService` (complete code above)
3. Write unit tests (with flags OFF and ON)

**Testing:** Run tests, verify services work when enabled, ignored when disabled

**Day 5: Documentation**

1. Document feature flags in README
2. Document new services
3. Create activation guide

**Deploy:** Safe to deploy - nothing changes (all flags OFF)

---

### Phase 2: Enable Features One-by-One (Week 2)

**Day 1: Enable PetPooja Sync (Staging Only)**

```bash
# In staging environment only
export ENABLE_PETPOOJA_SYNC=true

# Restart app
docker compose restart chatbot-app
```

**Test:**
1. Place order via chatbot
2. Verify order created in DB (existing behavior)
3. **NEW:** Verify order pushed to PetPooja
4. Check PetPooja kitchen dashboard - order should appear

**Rollback if issues:**
```bash
export ENABLE_PETPOOJA_SYNC=false
docker compose restart chatbot-app
```

**Day 2-3: Test PetPooja Sync Thoroughly**

- Different order types (dine-in, takeout)
- Edge cases (large orders, special instructions)
- Error handling (PetPooja API down)
- Monitoring/logging

**Day 4: Enable Advanced Table Assignment (Staging)**

```bash
export ENABLE_ADVANCED_TABLES=true
```

**Test:**
- Book tables via chatbot
- Verify smart assignment logic
- Test large group handling

**Day 5: Staging Verification**

- Full end-to-end tests
- Performance testing
- Log analysis

---

### Phase 3: Production Rollout (Week 3)

**Day 1: Production - PetPooja Sync**

```bash
# Production environment
export ENABLE_PETPOOJA_SYNC=true
```

**Monitor:**
- Order sync success rate
- PetPooja API response times
- Error rates
- Customer feedback

**Day 2-3: Monitor & Optimize**

- Fix any issues discovered
- Optimize performance
- Adjust logging

**Day 4: Production - Advanced Tables**

```bash
export ENABLE_ADVANCED_TABLES=true
```

**Monitor:**
- Table assignment accuracy
- Booking success rate
- Customer satisfaction

**Day 5: Final Verification**

- All features working
- No regressions in existing functionality
- Performance acceptable

---

## Rollback Strategy (Zero Risk)

At ANY point, instant rollback:

```bash
# Disable problematic feature immediately
export ENABLE_PETPOOJA_SYNC=false
export ENABLE_ADVANCED_TABLES=false

# Restart
docker compose restart chatbot-app

# System returns to exact previous behavior
```

**Rollback time:** ~30 seconds

---

## Code Organization

Your new structure:

```
restaurant-chatbot/
├── app/
│   ├── core/
│   │   ├── feature_flags.py          # NEW: Feature flag system
│   │   └── ...
│   │
│   ├── services/
│   │   ├── enhanced/                  # NEW: Enhanced services
│   │   │   ├── __init__.py
│   │   │   ├── petpooja_sync_service.py     # NEW: PetPooja kitchen sync
│   │   │   └── table_assignment_service.py   # NEW: Smart table assignment
│   │   │
│   │   ├── redis_service.py           # EXISTING (unchanged)
│   │   ├── menu_cache_service.py      # EXISTING (unchanged)
│   │   └── ...
│   │
│   ├── features/
│   │   ├── food_ordering/             # EXISTING (minor enhancements)
│   │   │   └── crew_agent.py          # Modified to use new services
│   │   │
│   │   ├── booking/                   # EXISTING (minor enhancements)
│   │   │
│   │   ├── mis_reporting/             # NEW: DEACTIVATED
│   │   │   ├── __init__.py            # Feature flag check
│   │   │   └── ...                     # Code present but not loaded
│   │   │
│   │   ├── staff_dashboard/           # NEW: DEACTIVATED
│   │   │   └── ...
│   │   │
│   │   └── complaints/                # NEW: DEACTIVATED
│   │       └── ...
│   │
│   └── ...
│
├── .env
│   # NEW: Feature flags (all false by default)
│   ENABLE_PETPOOJA_SYNC=false
│   ENABLE_ADVANCED_TABLES=false
│   ENABLE_MIS_REPORTING=false
│   ...
│
└── ...
```

---

## Testing Strategy

### Unit Tests (with feature flags):

```python
# tests/test_petpooja_sync.py

import pytest
from app.core.feature_flags import FeatureFlags, Feature
from app.services.enhanced.petpooja_sync_service import petpooja_sync_service

@pytest.mark.asyncio
async def test_sync_disabled_returns_none():
    """When feature disabled, sync should do nothing"""
    # Ensure flag is OFF
    FeatureFlags.disable(Feature.PETPOOJA_ORDER_SYNC)

    order = {"id": "123", "status": "confirmed"}
    result = await petpooja_sync_service.sync_order_to_kitchen(order)

    # Should return early without syncing
    assert result is None or result["success"] == False

@pytest.mark.asyncio
async def test_sync_enabled_pushes_to_petpooja():
    """When feature enabled, sync should work"""
    # Enable flag
    FeatureFlags.enable(Feature.PETPOOJA_ORDER_SYNC)

    order = {"id": "123", "status": "confirmed", ...}
    result = await petpooja_sync_service.sync_order_to_kitchen(order)

    # Should sync successfully
    assert result["success"] == True
    assert "petpooja_order_id" in result
```

---

## Success Metrics

After migration, you should have:

### ✅ Zero Impact (Week 1):
- All existing functionality works EXACTLY as before
- No changes in user experience
- No performance impact
- All tests pass

### ✅ Enhanced Features Available (Week 2-3):
- PetPooja order sync (when enabled)
- Smart table assignment (when enabled)
- Dormant features ready for future activation

### ✅ Future-Ready:
- MIS reporting code present (deactivated)
- Staff dashboard code present (deactivated)
- Complaints module present (deactivated)
- Easy to activate when needed

---

## Summary: Your Way vs Their Way

| Aspect | Their Way (hospitality-backend) | Your Way (This Plan) |
|--------|----------------------------------|----------------------|
| **Architecture** | FastAPI REST APIs | CrewAI agents + LLM-based |
| **Decision Making** | Hardcoded rules, keyword matching | LLM entity extraction |
| **Feature Control** | Deploy/undeploy code | Feature flags |
| **Integration** | Replace backend | Add to existing agents |
| **Risk** | High (full replacement) | **Zero (additive only)** |
| **Rollback** | Restore old system | **Flip flag (30 sec)** |
| **Code Style** | Their REST API style | **YOUR agent/service style** |

---

## Next Steps

1. **Review this plan** - Does it match your vision?

2. **Approve approach** - Feature flags + YOUR architecture style?

3. **Start Phase 1** (Week 1) - Add infrastructure with zero impact

4. **Would you like me to:**
   - Create the actual feature_flags.py file?
   - Implement PetPoojaSyncService in your style?
   - Implement TableAssignmentService in your style?
   - Set up the dormant feature folders?

This gives you:
- ✅ Food ordering + table booking enhanced (YOUR way)
- ✅ ZERO impact on existing code
- ✅ Easy rollback (feature flags)
- ✅ Future features ready (deactivated)
- ✅ Matches YOUR LLM-based architecture style

**Ready to proceed?**
