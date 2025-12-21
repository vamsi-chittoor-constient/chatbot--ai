# Feedback Feature

Modern hierarchical feedback and complaints management system with specialized sub-agents.

## Overview

The feedback feature handles:
- Complaint submission and tracking
- Feedback and rating collection
- NPS/CSAT/CES survey collection
- Satisfaction metrics and analytics
- Auto-complaint conversion from negative feedback

## Architecture

### Hierarchical Sub-Agent System

```
feedback_node (Entry Point)
    ↓
sub_intent_classifier
    ↓
┌─────────────────────────────────────────┐
│         Sub-Agent Router                │
├─────────────────────────────────────────┤
│  submit_complaint → complaint_creator   │
│  track_complaint → complaint_tracker    │
│  submit_feedback → feedback_collector   │
│  nps_survey → nps_surveyor              │
│  view_metrics → satisfaction_analyst    │
└─────────────────────────────────────────┘
```

### Sub-Agents

| Sub-Agent | Responsibility | Sub-Intents |
|-----------|---------------|-------------|
| **complaint_creator** | Create and submit complaints | submit_complaint |
| **complaint_tracker** | Track complaint status and updates | track_complaint |
| **feedback_collector** | Collect ratings and feedback | submit_feedback |
| **nps_surveyor** | Conduct NPS/CSAT/CES surveys | nps_survey |
| **satisfaction_analyst** | Generate metrics and analytics | view_metrics |

## Sub-Intent Classification

The feature uses LLM-based classification to determine user intent:

```python
class SubIntentClassification(BaseModel):
    sub_intent: Literal[
        "submit_complaint",
        "track_complaint",
        "submit_feedback",
        "nps_survey",
        "view_metrics"
    ]
    confidence: float
    entities: Dict[str, Any]
    missing_entities: List[str]
    reasoning: str
```

### Classification Examples

| User Message | Sub-Intent | Entities Extracted |
|--------------|------------|-------------------|
| "I want to file a complaint about cold food" | submit_complaint | description, category: food_quality |
| "What's the status of my complaint #C123?" | track_complaint | complaint_id |
| "I'd like to rate my recent order 5 stars" | submit_feedback | rating: 5 |
| "How likely am I to recommend this? 9/10" | nps_survey | nps_score: 9 |
| "Show me satisfaction trends for this month" | view_metrics | period, metric_type |

## State Management

### FeedbackProgress Tracker

Central progress tracker for feedback flows:

```python
class FeedbackProgress(BaseModel):
    # Authentication (3-tier)
    user_id: Optional[str] = None
    phone: Optional[str] = None
    device_id: Optional[str] = None

    # Complaint data
    complaint_category: Optional[Literal[
        "food_quality", "service", "cleanliness",
        "wait_time", "billing", "other"
    ]] = None
    complaint_description: Optional[str] = None
    complaint_id: Optional[str] = None
    complaint_priority: Optional[Literal["low", "medium", "high"]] = "medium"

    # Feedback data
    feedback_rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_text: Optional[str] = None
    feedback_category: Optional[str] = None

    # NPS data
    nps_score: Optional[int] = Field(default=None, ge=0, le=10)
    csat_score: Optional[int] = None
    ces_score: Optional[int] = None

    # Progress flags
    complaint_created: bool = False
    feedback_submitted: bool = False
    nps_recorded: bool = False

    # Metadata
    order_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
```

### Helper Methods

```python
# Check if complaint data is complete
if feedback_progress.is_complaint_ready():
    await create_complaint(...)

# Classify NPS category
category = feedback_progress.classify_nps_category()
# Returns: "promoter" (9-10), "passive" (7-8), or "detractor" (0-6)

# Get missing required fields
missing = feedback_progress.get_missing_complaint_fields()
# Returns: ["complaint_description", "complaint_category"]

# Get user identifier (3-tier fallback)
user_identifier = feedback_progress.get_user_identifier()
# Returns: user_id, phone, or device_id (first available)
```

## Tools

### Complaint Tools (`tools/complaint_tools.py`)

