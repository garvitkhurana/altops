"""
Facility engine.

The credit agreement is a specification, not a record. It defines the optionality:
permitted interest periods, the pricing grid, the day-count convention, minimum
borrowing amounts, required notice periods, availability. So every borrowing
notice and every agent rate-set has a CORRECT ANSWER derivable from the agreement.

Today an operator keys facility terms into an Excel template at setup, and from
then on nobody re-derives anything -- the agent's number is trusted because
re-deriving it by hand, per notice, is not feasible.

This does two things:
  1. Extract the facility spec from the agreement, once, with citations.
  2. For every notice thereafter, independently recompute and compare.

That second step is the product. It is not extraction; it is a second opinion
with money attached.
"""

import os
import re
from datetime import date, datetime, timedelta

from pypdf import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "credit_corpus")


def read_pdf(path):
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)


def _money(s):
    return float(re.sub(r"[^\d.]", "", s)) if s else None


# ------------------------------------------------------------ facility spec

EXTRACT_SYS = """You read private credit agreements and extract the facility terms \
that govern every downstream calculation. You are building a specification, not a \
summary.

Return JSON only:
{
  "borrower": str,
  "administrative_agent": str,
  "tranches": {"<facility name>": <commitment as number>},
  "permitted_interest_periods": [ints, in months],
  "day_count_sofr": int,
  "day_count_base": int,
  "credit_spread_adjustment": {"<months>": <percent as number>},
  "pricing_grid": [{"min_leverage": num|null, "max_leverage": num|null,
                    "margin": num}],
  "minimum_borrowing": num,
  "borrowing_multiple": num,
  "notice_days_sofr": int,
  "lc_sublimit": num,
  "_citations": {"<field>": {"section": "<e.g. 3.02>", "quote": "<verbatim>"}}
}

Rules:
- Percentages as plain numbers: 5.75 not "5.75%".
- Amounts as plain numbers: 75000000 not "$75,000,000.00".
- pricing_grid tiers: min_leverage is the exclusive lower bound ("Greater than"),
  max_leverage the inclusive upper bound ("less than or equal to" / "≤").
  Use null for an open end. Margin rises with leverage, so:
    Greater than 5.00 : 1.00          → {"min_leverage": 5.0, "max_leverage": null, "margin": 5.75}
    Greater than 4.00 but ≤ 5.00      → {"min_leverage": 4.0, "max_leverage": 5.0, "margin": 5.25}
    Less than or equal to 3.00 : 1.00 → {"min_leverage": null, "max_leverage": 3.0, "margin": 4.25}
  Never put the highest-margin tier on a max-only (≤) open end.
- credit_spread_adjustment keys must be integer months: 1, 3, 6 — never
  "One month" / "1mo".
- Every field you populate needs a _citations entry with the section number and
  the verbatim sentence. If you cannot find a term, omit it rather than guess.
- You are extracting terms ONLY. Never compute interest. A separate deterministic
  engine does the arithmetic, because that is where models are unreliable."""


def list_facilities(corpus=CORPUS):
    """Agreements available in the corpus — for the demo facility picker."""
    out = []
    for fn in sorted(os.listdir(corpus)):
        if not (fn.startswith("CreditAgreement") and fn.lower().endswith(".pdf")):
            continue
        label = (fn.replace("CreditAgreement_", "")
                   .replace(".pdf", "")
                   .replace("_", " "))
        out.append({"id": fn, "label": label, "file": fn})
    return out


def extract_facility_llm(text, provider=None):
    """
    LLM extraction path. The model reads the agreement and returns terms with
    clause citations -- and nothing else. It never does arithmetic.

    That division is the whole architecture: language work goes to the model,
    arithmetic goes to code that can be tested. An LLM asked to compute
    principal x (SOFR + CSA + margin) x days/360 will produce something
    plausible, and plausible is worthless when the output is a dollar figure
    someone disputes with their agent.
    """
    try:
        import pipeline
        client = pipeline._client(provider=provider)
        if client is None:
            return None, None, None, "no provider configured"
        used = provider or pipeline._provider()
        model = pipeline._model_for(used, honor_env_model=provider is None)
        raw = pipeline._ask(
            client, EXTRACT_SYS,
            f"<credit_agreement>\n{text[:24000]}\n</credit_agreement>", 3000,
            model=model)

        cites = raw.pop("_citations", {}) or {}
        F = {}
        for k, v in raw.items():
            if v in (None, "", [], {}):
                continue
            if k == "credit_spread_adjustment" and isinstance(v, dict):
                csa = {}
                for mk, mv in v.items():
                    mo = _as_months(mk)
                    if mo is None:
                        continue
                    try:
                        csa[mo] = float(mv)
                    except (TypeError, ValueError):
                        continue
                if csa:
                    F[k] = csa
            elif k == "tranches" and isinstance(v, dict):
                F[k] = {str(tk): float(tv) for tk, tv in v.items()
                        if tv not in (None, "")}
            elif k == "pricing_grid" and isinstance(v, list):
                F[k] = normalize_pricing_grid(v)
            else:
                F[k] = v
        return F, cites, used, None
    except Exception as e:
        return None, None, None, f"{type(e).__name__}: {str(e)[:160]}"


