# YC Fall 2026 — Application Draft

**Deadline: today, Mon 27 Jul 2026, 8:00pm PT. Decision by 28 Aug.**

Working name: **Altline**. Change it if you hate it — nobody was ever rejected over a name.

Anything in `[BRACKETS]` is a fact only you have. Fill it in. Do not submit with brackets in it.

Everything below follows PG's own rules from *How to Apply to YC*: matter-of-fact,
first sentence carries the idea, no marketing-speak, flaws disclosed rather than hidden.

---

## READ THIS FIRST — do not mention the RFS

I previously told you to lean on RFS #12 (AI-Native Compliance). **That was wrong and
I'm retracting it.** Two reasons:

1. YC's own guidance is that the RFS is a fraction of what they fund, most successful
   applicants work on ideas that aren't on it, and it is explicitly *not* a reason to
   abandon hard-won insight in a niche you understand deeply.
2. **#12 is effectively occupied — by YC.** Greenboard (YC W24) is building "Rippling
   for financial compliance," is at 500+ financial institutions, and raised $20M
   including a $15.5M Series A led by Base10 in May 2026. There are 68 compliance
   companies in the YC portfolio.

Auditing an agent's interest calculation is not regulatory compliance, and a partner
who sees you reaching for their list learns that you'd rather be adjacent to it than
right about your own market. Your strongest asset is that you know something they
don't.

**Read `THE_STORY.md` before you fill any of this in.** It is the ninety-second
version and everything below is downstream of it.

---

## COMPANY NAME
Altline

## DESCRIBE WHAT YOUR COMPANY DOES IN 50 CHARACTERS OR LESS
```
We audit private credit agents' math
```
(35 characters. Concrete, and a partner immediately knows who pays. Alternates:
`Credit agreements become checkable software` (43) — more accurate about the
mechanism but less obvious who the buyer is. Use the first.)

## COMPANY URL
`https://altline.co`

## DEMO VIDEO
`[LINK — see DEMO_VIDEO_SCRIPT]`

---

## WHAT IS YOUR COMPANY GOING TO MAKE?

> PG reads this first. He wants to be able to reproduce your idea after one sentence.
> Lead with the mechanism, not the mission.

```
We turn a private credit agreement into a machine-checkable specification, then
check every borrowing notice and agent interest calculation against it.

A credit agreement is not a record, it is a specification. It defines which
interest periods are permitted, what margin applies at what leverage, the day-count
convention, minimum borrowing amounts, required notice periods, and how
availability is computed. So every notice that follows has a correct answer
derivable from the contract.

Nobody derives it. At facility setup an operator reads the agreement and keys terms
into an Excel template that feeds the loan system. After that the administrative
agent sends a notice with a number on it and the number is trusted, because
recomputing it by hand for every notice on every facility is not feasible for a
team running eighty positions. The agent's number becomes the truth even when it
is wrong.

We extract the facility spec once, with a clause citation for every term, and push
it into the system of record by API instead of a copy-pasted spreadsheet. Then
every subsequent notice gets checked against it: is this Interest Period permitted,
is the Applicable Margin right for the current leverage, is the day count the one
the agreement specifies, does this draw exceed availability net of letters of
credit, and independently — what should the interest actually be?

Facility onboarding is where we enter, because it is a funded project and it is the
one moment a lender is already paying someone to read the agreement carefully.
Notice checking is what we sell forever after.

The validation layer is the part that matters, and it is why this is not a document
tool. Extraction alone is a demo. Because the agreement is a specification, we can
recompute the answer: principal times the sum of Term SOFR, the credit spread
adjustment for that Interest Period, and the Applicable Margin at the current
leverage tier, over the day count the agreement actually specifies. When the agent's
number and ours disagree, one of them is wrong and we can show which.

Every extracted term carries the clause it came from, and every finding shows the
arithmetic. That matters because a credit operations lead will not act on a model's
assertion — they will act on "§3.02 requires 5.75% at this leverage, the agent
applied 5.25%, here is the sentence."

We price per facility per year, because that is the unit our customer's cost scales
with. We are replacing the servicing headcount they rent today, not selling their
team a better spreadsheet.
```

