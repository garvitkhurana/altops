# YC Fall 2026 — paste-ready, in form order

Every field from the actual form. Copy the block under each heading.
`[BRACKETS]` = only you know it. Kill every one before submitting.

**Blocking errors on your form right now:** company name · company description ·
**founder video** · incomplete profile. The video is required — there is no
submission without it.

---

# ACCOMPLISHMENTS

## Please tell us about a time you most successfully hacked some (non-computer) system to your advantage.

```
Our university's course registration system had a UI restriction that could be
bypassed using the browser's inspect element. The bottleneck wasn't the trick — it
was information asymmetry: a few people knew, most didn't. Instead of using it
quietly, I documented it, made short tutorial videos, and shared them across student
groups. Within hours hundreds of students were registering for the best professors
before seats filled, and the unfairness in the existing process was impossible to
ignore. The university rebuilt the registration system afterward. The lesson: the
biggest leverage usually comes from changing how information flows through a system,
not from optimizing your own position inside it.
```

## Please tell us in one or two sentences about the most impressive thing other than this startup that you have built or achieved.

```
I went from clinically obese to visibly lean and was written up in GQ for it. I lost
39kg over 19 months, tracked every meal for 600 consecutive days, and did not miss a
training session in the final year.
https://www.gqindia.com/live-well/content/how-to-lose-weight-like-this-guy-who-lost-39-kgs-and-got-ripped-his-weight-loss-diet-plan-workouts-to-follow
```
*[Optional second line if you have room: the largest process you automated at
BlackRock, with a number — hours saved per week, headcount avoided, dollar value.
Not required; the GQ answer alone is strong.]*

## Tell us about things you've built before. Include URLs if possible.

```
Altline (this application) — a private credit facility verification engine that
compiles a credit agreement into a machine-checkable spec and independently
recomputes every agent interest calculation against it. Built in [X hours/days],
Python + FastAPI, two-model extraction cross-check with quarantine on disagreement.
[github.com/you/altline — push it tonight if you have 10 spare minutes; this field
explicitly rewards a URL over a description.]

[Anything else real: side projects, scripts, automations you can describe without
naming proprietary detail, open source contributions.]
```

## List any competitions/awards you have won, or papers you've published.

```
[Fill if true. Blank is a completely normal answer — don't stretch for something.]
```

---

# FOUNDERS

## Complete my profile
Do this first, it's a hard blocker. Name, email, LinkedIn, education, employment
(BlackRock — say it), date of birth.

## Who writes code, or does other technical work on your product? Was any of it done by a non-founder?

```
I do, and I wrote all of it. No contractors, no non-founder contributors.
```
*[If any of your architect friends touched the repo, say exactly what they did.
YC checks. A clean disclosure costs nothing; a discovered omission costs everything.]*

## Are you looking for a cofounder?

**Pick one. Decide before you submit.**

```
IF THEY COMMIT TONIGHT:
No. [Name] is joining as co-founder — [what they do, one line on the most
impressive thing they've built]. We've worked together on [what, how long].

IF NOT:
Yes. There's one person I've been talking to and I'd rather tell you that than
list someone as a co-founder before they've actually committed. I'm looking for
a technical co-founder who has worked in credit or fund operations — someone who
has been the person keying facility terms into a loan system, not someone who
needs it explained. I've shipped this alone so far.
```

---

# FOUNDER VIDEO

One minute, ≤100MB. **Required.** Script: `yc/VIDEO_SCRIPTS.md` §1. Three takes max.

---

# COMPANY

## Company name
```
Altline
```

## Describe what your company does in 50 characters or less
```
We audit private credit agents' math
```
*(35 chars)*

## Company URL
```
https://altline.co
```

## Demo
Upload the screen recording. ≤3 min, ≤100MB. Script: `yc/VIDEO_SCRIPTS.md` §2.

## Link to the product
```
[Leave blank — it's local. Do not link localhost.]
```

## What is your company going to make?

