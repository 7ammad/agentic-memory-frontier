from __future__ import annotations

from pydantic import BaseModel, Field


class OfficialEvaluatorScaffold(BaseModel):
    suite_name: str
    official_evaluator_name: str
    official_evaluator_source: str
    data_source: str
    status: str = "official_bounded_smoke_pending"
    required_env_vars: list[str] = Field(default_factory=list)
    setup_commands: list[str] = Field(default_factory=list)
    smoke_command: str
    bounded_smoke_command: str = ""
    full_run_command: str = ""
    smoke_evidence_path: str = ""
    resource_note: str = ""
    remaining_note: str


OFFICIAL_EVALUATOR_SCAFFOLDS = {
    "halumem_cem0": OfficialEvaluatorScaffold(
        suite_name="halumem_cem0",
        official_evaluator_name="HaluMem eval toolkit",
        official_evaluator_source="https://github.com/MemTensor/HaluMem/tree/main/eval",
        data_source="https://huggingface.co/datasets/IAAR-Shanghai/HaluMem",
        status="official_bounded_smoke_passed",
        required_env_vars=[
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_MODEL",
            "PYTHONIOENCODING",
        ],
        setup_commands=[
            "git clone https://github.com/MemTensor/HaluMem tmp\\official-evaluators\\HaluMem",
            "uv venv --python 3.11 tmp\\official-evaluators\\HaluMem\\.venv",
            "uv pip install --python tmp\\official-evaluators\\HaluMem\\.venv\\Scripts\\python.exe openai python-dotenv tenacity tqdm numpy pandas pyarrow jsonlines huggingface_hub tiktoken",
            "download IAAR-Shanghai/HaluMem HaluMem-Medium.jsonl to tmp\\official-data\\halumem",
        ],
        smoke_command=(
            "cd tmp\\official-evaluators\\HaluMem\\eval; "
            "..\\.venv\\Scripts\\python.exe -c "
            "\"import evaluation; evaluation.main('memzero', 'ams-smoke', "
            "user_num=1, max_workers=1)\""
        ),
        bounded_smoke_command=(
            "cd tmp\\official-evaluators\\HaluMem\\eval; "
            "$env:PYTHONIOENCODING='utf-8'; "
            "$env:OPENAI_API_KEY=$env:XAI_API_KEY; "
            "$env:OPENAI_BASE_URL='https://api.x.ai/v1'; "
            "$env:OPENAI_MODEL='grok-4.20-0309-non-reasoning'; "
            "..\\.venv\\Scripts\\python.exe -c "
            "\"import evaluation; evaluation.main('memzero', 'ams-smoke', "
            "user_num=1, max_workers=1)\""
        ),
        full_run_command=(
            "cd tmp\\official-evaluators\\HaluMem\\eval; poetry install --with eval; "
            "python eval_memzero.py; python evaluation.py --frame memzero --version default"
        ),
        smoke_evidence_path=(
            "tmp\\official-evaluators\\HaluMem\\eval\\results\\memzero-ams-smoke\\"
            "memzero_eval_stat_result.json"
        ),
        resource_note=(
            "Bounded smoke used three real public HaluMem sessions and xAI-compatible "
            "OpenAI API credentials. Full official scoring should run the complete "
            "HaluMem-Medium/Long data and the selected official memory wrapper."
        ),
        remaining_note=(
            "The official bounded smoke passed over a CEM-generated artifact, but it is "
            "not an official CEM leaderboard score and does not replace a full dataset run."
        ),
    ),
    "memoryarena_cem0": OfficialEvaluatorScaffold(
        suite_name="memoryarena_cem0",
        official_evaluator_name="MemoryArena environment gym",
        official_evaluator_source="https://github.com/ZexueHe/MemoryArena",
        data_source="https://huggingface.co/datasets/ZexueHe/memoryarena",
        status="official_bounded_smoke_passed",
        required_env_vars=[
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
        ],
        setup_commands=[
            "git clone https://github.com/ZexueHe/MemoryArena tmp\\official-evaluators\\MemoryArena",
            "uv venv --python 3.10 tmp\\official-evaluators\\MemoryArena\\.venv",
            "uv pip install --python tmp\\official-evaluators\\MemoryArena\\.venv\\Scripts\\python.exe fastapi uvicorn pydantic requests datasets openai tiktoken numpy tqdm python-dotenv pyyaml",
            "download ZexueHe/memoryarena formal_reasoning_math test row through datasets",
        ],
        smoke_command=(
            "start env\\env_server.py, then run official formal-reasoning long_context "
            "smoke against one real ZexueHe/memoryarena row"
        ),
        bounded_smoke_command=(
            "cd tmp\\official-evaluators\\MemoryArena; "
            "$env:OPENAI_API_KEY=$env:XAI_API_KEY; "
            "$env:OPENAI_BASE_URL='https://api.x.ai/v1'; "
            ".\\.venv\\Scripts\\python.exe env\\env_server.py; "
            "run official MathEnvironment + MathAgent + long_context over one "
            "formal_reasoning_math subtask"
        ),
        full_run_command=(
            "cd tmp\\official-evaluators\\MemoryArena; "
            "python env\\env_server.py; "
            "python run_math.py --memory-system long_context --model <model> "
            "--config-name formal_reasoning_math"
        ),
        smoke_evidence_path=(
            "tmp\\official-runs\\memoryarena-formal-long-context-smoke\\json\\"
            "long_context_grok-4.20-0309-non-reasoning\\all_results.json"
        ),
        resource_note=(
            "Bounded smoke used the official formal-reasoning environment boundary. "
            "The web-shopping path also needs Java/JDK and the WebShop product DB; "
            "java/javac were not installed locally during this run."
        ),
        remaining_note=(
            "The official formal-reasoning bounded smoke passed with long_context, but it is "
            "not an official CEM leaderboard score and does not yet wire CEM as the "
            "MemoryArena memory system."
        ),
    ),
    "longmemeval_v2_cem0": OfficialEvaluatorScaffold(
        suite_name="longmemeval_v2_cem0",
        official_evaluator_name="LongMemEval-V2 evaluation runner",
        official_evaluator_source="https://github.com/xiaowu0162/LongMemEval-V2",
        data_source="https://huggingface.co/datasets/xiaowu0162/longmemeval-v2",
        status="official_bounded_smoke_passed",
        required_env_vars=["OPENAI_API_KEY"],
        setup_commands=[
            "git clone https://github.com/xiaowu0162/LongMemEval-V2 tmp\\official-evaluators\\LongMemEval-V2",
            "uv venv --python 3.11 tmp\\official-evaluators\\LongMemEval-V2\\.venv",
            "uv pip install --python tmp\\official-evaluators\\LongMemEval-V2\\.venv\\Scripts\\python.exe -r tmp\\official-evaluators\\LongMemEval-V2\\requirements.txt",
            "download questions.jsonl, haystacks/lme_v2_small.json, and a streamed trajectory subset from xiaowu0162/longmemeval-v2",
        ],
        smoke_command=(
            "python data\\validate_data.py --data-root "
            "..\\..\\official-data\\longmemeval-v2-smoke --tier small --no-check-screenshots"
        ),
        bounded_smoke_command=(
            "cd tmp\\official-evaluators\\LongMemEval-V2; "
            "$env:OPENAI_API_KEY=$env:XAI_API_KEY; "
            ".\\.venv\\Scripts\\python.exe evaluation\\harness.py --domain enterprise "
            "--questions-path ..\\..\\official-data\\longmemeval-v2-smoke\\questions.jsonl "
            "--haystack-path ..\\..\\official-data\\longmemeval-v2-smoke\\haystacks\\lme_v2_small.json "
            "--trajectories-path ..\\..\\official-data\\longmemeval-v2-smoke\\trajectories.jsonl "
            "--memory-config-path evaluation\\memory_configs\\no_retrieval.json "
            "--output-dir ..\\..\\official-runs\\longmemeval-v2-no-retrieval-smoke "
            "--model grok-4.20-0309-non-reasoning --base-url https://api.x.ai/v1 "
            "--api-key-env OPENAI_API_KEY --reader-disable-thinking "
            "--evaluator-model grok-4.20-0309-non-reasoning "
            "--evaluator-base-url https://api.x.ai/v1 --evaluator-api-key-env OPENAI_API_KEY"
        ),
        full_run_command=(
            "cd tmp\\official-evaluators\\LongMemEval-V2; "
            ".\\.venv\\Scripts\\python.exe data\\download_data.py --data-root data\\longmemeval-v2; "
            ".\\.venv\\Scripts\\python.exe data\\prepare_data.py --data-root data\\longmemeval-v2 --mode symlink; "
            ".\\.venv\\Scripts\\python.exe data\\validate_data.py --data-root data\\longmemeval-v2 --tier small; "
            ".\\.venv\\Scripts\\python.exe evaluation\\run_eval.py --data-root data\\longmemeval-v2 "
            "--domain enterprise --tier small --method no_retrieval --output-dir runs\\no_retrieval_enterprise_small"
        ),
        smoke_evidence_path=(
            "tmp\\official-runs\\longmemeval-v2-no-retrieval-smoke\\aggregated_metrics.json"
        ),
        resource_note=(
            "Bounded smoke used one official question, 100 streamed official trajectories, "
            "and the official no_retrieval config. The full public data path downloads "
            "multi-GB archives and should run with screenshot validation enabled when "
            "the tarballs are available."
        ),
        remaining_note=(
            "The official bounded smoke passed through the released harness, but it is "
            "not an official CEM leaderboard score and does not yet score a CEM memory "
            "backend inside LongMemEval-V2."
        ),
    ),
}


def official_evaluator_scaffold(suite_name: str) -> OfficialEvaluatorScaffold:
    return OFFICIAL_EVALUATOR_SCAFFOLDS[suite_name]
