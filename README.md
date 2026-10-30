# Bump'em — Printable Physical Edition

A printable board game based on the Bump'em bumper car game from Hoyle Puzzle Games.

## What's Included

The build script generates 4 printable PDFs:

- **board.pdf** — 20" × 20" game board (print as poster or tile across multiple pages)
- **cards.pdf** — 54 ticket cards (poker size 2.5" × 3.5"), 9 per page with cut lines, plus card backs
- **rules.pdf** — Compact one-page rule sheet
- **cars.pdf** — 16 car tokens (4 per player color) with cut lines

## Requirements

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager

## Build

```bash
uv run python build_printable.py
```

Output goes to the `output/` directory.

## How to Play

### Setup
Each player (2–4) picks a color (Red, Green, Light Blue, Yellow) and places 4 car tokens in their PIT ROW on the board. Shuffle the 54-card ticket deck face-down.

### Goal
Move all 4 of your cars from your PIT ROW, around the track, and into your home stretch to reach FINISH.

### On Your Turn
Draw 1 ticket from the deck and follow its instruction. Reshuffle when the deck runs out.

### Special Spaces
- **TURBO** — If your car is bumped on a TURBO space, it teleports to the next TURBO cell instead of going back to pit row
- **OIL SLICK** — When you pass through an OIL SLICK space, you bump all cars on your remaining path back to their pit rows

### Bumping
Land on an opponent's car to bump it back to their pit row. The BUMP'EM ticket lets you take a car from your pit row and use it to bump any opponent's car.

## Project Structure

```
build_printable.py    — Main build script (Python + reportlab)
screenshots/          — Original game screenshots (board, tickets, logo)
output/               — Generated PDFs (created by build script)
CLAUDE.md             — Development notes and design spec
```

## Filing an issue (for AI agents and humans)

Open issues through the [issue forms](https://github.com/mnaoumov/bump-em-physical-edition/issues/new/choose), not as blank issues.

Filing from the CLI or the API (`gh issue create --body`, or an AI agent filing for you) skips the form, and `gh issue create --template` cannot load an issue form. In that case, open the matching form in [`.github/ISSUE_TEMPLATE/`](https://github.com/mnaoumov/bump-em-physical-edition/tree/HEAD/.github/ISSUE_TEMPLATE), copy every field as a `### <label>` heading in the form's order, and fill in each one. Always state the version you used and your operating system.
