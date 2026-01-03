# Balance Analysis & Improvement Notes

Based on 50,000 greedy vs greedy simulations.

## Key Findings

### First Player Advantage: 58% win rate (+8%)
This is significant. Consider:
- Second player compensation (e.g., start with 1 point, or see market before P1)
- Alternating first player across rounds in a match

---

## Cards Needing Attention

### Overperforming (>60% win rate)

**Embargo (87.7% win rate, 2639 appearances)**
- Locking the market for a turn is extremely powerful
- Only scores 1 point but the tempo advantage is massive
- Consider: Reduce lock duration, or make it symmetric (both players locked)

**Loner Bot (62.3% win rate, 25427 appearances)**
- 4 points for icon isolation is easy to achieve
- Greedy agent can plan around adjacency well
- Consider: Reduce to 3 points, or require NO adjacent cards share icons with each other

**Echo Chamber (60.6% win rate, 35827 appearances)**
- Scores 4 on even turns, 0 on odd - averages to 2/trigger
- Very common in final rows (35k appearances)
- Probably fine - high appearance rate dilutes impact

### Underperforming (<40% win rate)

**Magnet (24.6% win rate, 2674 appearances)**
- Pulling from market into row is complex and rarely beneficial
- Only scores 1 point
- The push-out mechanic may be confusing or counterproductive
- Consider: Simplify effect or increase base score to 2

**Patience Circuit (31.8% win rate, 224 appearances)**
- Delayed scoring rarely pays off
- Greedy agent doesn't value future points
- Low appearances suggest it's actively avoided
- Consider: Add immediate score (e.g., "Score 1. At end of game, score turns elapsed")

**Scavenger (32.7% win rate, 165 appearances)**
- Looking at face-down cards provides little value
- Swap ability is situational
- Very low appearances - actively avoided
- Consider: Add point value, or let it look at deck top cards

**One-Shot (34.0% win rate, 336 appearances)**
- 5 points but removes itself from game
- Net negative because you lose a card permanently
- Consider: Increase to 6-7 points to compensate for card loss

**Boomerang (34.9% win rate, 839 appearances)**
- Returns to hand on exit, can't play next turn
- The cooldown makes it clunky
- Consider: Remove cooldown, or add exit score (e.g., "Score 1. Return to hand")

### Traps Analysis

| Trap | Win Rate | Notes |
|------|----------|-------|
| Tripwire | 49.4% | Balanced - cancels opponent score |
| Mirror Trap | 47.5% | Slightly weak - copies opponent score |
| Snare | 41.7% | Weak - too situational (icon match) |
| False Flag | 38.8% | Weak - stealing market draws is niche |

**Snare** trigger condition (opponent plays same icon as your center) is too narrow.
Consider: Trigger on any card play, not just icon match.

**False Flag** rarely triggers because market draws are infrequent.
Consider: Also trigger on deck draws, or change effect entirely.

---

## Mechanical Observations

### Cards That Rarely Appear in Final Rows
Low appearance count suggests cards are:
1. Being pushed out quickly
2. Removed from game (One-Shot)
3. Actively avoided by greedy agent

| Card | Appearances | Reason |
|------|-------------|--------|
| Scavenger | 165 | 0 points, avoided |
| Patience Circuit | 224 | Delayed payoff, avoided |
| One-Shot | 336 | Self-removes |
| Spite Module | 405 | Exit card, pushed out |
| Rewinder | 458 | Exit card, pushed out |

### Kickback Underperformance (39.2%)
Despite scoring 2 points + pushing a card out, it underperforms.
Hypothesis: The push effect often removes valuable cards from your own row.
Consider: Let player choose whether to push or not.

### Donation Bot Negative Impact (38.4%)
Giving opponent a card hurts more than any strategic benefit.
This might be intentional (it's a "gift" that fills their hand).
Consider: This may be working as designed - a risky card.

---

## Recommendations Priority

1. **High**: Fix Magnet (24.6%) - significantly underpowered
2. **High**: Address first-player advantage (+8%)
3. **Medium**: Buff Patience Circuit, Scavenger, One-Shot
4. **Medium**: Rework or buff Snare and False Flag triggers
5. **Low**: Consider Embargo nerf if it remains dominant
