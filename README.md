## Sudoku-game

Sudoku implementation using **CSP (Constraint Satisfaction Problem)** techniques.

### Overview

- **Variables**: each cell \((r, c)\) in the 9×9 Sudoku grid.
- **Domains**: a set of possible digits \(\{1..9\}\) for each cell (singletons for given clues).
- **Constraints**: all-different on each row, column, and 3×3 sub-grid, enforced through:
  - **AC-3** arc consistency on binary constraints between peer cells.
  - **Backtracking search** with:
    - **MRV** (Minimum Remaining Values) variable ordering,
    - **Least-constraining value** heuristic,
    - **Forward checking** to prune domains of neighboring cells.

The core logic lives in `sudoku_csp.py`, and a small CLI interface is provided in `play.py`.

### Requirements

- Python 3.9 or later.
- No external libraries are required (see `requirements.txt`).

### Running the game / solver

From the project directory:

```bash
python play.py --puzzle "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3.."
```

You can also read a puzzle from a file:

```bash
python play.py --file puzzle.txt
```

Where `puzzle.txt` contains one line with 81 characters, using digits `1-9` for clues and `0` or `.` for empty cells.

If you run without arguments:

```bash
python play.py
```

you will be prompted to enter 9 lines of 9 characters each, representing the puzzle.

### CSP internals (short version)

- **Representation**:
  - Each cell is a key `(row, col)` in a `domains` dictionary.
  - `PEERS[(r, c)]` is the set of all cells sharing a row, column, or box with `(r, c)`.
- **AC-3**:
  - Initializes a queue with all arcs `(Xi, Xj)` where `Xj` is a peer of `Xi`.
  - For each arc, if `Xj` is singleton `{v}`, that value is removed from `Xi`’s domain.
  - If any domain becomes empty, the puzzle is inconsistent.
- **Search**:
  - Selects an unassigned variable using MRV.
  - Orders candidate values by how few domain values they remove from peers (least-constraining value).
  - Applies forward checking to propagate choices and recurses.
