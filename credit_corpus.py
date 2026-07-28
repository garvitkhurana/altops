"""
Private credit corpus: one credit agreement, then the notice traffic it governs.

The point of this vertical is that the credit agreement is not a record, it is a
SPECIFICATION. It defines the optionality: which interest periods are permitted,
what margin applies at what leverage, the day-count convention, minimum borrowing
amounts, required notice periods, availability.

So every borrowing notice and every agent rate-set has a correct answer that can
be computed from the agreement and checked. Today an operator keys the facility
terms into an Excel template at setup, and then nobody re-derives anything --
they trust the agent's number.

Generates:
  CreditAgreement_*.pdf   the facility terms (excerpt)
  BorrowingNotice_*.pdf   borrower requests a draw
  AgentNotice_*.pdf       agent's rate set and interest calculation
"""

import json
import os
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credit_corpus")
os.makedirs(OUT, exist_ok=True)

BORROWER = "Meridian Packaging Holdings, LLC"
AGENT = "Sterling Agency Services, LLC"
LENDER = "Ridgeline Private Credit Fund II, L.P."

# ---------------------------------------------------------------- the facility
FACILITY = {
    "borrower": BORROWER,
    "administrative_agent": AGENT,
    "closing_date": "2024-06-28",
    "maturity_date": "2030-06-28",
    "tranches": {
        "Revolving Credit Facility": 75_000_000,
        "Term Loan A": 150_000_000,
        "Delayed Draw Term Loan": 50_000_000,
    },
    "benchmark": "Term SOFR",
    # Applicable Margin for SOFR Loans, by Total Net Leverage Ratio.
    "pricing_grid": [
        {"min_leverage": 5.00, "max_leverage": None, "margin": 5.75},
        {"min_leverage": 4.00, "max_leverage": 5.00, "margin": 5.25},
        {"min_leverage": 3.00, "max_leverage": 4.00, "margin": 4.75},
        {"min_leverage": None, "max_leverage": 3.00, "margin": 4.25},
    ],
    "base_rate_margin_reduction": 1.00,
    "credit_spread_adjustment": {1: 0.10, 3: 0.15, 6: 0.25},
    "permitted_interest_periods": [1, 3, 6],
    "day_count_sofr": 360,
    "day_count_base": 365,
    "minimum_borrowing": 1_000_000,
    "borrowing_multiple": 500_000,
    "notice_days_sofr": 3,
    "notice_days_base": 0,
    "commitment_fee_bps": 50,
    "lc_sublimit": 15_000_000,
    "current_leverage": 5.20,      # per the most recent compliance certificate
    "drawn": {"Revolving Credit Facility": 22_000_000,
              "Term Loan A": 150_000_000,
              "Delayed Draw Term Loan": 20_000_000},
    "outstanding_lcs": 6_500_000,
}

styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Heading1"], fontSize=12, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10, spaceAfter=3)
B = ParagraphStyle("B", parent=styles["Normal"], fontSize=8.5, leading=12)
SM = ParagraphStyle("SM", parent=styles["Normal"], fontSize=7.5, leading=9.5,
                    textColor=colors.grey)


def _tbl(rows, widths, header=True):
    t = Table(rows, colWidths=widths)
    cmds = [("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#cccccc"))]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                 ("ALIGN", (0, 0), (-1, 0), "LEFT")]
    t.setStyle(TableStyle(cmds))
    return t


def _doc(fn):
    return SimpleDocTemplate(os.path.join(OUT, fn), pagesize=LETTER,
                             topMargin=0.65 * inch, bottomMargin=0.65 * inch,
                             leftMargin=0.85 * inch, rightMargin=0.85 * inch)