```python
# Create complaint
await create_complaint(
    description="Food was cold when delivered",
    category="food_quality",
    priority="high",
    user_id="user123",
    order_id="order456"
)

# Update complaint status
await update_complaint_status(
    complaint_id="C123",
    status="resolved",
    resolution_notes="Refund issued"
)

# Get complaint details
await get_complaint_details(complaint_id="C123")

# List user complaints
await get_user_complaints(
    user_id="user123",
    status="open",
    limit=10
)
```

### Feedback Tools (`tools/feedback_tools.py`)

```python
# Submit feedback
await create_feedback(
    rating=5,
    feedback_text="Excellent service!",
    category="service",
    user_id="user123",
    order_id="order456"
)

# Create detailed rating
await create_detailed_rating(
    order_id="order456",
    food_rating=5,
    service_rating=4,
    ambiance_rating=5,
    value_rating=4
)
```

**Auto-Complaint Conversion**: Ratings of 1-2 stars with feedback text automatically create complaints:
- 1 star → High priority complaint
- 2 stars → Medium priority complaint

### NPS Tools (`tools/nps_tools.py`)

```python
# Record NPS score
await record_nps_score(
    nps_score=9,
    user_id="user123",
    order_id="order456"
)
# Classifies as: promoter (9-10), passive (7-8), detractor (0-6)

# Record CSAT score
await record_csat_score(
    csat_score=5,
    user_id="user123"
)

# Record CES score
await record_ces_score(
    ces_score=1,  # 1=very easy, 7=very difficult
    user_id="user123"
)
```

### Analytics Tools (`tools/analytics_tools.py`)

```python
# Get satisfaction metrics
await get_satisfaction_metrics(
    user_id="user123",
    period_days=30,
    metric_type="nps"
)

# Calculate NPS breakdown
await calculate_nps_breakdown(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)
# Returns: promoters %, passives %, detractors %, net_promoter_score

# Get complaint trends
await get_complaint_trends(
    category="food_quality",
    period_days=30
)

# Compare satisfaction periods
await compare_satisfaction_periods(
    current_start=datetime(2025, 1, 1),
    current_end=datetime(2025, 1, 31),
    previous_start=datetime(2024, 12, 1),
    previous_end=datetime(2024, 12, 31)
)
```

## Formatters

### Complaint Formatting (`complaint_formatter.py`)

```python
# Format complaint list
formatted = format_complaint_list(
    complaints=[...],
    plain_text=True
)
# Output:
# Your Complaints:
# ---
# 1. C123 - food_quality (HIGH PRIORITY)
#    "Food was cold"
#    Status: open
#    Created: Jan 15, 2025 2:30 PM

# Format complaint details
formatted = format_complaint_details(
    complaint={...},
    plain_text=True
)

# Format status update
formatted = format_status_update(
    complaint_id="C123",
    old_status="open",
    new_status="resolved",
    plain_text=True
)

# Format confirmation
formatted = format_complaint_confirmation(
    complaint={...},
    plain_text=True
)
```

### Feedback Formatting (`feedback_formatter.py`)

```python
# Format feedback summary
formatted = format_feedback_summary(
    feedback={...},
    plain_text=True
)
# Output:
# Feedback Summary:
# Rating: ⭐⭐⭐⭐⭐ (5/5)
# Comments: "Excellent service!"

# Format NPS score
formatted = format_nps_score(
    nps_score=9,
    plain_text=True
)
# Output:
# NPS Score: 9/10 🌟
# Category: Promoter
# You're a Promoter! Thank you...

# Format NPS breakdown
formatted = format_nps_breakdown(
    breakdown={
        "promoters_percentage": 60.0,
        "passives_percentage": 30.0,
        "detractors_percentage": 10.0,
        "net_promoter_score": 50.0
    },
    plain_text=True
)

# Format satisfaction trends
formatted = format_satisfaction_trends(
    metrics=[...],
    plain_text=True
)

# Format star rating
stars = format_rating_stars(4)  # "⭐⭐⭐⭐"
```

## Integration

### Orchestrator Routing

The feedback feature is integrated into the main orchestrator:

**Router Configuration** (`app/orchestration/nodes/router.py`):
```python
intent_agent_mapping = {
    "complaint": "feedback_agent",
    "feedback": "feedback_agent",
    "satisfaction_survey": "feedback_agent",
    # ...
}
```

