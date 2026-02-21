# Bump'em Physical Edition

Build script (`build_printable.py`) generates printable PDFs: board, cards, rules, cars.
Uses Python + reportlab. Run with: `uv run python build_printable.py`

## User Preferences
- **No cryptic variable names**: use full words (padding, extension, radius — not pad, ext, r)
- **No unnecessary abbreviations**: in local variables too
- Board is 20"×20" single page for poster printing

---

## Board Track Loop Structure (from board.png + user sketch)

The track is a **self-crossing loop** that wraps around all 4 player bases.

### Key concept: 4 connected rectangular loops

Each player base sits inside a rectangular track loop. The 4 loops connect into
ONE continuous path. At each junction between two adjacent bases, the tracks
**cross each other** (self-intersecting).

The track visits all 4 bases in sequence (**Red → Blue → Yellow → Green → Red**),
going clockwise around each base. The progression between bases is
counterclockwise around the board center (down, right, up, left).
At each of the 2 junctions, the path crosses over itself.

### Cell count
- 60 cells total, 15 per base section
- Each base section: ~12 cells going around the base + ~3 cells for the crossing transition
- 4 crossing cells are shared between adjacent sections

### Cell numbering grid (from screenshot)

The track cell numbers laid out on an 11×11 spatial grid (`.` = empty / base interior):

```
55  56  57  58  59   .  37  38   .  39  40
54   .   .   .  60   .  36   .   .   .  41
 .   .   .   .   1   .  35   .   .   .  42
53   .   .   .   2   .  34   .   .   .  43
52  51  50  49   .  48   .  47  46  45  44
 .   .   .   .   3   .  33   .   .   .   .
14  15  16  17   .  18   .  19  20  21  22
13   .   .   .   4   .  32   .   .   .  23
12   .   .   .   5   .  31   .   .   .   .
11   .   .   .   6   .  30   .   .   .  24
10   9   .   8   7   .  29  28  27  26  25
```

#### Path direction (cell number order)

- **Red (TL) — Mihuil:** 55→56→57→58→59→60→1→2 (down right side), then crosses to Blue
- **Blue (BL) — Roswell:** 3→4→5→6→7→8→9→10→11→12→13→14→15→16→17→18 (around base), then crosses to Green
- **Green (TR) — Capt. Scurvy:** (continues from crossing) →33→34→35→36→37→38→39→40→41→42→43→44→45→46→47→48 (around base), then crosses back to Red
- **Yellow (BR) — Jack:** 19→20→21→22→23→24→25→26→27→28→29→30→31→32 (around base)

#### Crossing junctions (where vertical & horizontal channels intersect)

- **Top crossing** (between Red & Green): around cells 48 / 3 area (center row 4)
- **Bottom crossing** (between Blue & Yellow): around cells 18 / 33 area (center row 6)
- **Left crossing** (between Red & Blue): around cells 2-3 / 48-49 area (center col 4)
- **Right crossing** (between Green & Yellow): around cells 33 / 47 area (center col 6)

#### Cell roles (1–60)

| Cell | Role             | Player |
| ---- | ---------------- | ------ |
| 1    | Start            | Red    |
| 2    | End of oil slick | Red    |
| 4    | Turbo            | Common |
| 12   | Oil slick        | Blue   |
| 14   | Entrance to home | Blue   |
| 16   | Start            | Blue   |
| 17   | End of oil slick | Blue   |
| 19   | Turbo            | Common |
| 27   | Oil slick        | Yellow |
| 29   | Entrance to home | Yellow |
| 31   | Start            | Yellow |
| 32   | End of oil slick | Yellow |
| 34   | Turbo            | Common |
| 42   | Oil slick        | Green  |
| 44   | Entrance to home | Green  |
| 46   | Start            | Green  |
| 47   | End of oil slick | Green  |
| 49   | Turbo            | Common |
| 57   | Oil slick        | Red    |
| 59   | Entrance to home | Red    |

### Grid (16×16)
- CELL_SIZE = (BOARD_SIZE - 2*MARGIN) / GRID_SIZE
- Base areas (with track around them):
  - Red (TL): cols 0-5, rows 10-15
  - Green (TR): cols 10-15, rows 10-15
  - Yellow (BR): cols 10-15, rows 0-5
  - Blue (BL): cols 0-5, rows 0-5
- Connection channels: cols 6-9 (vertical), rows 6-9 (horizontal)
- Crossings at center area where channels intersect

### Player layout
- Red = TL, Green = TR, Yellow = BR, Blue = BL
- Home stretches go from each base toward the center
- Pit rows (2×2) centered inside each base area
- **No character names on board** — use quadrant colors only

### Per-quadrant elements
- Character portrait in a square frame
- Path in player's color (red / green / light blue / yellow)
- Labels: "START", "FINISH" (checkered flag)
- Direction: Small white triangular arrows along the path
- Special spaces: "Oil Slick" on outer curve of each quadrant; "TURBO" on straight connecting segments
- Tokens: Four small oval tokens per player (color-matched) below the portrait

