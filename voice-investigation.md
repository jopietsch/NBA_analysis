# Voice investigation: how to get engaging-but-not-filler prose

A note to myself, written after editing `home_court_findings.md` and noticing the
docs come out clean but dry. The question: my rules, hooks, and skills are all
about removing frustrating LLM filler, but I don't want the result to be
lifeless. How do I structure things to get the voice I actually want?

## The root problem: the voice system is entirely subtractive

Every mechanism only knows how to *remove*:

- **The hook** (`.claude/hooks/voice_check.py`) flags jargon and em-dashes. Pure deletion.
- **The CLAUDE.md rules** are "No em-dashes," "No drama," "Don't overstate," "Write like a person" (itself a list of *Avoid*).
- **The skill** (`voice-review.md`) catches drama, filler, generated-sounding prose, overstatement. All presence-of-bad-things.

There is a floor but no ceiling pull. The system can detect and punish bad prose;
nothing in it detects or rewards *flat* prose. So the safe equilibrium for any
writer optimizing against it (me included) is spare, declarative, lifeless:
technically clean, scores zero violations, and dry. That is exactly what felt off
on the findings doc.

The engaging seeds *do* already exist in the rules: "sports-magazine editor,"
"vary sentence length," "short sentences land findings," "concrete not abstract."
But they are (a) buried inside *Avoid* sections, (b) framed as defect-fixes rather
than techniques to reach for, and (c) unenforced, while the prohibitions get a
hook *and* a skill *and* rules. That asymmetry is the whole issue.

## The principle: match each mechanism to the judgment it can actually make

This decides *where* each kind of rule belongs, and it is why bolting "be
engaging" onto the wrong layer would backfire.

- **The hook** can only do mechanical, unambiguous, high-precision removals.
  Engagement is a judgment call; a regex for it would throw false positives that
  train me to ignore the hook. Leave the hook exactly as it is: purely
  subtractive, narrow. Resist any urge to make it judge liveliness.
- **CLAUDE.md** shapes *generation*, ambient and always-on. This is where the
  *balance* has to be stated, because the dryness happens at write time, not
  review time.
- **The skill** is the on-demand judgment pass. It is the only place that can flag
  *over-correction*, and that is the highest-leverage gap.

## Three (four) concrete changes

**1. In CLAUDE.md: state the target as a tension with two failure modes, not a
list of don'ts.** Add a short framing block above the voice rules. Right now only
one failure mode is named (purple / filler / dramatic). Name both:

> The target is a clear, lively magazine feature. Two ways to miss it:
> **inflated** (filler, drama, jargon) and **flat** (every sentence the same
> length, findings stated with no concrete detail, an opening that defines
> instead of hooks). The prohibitions below remove inflation. They are not a
> license for flatness. If cutting a filler word also kills the pace, recast,
> don't just delete.

**2. In CLAUDE.md: add a "Reach for" section, positive and parallel to the
"Avoid" lists.** Additive moves that are engaging *and* not filler, several of
which the docs already use:

- Open with the hook, not the definition (the fix made to the findings intro).
- One short sentence to land a finding after a longer one that sets it up.
- A concrete named example over a general statement (Denver's altitude; the
  empty-arena 2020-21 test).
- Rhetorical structure that aids comprehension: the "what is NOT behind it"
  device, the Yes/No bullets.
- First person where it's honest ("I ran a tighter test and found...").

**3. Give "filler vs. texture" a discriminator**, because that ambiguity is what
makes the rules feel anti-engagement. The test is *not* "is this word strictly
necessary" (that yields dryness). It is: **does removing it lose meaning, pace,
or clarity?** "It is worth noting that" loses nothing, so cut it. A short punchy
sentence isn't strictly necessary but carries pace, so keep it.

**4. (Highest leverage) In the voice-review skill: add a symmetric "too dry"
check.** Today the review only flags bad things present. Add a category that flags
*life absent*:

- a section that states findings with no concrete number or example,
- monotone rhythm (roughly every sentence the same length),
- an opening that's a definition rather than a hook,
- a stretch where every sentence is short-declarative subject-verb.

This is what lets the review push *back toward* engagement instead of only sanding
prose down. Right now a maximally dry doc passes voice-review clean. It shouldn't.

## What not to do

Don't split this into more hooks, and don't try to auto-detect engagement. The
leverage is in the two judgment layers (CLAUDE.md + skill), not in more
automation. The hook is correct; keep it dumb.

## One-line summary

A strong floor is built (no filler, no jargon, no drama). What's missing is a
ceiling pull (lively, vivid, well-paced) and a review that enforces *both*
directions, so prose stops settling on the floor.

## Next step when I pick this up

Draft the actual edits: the tension-framing block and the "Reach for" section in
`questions/CLAUDE.md`, the filler-vs-texture discriminator, and the "too dry"
category in `voice-review.md`. Leave `voice_check.py` untouched.
