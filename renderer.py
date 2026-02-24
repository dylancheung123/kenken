"""Curses TUI rendering for Mathdoku: borders, cage labels, colors, cursor."""

import curses
from game import GameState
from puzzle import Cage

CELL_WIDTH = 7
CELL_HEIGHT = 3

# Box-drawing characters indexed by (top, right, bottom, left) thickness
# 0 = none, 1 = thin, 2 = thick
_JUNCTION: dict[tuple[int, int, int, int], str] = {}


def _build_junction_table():
    """Build junction lookup from (top, right, bottom, left) -> character.
    Each direction is 0=none, 1=thin, 2=thick."""
    # Thick lines
    _JUNCTION[(0, 2, 2, 0)] = "┏"
    _JUNCTION[(0, 0, 2, 2)] = "┓"
    _JUNCTION[(2, 2, 0, 0)] = "┗"
    _JUNCTION[(2, 0, 0, 2)] = "┛"
    _JUNCTION[(2, 2, 2, 0)] = "┣"
    _JUNCTION[(2, 0, 2, 2)] = "┫"
    _JUNCTION[(0, 2, 2, 2)] = "┳"
    _JUNCTION[(2, 2, 0, 2)] = "┻"
    _JUNCTION[(2, 2, 2, 2)] = "╋"
    _JUNCTION[(0, 2, 0, 2)] = "━"
    _JUNCTION[(2, 0, 2, 0)] = "┃"

    # Thin lines
    _JUNCTION[(0, 1, 1, 0)] = "┌"
    _JUNCTION[(0, 0, 1, 1)] = "┐"
    _JUNCTION[(1, 1, 0, 0)] = "└"
    _JUNCTION[(1, 0, 0, 1)] = "┘"
    _JUNCTION[(1, 1, 1, 0)] = "├"
    _JUNCTION[(1, 0, 1, 1)] = "┤"
    _JUNCTION[(0, 1, 1, 1)] = "┬"
    _JUNCTION[(1, 1, 0, 1)] = "┴"
    _JUNCTION[(1, 1, 1, 1)] = "┼"
    _JUNCTION[(0, 1, 0, 1)] = "─"
    _JUNCTION[(1, 0, 1, 0)] = "│"

    # Mixed thick/thin — common cases
    _JUNCTION[(2, 1, 2, 1)] = "╂"
    _JUNCTION[(2, 1, 2, 0)] = "┠"
    _JUNCTION[(2, 0, 2, 1)] = "┨"
    _JUNCTION[(0, 1, 2, 1)] = "┰"
    _JUNCTION[(2, 1, 0, 1)] = "┸"

    _JUNCTION[(1, 2, 1, 2)] = "┿"
    _JUNCTION[(0, 2, 1, 2)] = "┯"
    _JUNCTION[(1, 2, 0, 2)] = "┷"
    _JUNCTION[(1, 2, 1, 0)] = "┝"
    _JUNCTION[(1, 0, 1, 2)] = "┥"

    _JUNCTION[(0, 2, 1, 0)] = "┎"
    _JUNCTION[(0, 1, 2, 0)] = "┍"
    _JUNCTION[(0, 0, 1, 2)] = "┒"
    _JUNCTION[(0, 0, 2, 1)] = "┑"
    _JUNCTION[(1, 2, 0, 0)] = "┕"
    _JUNCTION[(2, 1, 0, 0)] = "┖"
    _JUNCTION[(1, 0, 0, 2)] = "┙"
    _JUNCTION[(2, 0, 0, 1)] = "┚"

    _JUNCTION[(0, 2, 2, 1)] = "┲"
    _JUNCTION[(0, 1, 2, 2)] = "┱"
    _JUNCTION[(2, 2, 0, 1)] = "┺"
    _JUNCTION[(2, 1, 0, 2)] = "┹"
    _JUNCTION[(2, 2, 1, 0)] = "┢"
    _JUNCTION[(1, 2, 2, 0)] = "┡"
    _JUNCTION[(2, 0, 1, 2)] = "┪"
    _JUNCTION[(1, 0, 2, 2)] = "┩"

    _JUNCTION[(2, 1, 1, 0)] = "┞"
    _JUNCTION[(1, 1, 2, 0)] = "┟"
    _JUNCTION[(2, 0, 1, 1)] = "┦"
    _JUNCTION[(1, 0, 2, 1)] = "┧"

    _JUNCTION[(2, 2, 1, 2)] = "┻"
    _JUNCTION[(1, 2, 2, 2)] = "┳"
    _JUNCTION[(2, 2, 2, 1)] = "╊"
    _JUNCTION[(2, 1, 2, 2)] = "╉"
    _JUNCTION[(1, 2, 2, 1)] = "╅"
    _JUNCTION[(2, 1, 1, 2)] = "╃"
    _JUNCTION[(1, 1, 2, 2)] = "╆"
    _JUNCTION[(2, 2, 1, 1)] = "╄"
    _JUNCTION[(1, 2, 1, 1)] = "╀"
    _JUNCTION[(1, 1, 1, 2)] = "┽"

    # All 0/2 combinations (0 = no line, 2 = thick cage border)
    _JUNCTION[(0, 0, 0, 0)] = " "
    # One arm
    _JUNCTION[(0, 2, 0, 0)] = "╺"
    _JUNCTION[(0, 0, 0, 2)] = "╸"
    _JUNCTION[(0, 0, 2, 0)] = "╻"
    _JUNCTION[(2, 0, 0, 0)] = "╹"
    # Two arms (already defined: corners + straights)
    # ┏ ┓ ┗ ┛ ━ ┃ are already in the table
    # Three arms (already defined: ┣ ┫ ┳ ┻)
    # Four arms (already defined: ╋)

    # Mixed 0/2 with existing 1s — interior junctions where one cage
    # border meets a gap. Treat as the thick-only subset.
    _JUNCTION[(2, 2, 0, 0)] = "┗"
    _JUNCTION[(2, 0, 0, 2)] = "┛"
    _JUNCTION[(0, 2, 2, 0)] = "┏"
    _JUNCTION[(0, 0, 2, 2)] = "┓"
    _JUNCTION[(2, 2, 2, 0)] = "┣"
    _JUNCTION[(2, 0, 2, 2)] = "┫"
    _JUNCTION[(0, 2, 2, 2)] = "┳"
    _JUNCTION[(2, 2, 0, 2)] = "┻"
    _JUNCTION[(2, 2, 2, 2)] = "╋"
    _JUNCTION[(0, 2, 0, 2)] = "━"
    _JUNCTION[(2, 0, 2, 0)] = "┃"

    # Two thick + one or two zero
    _JUNCTION[(2, 0, 2, 0)] = "┃"
    _JUNCTION[(0, 2, 0, 2)] = "━"
    _JUNCTION[(2, 2, 0, 0)] = "┗"
    _JUNCTION[(0, 0, 2, 2)] = "┓"
    _JUNCTION[(0, 2, 2, 0)] = "┏"
    _JUNCTION[(2, 0, 0, 2)] = "┛"


