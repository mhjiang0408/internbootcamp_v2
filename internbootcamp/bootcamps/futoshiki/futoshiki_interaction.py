from __future__ import annotations

from typing import Any

from internbootcamp.src.base_interaction import BaseInteraction
from .futoshiki_reward_calculator import FutoshikiRewardCalculator


class FutoshikiInteraction(BaseInteraction):
    async def generate_response(
        self, instance_id: str, messages: list[dict[str, Any]], **kwargs
    ) -> tuple[bool, str, float, dict[str, Any]]:
        content = ""
        for item in reversed(messages):
            if item.get("role") == "assistant":
                content = item.get("content", "")
                break

        identity = self._instance_dict[instance_id]["identity"]
        score = FutoshikiRewardCalculator.verify_score(
            model_output=content,
            identity=identity,
            format_score=0.0,
            short_penalty=False,
        )
        if score >= 1.0:
            return True, "", score, {"score": score}
        hint = (
            "The grid is not correct yet. Double-check each inequality and make sure each row "
            "and column contains every digit exactly once before replying with Answer:."
        )
        return False, hint, score, {"score": score}