```
We turn a private credit agreement into a machine-checkable specification, then
check every borrowing notice and agent interest calculation against it.

A credit agreement is not a record, it is a specification. It defines which
interest periods are permitted, what margin applies at what leverage, the day-count
convention, minimum borrowing amounts, required notice periods, and how availability
is computed. So every notice that follows has a correct answer derivable from the
contract.

Nobody derives it. At facility setup an operator reads the agreement and keys terms
into an Excel template that feeds the loan system. After that the administrative
agent sends a notice with a number on it and the number is trusted, because
recomputing it by hand for every notice on every facility is not feasible for a team
running eighty positions. The agent's number becomes the truth even when it is wrong.

We extract the facility spec once, with a clause citation for every term, and push it
into the system of record by API instead of a copy-pasted spreadsheet. Then every
subsequent notice gets checked: is this Interest Period permitted, is the Applicable
Margin right for the current leverage, is the day count the one the agreement
specifies, does this draw exceed availability net of letters of credit, and
independently — what should the interest actually be?

The architecture is the argument: the model reads, deterministic code computes. An
LLM asked to evaluate principal x (SOFR + CSA + margin) x days/360 produces something
plausible, and plausible is worthless when the output is a dollar figure you are
disputing with your agent. The model only extracts terms, each with the clause it
came from. Every calculation is code.

Long term this is the agentic back office for alternative assets — the same engine
pointed at compliance certificates, borrowing base certificates, capital calls,
CLO waterfalls. A back office is defined by running unattended on an event stream:
work arrives without being requested, the system acts, a human sees only what broke.
```

## Where do you live now, and where would the company be based after YC?
```
[Your city], USA / San Francisco, USA
```

## Explain your decision regarding location
```
I'm already in the US and would move to San Francisco for the batch and stay after.
My customers — private credit funds, direct lenders, BDCs — are concentrated in New
York, so I expect to spend significant time there, but the company would be based in
SF.
```

---

# PROGRESS

## How far along are you?

```
Working software as of today.

It parses a credit agreement into a structured facility spec — tranche commitments,
the four-tier pricing grid, permitted Interest Periods, credit spread adjustments by
period, day-count conventions, minimum borrowing and integral multiple, required
notice days, LC sublimit — each with the section it came from. Then it checks the
notice traffic against it.

On a $275M test facility across three tranches it found 10 findings across 10 notices.
Three of four agent notices were mispriced:

- Agent applied a 5.25% Applicable Margin. At 5.20x Total Net Leverage the §3.02 grid
  requires 5.75%. Billed $73,721.38; recomputed $77,513.04.
- Agent computed interest Actual/365 where §3.01 specifies Actual/360 for SOFR Loans.
- Agent omitted the Credit Spread Adjustment — 0.00% where §3.01 specifies 0.15% for
  a 3-month Interest Period.

$5,453 of interest wrong in a single period on a single facility.

On the borrowing side: a 2-month Interest Period elected where §2.03 permits only
1, 3 or 6; $1,250,000 requested where §2.02 requires integral multiples of $500,000;
a SOFR borrowing noticed 1 business day out where §2.02 requires 3; and a $48M draw
against $46.5M availability — a $1.5M breach after netting $22M drawn and $6.5M of
outstanding letters of credit.

Every finding cites the section that proves it and shows the arithmetic.

Two controls, because the obvious question is how I know the extraction is right.
First, the agreement is read by two different models independently and compared term
by term; where they disagree the term is quarantined out of the spec entirely rather
than averaged or majority-voted, and a human reads the clause. Second, extraction is
scored against a ground-truth file, and the metric I care about is not accuracy but
silent errors — terms we got wrong and posted anyway. A wrong term that gets flagged
is the system working. A wrong term that reaches a calculation misprices every notice
for the life of the facility and looks exactly as authoritative as a correct one.

Honest caveat: the agreement and notices are synthetic. I wrote them to mirror
structures I have worked with — a real pricing grid, real CSA tiers, the Actual/360
convention — but they are a test harness, not a customer's paper. Real credit
agreements are confidential. Getting the first real one from a design partner is this
week's only job.

Not yet built: balance-level reconciliation against the loan system. I have built the
equivalent on the LP side already.

4 conversations with private credit operations leads so far. The consistent theme:
the pain is not ingestion, it is what happens after a notice is booked. Exceptions
dashboards fire constantly and someone has to work every break by hand, which is
exactly the queue our validation layer is designed to feed — cited, with the
arithmetic attached, instead of a bare flag someone has to re-derive from scratch.
```

