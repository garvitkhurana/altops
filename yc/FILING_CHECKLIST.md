# Filing checklist — YC Fall 2026

**Deadline: today, Mon 27 Jul 2026, 8:00pm PT.** Decision by 28 Aug.
Submit early and keep editing — YC lets you revise until the deadline.

Everything is in `~/Projects/altops/`. Docs in `yc/`, code in the root.

---

## Order of operations

Do these in this order. It is not arbitrary — DMs have a latency you can't
control, and the demo warms you up for the founder video.

### 1. DMs — right now, before anything else (20 min)

15 private credit operations leads on LinkedIn. Not a pitch. One question:

> Would you let me audit six months of your agent notices for free, if I only got
> paid on what I found?

A yes to that is a design partner, not a conversation. Every reply you get before
8pm goes into the "how far along" answer, and one real sentence from a real credit
ops person outweighs everything else in the application.

### 2. Buy a domain (5 min)
`altline.co` / `altline.ai` — ~$12. Fills the Company URL field.

### 3. Demo video (20 min)
```bash
cd ~/Projects/altops
python3 credit_corpus.py
python3 app.py                 # -> localhost:8000
```
**Check the badge top-right says `live · model + engine`** before recording. If it
reads `deterministic parser`, your provider key isn't loading — still demoable, but
live is the better story.

Script: `yc/VIDEO_SCRIPTS.md` §2. 90 seconds. The cross-check section at 0:32 is
your strongest 13 seconds — don't cut it for time.

### 4. Founder video (15 min, 3 takes max)
Script: `yc/VIDEO_SCRIPTS.md` §1. 60 seconds, hard cap.

Both videos → YouTube, **Unlisted** (not Private — Private links fail for the
partners and it's a common fatal mistake).

### 5. Fill the draft (40 min)
`yc/YC_APPLICATION_DRAFT.md`. **19 placeholders.** Search for `[` and kill every one.

The three that carry the most weight:
- **Most impressive thing** — PG calls this the single most important question.
  Needs one number and one mechanism. "42kg over 19 months, tracked 600 consecutive
  days" lands. "I got in great shape" doesn't.
- **Non-computer hack** — PG says a great answer here alone has earned interviews.
  Best candidate: how you got into GQ with no publicist. That's a closed system you
  opened.
- **Co-founder** — decide today. A clean "applying solo, here's why" beats a vague
  half-committed name.

### 6. Submit by 6:30pm, keep editing until 8:00pm

---

## Verify before you send

- [ ] Zero `[` brackets left in the submitted text
- [ ] Both YouTube links are **Unlisted** and open in a private window
- [ ] Every number you kept is one you can defend — the pricing ($8–15K/facility)
      and lender count are still my estimates, not verified. Either check them or
      soften them.
- [ ] The synthetic-corpus sentence is still in both the application and the demo
      video. **Do not cut it.** Volunteering your own weak spot is the cheapest
      credibility you will ever buy.
- [ ] You have not mentioned the RFS anywhere.

---

## Verified demo numbers (re-run `python3 facility.py` to confirm)

| | |
|---|---|
| findings | 10 across 10 notices |
| agent notices mispriced | 3 of 4 |
| interest wrong, one period | $5,453.47 |
| availability breach | $1,500,000 |
| facility | $275M, three tranches |

Specific findings, with sections:
- Margin 5.25% applied where §3.02 requires 5.75% at 5.20x → billed $73,721.38,
  recomputed $77,513.04
- Actual/365 where §3.01 specifies Actual/360
- CSA 0.00% where §3.01 specifies 0.15%
- 2-month Interest Period where §2.03 permits 1, 3 or 6
- $1,250,000 where §2.02 requires multiples of $500,000
- 1 business day notice where §2.02 requires 3
- $48M draw against $46.5M availability

---

## If a partner asks in the interview

**"How is this different from Hebbia?"**
> They produce a research answer — extract the covenant, benchmark it, cite it,
> LLM-mediated end to end. We produce a number. The model only reads; deterministic
> code does every calculation. And we check the administrative agent's math, a
> neutral party, not the borrower's own certificate.

**"How do you know your extraction is right?"**
> Two models read the agreement independently and we compare term by term. Where
> they disagree the term is quarantined out of the spec entirely and a human reads
> the clause. We don't average and we don't majority-vote — guessing between two
> disagreeing extractions is still guessing.

**"You don't own the data — how do you get benchmark rights?"**
> Opt-in, aggregated, anonymized, in customer agreement number one, with benchmark
> access as the consideration. Burgiss cleared exactly this bar on LP data. Get it
> wrong in the first contract and it never happens.

**"Isn't this just a services business?"**
> Checking the math is computation, so it carries software margins. Doing the
> servicing — wires, settlements, cash recs — is judgment, and that's the business
> Alter Domus runs at 20–35% by hiring people. Customers will ask us to take it on.
> That's the line I'm not crossing.

**"Why only private credit?"**
> The general form is a compiler for negotiated contracts — LPAs, leases,
> reinsurance treaties, freight invoices. I'm not building that yet. Private credit
> is first because I have the domain access, the buyer has budget, and the answer is
> unambiguously computable, so we can be provably right rather than plausibly
> helpful.