**Graph Configuration** (`app/orchestration/graph.py`):
```python
from app.features.feedback import feedback_node as feedback_agent_node

workflow.add_node("feedback_agent", feedback_agent_node)
workflow.add_edge("feedback_agent", "response_agent")
```

### Entry Point

```python
from app.features.feedback import feedback_node

# Called by orchestrator
result = await feedback_node(state)

# Returns:
{
    "action": "complaint_created",
    "success": True,
    "data": {
        "message": "...",
        "complaint_id": "C123",
        ...
    },
    "context": {
        "sub_intent": "submit_complaint",
        "confidence": 0.95
    }
}
```

## Database Models

The feature uses these database models:

1. **Complaint** - Customer complaints
2. **Feedback** - Ratings and feedback
3. **NPSSurvey** - Net Promoter Score surveys
4. **CSATSurvey** - Customer Satisfaction surveys
5. **CESSurvey** - Customer Effort Score surveys

## Sub-Agent Details

### 1. Complaint Creator

**File**: `agents/complaint_creator/node.py`

**Responsibility**: Create and submit complaints

**Features**:
- Auto-categorization based on description
- Auto-link to recent orders
- Priority assignment
- Validation of required fields

**Flow**:
```
1. Validate description and category
2. Get user identifier (user_id/phone/device_id)
3. Auto-link to recent order if not provided
4. Create complaint in database
5. Update FeedbackProgress
6. Return formatted confirmation
```

**Example**:
```python
Input: "The food was cold when it arrived"
Entities: {
    "description": "The food was cold when it arrived",
    "category": "food_quality"
}

Output: {
    "action": "complaint_created",
    "success": True,
    "data": {
        "complaint_id": "C123",
        "message": "Complaint C123 created successfully",
        "category": "food_quality",
        "priority": "medium"
    }
}
```

### 2. Complaint Tracker

**File**: `agents/complaint_tracker/node.py`

**Responsibility**: Track and update complaint status

**Features**:
- List user complaints
- View complaint details
- Update complaint status
- Filter by status

**Actions**:
- `list_complaints` - Show all user complaints
- `view_details` - Show specific complaint details
- `update_status` - Update complaint status

### 3. Feedback Collector

**File**: `agents/feedback_collector/node.py`

**Responsibility**: Collect ratings and feedback

**Features**:
- Rating collection (1-5 stars)
- Detailed ratings (food, service, ambiance, value)
- Auto-complaint conversion for negative feedback
- Order linking

**Auto-Complaint Logic**:
```python
if rating <= 2 and feedback_text:
    # Auto-create complaint
    priority = "high" if rating == 1 else "medium"
    await create_complaint(
        description=feedback_text,
        category="other",
        priority=priority
    )
```

### 4. NPS Surveyor

**File**: `agents/nps_surveyor/node.py`

**Responsibility**: Conduct NPS/CSAT/CES surveys

**Features**:
- NPS score collection (0-10)
- CSAT score collection (1-5)
- CES score collection (1-7)
- Auto-classification (promoter/passive/detractor)

**NPS Classification**:
- **Promoter** (9-10): 🌟 "You're a Promoter!"
- **Passive** (7-8): 😊 "Thanks for your feedback"
- **Detractor** (0-6): 😟 "We're sorry to hear that"

### 5. Satisfaction Analyst

**File**: `agents/satisfaction_analyst/node.py`

**Responsibility**: Generate metrics and analytics

**Features**:
- NPS breakdown calculation
- Complaint trend analysis
- Satisfaction metric tracking
- Period comparison

**Metrics**:
```python
{
    "nps_breakdown": {
        "promoters_percentage": 60.0,
        "passives_percentage": 30.0,
        "detractors_percentage": 10.0,
        "net_promoter_score": 50.0
    },
    "complaint_trends": {
        "food_quality": 15,
        "service": 8,
        "wait_time": 5
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

### Complaint Submission Flow

```
1. User: "I want to complain about cold food"
2. Sub-intent: submit_complaint
3. Entities: {description: "cold food", category: "food_quality"}
4. Agent: complaint_creator
5. Actions:
   - Validate description and category
   - Get user identifier
   - Auto-link to recent order
   - Create complaint
