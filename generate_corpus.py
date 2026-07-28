"""
Generate a realistic corpus of alternative-investment LP documents.

The entire premise of the product is that every GP sends a different format.
So this generator deliberately varies: layout, terminology, date format,
currency notation, field ordering, and which fields are present at all.

Output: PDFs in ./corpus/ + ground_truth.json for accuracy scoring.
"""

import json
import os
import random
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

random.seed(20260727)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
os.makedirs(OUT, exist_ok=True)

LP_NAME = "Ridgeline Family Office LP"

# Each GP has its own house style. This is the point.
GPS = [
    {
        "name": "Brookmont Capital Partners IV, L.P.",
        "short": "Brookmont IV",
        "mgr": "Brookmont Capital Management, LLC",
        "style": "table",
        "call_term": "Capital Call Notice",
        "dist_term": "Distribution Notice",
        "date_fmt": "%B %d, %Y",
        "cur": "plain",
        "commitment": 5_000_000,
        "vintage": 2021,
    },
    {
        "name": "Ardent Growth Fund III LP",
        "short": "Ardent III",
        "mgr": "Ardent Partners LLP",
        "style": "letter",
        "call_term": "Drawdown Notice",
        "dist_term": "Distribution Advice",
        "date_fmt": "%d %B %Y",
        "cur": "code",
        "commitment": 3_000_000,
        "vintage": 2022,
    },
    {
        "name": "Kestrel Private Credit Fund II, L.P.",
        "short": "Kestrel PC II",
        "mgr": "Kestrel Asset Management",
        "style": "dense",
        "call_term": "Notice of Capital Contribution",
        "dist_term": "Notice of Distribution",
        "date_fmt": "%m/%d/%Y",
        "cur": "plain",
        "commitment": 7_500_000,
        "vintage": 2023,
    },
    {
        "name": "Halloway Real Assets Partners, LP",
        "short": "Halloway RA",
        "mgr": "Halloway Investment Group",
        "style": "table",
        "call_term": "Funding Notice",
        "dist_term": "Distribution Notice",
        "date_fmt": "%d-%b-%y",
        "cur": "plain",
        "commitment": 2_500_000,
        "vintage": 2020,
    },
    {
        "name": "Sable Ventures Opportunity Fund I",
        "short": "Sable Opp I",
        "mgr": "Sable Ventures",
        "style": "minimal",
        "call_term": "Capital Call",
        "dist_term": "Distribution",
        "date_fmt": "%m/%d/%Y",
        "cur": "plain",
        "commitment": 1_000_000,
        "vintage": 2024,
    },
    {
        "name": "Northgate Infrastructure Partners II SCSp",
        "short": "Northgate II",
        "mgr": "Northgate Infrastructure Advisors S.à r.l.",
        "style": "letter",
        "call_term": "Drawdown Request",
        "dist_term": "Distribution Notice",
        "date_fmt": "%d/%m/%Y",  # European. A classic reconciliation landmine.
        "cur": "eur",
        "commitment": 4_000_000,
        "vintage": 2022,
    },
]

styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Heading1"], fontSize=13, spaceAfter=4)
HC = ParagraphStyle("HC", parent=H, alignment=TA_CENTER)
B = ParagraphStyle("B", parent=styles["Normal"], fontSize=9, leading=13)
BD = ParagraphStyle("BD", parent=styles["Normal"], fontSize=8, leading=10.5)
SM = ParagraphStyle("SM", parent=styles["Normal"], fontSize=7.5,
                    leading=9.5, textColor=colors.grey)


def money(v, gp):
    """Render an amount the way this particular GP renders amounts."""
    if gp["cur"] == "eur":
        return f"EUR {v:,.2f}"
    if gp["cur"] == "code":
        return f"USD {v:,.2f}"
    return f"${v:,.2f}"


def fdate(d, gp):
    return d.strftime(gp["date_fmt"])


def tbl(rows, widths, header=True, align_right_from=1):
    t = Table(rows, colWidths=widths)
    cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#cccccc")),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "LEFT" if align_right_from > 0 else "RIGHT"),
        ]
    t.setStyle(TableStyle(cmds))
    return t


