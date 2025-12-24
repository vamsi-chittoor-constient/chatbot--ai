# Staff Dashboard Feature

**Status:** 🔴 DORMANT (Not Implemented)

**Feature Flag:** `STAFF_DASHBOARD` (always disabled)

## Purpose

Staff management interface for restaurant operations across different roles.

## Planned Features

### Front Desk Role
- **Table Management**
  - View all table bookings
  - Manual table assignment
  - Walk-in customer registration
  - Check-in/check-out tracking

- **Order Management**
  - View active orders
  - Order status updates
  - Customer requests handling
  - Payment processing

- **Customer Service**
  - Customer profile lookup
  - Booking modifications
  - Complaint registration
  - Loyalty program management

### Manager Role
- **Operations Overview**
  - Real-time dashboard
  - Staff performance metrics
  - Inventory alerts
  - Revenue tracking

- **Configuration**
  - Menu updates
  - Table configuration
  - Pricing management
  - Special offers setup

- **Reports Access**
  - MIS reports viewing
  - Analytics dashboards
  - Performance analysis
  - Forecasting tools

### Housekeeping Role
- **Table Status**
  - Table cleaning status
  - Occupied/vacant tracking
  - Maintenance requests
  - Seating area readiness

- **Task Management**
  - Cleaning schedules
  - Task assignment
  - Completion tracking
  - Priority alerts

## Implementation Plan

When this feature is activated:

1. **Service Layer** (`services/`)
   - `staff_auth_service.py` - Role-based authentication
   - `task_management_service.py` - Staff task tracking
   - `notification_service.py` - Real-time staff alerts

2. **Data Models** (`models/`)
   - Staff profiles
   - Role permissions
   - Task assignments
   - Activity logs

3. **API Endpoints** (`routers/`)
   - Staff login/logout
   - Dashboard data
   - Task operations
   - Status updates

4. **Frontend** (separate React app)
   - Use existing hospitality-frontend from `latest code new/A24-hospitality-frontend-newschema`
   - Adapt to our backend API structure
   - Role-based UI rendering

## Activation

To activate this feature in the future:

1. Implement the services, models, and API endpoints
2. Change `Feature.STAFF_DASHBOARD` in `feature_flags.py` from hardcoded `False` to env variable
3. Set environment variable: `export ENABLE_STAFF_DASHBOARD=true`
4. Restart application

## Dependencies

- Authentication system (JWT tokens)
- Role-based access control (RBAC)
- WebSocket for real-time updates
- Frontend dashboard (React app)
- Staff database tables