6. Response: Complaint C123 created successfully
```

### Feedback Collection Flow

```
1. User: "I'd like to rate my order 5 stars"
2. Sub-intent: submit_feedback
3. Entities: {rating: 5}
4. Agent: feedback_collector
5. Actions:
   - Validate rating (1-5)
   - Link to order
   - Create feedback
6. Response: Feedback submitted successfully
```

### NPS Survey Flow

```
1. User: "I'd rate my likelihood to recommend as 9"
2. Sub-intent: nps_survey
3. Entities: {nps_score: 9}
4. Agent: nps_surveyor
5. Actions:
   - Validate score (0-10)
   - Record NPS
   - Classify as promoter
6. Response: NPS Score: 9/10 🌟 (Promoter)
```

## Testing

### Unit Tests

```bash
pytest app/features/feedback/tests/
```

### Test Files

- `tests/test_complaint_creator.py`
- `tests/test_complaint_tracker.py`
- `tests/test_feedback_collector.py`
- `tests/test_nps_surveyor.py`
- `tests/test_satisfaction_analyst.py`
- `tests/test_sub_intent_classifier.py`

## Migration Notes

### From Legacy customer_satisfaction_agent

The feedback feature replaces the legacy `customer_satisfaction_agent`:

**Changes**:
- ✅ Split monolithic agent into 5 specialized sub-agents
- ✅ Added FeedbackProgress tracker for state management
- ✅ Added sub-intent classification
- ✅ Reorganized tools into domain-specific files
- ✅ Added formatters for clean output
- ✅ Added auto-complaint conversion
- ✅ Added NPS classification

**Deprecation Timeline**:
- Phase 5: feedback_agent active, customer_satisfaction_agent marked deprecated
- Phase 6: Remove customer_satisfaction_agent completely

## Configuration

### Environment Variables

```bash
# LLM Model for sub-intent classification
SUB_INTENT_CLASSIFICATION_MODEL=gpt-4

# Cache settings
CACHE_TTL=300  # 5 minutes
```

### Agent Models

Each sub-agent can be configured independently:

```python
# In agent node files
llm = await llm_manager.get_llm(
    model=config.AGENT_MODEL,  # Default model
    temperature=0.3
)
```

## Logging

All components use structured logging:

```python
import structlog

logger = structlog.get_logger("feedback.complaint_creator")

logger.info(
    "Complaint created",
    complaint_id=complaint_id,
    category=category,
    priority=priority
)
```

## Cache

Feedback feature uses centralized caching:

```python
from app.features.feedback.cache import get_from_cache, set_cache

# Cache user complaints
cached = await get_from_cache(f"complaints:{user_id}")
if not cached:
    complaints = await get_user_complaints(user_id)
    await set_cache(f"complaints:{user_id}", complaints, ttl=300)
```

## Best Practices

1. **Always validate user input** before database operations
2. **Use FeedbackProgress** for multi-turn flows
3. **Leverage formatters** for consistent output
4. **Auto-link to orders** when possible for better tracking
5. **Log all operations** for debugging and analytics
6. **Cache frequently accessed data** (complaint lists, metrics)
7. **Use auto-complaint conversion** for negative feedback
8. **Classify NPS scores** for better customer segmentation

## Troubleshooting

### Common Issues

**Issue**: Missing entities for complaint creation
**Solution**: Use `get_missing_complaint_fields()` to prompt user

**Issue**: User not authenticated
**Solution**: Fallback to phone or device_id via `get_user_identifier()`

**Issue**: Complaint not linked to order
**Solution**: Auto-link to recent orders or prompt user

**Issue**: NPS score validation fails
**Solution**: Validate score is 0-10, provide clear error message

## Future Enhancements

- [ ] Multi-language support for feedback
- [ ] Sentiment analysis on feedback text
- [ ] AI-powered complaint categorization
- [ ] Automated resolution suggestions
- [ ] Real-time analytics dashboard
- [ ] Email/SMS notifications for complaint updates
- [ ] Image upload for complaints
- [ ] Voice feedback collection

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Pydantic Models](https://docs.pydantic.dev/)
- [NPS Best Practices](https://www.netpromoter.com/)
- [Structlog](https://www.structlog.org/)
