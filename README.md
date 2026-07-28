# Altline

**We audit private credit agents' math.**

*Long term: the agentic back office for alternative assets.*

Alternatives run on documents that arrive on somebody else's schedule — agent
notices, borrowing requests, compliance certificates, capital calls, capital
account statements — and on people who read them and key numbers into systems.
That function is a back office, and it is staffed rather than automated because
every document is governed by a different negotiated contract.

A back office is defined by running **unattended on an event stream**: work arrives
without being requested, the system acts on it, and a human sees only what broke.
That is the distinction from a copilot you open and query, and it is what "agentic"
has to mean here to be worth saying.

Private credit facilities are the first surface. The rest of the map is in
`yc/THE_STORY.md`.

---

## First surface: private credit facilities

A credit agreement is a *specification*, not a record. It defines which interest
periods are permitted, what margin applies at what leverage, the day-count
convention, minimum borrowing amounts, required notice periods, how availability
is computed. So every borrowing notice and every agent rate-set that follows has a
**correct answer derivable from the contract**.

Nobody derives it. At facility setup an operator reads the agreement and keys terms
into an Excel template that feeds the loan system. After that the administrative
agent sends a notice with a number on it, and that number is trusted — because
recomputing it by hand for every notice on every facility is not a job anyone can
staff. The agent's number becomes the truth even when it's wrong.

## Run it

```bash
pip install fastapi uvicorn pypdf reportlab

python3 credit_corpus.py     # build the agreement + notice traffic
python3 app.py               # -> http://localhost:8000
```

Provider keys go in `.env` — auto-detect order is `NVIDIA_API_KEY`, then
`OPENROUTER_API_KEY`, then `ANTHROPIC_API_KEY`. Without one, the deterministic
parser runs alone and the demo still works.

CLI, no server:

```bash
python3 facility.py
```

## The architecture, which is the whole argument

**The model reads. The engine computes.**

The LLM extracts terms from the agreement, each with the clause it came from —
language work, where models are strong. Then *deterministic code* recomputes every
interest figure. Never the model.

That split is the differentiator. Hebbia's Matrix does covenant extraction and
benchmarking on credit agreements with sentence-level citations, and it's good —
but the answer is LLM-mediated end to end. Asking a model to compute
`principal × (SOFR + CSA + margin) × days/360` gets you something plausible, and
plausible is worthless when the output is a dollar figure you're disputing with
your agent.

One produces a research answer an analyst still verifies. The other produces a
number someone can act on.

## What it finds

On the test facility — $275M across three tranches, 10 notices:

| | |
|---|---|
| interest mispriced | **$5,453.47** in one period, one facility |
| agent notices wrong | 3 of 4 |
| total findings | 10 across 10 notices |
| availability breach | $1.5M |

Agent-side:
- **Wrong margin tier** — applied 5.25% where the §3.02 grid requires 5.75% at
  5.20x leverage. Billed $73,721.38; recomputed $77,513.04.
- **Wrong day count** — Actual/365 where §3.01 specifies Actual/360 for SOFR Loans.
- **Missing credit spread adjustment** — 0.00% where §3.01 specifies 0.15%.

Borrower-side:
- 2-month Interest Period where §2.03 permits only 1, 3 or 6.
- $1,250,000 requested where §2.02 requires integral multiples of $500,000.
- SOFR borrowing noticed 1 business day out where §2.02 requires 3.
- $48M draw against $46.5M availability, after netting $22M drawn and $6.5M of LCs.

Every finding cites the section that proves it and shows the arithmetic. That's the
difference between "your agent is wrong," which is an argument, and a dispute letter.

## Positioning

| | What they do | Where we differ |
|---|---|---|
| **Allvue, Solvas, S&P WSO** | Administer the loan, process agent notices | They don't re-derive the agent's calculation, because they don't hold the agreement as structured data. We sit upstream and check what they're told. |
| **Hebbia** | Covenant extraction + benchmarking, cited | LLM-mediated research answer, per-seat, front office. We're event-triggered infrastructure in the back office, and we check the *neutral agent's* math, not the borrower's own certificate. |
| **Rogo, Capsa** | Data rooms, CIMs, deal screening | Pure front office. Different buyer entirely. |

Note that Hebbia licenses Preqin's data. The best-capitalized document-AI company in
finance had to rent a data layer, because reading documents you're shown doesn't
accumulate into owning anything. Compiling the agreements that govern a portfolio
does.

## Two rules that decide whether this is a good business

1. **Only check a neutral or subordinate party's math.** The admin agent has no
   stake in its own arithmetic error; your borrower is subordinate to you. Both are
   easy sells. GP-side fee and waterfall auditing is a bigger dollar pool and nearly
   unsellable — an LP who audits their GP's carry risks their next allocation.
2. **Check the math; never do the servicing.** Verification is computation, so it
   carries software margins. Wires, settlements, cash recs and corporate actions are
   judgment — that's the business Alter Domus and Citco run at 20–35% by hiring
   people. Customers will ask. That's the road from software company to BPO.

## Go to market

Contingency first. *"Give us six months of agent notices. We audit them free and
take a share of what we find."* Freight and telecom bill audit are billion-dollar
industries built on exactly this — 25–50% of recovered credits, and Gartner finds
7–12% of enterprise telecom invoices contain errors.

It solves the problem every verification product has: nobody believes you until
you've found something in *their* data. And the first customer doesn't have to trust
you — they have to hand you PDFs.

Then per facility, per year. 80 facilities at $8–15K is $650K–1.2M ACV.

## On the corpus

`credit_corpus.py` generates synthetic documents — a real pricing grid, real CSA
tiers, the actual Actual/360 convention, and six deliberately seeded defects. They
mirror structures worked with in production but they are **a test harness, not
customer paper**. Real credit agreements are confidential. Getting the first real
one from a design partner is the next job.

## Files

**Private credit — the product**

| | |
|---|---|
| `credit_corpus.py` | generates the agreement, borrowing notices, agent notices |
| `facility.py` | facility spec extraction (LLM + deterministic) and the checkers |
| `app.py` | demo server + UI |

**LP-side fund operations — second surface, built first**

Not an abandoned direction. The same extract-then-verify engine pointed at the
allocator side of the back office: capital calls, distributions and capital account
statements from many GPs, reconciled against a portfolio system. Built before the
private credit wedge and kept because it is evidence the engine generalises across
back-office surfaces — which is the whole thesis.

Out of the demo deliberately. One product on screen, not two.

| | |
|---|---|
| `app_alts_lp.py` | the LP-side demo UI |
| `pipeline.py` | four-agent extraction pipeline + reconciliation |
| `entities.py` | fund entity resolution (name variants → one position) |
| `migration.py` | legacy export vs. source documents |
| `generate_corpus.py`, `legacy_export.py` | LP-side document generators |
| `offline.py`, `schemas.py` | deterministic fallback parser, field schemas |