def build_credit_agreement():
    fn = "CreditAgreement_Meridian_Packaging.pdf"
    f = FACILITY
    S = [
        Paragraph("CREDIT AGREEMENT", H),
        Paragraph(f"dated as of June 28, 2024, among <b>{BORROWER}</b>, as "
                  f"Borrower, the Lenders party hereto, and <b>{AGENT}</b>, as "
                  f"Administrative Agent.", B),
        Spacer(1, 9),
        Paragraph("ARTICLE II — THE CREDITS", H2),
        Paragraph("Section 2.01. <b>Commitments.</b> Subject to the terms hereof, "
                  "the Lenders severally agree to make Loans in the following "
                  "aggregate principal amounts:", B),
        Spacer(1, 4),
        _tbl([["Facility", "Commitment"]] +
             [[k, f"${v:,.2f}"] for k, v in f["tranches"].items()] +
             [["Total Facilities", f"${sum(f['tranches'].values()):,.2f}"]],
             [3.5 * inch, 2.2 * inch]),
        Spacer(1, 8),
        Paragraph(
            f"Section 2.02. <b>Borrowings.</b> Each Borrowing of SOFR Loans shall "
            f"be in an aggregate principal amount of not less than "
            f"<b>${f['minimum_borrowing']:,.0f}</b> and in integral multiples of "
            f"<b>${f['borrowing_multiple']:,.0f}</b> in excess thereof. The Borrower "
            f"shall deliver a Borrowing Request to the Administrative Agent not "
            f"later than 1:00 p.m. <b>{f['notice_days_sofr']} U.S. Government "
            f"Securities Business Days</b> prior to the date of any SOFR Borrowing, "
            f"and on the date of any Base Rate Borrowing.", B),
        Spacer(1, 8),
        Paragraph(
            f"Section 2.03. <b>Interest Elections.</b> Each SOFR Borrowing shall "
            f"have an Interest Period of <b>one, three or six months</b> as elected "
            f"by the Borrower. No Interest Period may extend beyond the Maturity "
            f"Date of "
            f"{date.fromisoformat(f['maturity_date']).strftime('%B %d, %Y')}.", B),
        Spacer(1, 9),
        Paragraph("ARTICLE III — INTEREST AND FEES", H2),
        Paragraph(
            f"Section 3.01. <b>Interest.</b> SOFR Loans shall bear interest at "
            f"<b>Term SOFR</b> plus the applicable <b>Credit Spread Adjustment</b> "
            f"plus the <b>Applicable Margin</b>. Interest on SOFR Loans shall be "
            f"computed on the basis of a year of <b>{f['day_count_sofr']} days</b> "
            f"and actual days elapsed. Interest on Base Rate Loans shall be computed "
            f"on the basis of a year of <b>{f['day_count_base']} days</b>.", B),
        Spacer(1, 5),
        Paragraph("Credit Spread Adjustment, by Interest Period:", B),
        Spacer(1, 3),
        _tbl([["Interest Period", "Credit Spread Adjustment"],
              ["One month", "0.10%"], ["Three months", "0.15%"],
              ["Six months", "0.25%"]], [3.5 * inch, 2.2 * inch]),
        Spacer(1, 8),
        Paragraph(
            "Section 3.02. <b>Applicable Margin.</b> The Applicable Margin for SOFR "
            "Loans shall be determined by reference to the Total Net Leverage Ratio "
            "set forth in the most recently delivered Compliance Certificate:", B),
        Spacer(1, 4),
        _tbl([["Total Net Leverage Ratio", "Applicable Margin (SOFR Loans)"],
              ["Greater than 5.00 : 1.00", "5.75%"],
              ["Greater than 4.00 : 1.00 but ≤ 5.00 : 1.00", "5.25%"],
              ["Greater than 3.00 : 1.00 but ≤ 4.00 : 1.00", "4.75%"],
              ["Less than or equal to 3.00 : 1.00", "4.25%"]],
             [3.5 * inch, 2.2 * inch]),
        Spacer(1, 5),
        Paragraph(
            f"The Applicable Margin for Base Rate Loans shall in each case be "
            f"<b>{f['base_rate_margin_reduction']:.2f}%</b> less than the margin "
            f"for SOFR Loans.", B),
        Spacer(1, 8),
        Paragraph(
            f"Section 3.03. <b>Commitment Fee.</b> The Borrower shall pay a "
            f"commitment fee of <b>{f['commitment_fee_bps']/100:.2f}%</b> per annum "
            f"on the daily unused portion of the Revolving Credit Facility. "
            f"Letters of Credit shall not exceed a sublimit of "
            f"<b>${f['lc_sublimit']:,.0f}</b> and shall reduce availability.", B),
        Spacer(1, 12),
        Paragraph("This excerpt is illustrative and generated for testing. It is "
                  "not a real credit agreement and is not legal advice.", SM),
    ]
    _doc(fn).build(S)
    return fn


