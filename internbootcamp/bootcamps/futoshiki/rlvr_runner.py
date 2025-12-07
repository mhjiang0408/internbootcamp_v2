"""
RLVR-style query and verification helpers for the Futoshiki puzzle.

The file exposes:
- build_futoshiki_query: creates a single query dict consumable by BaseEvaluator.
- verify_futoshiki_completion: standalone verifier for training/inference loops.
- main: small CLI to run a few eval samples against an OpenAI-compatible API.
"""

from __future__ import annotations

import argparse
import asyncio
import os

# Avoid torch import from transformers in CPU-only evaluation to prevent broken distributed builds
os.environ.setdefault("TRANSFORMERS_NO_TORCH", "1")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_FLAX", "1")
from typing import Any, Dict, List

import random

from internbootcamp.bootcamps.futoshiki.futoshiki_reward_calculator import FutoshikiRewardCalculator
from internbootcamp.bootcamps.futoshiki.puzzle_case import default_futoshiki_case, random_futoshiki_case

# Defaults can be overridden with env vars FUTOSHIKI_API_BASE/FUTOSHIKI_API_KEY
DEFAULT_API_BASE = "https://jpd5c8gqpmcmc8jpmkqkq8kqajjkqqkh.openapi-qb.sii.edu.cn/v1"
DEFAULT_API_KEY = "46dk8wARhdHfta4oHIPGwBmInLmrQnqbf24jsyXO5WM="

SYSTEM_PROMPT = (
    "You are an expert at solving Futoshiki (Latin square) puzzles. "
    "Respect every inequality symbol and keep the grid formatting identical to the prompt. "
    "Do not add commentary; finish with one line that begins with `Answer:` followed by the solved grid."
)


def build_futoshiki_query(case: Dict[str, Any] | None = None, seed: int | None = None) -> Dict[str, Any]:
    """
    Build a single RLVR query dict understood by BaseEvaluator.

    Returns a dict containing the chat messages plus the ground-truth identity
    the verifier will use.
    """
    if case is None:
        identity = dict(random_futoshiki_case(seed=seed))
    else:
        identity = dict(case)
    prompt = (
        identity["question"]
        + "\nAlways end with a single line starting with `Answer:` followed by the completed grid in the same ASCII layout."
    )
    return {
        "data_source": "futoshiki_rlvr",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "reward_model": {"ground_truth": identity},
        "extra_info": {"generator_name": "futoshiki_rlvr", "identity": identity},
    }


def build_dataset(samples: int, base_seed: int | None = None) -> List[Dict[str, Any]]:
    """
    Create a small in-memory dataset for evaluation.
    Each sample gets a different seed; set base_seed for reproducibility.
    """
    rng = random.Random(base_seed)
    return [build_futoshiki_query(seed=rng.randrange(1, 2**31)) for _ in range(samples)]


def verify_futoshiki_completion(model_output: str, ground_truth: Dict[str, Any]) -> float:
    """Standalone verifier for RL loops or offline scoring."""
    return float(
        FutoshikiRewardCalculator.verify_score(
            model_output=model_output, identity=ground_truth, format_score=0.0, short_penalty=False
        )
    )


async def run_evaluation(
    model: str,
    api_base: str,
    api_key: str,
    samples: int,
    output_dir: str,
    concurrency: int,
) -> List[Dict[str, Any]]:
    # Local import to avoid pulling heavy deps when only using query/verify helpers
    from internbootcamp.src.base_evaluator import BaseEvaluator

    dataset = build_dataset(samples)
    evaluator = BaseEvaluator(
        api_url=api_base,
        api_key=api_key,
        api_model=model,
        reward_calculator=FutoshikiRewardCalculator,
        max_assistant_turns=1,
        max_user_turns=None,
    )
    results = await evaluator.run_evaluation(
        dataset=dataset,
        output_dir=output_dir,
        max_concurrent=concurrency,
    )
    solved = sum(1 for r in results if r and r.get("score", 0) >= 1.0)
    avg_score = sum(r.get("score", 0) for r in results if r) / len(results) if results else 0.0
    print(f"Finished: {solved}/{len(results)} solved, avg score={avg_score:.3f}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RLVR-style Futoshiki eval against an OpenAI-compatible API.")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name passed to the chat completion endpoint.")
    parser.add_argument(
        "--api-base",
        default=os.environ.get("FUTOSHIKI_API_BASE", DEFAULT_API_BASE),
        help="OpenAI-compatible API base URL.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("FUTOSHIKI_API_KEY", DEFAULT_API_KEY),
        help="API key; can also be set via FUTOSHIKI_API_KEY.",
    )
    parser.add_argument("--samples", type=int, default=1, help="How many Futoshiki cases to evaluate (randomized).")
    parser.add_argument(
        "--output-dir",
        default="outputs/futoshiki_rlvr",
        help="Directory where BaseEvaluator will dump jsonl/csv reports.",
    )
    parser.add_argument("--concurrency", type=int, default=1, help="Max concurrent requests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing API key: set --api-key or FUTOSHIKI_API_KEY.")
    asyncio.run(
        run_evaluation(
            model=args.model,
            api_base=args.api_base,
            api_key=args.api_key,
            samples=args.samples,
            output_dir=args.output_dir,
            concurrency=args.concurrency,
        )
    )


if __name__ == "__main__":
    main()
