"""Collect agency records from the Clutch.co /agencies directory.

Usage:
  python scrape.py --pages 1,120,260 --out agencies.json
  python scrape.py --pages 1-5 --out agencies.json --no-resolve

Listing pages give most fields. When a listing row has no website link, the
company's profile page is fetched once to resolve it (skip with --no-resolve).
"""
import argparse, json, random, threading, time
from concurrent.futures import ThreadPoolExecutor

from curl_cffi import requests as cr

from extract import parse_page, website_from_profile, domain_of

LISTING = "https://clutch.co/agencies?page={page}"
tl = threading.local()


def sess(new=False):
    if new or not hasattr(tl, "s"):
        tl.s = cr.Session(impersonate="chrome120")
    return tl.s


def get(url, tries=3):
    """GET with exponential backoff; a fresh session is used on every retry."""
    for a in range(tries):
        try:
            r = sess(a > 0).get(url, timeout=45)
            if r.status_code == 200:
                return r.text
            time.sleep(5 * (2 ** a) + random.random())
        except Exception:
            time.sleep(5 * (2 ** a))
    return None


def parse_pages(spec):
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages += range(int(a), int(b) + 1)
        else:
            pages.append(int(part))
    return pages


def fill_website(rec, pause):
    if rec["domain"] or not rec["clutch_profile"]:
        return rec
    t = get(rec["clutch_profile"])
    if t:
        u = website_from_profile(t)
        if u:
            rec["domain"], rec["website"] = domain_of(u), u.split("?")[0]
    time.sleep(pause)
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", default="1", help="comma list and/or ranges, e.g. 1,120,260 or 1-5")
    ap.add_argument("--out", default="agencies.json")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between listing pages")
    ap.add_argument("--no-resolve", action="store_true", help="do not visit profile pages for missing websites")
    args = ap.parse_args()

    t0 = time.time()
    rows = []
    for p in parse_pages(args.pages):          # sequential, paced
        t = get(LISTING.format(page=p))
        if t:
            rows += parse_page(t)
        else:
            print(f"page {p}: no response, skipped", flush=True)
        time.sleep(args.pause)

    recs = list({r["_pid"]: r for r in rows}.values())   # de-duplicate on the directory's own id
    print(f"listing rows {len(rows)} -> {len(recs)} unique companies", flush=True)

    if not args.no_resolve:
        need = [r for r in recs if not r["domain"]]
        print(f"resolving {len(need)} missing websites from profile pages", flush=True)
        with ThreadPoolExecutor(2) as ex:
            list(ex.map(lambda r: fill_website(r, 0.6), need))

    for r in recs:
        r.pop("_pid", None)
    recs.sort(key=lambda r: r["company_name"].lower())
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)

    n = len(recs) or 1
    for k in ("domain", "location", "employees", "min_project_size", "avg_hourly_rate", "rating"):
        got = sum(1 for r in recs if r.get(k))
        print(f"  {k:18s} {got}/{len(recs)} ({got / n * 100:.0f}%)")
    print(f"wrote {args.out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
