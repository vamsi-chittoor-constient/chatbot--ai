# Complaints Module Feature

**Status:** 🔴 DORMANT (Not Implemented)

**Feature Flag:** `COMPLAINTS_MODULE` (always disabled)

## Purpose

Customer complaints and feedback management system for tracking, resolving, and learning from customer issues.

## Planned Features

### Complaint Registration
- **Multi-Channel Input**
  - Chatbot-reported complaints
  - Staff dashboard entry
  - Email integration
  - Phone call logging
  - Social media monitoring

- **Categorization**
  - Food quality issues
  - Service problems
  - Cleanliness concerns
  - Booking/reservation issues
  - Payment/billing disputes
  - Other

### Issue Tracking
- **Workflow Management**
  - New → Acknowledged → In Progress → Resolved → Closed
  - Auto-assignment to responsible staff
  - Escalation rules (unresolved > 24h → manager)
  - SLA tracking

- **Resolution Tools**
  - Suggested actions based on complaint type
  - Compensation options (discount, refund, free item)
  - Communication templates
  - Follow-up reminders

### Feedback Collection
- **Surveys**
  - Post-meal satisfaction surveys
  - Booking experience feedback
  - Staff service ratings
  - Facility cleanliness ratings

- **Sentiment Analysis**
  - NLP analysis of free-text feedback
  - Trend detection
  - Alert on negative patterns

### Analytics
- **Reports**
  - Complaint volume trends
  - Resolution time metrics
  - Repeat complaint tracking
  - Root cause analysis
  - Staff performance impact

- **Insights**
  - Common complaint patterns
  - Peak complaint times
  - High-risk menu items
  - Service improvement areas

## Implementation Plan

When this feature is activated:

1. **Service Layer** (`services/`)
   - `complaint_service.py` - Core complaint management
   - `feedback_service.py` - Survey and feedback handling
   - `resolution_service.py` - Resolution workflow
   - `sentiment_service.py` - NLP sentiment analysis

2. **Data Models** (`models/`)
   - Complaint records
   - Feedback surveys
   - Resolution actions
   - Escalation rules

3. **Crew Agent** (`crew_agent.py`)
   - LLM-based complaint understanding
   - Auto-categorization
   - Suggested resolution generation
   - Customer communication

4. **Integration Points**
   - Connect to chatbot for complaint detection
   - Link to staff dashboard for staff entry
   - Email/SMS notifications
   - CRM integration for customer history

## LLM-Based Features

The complaints module will leverage LLM capabilities:

1. **Complaint Detection**
   - Detect complaints in normal conversation
   - Example: "The food was cold" → Auto-register complaint

2. **Sentiment Analysis**
   - Analyze customer tone and urgency
   - Prioritize severe complaints

3. **Auto-Response Generation**
   - Generate empathetic acknowledgment messages
   - Suggest resolution actions
   - Draft apology/compensation offers

4. **Root Cause Analysis**
   - Analyze patterns across complaints
   - Identify systemic issues
   - Generate improvement recommendations

## Activation

To activate this feature in the future:

1. Implement the services, models, and crew agent
2. Change `Feature.COMPLAINTS_MODULE` in `feature_flags.py` from hardcoded `False` to env variable
3. Set environment variable: `export ENABLE_COMPLAINTS_MODULE=true`
4. Restart application

## Dependencies

- NLP/LLM service for sentiment analysis
- Email/SMS service for notifications
- Staff dashboard for manual entry
- CRM integration for customer history
- Database tables for complaint storage