## How long have each of you been working on this? How much of that has been full-time?

```
Nine to ten days, evenings and weekends alongside my job at BlackRock. Zero
full-time. Everything described above was built in that window on my own
equipment and on my own time.
```

## What tech stack are you using?

```
Python. FastAPI for the service, pypdf for document text extraction, reportlab for
generating the synthetic corpus.

Models: provider-agnostic by design, auto-detecting across NVIDIA NIM, OpenRouter and
the Anthropic API — currently Llama 3.1 70B and Claude Haiku 4.5. The model layer is
deliberately swappable because the model is the cheap, commoditising part; the
extraction schema, the validation identities and the verification engine are the
product.

The model is used only to extract terms from the agreement with clause citations.
Every calculation — interest, margin tier lookup, day-count fractions, availability,
business-day notice periods — is deterministic Python with a test suite. That split
is intentional and is the core of the design.

AI coding tools: Claude Code and Cursor, heavily.
```

## Are people using your product?
```
No.
```

## When will you have a version people can use?
```
The demo works today against synthetic documents; a real customer can use it the
moment one hands over a real agreement, because the engine doesn't change — only
the input does. So the honest answer is closer to "as soon as a design partner
hands me their paper" than a calendar date, and that's the right thing to say to
a partner, because it's true and it puts the pressure where it belongs — on
getting that first document this week.
```

## Do you have revenue?
```
No
```

## If you are applying with the same idea as a previous batch, did anything change?
```
[Leave blank — first application.]
```

## If you have already participated in an incubator/accelerator
```
[Leave blank unless true.]
```

---

# IDEA

## Why did you pick this idea? Do you have domain expertise? How do you know people need this?

```
I am a software engineer in asset management at BlackRock, where I have spent
[X years] automating operational processes across alternative assets and most
recently building retrieval systems over private fund documents. I have watched this
failure mode from inside the largest asset manager in the world.

The specific thing I have seen repeatedly: facilities get set up from credit
agreements by hand, into Excel-based templates that feed the loan system. Then
borrowing notices and agent notices arrive that require calculations depending on the
optionality configured at inception — which interest period was elected, which margin
tier applies, which day count. Nobody re-derives those calculations. The agent's
number is accepted because checking it by hand, per notice, per facility, is not a
job anyone can staff.

The second thing, which took working inside a large manager to see: the industry
ingests everything first and reconciles afterward. That ordering is why the cost is
what it is. Reconciliation-after-ingestion is one of the largest lines in the
operating budget, and it exists because nobody validated at the point of entry —
where it is cheap, and where the governing document is still open in front of you.

And the failure that ordering produces is not a wrong number, it is a wrong identity.
Two lenders hold the same credit under different names — one books the holding
company the sponsor uses, the other an operating subsidiary. On paper that is two
positions. In reality it is one borrower and your concentration is double what your
system reports. The same happens to industry classification: whether a borrower is
coded packaging, industrials or consumer products decides which benchmark it is
measured against, which decides reported performance. In private markets there is no
ticker. The name in the document is the only identifier there is. That is a
concentration-risk and performance-measurement problem wearing a data-hygiene
costume, and it is invisible until something defaults.

How I know people need it: this is the work I do. The incumbents also tell you
directly — Allvue sells "a private-debt-focused servicing team that executes daily
workflows inside their platform: reconciliations, notice processing, break
resolution," and S&P's WSO sells agent notice processing as a service. When the
market's answer to a problem is renting you people, there is a budget line to attack.

What I have not done yet is put this in front of enough strangers. 4 conversations
with credit ops leads outside my employer so far, and the theme across all of them
was the same: the pain isn't ingesting the notice, it's what happens after it's
booked. Exception dashboards fire constantly and every break gets worked by hand.
That's the validation I was looking for — it means the product isn't "read the
document faster," it's "feed the exception queue something better than a bare flag."
Closing the gap on volume of conversations is this week's job, and I'd rather state
that than dress it up.
```

