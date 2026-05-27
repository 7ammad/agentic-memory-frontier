# Memory Frontier Foundation Report

Yes. Brutally honest: **a massive research pass is necessary, but only if it is weaponized into a sharper thesis and a publishable product plan.** If we just “read more papers,” we’ll drown. If we turn the research into a new Plan 1 foundation, this could become genuinely interesting.

The big shift is this:

**This should not be “Hammad’s memory system for Claude/Codex/OpenClaw/Hermes.”**

It should be:

> **A universal agent memory substrate that can onboard any agent stack in one command, give every agent a stable identity, enforce memory visibility, preserve provenance, detect stale knowledge, and let agents share memory safely.**

That is the head-turning version.

The market opening is real. Hassabis is basically pointing at the same hole: current systems still need “continual learning, better memory, longer context windows — or perhaps more efficient context windows,” and he explicitly says not to store everything, only the important things. That is exactly the wedge. He also separately describes current systems as trained/frozen and missing online continual learning from experience. Sources: [CMSWire interview](https://www.cmswire.com/digital-experience/inside-google-deepminds-ai-strategy/) and [Financial Express coverage](https://www.financialexpress.com/business/news/agi-still-years-away-deepmind-ceo/4147791/).

**My Honest Take**

Claude’s Plan 1 is a good internal baseline. It is not yet the foundation for an open-source project that turns heads.

It did identify useful pieces from the field: typed memory, temporal validity, supersession, visibility, identity, telemetry, migration discipline. But it is still framed around **SuperClaude memory as the center of gravity**. For OSS, that is too narrow.

The new center should be:

**Agent onboarding + trustworthy shared memory.**

Not “better vector recall.”

The sentence I’d want people to repeat is:

> “Agent memory is not just retrieval. It is identity, provenance, lifecycle, and trust across agent teams.”

That is stronger than most memory projects.

**Why Research Is Mandatory**

The field has moved past simple long-term chat recall. Current benchmark and research signals show the frontier splitting into several harder dimensions:

LongMemEval tests five long-term memory abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. Useful, but still chat-assistant shaped. Source: [LongMemEval paper](https://arxiv.org/abs/2410.10813).

The 2026 survey frames agent memory as a write-manage-read loop and says open gaps include continual consolidation, causally grounded retrieval, trustworthy reflection, learned forgetting, and multimodal embodied memory. Source: [Memory for Autonomous LLM Agents](https://arxiv.org/abs/2603.07670).

StructMemEval argues that many benchmarks over-focus on fact retention and do not test whether agents can organize memory into useful structures like ledgers, task trees, and other persistent state. Source: [StructMemEval](https://arxiv.org/abs/2602.11243).

LongMemEval-V2 moves toward “experienced colleague” memory in web environments: workflows, recurring failure modes, dynamic state, premise awareness, and environment gotchas across up to 115M tokens of history. That is much closer to coding agents and Hermes/OpenClaw workflows. Source: [LongMemEval-V2](https://arxiv.org/abs/2605.12493).

MemGym explicitly says existing benchmarks over-focus on personalized chat and transfer poorly to coding and web navigation. It includes coding, deep research, tool-use dialogue, and computer-use regimes. Source: [MemGym](https://arxiv.org/abs/2605.20833).

So yes: **Plan 1 needs to be upgraded from “SC memory review” into “Memory Frontier Research + OSS Positioning.”**

**The Approach I’d Take**

I would create a new **Plan 1R: Public Foundation Research Pack** before continuing B/C/D seriously.

It should have three outputs.

First: **Research Map**
A tight, current map of memory research:
- conversational memory: LongMemEval, LoCoMo;
- agentic memory: MemGym, MemoryAgentBench, AMemGym;
- structural memory: StructMemEval;
- environment/workflow memory: LongMemEval-V2;
- reflective/self-improving memory: Hindsight, Letta-style approaches;
- graph/temporal memory: Zep/Graphiti, Cognee;
- coding-agent memory: SWE-Gym/MemGym/code runbook style;
- trust/security memory: poisoning, stale facts, visibility, provenance.

Second: **Competitor Matrix**
Not just “Mem0 vs Zep vs Letta.” We need a serious matrix across:
- Mem0/OpenMemory;
- Zep/Graphiti;
- Letta;
- Hindsight;
- Cognee;
- LangMem;
- Mastra Observational Memory;
- OMEGA;
- ByteRover;
- Supermemory;
- Memvid;
- maybe emerging benchmark-first systems like Engram/MemPalace/Exabase if sources check out.

But I’d be careful: many benchmark claims are vendor-reported. The Mem0 benchmark repo is useful because it gives runnable LOCOMO, LongMemEval, and BEAM scripts, but benchmark marketing is getting noisy. Source: [mem0ai/memory-benchmarks](https://github.com/mem0ai/memory-benchmarks). Hindsight also has a public benchmark page showing scores across AMB datasets, but we should treat that as leaderboard/claim evidence until we reproduce. Source: [Hindsight benchmarks](https://benchmarks.hindsight.vectorize.io/).

Third: **Public Product Thesis**
This is where we decide the wedge. My recommendation:

> **Universal Agent Memory Onboarding. One command. Any agent. Safe shared memory.**

Example future UX:

```bash
ams init
ams onboard claude
ams onboard codex
ams onboard hermes
ams onboard openclaw
ams onboard cursor
ams onboard custom --name my-agent --mcp "node server.js"
```

The core abstraction should be:

```text
Agent = identity + connector + capabilities + memory policy
```

Where:
- identity = ed25519 keypair, stable `agent_id`;
- connector = MCP stdio/http, CLI adapter, HTTP webhook, file watcher, or Hermes/OpenClaw bridge;
- capabilities = what the agent can read/write/share;
- memory policy = private/shared defaults, review_after, retention, scopes;
- onboarding = writes config, starts health check, registers agent card, runs smoke test.

Hermes/OpenClaw/Claude/Codex should be **adapters**, not the core. That is the difference between “cool local hack” and “real OSS foundation.”

**What Would Turn Heads**

Not “we support vector search.”

This would turn heads:

1. **One-command agent onboarding**
People can plug in their stack immediately.

2. **Trust-aware memory**
Every memory has who wrote it, why, when, visibility, validity, supersession, and review state.

3. **Stale-memory workflow**
The system tells you “this may no longer be true” instead of silently poisoning agents.

4. **Agent-team memory**
Claude, Codex, Hermes, OpenClaw, Cursor, etc. can share selected memory without collapsing into one unsafe soup.

5. **Reproducible benchmarks**
Run LongMemEval, LOCOMO/BEAM, StructMemEval, and at least one coding/workflow benchmark. Publish scripts, not just numbers.

6. **A public manifesto**
Something like: “Agent memory is a trust boundary, not a vector database.”

**Where I’d Be Careful**

Do not overbuild ACS before the memory core is clean. ACS is exciting, but it can become protocol fog. For v0.1, the killer demo is not Bayes-factor disagreement. It is:

> Install AMS, onboard two agents, save private and shared memories, prove visibility boundaries, hand off a task, detect stale memory, and reproduce a benchmark.

That is enough.

Also, do not chase every benchmark leaderboard. Some are already becoming gamed by retrieval tricks, huge context windows, or vendor-specific settings. We should benchmark, but the public claim should be sober:

> “We optimize for trustworthy multi-agent memory, not just recall score.”

That stance will age better.

**My Recommendation**

Yes, do the massive research. But make it a **bounded research sprint** with a concrete artifact:

**Plan 1R: Open-Source Agentic Memory Foundation**
- latest research map;
- benchmark map;
- competitor matrix;
- public wedge;
- architecture principles;
- v0.1/v0.2/v1 roadmap;
- exact acceptance tests;
- one-command onboarding contract.

Then we revisit B/C/D through that lens. Some current work survives. Some gets demoted. Some needs to be rebuilt cleaner.

The brutal answer: **the current baseline can become the seed of something serious, but only if we stop treating SuperClaude as the center and make “any agent in your stack, onboarded safely in one command” the center.** That is the version with a real shot at getting noticed.