# --------------------------------------------------------------------------
# Document builders
# --------------------------------------------------------------------------

def build_capital_call(gp, seq, call_no, call_amt, due, notice_date,
                       cum_called, purpose):
    """A capital call notice, rendered in this GP's house style."""
    fn = f"{gp['short'].replace(' ', '_')}_CapitalCall_{call_no:02d}.pdf"
    path = os.path.join(OUT, fn)
    doc = SimpleDocTemplate(path, pagesize=LETTER,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch)
    S = []
    unfunded = gp["commitment"] - cum_called

    inv, fee, exp = purpose

    if gp["style"] == "letter":
        S += [
            Paragraph(gp["mgr"], H),
            Paragraph(f"<b>{gp['call_term']} No. {call_no}</b>", B),
            Spacer(1, 10),
            Paragraph(f"{fdate(notice_date, gp)}", B),
            Spacer(1, 8),
            Paragraph(f"To: {LP_NAME}", B),
            Paragraph(f"Re: {gp['name']}", B),
            Spacer(1, 10),
            Paragraph(
                f"Dear Limited Partner,<br/><br/>Pursuant to Section 3.2 of the "
                f"Limited Partnership Agreement, the General Partner hereby gives "
                f"notice of a drawdown of <b>{money(call_amt, gp)}</b> in respect of "
                f"your Commitment of {money(gp['commitment'], gp)}. Funds are "
                f"required in cleared form no later than "
                f"<b>{fdate(due, gp)}</b>.", B),
            Spacer(1, 10),
            Paragraph("The drawdown is applied as follows:", B),
            Spacer(1, 5),
            tbl([
                ["Purpose", "Amount"],
                ["Portfolio investments", money(inv, gp)],
                ["Management fee", money(fee, gp)],
                ["Partnership expenses", money(exp, gp)],
                ["Total drawdown", money(call_amt, gp)],
            ], [3.6 * inch, 2.0 * inch]),
            Spacer(1, 10),
            Paragraph(
                f"Following this drawdown, cumulative contributions total "
                f"{money(cum_called, gp)} ({cum_called / gp['commitment'] * 100:.1f}% "
                f"of Commitment) and your remaining undrawn Commitment is "
                f"{money(unfunded, gp)}.", B),
        ]
    elif gp["style"] == "dense":
        S += [
            Paragraph(f"{gp['mgr']} &mdash; {gp['call_term']}", HC),
            Spacer(1, 6),
            Paragraph(
                f"<b>Fund:</b> {gp['name']} &nbsp;|&nbsp; <b>Investor:</b> {LP_NAME} "
                f"&nbsp;|&nbsp; <b>Notice Date:</b> {fdate(notice_date, gp)} "
                f"&nbsp;|&nbsp; <b>Call #:</b> {call_no} &nbsp;|&nbsp; "
                f"<b>Due Date:</b> {fdate(due, gp)}", BD),
            Spacer(1, 8),
            Paragraph(
                f"The Partnership hereby calls capital in the amount of "
                f"{money(call_amt, gp)} from the above-referenced Limited Partner. "
                f"Total Commitment {money(gp['commitment'], gp)}; contributions to "
                f"date (inclusive of this call) {money(cum_called, gp)}; unfunded "
                f"commitment {money(unfunded, gp)}. Allocation: investments "
                f"{money(inv, gp)}; management fees {money(fee, gp)}; "
                f"partnership expenses {money(exp, gp)}. Payment must be received "
                f"by wire in immediately available funds on or before the due date "
                f"stated above. Late contributions accrue interest at the Default "
                f"Rate set forth in Section 3.5 of the LPA.", BD),
        ]
    elif gp["style"] == "minimal":
        S += [
            Paragraph(f"{gp['short']} &ndash; {gp['call_term']} #{call_no}", H),
            Spacer(1, 8),
            tbl([
                ["Field", "Value"],
                ["Fund", gp["name"]],
                ["Limited Partner", LP_NAME],
                ["Notice date", fdate(notice_date, gp)],
                ["Amount due", money(call_amt, gp)],
                ["Due date", fdate(due, gp)],
                ["Commitment", money(gp["commitment"], gp)],
                ["Called to date", money(cum_called, gp)],
                ["Unfunded", money(unfunded, gp)],
            ], [2.2 * inch, 3.4 * inch]),
        ]
    else:  # table
        S += [
            Paragraph(gp["mgr"], H),
            Paragraph(gp["name"], B),
            Spacer(1, 8),
            Paragraph(f"<b>{gp['call_term']} &ndash; Call No. {call_no}</b>", B),
            Spacer(1, 8),
            tbl([
                ["", ""],
                ["Limited Partner", LP_NAME],
                ["Notice Date", fdate(notice_date, gp)],
                ["Payment Due Date", fdate(due, gp)],
                ["Total Commitment", money(gp["commitment"], gp)],
                ["This Capital Call", money(call_amt, gp)],
                ["Cumulative Contributions", money(cum_called, gp)],
                ["Remaining Unfunded Commitment", money(unfunded, gp)],
            ], [2.8 * inch, 2.8 * inch], header=False),
            Spacer(1, 10),
            Paragraph("<b>Use of Proceeds</b>", B),
            Spacer(1, 4),
            tbl([
                ["Category", "Amount"],
                ["New / follow-on investments", money(inv, gp)],
                ["Management fee", money(fee, gp)],
                ["Fund expenses", money(exp, gp)],
                ["Total", money(call_amt, gp)],
            ], [3.6 * inch, 2.0 * inch]),
        ]

    S += [
        Spacer(1, 12),
        Paragraph("<b>Wire Instructions</b>", B),
        Spacer(1, 4),
        Paragraph(
            f"Bank: First Meridian Trust, N.A.<br/>"
            f"ABA: 021{random.randint(100000, 999999)}<br/>"
            f"Account Name: {gp['name']}<br/>"
            f"Account No.: {random.randint(10**9, 10**10 - 1)}<br/>"
            f"Reference: {LP_NAME} / Call {call_no}", BD),
        Spacer(1, 14),
        Paragraph(
            "This notice is confidential and intended solely for the named "
            "Limited Partner. Capitalized terms have the meanings given in the "
            "Limited Partnership Agreement.", SM),
    ]
    doc.build(S)

    return fn, {
        "doc_type": "capital_call",
        "fund_name": gp["name"],
        "gp_manager": gp["mgr"],
        "notice_date": notice_date.isoformat(),
        "due_date": due.isoformat(),
        "call_number": call_no,
        "amount": round(call_amt, 2),
        "currency": "EUR" if gp["cur"] == "eur" else "USD",
        "commitment": round(gp["commitment"], 2),
        "cumulative_called": round(cum_called, 2),
        "unfunded_commitment": round(unfunded, 2),
        "purpose_investments": round(inv, 2),
        "purpose_management_fee": round(fee, 2),
        "purpose_expenses": round(exp, 2),
    }


