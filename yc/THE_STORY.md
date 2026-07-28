# Altline — the story

Private credit. One page. If you can't tell it from memory in ninety seconds,
it isn't ready.

---

## The one-liner

**We turn a credit agreement into a machine-checkable specification, then check
every borrowing notice and agent calculation against it.**

Matter-of-fact, per PG. Not "AI for private credit" — that conveys nothing.

**The destination: the agentic back office for alternative assets.**

Alternatives run on documents that arrive on someone else's schedule and on people
who read them and key numbers into systems. That function is a back office. It is
staffed rather than automated because every document is governed by a different
negotiated contract, which is exactly the constraint that stopped being binding.

What makes "agentic" true here rather than decorative: a back office runs
**unattended on an event stream**. Work arrives without being requested, the system
acts on it, and a human sees only what broke. That is categorically different from a
copilot someone opens and queries — and it is why Hebbia is not the competitor even
where the documents overlap.

**But do not lead with it.** PG's instruction: *"Better to start with an overly
narrow description than try to describe it in its full generality and lose the
audience. If there's a simple one-sentence description that only conveys half your
potential, that's actually pretty good."*

"AI back office for alternatives" could describe Canoe, Allvue, Alter Domus, or
nothing. It conveys no mechanism. Lead with the agent's math; put the back office
underneath, where the specifics have earned it.

You are not constrained. You are sequenced. Private credit is the beachhead because
you have the domain access, the buyer has budget, and the answer is unambiguously
computable — so you can be provably right rather than plausibly helpful.

## The back-office map

Each surface is the same engine — compile the governing contract, then verify every
document it governs. Ranked by whether the check is sellable (see the two rules below).

| Surface | Governing document | What gets verified | Status |
|---|---|---|---|
| **Facility notices** | Credit agreement | Agent's interest math, borrowing conformity, availability | **Built** |
| Covenant compliance | Credit agreement | Compliance certificates vs. negotiated EBITDA definitions | Next |
| Borrowing base | ABL agreement | Borrower's borrowing base certificate | Next |
| LP fund operations | LPA | Capital calls, distributions, capital account statements | Built (LP-side engine) |
| CLO waterfalls | Indenture | Trustee's priority-of-payments calculation | Later |
| Fee and carry | LPA | Management fee offsets, waterfall, carry | Avoid — adversarial |

The last row is the biggest dollar pool in alternatives and the one to stay out of.
See rule 1.

---

## The observation

A credit agreement is not a record. It is a **specification**. It defines the
optionality: which interest periods are permitted, what margin applies at what
leverage, the day-count convention, minimum borrowing amounts, required notice
periods, how availability is computed.

Which means every borrowing notice and every agent rate-set has a *correct answer*
that is derivable from the agreement.

Nobody derives it. At facility setup an operator reads a 300-page agreement and
keys the terms into an Excel template that feeds the loan system. From then on the
administrative agent sends a notice with a number on it, and that number is
trusted — because recomputing it by hand, per notice, per facility, is not
feasible for a team running eighty positions.

So the agent's number becomes the truth. Even when it's wrong.

---

## What the demo shows

Extract the facility spec from the agreement once, with a clause citation for
every term. Then check the notice traffic against it. On our test facility —
$275M across three tranches — it found **10 breaks across 10 notices**:

**Three of four agent notices were mispriced.**

- Agent applied a 5.25% margin. At 5.20x leverage the grid in §3.02 requires
  5.75%. Interest billed $73,721.38; recomputed $77,513.04.
- Agent computed on Actual/365. §3.01 specifies Actual/360 for SOFR Loans.
- Agent omitted the Credit Spread Adjustment entirely — 0.00% where §3.01
  specifies 0.15% for a 3-month period.

**$5,453 of interest wrong in a single period, on one facility.** Annualize that
across a portfolio and it stops being a rounding error.

**And on the borrowing side:**

- A 2-month Interest Period elected where §2.03 permits only 1, 3 or 6.
- $1,250,000 requested where §2.02 requires integral multiples of $500,000.
- A SOFR borrowing noticed 1 business day out where §2.02 requires 3.
- A $48M draw against $46.5M of availability — a **$1.5M breach** after
  netting $22M drawn and $6.5M of outstanding letters of credit.

Every break cites the section that proves it. That's the difference between "your
agent is wrong," which is an argument, and a dispute letter.

---

## Why now

1. Private credit is **$1.96T in 2026, heading to $3.48T by 2031** at ~12% CAGR.
   Direct lending alone now matches the broadly syndicated loan market.
2. A model can finally read a 300-page negotiated agreement it has no template
   for. Every prior attempt was a rules engine with a per-agreement marginal cost,
   which is why this was only ever done by hand.
3. The incumbents' own answer to this problem is **renting you people**. Allvue
   sells "a private-debt-focused servicing team that executes daily workflows
   inside their platform — reconciliations, notice processing, break resolution."
   S&P's WSO does agent notice processing. When the market's solution is labour,
   there is a budget line to attack.

---

## Where we enter

Facility onboarding. It is the moment terms get keyed into the system, it has a
funded project budget, and it is the only point at which a lender is already
paying someone to read the agreement carefully.

We do the setup — agreement in, structured facility spec out, pushed into the
system of record via API rather than an operator copy-pasting an Excel template.
Then we stay, because the spec we built is what every subsequent notice gets
checked against.

Onboarding is the land. Notice checking is the recurring product.

---

## Two rules that decide whether this is a good business