def build_borrowing_notice(idx, req_date, borrow_date, tranche, amount,
                           rate_type, interest_period):
    fn = f"BorrowingNotice_{idx:02d}.pdf"
    S = [
        Paragraph("BORROWING REQUEST", H),
        Paragraph(f"Pursuant to Section 2.02 of the Credit Agreement dated as of "
                  f"June 28, 2024", B),
        Spacer(1, 9),
        _tbl([["", ""],
              ["Borrower", BORROWER],
              ["To", f"{AGENT}, as Administrative Agent"],
              ["Request Date", req_date.strftime("%B %d, %Y")],
              ["Proposed Borrowing Date", borrow_date.strftime("%B %d, %Y")],
              ["Facility", tranche],
              ["Principal Amount", f"${amount:,.2f}"],
              ["Type of Borrowing", rate_type],
              ["Interest Period",
               f"{interest_period} month" + ("s" if interest_period != 1 else "")
               if interest_period else "N/A"]],
             [2.3 * inch, 3.4 * inch], header=False),
        Spacer(1, 10),
        Paragraph("The Borrower certifies that the conditions precedent set forth "
                  "in Section 4.02 are satisfied as of the proposed Borrowing Date.",
                  B),
    ]
    _doc(fn).build(S)
    return fn, {
        "doc_type": "borrowing_notice", "notice_id": idx,
        "request_date": req_date.isoformat(),
        "borrowing_date": borrow_date.isoformat(),
        "tranche": tranche, "amount": amount,
        "rate_type": rate_type, "interest_period": interest_period,
    }


def build_agent_notice(idx, borrow_date, tranche, amount, interest_period,
                       sofr, csa, margin, days, day_count, interest):
    fn = f"AgentNotice_{idx:02d}.pdf"
    end = borrow_date + timedelta(days=days)
    S = [
        Paragraph("INTEREST RATE SET NOTICE", H),
        Paragraph(f"{AGENT}, as Administrative Agent", B),
        Paragraph(f"Re: {BORROWER} — Credit Agreement dated June 28, 2024", B),
        Spacer(1, 9),
        _tbl([["Item", "Value"],
              ["Facility", tranche],
              ["Borrowing Date", borrow_date.strftime("%B %d, %Y")],
              ["Interest Period End", end.strftime("%B %d, %Y")],
              ["Principal Amount", f"${amount:,.2f}"],
              ["Interest Period",
               f"{interest_period} month" + ("s" if interest_period != 1 else "")],
              ["Term SOFR", f"{sofr:.5f}%"],
              ["Credit Spread Adjustment", f"{csa:.2f}%"],
              ["Applicable Margin", f"{margin:.2f}%"],
              ["All-In Rate", f"{sofr + csa + margin:.5f}%"],
              ["Days in Period", str(days)],
              ["Day Count Basis", f"Actual/{day_count}"],
              ["Interest Due", f"${interest:,.2f}"]],
             [2.6 * inch, 3.1 * inch]),
        Spacer(1, 10),
        Paragraph("Funds are due to the Administrative Agent for the account of the "
                  "Lenders on the Interest Period End date set forth above.", B),
    ]
    _doc(fn).build(S)
    return fn, {
        "doc_type": "agent_notice", "notice_id": idx,
        "borrowing_date": borrow_date.isoformat(), "tranche": tranche,
        "amount": amount, "interest_period": interest_period,
        "sofr": sofr, "csa": csa, "margin": margin, "days": days,
        "day_count": day_count, "interest": interest,
    }


