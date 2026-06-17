#!/usr/bin/env python3
import sys
import requests
import concurrent.futures
import time
import argparse
import itertools
import string

def check_channel(base_url, channel_name, token, timeout):
    url = f"{base_url}{channel_name}/index.m3u8?token={token}"
    try:
        resp = requests.head(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            resp2 = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            if resp2.status_code == 200 and len(resp2.text) > 20:
                return (channel_name, url)
    except:
        pass
    return None

def generate_bruteforce(min_len, max_len, chars=string.ascii_lowercase):
    for l in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=l):
            yield "".join(combo)

def main():
    parser = argparse.ArgumentParser(description="Scan for HLS streaming channels")
    parser.add_argument("server", help="Server IP:port (e.g. 1.1.1.1:80)")
    parser.add_argument("-t", "--token", default="test", help="Auth token")
    parser.add_argument("-w", "--wordlist", help="Wordlist file (one name per line)")
    parser.add_argument("--bruteforce", action="store_true", help="Brute-force short names")
    parser.add_argument("--min-len", type=int, default=3, help="Min brute-force length (default: 3)")
    parser.add_argument("--max-len", type=int, default=4, help="Max brute-force length (default: 4)")
    parser.add_argument("--chars", default="abcdefghijklmnopqrstuvwxyz", help="Chars for brute-force (default: a-z)")
    parser.add_argument("--suffix", default="_HD", help="Comma-separated suffixes to append to brute-force names (default: _HD)")
    parser.add_argument("--threads", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=1.5)
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    base_url = f"http://{args.server}/"
    names = set()

    if args.wordlist:
        with open(args.wordlist) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    names.add(line)
        print(f"[*] Wordlist: {len(names)} names")

    if args.bruteforce:
        total_bf = sum(26**l for l in range(args.min_len, args.max_len + 1))
        print(f"[*] Brute-force: {args.min_len}-{args.max_len} letters ({total_bf} combos)")
        
        suffixes = [s.strip() for s in args.suffix.split(",") if s.strip()]
        bf_count = 0
        start = time.time()
        for name in generate_bruteforce(args.min_len, args.max_len, args.chars):
            names.add(name)
            bf_count += 1
            for s in suffixes:
                names.add(f"{name}{s}")
                names.add(f"{name.upper()}{s}")
            if bf_count % 500000 == 0:
                elapsed = time.time() - start
                print(f"[*] Generated {bf_count}/{total_bf} brute-force variants ({elapsed:.0f}s)")
                sys.stdout.flush()

    if not names:
        print("[-] No names to scan. Use -w <wordlist> and/or --bruteforce")
        sys.exit(1)

    variants = sorted(names, key=lambda x: (len(x), x))
    
    print(f"[*] Scanning http://{args.server}/")
    print(f"[*] {len(variants)} total names to check")
    print(f"[*] threads={args.threads}, timeout={args.timeout}s")
    sys.stdout.flush()

    found = []
    seen = set()
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(check_channel, base_url, n, args.token, args.timeout): n for n in variants}
        done = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            done += 1
            result = future.result()
            if result:
                name, url = result
                if url not in seen:
                    seen.add(url)
                    found.append((name, url))
                    print(f"[+] {name}")
                    sys.stdout.flush()
            if done % 2000 == 0 or done == total:
                elapsed = time.time() - start
                pct = done / total * 100
                rps = done / elapsed if elapsed else 0
                eta = (total - done) / rps if rps else 0
                print(f"[*] {done}/{total} ({pct:.1f}%) {elapsed:.0f}s {rps:.0f}req/s ETA {eta:.0f}s found={len(found)}")
                sys.stdout.flush()

    elapsed = time.time() - start
    print(f"\n[+] Done in {elapsed:.0f}s, found {len(found)}")
    for name, url in sorted(found, key=lambda x: x[0]):
        print(f"    {name:30s} {url}")
    if args.output and found:
        with open(args.output, "w") as f:
            for name, url in sorted(found, key=lambda x: x[0]):
                f.write(f"{url}\n")

if __name__ == "__main__":
    main()
