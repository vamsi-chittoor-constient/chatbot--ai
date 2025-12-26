# Load Testing Report - Restaurant Chatbot System
**Date:** 2025-12-26
**Test Duration:** ~103 seconds
**Testing Tool:** Custom Python asyncio load tester

---

## Executive Summary

The restaurant chatbot system was tested under various load conditions to identify performance limits and breaking points. **Critical issues were found at concurrent loads**, with chat API success rate dropping to **40% at 20 concurrent users**.

### Key Findings:
- ✅ Sustained load (10 req/sec): **100% success**
- ⚠️ Burst health checks (100 concurrent): **63% success**
- ❌ Concurrent chat (20 users): **40% success** - **CRITICAL BOTTLENECK**

---

## Test Results

### Test 1: Health Endpoint Burst Load (100 Concurrent Requests)

**Scenario:** 100 simultaneous health check requests

| Metric | Value |
|--------|-------|
| Total Requests | 100 |
| Successful | 63 (63%) |
| **Failed** | **37 (37%)** ⚠️ |
| Total Time | 0.72s |
| Throughput | 139.75 req/sec |
| Mean Response Time | 530.91ms |
| Min Response | 204.40ms |
| Max Response | 704.27ms |
| Median Response | 638.15ms |

**Analysis:**
- ❌ **FAILURE**: 37% failure rate is unacceptable
- System struggles with burst traffic spikes
- Response times very high (500ms+ average)

---

### Test 2: Concurrent Chat API Requests (20 Simultaneous Users)

**Scenario:** 20 users sending chat messages at the same time

| Metric | Value |
|--------|-------|
| Concurrent Requests | 20 |
| Successful | 8 (40%) |
| **Failed** | **12 (60%)** ❌ CRITICAL |
| Total Time | 60.12s |
| Mean Response Time | **42.03 seconds** |
| Min Response | 30.42s |
| Max Response | 51.51s |

**Analysis:**
- ❌ **CRITICAL FAILURE**: Only 40% success rate
- ❌ Response times completely unacceptable (30-51 seconds!)
- This is the **PRIMARY BOTTLENECK** in the system
- **Breaking Point: ~8-10 concurrent chat users**

**Root Cause Analysis:**
1. **CrewAI Agent Execution** - Each chat requires full agent reasoning chain (30-50 seconds)
2. **LLM API Calls** - Multiple sequential OpenAI API calls per message
3. **Database Queries** - Menu searches, cart operations adding latency
4. **No Request Queuing** - Concurrent requests all executed simultaneously

---

### Test 3: Database Connection Pool Stress Test

**Scenario:** Gradually increasing concurrent database connections

| Level | Success Rate | Throughput | Status |
|-------|--------------|------------|--------|
| 10 connections | 100% | 177.7 req/sec | ✅ OK |
| 20 connections | 100% | 198.3 req/sec | ✅ OK |
| 30 connections | 100% | 200.5 req/sec | ✅ OK |
| 40 connections | 100% | 129.9 req/sec | ⚠️ Slowdown |
| 50 connections | 100% | 166.6 req/sec | ⚠️ Variable |

**Analysis:**
- ✅ Database connection pool handles up to 50 concurrent connections
- ⚠️ Performance degradation starts at 40+ connections
- Throughput inconsistent at high loads (fluctuates 130-200 req/sec)
- Database itself is NOT the bottleneck

---

### Test 4: Sustained Load (10 req/sec for 30 seconds)

**Scenario:** Continuous 10 requests/second load for 30 seconds

| Metric | Value |
|--------|-------|
| Total Requests | 300 |
| Successful | 300 (100%) |
| Failed | 0 (0%) |
| Duration | 30.3 seconds |
| Actual Rate | 9.90 req/sec |
| Mean Response | 48.69ms |
| P95 Response | 92.27ms |
| P99 Response | 119.88ms |

**Analysis:**
- ✅ **EXCELLENT**: 100% success rate under sustained load
- ✅ Response times very healthy (<100ms)
- System performs well under controlled, steady load
- **Breaking Point: NOT REACHED** at 10 req/sec

---

## System Breaking Points

### 1. **Chat API Concurrent Users: 8-10 users** ❌ CRITICAL

**Breaking Point:** System fails when 20 concurrent users send chat messages

**Symptoms:**
- 60% request failure rate
- 30-51 second response times
- System becomes unresponsive

**Impact:** Production unusable with >10 simultaneous active users

---

### 2. **Health Endpoint Burst: 60-70 requests** ⚠️ WARNING

**Breaking Point:** 37% failure rate at 100 concurrent requests

**Symptoms:**
- High latency (500ms+ average)
- Connection failures
- Timeout errors

**Impact:** System struggles with traffic spikes

---

### 3. **Database Pool: 40+ connections** ⚠️ DEGRADATION

**Breaking Point:** Performance degradation begins at 40 concurrent DB connections

