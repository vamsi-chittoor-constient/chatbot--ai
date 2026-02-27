# General Queries Feature

## Overview

The **General Queries** feature handles FAQ searches, policy inquiries, restaurant information requests, and general assistance using a hierarchical sub-agent architecture. This feature provides a centralized system for answering common questions, retrieving restaurant operational details, and assisting users with general inquiries.

## Architecture

### Hierarchical Sub-Agent System

```
general_queries_node (Entry Point)
    ├── Sub-Intent Classifier (LLM-based)
    └── Sub-Agent Router
        ├── knowledge_agent (FAQ + Policies)
        ├── restaurant_info_agent (Hours, Location, Contact)
        └── general_assistant_agent (General Queries + Fallback)
```

### State Management

- **GeneralQueriesProgress**: Pydantic-based progress tracker
- **GeneralQueriesState**: TypedDict for feature-specific state
- Inherits from global `AgentState` for session context

### Key Components

1. **Sub-Intent Classifier**: LLM-based classification with structured output
2. **3 Specialized Sub-Agents**: Domain-specific query handling
3. **16 Domain Tools**: Organized across 4 tool files
4. **LangGraph Orchestration**: State-based routing and execution
5. **Query Analytics**: Performance tracking and satisfaction monitoring

## Sub-Agents

### 1. Knowledge Agent

**Responsibility**: FAQ and policy knowledge base

**Sub-Intent**: `search_knowledge`

**Handles**:
- FAQ searches (semantic search)
- FAQ retrieval by ID or category
- Policy inquiries (8 policy types)
- Featured FAQ display

**Priority Order**:
1. Get specific FAQ by ID (if `faq_id` provided)
2. Search policies (if `policy_type` provided)
3. Search FAQs by category (if `faq_category` provided)
4. Search FAQs with query (if `query` provided)
5. Get featured FAQs (default fallback)

**Tools Used**:
- `search_faq`: Semantic search across FAQ database
- `get_faq_by_id`: Retrieve specific FAQ
- `get_faqs_by_category`: Category-based filtering
- `get_featured_faqs`: Get highlighted FAQs
- `search_policies`: Policy search with fallback templates
- `get_policy_by_type`: Specific policy retrieval

**Example Entities**:
```python
{
    "query": "How do I cancel my reservation?",
    "faq_id": 42,
    "faq_category": "reservations",
    "policy_type": "cancellation"
}
```

### 2. Restaurant Info Agent

**Responsibility**: Restaurant operational information

**Sub-Intent**: `get_restaurant_info`

**Handles**:
- Business hours
- Location and directions
- Contact information
- Parking details
- General restaurant information

**Info Types**:
- `hours`: Operating hours and special schedules
- `location`: Address, directions, landmarks
- `contact`: Phone, email, social media
- `parking`: Availability, pricing, accessibility
- `general`: Comprehensive restaurant overview

**Tools Used**:
- `get_restaurant_info`: General information retrieval
- `get_business_hours`: Operating hours
- `get_location_info`: Address and directions
- `get_contact_info`: Contact details
- `get_parking_info`: Parking information

**Example Entities**:
```python
{
    "info_type": "hours",  # or "location", "contact", "parking", "general"
    "query": "What time do you close on weekends?"
}
```

### 3. General Assistant Agent

**Responsibility**: General queries, capability questions, and fallback

**Sub-Intent**: `general_inquiry`

**Handles**:
- Capability questions ("What can you help me with?")
- Vague or unclear queries
- Gratitude acknowledgment
- General assistance
- Query analytics tracking

**Special Behaviors**:
- **Capability Detection**: Responds to "can you", "do you", "what can" with capability list
- **Gratitude Handling**: Recognizes "thank you", marks query as satisfied
- **Vague Query Guidance**: Provides helpful suggestions for unclear requests
- **Analytics Tracking**: Records all general queries for improvement

**Tools Used**:
- `track_query`: Query analytics and performance tracking
- `update_faq_satisfaction`: User satisfaction feedback
- `get_query_statistics`: Query performance metrics

**Example Entities**:
```python
{
    "query": "Can you help me with something?",
    "query_type": "capability"  # or "vague", "gratitude", "general"
}
```

## Tools

### FAQ Tools (`faq_tools.py`)

```python
# Semantic search across FAQ database
search_faq(query: str, limit: int = 5) -> Dict[str, Any]

# Retrieve specific FAQ by ID
get_faq_by_id(faq_id: int) -> Dict[str, Any]

# Get featured/highlighted FAQs
get_featured_faqs(limit: int = 5) -> Dict[str, Any]

# Filter FAQs by category
get_faqs_by_category(category: str, limit: int = 10) -> Dict[str, Any]
```