## HOW FAR ALONG ARE YOU?

> Be exact and be honest about the synthetic corpus. YC partners smell inflated
> traction instantly, and getting caught on this one thing poisons everything else.

```
Working software as of today, built over [X hours/days].

It parses a credit agreement into a structured facility spec — tranche commitments,
the four-tier pricing grid, permitted Interest Periods, credit spread adjustments by
period, day-count conventions, minimum borrowing and integral multiple, required
notice days, LC sublimit — each with the section it came from. Then it checks the
notice traffic against it.

On a $275M test facility across three tranches it found 10 breaks across 10 notices.
Three of four agent notices were mispriced:

- Agent applied a 5.25% Applicable Margin. At 5.20x Total Net Leverage the §3.02
  grid requires 5.75%. Billed $73,721.38; recomputed $77,513.04.
- Agent computed interest Actual/365 where §3.01 specifies Actual/360 for SOFR Loans.
- Agent omitted the Credit Spread Adjustment — 0.00% where §3.01 specifies 0.15%
  for a 3-month Interest Period.

$5,453 of interest wrong in a single period on a single facility.

On the borrowing side: a 2-month Interest Period elected where §2.03 permits only
1, 3 or 6; $1,250,000 requested where §2.02 requires integral multiples of $500,000;
a SOFR borrowing noticed 1 business day out where §2.02 requires 3; and a $48M draw
against $46.5M availability — a $1.5M breach after netting $22M drawn and $6.5M of
outstanding letters of credit.

Every finding cites the section that proves it and shows the arithmetic.

Honest caveat: the agreement and notices are synthetic. I wrote them to mirror the
structures I have worked with — a real pricing grid, real CSA tiers, the actual
Actual/360 convention — but they are a test harness, not a customer's paper. Real
credit agreements are confidential. Getting the first real one from a design partner
is this week's only job.

Users: [N] conversations with private credit operations leads as of today. [Paste
the sharpest verbatim quote. One sentence from a real credit ops person beats
everything above it.]

Revenue: none. Company: not yet formed.
```

## WHY DID YOU PICK THIS IDEA TO WORK ON? WHAT DO YOU UNDERSTAND ABOUT IT THAT OTHERS DON'T?

> This is where you win. Domain access is the one thing a smarter generalist
> cannot copy over a weekend.

```
I am a software engineer in asset management at BlackRock, where I have spent
[X years] automating operational processes across alternative assets and most
recently building retrieval systems over private fund documents. I have watched this
failure mode from inside the largest asset manager in the world.

[Say where you work — it is the strongest credibility signal in this application and
a partner will find it in thirty seconds anyway. Note the obvious: BlackRock bought
Preqin for $3.2B, so the thesis that private markets data is the prize is one your
own employer has already validated with cash.]

The specific thing I have seen repeatedly and that nobody outside this work knows:
facilities get set up from credit agreements by hand, into Excel-based templates
that feed the loan system. Then borrowing notices and agent notices arrive that
require calculations depending on the optionality that was configured at inception —
which interest period was elected, which margin tier the borrower is in, which day
count applies. Nobody re-derives those calculations. The agent's number is accepted
because checking it by hand, per notice, per facility, is not a job anyone can staff.

The second thing, which took working inside a large manager to see: the industry
ingests everything first and reconciles afterward. That ordering is why the cost is
what it is. Reconciliation-after-ingestion is the single largest line in the
operating budget, and it exists because nobody validated the data at the point of
entry — where it is cheap, and where the governing document is still in front of you.

And the failure that ordering produces is not a wrong number, it is a wrong
identity. Two lenders hold the same credit under different names — one books the
holding company the sponsor uses, the other books an operating subsidiary. On paper
those are two positions. In reality it is one borrower and your exposure is double
what your system says. The same happens to industry classification: whether a
borrower is coded packaging, industrials or consumer products decides which
benchmark it is measured against, which decides reported performance. In private
markets there is no ticker to fall back on, so the name in the document is the only
identifier there is.

That is not a data-hygiene problem. It is a performance-measurement and
concentration-risk problem wearing a data-hygiene costume, and it is invisible until
something defaults.

We already do this. Entity resolution collapses name variants onto one obligor and
refuses to merge entities that only look similar — it will not fold Fund II into
Fund III, and it will not fold an opco into its holdco without evidence. Getting
that wrong silently corrupts a ledger for two quarters before anyone notices.

Three more things I know that someone approaching this from outside would get wrong:

1. Extraction is not the problem — recomputation is. Every team that attacks
documents in finance builds a better extractor and stalls. Anyone can pull a number
off a notice. The product is having an independent second opinion derived from the
contract, and being able to show the arithmetic.

2. The agreement is the schema. Most people treat a credit agreement as a document
to search. It is a specification you can compile, and once you have compiled it,
every downstream document becomes checkable rather than merely readable.

3. Trust is the gate, so the output is a cited exception rather than an automated
payment. A credit ops lead will not act on a model's assertion. They will act on
"§3.02 requires 5.75% at this leverage, the agent applied 5.25%, here is the clause."

Why now: private credit is $1.96T in 2026 heading toward $3.48T by 2031, direct
lending now matches the syndicated loan market in size, and a model can finally read
a heavily negotiated agreement it has no template for. Every prior attempt was a
rules engine with a per-agreement marginal cost, which is why the incumbent solution
is still labour — Allvue sells a servicing team that does notice processing and break
resolution inside your platform, and S&P's WSO does agent notice processing as a
service. When the market's answer to a problem is renting people, there is a budget
line to attack.
```

