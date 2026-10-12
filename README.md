# Agency Directory Scraper

Collects company records from the [Clutch.co](https://clutch.co/agencies) agency directory and
delivers them as clean JSON, CSV and a formatted Excel workbook.

Built as a lead-list sample: one row per company, de-duplicated, with the company's own
website domain resolved rather than the directory's redirect link.

## What you get

| Field | Example |
|---|---|
| `company_name` | (W)right On Communications |
| `domain` | wrightoncomm.com |
| `website` | https://www.wrightoncomm.com/ |
| `city`, `country`, `location` | San Diego, US, "San Diego, CA" |
| `employees` | 10 - 49 |
| `min_project_size` | $5,000+ |
| `avg_hourly_rate` | $200 - $300 / hr |
| `rating`, `reviews` | 5.0, 6 |
| `clutch_profile` | https://clutch.co/profile/wright-communications |

`sample/` holds a 587-company run:

- `agencies_sample.csv` / `.json`: all 587 records
- `agencies_sample_100.xlsx`: 100 records sliced evenly across the alphabet, formatted for handover
  (frozen header, filters, banded rows)

That sample was collected with an earlier version of the parser and carries eight fields;
location and rating were not captured reliably then and are left out of it. The current
parser in `extract.py` adds them: on a one-page check (85 companies) it filled location
for 95% and rating for 65% (companies with no reviews have no rating).

## Usage

```bash
pip install -r requirements.txt

# listing pages 1, 120 and 260 -> agencies.json
python scrape.py --pages 1,120,260 --out agencies.json

# formatted workbook; optional third argument limits the row count
python build_xlsx.py agencies.json agencies.xlsx
python build_xlsx.py agencies.json agencies_100.xlsx 100
```

`scrape.py` prints a fill rate per field at the end of every run, so gaps are visible
before the file is handed over.

## How it works

- **`extract.py`** parses listing pages with anchored regular expressions on the row
  markup and schema.org `itemprop` metadata. The website comes from the directory's
  redirect link, unwrapped and URL-decoded, so `domain` is the company's real domain.
- **`scrape.py`** fetches listing pages sequentially with a pause between them, retries
  with exponential backoff on a fresh session, and de-duplicates on the directory's own
  company id (the same company can appear on several pages as a sponsored row). Rows
  without a website link get one extra request to the profile page.
- **`build_xlsx.py`** strips leftover markup, drops any optional column that is less
  than half filled instead of shipping a mostly empty one, and writes the workbook.

## Notes

- Request pacing is deliberately slow. Sampling the directory in parallel got the client
  rate-limited during development, which is why listing pages are now fetched one at a time.
- Data is public business-listing information. Check the site's terms and your own use
  case before running large collections.
