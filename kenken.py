#!/usr/bin/env python3
"""KenKen CLI puzzle game — entry point."""

import argparse
import curses
import os
import sys
import threading

from puzzle import load_puzzle
from game import GameState
from renderer import Renderer, init_colors
from chat import ask_claude


def _get_chat_input(stdscr, renderer, won):
    """Read a line of text from the user. Returns None if cancelled (Esc)."""
    prompt = "Ask Claude: "
    user_input = ""
    curses.curs_set(1)
    # Block on input while typing
    stdscr.timeout(-1)

    while True:
        renderer.draw_with_input(won, prompt, user_input)
        key = stdscr.getch()

        if key == 27:  # Escape — cancel
            curses.curs_set(0)
            return None
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            curses.curs_set(0)
            return user_input.strip() if user_input.strip() else None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            user_input = user_input[:-1]
        elif 32 <= key <= 126:
            user_input += chr(key)


def main_loop(stdscr, game: GameState):
    curses.curs_set(0)
    init_colors()
    # Enable mouse reporting so scroll arrives as KEY_MOUSE (not arrow keys)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    stdscr.keypad(True)

    renderer = Renderer(stdscr, game)
    renderer.check_terminal_size()

    won = game.is_won()
    renderer.draw(won)

    # Use timeout so screen refreshes to show async chat responses
    stdscr.timeout(200)

    # Only respond to these exact keys
    MOVE_KEYS = {
        curses.KEY_UP: (-1, 0),
        curses.KEY_DOWN: (1, 0),
        curses.KEY_LEFT: (0, -1),
        curses.KEY_RIGHT: (0, 1),
    }

    while True:
        key = stdscr.getch()
        if key == -1:  # timeout, no input — just redraw
            renderer.draw(won)
            continue
        if key == curses.KEY_MOUSE:  # discard scroll/mouse events
            continue

        if won:
            if key == ord("q") or key == ord("\n") or key == 27:
                break
            continue

        if key == ord("q"):
            break
        elif key in MOVE_KEYS:
            dr, dc = MOVE_KEYS[key]
            game.move_cursor(dr, dc)
        elif ord("1") <= key <= ord("0") + game.size:
            game.place_number(key - ord("0"))
        elif key == ord("0") or key == curses.KEY_DC or key == curses.KEY_BACKSPACE or key == 127:
            game.clear_cell()
        elif key == ord("r"):
            game.reset()
            renderer.clear_chat()
        elif key == ord("c"):
            question = _get_chat_input(stdscr, renderer, won)
            # Restore timeout for main loop
            stdscr.timeout(200)
            if question:
                renderer.set_chat_response("Thinking...")
                grid_snapshot = [row[:] for row in game.grid]
                # Capture in local vars for the closure
                q = question
                gs = grid_snapshot

                def _bg_ask(q=q, gs=gs):
                    response = ask_claude(game, q, gs)
                    renderer.set_chat_response(response)

                threading.Thread(target=_bg_ask, daemon=True).start()

        won = game.is_won()
        renderer.draw(won)


def main():
    parser = argparse.ArgumentParser(description="KenKen puzzle game")
    parser.add_argument("puzzle", help="Path to puzzle JSON file")
    args = parser.parse_args()

    try:
        size, cages = load_puzzle(args.puzzle)
    except (ValueError, FileNotFoundError, KeyError) as e:
        print("Error loading puzzle: %s" % e, file=sys.stderr)
        sys.exit(1)

    # Save file lives next to the puzzle file: puzzle.json -> puzzle.save.json
    base, ext = os.path.splitext(args.puzzle)
    save_path = base + ".save.json"

    game = GameState(size, cages, save_path=save_path)
    if game.load_save():
        print("Resuming saved game...", file=sys.stderr)

    try:
        curses.wrapper(lambda stdscr: main_loop(stdscr, game))
    except RuntimeError as e:
        print("Error: %s" % e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
