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

# Lookahead agent (depth 2) vs greedy
python3 main.py simulate --games 500 -a0 lookahead -a1 greedy

# Lookahead with custom depth (depth 3)
python3 main.py simulate --games 500 -a0 lookahead:3 -a1 greedy

# With specific seed for reproducibility
python3 main.py simulate --games 1000 --seed 42
```

### Watch a demo game

```bash
# Random vs random with delays
python3 main.py demo

# Greedy vs greedy, instant
python3 main.py demo -a0 greedy -a1 greedy --no-delay

# Lookahead vs greedy
python3 main.py demo -a0 lookahead -a1 greedy --no-delay

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
- `lookahead` or `lookahead:N` - Minimax search agent that looks ahead N turns (default: 2)

## Interactive Mode

Play against AI opponents via a REST API:

```bash
# Start the API server
uvicorn api.server:app --reload

# Visit http://localhost:8000/docs for interactive API documentation
```

### API Endpoints

- `POST /game` - Create a new game (choose opponent: random, greedy, or lookahead)
- `GET /game/{game_id}` - Get current game state
- `POST /game/{game_id}/action` - Submit a play action (which card, which side)
- `POST /game/{game_id}/draw` - Submit a draw choice (deck or market)
- `POST /game/{game_id}/effect` - Submit an effect choice (for cards like Swap Bot)
- `DELETE /game/{game_id}` - End a game

### Example: Create and Play a Game

```bash
# Create a game against greedy AI
curl -X POST http://localhost:8000/game \
  -H "Content-Type: application/json" \
  -d '{"opponent": "greedy", "seed": 42}'

# Submit a play action (play card at hand index 0 to the left side)
curl -X POST http://localhost:8000/game/{game_id}/action \
  -H "Content-Type: application/json" \
  -d '{"hand_index": 0, "side": "LEFT", "face_down": false}'

# Draw from the deck
curl -X POST http://localhost:8000/game/{game_id}/draw \
  -H "Content-Type: application/json" \
  -d '{"source": "DECK"}'
```
