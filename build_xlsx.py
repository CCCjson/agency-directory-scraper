"""Build a formatted XLSX from collected records.

Usage: python build_xlsx.py agencies.json agencies.xlsx [limit]
"""
import json, re, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = sys.argv[1] if len(sys.argv) > 1 else "agencies.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "agencies.xlsx"

def clean(v):
    """Strip markup artefacts left by attribute-boundary captures."""
    return re.sub(r'^["\s>]+', '', str(v)).strip()

recs = json.load(open(SRC))
for r in recs:
    for k in r: r[k] = clean(r[k])
recs.sort(key=lambda r: r["company_name"].lower())
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else len(recs)
step = max(1, len(recs) // LIMIT)
recs = recs[::step][:LIMIT]   # even slice across the alphabet when a limit is given

# only ship columns that are actually populated
BASE = [("company_name","Company Name",36), ("domain","Domain",30), ("website","Website",46)]
OPT  = [("location","Location",26), ("employees","Employees",13),
        ("min_project_size","Min. Project Size",18), ("avg_hourly_rate","Avg. Hourly Rate",20),
        ("rating","Rating",9), ("reviews","Reviews",10), ("clutch_profile","Clutch Profile",46)]
cols = BASE + [c for c in OPT
               if c[0] in recs[0] and sum(1 for r in recs if r.get(c[0], "").strip()) >= len(recs) * 0.5]

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Agencies"
ws.append([c[1] for c in cols])
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF", size=11)
    c.fill = PatternFill("solid", fgColor="0D4F4A")
    c.alignment = Alignment(vertical="center", horizontal="left", indent=1)
ws.row_dimensions[1].height = 26

thin = Side(style="thin", color="DDE3E6")
band = PatternFill("solid", fgColor="F4F7F7")
for i, r in enumerate(recs):
    ws.append([r.get(k, "") for k, _, _ in cols])
    row = ws[ws.max_row]
    for c in row:
        c.border = Border(bottom=thin)
        c.alignment = Alignment(vertical="center", indent=1)
        if i % 2: c.fill = band
    for j, (k, _, _) in enumerate(cols):
        if k == "domain": row[j].font = Font(name="Menlo", size=10, color="0D4F4A")
        if k in ("rating", "reviews", "employees"):
            row[j].alignment = Alignment(horizontal="center", vertical="center")
        if k in ("website", "clutch_profile"):
            row[j].font = Font(size=9, color="5B6672")

for i, (_, _, w) in enumerate(cols, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
wb.save(OUT)
print(f"{OUT}\n  rows={len(recs)}  columns={[c[1] for c in cols]}")
for k, name, _ in cols:
    f = sum(1 for r in recs if r.get(k, "").strip())
    print(f"    {name:20s} {f:3d}/{len(recs)}")
