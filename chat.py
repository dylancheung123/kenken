"""Chat with Claude for KenKen hints, using the claude CLI for auth."""

import subprocess


def _build_board_description(game, grid_snapshot=None) -> str:
    """Build a text description of the current puzzle and board state."""
    size = game.size
    grid = grid_snapshot if grid_snapshot else game.grid
    lines = ["KenKen %dx%d puzzle." % (size, size)]
    lines.append("")
    lines.append("Cages:")
    for cage in game.cages:
        coords = []
        for r, c in cage.cells:
            col_letter = chr(ord("A") + c)
            row_num = size - r
            coords.append("%s%d" % (col_letter, row_num))
        if cage.op:
            lines.append("  %s: %d%s" % (", ".join(coords), cage.target, cage.op))
        else:
            lines.append("  %s: %d" % (", ".join(coords), cage.target))

    lines.append("")
    lines.append("Current board (0 = empty):")
    lines.append("     " + "  ".join(chr(ord("A") + c) for c in range(size)))
    for r in range(size):
        row_num = size - r
        vals = "  ".join(str(grid[r][c]) for c in range(size))
        lines.append("  %d  %s" % (row_num, vals))

    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are a helpful KenKen tutor. The user is playing a puzzle and may ask for hints, "
    "strategy advice, or help with specific cells. Give helpful hints without directly giving away the "
    "full solution. Guide them toward the answer. Be concise — your response will be shown in a small "
    "terminal area. Keep responses under 8 lines."
)


def ask_claude(game, user_message, grid_snapshot=None):
    """Send the current game state and user message to Claude via the claude CLI."""
    board_desc = _build_board_description(game, grid_snapshot)
    prompt = "%s\n\nHere is my current puzzle state:\n\n%s\n\nMy question: %s" % (
        SYSTEM_PROMPT, board_desc, user_message
    )

    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "haiku"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Error: %s" % (result.stderr.strip() or "claude CLI returned non-zero")
    except FileNotFoundError:
        return "Error: 'claude' CLI not found. Install Claude Code first."
    except subprocess.TimeoutExpired:
        return "Error: Request timed out."
    except Exception as e:
        return "Error: %s" % e
