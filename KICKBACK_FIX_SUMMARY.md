# Kickback Simulation Bug Fix - Summary

## The Bug

The lookahead agent simulation wasn't handling Kickback's special push mechanic, causing it to:
- Evaluate Kickback as **only 2 points** (the center score)
- Miss the **exit card push** that happens during Kickback's effect
- Underestimate Kickback's value by **60%** (2 points vs actual 5)

### Why This Happened

In the real game engine (engine.py), Kickback's effect:
1. Scores 2 points
2. Sets `metadata["kickback_pushed_card"]` to mark which card to push
3. **After** the effect returns, the engine handles the push and triggers exit effects

But in the lookahead simulation (_simulate_action), it:
1. Estimated center score → 2 points for Kickback ✓
2. **Stopped there** ✗
3. Never handled the special push that happens mid-trigger

The simulation only handled **regular pushes** (when a 4th card is added to a 3-card row), not **Kickback's mid-trigger push**.

---

## The Fix

Added Kickback-specific handling in `lookahead_agent.py` after center trigger evaluation:

```python
# Handle Kickback's special push mechanic
if center.card.name == "Kickback":
    # Determine push direction using greedy's logic
    direction = self.greedy.choose_effect_option(...)

    # Find which card gets pushed
    if direction == Side.LEFT:
        kickback_pushed = player.row[0]
    else:
        kickback_pushed = player.row[-1]

    # Evaluate exit effect
    if kickback_pushed.face_up and kickback_pushed.card.card_type == CardType.EXIT:
        exit_score = self.greedy._estimate_exit_score(...)
        player.score += int(exit_score)

    # Remove pushed card from row
    player.row.remove(kickback_pushed)
```

Now the simulation correctly:
1. Scores 2 points (center)
2. Simulates the push direction choice
3. Adds exit effect score (typically 3)
4. Updates the row state

**Total evaluation: 5 points instead of 2**

---

## Impact

### Before Fix:
```
Win rate:     26.9% (worst card in game, 26th/26)
Appearances:  386 games
Triggers:     0.02 per game (essentially never)
Agent choice: Actively avoided
```

### After Fix:
```
Win rate:     48.8% (middle tier, 13th/26)
Appearances:  337 games
Triggers:     6.61 per game
Trigger rate: 545% (multiple triggers per placement!)
Agent choice: Strategically used
```

### Detailed Trigger Analysis (200 games):

```
Games with Kickback:  118 (59%)
Total triggers:       780
Avg triggers/game:    6.61
Max triggers/game:    18
```

**Trigger Distribution:**
- 0 triggers: 15.3% of games
- 1-4 triggers: 24.5% of games
- **5+ triggers: 60.2% of games** ← Consecutive trigger mechanic working!

**Win rate when played: 42.4%** (close to expected 50%)

---

## What This Reveals About Kickback

### The Consecutive Trigger Mechanic Works!

When agents properly evaluate Kickback, they:
1. Play it and get it into center position
2. After it triggers and drops to 2 cards: `[Card A, Kickback]`
3. **Play another exit card** → `[Card A, Kickback, Exit Card]`
4. **Kickback triggers again** → 2 pts + exit (3 pts) = 5 pts
5. Repeat steps 3-4 multiple times

The **545% trigger rate** means Kickback triggers ~5.5 times per placement on average!

### Why It's Still Below Average (48.8% vs 50%)

While the mechanic works, Kickback has strategic downsides:
1. **Requires exit cards** - Without them, it only scores 2 points
2. **Vulnerable state** - The 2-card state can be disrupted
3. **Positioning challenge** - Must maintain Kickback in center
4. **Opportunity cost** - Could play other cards that score 3-4 immediately

So it's powerful when the combo works (6+ triggers), but:
- Needs the right cards in hand
- Requires multiple turns to pay off
- Can be disrupted by opponent actions

**This is good game design!** A high-risk, high-reward card that:
- Has powerful upside (18 trigger maximum!)
- Requires setup and maintenance
- Performs reasonably but not dominantly

---

## Key Takeaways

1. **Simulation bugs can completely hide card mechanics**
   - Before: Card appeared useless (26.9% win rate)
   - After: Card works as designed (48.8% win rate)
   - The mechanic was always there, agents just couldn't "see" it

2. **Agent evaluation is only as good as the simulation**
   - Lookahead agents make smart decisions based on what they simulate
   - If simulation is wrong, decisions will be wrong
   - Not "AI being dumb" - simulation being incomplete

3. **The consecutive trigger mechanic is powerful**
   - 5+ triggers in 60% of games
   - Maximum 18 triggers observed
   - Average 6.61 triggers per game when played

4. **Balance is sensitive to evaluation accuracy**
   - One missing piece of simulation: 22% win rate swing
   - Small bugs can make cards appear much worse than they are
   - Always verify agents can "see" special mechanics

---

## Files Modified

- `agents/lookahead_agent.py`: Added Kickback push simulation
- `analyze_kickback_gameplay.py`: Track triggers during gameplay (not just final state)

## Testing

Run tests to verify:
```bash
# Quick decision test
python test_kickback_choice.py

# Full trigger analysis
python analyze_kickback_gameplay.py

# Balance comparison
python main.py simulate --agent0 lookahead:3 --agent1 lookahead:3 --games 1000
```
