from __future__ import annotations

from typing import Any, Dict

from internbootcamp.src.base_instruction_generator import BaseInstructionGenerator

from .puzzle_case import default_futoshiki_case


class FutoshikiInstructionGenerator(BaseInstructionGenerator):
    """Instruction generator that emits a deterministic Futoshiki puzzle."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._identity = default_futoshiki_case()

    def case_generator(self) -> Dict[str, Any]:
        return dict(self._identity)

    def prompt_func(self, identity: Dict[str, Any]) -> str:
        return identity.get("question", self._identity["question"])
