#!/usr/bin/env python3
"""
Build printable Bump'em board game PDFs — physical edition.
Outputs: board.pdf, cards.pdf, rules.pdf, cars.pdf
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import io
import math

PROJECT_DIR = Path(__file__).resolve().parent
OUT_DIR = PROJECT_DIR / "output"

# Poker card size (2.5" x 3.5")
CARD_W = 2.5 * inch
CARD_H = 3.5 * inch

# Deck: 5x1, 4x2-11, 5x12, 4xBUMP'EM = 54 total
DECK_SPEC = [
    (1, 5), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4),
    (7, 4), (8, 4), (9, 4), (10, 4), (11, 4), (12, 5), ("bumpem", 4),
]

# Card definitions (vectorized)
CARD_INFO = {
    1:  {"label": "1",  "accent": "#F9A825",
         "text": "Move a car from pit row to your start space OR move a car on the track one space forward.",
         "bold": ["Move", "OR", "one space forward"]},
    2:  {"label": "2",  "accent": "#1565C0",
         "text": "Move a car on the track two spaces forward.",
         "bold": ["two"]},
    3:  {"label": "3",  "accent": "#2E7D32",
         "text": "Move a car on the track three spaces forward AND take another move ticket.",
         "bold": ["three spaces forward", "AND", "move ticket"]},
    4:  {"label": "4",  "accent": "#1565C0",
         "text": "Move a car on the track four spaces forward.",
         "bold": ["four"]},
    5:  {"label": "5",  "accent": "#1565C0",
         "text": "Move a car on the track five spaces forward.",
         "bold": ["five"]},
    6:  {"label": "6",  "accent": "#E65100",
         "text": "Move a car on the track six spaces forward OR nine spaces backward.",
         "bold": ["six spaces forward", "OR", "nine spaces backward"]},
    7:  {"label": "7",  "accent": "#6A1B9A",
         "text": "Move a car on the track seven spaces forward OR switch one of your cars with another player's car.",
         "bold": ["seven spaces forward", "OR", "switch one of your cars"]},
    8:  {"label": "8",  "accent": "#00695C",
         "text": "Move a car on the track eight spaces forward OR split the move between two cars.",
         "bold": ["eight spaces forward", "OR", "between two cars"]},
    9:  {"label": "9",  "accent": "#E65100",
         "text": "Move a car on the track nine spaces forward OR six spaces backward.",
         "bold": ["nine spaces forward", "OR", "six spaces backward"]},
    10: {"label": "10", "accent": "#1565C0",
         "text": "Move a car on the track ten spaces forward.",
         "bold": ["ten"]},
    11: {"label": "11", "accent": "#283593",
         "text": "Move a car on the track eleven spaces forward OR one space backward.",
         "bold": ["eleven", "OR"]},
    12: {"label": "12", "accent": "#F9A825",
         "text": "Move a car from pit row to your start space OR move a car on the track twelve spaces forward.",
         "bold": ["OR", "twelve spaces forward"]},
    "bumpem": {"label": "BUMP\n'EM!", "accent": "#4A148C",
         "text": "Take a car from your pit row and bump another player's car.",
         "bold": ["pit row", "bump"]},
}

# ── Board constants ──────────────────────────────────────────────
BOARD_SIZE = 20 * inch
BOARD_MARGIN = 1 * inch
GRID_SIZE = 14  # 14×14 grid (removed empty cols 2,13 and rows 2,12)
NUM_CELLS = 60
CELLS_PER_SIDE = 15
CELL_SIZE = (BOARD_SIZE - 2 * BOARD_MARGIN) / GRID_SIZE  # square cells, 81pt each

# Player definitions — 0-based indices, display = idx+1 (cells 1-60)
# Board positions: Red=TL, Green=TR, Yellow=BR, Blue=BL
# Track: self-crossing loop around all 4 bases (Red→Blue→Yellow→Green→Red)
PLAYERS = [
    {"name": "Red",    "color": "#C62828", "light": "#FFCDD2", "dark": "#B71C1C",
     "start": 0, "home_entry": 58},
    {"name": "Blue",   "color": "#1565C0", "light": "#BBDEFB", "dark": "#0D47A1",
     "start": 15, "home_entry": 13},
    {"name": "Yellow", "color": "#F9A825", "light": "#FFF9C4", "dark": "#F57F17",
     "start": 30, "home_entry": 28},
    {"name": "Green",  "color": "#2E7D32", "light": "#C8E6C9", "dark": "#1B5E20",
     "start": 45, "home_entry": 43},
]

TURBO_CELLS = {3, 18, 33, 48}          # cells 4, 19, 34, 49
OIL_SLICK_CELLS = {11, 26, 41, 56}     # cells 12, 27, 42, 57
OIL_SLICK_END_CELLS = {1, 16, 31, 46}  # cells 2, 17, 32, 47
START_CELLS = {p["start"] for p in PLAYERS}
HOME_ENTRY_CELLS = {p["home_entry"] for p in PLAYERS}

# 60-cell track path as (col, row) grid positions
# Self-crossing loop: Red(TL) → Blue(BL) → Yellow(BR) → Green(TR) → Red
# Track goes clockwise around each base, counterclockwise between bases
TRACK_CELLS = [
    # ── Red right side going down (cells 1-2) ──
    (4, 11),   # 0  cell 1  RED START
    (4, 10),   # 1  cell 2  End of oil slick
    # ── Center crossing to Blue (cell 3) ──
    (4, 7),    # 2  cell 3
    # ── Blue right side going down (cells 4-7) ──
    (4, 3),    # 3  cell 4  TURBO
    (4, 2),    # 4  cell 5
    (4, 1),    # 5  cell 6
    (4, 0),    # 6  cell 7
    # ── Blue bottom going left (cells 8-10) ──
    (3, 0),    # 7  cell 8
    (1, 0),    # 8  cell 9
    (0, 0),    # 9  cell 10
    # ── Blue left going up (cells 11-14) ──
    (0, 1),    # 10 cell 11
    (0, 2),    # 11 cell 12  OIL SLICK
    (0, 3),    # 12 cell 13
    (0, 4),    # 13 cell 14  Entrance to home
    # ── Blue top going right (cells 15-17) ──
    (1, 4),    # 14 cell 15
    (2, 4),    # 15 cell 16  BLUE START
    (3, 4),    # 16 cell 17  End of oil slick
    # ── Center crossing to Yellow (cell 18) ──
    (7, 4),    # 17 cell 18
    # ── Yellow top going right (cells 19-22) ──
    (10, 4),   # 18 cell 19  TURBO
    (11, 4),   # 19 cell 20
    (12, 4),   # 20 cell 21
    (13, 4),   # 21 cell 22
    # ── Yellow right going down (cells 23-25) ──
    (13, 3),   # 22 cell 23
    (13, 1),   # 23 cell 24
    (13, 0),   # 24 cell 25
    # ── Yellow bottom going left (cells 26-29) ──
    (12, 0),   # 25 cell 26
    (11, 0),   # 26 cell 27  OIL SLICK
    (10, 0),   # 27 cell 28
    (9, 0),    # 28 cell 29  Entrance to home
    # ── Yellow left going up (cells 30-32) ──
    (9, 1),    # 29 cell 30
    (9, 2),    # 30 cell 31  YELLOW START
    (9, 3),    # 31 cell 32  End of oil slick
    # ── Center crossing to Green (cell 33) ──
    (9, 7),    # 32 cell 33
    # ── Green left going up (cells 34-37) ──
    (9, 10),   # 33 cell 34  TURBO
    (9, 11),   # 34 cell 35
    (9, 12),   # 35 cell 36
    (9, 13),   # 36 cell 37
    # ── Green top going right (cells 38-40) ──
    (10, 13),  # 37 cell 38
    (12, 13),  # 38 cell 39
    (13, 13),  # 39 cell 40
    # ── Green right going down (cells 41-44) ──
    (13, 12),  # 40 cell 41
    (13, 11),  # 41 cell 42  OIL SLICK
    (13, 10),  # 42 cell 43
    (13, 9),   # 43 cell 44  Entrance to home
    # ── Green bottom going left (cells 45-47) ──
    (12, 9),   # 44 cell 45
    (11, 9),   # 45 cell 46  GREEN START
    (10, 9),   # 46 cell 47  End of oil slick
    # ── Center crossing to Red (cell 48) ──
    (7, 9),    # 47 cell 48
    # ── Red bottom going left (cells 49-52) ──
    (3, 9),    # 48 cell 49  TURBO
    (2, 9),    # 49 cell 50
    (1, 9),    # 50 cell 51
    (0, 9),    # 51 cell 52
    # ── Red left going up (cells 53-55) ──
    (0, 10),   # 52 cell 53
    (0, 12),   # 53 cell 54
    (0, 13),   # 54 cell 55
    # ── Red top going right (cells 56-60) ──
    (1, 13),   # 55 cell 56
    (2, 13),   # 56 cell 57  OIL SLICK
    (3, 13),   # 57 cell 58
    (4, 13),   # 58 cell 59  Entrance to home
    (4, 12),   # 59 cell 60
]


def _compute_arrow_directions(cells):
    """Compute arrow direction for each cell based on vector to next cell."""
    directions = []
    for index in range(len(cells)):
        current = cells[index]
        next_cell = cells[(index + 1) % len(cells)]
        delta_col = next_cell[0] - current[0]
        delta_row = next_cell[1] - current[1]
        if abs(delta_col) >= abs(delta_row):
            direction = 0 if delta_col > 0 else 2  # right or left
        else:
            direction = 3 if delta_row > 0 else 1  # up or down
        directions.append(direction)
    return directions


# Arrow direction per cell: 0=→, 1=↓, 2=←, 3=↑ (auto-computed)
TRACK_ARROWS = _compute_arrow_directions(TRACK_CELLS)

# Home stretch cells per player: 4 cells branching from home_entry toward center
# Each stretch goes from entrance through the center channel toward the board middle
HOME_CELLS = {
    "Red":    [(6, 13), (6, 12), (6, 11), (6, 10)],     # col 6 going down, 1 gap from entry
    "Blue":   [(0, 6),  (1, 6),  (2, 6),  (3, 6)],      # row 6 going right, 1 gap from entry
    "Yellow": [(7, 0),  (7, 1),  (7, 2),  (7, 3)],      # col 7 going up, 1 gap from entry
    "Green":  [(13, 7), (12, 7), (11, 7), (10, 7)],     # row 7 going left, 1 gap from entry
}

BOARD_BACKGROUND = HexColor("#1B5E20")
TRACK_GRAY = HexColor("#D0D0D0")
CELL_WHITE = HexColor("#F5F5F5")
CELL_BORDER = HexColor("#888888")
RAINBOW = [
    HexColor("#E53935"), HexColor("#FB8C00"), HexColor("#FDD835"),
    HexColor("#43A047"), HexColor("#1E88E5"), HexColor("#8E24AA"),
]


def ensure_output_dir():
    OUT_DIR.mkdir(exist_ok=True)


# ── Track geometry ───────────────────────────────────────────────

def _grid_xy(col, row):
    """Bottom-left corner of grid cell (col, row) in PDF coordinates."""
    return (BOARD_MARGIN + col * CELL_SIZE, BOARD_MARGIN + row * CELL_SIZE)


def _cell_rect(idx):
    """(x, y, w, h) for track cell idx (0-based, 0-59)."""
    col, row = TRACK_CELLS[idx]
    x, y = _grid_xy(col, row)
    return (x, y, CELL_SIZE, CELL_SIZE)


def _cell_center(idx):
    x, y, w, h = _cell_rect(idx)
    return x + w / 2, y + h / 2


def _home_rects(player):
    """4 home-stretch cells for the given player."""
    cells = []
    for col, row in HOME_CELLS[player["name"]]:
        x, y = _grid_xy(col, row)
        cells.append((x, y, CELL_SIZE, CELL_SIZE))
    return cells


CAR_TOKEN_RADIUS = CELL_SIZE * 0.44


def _draw_fabric_texture(canvas_obj):
    """Draw subtle woven fabric/mesh texture over the board background."""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(Color(0, 0.22, 0, alpha=0.07))
    canvas_obj.setLineWidth(0.3)
    spacing = 4
    board_int = int(BOARD_SIZE)
    for y_pos in range(0, board_int, spacing):
        canvas_obj.line(0, y_pos, BOARD_SIZE, y_pos)
    for x_pos in range(0, board_int, spacing):
        canvas_obj.line(x_pos, 0, x_pos, BOARD_SIZE)
    canvas_obj.restoreState()


def _draw_checkered_flag(canvas_obj, center_x, center_y, size):
    """Draw a small checkered flag/pattern for FINISH markers."""
    squares = 4
    square_size = size / squares
    start_x = center_x - size / 2
    start_y = center_y - size / 2
    for row in range(squares):
        for col in range(squares):
            if (row + col) % 2 == 0:
                canvas_obj.setFillColor(black)
            else:
                canvas_obj.setFillColor(white)
            canvas_obj.rect(start_x + col * square_size,
                            start_y + row * square_size,
                            square_size, square_size, fill=1, stroke=0)


# ── Board drawing ────────────────────────────────────────────────


def _fill_gap_positions(position_a, position_b):
    """Return all intermediate grid positions between two cells on the same row or column."""
    col_a, row_a = position_a
    col_b, row_b = position_b
    positions = set()
    if col_a == col_b:  # vertical segment
        step = 1 if row_b > row_a else -1
        for intermediate_row in range(row_a, row_b, step):
            positions.add((col_a, intermediate_row))
    elif row_a == row_b:  # horizontal segment
        step = 1 if col_b > col_a else -1
        for intermediate_col in range(col_a, col_b, step):
            positions.add((intermediate_col, row_a))
    return positions


def _draw_track_band(canvas_obj):
    """Draw track band by filling each cell and all gaps between consecutive cells."""
    canvas_obj.setFillColor(TRACK_GRAY)

    # Collect all grid positions that need grey fill
    fill_positions = set()

    # Main track cells and gaps between consecutive cells
    for index in range(len(TRACK_CELLS)):
        fill_positions.add(TRACK_CELLS[index])
        next_cell = TRACK_CELLS[(index + 1) % len(TRACK_CELLS)]
        fill_positions |= _fill_gap_positions(TRACK_CELLS[index], next_cell)

    # Home stretch cells, internal gaps, and connection from home entry to first home cell
    for player in PLAYERS:
        cells = HOME_CELLS[player["name"]]
        entry_position = TRACK_CELLS[player["home_entry"]]
        # Gap from home entry on main track to first home cell
        fill_positions |= _fill_gap_positions(entry_position, cells[0])
        for i, position in enumerate(cells):
            fill_positions.add(position)
            if i < len(cells) - 1:
                fill_positions |= _fill_gap_positions(position, cells[i + 1])

    # Draw all filled positions
    for col, row in fill_positions:
        x, y = _grid_xy(col, row)
        canvas_obj.rect(x, y, CELL_SIZE, CELL_SIZE, fill=1, stroke=0)


def _compute_gap_arrows():
    """Compute arrow directions for each intermediate gap cell.

    Returns a dict of (col, row) -> list of directions.
    Crossing cells where two tracks intersect get two directions.
    """
    gap_arrows = {}  # (col, row) -> [direction, ...]

    def _add_direction(pos, direction):
        if pos not in gap_arrows:
            gap_arrows[pos] = []
        if direction not in gap_arrows[pos]:
            gap_arrows[pos].append(direction)

    # Gaps between consecutive main track cells
    track_cell_set = set(TRACK_CELLS)
    for index in range(len(TRACK_CELLS)):
        current = TRACK_CELLS[index]
        next_cell = TRACK_CELLS[(index + 1) % len(TRACK_CELLS)]
        delta_col = next_cell[0] - current[0]
        delta_row = next_cell[1] - current[1]
        if abs(delta_col) >= abs(delta_row):
            direction = 0 if delta_col > 0 else 2
        else:
            direction = 3 if delta_row > 0 else 1
        for pos in _fill_gap_positions(current, next_cell):
            if pos not in track_cell_set:
                _add_direction(pos, direction)

    # Gaps in home stretches (entry to first cell, and between home cells)
    home_cell_set = set()
    for cells in HOME_CELLS.values():
        home_cell_set.update(cells)
    for player in PLAYERS:
        cells = HOME_CELLS[player["name"]]
        entry_position = TRACK_CELLS[player["home_entry"]]
        all_pairs = [(entry_position, cells[0])]
        for i in range(len(cells) - 1):
            all_pairs.append((cells[i], cells[i + 1]))
        for pos_a, pos_b in all_pairs:
            delta_col = pos_b[0] - pos_a[0]
            delta_row = pos_b[1] - pos_a[1]
            if abs(delta_col) >= abs(delta_row):
                direction = 0 if delta_col > 0 else 2
            else:
                direction = 3 if delta_row > 0 else 1
            for pos in _fill_gap_positions(pos_a, pos_b):
                if pos not in track_cell_set and pos not in home_cell_set:
                    _add_direction(pos, direction)
    return gap_arrows


GAP_ARROWS = _compute_gap_arrows()


def _draw_crossing_symbol(canvas_obj, cx, cy, directions):
    """Draw L-shaped arrows at crossing cells where two tracks intersect."""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(white)
    canvas_obj.setFillColor(white)
    canvas_obj.setLineWidth(1.5)
    size = CELL_SIZE * 0.30
    tip = size * 0.35
    # Draw an L-shaped arrow for each direction pair
    for direction in directions:
        canvas_obj.saveState()
        canvas_obj.translate(cx, cy)
        canvas_obj.rotate(-90 * direction)
        # Draw L: short stem + turn + arrowhead pointing in direction
        path = canvas_obj.beginPath()
        path.moveTo(-size, -size * 0.6)
        path.lineTo(-size, 0)
        path.lineTo(size, 0)
        canvas_obj.drawPath(path, fill=0, stroke=1)
        # Arrowhead at tip
        arrow = canvas_obj.beginPath()
        arrow.moveTo(size, 0)
        arrow.lineTo(size - tip, tip * 0.7)
        arrow.moveTo(size, 0)
        arrow.lineTo(size - tip, -tip * 0.7)
        canvas_obj.drawPath(arrow, fill=0, stroke=1)
        canvas_obj.restoreState()
    canvas_obj.restoreState()


def _draw_gap_arrows(canvas_obj):
    """Draw directional arrows on all intermediate gap cells.

    Crossing cells with two directions get both arrows drawn.
    """
    for (col, row), directions in GAP_ARROWS.items():
        x, y = _grid_xy(col, row)
        cx = x + CELL_SIZE / 2
        cy = y + CELL_SIZE / 2
        if len(directions) == 1:
            _draw_arrow(canvas_obj, cx, cy, directions[0])
        else:
            # Crossing: draw L-shaped arrows showing both perpendicular directions
            _draw_crossing_symbol(canvas_obj, cx, cy, directions)


def _draw_arrow(c, cx, cy, direction, size=7):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(-90 * direction)
    p = c.beginPath()
    p.moveTo(size, 0)
    p.lineTo(-size * 0.5, size * 0.55)
    p.lineTo(-size * 0.5, -size * 0.55)
    p.close()
    c.setFillColor(white)
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _player_for_cell(idx, attr):
    for p in PLAYERS:
        if p[attr] == idx:
            return p
    return None


def _draw_track_cells(c):
    for idx in range(NUM_CELLS):
        x, y, w, h = _cell_rect(idx)
        num = idx + 1  # display number 1-60

        # Cell fill
        if idx in TURBO_CELLS:
            fill = HexColor("#E1BEE7")
        elif idx in OIL_SLICK_CELLS:
            fill = HexColor("#455A64")
        elif idx in OIL_SLICK_END_CELLS:
            fill = HexColor("#607D8B")
        elif idx in START_CELLS:
            p = _player_for_cell(idx, "start")
            fill = HexColor(p["light"])
        elif idx in HOME_ENTRY_CELLS:
            p = _player_for_cell(idx, "home_entry")
            fill = HexColor(p["light"])
        else:
            fill = CELL_WHITE

        c.setFillColor(fill)
        c.setStrokeColor(CELL_BORDER)
        c.setLineWidth(0.8)
        c.rect(x, y, w, h, fill=1, stroke=1)

        cx, cy = x + w / 2, y + h / 2

        # Cell number
        if idx in OIL_SLICK_CELLS or idx in OIL_SLICK_END_CELLS:
            c.setFillColor(white)
        else:
            c.setFillColor(HexColor("#616161"))
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx, cy + 8, str(num))

        # Special labels
        if idx in START_CELLS:
            p = _player_for_cell(idx, "start")
            c.setFillColor(HexColor(p["dark"]))
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(cx, cy - 8, "START")
        elif idx in TURBO_CELLS:
            c.setFillColor(HexColor("#6A1B9A"))
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(cx, cy - 8, "TURBO")
        elif idx in OIL_SLICK_CELLS:
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 8, "OIL SLICK")
        elif idx in OIL_SLICK_END_CELLS:
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 8, "SLICK END")
        elif idx in HOME_ENTRY_CELLS:
            p = _player_for_cell(idx, "home_entry")
            c.setFillColor(HexColor(p["dark"]))
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(cx, cy - 8, "HOME \u25b8")
        else:
            _draw_arrow(c, cx, cy - 8, TRACK_ARROWS[idx])


def _draw_home_stretches(c):
    for player in PLAYERS:
        color = HexColor(player["color"])
        light = HexColor(player["light"])
        dark = HexColor(player["dark"])
        cells = _home_rects(player)
        for i, (x, y, w, h) in enumerate(cells):
            is_finish = (i == len(cells) - 1)
            blend = 0.2 + 0.8 * (i / 3)
            r = light.red * (1 - blend) + color.red * blend
            g = light.green * (1 - blend) + color.green * blend
            b = light.blue * (1 - blend) + color.blue * blend
            c.setFillColor(Color(r, g, b))
            c.setStrokeColor(dark)
            c.setLineWidth(1)
            c.rect(x, y, w, h, fill=1, stroke=1)
            cell_cx, cell_cy = x + w / 2, y + h / 2
            c.setFillColor(white)
            if is_finish:
                # FINISH marker: number + checkered flag + text
                num = player["home_entry"] + i + 2
                c.setFillColor(white)
                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(cell_cx, cell_cy + 16, str(num))
                _draw_checkered_flag(c, cell_cx, cell_cy + 2, CELL_SIZE * 0.35)
                c.setFillColor(white)
                c.setFont("Helvetica-Bold", 7)
                c.drawCentredString(cell_cx, cell_cy - 16, "FINISH")
            else:
                num = player["home_entry"] + i + 2  # continue numbering from track
                c.setFont("Helvetica-Bold", 15)
                c.drawCentredString(cell_cx, cell_cy - 6, str(num))


def _draw_pit_rows(c):
    """Draw 2×2 colored base areas in the board corners (between cross arms)."""
    # Center each 2×2 base in the 6×6 corner area
    base_positions = {
        "Red":    (1, 10),   # TL interior
        "Green":  (10, 10),  # TR interior
        "Yellow": (10, 1),   # BR interior
        "Blue":   (1, 1),    # BL interior
    }
    base_size = 3 * CELL_SIZE

    for player in PLAYERS:
        color = HexColor(player["color"])
        light = HexColor(player["light"])
        dark = HexColor(player["dark"])
        col, row = base_positions[player["name"]]
        x, y = _grid_xy(col, row)

        # Colored base area
        c.setFillColor(light)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.rect(x, y, base_size, base_size, fill=1, stroke=1)

        # "PIT ROW" label
        c.setFillColor(dark)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + base_size / 2, y + base_size / 2 - 4, "PIT ROW")


def _draw_center_logo(c):
    """Draw the logo.png image in the center of the board."""
    center_x = BOARD_SIZE / 2
    center_y = BOARD_SIZE / 2
    # Draw a dark green circle behind the logo
    radius = CELL_SIZE * 1.4
    c.setFillColor(HexColor("#1B5E20"))
    c.setStrokeColor(HexColor("#FDD835"))
    c.setLineWidth(4)
    c.circle(center_x, center_y, radius, fill=1, stroke=1)
    c.setStrokeColor(HexColor("#FB8C00"))
    c.setLineWidth(2)
    c.circle(center_x, center_y, radius * 0.88, fill=0, stroke=1)
    # Draw the actual logo image
    logo = PILImage.open(LOGO_PATH).convert("RGBA")
    background = PILImage.new("RGBA", logo.size, (27, 94, 32, 255))
    composited = PILImage.alpha_composite(background, logo).convert("RGB")
    buffer = io.BytesIO()
    composited.save(buffer, format="PNG")
    buffer.seek(0)
    reader = ImageReader(buffer)
    aspect = logo.width / logo.height
    logo_width = radius * 1.5
    logo_height = logo_width / aspect
    c.drawImage(reader,
                center_x - logo_width / 2, center_y - logo_height / 2,
                width=logo_width, height=logo_height)


def build_board_pdf():
    ensure_output_dir()
    pdf_path = OUT_DIR / "board.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(BOARD_SIZE, BOARD_SIZE))
    # 1. Background
    c.setFillColor(BOARD_BACKGROUND)
    c.rect(0, 0, BOARD_SIZE, BOARD_SIZE, fill=1, stroke=0)
    # 2. Fabric texture overlay
    _draw_fabric_texture(c)
    # 3. Player base areas (colored corners, behind the track)
    _draw_pit_rows(c)
    # 4. Track band
    _draw_track_band(c)
    # 5. Arrows on gap cells
    _draw_gap_arrows(c)
    # 6. Individual track cells
    _draw_track_cells(c)
    # 7. Home stretches
    _draw_home_stretches(c)
    # 8. Center logo
    _draw_center_logo(c)
    c.showPage()
    c.save()
    print("Wrote", pdf_path)


# ── Cards (fully vectorized) ────────────────────────────────────

def _wrap(text, font, size, max_w, c_obj):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if c_obj.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


LOGO_PATH = PROJECT_DIR / "screenshots" / "logo.png"

# Pre-load and cache logo watermark (12% opacity on cream background)
_logo_watermark_cache = {}


def _get_logo_watermark(opacity=0.12):
    """Return an ImageReader of the logo composited at given opacity onto cream."""
    if opacity in _logo_watermark_cache:
        return _logo_watermark_cache[opacity]
    logo = PILImage.open(LOGO_PATH).convert("RGBA")
    alpha = logo.split()[3]
    alpha = alpha.point(lambda pixel: int(pixel * opacity))
    logo.putalpha(alpha)
    background = PILImage.new("RGBA", logo.size, (255, 248, 231, 255))
    composited = PILImage.alpha_composite(background, logo).convert("RGB")
    buffer = io.BytesIO()
    composited.save(buffer, format="PNG")
    buffer.seek(0)
    reader = ImageReader(buffer)
    _logo_watermark_cache[opacity] = reader
    return reader


def _get_logo_full():
    """Return an ImageReader of the logo at full opacity."""
    if "full" in _logo_watermark_cache:
        return _logo_watermark_cache["full"]
    logo = PILImage.open(LOGO_PATH).convert("RGBA")
    background = PILImage.new("RGBA", logo.size, (230, 213, 230, 255))
    composited = PILImage.alpha_composite(background, logo).convert("RGB")
    buffer = io.BytesIO()
    composited.save(buffer, format="PNG")
    buffer.seek(0)
    reader = ImageReader(buffer)
    _logo_watermark_cache["full"] = reader
    return reader


def _logo_aspect_ratio():
    """Return width/height of the logo image."""
    logo = PILImage.open(LOGO_PATH)
    return logo.width / logo.height


def _draw_herringbone_texture(canvas_obj, x, y, width, height, corner_radius=4):
    """Draw subtle diagonal chevron lines over the card face at low opacity."""
    canvas_obj.saveState()
    clip = canvas_obj.beginPath()
    clip.roundRect(x, y, width, height, corner_radius)
    canvas_obj.clipPath(clip, stroke=0)
    canvas_obj.setStrokeColor(Color(0.82, 0.78, 0.70, alpha=0.13))
    canvas_obj.setLineWidth(0.35)
    spacing = 6
    for offset in range(int(-height), int(width + height), spacing):
        canvas_obj.line(x + offset, y, x + offset + height, y + height)
    for offset in range(0, int(width + height * 2), spacing):
        canvas_obj.line(x + offset, y + height, x + offset - height, y)
    canvas_obj.restoreState()


def _draw_halftone_dots(canvas_obj, x, y, width, height, corner_radius=5):
    """Draw subtle halftone dot pattern for retro comic feel."""
    canvas_obj.saveState()
    clip = canvas_obj.beginPath()
    clip.roundRect(x, y, width, height, corner_radius)
    canvas_obj.clipPath(clip, stroke=0)
    canvas_obj.setFillColor(Color(0.78, 0.70, 0.78, alpha=0.10))
    spacing = 8
    dot_radius = 1.2
    for dot_x in range(0, int(width) + spacing, spacing):
        for dot_y in range(0, int(height) + spacing, spacing):
            canvas_obj.circle(x + dot_x, y + dot_y, dot_radius, fill=1, stroke=0)
    canvas_obj.restoreState()


def _split_into_segments(text, bold_phrases):
    """Split text into (substring, is_bold) segments based on bold_phrases."""
    segments = []
    remaining = text
    while remaining:
        earliest_pos = len(remaining)
        earliest_phrase = None
        for phrase in bold_phrases:
            position = remaining.find(phrase)
            if position != -1 and position < earliest_pos:
                earliest_pos = position
                earliest_phrase = phrase
        if earliest_phrase is None:
            segments.append((remaining, False))
            break
        if earliest_pos > 0:
            segments.append((remaining[:earliest_pos], False))
        segments.append((earliest_phrase, True))
        remaining = remaining[earliest_pos + len(earliest_phrase):]
    return segments


def _draw_rich_text_centered(canvas_obj, text, bold_phrases, center_x, top_y,
                              max_width, font_size=8.5, line_spacing=11):
    """Draw text centered with certain phrases rendered in bold. OR in lime green."""
    regular_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    segments = _split_into_segments(text, bold_phrases)

    # Build word list with bold attribute
    words = []
    for segment_text, is_bold in segments:
        parts = segment_text.split(" ")
        for index, part in enumerate(parts):
            if not part:
                continue
            words.append((part, is_bold))

    # Word-wrap into lines
    lines = []
    current_line = []
    current_width = 0
    space_width = canvas_obj.stringWidth(" ", regular_font, font_size)
    for word_text, is_bold in words:
        font = bold_font if is_bold else regular_font
        word_width = canvas_obj.stringWidth(word_text, font, font_size)
        test_width = current_width + (space_width if current_line else 0) + word_width
        if test_width <= max_width or not current_line:
            current_line.append((word_text, is_bold))
            current_width = test_width
        else:
            lines.append(current_line)
            current_line = [(word_text, is_bold)]
            current_width = word_width
    if current_line:
        lines.append(current_line)

    # Draw each line centered
    draw_y = top_y
    for line_words in lines:
        # Calculate total width including spaces
        total_width = 0
        for index, (word_text, is_bold) in enumerate(line_words):
            font = bold_font if is_bold else regular_font
            total_width += canvas_obj.stringWidth(word_text, font, font_size)
            if index < len(line_words) - 1:
                total_width += space_width
        draw_x = center_x - total_width / 2
        for index, (word_text, is_bold) in enumerate(line_words):
            font = bold_font if is_bold else regular_font
            # "OR" and "AND" in lime green
            if word_text in ("OR", "AND") and is_bold:
                canvas_obj.setFillColor(HexColor("#8BC34A"))
            else:
                canvas_obj.setFillColor(HexColor("#333333") if not is_bold else HexColor("#1A1A1A"))
            canvas_obj.setFont(font, font_size)
            canvas_obj.drawString(draw_x, draw_y, word_text)
            draw_x += canvas_obj.stringWidth(word_text, font, font_size)
            if index < len(line_words) - 1:
                draw_x += space_width
        draw_y -= line_spacing


def _draw_number_card(canvas_obj, x, y, value):
    """Draw a number ticket card (1-12) matching the spec design."""
    info = CARD_INFO[value]

    # Layer 1: Outer gold/bronze border
    canvas_obj.setFillColor(HexColor("#C4A35A"))
    canvas_obj.roundRect(x, y, CARD_W, CARD_H, 8, fill=1, stroke=0)

    # Layer 2: Dark inner line
    canvas_obj.setStrokeColor(HexColor("#2C1810"))
    canvas_obj.setLineWidth(1.5)
    canvas_obj.roundRect(x + 5, y + 5, CARD_W - 10, CARD_H - 10, 6, fill=0, stroke=1)

    # Layer 3: Beige/tan inner band
    canvas_obj.setFillColor(HexColor("#F5F0E0"))
    canvas_obj.roundRect(x + 7, y + 7, CARD_W - 14, CARD_H - 14, 5, fill=1, stroke=0)

    # Layer 4: Card face (cream)
    face_x = x + 10
    face_y = y + 10
    face_width = CARD_W - 20
    face_height = CARD_H - 20
    canvas_obj.setFillColor(HexColor("#FFF8E7"))
    canvas_obj.roundRect(face_x, face_y, face_width, face_height, 4, fill=1, stroke=0)

    # Herringbone texture
    _draw_herringbone_texture(canvas_obj, face_x, face_y, face_width, face_height, 4)

    # Logo watermark behind number
    watermark = _get_logo_watermark(0.12)
    aspect = _logo_aspect_ratio()
    watermark_width = face_width * 0.75
    watermark_height = watermark_width / aspect
    watermark_center_x = x + CARD_W / 2
    watermark_center_y = y + CARD_H * 0.55
    canvas_obj.drawImage(watermark,
                         watermark_center_x - watermark_width / 2,
                         watermark_center_y - watermark_height / 2,
                         width=watermark_width, height=watermark_height)

    # Large number — dark grey/black, dark green for 1 & 12
    number_center_y = y + CARD_H * 0.62
    number_color = "#2D4A2D" if value in (1, 12) else "#1A1A1A"
    canvas_obj.setFillColor(HexColor(number_color))
    font_size = 48 if value < 10 else 38
    canvas_obj.setFont("Helvetica-Bold", font_size)
    canvas_obj.drawCentredString(x + CARD_W / 2, number_center_y - font_size * 0.35, str(value))

    # Instruction text with bold emphasis
    text_top = y + CARD_H * 0.30
    text_width = CARD_W - 30
    _draw_rich_text_centered(canvas_obj, info["text"], info["bold"],
                              x + CARD_W / 2, text_top, text_width, 8.5, 11)


def _draw_bumpem_card(canvas_obj, x, y):
    """Draw the BUMP'EM card with retro halftone comic style."""
    # Background: light pinkish-purple
    canvas_obj.setFillColor(HexColor("#E6D5E6"))
    canvas_obj.roundRect(x, y, CARD_W, CARD_H, 6, fill=1, stroke=0)

    # Thin dark purple border
    canvas_obj.setStrokeColor(HexColor("#4A148C"))
    canvas_obj.setLineWidth(2)
    canvas_obj.roundRect(x + 3, y + 3, CARD_W - 6, CARD_H - 6, 5, fill=0, stroke=1)

    # Halftone dot texture
    _draw_halftone_dots(canvas_obj, x + 3, y + 3, CARD_W - 6, CARD_H - 6, 5)

    card_center_x = x + CARD_W / 2

    # "BUMP 'EM!" title at top — yellow with dark purple outline
    title_y = y + CARD_H - 38
    canvas_obj.setFont("Helvetica-Bold", 22)
    canvas_obj.setFillColor(HexColor("#4A148C"))
    for offset_x, offset_y in [(-1.5, 0), (1.5, 0), (0, -1.5), (0, 1.5),
                                 (-1, -1), (1, 1), (-1, 1), (1, -1)]:
        canvas_obj.drawCentredString(card_center_x + offset_x, title_y + offset_y,
                                      "BUMP 'EM!")
    canvas_obj.setFillColor(HexColor("#FFD54F"))
    canvas_obj.drawCentredString(card_center_x, title_y, "BUMP 'EM!")

    # Logo image at full opacity, centered
    logo_reader = _get_logo_full()
    aspect = _logo_aspect_ratio()
    logo_width = CARD_W * 0.55
    logo_height = logo_width / aspect
    logo_center_y = y + CARD_H * 0.52
    canvas_obj.drawImage(logo_reader,
                         card_center_x - logo_width / 2,
                         logo_center_y - logo_height / 2,
                         width=logo_width, height=logo_height)

    # "BUMP 'EM!" again below logo — dark purple
    subtitle_y = y + CARD_H * 0.26
    canvas_obj.setFillColor(HexColor("#4A148C"))
    canvas_obj.setFont("Helvetica-Bold", 18)
    canvas_obj.drawCentredString(card_center_x, subtitle_y, "BUMP 'EM!")

    # Instruction text — dark purple with bold emphasis
    info = CARD_INFO["bumpem"]
    text_y = y + CARD_H * 0.14
    _draw_rich_text_centered(canvas_obj, info["text"], info["bold"],
                              card_center_x, text_y, CARD_W - 30, 8, 10)


