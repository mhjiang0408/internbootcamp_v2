#!/usr/bin/env bash

set -euo pipefail

DATASET="internbootcamp/bootcamps/futoshiki/data/futoshiki_eval_sample.jsonl"
OUTPUT_DIR="outputs/futoshiki"

: "${API_KEY:?Set API_KEY with your model credential}"

uv run python internbootcamp/utils/run_evaluation.py \
  --dataset-path "$DATASET" \
  --output-dir "$OUTPUT_DIR" \
  --api-key "$API_KEY" \
  --api-url "https://jpd5c8gqpmcmc8jpmkqkq8kqajjkqqkh.openapi-qb.sii.edu.cn/v1" \
  --api-model "gpt-4o-mini" \
  --reward-calculator-class "internbootcamp.bootcamps.futoshiki.futoshiki_reward_calculator.FutoshikiRewardCalculator" \
  --tool-config "internbootcamp/bootcamps/futoshiki/configs/futoshiki_tool_config.yaml" \
  --interaction-config "internbootcamp/bootcamps/futoshiki/configs/futoshiki_interaction_config.yaml" \
  --max-user-turns 4 \
  --max-assistant-turns 4 \
  --tokenizer-path "" \
  --verbose
