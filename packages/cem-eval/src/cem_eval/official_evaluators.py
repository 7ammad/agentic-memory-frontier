from __future__ import annotations

from pydantic import BaseModel, Field


class OfficialEvaluatorScaffold(BaseModel):
    suite_name: str
    official_evaluator_name: str
    official_evaluator_source: str
    data_source: str
    status: str = "not_wired"
    required_env_vars: list[str] = Field(default_factory=list)
    smoke_command: str
    remaining_note: str


OFFICIAL_EVALUATOR_SCAFFOLDS = {
    "halumem_cem0": OfficialEvaluatorScaffold(
        suite_name="halumem_cem0",
        official_evaluator_name="HaluMem eval toolkit",
        official_evaluator_source="https://github.com/MemTensor/HaluMem/tree/main/eval",
        data_source="https://huggingface.co/datasets/IAAR-Shanghai/HaluMem",
        required_env_vars=["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"],
        smoke_command="python eval/eval_memzero.py",
        remaining_note=(
            "Official HaluMem scoring needs the released eval wrapper runtime and model/service "
            "credentials; AMS currently reports local proxy extraction and QA metrics only."
        ),
    ),
    "memoryarena_cem0": OfficialEvaluatorScaffold(
        suite_name="memoryarena_cem0",
        official_evaluator_name="MemoryArena environment gym",
        official_evaluator_source="https://github.com/ZexueHe/MemoryArena",
        data_source="https://memoryarena.github.io/",
        required_env_vars=[
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "GOOGLE_API_KEY",
            "ANTHROPIC_API_KEY",
        ],
        smoke_command="python run_shopping.py",
        remaining_note=(
            "Official MemoryArena scoring requires the released environment gym and agent loop; "
            "AMS currently reports a local static JSON proxy over downloaded task rows."
        ),
    ),
    "longmemeval_v2_cem0": OfficialEvaluatorScaffold(
        suite_name="longmemeval_v2_cem0",
        official_evaluator_name="LongMemEval-V2 evaluation runner",
        official_evaluator_source="https://github.com/xiaowu0162/LongMemEval-V2",
        data_source="https://huggingface.co/datasets/xiaowu0162/longmemeval-v2",
        required_env_vars=["OPENAI_API_KEY"],
        smoke_command=(
            "python data/validate_data.py --data-root data/longmemeval-v2 --tier small"
        ),
        remaining_note=(
            "Official LongMemEval-V2 scoring needs the Python 3.11 eval environment, data "
            "checksums, answer evaluator, and latency runner; AMS currently reports local proxy "
            "answer/retrieval metrics only."
        ),
    ),
}


def official_evaluator_scaffold(suite_name: str) -> OfficialEvaluatorScaffold:
    return OFFICIAL_EVALUATOR_SCAFFOLDS[suite_name]