## Who are your competitors? What do you understand that they don't?

```
Allvue, Solvas and S&P's WSO are the loan servicing platforms. They administer the
loan and process agent notices, but none re-derives the agent's calculation from the
agreement, because none holds the agreement as structured data. That step is exactly
what gets done by hand at onboarding, into a spreadsheet. We are not replacing the
servicing platform — we sit upstream, feed it, and check what it is told.

Hebbia is the one I take seriously. Matrix already does covenant extraction and
benchmarking across credit agreements with sentence-level citations. The difference
is what kind of answer each produces. Hebbia gives a language answer — extract the
covenant, extract the metric, benchmark, cite — and the arithmetic is LLM-mediated,
which is precisely where a model is unreliable. We use the model only to extract
terms; deterministic code computes the expected figure and diffs it to the cent. One
produces a research answer an analyst still verifies. The other produces a number
someone can act on.

That split decides the buyer. Hebbia is a per-seat copilot a research analyst opens
and queries — front office, research budget. We are event-triggered infrastructure
wired to the notice stream, running unattended, surfacing an exception only when
something is wrong — back office, operations budget. And covenant monitoring checks
the borrower's own compliance certificate, the same side as the deal team that
sourced the loan. We check the administrative agent's arithmetic, a neutral party.
That is the check a credit ops lead actually loses sleep over, and the one with a
verified dollar figure a contingency fee can be taken on.

Rogo and Capsa are further out — data rooms, CIMs, deal screening. Front office.

What their architecture makes hard: every prior attempt to structure credit
agreements was a rules engine, and a rules engine has a marginal cost per agreement.
Credit agreements are heavily negotiated and no two are identical, so that cost never
amortises — which is why the industry's answer is still a servicing team. That is the
wedge, and it is the same one that has worked every time a general model ate a rules
engine.

Where they beat us today: deep system integrations, years of edge cases, and SOC 2.
We have none of that. Those are money-and-time problems rather than insight problems,
but they are real and they gate the first enterprise deal.

One instructive detail: Hebbia licenses Preqin's data. The best-capitalised
document-AI company in finance had to rent a data layer, because reading documents
you are shown does not accumulate into owning anything. Compiling the agreements that
govern a portfolio does.
```

## How do or will you make money? How much could you make?

