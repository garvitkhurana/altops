"""
Fund entity resolution.

The single most underrated problem in alt-asset operations. The same fund
arrives as "Brookmont Capital Partners IV, L.P.", "Brookmont IV",
"BROOKMONT CAPITAL PARTNERS IV LP" and "Brookmont Cap Ptrs IV" across four
documents from the same GP. If you don't resolve them to one entity, your
position ledger silently double-counts and your unfunded commitment is wrong.

Two jobs here:
  1. Reject strings that are not funds at all -- the management company and
     the LP's own name are the two things that constantly leak into this field.
  2. Collapse name variants onto a single canonical fund.
"""

import re
from difflib import SequenceMatcher

LEGAL_SUFFIXES = [
    "l\\.?p\\.?", "llp", "llc", "l\\.?l\\.?c\\.?", "scsp", "sca", "sicav",
    "s\\.à r\\.l\\.", "sarl", "gmbh", "ltd", "limited", "inc", "plc",
    "cayman", "offshore", "onshore", "feeder", "master",
]

# Strings that indicate this is the manager, not the fund.
MANAGER_MARKERS = [
    "management", "advisors", "advisers", "capital management", "asset management",
    "investment group", "partners llp", "ventures", "administrators",
]

FUND_MARKERS = [
    "fund", "partners", "partnership", "l.p.", "lp", "scsp", "trust",
    "vehicle", "opportunity", "opportunities",
]


# Legacy portfolio systems have column width limits, so operations teams
# abbreviate. The same fund is "Ardent Growth Fund III LP" in the documents and
# "Ardent Gr Fd III" in the system you are migrating off. Expanding these before
# comparison is what turns an unmatched row into a caught duplicate.
ABBREV = {
    "gr": "growth", "gro": "growth", "fd": "fund", "fds": "funds",
    "ptr": "partners", "ptrs": "partners", "prtnrs": "partners",
    "cap": "capital", "captl": "capital", "mgmt": "management",
    "opp": "opportunity", "opps": "opportunities", "oppty": "opportunity",
    "intl": "international", "infra": "infrastructure", "infrstr": "infrastructure",
    "re": "real estate", "cre": "commercial real estate",
    "pc": "private credit", "pe": "private equity", "vc": "venture capital",
    "cr": "credit", "crdt": "credit", "sec": "secondaries", "co": "company",
    "inv": "investment", "invts": "investments", "hldgs": "holdings",
    "tech": "technology", "ent": "enterprise", "glbl": "global", "eur": "europe",
}


def _norm(name):
    """Canonical comparison key for a fund name."""
    if not name:
        return ""
    s = name.lower().strip()
    s = re.sub(r"^(re|fund|account name|the)\s*[:\-]\s*", "", s)
    s = re.sub(r"^limited partner\s*[:\-]\s*", "", s)
    s = re.sub(r"[,\.]", " ", s)
    # "L.P." becomes "l p" once punctuation is stripped; recombine runs of single
    # letters so the suffix list can actually match them.
    s = re.sub(r"\b([a-z])\s+([a-z])\b(?!\s+[a-z]\b)", r"\1\2", s)
    for suf in LEGAL_SUFFIXES:
        s = re.sub(r"\b" + suf + r"\b", " ", s)
    # Expand legacy abbreviations before stripping filler words.
    s = " ".join(ABBREV.get(tok, tok) for tok in s.split())
    s = re.sub(r"\b(fund|funds|the|a)\b", " ", s)
    # Roman numerals and digits carry real meaning -- Fund II is not Fund III.
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_plausible_fund(name, lp_name=None, manager_names=()):
    """Reject the LP and the management company before they pollute the ledger."""
    if not name or len(name) < 5:
        return False, "empty or too short"
    low = name.lower()

    if lp_name and _norm(lp_name) and _norm(lp_name) in _norm(name):
        return False, "this is the LP's own name, not a fund"

    for m in manager_names:
        if m and _norm(m) and _norm(m) == _norm(name):
            return False, "this is the management company, not a fund"

    if any(k in low for k in MANAGER_MARKERS) and not any(
            k in low for k in ("fund", "partners iv", "partners ii", "partners iii")):
        if not re.search(r"fund|\bl\.?p\.?\b|scsp", low):
            return False, "looks like a management entity"

    if not any(k in low for k in FUND_MARKERS):
        return False, "no fund-like token present"

    if re.match(r"^(limited partner|investor|to)\b", low):
        return False, "label text captured instead of a name"

    return True, ""


def resolve(names, lp_name=None, manager_names=(), threshold=0.86):
    """
    Map every raw fund-name string onto a canonical entity.

    Returns (mapping, rejected) where mapping is {raw -> canonical} and
    rejected is {raw -> reason}.
    """
    rejected = {}
    good = []
    for n in names:
        ok, why = is_plausible_fund(n, lp_name, manager_names)
        (good.append(n) if ok else rejected.setdefault(n, why))

    # Longest name wins as canonical -- it is usually the full legal name.
    good = sorted(set(good), key=lambda s: -len(s))
    canon = []
    mapping = {}
    for n in good:
        key = _norm(n)
        hit = None
        for c in canon:
            ck = _norm(c)
            if key == ck:
                hit = c
                break
            # Guard against merging Fund II into Fund III.
            if _digits(key) == _digits(ck) and \
                    SequenceMatcher(None, key, ck).ratio() >= threshold:
                hit = c
                break
        if hit:
            mapping[n] = hit
        else:
            canon.append(n)
            mapping[n] = n
    return mapping, rejected


def _digits(s):
    """Extract the ordinal identity of a fund (III, 3, IV...) for safe matching."""
    roman = re.findall(r"\b(i{1,3}|iv|v|vi{1,3}|ix|x)\b", s)
    nums = re.findall(r"\b(\d+)\b", s)
    return (tuple(roman), tuple(nums))
