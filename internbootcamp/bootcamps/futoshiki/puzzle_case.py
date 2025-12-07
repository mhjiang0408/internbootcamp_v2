"""Static and procedural Futoshiki puzzle cases used for instruction/data generation."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

Grid = List[List[int]]
ConstraintKey = Tuple[Tuple[int, int], Tuple[int, int]]


def _build_constraint_map(
    triples: List[Tuple[Tuple[int, int], Tuple[int, int], str]]
) -> Dict[ConstraintKey, str]:
    mapping: Dict[ConstraintKey, str] = {}
    for left, right, sign in triples:
        if left > right:
            left, right = right, left
            sign = ">" if sign == "<" else "<"
        mapping[(left, right)] = sign
    return mapping


class _FutoshikiRenderer:
    """Utility that mirrors the formatting from the original generator."""

    @staticmethod
    def puzzle_to_string(grid: Grid, constraints: Dict[ConstraintKey, str]) -> str:
        size = len(grid)

        def cell_str(value: int) -> str:
            return str(value) if value != 0 else "_"

        def get_constraint(r1: int, c1: int, r2: int, c2: int) -> str | None:
            if (r1, c1) == (r2, c2):
                return None
            key: ConstraintKey
            invert = False
            if (r1, c1) < (r2, c2):
                key = ((r1, c1), (r2, c2))
            else:
                key = ((r2, c2), (r1, c1))
                invert = True
            sign = constraints.get(key)
            if sign is None:
                return None
            if invert:
                sign = ">" if sign == "<" else "<"

            if r1 == r2:
                return "<" if sign == "<" else ">"
            return "\u2227" if sign == "<" else "\u2228"

        lines: List[str] = []
        for r in range(size):
            row_tokens: List[str] = []
            for c in range(size):
                row_tokens.append(cell_str(grid[r][c]))
                if c < size - 1:
                    constraint = get_constraint(r, c, r, c + 1)
                    row_tokens.append(constraint if constraint else " ")
            lines.append(" ".join(row_tokens))

            if r < size - 1:
                vert_tokens: List[str] = []
                for c in range(size):
                    constraint = get_constraint(r, c, r + 1, c)
                    vert_tokens.append(constraint if constraint else " ")
                    if c < size - 1:
                        vert_tokens.append(" ")
                lines.append(" ".join(vert_tokens))

        return "\n".join(lines)


@dataclass(frozen=True)
class FutoshikiStaticCase:
    puzzle_grid: Grid
    solution_grid: Grid
    constraints: Dict[ConstraintKey, str]

    def build_identity(self) -> Dict[str, Any]:
        question = self.build_question_prompt()
        answer = _FutoshikiRenderer.puzzle_to_string(self.solution_grid, self.constraints)
        constraint_items = [
            {
                "r1": a[0],
                "c1": a[1],
                "r2": b[0],
                "c2": b[1],
                "sign": sign,
            }
            for (a, b), sign in self.constraints.items()
        ]
        metadata = {
            "puzzle_grid": self.puzzle_grid,
            "solution_grid": self.solution_grid,
            "constraints": constraint_items,
            "board_size": len(self.solution_grid),
        }
        return {
            "question": question,
            "solution_string": answer,
            "solution_grid": self.solution_grid,
            "constraints": constraint_items,
            "board_size": len(self.solution_grid),
            "metadata": metadata,
        }

    def build_question_prompt(self) -> str:
        puzzle = _FutoshikiRenderer.puzzle_to_string(self.puzzle_grid, self.constraints)
        board_size = len(self.puzzle_grid)
        return (
            "You are a Futoshiki (Latin square) expert. "
            "Fill every row and column with the numbers 1 through {size} exactly once.\n"
            "Inequalities (<, >, ∧, ∨) between adjacent cells must also be respected.\n\n"
            "Puzzle:\n{puzzle}\n\n"
            "Return the completed grid using the same ASCII layout as the puzzle. "
            "Please end your response with a single line that starts with Answer: followed by the grid.\n"
        ).format(size=board_size, puzzle=puzzle)


def default_futoshiki_case() -> Dict[str, Any]:
    puzzle_grid: Grid = [
        [0, 3, 0, 0],
        [0, 0, 3, 0],
        [1, 0, 0, 3],
        [0, 2, 4, 0],
    ]
    solution_grid: Grid = [
        [4, 3, 1, 2],
        [2, 1, 3, 4],
        [1, 4, 2, 3],
        [3, 2, 4, 1],
    ]
    constraint_triples: List[Tuple[Tuple[int, int], Tuple[int, int], str]] = [
        ((0, 0), (0, 1), ">"),
        ((0, 2), (0, 3), "<"),
        ((1, 0), (1, 1), ">"),
        ((2, 0), (2, 1), "<"),
        ((2, 2), (2, 3), "<"),
        ((3, 1), (3, 2), "<"),
        ((0, 0), (1, 0), ">"),
        ((1, 2), (2, 2), ">"),
        ((1, 3), (2, 3), ">"),
        ((2, 3), (3, 3), ">"),
    ]

    case = FutoshikiStaticCase(
        puzzle_grid=puzzle_grid,
        solution_grid=solution_grid,
        constraints=_build_constraint_map(constraint_triples),
    )
    return case.build_identity()


# -------------------------
# Procedural case generator
# -------------------------

def _latin_square(size: int, rng: random.Random) -> Grid:
    """Generate a valid Latin square then permute rows/cols/values for randomness."""
    base = [[((r + c) % size) + 1 for c in range(size)] for r in range(size)]
    row_idx = list(range(size))
    col_idx = list(range(size))
    val_perm = list(range(1, size + 1))
    rng.shuffle(row_idx)
    rng.shuffle(col_idx)
    rng.shuffle(val_perm)
    grid: Grid = []
    for r in row_idx:
        grid.append([val_perm[base[r][c] - 1] for c in col_idx])
    return grid


def _generate_constraints(solution: Grid, rng: random.Random, base_prob: float) -> Dict[ConstraintKey, str]:
    constraints: Dict[ConstraintKey, str] = {}
    size = len(solution)
    for r in range(size):
        for c in range(size):
            if c < size - 1 and rng.random() < base_prob:
                sign = "<" if solution[r][c] < solution[r][c + 1] else ">"
                constraints[((r, c), (r, c + 1))] = sign
            if r < size - 1 and rng.random() < base_prob:
                sign = "<" if solution[r][c] < solution[r + 1][c] else ">"
                constraints[((r, c), (r + 1, c))] = sign
    return constraints


def _remove_clues(solution: Grid, rng: random.Random, target_ratio: float = 0.45) -> Grid:
    """Remove clues down to a target fill ratio. No uniqueness guarantee, but OK for RL self-play."""
    grid = copy.deepcopy(solution)
    size = len(grid)
    coords = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(coords)
    target_filled = max(int(size * size * target_ratio), size)  # keep at least one clue per row-ish

    def filled() -> int:
        return sum(1 for r in range(size) for c in range(size) if grid[r][c] != 0)

    for r, c in coords:
        if filled() <= target_filled:
            break
        grid[r][c] = 0
    return grid


def random_futoshiki_case(
    seed: int | None = None,
    min_board_size: int = 4,
    max_board_size: int = 6,
    constraint_density: float = 0.18,
) -> Dict[str, Any]:
    """
    Build a random Futoshiki case (puzzle + ground-truth) using a Latin square base.
    Each call with a new seed yields a different instance.
    """
    rng = random.Random(seed)
    size = rng.randint(min_board_size, max_board_size)

    solution_grid = _latin_square(size, rng)
    constraints = _generate_constraints(solution_grid, rng, base_prob=constraint_density)
    puzzle_grid = _remove_clues(solution_grid, rng)

    puzzle_str = _FutoshikiRenderer.puzzle_to_string(puzzle_grid, constraints)
    solution_str = _FutoshikiRenderer.puzzle_to_string(solution_grid, constraints)

    constraint_items = [
        {"r1": a[0], "c1": a[1], "r2": b[0], "c2": b[1], "sign": sign} for (a, b), sign in constraints.items()
    ]

    question = (
        "You are a Futoshiki (Latin square) expert. "
        f"Fill every row and column with the numbers 1 through {size} exactly once.\n"
        "Inequalities (<, >, ∧, ∨) between adjacent cells must also be respected.\n\n"
        f"Puzzle:\n{puzzle_str}\n\n"
        "Return the completed grid using the same ASCII layout as the puzzle. "
        "Please end your response with a single line that starts with Answer: followed by the grid.\n"
    )

    metadata = {
        "puzzle_grid": puzzle_grid,
        "solution_grid": solution_grid,
        "constraints": constraint_items,
        "board_size": size,
        "seed": seed,
    }

    return {
        "question": question,
        "solution_string": solution_str,
        "solution_grid": solution_grid,
        "constraints": constraint_items,
        "board_size": size,
        "metadata": metadata,
    }
