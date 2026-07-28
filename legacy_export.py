"""
Generate a legacy-system export -- the file you get handed on day one of a
portfolio migration.

Loaders will map these columns into the new platform without complaint. That is
the problem: the loader's job is to move rows, not to ask whether the rows are
true. Every error below is one I would expect to survive a migration and become
permanent in the new system, because nothing downstream ever checks the loaded
balance against the source document again.

The errors seeded here are the realistic ones:

  - a capital call that was never keyed, so called-to-date is short
  - a fund carried twice under two name variants, double-counting commitment
  - a stale NAV from a prior quarter presented as current
  - a transposed digit in a distribution
  - a commitment recorded in the wrong currency at face value
  - a fund in the export with no supporting document at all
"""

import csv
import json
import os
import random

random.seed(20260727)
HERE = os.path.dirname(os.path.abspath(__file__))

# Ground truth comes from the documents; this is what the OLD system believes.
LEGACY_ROWS = [
    # (legacy_fund_name, commitment, called_to_date, distributed, nav, nav_date, ccy)
    ("Brookmont Capital Partners IV LP", 5_000_000, 2_161_510.46, None, None, None, "USD"),
    ("Ardent Growth Fund III LP", 3_000_000, 1_656_434.55, None, None, None, "USD"),
    # Same fund as above under an abbreviation -- classic double-count.
    ("Ardent Gr Fd III", 3_000_000, 0.0, 0.0, 0.0, "2026-03-31", "USD"),
    ("Kestrel Private Credit Fund II LP", 7_500_000, 2_542_937.85, None, None, None, "USD"),
    ("Halloway Real Assets Partners LP", 2_500_000, 1_313_845.44, None, None, None, "USD"),
    ("Sable Ventures Opportunity Fund I", 1_000_000, 499_990.69, None, None, None, "USD"),
    # EUR commitment recorded at face value with a USD currency code.
    ("Northgate Infrastructure Partners II SCSp", 4_000_000, 2_213_785.74, None, None, None, "USD"),
    # A position in the old system with no documents behind it at all.
    ("Westmere Credit Opportunities II LP", 1_500_000, 600_000.00, 125_000.00, 540_000.00, "2026-03-31", "USD"),
]


def build(results_path=os.path.join(HERE, "results.json"),
          out=os.path.join(HERE, "legacy_export.csv")):
    """Derive a legacy export from document truth, then damage it realistically."""
    truth = {}
    if os.path.exists(results_path):
        d = json.load(open(results_path))
        for p in d["reconciliation"]["positions"]:
            truth[p["fund"]] = p

    rows = []
    for (name, commit, called, dist, nav, nav_date, ccy) in LEGACY_ROWS:
        # Fill unknown fields from document truth where we can, then corrupt.
        match = None
        for k, v in truth.items():
            if k.split()[0].lower() == name.split()[0].lower():
                match = v
                break
        if dist is None:
            dist = round((match or {}).get("distributed") or 0.0, 2)
        if nav is None:
            nav = round((match or {}).get("latest_nav") or 0.0, 2)
        if nav_date is None:
            nav_date = (match or {}).get("nav_date") or "2026-03-31"
        rows.append({
            "fund_name": name, "commitment": f"{commit:.2f}",
            "called_to_date": f"{called:.2f}", "distributed": f"{dist:.2f}",
            "nav": f"{nav:.2f}", "nav_date": nav_date, "currency": ccy,
        })

    # --- seed the errors -------------------------------------------------
    def find(prefix):
        return next(r for r in rows if r["fund_name"].startswith(prefix))

    # 1. Missing capital call: knock the most recent call off Kestrel.
    k = find("Kestrel")
    k["called_to_date"] = f"{float(k['called_to_date']) - 808_932.60:.2f}"

    # 2. Transposed digits in a Halloway distribution (e.g. 45,900 -> 49,500).
    h = find("Halloway")
    if float(h["distributed"]) > 0:
        s = f"{float(h['distributed']):.2f}"
        digits = list(s)
        for i in range(len(digits) - 1):
            if digits[i].isdigit() and digits[i + 1].isdigit() and digits[i] != digits[i + 1]:
                digits[i], digits[i + 1] = digits[i + 1], digits[i]
                break
        h["distributed"] = "".join(digits)

    # 3. Stale NAV: Brookmont carries a Q4 value labelled as current.
    b = find("Brookmont")
    b["nav"] = f"{float(b['nav']) * 0.93:.2f}"
    b["nav_date"] = "2025-12-31"

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return out, rows


if __name__ == "__main__":
    path, rows = build()
    print(f"Wrote {len(rows)} legacy positions -> {path}")
    for r in rows:
        print(f"  {r['fund_name'][:44]:46s} called={float(r['called_to_date']):>12,.0f}")