### Board visual design
- **Background:** Dark green with subtle interwoven fabric/mesh texture
- **Outer border:** Thick frame with gradient: red → orange → yellow → green → light blue → purple (neon/glow effect)
- **Track:** White track with grey borders; central path connects four quadrants
- **Typography:** Simple sans-serif for START, FINISH, Oil Slick, TURBO
- **Colors:** Saturated red, green, light blue, yellow for paths; rainbow gradient on outer board border

---

## Deck Composition (54 cards)

| Card | Count |
|------|-------|
| 1 | 5 |
| 2–11 | 4 each |
| 12 | 5 |
| BUMP'EM | 4 |

Reshuffle when deck is exhausted.

## Ticket Rules (exact wording from in-game UI)

| # | Wording | Bold emphasis |
|---|---------|---------------|
| 1 | Move a car from pit row to your start space **OR** move a car on the track one space forward. | Move, OR, one space forward |
| 2 | Move a car on the track **two** spaces forward. | two |
| 3 | Move a car on the track **three spaces forward** **AND** take another **move ticket.** | three spaces forward, AND, move ticket |
| 4 | Move a car on the track **four** spaces forward. | four |
| 5 | Move a car on the track **five** spaces forward. | five |
| 6 | Move a car on the track **six spaces forward** **OR** **nine spaces backward.** | six spaces forward, OR, nine spaces backward |
| 7 | Move a car on the track **seven spaces forward** **OR** **switch one of your cars** with another player's car. | seven spaces forward, OR, switch one of your cars |
| 8 | Move a car on the track **eight spaces forward** **OR** split the move **between two cars.** | eight spaces forward, OR, between two cars |
| 9 | Move a car on the track **nine spaces forward** **OR** **six spaces backward.** | nine spaces forward, OR, six spaces backward |
| 10 | Move a car on the track ten spaces forward. | ten (optional bold) |
| 11 | Move a car on the track **eleven** spaces forward **OR** one space backward. | eleven, OR |
| 12 | Move a car from pit row to your start space **OR** move a car on the track **twelve spaces forward.** | OR, twelve spaces forward |
| BUMP'EM | Take a car from your **pit row** and **bump** another player's car. | pit row, bump |

---

## Card Visual Design

### Number tickets (1–12)

- **Orientation:** Portrait, standard playing-card proportion (2.5" × 3.5" poker size)
- **Corners:** Rounded
- **Border:** Multi-layer:
  - Outer: textured, braided-rope or metallic gold/bronze trim
  - Inner: thin dark line, then pale yellow-tan/beige band
- **Card background:** Off-white / cream / very pale yellow; subtle diagonal herringbone or chevron texture; slight distressed/aged look
- **Main number:** Large, bold, black/dark grey, sans-serif, centered in upper half
- **Background graphic:** Game logo (bumper cars) faded as watermark behind number, ~10-15% opacity, light purple-pink or very light grey
- **Instruction text:** Lower half, dark green/grey/black sans-serif; bold for numbers-in-words, "OR", "AND", key actions

### Color palette (number tickets)
- Card face: Off-white/cream/pale yellow (#F5F5DC–#FFF8E7)
- Border: Gold/bronze/tan (#C4A35A–#D2B48C); inner dark line (#2C1810–#3D2314)
- Number & text: Dark grey/black (#1A1A1A–#2D2D2D); tickets 1 & 12: dark green (#2D4A2D–#3D5C3D)
- Accent: "OR" in lime green on some cards (#8BC34A)
- Background graphic: Muted purple-pink, very low opacity (~10-15%)

### BUMP'EM card
- **Style:** Retro halftone; comic/poster feel
- **Background:** Light pinkish-purple with subtle distressed texture; halftone dot pattern
- **Border:** Thin dark (black or dark purple)
- **Content (top to bottom):**
  1. "BUMP 'EM!" — large, bold, cartoonish yellow with thick dark purple outline
  2. Game logo: two stylized bumper cars with white splatter; same logo as on number tickets but at full opacity
  3. "BUMP 'EM!" again — large, bold, dark purple
  4. Instruction text — smaller sans-serif, dark purple

### BUMP'EM color palette
- Background: Light pinkish-purple (#E6D5E6–#E8D8E8)
- Title yellow: #FFD54F–#FFEB3B with dark purple outline (#4A148C–#6A1B9A)
- Body text: Dark purple (#4A148C–#5E35B1)
- Bumper cars: Light grey/off-white (#E0E0E0–#F5F5F5)
- Splash/puddle: Light purple (#B39DDB–#CE93D8)

### Logo usage on cards
- **Logo asset:** `logo.png` in project root
- **BUMP'EM card:** Full logo at full opacity at top
- **Number tickets 1-12:** Same logo as faded watermark behind number, ~10-15% opacity, light purple-pink tint

---

## Components List

- 54-card ticket deck (poker size 2.5" × 3.5")
- Full printable board (20" × 20" poster)
- 16 printable car tokens (4 each: red, green, light blue, yellow)
- Oil slick & turbo markers
- Compact printable rule sheet

## Source Screenshots

All screenshots are in the `screenshots/` folder:
- `screenshots/board.png` — original game board
- `screenshots/board-with-numbers.png` — board with cell numbers overlaid
- `screenshots/ticket-1.png` through `screenshots/ticket-12.png` — ticket cards
- `screenshots/ticket-bumpem.png` — BUMP'EM card
- `screenshots/logo.png` — game logo asset
