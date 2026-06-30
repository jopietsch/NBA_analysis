# Comparing Teams Across Eras: A Field Guide

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

You cannot put the 2025-26 Knicks and the 1986-87 Lakers on the same floor, so "best ever" is never a fact; it is an argument about method.
Comparing teams across decades comes down to two choices, and the ranking can flip depending on which you make.
Here is the toolkit, with the 2025-26 Knicks (the biggest raw playoff margin in 43 years) as the worked example.

## Two questions you have to answer

1. **How do you rate the opponents?** You cannot credit a team for a tough schedule until you have graded the teams it played.
2. **How do you put the eras on one scale?** A 12-point margin means one thing in a high-scoring, top-heavy league and another in a low-scoring, bunched-up one.

The first is about *who they beat*; the second is about *the world they did it in*.
They are independent, and a serious comparison settles both.

## Axis 1: how you rate opponents

| Method | Uses | Stresses | Knicks |
|---|---|---|---|
| **SRS** | margins + schedule | the baseline | 1st |
| **Bradley-Terry** | wins only | ignores blowouts entirely | 1st |
| **Capped-margin SRS** | margins clipped at ±15 | no single rout counts double | 1st |
| **Elo** | margins, recent games weighted more | late-season form | 3rd |

Three of the four make the Knicks #1.
Only Elo disagrees, because it credits their opponents for how well those teams were playing *late*.
The lesson: wins-only and blowout-capped ratings are how you rule out "their margins were just padding"; recency weighting is how you ask "but were their opponents tougher than their season record made them look?"

## Axis 2: how you put the eras on one scale

| Adjustment | Neutralizes | Knicks |
|---|---|---|
| Raw margin | nothing | 1st |
| Opponent-adjusted | strength of schedule | 1st |
| Scoring-share | total scoring (pace + shooting) | 1st |
| Per-100 possessions | pace only | 1st |
| **Spread-standardized** | how spread-out the league was | 5th |

The three era rows all grade the opponent-adjusted margin, the same basis as the Stats Explainer (§22).
On the raw margin instead, the scoring-share row drops the Knicks to 3rd; that is the one place the two bases disagree.

Two traps live here.
**Scoring-share** scales margins by points per game, which over-corrects: it treats a league's better shooting as if it were inflation.
**Per-100 possessions** divides by possessions instead, the cleaner fix, because it strips out pace without punishing efficiency.
But both only touch the *level* of scoring.
Neither touches the *spread* of team quality, which has nearly doubled since 1984 (the spread of team ratings rose from 3.1 to 5.90).
Measure a team by how far it stood above an average opponent in units of the league's spread, and a huge margin in today's top-heavy league counts for less than the same margin in a bunched one.

## The punchline: absolute vs. relative

Every *absolute* measure (biggest margin, schedule-adjusted margin, per-possession margin) makes the 2025-26 Knicks the most dominant champion on record.
Every *relative* measure makes them a top-five run: **5th** once graded against the league's spread (the 16–17 Warriors lead at +2.48 spread-widths above average, the Knicks at +1.90), and **3rd** once opponents get credit for recent form.
Both are honest.
They answer different questions:

- **"Who had the biggest edge in points?"** is an absolute question. The answer is the Knicks.
- **"Who was most exceptional for their own time?"** is a relative one. The answer is top five, not first.

## A rule of thumb

- To rule out a **padded margin**, switch the opponent rating to wins-only or blowout-capped. If #1 survives, the routs were not the story.
- To handle a **high-scoring era**, divide by possessions, not points: pace is the artifact, shooting is real basketball.
- To handle a **top-heavy era**, standardize by the league's spread. It is the adjustment most people skip, and the one that moves recent teams the most.
- When a claim says "best ever," ask which axis it used. If it cannot say, it has not compared eras; it has just picked the flattering number.

Built from the 2025-26 Knicks study: full method detail in the Stats Explainer (§15-§22 and "Comparing teams across eras"), full numbers in the Regression Results companion.
