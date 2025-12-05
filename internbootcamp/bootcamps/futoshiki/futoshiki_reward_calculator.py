from __future__ import annotations

from typing import Any, Dict, List

from internbootcamp.src.base_reward_calculator import BaseRewardCalculator


class FutoshikiRewardCalculator(BaseRewardCalculator):
    @staticmethod
    def extract_output(output_str: str) -> str | None:
        if not isinstance(output_str, str):
            return None
        marker = "Answer:"
        if marker in output_str:
            return output_str.split(marker, 1)[1].strip()
        return output_str.strip()

    @classmethod
    def _verify_correction(cls, extracted_output, identity: Dict[str, Any], **kwargs) -> float:
        if not extracted_output:
            return 0.0

        expected_grid: List[List[int]] = identity.get("solution_grid", [])
        board_size = identity.get("board_size", len(expected_grid))
        constraints = identity.get("constraints", [])
        candidate_grid = cls._parse_numeric_grid(extracted_output, board_size)

        if len(candidate_grid) != board_size:
            return 0.0

        total = board_size * board_size
        matches = sum(
            1
            for r in range(board_size)
            for c in range(board_size)
            if c < len(candidate_grid[r]) and candidate_grid[r][c] == expected_grid[r][c]
        )

        if matches == total and cls._constraints_ok(candidate_grid, constraints):
            return 1.0

        return matches / total

    @staticmethod
    def _parse_numeric_grid(answer: str, size: int) -> List[List[int]]:
        rows: List[List[int]] = []
        for line in answer.splitlines():
            digits = [int(ch) for ch in line if ch.isdigit()]
            if len(digits) == size:
                rows.append(digits)
        return rows[:size]

    @staticmethod
    def _constraints_ok(grid: List[List[int]], constraints: List[Dict[str, Any]]) -> bool:
        for constraint in constraints:
            r1, c1 = constraint["r1"], constraint["c1"]
            r2, c2 = constraint["r2"], constraint["c2"]
            sign = constraint["sign"]
            try:
                value1 = grid[r1][c1]
                value2 = grid[r2][c2]
            except IndexError:
                return False
            if sign == ">" and not (value1 > value2):
                return False
            if sign == "<" and not (value1 < value2):
                return False
        return True

