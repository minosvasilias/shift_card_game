# Robot Assembly Line - Playtesting Simulator

Automated playtesting for the Robot Assembly Line card game.

## Setup

```bash
pip install -r requirements.txt
```

## Commands

### Run simulations

```bash
# 1000 games, random vs random
python3 main.py simulate --games 1000

# Greedy vs random (greedy dominates ~99%)
python3 main.py simulate --games 500 --agent0 greedy --agent1 random

# Greedy vs greedy
python3 main.py simulate --games 500 -a0 greedy -a1 greedy

# With specific seed for reproducibility
python3 main.py simulate --games 1000 --seed 42
```

### Watch a demo game

```bash
# Random vs random with delays
python3 main.py demo

# Greedy vs greedy, instant
python3 main.py demo -a0 greedy -a1 greedy --no-delay

# Specific seed, 5 turns
python3 main.py demo --seed 42 --turns 5
```

### Other

```bash
# List all cards
python3 main.py list-cards

# Quick test (validates engine works)
python3 main.py quick-test
```

## Agent types

- `random` - Makes valid random moves
- `greedy` - Picks highest immediate value move
