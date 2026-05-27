# CEM-0 Storage Backends

Date: 2026-05-27

Status: V0 backend abstraction

## Scope

This slice makes CEM-0 backend-agnostic without turning the project into a storage platform.

The kernel now writes through a `CEMStore` protocol. Two local backends implement it:

- `SQLiteStore`: default persistent backend used by `CEM(root)`.
- `InMemoryStore`: file-free backend for deterministic tests, eval fixtures, and runner experiments.

## Non-Claim

This is not MCP integration, not a hosted memory API, and not a vector/database adapter layer.

The purpose is to keep CEM-0's validated-experience primitive above storage while preserving the current SQLite + JSONL default.

## Usage

Default persistent storage:

```python
from cem_core import CEM

cem = CEM("tmp/cem-run")
```

In-memory backend:

```python
from cem_core import CEM, InMemoryStore

cem = CEM(store=InMemoryStore())
```

`CEM` accepts exactly one storage configuration: either `root` or `store`.

## Contract

`CEMStore` covers the current kernel persistence surface:

- traces;
- atoms;
- cards;
- validation results;
- validation decisions.

The validator and kernel depend on this protocol instead of a concrete SQLite class.

## Verification

The storage slice is covered by `tests/test_cem_kernel.py`:

- `test_storage_backend_can_be_swapped_to_in_memory`
- `test_cem_requires_exactly_one_storage_backend`