def _draw_vector_card(canvas_obj, x, y, value):
    """Dispatch to the appropriate card renderer."""
    if value == "bumpem":
        _draw_bumpem_card(canvas_obj, x, y)
    else:
        _draw_number_card(canvas_obj, x, y, value)


def _get_logo_on_green():
    """Return an ImageReader of the logo composited onto dark green background."""
    if "green_back" in _logo_watermark_cache:
        return _logo_watermark_cache["green_back"]
    logo = PILImage.open(LOGO_PATH).convert("RGBA")
    background = PILImage.new("RGBA", logo.size, (27, 94, 32, 255))
    composited = PILImage.alpha_composite(background, logo).convert("RGB")
    buffer = io.BytesIO()
    composited.save(buffer, format="PNG")
    buffer.seek(0)
    reader = ImageReader(buffer)
    _logo_watermark_cache["green_back"] = reader
    return reader


def _draw_card_back(c, x, y):
    c.setFillColor(HexColor("#1B5E20"))
    c.roundRect(x, y, CARD_W, CARD_H, 6, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#FDD835"))
    c.setLineWidth(2)
    c.roundRect(x + 6, y + 6, CARD_W - 12, CARD_H - 12, 5, fill=0, stroke=1)
    c.setStrokeColor(HexColor("#FB8C00"))
    c.setLineWidth(1)
    c.roundRect(x + 12, y + 12, CARD_W - 24, CARD_H - 24, 4, fill=0, stroke=1)
    # Logo centered on card back
    logo_reader = _get_logo_on_green()
    aspect = _logo_aspect_ratio()
    logo_width = CARD_W * 0.7
    logo_height = logo_width / aspect
    cx = x + CARD_W / 2
    cy = y + CARD_H / 2
    c.drawImage(logo_reader,
                cx - logo_width / 2, cy - logo_height / 2,
                width=logo_width, height=logo_height)


def build_cards_pdf():
    ensure_output_dir()
    pw, ph = letter
    gap = 0.12 * inch
    total_w = 3 * CARD_W + 2 * gap
    total_h = 3 * CARD_H + 2 * gap
    sx = (pw - total_w) / 2
    sy = (ph - total_h) / 2
    pdf_path = OUT_DIR / "cards.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    deck = []
    for value, count in DECK_SPEC:
        deck.extend([value] * count)

    for page_start in range(0, len(deck), 9):
        page_cards = deck[page_start:page_start + 9]
        for i, val in enumerate(page_cards):
            row, col = i // 3, i % 3
            x = sx + col * (CARD_W + gap)
            y = sy + (2 - row) * (CARD_H + gap)
            _draw_vector_card(c, x, y, val)
            c.setDash(3, 3)
            c.setStrokeColor(HexColor("#AAAAAA"))
            c.setLineWidth(0.3)
            c.rect(x - 1, y - 1, CARD_W + 2, CARD_H + 2, fill=0, stroke=1)
            c.setDash()
        c.setFont("Helvetica", 7)
        c.drawString(sx, sy - 14, "Cut along dashed lines. Poker size 2.5\" \u00d7 3.5\".")
        c.showPage()

    num_pages = math.ceil(len(deck) / 9)
    for _ in range(num_pages):
        for row in range(3):
            for col in range(3):
                x = sx + col * (CARD_W + gap)
                y = sy + (2 - row) * (CARD_H + gap)
                _draw_card_back(c, x, y)
                c.setDash(3, 3)
                c.setStrokeColor(HexColor("#AAAAAA"))
                c.setLineWidth(0.3)
                c.rect(x - 1, y - 1, CARD_W + 2, CARD_H + 2, fill=0, stroke=1)
                c.setDash()
        c.setFont("Helvetica", 7)
        c.drawString(sx, sy - 14, "Card backs \u2014 print double-sided or glue to fronts.")
        c.showPage()

    c.save()
    print("Wrote", pdf_path)


# ── Rules ────────────────────────────────────────────────────────

def build_rules_pdf():
    ensure_output_dir()
    pdf_path = OUT_DIR / "rules.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    pw, ph = letter
    margin = 60
    max_w = pw - 2 * margin
    y = ph - margin

    c.setFillColor(HexColor("#1B5E20"))
    c.rect(0, y - 10, pw, 50, fill=1, stroke=0)
    c.setFillColor(HexColor("#FDD835"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(pw / 2, y + 4, "BUMP'EM \u2014 Rules")
    y -= 40

    def section(title):
        nonlocal y
        y -= 16
        c.setFillColor(HexColor("#1B5E20"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, title)
        y -= 4
        c.setStrokeColor(HexColor("#43A047"))
        c.setLineWidth(1)
        c.line(margin, y, pw - margin, y)
        y -= 14

    def body(text):
        nonlocal y
        c.setFont("Helvetica", 10)
        c.setFillColor(black)
        for line in _wrap(text, "Helvetica", 10, max_w, c):
            c.drawString(margin, y, line)
            y -= 13

    def ticket(num, text):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(HexColor("#1565C0"))
        c.drawString(margin + 4, y, str(num))
        c.setFont("Helvetica", 10)
        c.setFillColor(black)
        c.drawString(margin + 56, y, text)
        y -= 13

    section("Components")
    body("54 ticket cards, 1 game board (60-space track), 16 car tokens "
         "(4 each: red, blue, yellow, green).")

    section("Setup")
    body("Each player picks a color and places 4 car tokens in their PIT ROW on the board. "
         "Shuffle the 54-card ticket deck face-down.")

    section("Goal")
    body("Move all 4 of your cars from your PIT ROW, around the track (60 numbered spaces), "
         "and into your 4-space home stretch to reach FINISH.")

    section("On Your Turn")
    body("Draw 1 ticket and follow it. Reshuffle when the deck runs out.")

    section("Ticket Guide")
    ticket(1, "Pit row \u2192 START space OR move a car on the track one space forward.")
    ticket(2, "Move a car on the track two spaces forward.")
    ticket(3, "Move a car on the track three spaces forward AND take another move ticket.")
    ticket(4, "Move a car on the track four spaces forward.")
    ticket(5, "Move a car on the track five spaces forward.")
    ticket(6, "Move a car on the track six spaces forward OR nine spaces backward.")
    ticket(7, "Move seven spaces forward OR switch one of your cars with another player's car.")
    ticket(8, "Move eight spaces forward OR split the move between two cars.")
    ticket(9, "Move a car on the track nine spaces forward OR six spaces backward.")
    ticket(10, "Move a car on the track ten spaces forward.")
    ticket(11, "Move a car on the track eleven spaces forward OR one space backward.")
    ticket(12, "Pit row \u2192 START space OR move a car on the track twelve spaces forward.")
    ticket("BUMP'EM", "Take a car from your pit row and bump another player's car.")

    section("Special Spaces")
    body("TURBO \u2014 If your car is hit (bumped) on a TURBO space by any car "
         "(yours or an opponent's), it is teleported to the next TURBO cell on the track "
         "instead of going back to pit row.")
    y -= 2
    body("OIL SLICK \u2014 When you pass through an OIL SLICK space, "
         "you bump all cars on your remaining path (they go back to their pit rows).")

    section("Bumping")
    body("Land on an opponent's car to bump it back to their pit row. You cannot bump your own.")

    section("Home Stretch")
    body("After circling the full track, enter your home stretch at the HOME cell. "
         "You must reach FINISH by exact count. Opponents cannot enter your home stretch.")

    y -= 16
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#757575"))
    c.drawCentredString(pw / 2, y,
                        "Physical edition based on Hoyle\u00ae Puzzle Games \u2014 Bump 'em.")
    c.showPage()
    c.save()
    print("Wrote", pdf_path)


# ── Cars (simple circles, no numbers) ───────────────────────────

def build_cars_pdf():
    ensure_output_dir()
    pdf_path = OUT_DIR / "cars.pdf"
    pw, ph = letter
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    token_r = CAR_TOKEN_RADIUS  # same size as pit row slots on the board
    margin = 0.8 * inch
    gap = 0.25 * inch
    col_gap = token_r * 2 + gap

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(black)
    c.drawString(margin, ph - margin + 10,
                 "Car Tokens \u2014 cut out circles, place on board")

    y_cursor = ph - margin - 20 - token_r  # extra 20pt gap below title

    for player in PLAYERS:
        color = HexColor(player["color"])
        dark = HexColor(player["dark"])

        c.setFillColor(dark)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y_cursor + token_r + 8, f"{player['name']} Cars")

        for i in range(4):
            cx = margin + token_r + i * col_gap
            cy = y_cursor

            c.setDash(3, 3)
            c.setStrokeColor(HexColor("#AAAAAA"))
            c.setLineWidth(0.5)
            c.circle(cx, cy, token_r + 3, fill=0, stroke=1)
            c.setDash()

            c.setFillColor(color)
            c.setStrokeColor(dark)
            c.setLineWidth(2)
            c.circle(cx, cy, token_r, fill=1, stroke=1)

            c.setStrokeColor(white)
            c.setLineWidth(1.5)
            c.circle(cx, cy, token_r * 0.7, fill=0, stroke=1)

        y_cursor -= token_r * 2 + gap + 20

    c.setFont("Helvetica", 7)
    c.drawString(margin, 30, "Cut along dashed circles. Place on board cells.")
    c.showPage()
    c.save()
    print("Wrote", pdf_path)


# ── Main ─────────────────────────────────────────────────────────

def main():
    ensure_output_dir()
    build_board_pdf()
    build_cards_pdf()
    build_rules_pdf()
    build_cars_pdf()
    print("Done. Outputs in:", OUT_DIR)


if __name__ == "__main__":
    main()
