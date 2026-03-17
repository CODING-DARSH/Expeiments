"""
loadtest_submit.py
Tests /submit endpoint latency and throughput.
Simulates multiple teams submitting simultaneously.

Usage:
    python loadtest_submit.py                  # 10 concurrent, local
    python loadtest_submit.py --users 30       # 30 concurrent
    python loadtest_submit.py --url https://.. # test deployed URL
"""

import asyncio
import aiohttp
import time
import argparse
import statistics
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────
DEFAULT_URL   = 'http://localhost:5000'
DEFAULT_USERS = 10

# Simple correct Python code for Q1 (multiplication table)
# This will actually pass all test cases
CORRECT_CODE = """n = int(input())
for i in range(1, 6):
    print(n * i)
"""

WRONG_CODE = """print("wrong answer")"""

# ── RESULTS STORAGE ───────────────────────────────────────────────────
results = {
    'success':   [],
    'failed':    [],
    'errors':    [],
    'latencies': [],
}

async def submit_once(session, base_url, team_name, question, code, user_num):
    """Send one submit request and record latency."""
    payload = {
        'name':      team_name,
        'roll':      team_name,
        'question':  question,
        'code':      code,
        'startTime': int(time.time() * 1000) - 5000,
    }

    start = time.time()
    try:
        async with session.post(
            f'{base_url}/submit',
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            latency = (time.time() - start) * 1000  # ms
            data    = await resp.json()

            results['latencies'].append(latency)

            if resp.status == 200:
                if data.get('success'):
                    results['success'].append({
                        'user':    user_num,
                        'team':    team_name,
                        'latency': latency,
                        'passed':  data.get('passed'),
                    })
                    status = '✅ PASS' if data.get('passed') else '❌ WRONG'
                else:
                    results['failed'].append({
                        'user':    user_num,
                        'team':    team_name,
                        'latency': latency,
                        'error':   data.get('error'),
                    })
                    status = f'⚠️  FAIL ({data.get("error")})'
            else:
                results['errors'].append({'user': user_num, 'status': resp.status})
                status = f'🔴 HTTP {resp.status}'

            print(f'  User {user_num:02d} | {team_name:<20} | {latency:7.0f}ms | {status}')

    except asyncio.TimeoutError:
        latency = (time.time() - start) * 1000
        results['errors'].append({'user': user_num, 'error': 'timeout'})
        results['latencies'].append(latency)
        print(f'  User {user_num:02d} | {team_name:<20} | TIMEOUT after {latency:.0f}ms')
    except Exception as e:
        latency = (time.time() - start) * 1000
        results['errors'].append({'user': user_num, 'error': str(e)})
        results['latencies'].append(latency)
        print(f'  User {user_num:02d} | {team_name:<20} | ERROR: {e}')


async def run_load_test(base_url, num_users, use_correct_code):
    """Run all users concurrently."""

    code = CORRECT_CODE if use_correct_code else WRONG_CODE

    # Generate unique team names so no duplicate check triggers
    teams = [f'LoadTest_Team_{i:02d}' for i in range(1, num_users + 1)]

    print(f'\n{"="*60}')
    print(f'  🚀 Hack & Crack — Submit Load Test')
    print(f'{"="*60}')
    print(f'  URL:          {base_url}')
    print(f'  Concurrent:   {num_users} users')
    print(f'  Question:     Q1 (Multiplication Table)')
    print(f'  Code:         {"✅ Correct" if use_correct_code else "❌ Wrong (testing rejection speed)"}')
    print(f'  Started:      {datetime.now().strftime("%H:%M:%S")}')
    print(f'{"="*60}\n')

    # Check server is alive
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{base_url}/ping', timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status != 200:
                    print('❌ Server not responding! Make sure backend is running.')
                    return
        except Exception as e:
            print(f'❌ Cannot reach server: {e}')
            print(f'   Make sure backend is running at {base_url}')
            return

    print(f'  Server is alive ✅\n')
    print(f'  {"User":<8} {"Team":<22} {"Latency":>10} {"Result"}')
    print(f'  {"-"*60}')

    overall_start = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            submit_once(session, base_url, teams[i], 'Q1', code, i + 1)
            for i in range(num_users)
        ]
        await asyncio.gather(*tasks)

    total_time = (time.time() - overall_start) * 1000

    # ── PRINT SUMMARY ─────────────────────────────────────────────
    print(f'\n{"="*60}')
    print(f'  📊 RESULTS SUMMARY')
    print(f'{"="*60}')
    print(f'  Total requests:    {num_users}')
    print(f'  Successful:        {len(results["success"])}')
    print(f'  Failed (app):      {len(results["failed"])}')
    print(f'  Errors/Timeouts:   {len(results["errors"])}')
    print(f'  Total wall time:   {total_time:.0f}ms ({total_time/1000:.1f}s)')

    if results['latencies']:
        lats = results['latencies']
        print(f'\n  ⏱️  LATENCY BREAKDOWN')
        print(f'  Min:     {min(lats):>8.0f}ms')
        print(f'  Max:     {max(lats):>8.0f}ms')
        print(f'  Avg:     {statistics.mean(lats):>8.0f}ms')
        print(f'  Median:  {statistics.median(lats):>8.0f}ms')
        if len(lats) >= 2:
            print(f'  StdDev:  {statistics.stdev(lats):>8.0f}ms')

        # Percentiles
        sorted_lats = sorted(lats)
        p90 = sorted_lats[int(len(sorted_lats) * 0.9)]
        p95 = sorted_lats[int(len(sorted_lats) * 0.95)]
        print(f'  P90:     {p90:>8.0f}ms')
        print(f'  P95:     {p95:>8.0f}ms')

    # Throughput
    if total_time > 0:
        throughput = (num_users / total_time) * 1000 * 60
        print(f'\n  📈 THROUGHPUT')
        print(f'  Requests/min:  {throughput:.0f}')
        print(f'  Requests/sec:  {num_users / (total_time/1000):.1f}')

    # Rating
    avg = statistics.mean(results['latencies']) if results['latencies'] else 9999
    error_rate = len(results['errors']) / num_users * 100

    print(f'\n  🏆 VERDICT')
    if error_rate == 0 and avg < 3000:
        print(f'  ✅ EXCELLENT — Handles {num_users} concurrent users well!')
        print(f'     Should handle 30 teams comfortably.')
    elif error_rate == 0 and avg < 6000:
        print(f'  ⚠️  OK — Handles {num_users} users but might be slow at peak.')
        print(f'     Consider upgrading Render plan for event day.')
    elif error_rate < 10:
        print(f'  ⚠️  BORDERLINE — {error_rate:.0f}% error rate. Upgrade recommended.')
    else:
        print(f'  ❌ POOR — {error_rate:.0f}% error rate. Upgrade Render plan!')

    print(f'{"="*60}\n')


