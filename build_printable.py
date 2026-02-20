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
         "text": "Move a car from pit row to your START space OR move a car 1 space forward."},
    2:  {"label": "2",  "accent": "#1565C0",
         "text": "Move a car on the track 2 spaces forward."},
    3:  {"label": "3",  "accent": "#2E7D32",
         "text": "Move a car on the track 3 spaces forward AND take another ticket."},
    4:  {"label": "4",  "accent": "#1565C0",
         "text": "Move a car on the track 4 spaces forward."},
    5:  {"label": "5",  "accent": "#1565C0",
         "text": "Move a car on the track 5 spaces forward."},
    6:  {"label": "6",  "accent": "#E65100",
         "text": "Move a car 6 spaces forward OR 9 spaces backward."},
    7:  {"label": "7",  "accent": "#6A1B9A",
         "text": "Move a car 7 spaces forward OR switch one of your cars with another player's car."},
    8:  {"label": "8",  "accent": "#00695C",
         "text": "Move a car 8 spaces forward OR split the move between two cars."},
    9:  {"label": "9",  "accent": "#E65100",
         "text": "Move a car 9 spaces forward OR 6 spaces backward."},
    10: {"label": "10", "accent": "#1565C0",
         "text": "Move a car on the track 10 spaces forward."},
    11: {"label": "11", "accent": "#283593",
         "text": "Move a car 11 spaces forward OR 1 space backward."},
    12: {"label": "12", "accent": "#F9A825",
         "text": "Move a car from pit row to your START space OR move 12 spaces forward."},
    "bumpem": {"label": "BUMP\n'EM!", "accent": "#C62828",
         "text": "Take a car from your pit row and bump another player's car back to their pit row."},
}

# ── Board constants ──────────────────────────────────────────────
BOARD_SIZE = 20 * inch
BOARD_MARGIN = 1 * inch
GRID_SIZE = 16  # 16×16 grid for cross/Parcheesi layout
NUM_CELLS = 60
CELLS_PER_SIDE = 15
CELL_SIZE = (BOARD_SIZE - 2 * BOARD_MARGIN) / GRID_SIZE  # square cells, 81pt each

# Player definitions — 0-based indices, display = idx+1 (cells 1-60)
# Board positions: Red=TL, Green=TR, Yellow=BR, Blue=BL
# Track: clockwise around cross-shaped board
# home_entry = turn cell just before START = (start - 1) % 60
PLAYERS = [
    {"name": "Red",    "color": "#C62828", "light": "#FFCDD2", "dark": "#B71C1C",
     "start": 0, "home_entry": 59},
    {"name": "Green",  "color": "#2E7D32", "light": "#C8E6C9", "dark": "#1B5E20",
     "start": 15, "home_entry": 14},
    {"name": "Yellow", "color": "#F9A825", "light": "#FFF9C4", "dark": "#F57F17",
     "start": 30, "home_entry": 29},
    {"name": "Blue",   "color": "#1565C0", "light": "#BBDEFB", "dark": "#0D47A1",
     "start": 45, "home_entry": 44},
]

TURBO_CELLS = {3, 18, 33, 48}
OIL_SLICK_CELLS = {11, 26, 41, 56}
START_CELLS = {p["start"] for p in PLAYERS}
HOME_ENTRY_CELLS = {p["home_entry"] for p in PLAYERS}
OIL_SLICK_END_CELLS = {(p["start"] + 1) % NUM_CELLS for p in PLAYERS}

