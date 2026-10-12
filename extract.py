"""Clutch.co /agencies extractor — clean field parsing."""
import re, html as H, urllib.parse as UP

SPLIT = re.compile(r'<div\s+class="provider provider-row')
RED   = re.compile(r'r\.clutch\.co/redirect\?[^"]*?&amp;u=([^"&]+)')

def _txt(x):
    return H.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x))).strip()

def _highlight(block, cls):
    """Value of a provider__highlights-item: text after the icon <span>."""
    m = re.search(r'class="[^"]*provider__highlights-item[^"]*\b' + cls + r'\b', block)
    if not m: return ""
    seg = block[m.end():m.end() + 900]
    v = re.search(r'-icon[^"]*"></span>(.*?)<', seg, re.S)
    return _txt(v.group(1)) if v else ""

def _meta(block, prop):
    m = re.search(r'<meta itemprop="' + prop + r'" content="([^"]*)"', block)
    return H.unescape(m.group(1)).strip() if m else ""

def domain_of(u):
    return UP.urlparse(u).netloc.lower().removeprefix("www.")

def parse_page(t):
    rows = []
    for raw in SPLIT.split(t)[1:]:
        pid = re.search(r'data-clutch-pid="(\d+)"', raw)
        title = re.search(r'data-title="([^"]*)"', raw)
        if not (pid and title): continue
        b = re.sub(r'<script.*?</script>', '', raw, flags=re.S)
        prof = re.search(r'href="(/profile/[^"#?]+)', b)
        u = RED.search(b)
        web = UP.unquote(H.unescape(u.group(1))) if u else ""
        rating = re.search(r'class="sg-rating__number"[^>]*>\s*([0-9](?:\.[0-9])?)', b)
        revs = re.search(r'([\d,]+)\s+reviews?\b', b)
        city, country = _meta(b, "addressLocality"), _meta(b, "addressCountry")
        loc = _highlight(b, "location") or ", ".join(x for x in (city, country) if x)
        rows.append({
            "company_name": H.unescape(title.group(1)).strip(),
            "domain": domain_of(web),
            "website": web.split("?")[0],
            "city": city,
            "country": country,
            "location": loc,
            "employees": _highlight(b, "employees-count"),
            "min_project_size": _highlight(b, "min-project-size"),
            "avg_hourly_rate": _highlight(b, "hourly-rate"),
            "rating": rating.group(1) if rating else "",
            "reviews": revs.group(1).replace(",", "") if revs else "0",
            "clutch_profile": "https://clutch.co" + prof.group(1) if prof else "",
            "_pid": pid.group(1),
        })
    return rows

def website_from_profile(t):
    for x in RED.findall(t):
        u = UP.unquote(H.unescape(x))
        if domain_of(u): return u
    return ""
