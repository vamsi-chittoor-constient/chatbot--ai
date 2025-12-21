# System Specifications for 20 Concurrent Users

## Executive Summary

This document outlines the system architecture and specifications required to handle **20 concurrent users** in a production environment for the Restaurant AI Chatbot.

---

## Current Architecture

### Threading Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UVICORN SERVER                              │
│                     (4 workers x 2 threads)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐    ┌─────────────────────────────────────────┐   │
│   │   WORKER 1  │    │          THREAD POOL EXECUTOR           │   │
│   │   WORKER 2  │───▶│         (50 threads shared)             │   │
│   │   WORKER 3  │    │                                         │   │
│   │   WORKER 4  │    │    ┌─────────────────────────────────┐  │   │
│   └─────────────┘    │    │    SEMAPHORE (20 concurrent)    │  │   │
│                      │    │    Rate limits CrewAI calls     │  │   │
│                      │    └─────────────────────────────────┘  │   │
│                      └─────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
            ┌───────────────────────────────────────────┐
            │              CREWAI AGENTS                │
            │  ┌─────────────┐  ┌─────────────────────┐ │
            │  │ Food Agent  │  │   Booking Agent     │ │
            │  │  (GPT-4o-   │  │    (GPT-4o-mini)    │ │
            │  │   mini)     │  │                     │ │
            │  └─────────────┘  └─────────────────────┘ │
            └───────────────────────────────────────────┘
```

### Key Configuration (crew_agent.py)

```python
# Thread pool for running synchronous CrewAI in async context
MAX_CONCURRENT_CREWS = 20  # Semaphore limit
THREAD_POOL_SIZE = 50      # ThreadPoolExecutor max_workers

_EXECUTOR = ThreadPoolExecutor(max_workers=50, thread_name_prefix="crew_worker")
_CREW_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_CREWS)
```

---

## Why This Works for 20 Users

### 1. **Semaphore (20 slots)**
- Limits concurrent CrewAI executions to 20
- Prevents OpenAI API rate limiting
- Provides backpressure when system is overloaded

### 2. **Thread Pool (50 threads)**
- 50 threads > 20 concurrent users
- Extra threads handle:
  - Burst traffic
  - Database operations
  - Redis operations
  - Background tasks

### 3. **GPT-4o-mini (not GPT-4o)**
- 10x faster response times
- Lower latency = higher throughput
- Sufficient quality for restaurant chatbot

### 4. **GIL is NOT the bottleneck**
- 98% of operations are I/O-bound (API calls, DB, Redis)
- Python GIL only affects CPU-bound operations
- `asyncio` + `ThreadPoolExecutor` handles I/O efficiently

---

## Hardware Requirements

### Minimum (20 Users)

| Component | Specification |
|-----------|---------------|
| **CPU** | 2 vCPU (4 recommended) |
| **RAM** | 4 GB (8 GB recommended) |
| **Storage** | 20 GB SSD |
| **Network** | 100 Mbps |

### Recommended AWS Instance Types

| Users | Instance Type | vCPU | RAM | Cost/month |
|-------|---------------|------|-----|------------|
| 20 | t3.medium | 2 | 4 GB | ~$30 |
| 50 | t3.large | 2 | 8 GB | ~$60 |
| 100 | t3.xlarge | 4 | 16 GB | ~$120 |
| 200+ | c5.2xlarge | 8 | 16 GB | ~$250 |

---

## Scaling Strategy

### Horizontal Scaling (Recommended for 50+ users)

```
                    ┌─────────────┐
                    │   AWS ALB   │
                    │   (Load     │
                    │  Balancer)  │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  ECS     │    │  ECS     │    │  ECS     │
    │ Task 1   │    │ Task 2   │    │ Task 3   │
    │ (20      │    │ (20      │    │ (20      │
    │ users)   │    │ users)   │    │ users)   │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  RDS     │    │ ElastiC. │    │ OpenAI   │
    │ Postgres │    │  Redis   │    │   API    │
    └──────────┘    └──────────┘    └──────────┘
