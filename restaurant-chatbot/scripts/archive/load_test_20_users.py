"""
Load Test: 20 Concurrent Users
==============================
Simulates 20 real users going through:
1. Authentication flow (phone -> OTP -> name for new users)
2. Food ordering (browse menu, add items, checkout)

This tests the full system under realistic load.
"""

import asyncio
import aiohttp
import time
import random
import uuid
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
STREAM_ENDPOINT = f"{BASE_URL}/api/v1/chat/stream"
NUM_USERS = 100
TEST_OTP = "123456"

# Test user names
TEST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram",
    "Anjali", "Karthik", "Divya", "Rohan", "Meera",
    "Arjun", "Nisha", "Suresh", "Kavya", "Aditya",
    "Pooja", "Ravi", "Lakshmi", "Rajesh", "Sana"
]

# Food ordering scenarios
FOOD_SCENARIOS = [
    ["show menu", "add 2 butter chicken", "add 1 naan", "view cart", "checkout", "dine in"],
    ["what burgers do you have", "add 1 beef burger", "add a coke", "checkout", "take away"],
    ["I want pizza", "add margherita pizza", "view cart", "checkout", "dine in"],
    ["show me starters", "add 2 samosa", "add lassi", "checkout", "take away"],
    ["add biryani", "how many", "2", "add raita", "checkout", "dine in"],
]


@dataclass
class UserMetrics:
    """Metrics for a single user session"""
    user_id: int
    session_id: str
    phone: str
    name: str

    # Timing metrics
    auth_start: float = 0
    auth_end: float = 0
    order_start: float = 0
    order_end: float = 0

    # Response times per message
    response_times: List[float] = field(default_factory=list)

    # First CrewAI message timing (first food order message after auth)
    first_crew_response_time: float = 0

    # Auth message timing (non-CrewAI, just state machine)
    auth_response_times: List[float] = field(default_factory=list)

    # CrewAI message timings (food ordering)
    crew_response_times: List[float] = field(default_factory=list)

    # Status
    auth_success: bool = False
    order_success: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def auth_duration(self) -> float:
        return self.auth_end - self.auth_start if self.auth_end else 0

    @property
    def order_duration(self) -> float:
        return self.order_end - self.order_start if self.order_end else 0

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def max_response_time(self) -> float:
        return max(self.response_times) if self.response_times else 0


