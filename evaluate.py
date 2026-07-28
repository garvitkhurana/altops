"""
Extraction scoring.

Three different things get conflated when someone asks "how do you know it's
right?", and only one of them is actually correctness:

  1. GROUND TRUTH   -- does the extracted term match reality? Requires a label.
                       This file. Real correctness.
  2. CONSENSUS      -- do two independent readers agree? Catches divergent error,
                       blind to shared error. A proxy.
  3. SELF-CONSISTENCY -- does the document's own arithmetic tie? Catches internal
                       contradiction, blind to a document that is wrong but
                       coherent. A proxy.

We run all three. Only this one is evidence.

The metric that matters is NOT accuracy. It is SILENT ERROR COUNT: terms we got
wrong AND posted anyway. A wrong term that got quarantined is the system working.
A wrong term that reached a downstream calculation is the failure that loses a
customer, because everything computed from it looks exactly as authoritative as
a correct answer.

Target is zero silent errors. Accuracy can be 80% if the other 20% is flagged.

    python3 evaluate.py                 # deterministic path
    python3 evaluate.py --llm           # whichever provider .env resolves to

--------------------------------------------------------------------------
WHERE GROUND TRUTH COMES FROM ONCE THERE IS A REAL CUSTOMER

This file has a truth label because we generated the corpus. A customer's
credit agreement has no label, so the question becomes real. Four sources, in
descending order of strength:

1. A GOLD SET, LABELLED ONCE. During onboarding the design partner's own team
   confirms the terms for N agreements -- work they are already doing, since
   somebody keys those terms into the loan system regardless. That becomes a
   permanent regression set. This is the only true label and it is nearly free
   to obtain, because it is a by-product of the onboarding we are being paid
   for.

2. CONFIRMED RECOVERIES. Under the contingency model we only get paid on
   findings the customer confirms with their agent. So every confirmed
   recovery is a positive label and every rejected flag is a negative one.
   Precision is measured directly by the fraction of flags that survive
   contact with the agent -- the business model and the evaluation loop are
   the same mechanism, which is the main reason to price this way.

3. BACK-TESTING. Run against historical notices where a dispute already
   happened and the outcome is documented. Small sample, but the labels are
   authoritative and cost nothing to obtain.

4. PROXIES -- consensus and self-consistency. Available on every document with
   no label at all. They catch divergent error and internal contradiction.
   They cannot catch an error both readers share, and they never prove
   correctness. Treat as smoke detectors, not audits.
--------------------------------------------------------------------------
"""

import json
import os
import sys

import facility

HERE = os.path.dirname(os.path.abspath(__file__))

# Terms whose value drives a downstream calculation. Getting one of these wrong
# and posting it silently misprices every notice for the life of the facility.
LOAD_BEARING = {
    "pricing_grid", "credit_spread_adjustment", "day_count_sofr",
    "permitted_interest_periods", "minimum_borrowing", "borrowing_multiple",
    "notice_days_sofr", "tranches",
}

# In the truth file but deliberately not extracted -- they are facility STATE
# (how much is drawn today, current leverage), not terms of the agreement. They
# come from the loan system, not the contract.
NOT_IN_AGREEMENT = {
    "drawn", "outstanding_lcs", "current_leverage", "closing_date",
    "maturity_date", "benchmark", "base_rate_margin_reduction",
    "notice_days_base", "commitment_fee_bps",
}


def compare(truth, got):
    """Term-by-term comparison against the known-correct facility."""
    rows = []
    for key, want in truth.items():
        if key in NOT_IN_AGREEMENT:
            continue
        have = got.get(key)
        if have is None:
            status = "missed"
        elif facility._same(_norm(want), _norm(have)):
            status = "correct"
        else:
            status = "WRONG"
        rows.append({
            "term": key, "status": status,
            "expected": want, "extracted": have,
            "load_bearing": key in LOAD_BEARING,
        })
    for key in got:
        if key not in truth and key not in NOT_IN_AGREEMENT:
            rows.append({"term": key, "status": "extra", "expected": None,
                         "extracted": got[key], "load_bearing": False})
    return rows


def _norm(v):
    """Ground truth stores CSA keys as ints; JSON round-trips them to strings."""
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def main(use_llm=False):
    truth_file = json.load(open(os.path.join(HERE, "credit_ground_truth.json")))
    truth = truth_file["facility"]

    r = facility.run(use_llm=use_llm)
    got = r["facility"]
    consensus = (r.get("extraction") or {}).get("consensus") or {}
    quarantined = set((consensus.get("disputed") or {}).keys())

    rows = compare(truth, got)

    correct = [x for x in rows if x["status"] == "correct"]
    wrong = [x for x in rows if x["status"] == "WRONG"]
    missed = [x for x in rows if x["status"] == "missed"]

    # The number that actually matters.
    silent = [x for x in wrong if x["term"] not in quarantined]
    caught = [x for x in wrong if x["term"] in quarantined]
    silent_load_bearing = [x for x in silent if x["load_bearing"]]

    mode = (r.get("extraction") or {}).get("mode", "deterministic")
    print(f"\nEXTRACTION SCORED AGAINST GROUND TRUTH   [{mode}]")
    print(f"  terms in agreement   {len(rows)}")
    print(f"  correct              {len(correct)}")
    print(f"  wrong                {len(wrong)}   "
          f"({len(caught)} quarantined by cross-check, {len(silent)} silent)")
    print(f"  not extracted        {len(missed)}")
    if rows:
        print(f"  accuracy             {len(correct)/len(rows)*100:.0f}%")

    print(f"\n  SILENT ERRORS        {len(silent)}"
          f"   <-- the only number that matters")
    print(f"  of those load-bearing {len(silent_load_bearing)}")

    if silent:
        print("\n  Terms wrong and posted anyway:")
        for x in silent:
            flag = " [LOAD-BEARING]" if x["load_bearing"] else ""
            print(f"    {x['term']}{flag}")
            print(f"      expected : {x['expected']}")
            print(f"      extracted: {x['extracted']}")

    if missed:
        print(f"\n  Not extracted (safe -- no downstream check runs on a term "
              f"we don't have):")
        for x in missed:
            print(f"    {x['term']}")

    print()
    if not silent_load_bearing:
        print("  PASS - no load-bearing term was wrong and posted.")
    else:
        print("  FAIL - a load-bearing term was wrong and used downstream.")

    if mode == "deterministic":
        print("""
  ---------------------------------------------------------------------------
  READ THIS BEFORE QUOTING THE NUMBER ABOVE.

  The deterministic parser was written against these exact documents. Scoring
  it here is circular -- it is a regression test that catches breakage, not
  evidence the approach generalises. Do not present it as accuracy.

  The honest test is `python3 evaluate.py --llm`: the model has never seen the
  generator, so its extraction is a genuine read of an unfamiliar contract.

  And the real test is a design partner's actual agreement, where there is no
  truth file at all -- see the note in the module docstring on how ground truth
  works in production.
  ---------------------------------------------------------------------------""")
    print()
    return 0 if not silent_load_bearing else 1


if __name__ == "__main__":
    sys.exit(main(use_llm="--llm" in sys.argv))
