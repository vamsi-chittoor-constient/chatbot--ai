# MIS Reporting Feature

**Status:** 🔴 DORMANT (Not Implemented)

**Feature Flag:** `MIS_REPORTING` (always disabled)

## Purpose

Management Information System (MIS) reporting and analytics for restaurant operations.

## Planned Features

### Reports
- **Order Analytics**
  - Daily/weekly/monthly order volumes
  - Peak hours analysis
  - Popular items tracking
  - Order type distribution (dine-in, takeout, delivery)

- **Revenue Reports**
  - Sales by time period
  - Revenue by menu category
  - Average order value trends
  - Payment method breakdown

- **Table Booking Analytics**
  - Booking conversion rates
  - Table utilization rates
  - Popular time slots
  - Cancellation patterns

- **Customer Insights**
  - Repeat customer rates
  - Customer lifetime value
  - Order frequency patterns
  - Preference analysis

### Dashboards
- Real-time operations dashboard
- Historical trends visualization
- Forecasting and predictions
- Custom report builder

## Implementation Plan

When this feature is activated:

1. **Service Layer** (`services/`)
   - `reporting_service.py` - Core reporting logic
   - `analytics_service.py` - Analytics calculations
   - `export_service.py` - Report export (PDF, Excel, CSV)

2. **Data Models** (`models/`)
   - Report templates
   - Analytics aggregations
   - Cached report results

3. **Integration**
   - Connect to existing order and booking data
   - Real-time event streaming for live dashboards
   - Scheduled report generation

4. **Frontend** (separate React app)
   - Use existing MIS frontend from `latest code new/A24-mis-report-newschema`
   - Adapt to our backend API structure

## Activation

To activate this feature in the future:

1. Implement the services and models
2. Change `Feature.MIS_REPORTING` in `feature_flags.py` from hardcoded `False` to env variable
3. Set environment variable: `export ENABLE_MIS_REPORTING=true`
4. Restart application

## Dependencies

- PostgreSQL for data storage
- Redis for report caching
- Background task queue for scheduled reports
- Frontend dashboard (React app)