def _as_months(key):
    """Normalize CSA keys like 1, '1', '1mo', 'One month' -> int months."""
    if isinstance(key, (int, float)):
        return int(key)
    s = str(key).strip().lower()
    m = re.search(r"\d+", s)
    if m:
        return int(m.group(0))
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "twelve": 12,
    }
    for w, n in words.items():
        if w in s:
            return n
    return None


def normalize_pricing_grid(grid):
    """
    Fix the failure mode small models hit constantly: swapping the open end of
    a leverage tier. Highest margin belongs on a min-only (Greater than) open
    end; lowest margin on a max-only (≤) open end. Margin rises with leverage.
    """
    if not isinstance(grid, list) or not grid:
        return grid
    out = []
    for t in grid:
        if not isinstance(t, dict) or "margin" not in t:
            continue
        try:
            margin = float(t["margin"])
        except (TypeError, ValueError):
            continue
        lo = t.get("min_leverage")
        hi = t.get("max_leverage")
        lo = float(lo) if lo is not None else None
        hi = float(hi) if hi is not None else None
        out.append({"min_leverage": lo, "max_leverage": hi, "margin": margin})
    if not out:
        return grid

    # Single-bound tiers: flip open end to match margin vs the rest of the grid.
    margins = [t["margin"] for t in out]
    hi_m, lo_m = max(margins), min(margins)
    for t in out:
        lo, hi = t["min_leverage"], t["max_leverage"]
        if lo is None and hi is None:
            continue
        if lo is not None and hi is not None:
            continue
        # One bound set.
        bound = lo if lo is not None else hi
        if t["margin"] == hi_m and abs(hi_m - lo_m) > 1e-9:
            # Top tier: Greater than X
            t["min_leverage"], t["max_leverage"] = bound, None
        elif t["margin"] == lo_m and abs(hi_m - lo_m) > 1e-9:
            # Bottom tier: ≤ X
            t["min_leverage"], t["max_leverage"] = None, bound
    return out


def extract_consensus(text, passes=2, providers=None):
    """
    Run extraction more than once and treat disagreement as a finding.

    The engine catches a wrong calculation. Nothing catches a wrong TERM. If we
    read the margin grid as 4.75% where the agreement says 5.75%, every
    downstream check is confidently wrong forever and the output looks exactly
    as authoritative as a correct one. That is the failure that loses a customer,
    so it gets its own control.

    Terms every pass agrees on are trusted. Terms they disagree on are quarantined
    -- not averaged, not majority-voted, not silently resolved. A human sees the
    clause and decides, because picking a winner between two disagreeing
    extractions is just guessing with extra steps.

    Note this is emphatically NOT "an agent that computes." The arithmetic never
    goes near a model. This is redundancy on the reading, which is the only part
    a model touches.
    """
    runs, errors = [], []

    # Prefer genuinely different models -- two passes of the same model share
    # their blind spots, so agreement between them is weaker evidence.
    if providers:
        for p in providers[:passes]:
            F, c, used, err = extract_facility_llm(text, provider=p)
            (runs.append((used or p, F, c)) if F else errors.append(f"{p}: {err}"))
    else:
        for i in range(passes):
            F, c, used, err = extract_facility_llm(text)
            (runs.append((f"{used or 'llm'} #{i+1}", F, c)) if F
             else errors.append(str(err)))

    if not runs:
        return None, None, None, {"status": "unavailable", "errors": errors}

    det, det_cites = extract_facility(text)
    runs.append(("deterministic", det, det_cites))

    keys = set()
    for _, F, _ in runs:
        keys |= set(F or {})

    agreed, disputed, partial = {}, {}, {}
    cites = {}
    for k in sorted(keys):
        vals = [(name, F[k]) for name, F, _ in runs if F and k in F]
        if len(vals) < 2:
            # Only one source saw it. Usable, but flagged as unconfirmed.
            partial[k] = {"value": vals[0][1], "source": vals[0][0]}
            agreed[k] = vals[0][1]
        elif all(_same(v, vals[0][1]) for _, v in vals):
            agreed[k] = vals[0][1]
        else:
            disputed[k] = {name: v for name, v in vals}
        for name, F, c in runs:
            if c and k in c and k not in cites:
                cites[k] = c[k]

    return agreed, cites, disputed, {
        "status": "ok",
        "passes": [name for name, _, _ in runs],
        "agreed": len(agreed) - len(partial),
        "unconfirmed": len(partial),
        "disputed": len(disputed),
        "partial_terms": partial,
        "errors": errors,
    }


