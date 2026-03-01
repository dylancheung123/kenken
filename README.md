# KenKen

A terminal-based [KenKen](https://en.wikipedia.org/wiki/KenKen) puzzle game built with Python and curses. Define puzzles in JSON, solve them in a clean TUI, and ask Claude for hints when you're stuck.

<img width="551" height="533" alt="Screenshot 2026-02-24 at 12 00 03 PM" src="https://github.com/user-attachments/assets/f544d4dd-f11d-4012-89a9-c5fe11b29c41" />


![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![No Dependencies](https://img.shields.io/badge/dependencies-none-green)

## Features

- Interactive curses TUI with cage borders, labels, and conflict highlighting
- Puzzles defined in JSON with chess-style coordinates (A1 = bottom-left)
- Real-time validation — row/column duplicates highlighted in red
- Auto-save — progress is saved automatically and restored on relaunch
- Built-in Claude chat — press `c` to ask for hints without leaving the game
- Responsive layout — centers in the terminal and adapts to resizing
- No external dependencies — pure Python stdlib

## Getting Started

```bash
python3 kenken.py sample_4x4.json
```

### Controls

| Key | Action |
|-----|--------|
| `←→↑↓` | Move cursor |
| `1`-`N` | Place number (N = grid size) |
| `0` / `Del` | Clear cell |
| `r` | Reset board |
| `c` | Chat with Claude for hints |
| `q` | Quit |

## Puzzle Format

Puzzles are JSON files with chess-style coordinates (columns = A-I, rows = 1-9, A1 = bottom-left):

```json
{
  "size": 4,
  "cages": [
    {"cells": ["A4", "A3"], "op": "+", "target": 5},
    {"cells": ["B4", "C4", "C3"], "op": "*", "target": 12},
    {"cells": ["D4"], "target": 2},
    {"cells": ["B3", "B2", "B1"], "op": "+", "target": 7},
    {"cells": ["A2", "A1"], "op": "-", "target": 1},
    {"cells": ["C2", "C1"], "op": "+", "target": 5},
    {"cells": ["D3", "D2", "D1"], "op": "+", "target": 8}
  ]
}
```

- **size**: Grid dimension (2-9)
- **cells**: List of cell coordinates (`A1` = bottom-left)
- **op**: `+`, `-`, `*`, `/` (omit for single-cell cages)
- **target**: The number the cage operation must produce
- `-` and `/` require exactly 2 cells

## Chat with Claude

Press `c` during gameplay to ask Claude for hints. This uses the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (`claude -p`) for authentication — no API key setup needed if you already have Claude Code installed.

The chat runs in the background so you can keep playing while waiting for a response. Claude sees your full board state and gives hints without spoiling the solution.

## Project Structure

```
kenken.py       # Entry point — argparse, loads JSON, launches curses
puzzle.py       # Puzzle loading, coordinate parsing, validation
game.py         # Game state, input handling, validation, win check
renderer.py     # Curses TUI rendering — grid, borders, colors
chat.py         # Claude integration for in-game hints
```