### Policy Tools (`policy_tools.py`)

**Available Policy Types**:
- `cancellation`: Reservation cancellation rules
- `refund`: Refund policies and timelines
- `reservation`: Booking terms and conditions
- `dietary`: Dietary restrictions and accommodations
- `allergen`: Allergen information and handling
- `group_booking`: Large party reservation policies
- `payment`: Payment methods and policies
- `privacy`: Data privacy and protection

```python
# Search policies (database-first, template fallback)
search_policies(policy_type: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]

# Get specific policy by type
get_policy_by_type(policy_type: str) -> Dict[str, Any]

# Get all available policies
get_all_policies() -> Dict[str, Any]
```

**Fallback Templates**: 8 hardcoded policy templates ensure responses even without database content.

### Restaurant Tools (`restaurant_tools.py`)

```python
# General restaurant information
get_restaurant_info(info_type: str = "general") -> Dict[str, Any]

# Business hours (regular, weekend, holiday)
get_business_hours() -> Dict[str, Any]

# Location details (address, directions, landmarks)
get_location_info() -> Dict[str, Any]

# Contact information (phone, email, social)
get_contact_info() -> Dict[str, Any]

# Parking information (availability, pricing)
get_parking_info() -> Dict[str, Any]
```

### Analytics Tools (`analytics_tools.py`)

```python
# Track query for analytics
track_query(
    query_text: str,
    query_category: str,
    response_type: str,
    confidence_score: float,
    user_satisfied: Optional[bool] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]

# Update FAQ satisfaction score
update_faq_satisfaction(
    faq_id: int,
    satisfied: bool
) -> Dict[str, Any]

# Get query statistics
get_query_statistics(
    category: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]
```

## Sub-Intent Classification

### Classifier Schema

```python
class SubIntentClassification(BaseModel):
    sub_intent: Literal["search_knowledge", "get_restaurant_info", "general_inquiry"]
    confidence: float  # 0.0 to 1.0
    entities: Dict[str, Any]
    missing_entities: List[str]
    reasoning: str
```

### Classification Examples

**Example 1: FAQ Search**
```python
User: "How do I cancel my reservation?"

Classification:
{
    "sub_intent": "search_knowledge",
    "confidence": 0.95,
    "entities": {
        "query": "How do I cancel my reservation?",
        "policy_type": "cancellation"
    },
    "missing_entities": [],
    "reasoning": "User asking about cancellation process - policy inquiry"
}

→ Routes to: knowledge_agent
```

**Example 2: Restaurant Hours**
```python
User: "What time do you close on Sunday?"

Classification:
{
    "sub_intent": "get_restaurant_info",
    "confidence": 0.92,
    "entities": {
        "info_type": "hours",
        "query": "What time do you close on Sunday?"
    },
    "missing_entities": [],
    "reasoning": "User requesting business hours information"
}

→ Routes to: restaurant_info_agent
```

**Example 3: General Capability**
```python
User: "What can you help me with?"

Classification:
{
    "sub_intent": "general_inquiry",
    "confidence": 0.88,
    "entities": {
        "query": "What can you help me with?",
        "query_type": "capability"
    },
    "missing_entities": [],
    "reasoning": "User asking about assistant capabilities"
}

→ Routes to: general_assistant_agent
```

## User Flows

### Flow 1: FAQ Search

```
User: "How do I make a reservation?"
    ↓
Sub-Intent Classifier
    ↓ [search_knowledge, confidence: 0.94]
knowledge_agent
    ↓
search_faq("How do I make a reservation?", limit=5)
    ↓
Return top 5 relevant FAQs with answers
    ↓
Track query analytics (category: "faq", satisfied: true)
    ↓
Response: "Here are some FAQs about making reservations: ..."
```

### Flow 2: Policy Inquiry

```
User: "What's your cancellation policy?"
    ↓
Sub-Intent Classifier
    ↓ [search_knowledge, confidence: 0.96, entities: {policy_type: "cancellation"}]
knowledge_agent
    ↓
get_policy_by_type("cancellation")
    ↓
Check database → Fallback to template if needed
    ↓
Track query analytics (category: "policy", satisfied: true)
    ↓
Response: "Our Cancellation Policy: You may cancel..."
```

### Flow 3: Restaurant Hours

```
User: "Are you open on holidays?"
    ↓
Sub-Intent Classifier
    ↓ [get_restaurant_info, confidence: 0.91, entities: {info_type: "hours"}]
restaurant_info_agent
    ↓
get_business_hours()
    ↓
Query Restaurant table for hours data
    ↓
Track query analytics (category: "hours", satisfied: true)
    ↓
Response: "Our holiday hours are: ..."
```

