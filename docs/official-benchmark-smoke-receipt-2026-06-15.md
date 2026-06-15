# Official Benchmark Smoke Receipt - 2026-06-15

Task: AMS benchmark final build correction.

Verdict: official bounded smokes executed for HaluMem, LongMemEval-V2, and
MemoryArena. These are official runner-path smokes, not leaderboard-grade CEM
scores.

## Environment

- Workspace: `C:\Dev\Builds\Agentic Memory System`
- Branch: `codex/ams-only-memory-default`
- Official repo root: `tmp\official-evaluators`
- Official data root: `tmp\official-data`
- Official run output root: `tmp\official-runs`
- Credential path used: `XAI_API_KEY` exposed as `OPENAI_API_KEY`
- Base URL used: `https://api.x.ai/v1`
- Model used: `grok-4.20-0309-non-reasoning`

## HaluMem

- Official repo: `https://github.com/MemTensor/HaluMem`
- Commit: `c29025f43b347f68fc36a06bee8ed29b4dc6c3fb`
- Data source: `https://huggingface.co/datasets/IAAR-Shanghai/HaluMem`
- Bounded data: three real public HaluMem sessions from
  `tmp\official-data\halumem\ams-smoke-subset.jsonl`
- Official artifact staged at:
  `tmp\official-evaluators\HaluMem\eval\results\memzero-ams-smoke\memzero_eval_results.jsonl`

Command:

```powershell
cd tmp\official-evaluators\HaluMem\eval
$env:PYTHONIOENCODING='utf-8'
$env:OPENAI_API_KEY=$env:XAI_API_KEY
$env:OPENAI_BASE_URL='https://api.x.ai/v1'
$env:OPENAI_MODEL='grok-4.20-0309-non-reasoning'
..\.venv\Scripts\python.exe -c "import evaluation; evaluation.main('memzero', 'ams-smoke', user_num=1, max_workers=1)"
```

Result:

- Output: `tmp\official-evaluators\HaluMem\eval\results\memzero-ams-smoke\memzero_eval_stat_result.json`
- Official scorer completed and wrote the stat result.
- Record counts: memory integrity `9`, memory accuracy `44`, memory update `4`,
  QA `3`.
- Summary: extraction F1 `0.0`, memory accuracy target-all `1.0`,
  weighted-all `0.06818`, interference accuracy `0.3333`, update omission
  ratio `1.0`, QA omission ratio `1.0`.

Full-run path:

```powershell
cd tmp\official-evaluators\HaluMem\eval
poetry install --with eval
python eval_memzero.py
python evaluation.py --frame memzero --version default
```

Full-run requirement: complete HaluMem-Medium/Long data, selected official
memory-wrapper credentials or a production CEM wrapper, and model/API budget for
all judge calls.

## LongMemEval-V2

- Official repo: `https://github.com/xiaowu0162/LongMemEval-V2`
- Commit: `8e8b92a3cece71af6af0d3aa2d7957df49dd9f65`
- Data source: `https://huggingface.co/datasets/xiaowu0162/longmemeval-v2`
- Bounded data: question `01307e07` plus 100 streamed official trajectories
  from `trajectories.jsonl`

Validation command:

```powershell
cd tmp\official-evaluators\LongMemEval-V2
.\.venv\Scripts\python.exe data\validate_data.py --data-root ..\..\official-data\longmemeval-v2-smoke --tier small --no-check-screenshots
```

Validation result:

```json
{"questions":1,"trajectories":100,"haystack_questions":1,"tier":"small","check_screenshots":false}
```

Harness command:

```powershell
cd tmp\official-evaluators\LongMemEval-V2
$env:OPENAI_API_KEY=$env:XAI_API_KEY
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe evaluation\harness.py --domain enterprise --questions-path ..\..\official-data\longmemeval-v2-smoke\questions.jsonl --haystack-path ..\..\official-data\longmemeval-v2-smoke\haystacks\lme_v2_small.json --trajectories-path ..\..\official-data\longmemeval-v2-smoke\trajectories.jsonl --memory-config-path evaluation\memory_configs\no_retrieval.json --output-dir ..\..\official-runs\longmemeval-v2-no-retrieval-smoke --model grok-4.20-0309-non-reasoning --base-url https://api.x.ai/v1 --api-key-env OPENAI_API_KEY --max-completion-tokens 512 --memory-context-max-tokens 4096 --reader-max-concurrent-requests 1 --timeout-seconds 300 --reader-disable-thinking --temperature 0 --evaluator-model grok-4.20-0309-non-reasoning --evaluator-base-url https://api.x.ai/v1 --evaluator-api-key-env OPENAI_API_KEY --evaluator-max-completion-tokens 512 --evaluator-timeout-seconds 300
```

