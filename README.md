# HLS Stream Scanner

Scans streaming servers for accessible HLS channels by probing `/{name}/index.m3u8?token={token}` URLs.

## Requirements

```
pip3 install requests
```

## Usage

### Basic scan with wordlist

```
python3 scan_final.py <IP:PORT> -w wordlist.txt
```

### Specify token and concurrency

```
python3 scan_final.py <IP:PORT> -w wordlist.txt -t test --threads 50 --timeout 5
```

### Brute-force short names (3-4 letters)

```
python3 scan_final.py <IP:PORT> --bruteforce --min-len 3 --max-len 4 --threads 200
```

### Brute-force with custom suffixes

```
python3 scan_final.py <IP:PORT> --bruteforce --suffix "_HD,HD,_TV" --min-len 3 --max-len 5
```

### Save results to file

```
python3 scan_final.py <IP:PORT> -w wordlist.txt -o found_channels.txt
```

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `server` | (required) | Server `IP:PORT` |
| `-t` / `--token` | `test` | Auth token appended to URL |
| `-w` / `--wordlist` | — | Wordlist file (one name per line) |
| `--bruteforce` | off | Enumerate all letter combinations |
| `--min-len` | `3` | Minimum brute-force length |
| `--max-len` | `4` | Maximum brute-force length |
| `--chars` | `a-z` | Character set for brute-force |
| `--suffix` | `_HD` | Comma-separated suffixes (appended to each brute-force name + uppercase variant) |
| `--threads` | `200` | Concurrent request count |
| `--timeout` | `1.5s` | Request timeout |
| `-o` / `--output` | — | Write found URLs to file (one per line) |

## How it works

1. Each channel name is tested at `http://server/{name}/index.m3u8?token={token}`
2. First a HEAD request — if it returns 200, a GET follows
3. A channel is confirmed if GET returns 200 with content longer than 20 bytes
4. Wordlist + brute-force names are merged, deduplicated, and sorted by length then alphabetically

## Wordlist format

Plain text, one name per line. Lines starting with `#` are ignored. Case-sensitive — the URL path uses the exact name as given.