def main():
    truth = {"facility": FACILITY, "documents": {}}
    ca = build_credit_agreement()
    truth["documents"][ca] = {"doc_type": "credit_agreement"}

    SOFR = 4.32150  # Term SOFR for the period

    # --- borrowing notices, each carrying one realistic defect --------------
    specs = [
        # (req, borrow, tranche, amount, type, period, note)
        (date(2026, 6, 1), date(2026, 6, 4), "Revolving Credit Facility",
         5_000_000, "SOFR Loan", 3, "clean"),
        (date(2026, 6, 15), date(2026, 6, 18), "Revolving Credit Facility",
         3_000_000, "SOFR Loan", 2, "interest period not permitted"),
        (date(2026, 6, 22), date(2026, 6, 25), "Revolving Credit Facility",
         1_250_000, "SOFR Loan", 1, "not an integral multiple of 500,000"),
        (date(2026, 7, 6), date(2026, 7, 7), "Revolving Credit Facility",
         4_000_000, "SOFR Loan", 3, "only 1 day notice, agreement requires 3"),
        (date(2026, 7, 13), date(2026, 7, 16), "Revolving Credit Facility",
         48_000_000, "SOFR Loan", 3, "exceeds availability"),
        (date(2026, 7, 20), date(2026, 7, 23), "Delayed Draw Term Loan",
         10_000_000, "SOFR Loan", 6, "clean"),
    ]
    for i, (rq, bd, tr, amt, rt, ip, note) in enumerate(specs, 1):
        fn, rec = build_borrowing_notice(i, rq, bd, tr, amt, rt, ip)
        rec["seeded_issue"] = note
        truth["documents"][fn] = rec

    # --- agent notices; some miscalculate ----------------------------------
    # Correct margin at 5.20x leverage is 5.75%.
    agents = [
        # (idx, borrow_date, tranche, amount, ip, sofr, csa, margin, days, dc, note)
        (1, date(2026, 6, 4), "Revolving Credit Facility", 5_000_000, 3,
         SOFR, 0.15, 5.75, 91, 360, "correct"),
        (2, date(2026, 6, 18), "Revolving Credit Facility", 3_000_000, 3,
         SOFR, 0.15, 5.25, 91, 360, "wrong margin: used 4.00-5.00x tier at 5.20x"),
        (3, date(2026, 6, 25), "Revolving Credit Facility", 1_250_000, 1,
         SOFR, 0.10, 5.75, 30, 365, "wrong day count: 365 on a SOFR loan"),
        (4, date(2026, 7, 7), "Revolving Credit Facility", 4_000_000, 3,
         SOFR, 0.00, 5.75, 91, 360, "credit spread adjustment omitted"),
    ]
    for (i, bd, tr, amt, ip, sofr, csa, margin, days, dc, note) in agents:
        interest = amt * ((sofr + csa + margin) / 100) * days / dc
        fn, rec = build_agent_notice(i, bd, tr, amt, ip, sofr, csa, margin,
                                     days, dc, round(interest, 2))
        rec["seeded_issue"] = note
        truth["documents"][fn] = rec

    with open(os.path.join(OUT, "..", "credit_ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=2, default=str)

    n = len(truth["documents"])
    print(f"Generated {n} private credit documents -> {OUT}")
    print(f"  1 credit agreement, {len(specs)} borrowing notices, "
          f"{len(agents)} agent notices")


if __name__ == "__main__":
    main()