## WHO ARE YOUR COMPETITORS? WHAT DO YOU UNDERSTAND THAT THEY DON'T?

> PG explicitly says: name the obstacle, then say how you get a toehold. Do not
> pretend the servicing platforms don't exist. He will find them in ninety seconds.

```
Allvue, Solvas and S&P's WSO are the loan servicing platforms. They administer the
loan and process agent notices — but none of them re-derives the agent's calculation
from the agreement, because none of them holds the agreement as structured data.
That step is precisely what gets done by hand at onboarding, into a spreadsheet. We
are not replacing the servicing platform. We sit upstream of it, feed it by API, and
check what it is told.

Hebbia ($161M raised, ~$700M valuation, 33% of top global asset managers) is the one
I take seriously, because Matrix already does covenant extraction and benchmarking
across credit agreements with sentence-level citations. I want to be precise about
where that overlaps us and where it doesn't, rather than wave it away.

Hebbia produces a language answer: extract the covenant, extract the metric, benchmark
them, with a citation. The arithmetic itself is LLM-mediated, which is exactly where a
model is unreliable — margin plus CSA plus SOFR times a day-count fraction is not a
task you want an LLM doing unchecked. We use the model only to extract terms with a
citation; a deterministic engine computes the expected number and diffs it against
what the agent billed, to the cent. One produces a research answer an analyst still
verifies. The other produces a number someone can act on today.

That split determines the buyer. Hebbia is a per-seat copilot a research analyst
opens and queries — front office, research budget. We are event-triggered
infrastructure wired to the notice stream, running unattended, posting an exception
only when something's wrong — back office, ops budget. And covenant monitoring checks
the borrower's own compliance certificate, the same side as the deal team that sourced
the loan. We check the administrative agent's arithmetic — a neutral party — which is
the check a credit ops lead actually loses sleep over and the one that makes a
contingency fee possible, because there is a verified dollar figure to take a cut of.

Rogo and Capsa are further out: data rooms, CIMs, deal screening. Pure front office.

The instructive detail across all three: Hebbia licenses Preqin's data. The
best-capitalized document-AI company in finance had to rent a data layer, because
reading documents you're shown doesn't accumulate into owning anything. Compiling the
agreements that govern a portfolio does.

Where they beat us today, plainly: the servicing platforms have deep system
integrations, years of edge cases, and SOC 2. We have none of that. Those are
money-and-time problems rather than insight problems, but they are real and they
gate our first enterprise deal.

What the incumbents' architecture makes hard rather than impossible: every prior
attempt to structure credit agreements was a rules engine, and a rules engine has a
marginal cost for every new agreement. Credit agreements are heavily negotiated and
no two are identical, so that cost never amortises — which is exactly why the
industry's answer is still a servicing team rather than software. That is the wedge,
and it is the same wedge that has worked every time a general model ate a rules
engine.
```