# 60-cell track path as (col, row) grid positions — clockwise
# Side 0 (Top arm): up col 6, tip row 15, down col 9, turn at (9,9)
# Side 1 (Right arm): right row 9, tip col 15, left row 6, turn at (9,6)
# Side 2 (Bottom arm): down col 9, tip row 0, up col 6, turn at (6,6)
# Side 3 (Left arm): left row 6, tip col 0, right row 9, turn at (6,9)
TRACK_CELLS = [
    # Side 0 — Top arm (cells 0–14)
    (6,10), (6,11), (6,12), (6,13), (6,14), (6,15),   # up col 6
    (7,15), (8,15),                                      # tip row 15
    (9,15), (9,14), (9,13), (9,12), (9,11), (9,10),    # down col 9
    (9,9),                                                # turn
    # Side 1 — Right arm (cells 15–29)
    (10,9), (11,9), (12,9), (13,9), (14,9), (15,9),    # right row 9
    (15,8), (15,7),                                      # tip col 15
    (15,6), (14,6), (13,6), (12,6), (11,6), (10,6),    # left row 6
    (9,6),                                                # turn
    # Side 2 — Bottom arm (cells 30–44)
    (9,5), (9,4), (9,3), (9,2), (9,1), (9,0),          # down col 9
    (8,0), (7,0),                                        # tip row 0
    (6,0), (6,1), (6,2), (6,3), (6,4), (6,5),          # up col 6
    (6,6),                                                # turn
    # Side 3 — Left arm (cells 45–59)
    (5,6), (4,6), (3,6), (2,6), (1,6), (0,6),          # left row 6
    (0,7), (0,8),                                        # tip col 0
    (0,9), (1,9), (2,9), (3,9), (4,9), (5,9),          # right row 9
    (6,9),                                                # turn
]

# Arrow direction per cell: 0=→, 1=↓, 2=←, 3=↑
TRACK_ARROWS = [
    # Side 0 — Top arm
    3, 3, 3, 3, 3, 3,   # up
    0, 0,                 # tip right
    1, 1, 1, 1, 1, 1,   # down
    0,                    # turn → into right arm
    # Side 1 — Right arm
    0, 0, 0, 0, 0, 0,   # right
    1, 1,                 # tip down
    2, 2, 2, 2, 2, 2,   # left
    1,                    # turn ↓ into bottom arm
    # Side 2 — Bottom arm
    1, 1, 1, 1, 1, 1,   # down
    2, 2,                 # tip left
    3, 3, 3, 3, 3, 3,   # up
    2,                    # turn ← into left arm
    # Side 3 — Left arm
    2, 2, 2, 2, 2, 2,   # left
    3, 3,                 # tip up
    0, 0, 0, 0, 0, 0,   # right
    3,                    # turn ↑ into top arm
]