def _same(a, b, tol=1e-6):
    """Structural equality, tolerant of float representation."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_same(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        # pricing grids often come in different row order; compare as a set of
        # canonical tiers when every element is a dict with a margin.
        if a and all(isinstance(x, dict) and "margin" in x for x in a):
            def key(t):
                return (t.get("min_leverage") is None, t.get("min_leverage") or 0,
                        t.get("max_leverage") is None, t.get("max_leverage") or 0,
                        t.get("margin") or 0)
            aa, bb = sorted(a, key=key), sorted(b, key=key)
            return len(aa) == len(bb) and all(_same(x, y, tol) for x, y in zip(aa, bb))
        return len(a) == len(b) and all(_same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def extract_facility(text):
    """
    Parse the agreement into a machine-checkable specification.

    Every term carries the clause it came from, because when we later tell a
    lender their agent is wrong, "Section 3.02" is the difference between an
    argument and a correction.
    """
    F, cite = {}, {}

    def grab(key, pattern, cast=str, section=None, flags=re.I | re.S):
        m = re.search(pattern, text, flags)
        if m:
            raw = m.group(1)
            # PDF text extraction wraps lines mid-name; collapse before casting.
            F[key] = cast(re.sub(r"\s+", " ", raw).strip() if cast is str else raw)
            cite[key] = {"section": section,
                         "quote": re.sub(r"\s+", " ", m.group(0))[:150]}
        return F.get(key)

    grab("borrower", r"among\s+(.+?),\s*as\s*\n?\s*Borrower", str, "Preamble")
    # The agent's legal name contains its own comma ("Sterling\nAgency Services,
    # LLC"), so this cannot be a comma-delimited capture.
    grab("administrative_agent",
         r"and\s+(.+?),?\s*as\s*\n?\s*Administrative Agent", str, "Preamble")

    # Tranche commitments.
    tranches = {}
    for name in ("Revolving Credit Facility", "Term Loan A",
                 "Delayed Draw Term Loan"):
        m = re.search(re.escape(name) + r"\s*\n?\s*\$?([\d,]+\.\d{2})", text)
        if m:
            tranches[name] = _money(m.group(1))
    if tranches:
        F["tranches"] = tranches
        cite["tranches"] = {"section": "2.01", "quote": "Commitments table"}

    grab("minimum_borrowing",
         r"not less than\s*\n?\s*\$?([\d,]+)", _money, "2.02")
    grab("borrowing_multiple",
         r"integral multiples of\s*\$?([\d,]+)", _money, "2.02")
    # "[^.]" fails here because the clause contains "1:00 p.m." before the number.
    grab("notice_days_sofr",
         r"not later than.*?(\d+)\s+U\.S\.\s*Government Securities Business Days",
         int, "2.02")

    m = re.search(r"Interest Period of\s*\n?\s*([a-z,\s]+?)\s*months?\s*as elected",
                  text, re.I)
    if m:
        words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "nine": 9, "twelve": 12}
        F["permitted_interest_periods"] = [
            words[w] for w in re.findall(r"[a-z]+", m.group(1).lower())
            if w in words]
        cite["permitted_interest_periods"] = {
            "section": "2.03", "quote": re.sub(r"\s+", " ", m.group(0))[:150]}

    # Day-count conventions differ by loan type; getting this wrong is a
    # 1.4% error on every interest payment for the life of the facility.
    m = re.search(r"SOFR Loans shall be computed on the basis of a year of\s*"
                  r"\n?\s*(\d{3})\s*days", text, re.I)
    if m:
        F["day_count_sofr"] = int(m.group(1))
        cite["day_count_sofr"] = {"section": "3.01",
                                  "quote": re.sub(r"\s+", " ", m.group(0))[:150]}
    m = re.search(r"Base Rate Loans shall be computed on the basis of a year of\s*"
                  r"\n?\s*(\d{3})\s*days", text, re.I)
    if m:
        F["day_count_base"] = int(m.group(1))

    # Credit spread adjustment by interest period.
    csa = {}
    for label, months in (("One month", 1), ("Three months", 3), ("Six months", 6)):
        m = re.search(re.escape(label) + r"\s*\n?\s*([\d.]+)%", text, re.I)
        if m:
            csa[months] = float(m.group(1))
    if csa:
        F["credit_spread_adjustment"] = csa
        cite["credit_spread_adjustment"] = {"section": "3.01",
                                            "quote": "Credit Spread Adjustment table"}

    # Pricing grid.
    grid = []
    for m in re.finditer(
            r"Greater than\s*([\d.]+)\s*:\s*1\.00(?:\s*but\s*≤\s*([\d.]+)\s*:\s*1\.00)?"
            r"\s*\n?\s*([\d.]+)%", text, re.I):
        grid.append({"min_leverage": float(m.group(1)),
                     "max_leverage": float(m.group(2)) if m.group(2) else None,
                     "margin": float(m.group(3))})
    m = re.search(r"Less than or equal to\s*([\d.]+)\s*:\s*1\.00\s*\n?\s*([\d.]+)%",
                  text, re.I)
    if m:
        grid.append({"min_leverage": None, "max_leverage": float(m.group(1)),
                     "margin": float(m.group(2))})
    if grid:
        F["pricing_grid"] = grid
        cite["pricing_grid"] = {"section": "3.02",
                                "quote": "Applicable Margin pricing grid"}

    grab("lc_sublimit", r"sublimit of\s*\n?\s*\$?([\d,]+)", _money, "3.03")
    return F, cite


def applicable_margin(facility, leverage):
    """Walk the pricing grid. Returns (margin, tier description)."""
    for tier in facility.get("pricing_grid", []):
        lo, hi = tier["min_leverage"], tier["max_leverage"]
        if lo is not None and hi is not None:
            if lo < leverage <= hi:
                return tier["margin"], f">{lo:.2f}x and <={hi:.2f}x"
        elif lo is not None:
            if leverage > lo:
                return tier["margin"], f">{lo:.2f}x"
        elif hi is not None:
            if leverage <= hi:
                return tier["margin"], f"<={hi:.2f}x"
    return None, None


def business_days_between(d1, d2):
    """Business days strictly between the request and the borrowing date."""
    n, cur = 0, d1
    while cur < d2:
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n


# --------------------------------------------------------- notice checking

def check_borrowing_notice(facility, n, drawn, lcs):
    """Validate a borrowing request against what the agreement permits."""
    breaks = []
    tranche = n["tranche"]
    amt = n["amount"]
    ip = n.get("interest_period")
    bd = date.fromisoformat(n["borrowing_date"])
    rq = date.fromisoformat(n["request_date"])

    permitted = facility.get("permitted_interest_periods") or []
    if ip and permitted and ip not in permitted:
        breaks.append({
            "severity": "critical", "type": "interest_period_not_permitted",
            "detail": f"Borrower elected a {ip}-month Interest Period. The "
                      f"agreement permits only "
                      f"{', '.join(str(p) for p in permitted)} months.",
            "section": "2.03",
            "expected": f"{permitted} months", "actual": f"{ip} months",
            "impact": None,
            "fix": "Reject the request or obtain a waiver before funding. "
                   "Funding a non-conforming Interest Period creates a "
                   "documentation break at the next audit.",
        })

    minimum = facility.get("minimum_borrowing")
    mult = facility.get("borrowing_multiple")
    if minimum and amt < minimum:
        breaks.append({
            "severity": "high", "type": "below_minimum_borrowing",
            "detail": f"Requested ${amt:,.0f} is below the ${minimum:,.0f} minimum.",
            "section": "2.02", "expected": f"${minimum:,.0f}",
            "actual": f"${amt:,.0f}", "impact": None,
            "fix": "Increase the request to the minimum.",
        })
    elif minimum and mult and (amt - minimum) % mult != 0:
        excess = amt - minimum
        breaks.append({
            "severity": "high", "type": "not_integral_multiple",
            "detail": f"Requested ${amt:,.0f}. Amounts above the ${minimum:,.0f} "
                      f"minimum must be in integral multiples of ${mult:,.0f}; "
                      f"${excess:,.0f} is not.",
            "section": "2.02",
            "expected": f"${minimum + (excess // mult) * mult:,.0f} or "
                        f"${minimum + (excess // mult + 1) * mult:,.0f}",
            "actual": f"${amt:,.0f}", "impact": None,
            "fix": "Round the request to a conforming amount before funding.",
        })

    req_days = facility.get("notice_days_sofr")
    if req_days and "SOFR" in (n.get("rate_type") or ""):
        actual = business_days_between(rq, bd)
        if actual < req_days:
            breaks.append({
                "severity": "high", "type": "insufficient_notice",
                "detail": f"Borrowing Request delivered {actual} business day"
                          f"{'s' if actual != 1 else ''} before the proposed "
                          f"Borrowing Date. The agreement requires {req_days} "
                          f"U.S. Government Securities Business Days for SOFR "
                          f"Borrowings.",
                "section": "2.02", "expected": f"{req_days} business days",
                "actual": f"{actual} business days", "impact": None,
                "fix": "Either delay the borrowing date or fund as a Base Rate "
                       "Loan, which requires same-day notice.",
            })

    commitment = (facility.get("tranches") or {}).get(tranche)
    if commitment:
        already = drawn.get(tranche, 0)
        lc = lcs if "Revolv" in tranche else 0
        available = commitment - already - lc
        if amt > available:
            breaks.append({
                "severity": "critical", "type": "exceeds_availability",
                "detail": f"Requested ${amt:,.0f} against ${available:,.0f} of "
                          f"availability (${commitment:,.0f} commitment less "
                          f"${already:,.0f} drawn"
                          + (f" less ${lc:,.0f} of outstanding letters of credit"
                             if lc else "") + ").",
                "section": "2.01", "expected": f"<= ${available:,.0f}",
                "actual": f"${amt:,.0f}", "impact": amt - available,
                "fix": "Reduce the draw or the facility is overdrawn on funding.",
            })
    return breaks


def check_agent_notice(facility, a, leverage):
    """
    Independently recompute the agent's interest calculation.

    This is the part nobody does today, because doing it by hand for every
    notice is not feasible, so the agent's number is simply trusted.
    """
    breaks = []
    ip = a["interest_period"]
    amt = a["amount"]

    exp_margin, tier = applicable_margin(facility, leverage)
    exp_csa = (facility.get("credit_spread_adjustment") or {}).get(ip)
    exp_dc = facility.get("day_count_sofr")

    if exp_margin is not None and abs(a["margin"] - exp_margin) > 1e-9:
        breaks.append({
            "severity": "critical", "type": "wrong_applicable_margin",
            "detail": f"Agent applied {a['margin']:.2f}%. At a Total Net Leverage "
                      f"Ratio of {leverage:.2f}x the grid requires "
                      f"{exp_margin:.2f}% ({tier}).",
            "section": "3.02", "expected": f"{exp_margin:.2f}%",
            "actual": f"{a['margin']:.2f}%", "impact": None,
            "fix": "Re-issue the rate set at the correct tier.",
        })

    if exp_csa is not None and abs(a["csa"] - exp_csa) > 1e-9:
        breaks.append({
            "severity": "critical", "type": "wrong_credit_spread_adjustment",
            "detail": f"Agent applied a Credit Spread Adjustment of "
                      f"{a['csa']:.2f}% for a {ip}-month Interest Period. "
                      f"The agreement specifies {exp_csa:.2f}%.",
            "section": "3.01", "expected": f"{exp_csa:.2f}%",
            "actual": f"{a['csa']:.2f}%", "impact": None,
            "fix": "Re-issue the rate set including the CSA.",
        })

    if exp_dc and a["day_count"] != exp_dc:
        breaks.append({
            "severity": "critical", "type": "wrong_day_count",
            "detail": f"Agent computed interest on an Actual/{a['day_count']} "
                      f"basis. The agreement specifies Actual/{exp_dc} for SOFR "
                      f"Loans.",
            "section": "3.01", "expected": f"Actual/{exp_dc}",
            "actual": f"Actual/{a['day_count']}", "impact": None,
            "fix": "Recompute on the correct basis.",
        })

    # Recompute interest using the agreement's own terms.
    if exp_margin is not None and exp_csa is not None and exp_dc:
        rate = (a["sofr"] + exp_csa + exp_margin) / 100
        expected_interest = amt * rate * a["days"] / exp_dc
        delta = a["interest"] - expected_interest
        if abs(delta) > 0.01:
            who = "overcharged" if delta > 0 else "undercharged"
            breaks.append({
                "severity": "critical", "type": "interest_miscalculation",
                "detail": f"Agent billed ${a['interest']:,.2f}. Recomputing from "
                          f"the agreement — ${amt:,.0f} x "
                          f"({a['sofr']:.5f}% + {exp_csa:.2f}% + "
                          f"{exp_margin:.2f}%) x {a['days']}/{exp_dc} — gives "
                          f"${expected_interest:,.2f}. The lender is {who} by "
                          f"${abs(delta):,.2f} on this period.",
                "section": "3.01",
                "expected": f"${expected_interest:,.2f}",
                "actual": f"${a['interest']:,.2f}",
                "impact": delta,
                "fix": "Dispute the rate set with the Administrative Agent, "
                       "citing Sections 3.01 and 3.02.",
            })
    return breaks


def score_extraction(extracted, gt_facility):
    """
    Gate 1: score the facility spec against the corpus seed.

    The seed authored the PDF, so agreement here means extraction recovered what
    we planted. Production has no seed file -- a human confirms terms at setup.
    """
    # Fields that define the checkable specification (skip operational state).
    keys = [
        "borrower", "administrative_agent", "tranches", "pricing_grid",
        "credit_spread_adjustment", "permitted_interest_periods",
        "day_count_sofr", "day_count_base", "minimum_borrowing",
        "borrowing_multiple", "notice_days_sofr", "lc_sublimit",
    ]
    matched, mismatched, missing = [], [], []
    details = {}

    def norm_csa(v):
        if not isinstance(v, dict):
            return v
        out = {}
        for k, val in v.items():
            try:
                out[int(k)] = float(val)
            except (TypeError, ValueError):
                continue
        return out

    for k in keys:
        exp = gt_facility.get(k)
        if exp is None:
            continue
        if k == "credit_spread_adjustment":
            exp = norm_csa(exp)
        got = extracted.get(k)
        if got is None:
            missing.append(k)
            details[k] = {"status": "missing", "expected": exp, "got": None}
            continue
        if k == "credit_spread_adjustment":
            got = norm_csa(got)
        if _same(got, exp):
            matched.append(k)
            details[k] = {"status": "matched"}
        else:
            mismatched.append(k)
            details[k] = {"status": "mismatched", "expected": exp, "got": got}

    total = len(matched) + len(mismatched) + len(missing)
    return {
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
        "score": f"{len(matched)}/{total}" if total else "0/0",
        "n_matched": len(matched),
        "n_total": total,
        "ok": not mismatched and not missing and total > 0,
        "details": {k: {kk: (str(vv) if not isinstance(vv, (str, int, float, bool, type(None))) else vv)
                        for kk, vv in d.items()} for k, d in details.items()},
    }


# seeded_issue phrase -> break types that count as catching it
_SEEDED_TYPES = {
    "clean": [],
    "correct": [],
    "interest period not permitted": ["interest_period_not_permitted"],
    "not an integral multiple": ["not_integral_multiple"],
    "only 1 day notice": ["insufficient_notice"],
    "exceeds availability": ["exceeds_availability"],
    "wrong margin": ["wrong_applicable_margin", "interest_miscalculation"],
    "wrong day count": ["wrong_day_count", "interest_miscalculation"],
    "credit spread adjustment": ["wrong_credit_spread_adjustment",
                                 "interest_miscalculation"],
}


def score_detection(findings):
    """
    Gate 2 harness: did we catch the defects we planted, and leave clean notices
    alone?
    """
    caught, missed, false_pos, clean_ok = [], [], [], []
    for f in findings:
        seeded = (f.get("seeded") or "").strip()
        types = {b["type"] for b in f.get("breaks") or []}
        is_clean = seeded.lower() in ("clean", "correct", "")
        if is_clean:
            if types:
                false_pos.append({"file": f["file"], "seeded": seeded,
                                  "breaks": sorted(types)})
            else:
                clean_ok.append(f["file"])
            continue
        expected = None
        for phrase, tlist in _SEEDED_TYPES.items():
            if phrase in seeded.lower() and tlist:
                expected = tlist
                break
        hit = bool(types) if expected is None else any(t in types for t in expected)
        if hit:
            caught.append({"file": f["file"], "seeded": seeded,
                           "breaks": sorted(types)})
        else:
            missed.append({"file": f["file"], "seeded": seeded,
                           "expected": expected or ["any_break"],
                           "breaks": sorted(types)})
    n_seeded = len(caught) + len(missed)
    return {
        "caught": caught,
        "missed": missed,
        "false_positives": false_pos,
        "clean_ok": clean_ok,
        "n_caught": len(caught),
        "n_seeded_defects": n_seeded,
        "n_clean_ok": len(clean_ok),
        "n_false_positives": len(false_pos),
        "score": f"{len(caught)}/{n_seeded}" if n_seeded else "0/0",
        "ok": not missed and not false_pos and n_seeded > 0,
    }


def run(corpus=CORPUS, leverage=5.20, drawn=None, lcs=6_500_000,
        use_llm=True, provider=None, agreement=None):
    """Extract the facility, then check every notice against it."""
    import json
    truth = json.load(open(os.path.join(HERE, "credit_ground_truth.json")))
    docs = truth["documents"]
    drawn = drawn or truth["facility"]["drawn"]
    if leverage is None:
        leverage = truth["facility"].get("current_leverage", 5.20)
    if lcs is None:
        lcs = truth["facility"].get("outstanding_lcs", 6_500_000)

    available = [f for f in docs if f.startswith("CreditAgreement")]
    ca = agreement if agreement in available else available[0]
    ca_text = read_pdf(os.path.join(corpus, ca))

    # Deterministic parse always runs -- it is the floor.
    facility, cites = extract_facility(ca_text)
    mode, note, used_provider = "deterministic", None, None
    attempted = None if provider == "deterministic" else (provider or None)
    llm_F, llm_cites = None, None

    if use_llm and provider != "deterministic":
        attempted = provider or "auto"
        llm_F, llm_cites, used_provider, err = extract_facility_llm(
            ca_text, provider=provider)
        if llm_F:
            # The model fills terms the regex missed; where both found a term we
            # keep the deterministic value, because a parser that matched a known
            # pattern is more trustworthy than a generation.
            added = [k for k in llm_F if k not in facility]
            for k in added:
                facility[k] = llm_F[k]
                if k in llm_cites:
                    cites[k] = llm_cites[k]
            agreed = [k for k in llm_F if k in facility and k not in added
                      and llm_F[k] == facility[k]]
            mode = "llm+deterministic"
            note = (f"{used_provider}: model extracted {len(llm_F)} terms, "
                    f"agreed with the parser on {len(agreed)}, contributed "
                    f"{len(added)} the parser missed")
        else:
            who = provider or "llm"
            note = (f"{who} failed ({err}); fell back to deterministic parser")

    # Cross-check the LLM read against the deterministic parser only.
    # A second live-model call used to run here and made every Anthropic click
    # also wait on NVIDIA (~80s of avoidable latency).
    consensus = None
    if (use_llm and provider != "deterministic"
            and mode == "llm+deterministic" and llm_F is not None):
        try:
            det_only, det_only_cites = extract_facility(ca_text)
            runs = [
                (used_provider, llm_F, llm_cites),
                ("deterministic", det_only, det_only_cites),
            ]
            keys = set()
            for _, F, _ in runs:
                keys |= set(F or {})
            disputed = {}
            agreed_n = unconfirmed = 0
            for k in keys:
                vals = [(name, F[k]) for name, F, _ in runs if F and k in F]
                if len(vals) < 2:
                    unconfirmed += 1
                elif all(_same(v, vals[0][1]) for _, v in vals):
                    agreed_n += 1
                else:
                    disputed[k] = {name: v for name, v in vals}
            consensus = {
                "passes": [name for name, _, _ in runs],
                "agreed": agreed_n,
                "unconfirmed": unconfirmed,
                "disputed": {
                    k: {kk: str(vv) for kk, vv in v.items()}
                    for k, v in disputed.items()},
            }
            # Keep the deterministic value for any disputed term so checks still
            # run. Quarantine is a UI finding, not a hole in the facility spec.
            for k in disputed:
                if k in det_only:
                    facility[k] = det_only[k]
                    if k in det_only_cites:
                        cites[k] = det_only_cites[k]
                else:
                    facility.pop(k, None)
        except Exception as e:
            consensus = {"error": f"{type(e).__name__}: {str(e)[:100]}"}


    findings = []
    for fn, d in sorted(docs.items()):
        if d.get("doc_type") == "borrowing_notice":
            bs = check_borrowing_notice(facility, d, drawn, lcs)
            findings.append({"file": fn, "doc_type": "borrowing_notice",
                             "breaks": bs, "seeded": d.get("seeded_issue")})
        elif d.get("doc_type") == "agent_notice":
            bs = check_agent_notice(facility, d, leverage)
            findings.append({"file": fn, "doc_type": "agent_notice",
                             "breaks": bs, "seeded": d.get("seeded_issue")})

    allb = [b for f in findings for b in f["breaks"]]

    # Keep these separate. Mispriced interest is money that actually moves
    # wrong every period. An availability breach is a limit exceeded, not a
    # dollar lost. Summing them into one headline number would be dishonest.
    interest_impact = sum(abs(b["impact"]) for b in allb
                          if b["type"] == "interest_miscalculation" and b.get("impact"))
    availability_breach = sum(abs(b["impact"]) for b in allb
                              if b["type"] == "exceeds_availability" and b.get("impact"))

    total = None
    if facility.get("tranches"):
        total = sum(facility["tranches"].values())

    gt_score = score_extraction(facility, truth["facility"])
    detection = score_detection(findings)

    return {
        "facility": facility, "citations": cites, "findings": findings,
        "agreement": ca,
        "extraction": {
            "mode": mode, "note": note, "provider": used_provider,
            "attempted": attempted if mode != "llm+deterministic" else used_provider,
            "consensus": consensus,
            "gt": gt_score,
        },
        "summary": {
            "documents": len(docs),
            "notices_checked": len(findings),
            "clean": sum(1 for f in findings if not f["breaks"]),
            "with_breaks": sum(1 for f in findings if f["breaks"]),
            "total_breaks": len(allb),
            "critical": sum(1 for b in allb if b["severity"] == "critical"),
            "high": sum(1 for b in allb if b["severity"] == "high"),
            "leverage": leverage,
            "mispriced_notices": sum(
                1 for b in allb if b["type"] == "interest_miscalculation"),
            "interest_impact": round(interest_impact, 2),
            "availability_breach": round(availability_breach, 2),
            "total_commitments": total,
            "detection": detection,
            "extraction_score": gt_score["score"],
            "extraction_ok": gt_score["ok"],
            "detection_score": detection["score"],
            "detection_ok": detection["ok"],
        },
    }


if __name__ == "__main__":
    r = run()
    F, s = r["facility"], r["summary"]
    print("\nFACILITY SPEC EXTRACTED FROM THE AGREEMENT")
    print(f"  borrower           {F.get('borrower')}")
    print(f"  agent              {F.get('administrative_agent')}")
    print(f"  tranches           {F.get('tranches')}")
    print(f"  permitted periods  {F.get('permitted_interest_periods')} months")
    print(f"  day count (SOFR)   Actual/{F.get('day_count_sofr')}")
    print(f"  CSA                {F.get('credit_spread_adjustment')}")
    print(f"  min / multiple     ${F.get('minimum_borrowing'):,.0f} / "
          f"${F.get('borrowing_multiple'):,.0f}")
    print(f"  SOFR notice        {F.get('notice_days_sofr')} business days")
    print(f"  pricing grid       {len(F.get('pricing_grid') or [])} tiers")
    m, tier = applicable_margin(F, s["leverage"])
    print(f"  margin @ {s['leverage']}x      {m}%  ({tier})")

    print(f"\nNOTICE REVIEW  —  {s['total_breaks']} breaks across "
          f"{s['notices_checked']} notices")
    print(f"  {s['mispriced_notices']} of 4 agent notices mispriced, "
          f"${s['interest_impact']:,.2f} of interest wrong in one period")
    print(f"  ${s['availability_breach']:,.0f} availability breach\n")
    for f in r["findings"]:
        if not f["breaks"]:
            print(f"  [clean]    {f['file']}")
            continue
        for b in f["breaks"]:
            print(f"  [{b['severity'].upper():8s}] {f['file']}  §{b['section']}  "
                  f"{b['type']}")
            print(f"    {b['detail']}")
            print()