```
Contingency first, then subscription.

The first engagement is a retrospective audit: give us six months of agent notices,
we check them against your agreements, and we take a share of what we recover. No
upfront fee. This is the standard model in the industries that already do this work
by hand — freight and telecom bill audit run at 25-50% of recovered credits, and
Gartner finds 7-12% of enterprise telecom invoices contain errors.

It solves the problem every verification product has, which is that nobody believes
you until you have found something in their data. It also means the first customer
does not have to trust us — they have to hand us PDFs. And it doubles as the
evaluation loop: a confirmed recovery is a ground-truth label, so precision is
measured directly by the fraction of our flags that survive contact with the agent.

Then per facility, per year. A lender running 80 facilities at $8-15K each is
$650K-1.2M ACV, priced against credit operations headcount and agent-servicing fees
rather than per seat, because the customer's cost scales with facilities and so
should ours.

Private credit is $1.96T of AUM in 2026, forecast to reach $3.48T by 2031. [Verify
the count of US direct lenders and BDCs before submitting — do not guess in front of
people who will check.] A thousand lenders at 80 facilities and $10K is $800M of
addressable ACV.

Then the expansion, which is where it stops being a good company and becomes a large
one. Covenant and compliance certificate monitoring is the same engine at a higher
price to the same buyer. And nobody knows what private credit is actually priced at —
terms are bilateral and unpublished, there is no tape. A system that has compiled
thousands of agreements knows the real distribution of margins, leverage tiers,
covenant packages and call protection, which every LP, allocator, regulator and
rating agency currently estimates. Burgiss built the private markets benchmark by
sourcing data exclusively from LPs using its platform and MSCI paid $913M for it;
Preqin, with weaker ground truth, sold to BlackRock for $3.2B.

The obvious objection, which I would rather raise than have you raise: we do not own
that data, our customers do, and credit agreements carry confidentiality provisions.
That is a contract design problem and it has to be solved in the first customer
agreement, not the fiftieth — explicit, opt-in, aggregated and anonymised so no
individual facility is identifiable, with benchmark access as the consideration.
Burgiss cleared exactly this bar. Get it wrong in agreement number one and the data
business never happens.

What we will not do is the servicing itself. Wires, settlements, cash reconciliation
and corporate actions are judgment and exception handling — the business Alter Domus
and Citco run at 20-35% margins by hiring people. Customers will ask us to take it
on. That is how a software company becomes a BPO, and I would rather name the
boundary now.
```

## Other ideas you considered

```
Covenant monitoring: compile the financial covenants and compliance certificate
schedule out of the credit agreement, then check each quarterly certificate against
the actual negotiated definitions — which is where EBITDA add-backs live. Today a
credit analyst recomputes this by hand or trusts the borrower's spreadsheet. Same
engine, same buyer, and it moves us from operations into credit risk, which is where
the money and the fear are.

Borrowing base certificate verification for asset-based lending: the borrower
computes it monthly, the lender trusts it, and the agreement defines exactly how
eligibility and advance rates work. Checking a subordinate party's math, which is the
easiest version of this to sell.

LP-side fund operations: the same extract-and-verify engine pointed at capital calls,
distributions and capital account statements for allocators, entered at portfolio
migration. I built this first and it works — 43 documents across 6 general partners
in 6 formats, reconciled against a legacy export, finding a capital call that was
never keyed and one fund double-counted under two name variants. I did not lead with
it because the buyer is smaller and Canoe already serves the top of that market. But
it is the second surface of the same back office rather than a different company, and
having built both is why I believe the engine generalises.
```

---

# EQUITY

| Question | Answer |
|---|---|
| Have you formed ANY legal entity yet? | **No** |
| Have you taken any investment yet? | **No** |
| Are you currently fundraising? | **No** |

---

# CURIOUS

## What convinced you to apply to Y Combinator?

```
I've spent years having my future decided by things outside my control — a visa
process I have no leverage over, timelines set by other people's paperwork. This is
me taking the decision back. I know the domain, I can ship, and I'm done waiting
for permission to try.

What I want from YC specifically is customer introductions. My buyer is credit
operations leads at private credit funds and direct lenders, and that's a category
YC's network reaches directly. A design partner intro is worth more to me right now
than the money.
```
*[Cut "a visa process" if you'd rather not name it explicitly — "things outside my
control" alone still lands. Better yet: type this one yourself. A partner can often
tell polished prose from a founder's real voice, and this field is testing for the
latter.]*

## How did you hear about Y Combinator?
```
[Honest, one line. Hacker News / Paul Graham's essays / a founder you know.]
```

---

# BATCH PREFERENCE
```
Fall 2026
```

---

# BEFORE YOU HIT SUBMIT

- [ ] Profile completed (hard blocker)
- [ ] Founder video uploaded (hard blocker)
- [ ] Company name + 50-char description filled (hard blockers)
- [ ] Zero `[` brackets anywhere in the submitted text
- [ ] The synthetic-corpus sentence is still in. **Do not cut it.**
- [ ] Numbers you can't defend are softened — pricing and lender count are estimates
- [ ] No mention of the RFS anywhere
- [ ] Submit by 7:15pm, then keep editing until 8:00pm
