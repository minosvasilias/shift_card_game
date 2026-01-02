# Shift Card Game - React Frontend

A beautiful, interactive frontend for the Shift Card Game built with React, TypeScript, and Framer Motion.

## Features

- **Intuitive UI**: Clean, modern interface with card-based gameplay
- **Smooth Animations**: Powered by Framer Motion for fluid card movements
- **Random Card Colors**: Each card has a unique color generated from its name
- **Game Log**: Expandable log to track all game events
- **Real-time Updates**: Instant feedback on game state changes
- **Responsive Design**: Works on desktop and tablet devices

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Make sure the backend API is running on port 8000

4. Open http://localhost:3000 in your browser

## Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Fast build tool
- **Framer Motion**: Animation library
- **Tailwind CSS**: Utility-first CSS

## Game Controls

1. Select a card from your hand by clicking on it
2. Choose LEFT or RIGHT to place the card
3. Click "Play Card" to execute your move
4. When prompted, draw from the DECK or select a card from the MARKET
5. Watch the game log for detailed event tracking

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── Card.tsx           # Card display component
│   │   ├── GameBoard.tsx      # Main game board
│   │   └── GameLog.tsx        # Event log component
│   ├── services/       # API client
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions (color generation)
│   ├── App.tsx         # Root component
│   └── main.tsx        # Entry point
├── package.json
└── vite.config.ts
```