```

### Configuration per Instance

```python
# For each container/instance handling 20 users:
WORKERS = 4                    # Uvicorn workers
THREADS_PER_WORKER = 2         # Threads per worker
MAX_CONCURRENT_CREWS = 20      # Semaphore limit
THREAD_POOL_SIZE = 50          # ThreadPoolExecutor
```

---

## Performance Tuning Parameters

### FastAPI/Uvicorn

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \                    # 4 worker processes
    --limit-concurrency 100 \        # Max connections per worker
    --timeout-keep-alive 120 \       # SSE streaming timeout
    --access-log
```

### PostgreSQL

```sql
-- For 20 concurrent users
max_connections = 100          -- 20 users × 4 workers + buffer
shared_buffers = 1GB           -- 25% of RAM
effective_cache_size = 3GB     -- 75% of RAM
work_mem = 16MB                -- Per-query memory
maintenance_work_mem = 512MB   -- Vacuum/index operations
```

### Redis

```bash
redis-server \
    --maxmemory 512mb \              # Memory limit
    --maxmemory-policy allkeys-lru   # Eviction policy
```

---

## Bottleneck Analysis

| Component | Bottleneck Risk | Mitigation |
|-----------|-----------------|------------|
| **OpenAI API** | HIGH - Rate limits | Use GPT-4o-mini, semaphore |
| **Python GIL** | LOW - I/O bound | ThreadPoolExecutor |
| **Database** | MEDIUM - Connection pool | Increase pool size |
| **Redis** | LOW - Very fast | Cluster for 100+ users |
| **Network** | LOW | CDN for static assets |

---

## Monitoring Checklist

### Key Metrics to Watch

1. **Response Time**
   - Target: < 5s average
   - Alert: > 10s

2. **Concurrent Connections**
   - Track: Active SSE streams
   - Alert: > 80% of limit

3. **Thread Pool Utilization**
   - Track: Active threads / 50
   - Alert: > 90%

4. **OpenAI API Errors**
   - Track: Rate limit errors
   - Alert: > 5/minute

5. **Memory Usage**
   - Track: RSS memory
   - Alert: > 80% of limit

### AWS CloudWatch Alarms

```yaml
# Example CloudWatch alarm config
ResponseTimeAlarm:
  Metric: ResponseTime
  Threshold: 10
  Period: 60
  EvaluationPeriods: 3
  ComparisonOperator: GreaterThanThreshold

ConcurrentUsersAlarm:
  Metric: ActiveConnections
  Threshold: 80
  Period: 60
  EvaluationPeriods: 2
```

---

## Quick Reference

### For 20 Concurrent Users

```
┌────────────────────────────────────────┐
│  RECOMMENDED CONFIGURATION             │
├────────────────────────────────────────┤
│  Instance: t3.medium (or t3.large)     │
│  vCPU: 2-4                             │
│  RAM: 4-8 GB                           │
│  Uvicorn workers: 4                    │
│  ThreadPoolExecutor: 50 threads        │
│  Semaphore: 20 concurrent              │
│  Model: GPT-4o-mini                    │
│  Expected response: 3-5 seconds        │
└────────────────────────────────────────┘
```

### Scaling Formula

```
Max Users = (Instances) × (Semaphore Limit)
          = 2 instances × 20 concurrent
          = 40 concurrent users

Response Time ≈ OpenAI latency + Processing
             ≈ 2-3s + 0.5s = 3-5 seconds
```

---

## Next Steps for Production

1. **Run Load Test**: `python load_test_20_users.py`
2. **Build Docker Image**: `docker build -t restaurant-ai .`
3. **Deploy to AWS ECS/EKS**
4. **Set up CloudWatch monitoring**
5. **Configure auto-scaling policies**