_build_junction_table()

# Color pair IDs
COLOR_DEFAULT = 0
COLOR_LABEL = 1
COLOR_CORRECT = 2
COLOR_CONFLICT = 3
COLOR_CURSOR = 4
COLOR_WIN = 5
COLOR_CHAT = 6
COLOR_CAGE_BORDER = 7
COLOR_GRID_DIM = 8


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_LABEL, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_CORRECT, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_CONFLICT, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_CURSOR, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(COLOR_WIN, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(COLOR_CHAT, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_CAGE_BORDER, curses.COLOR_WHITE, -1)
    # 240 = dark gray in 256-color terminals; fall back to default if unavailable
    try:
        curses.init_pair(COLOR_GRID_DIM, 240, -1)
    except (curses.error, ValueError):
        curses.init_pair(COLOR_GRID_DIM, curses.COLOR_BLACK, -1)


class Renderer:
    def __init__(self, stdscr, game: GameState):
        self.stdscr = stdscr
        self.game = game
        self.size = game.size
        self.grid_width = self.size * (CELL_WIDTH + 1) + 1
        self.header_pad = 3
        self._update_offsets()
        self.offset_y = 2
        # Persistent chat response lines
        self.chat_lines = []
        # Precompute border thickness between adjacent cells
        self._h_border = self._compute_h_borders()
        self._v_border = self._compute_v_borders()

    def _update_offsets(self):
        max_y, max_x = self.stdscr.getmaxyx()
        self.offset_x = max(self.header_pad, (max_x - self.grid_width) // 2)
        self.offset_y = 2

    def _same_cage(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        return self.game.cell_cage.get((r1, c1)) is self.game.cell_cage.get((r2, c2))

    def _compute_h_borders(self) -> list[list[int]]:
        """Horizontal border: 2=cage/outer edge, 0=within cage (no line)."""
        n = self.size
        borders = []
        for r in range(n + 1):
            row = []
            for c in range(n):
                if r == 0 or r == n:
                    row.append(2)
                elif self._same_cage(r - 1, c, r, c):
                    row.append(0)
                else:
                    row.append(2)
            borders.append(row)
        return borders

    def _compute_v_borders(self) -> list[list[int]]:
        """Vertical border: 2=cage/outer edge, 0=within cage (no line)."""
        n = self.size
        borders = []
        for r in range(n):
            row = []
            for c in range(n + 1):
                if c == 0 or c == n:
                    row.append(2)
                elif self._same_cage(r, c - 1, r, c):
                    row.append(0)
                else:
                    row.append(2)
            borders.append(row)
        return borders

    def check_terminal_size(self):
        max_y, max_x = self.stdscr.getmaxyx()
        need_y = self.offset_y + self.size * CELL_HEIGHT + self.size + 1 + 4
        need_x = self.offset_x + self.size * CELL_WIDTH + self.size + 1
        if max_y < need_y or max_x < need_x:
            raise RuntimeError(
                "Terminal too small: need at least %dx%d, got %dx%d"
                % (need_x, need_y, max_x, max_y)
            )

    def _junction_char(self, r: int, c: int) -> str:
        n = self.size
        if r > 0:
            if c == 0 or c == n:
                top = 2
            else:
                top = self._v_border[r - 1][c]
        else:
            top = 0

        if r < n:
            if c == 0 or c == n:
                bottom = 2
            else:
                bottom = self._v_border[r][c]
        else:
            bottom = 0

        if c > 0:
            if r == 0 or r == n:
                left = 2
            else:
                left = self._h_border[r][c - 1]
        else:
            left = 0

        if c < n:
            if r == 0 or r == n:
                right = 2
            else:
                right = self._h_border[r][c]
        else:
            right = 0

        # Normalize: non-zero becomes 1 for thin junction lookup
        top = 1 if top else 0
        right = 1 if right else 0
        bottom = 1 if bottom else 0
        left = 1 if left else 0

        key = (top, right, bottom, left)
        return _JUNCTION.get(key, " ")

    def _get_junction_thickness(self, r: int, c: int) -> int:
        """Return max thickness of any arm at this junction. 2=has cage border, 1=thin only."""
        n = self.size
        vals = []
        if r > 0:
            vals.append(2 if (c == 0 or c == n) else self._v_border[r - 1][c])
        if r < n:
            vals.append(2 if (c == 0 or c == n) else self._v_border[r][c])
        if c > 0:
            vals.append(2 if (r == 0 or r == n) else self._h_border[r][c - 1])
        if c < n:
            vals.append(2 if (r == 0 or r == n) else self._h_border[r][c])
        return max(vals) if vals else 0

    def _draw_grid(self):
        n = self.size
        oy, ox = self.offset_y, self.offset_x

        for c in range(n):
            x = ox + 1 + c * (CELL_WIDTH + 1) + CELL_WIDTH // 2
            self.stdscr.addstr(oy - 1, x, chr(ord("A") + c))

        dim_attr = curses.color_pair(COLOR_GRID_DIM)
        border_attr = curses.color_pair(COLOR_CAGE_BORDER)

        # Layer 1: dotted background grid
        # Horizontal dot rows at cell borders
        for r in range(n + 1):
            y = oy + r * (CELL_HEIGHT + 1)
            for c in range(n):
                x = ox + c * (CELL_WIDTH + 1)
                seg = "- " * ((CELL_WIDTH + 1) // 2)
                try:
                    self.stdscr.addstr(y, x, seg[:CELL_WIDTH + 1], dim_attr)
                except curses.error:
                    pass

        # Vertical dot columns at cell borders (every row, not just border rows)
        grid_top = oy
        grid_bottom = oy + n * (CELL_HEIGHT + 1)
        for y in range(grid_top, grid_bottom + 1):
            for c in range(n + 1):
                x = ox + c * (CELL_WIDTH + 1)
                try:
                    self.stdscr.addstr(y, x, "|", dim_attr)
                except curses.error:
                    pass

        # Layer 2: solid cage borders (overwrites dashes where cages meet)
        for r in range(n + 1):
            y = oy + r * (CELL_HEIGHT + 1)
            for c in range(n + 1):
                x = ox + c * (CELL_WIDTH + 1)
                ch = self._junction_char(r, c)
                if ch != " ":
                    try:
                        self.stdscr.addstr(y, x, ch, border_attr)
                    except curses.error:
                        pass
                if c < n and self._h_border[r][c]:
                    try:
                        self.stdscr.addstr(y, x + 1, "─" * CELL_WIDTH, border_attr)
                    except curses.error:
                        pass

            if r < n:
                # Row header
                self.stdscr.addstr(oy + r * (CELL_HEIGHT + 1) + 1 + CELL_HEIGHT // 2,
                                   ox - 2, str(n - r))
                for line in range(CELL_HEIGHT):
                    y = oy + r * (CELL_HEIGHT + 1) + 1 + line
                    for c in range(n + 1):
                        if self._v_border[r][c]:
                            x = ox + c * (CELL_WIDTH + 1)
                            try:
                                self.stdscr.addstr(y, x, "│", border_attr)
                            except curses.error:
                                pass

    def _get_cage_label(self, cage: Cage) -> str:
        if cage.op == "":
            return str(cage.target)
        return "%d%s" % (cage.target, cage.op)

    def _draw_cell_contents(self, won: bool):
        n = self.size
        oy, ox = self.offset_y, self.offset_x

        cage_label_cell: dict[int, tuple[int, int]] = {}
        for cage in self.game.cages:
            top_left = min(cage.cells, key=lambda c: (c[0], c[1]))
            cage_label_cell[id(cage)] = top_left

        for r in range(n):
            for c in range(n):
                cell_y = oy + r * (CELL_HEIGHT + 1) + 1
                cell_x = ox + c * (CELL_WIDTH + 1) + 1

                cage = self.game.cell_cage[(r, c)]

                if cage_label_cell[id(cage)] == (r, c):
                    label = self._get_cage_label(cage)
                    self.stdscr.addstr(cell_y, cell_x, label[:CELL_WIDTH],
                                       curses.color_pair(COLOR_LABEL))

                val = self.game.grid[r][c]
                num_y = cell_y + 1 if CELL_HEIGHT > 1 else cell_y
                num_x = cell_x + CELL_WIDTH // 2

                is_cursor = (r == self.game.cursor_row and c == self.game.cursor_col)

                if val != 0:
                    if won:
                        attr = curses.color_pair(COLOR_WIN) | curses.A_BOLD
                    elif is_cursor:
                        attr = curses.color_pair(COLOR_CURSOR) | curses.A_BOLD
                    elif (r, c) in self.game.conflicts:
                        attr = curses.color_pair(COLOR_CONFLICT) | curses.A_BOLD
                    else:
                        attr = curses.A_BOLD
                    self.stdscr.addstr(num_y, num_x, str(val), attr)
                elif is_cursor:
                    self.stdscr.addstr(num_y, num_x, " ",
                                       curses.color_pair(COLOR_CURSOR))

    def _grid_bottom_y(self) -> int:
        """Return the y coordinate just below the grid."""
        return self.offset_y + self.size * (CELL_HEIGHT + 1) + 1

    def _draw_status(self, won: bool):
        max_y, max_x = self.stdscr.getmaxyx()
        y = self._grid_bottom_y() + 1  # extra line of space
        if won:
            msg = "Congratulations! Puzzle solved!"
            x = max(0, (max_x - len(msg)) // 2)
            self.stdscr.addstr(y, x, msg,
                               curses.color_pair(COLOR_WIN) | curses.A_BOLD)
        else:
            msg = "←→↑↓ move │ 1-6 place │ 0 clear │ r reset │ c chat │ q quit"
            x = max(0, (max_x - len(msg)) // 2)
            self.stdscr.addstr(y, x, msg)

    def _draw_chat_area(self):
        """Draw the persistent chat response area below the status line."""
        if not self.chat_lines:
            return
        max_y, max_x = self.stdscr.getmaxyx()
        start_y = self._grid_bottom_y() + 3
        wrap_width = max_x - self.offset_x - 1
        if wrap_width < 10:
            return

        # Word-wrap chat lines
        wrapped = []
        for raw_line in self.chat_lines:
            if not raw_line:
                wrapped.append("")
                continue
            while len(raw_line) > wrap_width:
                # Try to break at a space
                brk = raw_line.rfind(" ", 0, wrap_width)
                if brk <= 0:
                    brk = wrap_width
                wrapped.append(raw_line[:brk])
                raw_line = raw_line[brk:].lstrip()
            wrapped.append(raw_line)

        # Draw "Claude:" header
        if start_y < max_y:
            try:
                self.stdscr.addstr(start_y, self.offset_x, "Claude:",
                                   curses.color_pair(COLOR_CHAT) | curses.A_BOLD)
            except curses.error:
                pass

        # Draw response lines
        available = max_y - start_y - 2
        for i, line in enumerate(wrapped[:available]):
            y = start_y + 1 + i
            if y >= max_y:
                break
            try:
                self.stdscr.addstr(y, self.offset_x, line[:wrap_width],
                                   curses.color_pair(COLOR_CHAT))
            except curses.error:
                pass

    def set_chat_response(self, text: str):
        """Update the persistent chat response text."""
        self.chat_lines = text.splitlines()

    def clear_chat(self):
        self.chat_lines = []

    def _draw_chat_input(self, prompt: str, user_input: str):
        """Draw a chat input bar at the bottom of the screen."""
        max_y, max_x = self.stdscr.getmaxyx()
        y = max_y - 1
        try:
            self.stdscr.addstr(y, 0, " " * (max_x - 1), curses.A_REVERSE)
            text = "%s%s" % (prompt, user_input)
            self.stdscr.addstr(y, 1, text[:max_x - 3], curses.A_REVERSE)
        except curses.error:
            pass

    def draw(self, won: bool = False):
        self._update_offsets()
        self.stdscr.clear()
        self._draw_grid()
        self._draw_cell_contents(won)
        self._draw_status(won)
        self._draw_chat_area()
        self.stdscr.refresh()

    def draw_with_input(self, won: bool, prompt: str, user_input: str):
        self._update_offsets()
        self.stdscr.clear()
        self._draw_grid()
        self._draw_cell_contents(won)
        self._draw_status(won)
        self._draw_chat_area()
        self._draw_chat_input(prompt, user_input)
        self.stdscr.refresh()