### Flow 4: General Assistance

```
User: "Can you help me?"
    ↓
Sub-Intent Classifier
    ↓ [general_inquiry, confidence: 0.87, entities: {query_type: "capability"}]
general_assistant_agent
    ↓
Detect capability keywords
    ↓
Return capability list + suggestions
    ↓
Track query analytics (category: "general", satisfied: true)
    ↓
Response: "I can help you with: Restaurant Information, FAQs..."
```

## State Management

### GeneralQueriesProgress Tracker

```python
class GeneralQueriesProgress(BaseModel):
    # Identity (3-tier)
    user_id: Optional[int] = None
    phone: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None

    # Query context
    query_text: Optional[str] = None
    query_category: Optional[Literal["faq", "policy", "hours", "location", "contact", "general"]] = None

    # FAQ search
    faq_search_query: Optional[str] = None
    faq_results: List[Dict[str, Any]] = Field(default_factory=list)
    faq_category_filter: Optional[str] = None

    # Policy inquiry
    policy_type: Optional[Literal["cancellation", "refund", "reservation", ...]] = None
    policy_results: List[Dict[str, Any]] = Field(default_factory=list)

    # Restaurant info
    info_type: Optional[Literal["general", "hours", "location", "contact", ...]] = None
    restaurant_info: Dict[str, Any] = Field(default_factory=dict)

    # Analytics
    confidence_score: float = 0.0
    query_resolved: bool = False
    user_satisfied: Optional[bool] = None
    response_time_ms: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### Helper Methods

```python
# Mark query as resolved
queries_progress.mark_query_resolved(satisfied: bool = True)

# Update FAQ results
queries_progress.add_faq_result(faq_data: Dict[str, Any])

# Update policy results
queries_progress.add_policy_result(policy_data: Dict[str, Any])

# Set restaurant information
queries_progress.set_restaurant_info(info_data: Dict[str, Any])
```

## Integration

### Orchestrator Integration

The general_queries feature is integrated into the main orchestrator at `/app/orchestration/graph.py`:

```python
# Import new general queries feature
from app.features.general_queries import general_queries_node as general_queries_agent_node

# Add to workflow
workflow.add_node("general_queries_agent", general_queries_agent_node)
```

### Entry Point

```python
from app.features.general_queries import general_queries_node

