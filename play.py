

import argparse
from pathlib import Path
from typing import Optional

from sudoku_csp import SudokuCSP, solve_puzzle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sudoku game using CSP techniques")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--puzzle",
        type=str,
        help="81-character puzzle string (use 0 or . for empty cells)",
    )
    group.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing a single 81-character puzzle line",
    )
    return parser.parse_args()


def read_puzzle_from_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    # Use first non-empty line as puzzle
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    raise SystemExit("No non-empty line found in puzzle file")


def read_puzzle_interactively() -> str:
    print("Enter the Sudoku puzzle as 9 lines of 9 characters each.")
    print("Use digits 1-9 for clues, and 0 or . for empty cells.")
    rows = []
    for r in range(9):
        while True:
            line = input(f"Row {r + 1}: ").strip()
            if len(line) != 9:
                print("Please enter exactly 9 characters.")
                continue
            rows.append(line)
            break
    return "".join(rows)


def main() -> None:
    args = parse_args()

    if args.puzzle:
        puzzle = args.puzzle
    elif args.file:
        puzzle = read_puzzle_from_file(args.file)
    else:
        puzzle = read_puzzle_interactively()

    print("\nOriginal puzzle:\n")
    csp = SudokuCSP.from_string(puzzle)
    print(csp.pretty())

    print("\nSolving with CSP (AC-3 + backtracking)...\n")
    solution: Optional[SudokuCSP] = csp.solve()
    if solution is None:
        print("No solution found. The puzzle may be unsatisfiable.")
        return

    print("Solution:\n")
    print(solution.pretty())


if __name__ == "__main__":
    main()


