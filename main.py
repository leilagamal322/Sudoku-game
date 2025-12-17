

from __future__ import annotations

from typing import Callable, List

import matplotlib.pyplot as plt

from sudoku_csp import SudokuCSP


def make_step_visualizer() -> Callable[[int, List[List[int]]], None]:
    
    plt.ion()
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("Sudoku CSP Search")

    data = [[0 for _ in range(9)] for _ in range(9)]
    im = ax.imshow(data, cmap="Pastel1", vmin=0, vmax=9)

    for i in range(10):
        lw = 2 if i % 3 == 0 else 0.5
        ax.axhline(i - 0.5, color="black", linewidth=lw)
        ax.axvline(i - 0.5, color="black", linewidth=lw)

    ax.set_xticks([])
    ax.set_yticks([])

    texts = [
        [ax.text(c, r, "", ha="center", va="center", fontsize=14) for c in range(9)]
        for r in range(9)
    ]

    def step_visualizer(step: int, grid: List[List[int]]) -> None:
        ax.set_title(f"Sudoku CSP search – step {step}")
        im.set_data(grid)
        for r in range(9):
            for c in range(9):
                v = grid[r][c]
                texts[r][c].set_text(str(v) if v != 0 else "")
        plt.pause(0.001)

    # Return the callable that matches the solver's step_callback signature
    return step_visualizer


def main() -> None:
    hard_puzzle = (
        "100007090"
        "030020008"
        "009600500"
        "005300900"
        "010080002"
        "600004000"
        "300000010"
        "040000007"
        "007000300"
    )

    print("Initial puzzle:\n")
    initial_csp = SudokuCSP.from_string(hard_puzzle)
    print(initial_csp.pretty())

    print("\nSolving using CSP (AC-3 + backtracking)...")
    print("Visualizing the search every 1000 steps with matplotlib.\n")

    step_visualizer = make_step_visualizer()
    solution_csp = initial_csp.solve(step_callback=step_visualizer, step_interval=1000)

    if solution_csp is None:
        print("No solution found for this puzzle.")
        plt.ioff()
        plt.show()
        return

    print("\nFinal solution:\n")
    print(solution_csp.pretty())

    final_grid = solution_csp.to_grid()
    step_visualizer(0, final_grid)

    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()


