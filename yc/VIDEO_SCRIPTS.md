# Video Scripts — shoot both, total 40 minutes

YC's own guidance: applicants who submit a founder video are **statistically much
more likely** to be interviewed. Highest return per minute of anything left.

Upload both to YouTube as **Unlisted** — not Private. Private links fail for the
partners and it is a common, fatal, stupid mistake.

---

## 1. FOUNDER VIDEO — 60 seconds, hard cap

**Setup:** phone at eye level, window in front of you, plain wall behind. Look at
the lens, not at yourself.

**Rule: 3 takes maximum.** Energy beats polish. A slightly rough take from someone
who obviously knows the domain reads as real. Take 19 reads as rehearsed.

### Beats, not words

**[0:00–0:10] Name and the sentence.**
> I'm Garvit. I'm an engineer and for the last [X] years I've automated operations
> inside alternative assets. I'm building Altline.

**[0:10–0:30] The insight, stated flatly.**
> A private credit agreement isn't a record, it's a specification. It says which
> interest periods are allowed, what margin applies at what leverage, what day-count
> convention to use. So every borrowing notice and every agent interest calculation
> that follows has a correct answer you could derive from the contract.
>
> Nobody derives it. At setup an operator reads a 300-page agreement and types the
> terms into an Excel template. After that the agent sends a number and everyone
> trusts it, because recomputing it by hand for every notice on every facility
> isn't a job you can staff.

**[0:30–0:48] What you built and what it found.**
> Altline compiles the agreement into a spec, then checks every notice against it.
> On our test facility three of four agent notices were mispriced — wrong margin
> tier, wrong day count, a missing credit spread adjustment. Five and a half
> thousand dollars of interest wrong in one period on one facility. Every finding
> cites the section that proves it.

**[0:48–1:00] Why you, then stop.**
> I've watched this from the inside, which is why I know the problem isn't
> extraction — it's that nobody recomputes.
>
> [ONE sentence of the personal thing, stated flatly, no inspirational framing.
> e.g. "I also went from clinically obese to lean over 19 months and got written up
> in GQ. I'm good at doing the boring correct thing for a very long time."]
> That's it. Thanks.

**Do not:** apologize, say "so basically", mention market size, or run over 60
seconds. End on a clean stop.

---

## 2. DEMO VIDEO — 90 seconds, screen recording

No face needed. Narrate over the screen. QuickTime or Loom.

**Before you record:**
```bash
cd ~/Projects/altops
python3 credit_corpus.py       # builds the agreement + notices
python3 app.py                 # -> localhost:8000
```
Confirm the badge top-right reads **live · model + engine** before you hit record.
If it says "deterministic parser" your provider key isn't loading — the demo still
works, but the live version is the better story.

Have two things open: `credit_corpus/CreditAgreement_Meridian_Packaging.pdf` and
the browser.

### Beat sheet

**[0:00–0:20] The agreement is a spec.** Open `CreditAgreement_Meridian_Packaging.pdf`.
Scroll to §3.02, the pricing grid.
> This is a credit agreement. Section 3.02 — applicable margin by leverage ratio.
> Section 3.01 — credit spread adjustment by interest period, and interest computed
> on a 360-day year. Section 2.03 — interest periods of one, three or six months only.
>
> Today an operator reads this once, types it into an Excel template, and it's never
> referenced again. Every notice after this is taken on trust.

**[0:20–0:32] Compile it.** Switch to the browser. Scroll to "Agreement, compiled."
> We compile it instead. Tranches, the four-tier pricing grid, permitted interest
> periods, credit spread adjustments, day count, minimum borrowing, notice days.
> Every term carries the section it came from.

**[0:32–0:45] The cross-check. Do not skip this — it's your best 13 seconds.**
Scroll up to "Extraction cross-check."
> Here's the part I care most about. The engine catches a wrong calculation. But a
> wrong *term* is invisible — if we misread the margin grid, every check below it is
> confidently wrong forever and looks exactly as authoritative as a correct one.
>
> So two different models read the agreement independently and we compare term by
> term. Where they agree, we proceed. Where they disagree, we quarantine the term —
> it's pulled out of the spec entirely and a human reads the clause. We don't average
> it and we don't majority-vote it. Guessing between two disagreeing extractions is
> still guessing.

**[0:45–1:12] The findings.**

Point at the agent notices:
> Now check the notice traffic against it. Three of four agent notices are mispriced.
>
> This one: the agent applied a 5.25% margin. At 5.20 times leverage the grid
> requires 5.75%. Billed seventy-three thousand seven twenty-one; recomputed
> seventy-seven five thirteen.
>
> This one computed interest on a 365-day year. The agreement says 360.
>
> And this one dropped the credit spread adjustment entirely — zero where the
> agreement says fifteen basis points.
>
> That's five and a half thousand dollars of interest wrong, in one period, on one
> facility.

Point at the borrowing notices:
> On the borrow side — a two-month interest period where the agreement permits only
> one, three or six. A request for one and a quarter million where amounts have to
> be in multiples of five hundred thousand. A SOFR borrowing noticed one business
> day out where three are required. And a forty-eight million dollar draw against
> forty-six and a half million of availability, once you net the letters of credit.

**[1:12–1:25] Why it's actionable.**
> Every finding shows the section and the arithmetic. That's deliberate — a credit
> ops lead won't act on a model saying "this looks wrong." They'll act on "section
> 3.02 requires 5.75% at this leverage, the agent applied 5.25%, here's the clause."
> This is a second opinion, not an automated payment.

**[1:25–1:30] The honest line. Do not skip it.**
> This agreement and these notices are synthetic — I wrote them to mirror structures
> I've worked with. Real credit agreements are confidential. Getting the first real
> one from a design partner is this week's job.

That sentence is worth more than the rest of the demo. It tells a partner you won't
inflate a number, which is what makes them willing to believe every number you give
them afterward.

---

## Recording order

Demo first — it loads the product language into your head. Then the founder video in
three takes. Upload both, set Unlisted, paste links, submit.
