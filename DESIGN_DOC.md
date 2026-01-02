# ROBOT ASSEMBLY LINE

*Board Game Design Document v0.2*

---

## OVERVIEW

A compact two-player card game about building and cycling robot assemblies. Players manage a row of up to three cards, pushing cards through to score points when they hit the center position. The game fits in a tiny box and emphasizes spatial positioning, timing, and tactical card play.

### Design Pillars

**Minimal components:** Cards only, with a small turn counter track. No tokens if avoidable.

**Positional play:** Card placement and relative positioning drive scoring and strategy.

**Cycling mechanic:** Cards flow through your row—enter from edges, score in center, exit to market.

**Hidden information:** Face-down trap cards create uncertainty and mind games.

---

## COMPONENTS

- Deck of cards (24–30 unique cards, each card appears once)
- Turn counter track (1–10) with shared marker
- Score tracking method (TBD)

---

## SETUP

1. Shuffle the deck and place it face-down as a draw pile.
2. Deal 2 cards to each player (hand limit: 2).
3. Fill the market to 3 cards from the top of the deck.
4. Both players start with empty rows.
5. Place turn counter marker on position 1.

---

## TURN STRUCTURE

On your turn, perform these steps in order:

1. **Play a card** from your hand to either edge of your row (left or right). Trap cards may be played face-down.

2. **Resolve push:** If your row now exceeds 3 cards, the card at the opposite edge is pushed out. Pushed cards trigger their exit effect (if any) before leaving.

3. **Market update:** Place the pushed-out card into the market (face-up). If market exceeds 3 cards, you must trash one card of your choice from the market (removed from game, face-down).

4. **Draw a card:** Take one card into your hand from either the market or the top of the deck.

5. **Refill market:** If market is below 3 cards, refill from deck until it reaches 3.

6. **Advance turn counter** by one position.

---

## CENTER SCORING

When a card enters the center position of your row (the slot with cards on both sides), its **center effect** triggers immediately.

**Center only exists with exactly 3 cards.** With 1–2 cards in your row, there is no center position and no center triggers occur.

Cards can score multiple times if they re-enter center through pushing mechanics.

If a card is removed from center by an effect (creating a gap), the gap fills naturally when the next card is pushed from either edge.

---

## EXIT SCORING

Some cards have **exit effects** instead of center effects. These trigger when the card is pushed out of your row.

Approximately 15–20% of cards should be exit-scorers. They offer flexibility and combo potential but don't contribute while in your row.

---

## TRAP CARDS

Trap cards are played face-down to an edge slot. While face-down:

**No icon:** They don't count for adjacency checks or icon-based effects.

**Hidden:** Opponent knows something is there but not what.

Each trap specifies a trigger condition. When that condition occurs, the trap flips face-up, resolves its effect, then remains in your row as a normal card (with icon, pushable, etc.).

**Failed traps:** If a trap is pushed out before triggering, it goes to the trash pile face-down (stays hidden). No effect occurs.

---

## ICONS

Four icon types appear on cards for adjacency conditions and effects:

| Icon | Thematic Association |
|------|---------------------|
| **Gear** | Mechanical, industrial, reliable workhorses |
| **Spark** | Energy, aggression, high-risk/high-reward |
| **Chip** | Logic, calculation, conditional effects |
| **Heart** | Social, synergy, mutual benefit, interaction |

---

## HAND LIMIT

**Hand limit is 2 cards.** The moment you receive a card that would exceed this limit (from any source), you must immediately discard one card to the trash pile.

This creates tension around effects that add cards to hand—receiving a "gift" might force you to discard something valuable.

---

## GAME END

The game ends when the turn counter reaches 10.

The player with the highest score wins. Tiebreaker: player with more cards remaining in their row.

---

## CARD LIST

All cards are unique—each appears exactly once in the deck.

### Center-Scoring Cards

| Name | Icon | Center Effect |
|------|------|---------------|
| Calibration Unit | Gear | Score 2 points. |
| Loner Bot | Chip | Score 4 if neither adjacent card shares an icon with this. Otherwise score 0. |
| Copycat | Gear | Score points equal to the lower of your two adjacent cards' last center-scores. |
| Siphon Drone | Spark | Score 3. Opponent also scores 2. |
| Jealous Unit | Heart | Score 2 per card in opponent's row that shares an icon with this card. |
| Sequence Bot | Chip | Score 3 if your row has exactly three different icons. Otherwise score 1. |
| Kickback | Spark | Score 2. Then push this card one slot toward either edge (your choice). |
| Patience Circuit | Chip | Note the current turn number. At end of game, score points equal to turns elapsed since this scored. |
| Turncoat | Heart | Score 2. Swap this card with one card in opponent's row (your choice). That card enters your row in this slot. |
| Void | None | Score 2 per empty slot across both rows. |
| Buddy System | Heart | Score 3 if there is exactly one other card in your row. Otherwise score 0. |
| Mimic | Chip | This card's icon becomes the icon of the card to its left until it leaves. Score 2. If the card to your left exits, this also exits. |
| Tug-of-War | Gear | Score 2. Opponent must push out one of their edge cards (their choice) if they have 3 cards. |
| Hollow Frame | Gear | Score 0. This card counts as having every icon for adjacency purposes. |
| Echo Chamber | Chip | Score 2. If the turn counter is even, trigger this effect again. |
| One-Shot | Spark | Score 5. Remove this card from the game entirely (not to market). |
| Embargo | Gear | Score 1. The market is locked until your next turn—no drafting or trashing. |
| Scavenger | Gear | Score 0. Look at all face-down cards in both rows. You may swap this with one of them. |
| Magnet | Spark | Score 1. Pull one card from the market into an adjacent slot. If occupied, that card is pushed out. |
| Hot Potato | Spark | Score 2. This card goes to opponent's hand. |

### Exit-Scoring Cards

| Name | Icon | Exit Effect |
|------|------|-------------|
| Farewell Unit | Heart | Score 3. |
| Spite Module | Chip | Opponent must push out one of their edge cards immediately (no center-score for it). |
| Boomerang | Spark | Return to your hand. You may not play this card next turn. |
| Donation Bot | Gear | Goes directly to opponent's hand instead of market. |
| Rewinder | Chip | Take one card from the market into your hand. This card goes to market as normal. |
| Sacrificial Lamb | Heart | Score 3. (Has no center effect—purely an exit card.) |

### Trap Cards

| Name | Icon | Trigger & Effect |
|------|------|------------------|
| Tripwire | Spark | **Trigger:** Opponent scores from a center effect. **Effect:** Their score is cancelled. You score 1. |
| False Flag | Chip | **Trigger:** Opponent takes a card from the market. **Effect:** That card goes to your hand instead. |
| Snare | Gear | **Trigger:** Opponent plays a card with the same icon as your center card. **Effect:** Their card goes to market instead of their row. |
| Mirror Trap | Heart | **Trigger:** Opponent's center card scores. **Effect:** You score the same amount. |

---

## OPEN QUESTIONS

1. **Turn count:** Starting with 10 turns. Will adjust based on playtesting.

2. **First-player advantage:** Needs testing. May require compensation mechanism.

3. **Trap frequency:** Are 4 trap cards enough to create uncertainty? Will revise based on play.

4. **Score tracking component:** To be designed later.