async def send_message(
    session: aiohttp.ClientSession,
    message: str,
    session_id: str,
    device_id: str,
    conversation_history: List[str]
) -> tuple[str, float, bool]:
    """
    Send a message and collect the streamed response.

    Returns: (response_text, response_time_seconds, success)
    """
    payload = {
        "message": message,
        "session_id": session_id,
        "device_id": device_id,
        "conversation_history": conversation_history[-6:]  # Last 6 messages
    }

    start_time = time.time()
    response_text = ""
    success = False

    try:
        async with session.post(
            STREAM_ENDPOINT,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status != 200:
                return f"HTTP {response.status}", time.time() - start_time, False

            # Read SSE stream
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    try:
                        data = json.loads(line[5:].strip())
                        event_type = data.get('type', '')

                        if event_type == 'TEXT_MESSAGE_CONTENT':
                            response_text += data.get('delta', '')
                        elif event_type == 'RUN_FINISHED':
                            success = True
                            break
                        elif event_type == 'RUN_ERROR':
                            response_text = f"Error: {data.get('error', 'Unknown')}"
                            break
                    except json.JSONDecodeError:
                        continue

            return response_text, time.time() - start_time, success

    except asyncio.TimeoutError:
        return "TIMEOUT", time.time() - start_time, False
    except Exception as e:
        return f"ERROR: {str(e)}", time.time() - start_time, False


async def simulate_user(user_id: int) -> UserMetrics:
    """
    Simulate a complete user journey:
    1. Start session
    2. Authenticate (phone -> OTP -> name if new)
    3. Place an order
    """
    session_id = f"load_test_{uuid.uuid4().hex[:12]}"
    device_id = f"device_{uuid.uuid4().hex[:8]}"
    phone = f"+9199{random.randint(10000000, 99999999)}"
    name = TEST_NAMES[user_id % len(TEST_NAMES)]

    metrics = UserMetrics(
        user_id=user_id,
        session_id=session_id,
        phone=phone,
        name=name
    )

    conversation_history = []

    async with aiohttp.ClientSession() as session:
        # =====================================================================
        # PHASE 1: AUTHENTICATION
        # =====================================================================
        metrics.auth_start = time.time()

        try:
            # Step 1: Initial message (triggers phone prompt) - STATE MACHINE
            response, resp_time, success = await send_message(
                session, "Hi", session_id, device_id, conversation_history
            )
            metrics.response_times.append(resp_time)
            metrics.auth_response_times.append(resp_time)  # Auth timing
            conversation_history.extend([f"User: Hi", f"Assistant: {response}"])

            if not success:
                metrics.errors.append(f"Initial message failed: {response}")
                return metrics

            # Step 2: Send phone number - STATE MACHINE
            response, resp_time, success = await send_message(
                session, phone, session_id, device_id, conversation_history
            )
            metrics.response_times.append(resp_time)
            metrics.auth_response_times.append(resp_time)  # Auth timing
            conversation_history.extend([f"User: {phone}", f"Assistant: {response}"])

            if not success:
                metrics.errors.append(f"Phone step failed: {response}")
                return metrics

            # Step 3: Send OTP - STATE MACHINE
            response, resp_time, success = await send_message(
                session, TEST_OTP, session_id, device_id, conversation_history
            )
            metrics.response_times.append(resp_time)
            metrics.auth_response_times.append(resp_time)  # Auth timing
            conversation_history.extend([f"User: {TEST_OTP}", f"Assistant: {response}"])

            if not success:
                metrics.errors.append(f"OTP step failed: {response}")
                return metrics

            # Step 4: If new user, send name - STATE MACHINE
            if "name" in response.lower() or "new here" in response.lower():
                response, resp_time, success = await send_message(
                    session, name, session_id, device_id, conversation_history
                )
                metrics.response_times.append(resp_time)
                metrics.auth_response_times.append(resp_time)  # Auth timing
                conversation_history.extend([f"User: {name}", f"Assistant: {response}"])

                if not success:
                    metrics.errors.append(f"Name step failed: {response}")
                    return metrics

            metrics.auth_end = time.time()
            metrics.auth_success = True

        except Exception as e:
            metrics.errors.append(f"Auth exception: {str(e)}")
            metrics.auth_end = time.time()
            return metrics

        # =====================================================================
        # PHASE 2: FOOD ORDERING
        # =====================================================================
        metrics.order_start = time.time()

        try:
            # Pick a random food ordering scenario
            scenario = random.choice(FOOD_SCENARIOS)

            for i, msg in enumerate(scenario):
                # Add small random delay between messages (0.5-2 seconds)
                await asyncio.sleep(random.uniform(0.5, 2.0))

                response, resp_time, success = await send_message(
                    session, msg, session_id, device_id, conversation_history
                )
                metrics.response_times.append(resp_time)
                metrics.crew_response_times.append(resp_time)  # CrewAI timing

                # Track first CrewAI message specifically (index 0 of ordering phase)
                if i == 0:
                    metrics.first_crew_response_time = resp_time

                conversation_history.extend([f"User: {msg}", f"Assistant: {response}"])

                if not success:
                    metrics.errors.append(f"Order step '{msg}' failed: {response}")
                    # Continue with other steps even if one fails

            metrics.order_end = time.time()
            metrics.order_success = len([e for e in metrics.errors if "Order step" in e]) == 0

        except Exception as e:
            metrics.errors.append(f"Order exception: {str(e)}")
            metrics.order_end = time.time()

    return metrics


async def run_load_test():
    """Run load test with NUM_USERS concurrent users"""
    print("=" * 70)
    print(f"LOAD TEST: {NUM_USERS} CONCURRENT USERS")
    print("=" * 70)
    print(f"Endpoint: {STREAM_ENDPOINT}")
    print(f"Test OTP: {TEST_OTP}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Start all users concurrently
    print(f"Starting {NUM_USERS} users...")
    start_time = time.time()

    tasks = [simulate_user(i) for i in range(NUM_USERS)]
    results: List[UserMetrics] = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # =========================================================================
    # ANALYZE RESULTS
    # =========================================================================
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Summary stats
    auth_success = sum(1 for r in results if r.auth_success)
    order_success = sum(1 for r in results if r.order_success)

    all_response_times = []
    for r in results:
        all_response_times.extend(r.response_times)

    print(f"\nOVERALL SUMMARY:")
    print(f"  Total Users:        {NUM_USERS}")
    print(f"  Total Test Time:    {total_time:.2f}s")
    print(f"  Auth Success:       {auth_success}/{NUM_USERS} ({100*auth_success/NUM_USERS:.1f}%)")
    print(f"  Order Success:      {order_success}/{NUM_USERS} ({100*order_success/NUM_USERS:.1f}%)")

    if all_response_times:
        print(f"\nRESPONSE TIMES (across all {len(all_response_times)} messages):")
        print(f"  Average:            {statistics.mean(all_response_times):.2f}s")
        print(f"  Median:             {statistics.median(all_response_times):.2f}s")
        print(f"  Min:                {min(all_response_times):.2f}s")
        print(f"  Max:                {max(all_response_times):.2f}s")
        print(f"  Std Dev:            {statistics.stdev(all_response_times):.2f}s" if len(all_response_times) > 1 else "")

        # Percentiles
        sorted_times = sorted(all_response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p90 = sorted_times[int(len(sorted_times) * 0.90)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[min(int(len(sorted_times) * 0.99), len(sorted_times)-1)]

        print(f"\nPERCENTILES:")
        print(f"  P50:                {p50:.2f}s")
        print(f"  P90:                {p90:.2f}s")
        print(f"  P95:                {p95:.2f}s")
        print(f"  P99:                {p99:.2f}s")

    # Auth vs Order timing
    auth_times = [r.auth_duration for r in results if r.auth_success]
    order_times = [r.order_duration for r in results if r.order_success]

    if auth_times:
        print(f"\nAUTH FLOW DURATION:")
        print(f"  Average:            {statistics.mean(auth_times):.2f}s")
        print(f"  Max:                {max(auth_times):.2f}s")

    if order_times:
        print(f"\nORDER FLOW DURATION:")
        print(f"  Average:            {statistics.mean(order_times):.2f}s")
        print(f"  Max:                {max(order_times):.2f}s")

    # ==========================================================================
    # CRITICAL: AUTH VS CREWAI RESPONSE TIME COMPARISON
    # ==========================================================================
    print()
    print("=" * 70)
    print("AUTH (State Machine) vs CREWAI (LLM) RESPONSE TIMES")
    print("=" * 70)

    # Collect all auth response times
    all_auth_response_times = []
    for r in results:
        all_auth_response_times.extend(r.auth_response_times)

    # Collect all CrewAI response times
    all_crew_response_times = []
    for r in results:
        all_crew_response_times.extend(r.crew_response_times)

    # First CrewAI message times (the critical one)
    first_crew_times = [r.first_crew_response_time for r in results if r.first_crew_response_time > 0]

    if all_auth_response_times:
        print(f"\nAUTH RESPONSE TIMES (State Machine - {len(all_auth_response_times)} messages):")
        print(f"  Average:            {statistics.mean(all_auth_response_times):.2f}s")
        print(f"  Median:             {statistics.median(all_auth_response_times):.2f}s")
        print(f"  Min:                {min(all_auth_response_times):.2f}s")
        print(f"  Max:                {max(all_auth_response_times):.2f}s")

    if all_crew_response_times:
        print(f"\nCREWAI RESPONSE TIMES (LLM - {len(all_crew_response_times)} messages):")
        print(f"  Average:            {statistics.mean(all_crew_response_times):.2f}s")
        print(f"  Median:             {statistics.median(all_crew_response_times):.2f}s")
        print(f"  Min:                {min(all_crew_response_times):.2f}s")
        print(f"  Max:                {max(all_crew_response_times):.2f}s")

    if first_crew_times:
        print(f"\n*** FIRST CREWAI MESSAGE TIMES ({len(first_crew_times)} users) ***")
        print(f"  Average:            {statistics.mean(first_crew_times):.2f}s")
        print(f"  Median:             {statistics.median(first_crew_times):.2f}s")
        print(f"  Min:                {min(first_crew_times):.2f}s")
        print(f"  Max:                {max(first_crew_times):.2f}s")
        print(f"  (This measures first-message latency after auth)")

    # Speedup calculation
    if all_auth_response_times and all_crew_response_times:
        auth_avg = statistics.mean(all_auth_response_times)
        crew_avg = statistics.mean(all_crew_response_times)
        print(f"\nCOMPARISON:")
        print(f"  Auth avg:           {auth_avg:.2f}s (state machine)")
        print(f"  CrewAI avg:         {crew_avg:.2f}s (LLM)")
        print(f"  Ratio:              CrewAI is {crew_avg/auth_avg:.1f}x slower than Auth")

    # Throughput
    total_messages = len(all_response_times)
    throughput = total_messages / total_time if total_time > 0 else 0
    print(f"\nTHROUGHPUT:")
    print(f"  Messages/second:    {throughput:.2f}")
    print(f"  Users/minute:       {(NUM_USERS / total_time) * 60:.1f}")

    # Errors
    all_errors = []
    for r in results:
        for e in r.errors:
            all_errors.append(f"User {r.user_id}: {e}")

    if all_errors:
        print(f"\nERRORS ({len(all_errors)}):")
        for error in all_errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
    else:
        print(f"\nNo errors!")

    # Per-user breakdown (optional, for debugging)
    print(f"\nPER-USER BREAKDOWN:")
    print(f"{'User':<6} {'Auth':<8} {'Order':<8} {'Msgs':<6} {'Avg(s)':<8} {'Max(s)':<8} {'Status'}")
    print("-" * 70)
    for r in results:
        status = "OK" if r.auth_success and r.order_success else "FAIL"
        print(f"{r.user_id:<6} {r.auth_duration:>6.2f}s {r.order_duration:>6.2f}s {len(r.response_times):<6} {r.avg_response_time:>6.2f}s {r.max_response_time:>6.2f}s {status}")

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    print()
    print("=" * 70)
    print("SYSTEM RECOMMENDATIONS FOR 20 CONCURRENT USERS")
    print("=" * 70)

    avg_response = statistics.mean(all_response_times) if all_response_times else 0

    if avg_response < 3:
        print("EXCELLENT: Response times are great!")
    elif avg_response < 5:
        print("GOOD: Response times are acceptable for production.")
    elif avg_response < 10:
        print("WARNING: Response times are slow. Consider:")
        print("  - Increase ThreadPoolExecutor workers")
        print("  - Use GPT-4o-mini instead of GPT-4o")
        print("  - Add response caching")
    else:
        print("CRITICAL: Response times too slow. Actions needed:")
        print("  - Scale horizontally (multiple server instances)")
        print("  - Increase thread pool and semaphore limits")
        print("  - Consider async CrewAI or LangGraph")

    print()
    print("=" * 70)

    return results


if __name__ == "__main__":
    asyncio.run(run_load_test())