## HOW DO OR WILL YOU MAKE MONEY? HOW MUCH COULD YOU MAKE?

```
We start on contingency and convert to subscription.

The first engagement is a retrospective audit: give us your last six months of agent
notices, we check them against your agreements, and we take a share of what we
recover. No upfront fee. This is the standard model in the industries that already
do this work by hand — freight and telecom bill audit run at 25-50% of recovered
credits, and Gartner finds 7-12% of enterprise telecom invoices contain errors.

It solves the problem every verification product has, which is that nobody believes
you until you have found something in their data. It also means our first customer
does not have to trust us. They have to hand us PDFs.

Then per facility, per year. A lender running 80 facilities at $8-15K each is
$650K-1.2M in ACV, priced against the credit operations headcount and agent-servicing
fees it displaces rather than per seat, because the customer's cost scales with
facilities and so should ours.

What we will not do is the servicing itself. Wires, settlements, cash reconciliation
and corporate actions are judgment and exception handling — that is the business
Alter Domus and Citco run at 20-35% margins by hiring people. Customers will ask us
to take it on. Doing so is how a software company becomes a BPO, and I would rather
name that boundary now than discover it at scale.

Facility onboarding is billed as a setup fee per facility. It is project-shaped
revenue and I would rather say so than have you point it out — but unlike a pure
services engagement it produces the structured spec that the recurring product runs
on, so the land and the expand are the same artifact.

Bottom-up: private credit is $1.96T in AUM in 2026 and forecast to reach $3.48T by
2031. [Verify the count of US direct lenders and BDCs before you submit — do not
guess in front of people who will check.] At 80 facilities and $10K each, a thousand
lenders is $800M of addressable ACV.

That is the SaaS business, and on its own it is a good company rather than a large
one. The reason to build it is what the software accumulates.

Nobody knows what private credit is actually priced at. Terms are bilateral and
unpublished — there is no tape. A system that has compiled thousands of credit
agreements knows the real distribution of margins, leverage tiers, covenant packages
and call protection, which is the thing every LP, allocator, regulator and rating
agency currently estimates. That matters more here than in any other private asset
class, because private credit is the one growing fastest and the one supervisors are
most worried about being opaque.

The precedent: Burgiss built the private markets benchmark by sourcing data
exclusively from LPs using its platform — no voluntary submissions, no FOIA. It ran
back-office software and the dataset came out as exhaust. MSCI paid $913M. Preqin,
with weaker ground truth, sold to BlackRock for $3.2B.

Onboarding is what makes the timeline work. Checking notices gets you one facility's
traffic at a time. Doing a lender's facility onboarding hands you their whole book of
agreements at once.

So there are three acts and each funds the next:

1. Facility onboarding and notice checking. Per-facility SaaS, replacing rented
   servicing headcount. $650K-1.2M ACV at 80 facilities.
2. Covenant and compliance certificate monitoring. The same extract-then-verify
   engine pointed at financial covenants. Hebbia already does covenant extraction
   and benchmarking, so I am not calling this open water — but their answer is
   LLM-mediated and ours would be a deterministic recomputation against the
   agreement's actual EBITDA add-back definitions, which is the same edge we have
   in Act 1. Same buyer, higher price, no new sales motion.
3. Pricing data. What private credit is really priced at, derived from thousands of
   compiled agreements. Every LP, allocator, regulator and rating agency currently
   estimates this.

To say the destination out loud once, because I would rather state it than have it
inferred: we are building the agentic back office for alternative assets.

Alternatives run on documents that arrive on someone else's schedule and on people
who read them and key numbers into systems. That function is a back office, and it
is staffed rather than automated because every document is governed by a different
negotiated contract. That constraint is the one that just stopped being binding.

The same engine — compile the governing contract, verify every document it governs —
points at compliance certificates against the credit agreement, borrowing base
certificates against an ABL, capital calls against a limited partnership agreement,
priority of payments against a CLO indenture. I have already built the LP-side
version of this for capital calls and capital account statements, which is how I know
the engine generalises rather than hoping it does.

The word I would defend is "unattended". A back office runs on an event stream:
work arrives without being requested, the system acts, and a human sees only what
broke. That is a different product from a copilot someone opens and queries, and it
is the reason the incumbents' answer to this problem is still headcount.

I am not building all of that yet and I would rather not pretend otherwise. Private
credit facilities are the right first surface because I have the domain access, the
buyer has budget, and the answer is unambiguously computable — so we can be provably
right rather than plausibly helpful. That property is what lets the second surface be
sold on evidence instead of on a story.

The obvious objection, and I would rather raise it than have you raise it: we do not
own this data, our customers do, and credit agreements carry confidentiality
provisions. That is a contract design problem and it has to be solved in the first
customer agreement, not the fiftieth — explicit, opt-in, aggregated and anonymized so
that no individual facility is identifiable, with benchmark access as the
consideration. Burgiss cleared exactly this bar on LP data. If we do not get the
rights language right in agreement number one, act three never happens, and I would
rather lose an early deal than sign one without it.
```