async def run_sequential_test(base_url, num_requests):
    """Test sequential throughput — one by one."""
    print(f'\n{"="*60}')
    print(f'  🔄 Sequential Test — {num_requests} requests one by one')
    print(f'{"="*60}\n')

    latencies = []
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            team = f'SeqTest_{i:02d}'
            start = time.time()
            try:
                async with session.post(
                    f'{base_url}/submit',
                    json={
                        'name': team, 'roll': team,
                        'question': 'Q1', 'code': CORRECT_CODE,
                        'startTime': int(time.time() * 1000) - 5000
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    latency = (time.time() - start) * 1000
                    data = await resp.json()
                    latencies.append(latency)
                    print(f'  Request {i+1:02d}: {latency:6.0f}ms | {"✅" if data.get("success") else "❌"}')
            except Exception as e:
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                print(f'  Request {i+1:02d}: ERROR — {e}')

    if latencies:
        rpm = (len(latencies) / sum(latencies)) * 1000 * 60
        print(f'\n  Avg latency: {statistics.mean(latencies):.0f}ms')
        print(f'  Estimated RPM (sequential): {rpm:.0f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hack & Crack Submit Load Test')
    parser.add_argument('--url',        default=DEFAULT_URL,   help='Base URL')
    parser.add_argument('--users',      type=int, default=10,  help='Concurrent users')
    parser.add_argument('--wrong',      action='store_true',   help='Use wrong code (test rejection)')
    parser.add_argument('--sequential', action='store_true',   help='Run sequential test instead')
    parser.add_argument('--seq-count',  type=int, default=10,  help='Sequential request count')
    args = parser.parse_args()

    if args.sequential:
        asyncio.run(run_sequential_test(args.url, args.seq_count))
    else:
        asyncio.run(run_load_test(args.url, args.users, not args.wrong))
