from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

Coord = Tuple[int, int]  # (row, col) 0-based


def _all_coords() -> List[Coord]:
    return [(r, c) for r in range(9) for c in range(9)]


def _peers() -> Dict[Coord, Set[Coord]]:
    coords = _all_coords()
    peers: Dict[Coord, Set[Coord]] = {}

    for r, c in coords:
        row_peers = {(r, cc) for cc in range(9) if cc != c}
        col_peers = {(rr, c) for rr in range(9) if rr != r}
        br, bc = (r // 3) * 3, (c // 3) * 3
        box_peers = {
            (rr, cc)
            for rr in range(br, br + 3)
            for cc in range(bc, bc + 3)
            if (rr, cc) != (r, c)
        }
        peers[(r, c)] = row_peers | col_peers | box_peers
    return peers


PEERS: Dict[Coord, Set[Coord]] = _peers()


@dataclass
class SudokuCSP:
    domains: Dict[Coord, Set[int]]

    @classmethod
    def from_string(cls, puzzle: str) -> "SudokuCSP":
        cleaned = [ch for ch in puzzle if not ch.isspace()]
        if len(cleaned) != 81:
            raise ValueError("Puzzle must have exactly 81 non-whitespace characters")

        domains: Dict[Coord, Set[int]] = {}
        for idx, ch in enumerate(cleaned):
            r, c = divmod(idx, 9)
            if ch in "0.":
                domains[(r, c)] = set(range(1, 10))
            elif ch.isdigit() and ch != "0":
                val = int(ch)
                if not 1 <= val <= 9:
                    raise ValueError(f"Invalid digit {ch} at position {idx}")
                domains[(r, c)] = {val}
            else:
                raise ValueError(f"Invalid character {ch!r} in puzzle")

        csp = cls(domains)
        if not csp.ac3():
            raise ValueError("Puzzle is immediately inconsistent under AC-3")
        return csp

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def is_solved(self) -> bool:
        return all(len(d) == 1 for d in self.domains.values()) and self._constraints_satisfied()

    def _constraints_satisfied(self) -> bool:
        for (r, c), dom in self.domains.items():
            if len(dom) != 1:
                continue
            val = next(iter(dom))
            for pr, pc in PEERS[(r, c)]:
                pdom = self.domains[(pr, pc)]
                if len(pdom) == 1 and next(iter(pdom)) == val:
                    return False
        return True

    def to_grid(self) -> List[List[int]]:
        grid = [[0 for _ in range(9)] for _ in range(9)]
        for (r, c), dom in self.domains.items():
            if len(dom) == 1:
                grid[r][c] = next(iter(dom))
        return grid

    def to_string(self) -> str:
        grid = self.to_grid()
        return "".join(str(grid[r][c]) for r in range(9) for c in range(9))

    def pretty(self) -> str:
        grid = self.to_grid()
        lines: List[str] = []
        for r in range(9):
            if r in (3, 6):
                lines.append("------+-------+------")
            row_vals: List[str] = []
            for c in range(9):
                if c in (3, 6):
                    row_vals.append("|")
                v = grid[r][c]
                row_vals.append(str(v) if v != 0 else ".")
            lines.append(" ".join(row_vals))
        return "\n".join(lines)

    def ac3(self) -> bool:
        queue: List[Tuple[Coord, Coord]] = [
            (xi, xj) for xi in self.domains for xj in PEERS[xi]
        ]

        while queue:
            xi, xj = queue.pop(0)
            if self._revise(xi, xj):
                if not self.domains[xi]:
                    return False
                for xk in PEERS[xi] - {xj}:
                    queue.append((xk, xi))
        return True

    def _revise(self, xi: Coord, xj: Coord) -> bool:
        revised = False
        dom_i = self.domains[xi]
        dom_j = self.domains[xj]

        if len(dom_j) == 1:
            val_j = next(iter(dom_j))
            if val_j in dom_i:
                if len(dom_i) == 1:
                    # Would make Xi empty; AC-3 will detect inconsistency later.
                    return revised
                dom_i.remove(val_j)
                revised = True
        return revised

    def solve(
        self,
        step_callback: Optional[Callable[[int, List[List[int]]], None]] = None,
        step_interval: int = 1000,
    ) -> Optional["SudokuCSP"]:
        domains_copy: Dict[Coord, Set[int]] = {k: set(v) for k, v in self.domains.items()}
        state = {"steps": 0}
        result = self._backtrack(domains_copy, step_callback, step_interval, state)
        if result is None:
            return None
        return SudokuCSP(result)

    def _select_unassigned_variable(self, domains: Dict[Coord, Set[int]]) -> Optional[Coord]:
        unassigned = [(v, d) for v, d in domains.items() if len(d) > 1]
        if not unassigned:
            return None
        # Sort by domain size (MRV); tie-breaker by fixed order
        v, _ = min(unassigned, key=lambda item: len(item[1]))
        return v

    def _order_domain_values(self, var: Coord, domains: Dict[Coord, Set[int]]) -> Sequence[int]:
        counts: List[Tuple[int, int]] = []
        for val in domains[var]:
            impact = 0
            for peer in PEERS[var]:
                if val in domains[peer]:
                    impact += 1
            counts.append((val, impact))
        # Sort by impact ascending: least constraining value first
        counts.sort(key=lambda t: t[1])
        return [v for v, _ in counts]

    def _consistent(self, var: Coord, val: int, domains: Dict[Coord, Set[int]]) -> bool:
        for peer in PEERS[var]:
            d = domains[peer]
            if len(d) == 1 and val in d:
                return False
        return True

    def _forward_check(
        self, var: Coord, val: int, domains: Dict[Coord, Set[int]]
    ) -> Optional[Dict[Coord, Set[int]]]:
        new_domains: Dict[Coord, Set[int]] = {v: set(d) for v, d in domains.items()}
        new_domains[var] = {val}

        for peer in PEERS[var]:
            if val in new_domains[peer]:
                if len(new_domains[peer]) == 1:
                    return None
                new_domains[peer].remove(val)

        return new_domains

    def _backtrack(
        self,
        domains: Dict[Coord, Set[int]],
        step_callback: Optional[Callable[[int, List[List[int]]], None]],
        step_interval: int,
        state: Dict[str, int],
    ) -> Optional[Dict[Coord, Set[int]]]:
        state["steps"] += 1
        if step_callback is not None and state["steps"] % step_interval == 0:
            grid = [[0 for _ in range(9)] for _ in range(9)]
            for (r, c), dom in domains.items():
                if len(dom) == 1:
                    grid[r][c] = next(iter(dom))
            step_callback(state["steps"], grid)

        if all(len(d) == 1 for d in domains.values()):
            tmp = SudokuCSP(domains)
            if tmp._constraints_satisfied():
                return domains
            return None

        var = self._select_unassigned_variable(domains)
        if var is None:
            return None

        for val in self._order_domain_values(var, domains):
            if not self._consistent(var, val, domains):
                continue

            new_domains = self._forward_check(var, val, domains)
            if new_domains is None:
                continue

            result = self._backtrack(new_domains, step_callback, step_interval, state)
            if result is not None:
                return result

        return None


def solve_puzzle(puzzle: str) -> Optional[SudokuCSP]:
    csp = SudokuCSP.from_string(puzzle)
    return csp.solve()