# Home stretch cells per player: 4 cells going away from center through arm
HOME_CELLS = {
    "Red":    [(7, 10), (7, 11), (7, 12), (7, 13)],   # up through col 7 of top arm
    "Green":  [(10, 8), (11, 8), (12, 8), (13, 8)],   # right through row 8 of right arm
    "Yellow": [(8, 5),  (8, 4),  (8, 3),  (8, 2)],    # down through col 8 of bottom arm
    "Blue":   [(5, 7),  (4, 7),  (3, 7),  (2, 7)],    # left through row 7 of left arm
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


# ── Board drawing ────────────────────────────────────────────────


def _draw_cross_band(c):
    """Draw the track as a cross-shaped loop (only the track path, not solid arms)."""
    c.setFillColor(TRACK_GRAY)
    # Top arm: left strip (col 6) + right strip (col 9) + tip connection (cols 7-8)
    x, y = _grid_xy(6, 10)
    c.rect(x, y, CELL_SIZE, 6 * CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(9, 10)
    c.rect(x, y, CELL_SIZE, 6 * CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(7, 15)
    c.rect(x, y, 2 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    # Right arm: top strip (row 9) + bottom strip (row 6) + tip connection (rows 7-8)
    x, y = _grid_xy(10, 9)
    c.rect(x, y, 6 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(10, 6)
    c.rect(x, y, 6 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(15, 7)
    c.rect(x, y, CELL_SIZE, 2 * CELL_SIZE, fill=1, stroke=0)
    # Bottom arm: right strip (col 9) + left strip (col 6) + tip connection (cols 7-8)
    x, y = _grid_xy(9, 0)
    c.rect(x, y, CELL_SIZE, 6 * CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(6, 0)
    c.rect(x, y, CELL_SIZE, 6 * CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(7, 0)
    c.rect(x, y, 2 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    # Left arm: bottom strip (row 6) + top strip (row 9) + tip connection (rows 7-8)
    x, y = _grid_xy(0, 6)
    c.rect(x, y, 6 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(0, 9)
    c.rect(x, y, 6 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    x, y = _grid_xy(0, 7)
    c.rect(x, y, CELL_SIZE, 2 * CELL_SIZE, fill=1, stroke=0)
    # Center square perimeter — connects all 4 arms into a visible loop
    # Top edge (row 9, cols 6-9)
    x, y = _grid_xy(6, 9)
    c.rect(x, y, 4 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    # Bottom edge (row 6, cols 6-9)
    x, y = _grid_xy(6, 6)
    c.rect(x, y, 4 * CELL_SIZE, CELL_SIZE, fill=1, stroke=0)
    # Left edge (col 6, rows 7-8)
    x, y = _grid_xy(6, 7)
    c.rect(x, y, CELL_SIZE, 2 * CELL_SIZE, fill=1, stroke=0)
    # Right edge (col 9, rows 7-8)
    x, y = _grid_xy(9, 7)
    c.rect(x, y, CELL_SIZE, 2 * CELL_SIZE, fill=1, stroke=0)


def _draw_arrow(c, cx, cy, direction, size=7):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(-90 * direction)
    p = c.beginPath()
    p.moveTo(size, 0)
    p.lineTo(-size * 0.5, size * 0.55)
    p.lineTo(-size * 0.5, -size * 0.55)
    p.close()
    c.setFillColor(HexColor("#BDBDBD"))
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
            fill = HexColor("#90A4AE")
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
        if idx in OIL_SLICK_CELLS:
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
            c.setFillColor(HexColor("#455A64"))
            c.setFont("Helvetica-Bold", 5.5)
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
                # FINISH marker: circle + text
                c.setStrokeColor(white)
                c.setLineWidth(2)
                c.circle(cell_cx, cell_cy, CELL_SIZE * 0.35, fill=0, stroke=1)
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(cell_cx, cell_cy - 3, "FINISH")
            else:
                num = player["home_entry"] + i + 2  # continue numbering from track
                c.setFont("Helvetica-Bold", 15)
                c.drawCentredString(cell_cx, cell_cy - 6, str(num))


def _draw_pit_rows(c):
    """Draw 2×2 colored base areas in the board corners (between cross arms)."""
    # Center each 2×2 base in the 6×6 corner area
    base_positions = {
        "Red":    (2, 12),   # TL corner, centered
        "Green":  (12, 12),  # TR corner, centered
        "Yellow": (12, 2),   # BR corner, centered
        "Blue":   (2, 2),    # BL corner, centered
    }
    base_size = 2 * CELL_SIZE

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
    """Draw logo in the center 2×2 cells: grid (7,7)-(8,8)."""
    x, y = _grid_xy(7, 7)
    size = 2 * CELL_SIZE
    cx = x + size / 2
    cy = y + size / 2
    radius = size * 0.45
    c.setFillColor(HexColor("#1B5E20"))
    c.setStrokeColor(HexColor("#FDD835"))
    c.setLineWidth(4)
    c.circle(cx, cy, radius, fill=1, stroke=1)
    c.setStrokeColor(HexColor("#FB8C00"))
    c.setLineWidth(2)
    c.circle(cx, cy, radius * 0.85, fill=0, stroke=1)
    c.setFillColor(HexColor("#FDD835"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(cx, cy + 6, "BUMP")
    c.drawCentredString(cx, cy - 18, "'EM!")


def build_board_pdf():
    ensure_output_dir()
    pdf_path = OUT_DIR / "board.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(BOARD_SIZE, BOARD_SIZE))
    # 1. Background
    c.setFillColor(BOARD_BACKGROUND)
    c.rect(0, 0, BOARD_SIZE, BOARD_SIZE, fill=1, stroke=0)
    # 2. Player base areas (colored corners, behind the cross)
    _draw_pit_rows(c)
    # 3. Cross-shaped track band (gray)
    _draw_cross_band(c)
    # 4. Individual track cells
    _draw_track_cells(c)
    # 5. Home stretches
    _draw_home_stretches(c)
    # 6. Center logo
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


CARD_ACCENT = HexColor("#1B5E20")  # uniform accent color for all cards


def _draw_vector_card(c, x, y, value):
    info = CARD_INFO[value]
    accent = CARD_ACCENT
    text = info["text"]

    c.setFillColor(white)
    c.roundRect(x, y, CARD_W, CARD_H, 6, fill=1, stroke=0)

    c.setStrokeColor(accent)
    c.setLineWidth(2.5)
    c.roundRect(x + 3, y + 3, CARD_W - 6, CARD_H - 6, 5, fill=0, stroke=1)

    bar_h = 28
    c.setFillColor(accent)
    c.rect(x + 3, y + CARD_H - 3 - bar_h, CARD_W - 6, bar_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + CARD_W / 2, y + CARD_H - bar_h + 6, "BUMP'EM")

    c.setFillColor(accent)
    c.rect(x + 3, y + 3, CARD_W - 6, 10, fill=1, stroke=0)

    center_y = y + CARD_H * 0.55
    if value == "bumpem":
        c.setFillColor(accent)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(x + CARD_W / 2, center_y + 10, "BUMP")
        c.drawCentredString(x + CARD_W / 2, center_y - 18, "'EM!")
    else:
        nr = 26
        c.setFillColor(accent)
        c.circle(x + CARD_W / 2, center_y + 4, nr, fill=1, stroke=0)
        c.setFillColor(white)
        font_size = 30 if value < 10 else 24
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(x + CARD_W / 2, center_y - 6, str(value))

    text_top = y + CARD_H * 0.33
    text_w = CARD_W - 24
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 8.5)
    lines = _wrap(text, "Helvetica", 8.5, text_w, c)
    ly = text_top
    for line in lines:
        c.drawCentredString(x + CARD_W / 2, ly, line)
        ly -= 11


def _draw_card_back(c, x, y):
    c.setFillColor(HexColor("#1B5E20"))
    c.roundRect(x, y, CARD_W, CARD_H, 6, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#FDD835"))
    c.setLineWidth(2)
    c.roundRect(x + 6, y + 6, CARD_W - 12, CARD_H - 12, 5, fill=0, stroke=1)
    c.setStrokeColor(HexColor("#FB8C00"))
    c.setLineWidth(1)
    c.roundRect(x + 12, y + 12, CARD_W - 24, CARD_H - 24, 4, fill=0, stroke=1)
    cx, cy = x + CARD_W / 2, y + CARD_H / 2
    c.setFillColor(HexColor("#FDD835"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(cx, cy + 12, "BUMP")
    c.drawCentredString(cx, cy - 12, "'EM!")
    for i, col in enumerate(RAINBOW):
        c.setFillColor(col)
        a = i * 60
        c.circle(cx + 35 * math.cos(math.radians(a)),
                 cy - 32 + 35 * math.sin(math.radians(a)), 3, fill=1, stroke=0)


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
    ticket(1, "PIT ROW \u2192 START space  OR  move a car 1 space forward.")
    ticket(2, "Move a car 2 spaces forward.")
    ticket(3, "Move a car 3 spaces forward AND draw another ticket.")
    ticket(4, "Move a car 4 spaces forward.")
    ticket(5, "Move a car 5 spaces forward.")
    ticket(6, "Move a car 6 spaces forward OR 9 spaces backward.")
    ticket(7, "Move 7 forward OR swap one of your cars with an opponent's.")
    ticket(8, "Move 8 forward OR split the move between two cars.")
    ticket(9, "Move a car 9 spaces forward OR 6 spaces backward.")
    ticket(10, "Move a car 10 spaces forward.")
    ticket(11, "Move a car 11 spaces forward OR 1 space backward.")
    ticket(12, "PIT ROW \u2192 START space  OR  move a car 12 spaces forward.")
    ticket("BUMP'EM", "Move a car from PIT ROW and bump an opponent's car to their pit row.")

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