Result:

- Output: `tmp\official-runs\longmemeval-v2-no-retrieval-smoke\aggregated_metrics.json`
- `overall_full_set=0.0`
- `count_all_questions=1`
- `pct_answered_wrong=1.0`
- Prompt tokens `281`, completion tokens `214`, total tokens `495`

Full-run path:

```powershell
cd tmp\official-evaluators\LongMemEval-V2
.\.venv\Scripts\python.exe data\download_data.py --data-root data\longmemeval-v2
.\.venv\Scripts\python.exe data\prepare_data.py --data-root data\longmemeval-v2 --mode symlink
.\.venv\Scripts\python.exe data\validate_data.py --data-root data\longmemeval-v2 --tier small
.\.venv\Scripts\python.exe evaluation\run_eval.py --data-root data\longmemeval-v2 --domain enterprise --tier small --method no_retrieval --output-dir runs\no_retrieval_enterprise_small
```

Full-run requirement: multi-GB public data download, screenshot/tarball
validation, model/API budget, and a CEM memory module if the goal is an
official CEM backend score rather than the official no-retrieval boundary.

## MemoryArena

- Official repo: `https://github.com/ZexueHe/MemoryArena`
- Commit: `6cd9de14b71915e39ac742a20dc33785e14b6aab`
- Data source: `https://huggingface.co/datasets/ZexueHe/memoryarena`
- Bounded data: one real `formal_reasoning_math` test row and one subtask
- Local limitation found: `java` and `javac` were absent, so the shopping route
  was not used. The formal-reasoning env server route was used.

Server command:

```powershell
cd tmp\official-evaluators\MemoryArena
$env:OPENAI_API_KEY=$env:XAI_API_KEY
$env:OPENAI_BASE_URL='https://api.x.ai/v1'
.\.venv\Scripts\python.exe env\env_server.py
```

Runner boundary:

- Official `EnvironmentClient`
- Official `MathEnvironment`
- Official `MathAgent`
- Official `memory/memory_systems/long_context.py`
- Official `eval_and_print_result`

Result:

- Output:
  `tmp\official-runs\memoryarena-formal-long-context-smoke\json\long_context_grok-4.20-0309-non-reasoning\all_results.json`
- Paper id: `2503.19064`
- Subtask rows: `1` in
  `tmp\official-runs\memoryarena-formal-long-context-smoke\json\long_context_grok-4.20-0309-non-reasoning\2503.19064\result.jsonl`
- Row result: `is_correct=true`
- `overall_average_passrate=1.0`
- `avg_progress_score=1.0`
- Average session/task time: `30.3604s`
- Average memory length: `20.0`

Full-run path:

```powershell
cd tmp\official-evaluators\MemoryArena
.\.venv\Scripts\python.exe env\env_server.py
.\.venv\Scripts\python.exe run_math.py --memory-system long_context --model <model> --config-name formal_reasoning_math
```

Full-run requirement: long-lived env server with API credentials, official
domain config, model/API budget, and a CEM memory-system implementation for a
CEM-specific score. The shopping path additionally requires Java/JDK and the
WebShop product database.

## Acceptance Boundary

Accepted in this receipt:

- official setup paths inspected;
- dependencies installed locally for all three official repos;
- public dataset paths inspected and real rows materialized;
- available local credential path checked and used;
- official bounded smoke/scoring path executed for all three suites;
- exact full-run command paths recorded.

Not accepted in this receipt:

- a full official CEM leaderboard score;
- treating local proxy metrics as official benchmark metrics;
- MemoryArena shopping-domain execution;
- LongMemEval-V2 CEM memory backend integration.