**1. Only check a neutral or subordinate party's math.** The admin agent has no stake
in its own arithmetic error. Your borrower is subordinate to you. Both are easy
sells. The biggest dollar pool in alternatives is GP-side — management fee offsets
past step-down, quarterly accrual where the LPA says daily, waterfall and carry — and
the SEC has charged advisers over exactly this. It is also nearly unsellable, because
an LP who audits their GP's carry risks their next allocation. Never build a product
that requires your customer to accuse the counterparty they depend on.

**2. Check the math; never do the servicing.** Verification reduces to computation, so
it carries software margins. Servicing — wires, settlements, cash reconciliation,
corporate actions — is judgment and exception handling, which is why Alter Domus and
Citco run it at 20-35% by hiring people. Customers will ask us to take it on. That is
the road from software company to BPO.

## How it makes money

**Contingency first, then subscription.** The opening offer is a retrospective
audit — six months of agent notices, no upfront fee, we take a share of what we
recover. Freight and telecom bill audit are billion-dollar industries built on
exactly this (25–50% of recovered credits; Gartner finds 7–12% of enterprise telecom
invoices contain errors). It solves the problem every verification product has:
nobody believes you until you've found something in *their* data. And the first
customer doesn't have to trust us — they have to hand us PDFs.

**Then per facility, per year.** A lender running 80 facilities at $8–15K each is
$650K–1.2M. Priced against the credit ops headcount and the agent-servicing fees
it displaces, not per seat.

The expansion is covenant and compliance certificate monitoring — the same
extract-then-verify engine pointed at financial covenants, which is where the
credit risk actually lives.

And the long game is the data. Nobody knows what private credit is actually
priced at. Terms are bilateral and unpublished. A system that has parsed thousands
of agreements knows the real distribution of margins, leverage, and covenant
packages — the thing every LP, regulator and rating agency currently guesses at.
Burgiss built the private-markets benchmark by running software for allocators and
keeping the data; MSCI paid $913M. Preqin, with weaker data, went to BlackRock for
$3.2B.

---

## The insight worth leading the interview with

**The industry ingests first and reconciles afterward.** That ordering is the whole
cost. Reconciliation-after-ingestion is the largest line in the operating budget and
it exists because nobody validated at the point of entry — where it is cheap, and
where the governing document is still open in front of you.

**And the error it produces is an identity error, not an arithmetic one.** Two
lenders hold the same credit under different names — one books the sponsor's holdco,
the other books an operating subsidiary. On paper: two positions. In reality: one
borrower, and your concentration is double what the system reports. Same for industry
classification — packaging vs. industrials vs. consumer products decides the
benchmark, which decides reported performance. In private markets there is no ticker.
The name in the document is the only identifier that exists.

That is a performance-measurement and concentration-risk problem wearing a
data-hygiene costume. Invisible until something defaults.

This is the answer to "what do you understand that others don't." Lead with it.

---

## Why me

I have spent [X years] as an engineer automating operational processes inside
alternative assets. The specific thing I know: facilities get set up from
agreements by hand, into Excel-based templates, and then borrowing and agent
notices arrive that require calculations depending on the optionality that was
set up at inception. Nobody re-derives those calculations. I have watched it.

Three things an outsider gets wrong:

1. **Extraction is not the problem — recomputation is.** Anyone can pull a number
   off a notice. The product is having a second opinion derived from the contract.
2. **The agreement is the schema.** Most people treat it as a document to search.
   It is a specification you can compile.
3. **Trust is the gate.** A credit ops lead will not act on a model's number. That
   is why every finding cites a section and shows the arithmetic.

---

## Objections, raised before they're asked

**"Allvue, Solvas, WSO already do this."** They administer the loan and process
notices. None of them re-derives the agent's calculation from the agreement,
because none of them has the agreement as structured data — that is exactly the
step done by hand at onboarding. We are not replacing the servicing platform; we
sit upstream and feed it, and we check what it's told.

**"Hebbia already does covenant extraction and benchmarking on credit agreements."**
True, and the one I take seriously rather than wave off. But it's an LLM-mediated
research answer — extract the covenant, extract the metric, benchmark, with a
citation. We use the model only to extract terms; a deterministic engine computes
the expected number and diffs it to the cent. Their output still needs an analyst to
verify it. Ours is a number someone can act on. That split also decides the buyer:
Hebbia is a per-seat research copilot, front office; we're infrastructure wired to
the notice stream, back office — and we check the neutral agent's math rather than
the borrower's own certificate, which is the check a credit ops lead actually loses
sleep over, and the one with a verified dollar figure a contingency fee can be taken
on.

**"Credit agreements are too varied to parse reliably."** They are heavily
negotiated and every one differs. That is the moat, not the objection — it is why
rules engines failed and why the incumbent answer is labour. And we never post an
unverified term: anything low-confidence routes to a human with the clause
attached.

**"Getting this wrong is dangerous."** Yes. Which is why the product's output is a
flagged exception with a citation, not an automated payment. We are a second set
of eyes, and second sets of eyes are exactly what a credit ops team cannot hire
enough of.

**"This is a feature of a loan servicing platform."** Possibly, eventually. But
none of them can build it without the structured agreement, and getting that
requires doing the onboarding work nobody wants. We'd rather own that step.

---

## On the RFS — say nothing

YC's own guidance: the RFS is a fraction of what they fund, most successful
applicants work on ideas that aren't on it, and it is explicitly not a reason to
abandon insight in a niche you understand deeply. #12 is also effectively occupied
— Greenboard (YC W24) is at 500+ financial institutions and $20M raised.

**Do not mention the RFS.** Your edge is that you know something they don't.
