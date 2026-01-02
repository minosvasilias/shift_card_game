# Balance Analysis Comparison

Comparing **Greedy vs Greedy (50k games)** baseline against **Lookahead:3 vs Lookahead:3 (100k games)** with stronger agents.

## First Player Advantage

| Metric | Greedy vs Greedy | Lookahead:3 vs Lookahead:3 | Change |
|--------|------------------|----------------------------|--------|
| **First Player Win Rate** | 58.0% (+8%) | **59.7% (+9.7%)** | **+1.7%** |

**Analysis:** First player advantage **INCREASED** with stronger agents. Smarter play makes going first even more valuable. This reinforces the HIGH priority recommendation to address first-player advantage.

---

## Card Performance Comparison

### Embargo - Still Dominant
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 87.7% | 2,639 |
| **Lookahead:3** | **88.4%** | **5,326** |

**Status:** ⚠️ **WORSE** - Even more dominant with smart agents, AND appears twice as often!
**Priority:** HIGH - Needs nerf

---

### Loner Bot - Strong But More Balanced
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 62.3% | 25,427 |
| **Lookahead:3** | **58.2%** | **55,897** |

**Status:** ✅ **IMPROVED** - Win rate dropped 4% with smarter opponents who can better contest icon isolation
**Priority:** Medium - Monitor, but much better

---

### Echo Chamber - Consistent
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 60.6% | 35,827 |
| **Lookahead:3** | **61.4%** | **82,869** |

**Status:** ⚠️ Consistent strength, very high appearances
**Priority:** Low - Working as intended (high-value common card)

---

### Magnet - CRITICALLY WEAK
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 24.6% | 2,674 |
| **Lookahead:3** | **21.4%** | **3,953** |

**Status:** 🚨 **WORSE** - Even weaker with smart agents!
**Priority:** CRITICAL - Major buff needed

---

### Patience Circuit - Still Terrible
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 31.8% | 224 |
| **Lookahead:3** | **19.9%** | **405** |

**Status:** 🚨 **MUCH WORSE** - 12% drop! Smart agents avoid it even more
**Priority:** CRITICAL - Rework needed

---

### Kickback - Disaster with Smart Agents
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 39.2% | ~20k |
| **Lookahead:3** | **27.8%** | **39,925** |

**Status:** 🚨 **CATASTROPHIC** - 11% drop! Smart agents recognize it hurts more than helps
**Priority:** CRITICAL - The push mechanic is fundamentally flawed

---

### One-Shot - Unexpectedly Better
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | 34.0% | 336 |
| **Lookahead:3** | **48.2%** | **428** |

**Status:** ✅ **MUCH IMPROVED** - Smart agents can leverage the 5-point burst better
**Priority:** Low - Appears balanced now

---

### Mimic - Surprise Winner
| Agent | Win Rate | Appearances |
|-------|----------|-------------|
| Greedy | ~46% (estimated) | ~4.5k |
| **Lookahead:3** | **56.5%** | **8,996** |

**Status:** ✅ Smart agents position it better to copy high-value adjacents
**Priority:** Low - Now performing well

---

## Trap Performance

| Trap | Greedy WR | Lookahead:3 WR | Change | Status |
|------|-----------|----------------|--------|--------|
| **Tripwire** | 49.4% | 50.2% | +0.8% | ✅ Balanced |
| **Mirror Trap** | 47.5% | 48.1% | +0.6% | ✅ Slightly better |
| **Snare** | 41.7% | 43.9% | +2.2% | ⚠️ Still weak |
| **False Flag** | 38.8% | 45.3% | +6.5% | ✅ Much improved! |

**False Flag** improved significantly - smart agents can predict and exploit market draws better.
**Snare** still weak - icon-matching trigger is too narrow.

---

## Biggest Changes (Win Rate Delta)

### Cards That Improved Most:
1. **One-Shot**: +14.2% (34.0% → 48.2%)
2. **Mimic**: ~+10% (estimated)
3. **False Flag**: +6.5% (38.8% → 45.3%)

### Cards That Got Worse:
1. **Patience Circuit**: -11.9% (31.8% → 19.9%) 🚨
2. **Kickback**: -11.4% (39.2% → 27.8%) 🚨
3. **Loner Bot**: -4.1% (62.3% → 58.2%) ✅

---

## Updated Priority Recommendations

### 🚨 CRITICAL (Game-Breaking):
1. **Kickback (27.8%)** - Fundamentally broken mechanic. The push hurts the player using it.
   - Suggestion: Let player CHOOSE whether to push, or push opponent's card instead
2. **Magnet (21.4%)** - Worse with smart agents. Effect is counterproductive.
   - Suggestion: Increase to 2 points, simplify effect
3. **Patience Circuit (19.9%)** - Actively avoided by smart agents.
   - Suggestion: Add immediate score: "Score 2. At game end, score +1 per turn elapsed"

### ⚠️ HIGH (Balance Issues):
4. **Embargo (88.4%, 5326 appearances)** - Dominance increased with smart agents
   - Suggestion: Both players locked, OR reduce to "opponent can't draw from market next turn"
5. **First Player Advantage (+9.7%)** - Worse with smart agents
   - Suggestion: Player 2 starts with 1 point, or sees market before P1 draws

### 📊 MEDIUM (Needs Monitoring):
6. **Snare (43.9%)** - Still too weak despite improvement
   - Suggestion: Trigger on any opponent card play, not just icon match
7. **Boomerang (32.6%)** - Still weak
   - Suggestion: Add exit score: "Score 1. Return to hand"

### ✅ VALIDATED (Working as Intended):
- **One-Shot** - Now balanced with smart play (48.2%)
- **Mimic** - Smart positioning makes it strong (56.5%)
- **False Flag** - Much better with smart agents (45.3%)
- **Loner Bot** - More balanced against smart opponents (58.2%)

---

## Key Insights

1. **First-player advantage gets WORSE with better play** - This is a fundamental game design issue
2. **Cards with delayed payoffs (Patience Circuit) are trap options** - Never worth playing
3. **Cards that push from your own row (Kickback) are actively harmful** - Players recognize this
4. **Positioning-dependent cards (Mimic) improve with smarter agents** - Good strategic depth
5. **Embargo remains broken** - Even stronger with smart agents, appears more often

## Conclusion

The lookahead:3 agent reveals that **three cards are critically broken** (Kickback, Magnet, Patience Circuit) and should be reworked before any other balance changes. The first-player advantage is also a more serious problem than initially apparent.

Some cards that appeared weak with greedy agents (One-Shot, False Flag, Mimic) are actually fine - they just require smart play to leverage effectively.