def build_distribution(gp, dist_no, amount, pay_date, notice_date, split):
    fn = f"{gp['short'].replace(' ', '_')}_Distribution_{dist_no:02d}.pdf"
    path = os.path.join(OUT, fn)
    doc = SimpleDocTemplate(path, pagesize=LETTER, topMargin=0.7 * inch,
                            bottomMargin=0.7 * inch, leftMargin=0.8 * inch,
                            rightMargin=0.8 * inch)
    roc, gain, income, recallable = split
    S = [
        Paragraph(gp["mgr"], H),
        Paragraph(gp["name"], B),
        Spacer(1, 8),
        Paragraph(f"<b>{gp['dist_term']} No. {dist_no}</b>", B),
        Spacer(1, 8),
    ]
    if gp["style"] in ("letter", "dense"):
        S += [
            Paragraph(f"{fdate(notice_date, gp)}", B),
            Spacer(1, 6),
            Paragraph(
                f"To {LP_NAME}: the Partnership will distribute "
                f"<b>{money(amount, gp)}</b> to you on <b>{fdate(pay_date, gp)}</b>. "
                f"The distribution comprises return of capital {money(roc, gp)}, "
                f"realised gain {money(gain, gp)} and investment income "
                f"{money(income, gp)}. Of the total, {money(recallable, gp)} is "
                f"subject to recall pursuant to Section 4.4 of the LPA.", B),
        ]
    else:
        S += [
            tbl([
                ["Component", "Amount"],
                ["Return of capital", money(roc, gp)],
                ["Realized gain", money(gain, gp)],
                ["Investment income", money(income, gp)],
                ["Total distribution", money(amount, gp)],
                ["  of which recallable", money(recallable, gp)],
            ], [3.6 * inch, 2.0 * inch]),
            Spacer(1, 8),
            Paragraph(f"Payment date: <b>{fdate(pay_date, gp)}</b>", B),
            Paragraph(f"Limited Partner: {LP_NAME}", B),
        ]
    S += [
        Spacer(1, 12),
        Paragraph(
            "Proceeds will be remitted to the account of record. Tax "
            "characterization is provisional and will be finalized on the "
            "Schedule K-1.", SM),
    ]
    doc.build(S)

    return fn, {
        "doc_type": "distribution",
        "fund_name": gp["name"],
        "gp_manager": gp["mgr"],
        "notice_date": notice_date.isoformat(),
        "payment_date": pay_date.isoformat(),
        "distribution_number": dist_no,
        "amount": round(amount, 2),
        "currency": "EUR" if gp["cur"] == "eur" else "USD",
        "return_of_capital": round(roc, 2),
        "realized_gain": round(gain, 2),
        "investment_income": round(income, 2),
        "recallable_amount": round(recallable, 2),
    }


