# Interactive Game API

This module provides a FastAPI-based interactive mode for playing the Shift card game.

## Features

- **RESTful API** for game management and player actions
- **Terminal client** for playing against AI opponents
- **Clean architecture** that reuses all existing game logic
- **Threaded game sessions** for concurrent games
- Support for multiple AI opponent types (random, greedy, lookahead)

## Quick Start

### Play via Terminal (One Command)

```bash
./play_interactive.sh
```

This script will:
1. Start the FastAPI server in the background
2. Launch the terminal client for you to play
3. Clean up and stop the server when you're done

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

3. In another terminal, run the client:
```bash
python api/client.py
```

## API Documentation

Once the server is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## Architecture

### Components

1. **InteractiveAgent** (`agents/interactive_agent.py`)
   - Implements the Agent interface
   - Uses queues to wait for external input via API
   - Blocks game execution until player makes a decision

2. **Session Manager** (`api/session_manager.py`)
   - Manages active game sessions
   - Runs each game in a background thread
   - Thread-safe state access with locks

3. **FastAPI Server** (`api/server.py`)
   - RESTful endpoints for game management
   - Serializes game state to JSON
   - Handles player actions, draws, and effect choices

4. **Terminal Client** (`api/client.py`)
   - HTTP client that communicates with the API
   - Terminal UI for displaying game state
   - Prompts for player input

### Game Flow

1. Client creates a new game via `POST /game`
2. Server creates a GameSession with InteractiveAgent + AI agent
3. Game runs in background thread
4. When it's the player's turn, InteractiveAgent blocks waiting for input
5. Client submits action via `POST /game/{id}/action`
6. InteractiveAgent receives action and game continues
7. Process repeats until game ends

## API Endpoints

- `POST /game` - Create a new game session
- `GET /game/{game_id}` - Get current game state
- `POST /game/{game_id}/action` - Submit a play action
- `POST /game/{game_id}/draw` - Submit a draw choice
- `POST /game/{game_id}/effect` - Submit an effect choice
- `DELETE /game/{game_id}` - End a game session

## Design Decisions

### Why Threading?

Threading allows us to reuse the existing GameEngine without modifications. The engine calls agent methods synchronously, and those calls block until the player makes a decision via the API.

Alternative approaches would require restructuring the game engine to be async or step-based, which would duplicate logic.

### Why Queue-Based InteractiveAgent?

The queue pattern allows the API to "push" decisions to the agent while the game thread "pulls" them. This decouples the HTTP request-response cycle from the game execution flow.

### Why Lock-Based State Access?

Game state is modified by the background thread but read by API endpoints. Locks ensure thread-safe access and prevent race conditions.
