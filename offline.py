"""
OFFLINE FALLBACK PARSER -- deterministic regex, no LLM.

Read this honestly: this exists so the demo runs with no API key, and so the
pipeline has a cheap first pass. It is NOT the product. It only works on label
phrasings it has been shown, which is exactly the reason rules-based extraction
loses in this market -- every new GP is a new rule. Set ANTHROPIC_API_KEY to
run the real path.

Anything this parser is unsure about it marks low-confidence, which routes it
to the exception queue rather than silently guessing.
"""

import re
from datetime import datetime

MONTHS = ("january february march april may june july august september "
          "october november december").split()


def _f(s):
    if s is None:
        return None
    neg = "(" in s and ")" in s
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _date(s, european=False):
    """Normalize a date string, resolving DD/MM vs MM/DD where possible."""
    if not s:
        return None, 0.6
    s = s.strip().rstrip(".,")
    for fmt in ("%B %d, %Y", "%d %B %Y", "%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat(), 0.97
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # If the first component can't be a month, it's DD/MM. Unambiguous.
        if a > 12:
            return f"{y:04d}-{b:02d}-{a:02d}", 0.97
        if b > 12:
            return f"{y:04d}-{a:02d}-{b:02d}", 0.97
        # Genuinely ambiguous. Use the manager's domicile as the tiebreak,
        # and drop confidence so a human confirms it.
        if european:
            return f"{y:04d}-{b:02d}-{a:02d}", 0.62
        return f"{y:04d}-{a:02d}-{b:02d}", 0.66
    return None, 0.0


def _grab(text, patterns, european=False, is_date=False, conf=0.93):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            raw = m.group(1).strip()
            if is_date:
                v, c = _date(raw, european)
                return {"value": v, "confidence": c, "quote": m.group(0)[:130]}
            return {"value": _f(raw), "confidence": conf,
                    "quote": m.group(0)[:130]}
    return {"value": None, "confidence": 0.0, "quote": ""}


AMT = r"(?:USD|EUR|GBP|\$|€|£)?\s*\(?([\d,]+\.\d{2})\)?"
DATE = (r"([A-Z][a-z]+ \d{1,2}, \d{4}|\d{1,2} [A-Z][a-z]+ \d{4}"
        r"|\d{1,2}-[A-Z][a-z]{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})")


def classify(text):
    low = text.lower()
    if "capital account" in low and "beginning capital" in low:
        return {"doc_type": "capital_account_statement", "confidence": 0.94,
                "reason": "capital account roll-forward present [offline]"}
    if re.search(r"distribution (notice|advice)|notice of distribution", low):
        return {"doc_type": "distribution", "confidence": 0.93,
                "reason": "distribution notice heading [offline]"}
    if re.search(r"capital call|drawdown (notice|request)|funding notice"
                 r"|notice of capital contribution", low):
        return {"doc_type": "capital_call", "confidence": 0.93,
                "reason": "capital call heading [offline]"}
    return {"doc_type": "other", "confidence": 0.35, "reason": "no match [offline]"}


def extract(text, doc_type):
    eu = bool(re.search(r"S\.à r\.l\.|SCSp|EUR", text))
    cur = "EUR" if re.search(r"\bEUR\b|€", text) else "USD"

    fund = _grab_str(text, [
        r"Re:\s*(.+?)(?:\n|$)",
        r"Fund\s*[:|]\s*\*?\*?\s*(.+?)(?:\s*\||\n)",
        r"^\s*(\S.*?(?:Fund|Partners)\s*(?:I{1,3}V?|IV|V?I{0,3}|\d+)?[^\n]*?"
        r"(?:L\.?P\.?|LP|SCSp|LLP))\s*$",
        r"Account Name:\s*(.+?)(?:\n|$)",
        # Capital account statements: manager on line 1, fund on line 2.
        r"\A[^\n]+\n([^\n]*(?:Fund|Partners)[^\n]*)\n",
    ])
    mgr = _grab_str(text, [r"^\s*(.+?(?:LLC|LLP|Management|Advisors|Ventures|"
                           r"Group|S\.à r\.l\.))\s*$"])

    common = {"fund_name": fund, "gp_manager": mgr,
              "currency": {"value": cur, "confidence": 0.95,
                           "quote": cur}}

    if doc_type == "capital_call":
        f = dict(common)
        f["notice_date"] = _grab(text, [
            r"Notice Date[:\s|]*\*?\*?\s*" + DATE,
            r"^\s*" + DATE + r"\s*$",
        ], eu, True)
        f["due_date"] = _grab(text, [
            r"(?:Payment Due Date|Due Date|Due date)\s*[:\s|]*\*?\*?\s*" + DATE,
            r"no later than\s*\*?\*?\s*" + DATE,
            r"required in cleared form no later than\s*\n?\s*" + DATE,
        ], eu, True)
        f["call_number"] = _grab(text, [
            r"(?:Call|Notice|No\.)\s*#?\s*(\d+)",
            r"Call #:\s*\*?\*?\s*(\d+)",
        ], conf=0.88)
        f["amount"] = _grab(text, [
            r"(?:Total drawdown|Total)\s*" + AMT,
            r"drawdown of\s*\*?\*?" + AMT,
            r"calls capital in the amount of\s*" + AMT,
            r"(?:This Capital Call|Amount due)\s*" + AMT,
        ])
        f["commitment"] = _grab(text, [
            r"(?:Total Commitment|Commitment of|Total commitment|Commitment)\s*" + AMT,
        ])
        f["cumulative_called"] = _grab(text, [
            r"(?:cumulative contributions total|Cumulative Contributions|"
            r"contributions to date \(inclusive of this call\)|Called to date)\s*" + AMT,
        ])
        f["unfunded_commitment"] = _grab(text, [
            r"(?:remaining undrawn Commitment is|Remaining Unfunded Commitment|"
            r"unfunded commitment|Unfunded)\s*" + AMT,
        ])
        f["purpose_investments"] = _grab(text, [
            r"(?:Portfolio investments|New / follow-on investments|investments)\s*" + AMT])
        f["purpose_management_fee"] = _grab(text, [
            r"(?:Management fee|management fees)\s*" + AMT])
        f["purpose_expenses"] = _grab(text, [
            r"(?:Partnership expenses|Fund expenses|partnership expenses)\s*" + AMT])
        return {"fields": f}

    if doc_type == "distribution":
        f = dict(common)
        f["notice_date"] = _grab(text, [r"^\s*" + DATE + r"\s*$"], eu, True)
        f["payment_date"] = _grab(text, [
            r"Payment date:\s*\*?\*?" + DATE,
            r"to you on\s*\*?\*?" + DATE,
        ], eu, True)
        f["distribution_number"] = _grab(text, [r"No\.\s*(\d+)"], conf=0.88)
        f["amount"] = _grab(text, [
            r"Total distribution\s*" + AMT,
            r"will distribute\s*\*?\*?" + AMT,
        ])
        f["return_of_capital"] = _grab(text, [
            r"[Rr]eturn of capital\s*" + AMT])
        f["realized_gain"] = _grab(text, [
            r"[Rr]eali[sz]ed gain\s*" + AMT])
        f["investment_income"] = _grab(text, [
            r"[Ii]nvestment income\s*" + AMT])
        f["recallable_amount"] = _grab(text, [
            r"of which recallable\s*" + AMT,
            r"([\d,]+\.\d{2})\s*is\s*\n?\s*subject to recall",
            r"Of the total,\s*(?:USD|EUR|\$)?\s*([\d,]+\.\d{2})",
        ])
        return {"fields": f}

    f = dict(common)
    f["period_end"] = _grab(text, [r"As of:\s*" + DATE], eu, True)
    f["beginning_nav"] = _grab(text, [r"Beginning capital balance\s*" + AMT])
    f["contributions"] = _grab(text, [r"Contributions\s*" + AMT])
    f["distributions"] = _grab(text, [r"Distributions\s*\(" + AMT.replace(r"\(?", "") ])
    d = _grab(text, [r"Distributions\s*\(?(?:USD|EUR|\$|€)?\s*\(?([\d,]+\.\d{2})\)?"])
    if d["value"] is not None and re.search(r"Distributions\s*\(", text):
        d["value"] = -abs(d["value"])
    f["distributions"] = d
    f["realized_gain"] = _grab(text, [r"Realized gain / \(loss\)\s*" + AMT])
    f["unrealized_change"] = _grab(text, [r"Change in unrealized\s*" + AMT])
    mf = _grab(text, [r"Management fee\s*\(?(?:USD|EUR|\$|€)?\s*\(?([\d,]+\.\d{2})\)?"])
    if mf["value"] is not None:
        mf["value"] = -abs(mf["value"])
    f["management_fee"] = mf
    ci = _grab(text, [r"Carried interest accrual\s*\(?(?:USD|EUR|\$|€)?\s*\(?([\d,]+\.\d{2})\)?"])
    if ci["value"] is not None:
        ci["value"] = -abs(ci["value"])
    f["carried_interest"] = ci
    f["ending_nav"] = _grab(text, [r"Ending capital balance\s*" + AMT])
    return {"fields": f}


def _grab_str(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.I | re.M)
        if m:
            v = m.group(1).strip()
            if 3 < len(v) < 90:
                return {"value": v, "confidence": 0.9, "quote": m.group(0)[:130]}
    return {"value": None, "confidence": 0.0, "quote": ""}
