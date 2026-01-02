# Robot Assembly Line - Playtesting Simulator

Automated playtesting for the Robot Assembly Line card game with both CLI simulations and an interactive web UI.

## Quick Start - Play the Game!

### Web UI (Recommended)

Run the game with a beautiful React frontend:

```bash
./start_game_ui.sh
```

Then open http://localhost:3000 in your browser.

### Terminal UI

Run the interactive terminal game:

```bash
./play_interactive.sh
```

## Setup

### Backend

```bash
pip install -r requirements.txt
```

### Frontend (for web UI)

```bash
cd frontend
npm install
cd ..
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

## Interactive Modes

### Web UI

The React frontend features:
- Beautiful card designs with unique colors
- Smooth animations for all game events
- Expandable game log tracking all actions
- Intuitive click-to-play interface
- Real-time score updates
- Visual feedback for card selection

Start it with `./start_game_ui.sh` or manually:

```bash
# Terminal 1: Backend
python3 -m uvicorn api.server:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Terminal UI

A text-based interactive mode is also available with `./play_interactive.sh`

## Agent types

- `random` - Makes valid random moves
- `greedy` - Picks highest immediate value move
- `lookahead` - Minimax with lookahead (available in interactive mode)