## PLEASE TELL US ABOUT SOMETHING IMPRESSIVE THAT EACH FOUNDER HAS BUILT OR ACHIEVED

> **PG says this is the most important question on the application.** He also says
> do not list the startup itself. Magnitude matters more than category. Your
> transformation is a genuinely strong answer — it is rare, verifiable, and it is
> evidence of exactly the trait YC is underwriting: sustained execution against
> a hard goal with no external accountability.

```
I went from clinically obese to visibly lean and was written up in GQ for it.
[ONE specific number and ONE specific mechanism. e.g. "I lost 42kg over 19 months,
tracked every meal for 600 consecutive days, and did not miss a training session
in the final year." The number and the streak are what make this land — without
them it reads as a claim rather than a feat. Link the GQ piece.]

That took [X] months of doing the boring correct thing daily with nobody checking.
It is the closest analogue I have to what building a company actually requires.

Professionally: [PICK ONE and quantify it — the single largest process you
automated inside alternative assets. Format it as: "X was done by hand by N people
taking H hours per week; I built Y; it now takes M minutes." A number a partner
can picture beats any adjective. If you have a promotion timeline, dollar value
saved, or headcount avoided, use it.]
```

## PLEASE TELL US ABOUT THE TIME YOU MOST SUCCESSFULLY HACKED SOME (NON-COMPUTER) SYSTEM TO YOUR ADVANTAGE

> PG calls this the wildcard and says a great answer alone has earned people
> interviews. He is screening for people who beat systems rather than obey them.
> Do not write about code. Do not write something you think sounds respectable.

```
[YOURS. The strongest version is a specific instance where you got a result the
system was not set up to give you, through a legitimate but non-obvious route.

Three seams worth mining, in order of likely strength:

1. The GQ feature. You did not have a publicist. How did an unknown person get
into GQ? If you pitched it, found the right editor, built an audience first, or
engineered the story so it was easy to write — that is a textbook answer. Media
placement is a closed system and you opened it.

2. The visa and immigration path. You said you have let visas decide your future.
Every immigrant has at least one story of finding the route nobody told them about.
If you ever found a filing path, category, or timing move that others in your
position missed, write that.

3. Anything where you got access, a decision, or a price by finding the one person
who could actually say yes and going straight to them.

Write it in four sentences: what the system was, what it was set up to deny you,
what you actually did, what you got. Concrete beats clever.]
```

## WHO WRITES CODE, OR DOES OTHER TECHNICAL WORK ON YOUR PRODUCT?

```
I do, and I wrote all of it. [If any of your architect friends touched the repo,
say so explicitly and say exactly what they did. YC checks this and a clean
disclosure costs you nothing while a discovered omission costs you everything.]
```

## ARE YOU LOOKING FOR A CO-FOUNDER?

> You said "someone in mind, not locked." Do not hide this and do not oversell it.
> Solo is a real headwind at YC; a vague half-committed co-founder is worse than
> a clear solo answer.

