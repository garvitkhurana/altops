"""
Migration reconciliation.

The actual product. A loader moves rows from the old system into the new one; its
job is to map columns, not to ask whether the values are true. So whatever was
wrong in the legacy system arrives in the new platform intact and becomes
permanent, because nothing downstream ever re-checks a loaded balance against the
source document again.

This reconciles the legacy export against the documents themselves and produces a
break report: what disagrees, by how much, which document proves it, and what the
fix is. Every break carries a citation, because "your NAV is wrong" is an argument
and "your NAV is wrong, here is the statement, here is the missing call" is a
work item.

Break severities:
  critical - a cash or commitment figure is wrong; it will misstate the portfolio
  high     - a position is duplicated or unsupported; the ledger is structurally wrong
  medium   - a value is stale or a currency is mislabelled
"""

import csv
import os
from datetime import date

import entities

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 1.00  # dollars; below this we do not care


def _f(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (ValueError, AttributeError):
        return None


def load_legacy(path=os.path.join(HERE, "legacy_export.csv")):
    with open(path) as f:
        return list(csv.DictReader(f))


def reconcile_migration(legacy_rows, recon, results):
    """
    legacy_rows : what the old system believes
    recon       : document-derived positions from pipeline.reconcile()
    results     : per-document extraction results, for citations
    """
    doc_positions = {p["fund"]: p for p in recon["positions"]}

    # Match legacy names onto document-derived fund entities. This is the step
    # every loader skips, and it is why portfolios arrive double-counted.
    all_names = list(doc_positions) + [r["fund_name"] for r in legacy_rows]
    mapping, _ = entities.resolve(all_names)

    def match(legacy_name):
        canon = mapping.get(legacy_name, legacy_name)
        if canon in doc_positions:
            return canon
        key = entities._norm(legacy_name)
        for fund in doc_positions:
            if entities._norm(fund) == key:
                return fund
            if entities._digits(entities._norm(fund)) == entities._digits(key) and (
                    key in entities._norm(fund) or entities._norm(fund) in key):
                return fund
        return None

    breaks = []
    seen = {}
    matched_funds = set()

    for row in legacy_rows:
        name = row["fund_name"]
        fund = match(name)

        if fund is None:
            breaks.append({
                "severity": "high", "type": "unsupported_position",
                "legacy_fund": name, "fund": None,
                "detail": "Position exists in the legacy system with no supporting "
                          "document in the migration set.",
                "legacy_value": _f(row["called_to_date"]),
                "document_value": None, "delta": None,
                "evidence": [],
                "fix": "Obtain the capital account statement and call notices from "
                       "the GP, or confirm the position was transferred out and "
                       "should not migrate.",
            })
            continue

        # Duplicate detection: two legacy rows resolving to one real fund.
        if fund in seen:
            breaks.append({
                "severity": "high", "type": "duplicate_position",
                "legacy_fund": name, "fund": fund,
                "detail": f"Legacy rows '{seen[fund]}' and '{name}' are the same "
                          f"fund. Loading both double-counts the commitment.",
                "legacy_value": _f(row["commitment"]),
                "document_value": doc_positions[fund].get("commitment"),
                "delta": None, "evidence": [],
                "fix": f"Merge into a single position under '{fund}' before load.",
            })
            continue
        seen[fund] = name
        matched_funds.add(fund)

        p = doc_positions[fund]
        cites = [c["file"] for c in p.get("calls", [])][:3]

        # --- called to date -------------------------------------------------
        lg, dv = _f(row["called_to_date"]), p.get("called")
        if lg is not None and dv is not None and abs(lg - dv) > TOL:
            delta = dv - lg
            missing = [c for c in p.get("calls", [])
                       if abs((c.get("amount") or 0) - abs(delta)) < TOL]
            d = (f"Legacy called-to-date is short by {abs(delta):,.2f}."
                 if delta > 0 else
                 f"Legacy called-to-date exceeds the documents by {abs(delta):,.2f}.")
            if missing:
                d += (f" This equals capital call {missing[0]['file']} "
                      f"({missing[0]['amount']:,.2f}, due {missing[0]['due']}), "
                      f"which was never keyed.")
            breaks.append({
                "severity": "critical", "type": "called_to_date_mismatch",
                "legacy_fund": name, "fund": fund, "detail": d,
                "legacy_value": lg, "document_value": dv, "delta": delta,
                "evidence": [m["file"] for m in missing] or cites,
                "fix": "Post the missing capital call before go-live. Unfunded "
                       "commitment is overstated until you do.",
            })

        # --- distributions ---------------------------------------------------
        lg, dv = _f(row["distributed"]), p.get("distributed")
        if lg is not None and dv is not None and abs(lg - dv) > TOL:
            delta = dv - lg
            same_digits = sorted(f"{lg:.2f}") == sorted(f"{dv:.2f}")
            d = f"Legacy distributions differ from the documents by {abs(delta):,.2f}."
            if same_digits:
                d += (" Both values contain identical digits — this is a "
                      "transposition, not a missing transaction.")
            breaks.append({
                "severity": "critical", "type": "distribution_mismatch",
                "legacy_fund": name, "fund": fund, "detail": d,
                "legacy_value": lg, "document_value": dv, "delta": delta,
                "evidence": [x["file"] for x in p.get("distributions", [])][:3],
                "fix": "Correct to the documented value before load.",
            })

        # --- commitment -------------------------------------------------------
        lg, dv = _f(row["commitment"]), p.get("commitment")
        if lg is not None and dv is not None and abs(lg - dv) > TOL:
            breaks.append({
                "severity": "critical", "type": "commitment_mismatch",
                "legacy_fund": name, "fund": fund,
                "detail": f"Commitment disagrees with the subscription amount "
                          f"stated on the fund's own notices by {abs(dv - lg):,.2f}.",
                "legacy_value": lg, "document_value": dv, "delta": dv - lg,
                "evidence": cites,
                "fix": "Confirm against the subscription agreement before load.",
            })

        # --- currency ---------------------------------------------------------
        lg_ccy = (row.get("currency") or "").upper()
        doc_ccy = (p.get("currency") or "").upper()
        if lg_ccy and doc_ccy and lg_ccy != doc_ccy:
            breaks.append({
                "severity": "medium", "type": "currency_mismatch",
                "legacy_fund": name, "fund": fund,
                "detail": f"Legacy records this position as {lg_ccy}; the fund "
                          f"reports in {doc_ccy}. The amount appears to have been "
                          f"carried at face value with no conversion.",
                "legacy_value": None, "document_value": None, "delta": None,
                "evidence": cites,
                "fix": f"Reload as {doc_ccy} and apply the correct rate at each "
                       f"transaction date, not a single spot rate.",
            })

        # --- NAV staleness ------------------------------------------------------
        lg_nav, doc_nav = _f(row["nav"]), p.get("latest_nav")
        lg_date, doc_date = row.get("nav_date"), p.get("nav_date")
        if doc_date and lg_date and lg_date < doc_date:
            breaks.append({
                "severity": "medium", "type": "stale_nav",
                "legacy_fund": name, "fund": fund,
                "detail": f"Legacy NAV is as of {lg_date}; a more recent capital "
                          f"account statement exists as of {doc_date}.",
                "legacy_value": lg_nav, "document_value": doc_nav,
                "delta": (doc_nav - lg_nav) if (doc_nav and lg_nav) else None,
                "evidence": cites,
                "fix": f"Migrate the {doc_date} valuation.",
            })
        elif lg_nav is not None and doc_nav is not None and abs(lg_nav - doc_nav) > TOL:
            breaks.append({
                "severity": "critical", "type": "nav_mismatch",
                "legacy_fund": name, "fund": fund,
                "detail": f"Legacy NAV disagrees with the capital account statement "
                          f"for the same date by {abs(doc_nav - lg_nav):,.2f}.",
                "legacy_value": lg_nav, "document_value": doc_nav,
                "delta": doc_nav - lg_nav, "evidence": cites,
                "fix": "Reconcile to the statement before load.",
            })

    # Positions we have documents for that the legacy export omits entirely.
    for fund, p in doc_positions.items():
        if fund not in matched_funds:
            breaks.append({
                "severity": "high", "type": "missing_from_legacy",
                "legacy_fund": None, "fund": fund,
                "detail": "Documents exist for this fund but it does not appear in "
                          "the legacy export. It would be dropped by the migration.",
                "legacy_value": None, "document_value": p.get("called"),
                "delta": None,
                "evidence": [c["file"] for c in p.get("calls", [])][:3],
                "fix": "Add the position to the load file.",
            })

    order = {"critical": 0, "high": 1, "medium": 2}
    breaks.sort(key=lambda b: (order.get(b["severity"], 9), b["type"]))

    cash = sum(abs(b["delta"]) for b in breaks
               if b["delta"] and b["type"] in (
                   "called_to_date_mismatch", "distribution_mismatch",
                   "commitment_mismatch", "nav_mismatch"))

    return {
        "breaks": breaks,
        "summary": {
            "legacy_positions": len(legacy_rows),
            "document_positions": len(doc_positions),
            "matched": len(matched_funds),
            "total_breaks": len(breaks),
            "critical": sum(1 for b in breaks if b["severity"] == "critical"),
            "high": sum(1 for b in breaks if b["severity"] == "high"),
            "medium": sum(1 for b in breaks if b["severity"] == "medium"),
            "clean_positions": len(matched_funds) - len(
                {b["fund"] for b in breaks if b["fund"]}),
            "cash_at_risk": round(cash, 2),
        },
    }


if __name__ == "__main__":
    import json
    import pipeline

    results = pipeline.process_dir(os.path.join(HERE, "corpus"))
    recon = pipeline.reconcile(results, today=date(2026, 7, 27))

    import legacy_export
    legacy_export.build()

    out = reconcile_migration(load_legacy(), recon, results)
    s = out["summary"]
    print(f"\nMIGRATION RECONCILIATION")
    print(f"  legacy positions   {s['legacy_positions']}")
    print(f"  document positions {s['document_positions']}")
    print(f"  breaks             {s['total_breaks']}  "
          f"({s['critical']} critical / {s['high']} high / {s['medium']} medium)")
    print(f"  cash at risk       ${s['cash_at_risk']:,.2f}\n")
    for b in out["breaks"]:
        print(f"  [{b['severity'].upper():8s}] {b['type']}")
        print(f"    {b['fund'] or b['legacy_fund']}")
        print(f"    {b['detail']}")
        if b["evidence"]:
            print(f"    evidence: {', '.join(b['evidence'][:2])}")
        print()
