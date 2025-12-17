

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from sudoku_csp import SudokuCSP, solve_puzzle


class SudokuGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sudoku (CSP)")

        self.entries: list[list[tk.Entry]] = []
        self.solution_grid: list[list[int]] | None = None
        self.autoplay_running: bool = False
        self.status_var = tk.StringVar(value="Enter a puzzle, then click Next Step.")

        container = tk.Frame(root, padx=10, pady=10)
        container.pack()

        self._build_grid(container)
        self._build_controls(root)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_grid(self, parent: tk.Widget) -> None:
        for r in range(9):
            row_entries: list[tk.Entry] = []
            for c in range(9):
                frame = tk.Frame(
                    parent,
                    bd=1,
                    relief="solid",
                    highlightthickness=0,
                )

                # Thicker borders between 3x3 blocks
                top = 2 if r in (0, 3, 6) else 1
                left = 2 if c in (0, 3, 6) else 1
                bottom = 2 if r == 8 else 1
                right = 2 if c == 8 else 1

                frame.grid(
                    row=r,
                    column=c,
                    padx=(left, right),
                    pady=(top, bottom),
                )

                entry = tk.Entry(
                    frame,
                    width=2,
                    justify="center",
                    font=("Segoe UI", 14),
                )
                entry.pack(padx=1, pady=1)
                row_entries.append(entry)
            self.entries.append(row_entries)

    def _build_controls(self, parent: tk.Widget) -> None:
        btn_frame = tk.Frame(parent, pady=10)
        btn_frame.pack()

        step_btn = tk.Button(btn_frame, text="Next Step", command=self.on_next_step)
        step_btn.grid(row=0, column=0, padx=5)

        start_btn = tk.Button(btn_frame, text="Start Auto-Play", command=self.on_start_autoplay)
        start_btn.grid(row=0, column=1, padx=5)

        clear_btn = tk.Button(btn_frame, text="Clear", command=self.on_clear)
        clear_btn.grid(row=0, column=2, padx=5)

        sample_btn = tk.Button(btn_frame, text="Load Sample", command=self.on_load_sample)
        sample_btn.grid(row=0, column=3, padx=5)

        status_label = tk.Label(parent, textvariable=self.status_var, anchor="w")
        status_label.pack(pady=(0, 5), padx=10, fill="x")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_puzzle_from_ui(self) -> str:
        chars: list[str] = []
        for r in range(9):
            for c in range(9):
                text = self.entries[r][c].get().strip()
                if text in ("", ".", "0"):
                    chars.append(".")
                elif text.isdigit() and text != "0":
                    chars.append(text[0])
                else:
                    # Invalid char, treat as empty
                    chars.append(".")
        return "".join(chars)

    def _write_grid_to_ui(self, grid: list[list[int]]) -> None:
        for r in range(9):
            for c in range(9):
                val = grid[r][c]
                self.entries[r][c].delete(0, tk.END)
                if val != 0:
                    self.entries[r][c].insert(0, str(val))

    def _read_grid_from_ui(self) -> list[list[int]]:
        grid: list[list[int]] = [[0 for _ in range(9)] for _ in range(9)]
        for r in range(9):
            for c in range(9):
                text = self.entries[r][c].get().strip()
                if text.isdigit() and text != "0":
                    grid[r][c] = int(text[0])
        return grid

    def _load_puzzle_string(self, puzzle: str) -> None:
        try:
            csp = SudokuCSP.from_string(puzzle)
        except ValueError as exc:
            messagebox.showerror("Invalid puzzle", str(exc))
            return
        grid = csp.to_grid()
        self._write_grid_to_ui(grid)

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def on_next_step(self) -> None:
        if self.autoplay_running:
            return

        puzzle = self._read_puzzle_from_ui()

        # If we don't have a cached solution (or user changed the grid), recompute.
        if self.solution_grid is None:
            try:
                solution_csp = solve_puzzle(puzzle)
            except ValueError as exc:
                messagebox.showerror("Invalid puzzle", str(exc))
                self.status_var.set("Invalid puzzle; please check your entries.")
                return

            if solution_csp is None:
                messagebox.showinfo("No solution", "No solution found for this puzzle.")
                self.status_var.set("No solution for this puzzle.")
                return

            self.solution_grid = solution_csp.to_grid()
            self.status_var.set("Solution computed. Applying steps...")

        if self.solution_grid is None:
            self.status_var.set("No solution available.")
            return

        current_grid = self._read_grid_from_ui()

        # Find the next cell that differs from the solution.
        for r in range(9):
            for c in range(9):
                target = self.solution_grid[r][c]
                if current_grid[r][c] != target:
                    # Fill this cell as the next AI step.
                    self.entries[r][c].delete(0, tk.END)
                    self.entries[r][c].insert(0, str(target))
                    self.status_var.set(
                        f"Filled row {r + 1}, col {c + 1} with {target}."
                    )
                    return

        # If we reach here, the grid already matches the solution.
        self.status_var.set("Puzzle is already solved.")

    def _ensure_solution(self) -> bool:
        """Compute and cache solution_grid based on current UI if needed."""
        puzzle = self._read_puzzle_from_ui()
        if self.solution_grid is not None:
            return True
        try:
            solution_csp = solve_puzzle(puzzle)
        except ValueError as exc:
            messagebox.showerror("Invalid puzzle", str(exc))
            self.status_var.set("Invalid puzzle; please check your entries.")
            return False

        if solution_csp is None:
            messagebox.showinfo("No solution", "No solution found for this puzzle.")
            self.status_var.set("No solution for this puzzle.")
            return False

        self.solution_grid = solution_csp.to_grid()
        return True

    def _autoplay_step(self) -> None:
        if not self.autoplay_running:
            return
        if self.solution_grid is None:
            self.autoplay_running = False
            return

        current_grid = self._read_grid_from_ui()

        for r in range(9):
            for c in range(9):
                target = self.solution_grid[r][c]
                if current_grid[r][c] != target:
                    self.entries[r][c].delete(0, tk.END)
                    self.entries[r][c].insert(0, str(target))
                    self.status_var.set(
                        f"Auto-play: filled row {r + 1}, col {c + 1} with {target}."
                    )
                    # Schedule next step
                    self.root.after(120, self._autoplay_step)
                    return

        self.autoplay_running = False
        self.status_var.set("Auto-play finished: puzzle solved.")

    def on_start_autoplay(self) -> None:
        if self.autoplay_running:
            return
        if not self._ensure_solution():
            return
        self.autoplay_running = True
        self.status_var.set("Auto-play started...")
        self._autoplay_step()

    def on_clear(self) -> None:
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)
        self.solution_grid = None
        self.autoplay_running = False
        self.status_var.set("Board cleared. Enter a puzzle, then click Next Step or Start Auto-Play.")

    def on_load_sample(self) -> None:
        sample = "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3.."
        self._load_puzzle_string(sample)
        self.solution_grid = None
        self.autoplay_running = False
        self.status_var.set("Sample loaded. Click Next Step or Start Auto-Play to see AI moves.")


def main() -> None:
    root = tk.Tk()
    SudokuGUI(root)
    root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()