```
[PICK ONE — decide before you submit.]

IF THEY COMMIT TODAY:
[Name], [what they do], committed to full-time in the batch. [One line on the
single most impressive thing they have built.] We have worked together on
[what, for how long].

IF THEY DO NOT COMMIT TODAY:
Applying solo. There is one person I want and we have been talking; I am not going
to list someone as a co-founder before they have actually committed, and I would
rather tell you that than dress it up. If they come, they come as an equal.

I have shipped this alone so far and I am in the domain the customer lives in.
```

## WHERE DO YOU LIVE NOW, AND WHERE WOULD THE COMPANY BE BASED AFTER YC?

```
I live in [CITY], US. The company would be based in San Francisco.
```

## HOW LONG HAVE YOU BEEN WORKING ON THIS?

```
[Be exact and do not inflate. "Nine days, full-time on evenings and weekends" is a
better answer than a vague one, because it makes the amount you built look like
what it is — fast. Speed is the signal here, not tenure.]
```

## WHAT CONVINCED YOU TO APPLY TO Y COMBINATOR?

```
[Answer in your own voice — this is the one question where a real reason beats a
polished one. The honest version of what you told me is strong: you have spent
years having your future decided by things outside your control, you are done with
that, and this is you taking the decision back. Say it in three sentences without
melodrama. What you want from YC specifically: the customer introductions. Your
buyer is a category YC's network reaches — the alumni base is full of people who
raise and allocate capital, and design-partner intros are worth more to us than
the money.]
```

## IF WE FUNDED YOU, WHAT WOULD YOU WORK ON FOR THE NEXT MONTH?

```
Get three real credit agreements from design partners and compile them. Publish the
extraction accuracy honestly, including the misses. Every term the model gets wrong
becomes a validation rule or a schema change the same day.

Then run their last six months of agent notices through the checker retrospectively.
That is the demo that closes a credit ops lead: not "here is what we could catch"
but "here are the three notices you already paid that were wrong."

Then the two things that gate the first paid contract: a write-path integration into
one loan servicing system, and starting SOC 2.
```

## OTHER IDEAS YOU CONSIDERED

> PG says YC quite often funds groups on an idea they listed as an alternate.
> This is a free option. Do not waste it.

```
Covenant monitoring: compile the financial covenants and the compliance certificate
schedule out of the credit agreement, then check each quarterly certificate against
the actual definitions — which are negotiated per deal and where EBITDA add-backs
live. Today a credit analyst recomputes this by hand, or trusts the borrower's
spreadsheet. Same engine, same buyer, and it moves us from operations into credit
risk, which is where the money and the fear are.

LP-side fund operations: the same extract-and-verify engine pointed at capital calls,
distributions and capital account statements for allocators, entered at portfolio
migration. I built this first and it works — 43 documents across 6 general partners
in 6 formats, reconciled against a legacy export, finding a capital call that was
never keyed and one fund double-counted under two name variants.

I did not list it as the main idea because the buyer is smaller, Canoe already serves
the top of that market, and my domain edge is weaker there. But it is the second
surface of the same back office rather than a different company, and having built
both is the reason I believe the engine generalises.
```

---

# BEFORE YOU HIT SUBMIT

1. **Submit early, edit later.** YC lets you keep editing until the deadline. Get a
   complete draft in by 6pm PT. Do not be writing prose at 7:55.
2. **Do the video.** YC says applicants with a founder video are *statistically much
   more likely* to get an interview. One take, one minute, phone camera, your face,
   good light. Perfect is not the bar; existing is the bar.
3. **Kill the brackets.** Search the text for `[` before submitting.
4. **Red-pen pass.** PG's literal instruction: print it, cross out every word you
   do not need. Do this once. It will cut 20%.
5. **Numbers you cannot verify come out.** One checkable exaggeration costs more
   than every strong sentence gains.
6. **Be ready for the data-rights question in the interview.** You are now telling
   a story whose third act is a data asset. The first question any competent partner
   asks is "you don't own that data — how do you get the rights?" The answer is in
   the money section: opt-in, aggregated, anonymized, in customer agreement number
   one, with benchmark access as the consideration. Know it cold. If you fumble
   this, the big story becomes a liability instead of the reason to fund you.