def build_capital_account(gp, period_end, beg_nav, contrib, dist,
                          realized, unrealized, mgmt_fee, carry, end_nav):
    fn = f"{gp['short'].replace(' ', '_')}_CapAcct_{period_end.isoformat()}.pdf"
    path = os.path.join(OUT, fn)
    doc = SimpleDocTemplate(path, pagesize=LETTER, topMargin=0.7 * inch,
                            bottomMargin=0.7 * inch, leftMargin=0.8 * inch,
                            rightMargin=0.8 * inch)
    q = (period_end.month - 1) // 3 + 1
    S = [
        Paragraph(gp["mgr"], H),
        Paragraph(gp["name"], B),
        Spacer(1, 6),
        Paragraph(
            f"<b>Capital Account Statement &mdash; Q{q} {period_end.year}</b>", B),
        Paragraph(f"Limited Partner: {LP_NAME}", BD),
        Paragraph(f"As of: {fdate(period_end, gp)}", BD),
        Spacer(1, 10),
        tbl([
            ["Capital Account Activity", "Amount"],
            ["Beginning capital balance", money(beg_nav, gp)],
            ["Contributions", money(contrib, gp)],
            ["Distributions", f"({money(abs(dist), gp)})" if dist else money(0, gp)],
            ["Realized gain / (loss)", money(realized, gp)],
            ["Change in unrealized", money(unrealized, gp)],
            ["Management fee", f"({money(abs(mgmt_fee), gp)})"],
            ["Carried interest accrual", f"({money(abs(carry), gp)})"],
            ["Ending capital balance", money(end_nav, gp)],
        ], [3.6 * inch, 2.0 * inch]),
        Spacer(1, 10),
        tbl([
            ["Commitment Summary", "Amount"],
            ["Total commitment", money(gp["commitment"], gp)],
            ["Contributions to date", money(contrib * 3.2, gp)],
            ["Unfunded commitment",
             money(max(gp["commitment"] - contrib * 3.2, 0), gp)],
        ], [3.6 * inch, 2.0 * inch]),
        Spacer(1, 12),
        Paragraph(
            "Values are unaudited and subject to change. Carried interest is "
            "accrued on a hypothetical liquidation basis and may not be realized.",
            SM),
    ]
    doc.build(S)

    return fn, {
        "doc_type": "capital_account_statement",
        "fund_name": gp["name"],
        "gp_manager": gp["mgr"],
        "period_end": period_end.isoformat(),
        "currency": "EUR" if gp["cur"] == "eur" else "USD",
        "beginning_nav": round(beg_nav, 2),
        "contributions": round(contrib, 2),
        "distributions": round(dist, 2),
        "realized_gain": round(realized, 2),
        "unrealized_change": round(unrealized, 2),
        "management_fee": round(mgmt_fee, 2),
        "carried_interest": round(carry, 2),
        "ending_nav": round(end_nav, 2),
    }