# Execute general queries feature
result = await general_queries_node(state)
```

### Return Format

All sub-agents return standardized responses:

```python
{
    "action": str,              # e.g., "faq_search_complete", "policy_retrieved"
    "success": bool,            # True if operation succeeded
    "data": {
        "message": str,         # User-facing response message
        "faq_results": [...],   # FAQ search results (if applicable)
        "policy": {...},        # Policy details (if applicable)
        "restaurant_info": {...} # Restaurant info (if applicable)
    },
    "context": {
        "sub_intent": str,      # Original sub-intent
        "confidence": float,    # Classification confidence
        "query_category": str,  # Query category for analytics
        "entities": {...}       # Extracted entities
    }
}
```

## Database Models

### FAQ Model

```sql
CREATE TABLE faq (
    id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    search_vector VECTOR(1536),  -- Semantic search embeddings
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### RestaurantPolicy Model

```sql
CREATE TABLE restaurant_policy (
    id INTEGER PRIMARY KEY,
    policy_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    details TEXT,
    effective_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Restaurant Model

```sql
CREATE TABLE restaurant (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Hours
    hours_monday VARCHAR(50),
    hours_tuesday VARCHAR(50),
    hours_wednesday VARCHAR(50),
    hours_thursday VARCHAR(50),
    hours_friday VARCHAR(50),
    hours_saturday VARCHAR(50),
    hours_sunday VARCHAR(50),
    special_hours TEXT,

    -- Location
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    directions TEXT,

    -- Contact
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),

    -- Parking
    parking_available BOOLEAN DEFAULT TRUE,
    parking_details TEXT,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### QueryAnalytics Model

```sql
CREATE TABLE query_analytics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    query_category VARCHAR(50),
    response_type VARCHAR(50),
    confidence_score FLOAT,
    user_satisfied BOOLEAN,
    response_time_ms INTEGER,
    created_at TIMESTAMP
);
```

## Best Practices

### 1. Semantic FAQ Search

- Use `search_faq` for natural language queries
- Leverage vector embeddings for better matching
- Set appropriate `limit` (default: 5, max: 20)

### 2. Policy Fallback Strategy

- Always use database-first approach
- Hardcoded templates ensure availability
- Update templates when policies change

### 3. Restaurant Information

- Keep Restaurant table updated with accurate data
- Validate hours format: "9:00 AM - 10:00 PM"
- Include special hours for holidays

### 4. Analytics Tracking

- Track all queries for performance monitoring
- Use satisfaction feedback to improve FAQs
- Monitor confidence scores for classification accuracy

### 5. Error Handling

- Graceful degradation for missing data
- User-friendly error messages
- Log errors for debugging without exposing internals

### 6. Entity Extraction

- Validate entities before using
- Provide defaults for missing optional entities
- Handle multiple entity combinations

## Performance Considerations

### Caching

- FAQ results cached for common queries
- Policy templates pre-loaded at startup
- Restaurant info cached (refresh: 1 hour)

### Query Optimization

- Use semantic search for FAQ matching
- Index frequently queried fields
- Limit result sets appropriately

### Analytics

- Async query tracking (non-blocking)
- Batch analytics updates
- Periodic aggregation for statistics

## Migration from Legacy

### Legacy Agent Location

`/app/agents/general_queries/general_queries_agent.py` (543 lines, monolithic)

### Key Improvements

1. **Modular Architecture**: 3 specialized sub-agents vs. single monolithic agent
2. **Better Organization**: 16 tools across 4 domain files vs. 6 tools in single file
3. **Enhanced Classification**: LLM-based sub-intent classifier vs. rule-based routing
4. **Progress Tracking**: Centralized GeneralQueriesProgress vs. scattered state
5. **Policy Fallback**: Hardcoded templates ensure availability
6. **Analytics**: Comprehensive query tracking and satisfaction monitoring

### Breaking Changes

- Import path changed: `from app.features.general_queries import general_queries_node`
- State structure changed: Now uses `GeneralQueriesState` and `GeneralQueriesProgress`
- Tool function signatures unchanged (backward compatible)

### Orchestrator Integration

```python
# Legacy (deprecated)
from app.agents.general_queries import general_queries_agent_node as legacy_general_queries_agent_node

# New (active)
from app.features.general_queries import general_queries_node as general_queries_agent_node
```

## Testing

### Unit Tests

```bash
# Test sub-agents
pytest app/features/general_queries/agents/knowledge_agent/tests/
pytest app/features/general_queries/agents/restaurant_info_agent/tests/
pytest app/features/general_queries/agents/general_assistant_agent/tests/

# Test tools
pytest app/features/general_queries/tools/tests/

# Test classifier
pytest app/features/general_queries/tests/test_sub_intent_classifier.py
```

### Integration Tests

```bash
# Test full feature flow
pytest app/features/general_queries/tests/test_integration.py
```

### Example Test Cases

```python
# Test FAQ search
async def test_faq_search():
    result = await search_faq("How do I make a reservation?", limit=5)
    assert result["success"] is True
    assert len(result["data"]["faqs"]) <= 5

# Test policy retrieval
async def test_policy_retrieval():
    result = await get_policy_by_type("cancellation")
    assert result["success"] is True
    assert "title" in result["data"]["policy"]

# Test classification
async def test_sub_intent_classification():
    classification = await classify_sub_intent(
        "What time do you close?",
        state
    )
    assert classification.sub_intent == "get_restaurant_info"
    assert classification.confidence > 0.7
```

## Troubleshooting

### Common Issues

**Issue 1: No FAQ results returned**
- Check if FAQ database is populated
- Verify search embeddings are generated
- Test with featured FAQs fallback

**Issue 2: Policy templates not found**
- Ensure `POLICY_TEMPLATES` dict is complete
- Check policy_type spelling
- Verify database-first logic

**Issue 3: Restaurant info missing**
- Confirm Restaurant table has data
- Check column names match tool expectations
- Verify info_type parameter

**Issue 4: Low classification confidence**
- Review user message clarity
- Check sub-intent examples in classifier
- Consider adding more classification examples

## Future Enhancements

### Planned Features

1. **Multi-language Support**: FAQ and policy translations
2. **Voice Search**: Audio query processing
3. **FAQ Suggestions**: Proactive FAQ recommendations
4. **Advanced Analytics**: ML-based query analysis
5. **Personalized Responses**: User preference-based answers
6. **FAQ Voting**: Community-driven FAQ ranking

### Extensibility

- Add new sub-agents by updating `graph.py` routing
- Create new tools in respective domain files
- Extend `GeneralQueriesProgress` with custom fields
- Add new sub-intents to classifier schema

## Support

For issues or questions about the general_queries feature:

1. Check this README for common solutions
2. Review logs in `app/logs/general_queries.log`
3. Test classification with example queries
4. Verify database connectivity and data availability

---

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Maintainer**: A24 Development Team