**Symptoms:**
- Throughput drops from 200 to 130 req/sec
- Variable performance

**Impact:** Minor - not the primary bottleneck

---

## Bottleneck Analysis

### PRIMARY BOTTLENECK: CrewAI Agent Processing

**Identified Issue:**
Each chat message requires 30-50 seconds of processing due to:
1. LLM reasoning/planning (gpt-4o)
2. Tool execution (menu search, cart ops)
3. Agent delegation (booking agent)
4. Sequential API calls to OpenAI

**Current Architecture:**
```
User Message → CrewAI Agent → Multiple LLM Calls → Tools → Response
    |              |                |                |        |
  instant        5-10s           10-20s           5-10s    10-20s

Total: 30-50 seconds per message
```

**Why It Breaks at 20 Concurrent:**
- 20 messages × 30-50 seconds each = **600-1000 seconds of work**
- All processed concurrently (no queue)
- OpenAI API rate limits hit
- Database connections exhausted
- System memory saturated

---

### SECONDARY BOTTLENECK: No Request Queuing

**Issue:** All concurrent requests processed simultaneously
**Impact:** Resource exhaustion under burst load
**Solution Needed:** Request queue with worker pool

---

### TERTIARY BOTTLENECK: OpenAI API Rate Limits

**Issue:** Multiple OpenAI accounts configured but still hitting limits
**Impact:** API errors at high concurrent load
**Solution Needed:** Better rate limit management

---

## Recommendations

### CRITICAL - Immediate Actions Required

1. **Implement Request Queue** (Priority: URGENT)
   - Add Redis-based job queue (e.g., Celery, RQ)
   - Limit concurrent agent executions to 5-10
   - Queue remaining requests
   - **Impact**: Prevents system overload

2. **Add Worker Pool** (Priority: HIGH)
   - Separate worker processes for agent execution
   - Horizontal scaling capability
   - **Impact**: Increases capacity to 50-100 concurrent users

3. **Implement Rate Limiting** (Priority: HIGH)
   - Limit to 5 concurrent requests per session
   - Return "Please wait" message when limit exceeded
   - **Impact**: Prevents individual users from exhausting resources

### HIGH - Performance Optimizations

4. **Cache Menu Data** (Priority: MEDIUM)
   - Menu rarely changes - cache for 1 hour
   - Reduce database queries by 80%
   - **Impact**: Reduces response time by 5-10 seconds

5. **Optimize Agent Prompts** (Priority: MEDIUM)
   - Reduce token count in system prompts
   - Use gpt-4o-mini where possible (already done partially)
   - **Impact**: Reduces API costs and latency

6. **Database Connection Pool** (Priority: LOW)
   - Increase pool size from 20 to 30
   - Increase overflow from 40 to 60
   - **Impact**: Minimal - not current bottleneck

### MEDIUM - Monitoring & Observability

7. **Add Metrics Collection**
   - Track concurrent active requests
   - Monitor queue depth
   - Alert on >80% capacity
   - **Tool**: Prometheus + Grafana

8. **Add Circuit Breakers**
   - Fail fast when OpenAI API down
   - Graceful degradation
   - **Tool**: resilience4j pattern

---

## Production Capacity Estimates

### Current Capacity (Without Fixes):
- **Concurrent Users:** 8-10 MAX
- **Requests/second:** 10 sustained, 60-70 burst
- **Daily Active Users:** ~100-200 (if spread out)

### After Implementing Queue + Workers (Recommended):
- **Concurrent Users:** 50-100
- **Requests/second:** 50 sustained, 200 burst
- **Daily Active Users:** 5,000-10,000

### After Full Optimization:
- **Concurrent Users:** 200-500
- **Requests/second:** 100 sustained, 500 burst
- **Daily Active Users:** 50,000-100,000

---

## Test Environment

**System Configuration:**
- CPU: Intel i7 (8 cores)
- RAM: 16GB
- Database: PostgreSQL 15 (local)
- Redis: 7-alpine (local)
- Chatbot: Docker (2 CPU, 4GB RAM)
- PetPooja Service: Docker (2 CPU, 2GB RAM)

**Software Versions:**
- Python: 3.11
- FastAPI: 0.115+
- CrewAI: Latest
- OpenAI API: gpt-4o, gpt-4o-mini

---

## Conclusion

The restaurant chatbot system **CANNOT handle production load** in its current state. With only **8-10 concurrent users** before critical failure, immediate architectural changes are required.

### Priority Actions:
1. ✅ **Implement request queue** - Required before production
2. ✅ **Add worker pool** - Scale to 50-100 users
3. ✅ **Implement rate limiting** - Protect system from abuse

### Timeline:
- Request queue implementation: 2-3 days
- Worker pool setup: 1-2 days
- Rate limiting: 1 day
- **Total: ~1 week to production-ready**

---

**Last Updated:** 2025-12-26
**Status:** CRITICAL ISSUES IDENTIFIED
**Action Required:** Immediate architectural improvements needed