# --------------------------------------------------------------------------

def main():
    truth = {}
    today = date(2026, 7, 27)

    for gp in GPS:
        cum = 0.0
        n_calls = random.randint(2, 4)
        # Space calls back through the last ~15 months.
        for i in range(n_calls):
            call_no = i + 1
            pct = random.uniform(0.08, 0.20)
            amt = round(gp["commitment"] * pct, 2)
            cum += amt
            notice_date = today - timedelta(days=random.randint(20, 450))
            due = notice_date + timedelta(days=random.choice([10, 10, 14, 15]))
            fee = round(amt * random.uniform(0.04, 0.09), 2)
            exp = round(amt * random.uniform(0.005, 0.02), 2)
            inv = round(amt - fee - exp, 2)
            fn, rec = build_capital_call(
                gp, i, call_no, amt, due, notice_date, cum, (inv, fee, exp))
            truth[fn] = rec

        # A couple of upcoming calls so the cash calendar has something live.
        if gp["vintage"] >= 2022:
            call_no = n_calls + 1
            amt = round(gp["commitment"] * random.uniform(0.06, 0.12), 2)
            cum += amt
            notice_date = today - timedelta(days=random.randint(1, 6))
            due = today + timedelta(days=random.choice([4, 7, 9, 12, 16]))
            fee = round(amt * 0.06, 2)
            exp = round(amt * 0.01, 2)
            inv = round(amt - fee - exp, 2)
            fn, rec = build_capital_call(
                gp, 99, call_no, amt, due, notice_date, cum, (inv, fee, exp))
            truth[fn] = rec

        # Distributions, mostly from older vintages.
        for j in range(random.randint(0, 2) if gp["vintage"] > 2021 else 2):
            amt = round(gp["commitment"] * random.uniform(0.03, 0.14), 2)
            pay = today - timedelta(days=random.randint(15, 400))
            roc = round(amt * random.uniform(0.4, 0.7), 2)
            gain = round(amt * random.uniform(0.2, 0.4), 2)
            income = round(amt - roc - gain, 2)
            recall = round(roc * random.uniform(0.0, 0.5), 2)
            fn, rec = build_distribution(
                gp, j + 1, amt, pay, pay - timedelta(days=8),
                (roc, gain, income, recall))
            truth[fn] = rec

        # Two quarters of capital account statements.
        for pe in (date(2026, 3, 31), date(2025, 12, 31)):
            beg = round(cum * random.uniform(0.75, 1.05), 2)
            contrib = round(cum * random.uniform(0.05, 0.15), 2)
            dist = round(-cum * random.uniform(0.0, 0.08), 2)
            realized = round(cum * random.uniform(-0.01, 0.06), 2)
            unreal = round(cum * random.uniform(-0.04, 0.11), 2)
            mfee = round(-cum * random.uniform(0.003, 0.009), 2)
            carry = round(-max(realized + unreal, 0) * 0.2, 2)
            end = round(beg + contrib + dist + realized + unreal + mfee + carry, 2)
            fn, rec = build_capital_account(
                gp, pe, beg, contrib, dist, realized, unreal, mfee, carry, end)
            truth[fn] = rec

    with open(os.path.join(OUT, "..", "ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=2, sort_keys=True)

    n = len(truth)
    types = {}
    for r in truth.values():
        types[r["doc_type"]] = types.get(r["doc_type"], 0) + 1
    print(f"Generated {n} documents across {len(GPS)} GPs -> {OUT}")
    for k, v in sorted(types.items()):
        print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
