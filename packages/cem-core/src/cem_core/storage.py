from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from .models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    AgentTrace,
    ExperienceAtom,
    ExperienceCard,
    ValidationDecision,
    ValidationResult,
    VerificationProbe,
    VerificationResult,
)


class CEMStore(Protocol):
    def save_trace(self, trace: AgentTrace) -> None: ...
    def get_trace(self, trace_id: str) -> AgentTrace: ...
    def save_atom(self, atom: ExperienceAtom) -> None: ...
    def get_atom(self, atom_id: str) -> ExperienceAtom: ...
    def list_atoms(self) -> list[ExperienceAtom]: ...
    def save_card(self, card: ExperienceCard) -> None: ...
    def get_card(self, card_id: str) -> ExperienceCard: ...
    def list_cards(self) -> list[ExperienceCard]: ...
    def save_validation(self, result: ValidationResult) -> None: ...
    def list_validations(self, atom_id: str) -> list[ValidationResult]: ...
    def save_validation_decision(self, decision: ValidationDecision) -> None: ...
    def list_validation_decisions(self, atom_id: str) -> list[ValidationDecision]: ...
    def get_latest_validation_decision(self, atom_id: str) -> ValidationDecision | None: ...
    def save_probe(self, probe: VerificationProbe) -> None: ...
    def get_probe(self, probe_id: str) -> VerificationProbe: ...
    def list_probes(self) -> list[VerificationProbe]: ...
    def save_verification_result(self, result: VerificationResult) -> None: ...
    def list_verification_results(self, card_id: str) -> list[VerificationResult]: ...
    def save_action_brief_record(self, record: ActionBriefRecord) -> None: ...
    def get_action_brief_record(self, brief_id: str) -> ActionBriefRecord: ...
    def save_action_influence_event(self, event: ActionInfluenceEvent) -> None: ...
    def list_action_influence_events(self, influence_id: str) -> list[ActionInfluenceEvent]: ...


class SQLiteStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "cem.sqlite"
        self.trace_log_path = self.root / "traces.jsonl"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS atoms (
                    atom_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cards (
                    card_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atom_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS validation_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atom_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS verification_probes (
                    probe_id TEXT PRIMARY KEY,
                    target_card_id TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS verification_results (
                    result_id TEXT PRIMARY KEY,
                    card_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_brief_records (
                    brief_id TEXT PRIMARY KEY,
                    influence_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_influence_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    influence_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def save_trace(self, trace: AgentTrace) -> None:
        payload = trace.model_dump_json()
        with self.trace_log_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO traces(trace_id, payload) VALUES(?, ?)",
                (trace.trace_id, payload),
            )

    def get_trace(self, trace_id: str) -> AgentTrace:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Trace not found: {trace_id}")
        return AgentTrace.model_validate_json(row[0])

    def save_atom(self, atom: ExperienceAtom) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO atoms(atom_id, payload) VALUES(?, ?)",
                (atom.atom_id, atom.model_dump_json()),
            )

    def get_atom(self, atom_id: str) -> ExperienceAtom:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM atoms WHERE atom_id = ?",
                (atom_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Atom not found: {atom_id}")
        return ExperienceAtom.model_validate_json(row[0])

    def list_atoms(self) -> list[ExperienceAtom]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM atoms").fetchall()
        return [ExperienceAtom.model_validate_json(row[0]) for row in rows]

    def save_card(self, card: ExperienceCard) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cards(card_id, payload) VALUES(?, ?)",
                (card.card_id, card.model_dump_json()),
            )

    def get_card(self, card_id: str) -> ExperienceCard:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM cards WHERE card_id = ?",
                (card_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Card not found: {card_id}")
        return ExperienceCard.model_validate_json(row[0])

    def list_cards(self) -> list[ExperienceCard]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM cards").fetchall()
        return [ExperienceCard.model_validate_json(row[0]) for row in rows]

    def save_validation(self, result: ValidationResult) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO validations(atom_id, payload) VALUES(?, ?)",
                (result.atom_id, result.model_dump_json()),
            )

    def list_validations(self, atom_id: str) -> list[ValidationResult]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM validations WHERE atom_id = ? ORDER BY id",
                (atom_id,),
            ).fetchall()
        return [ValidationResult.model_validate_json(row[0]) for row in rows]

    def save_validation_decision(self, decision: ValidationDecision) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO validation_decisions(atom_id, payload) VALUES(?, ?)",
                (decision.atom_id, decision.model_dump_json()),
            )

    def list_validation_decisions(self, atom_id: str) -> list[ValidationDecision]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM validation_decisions WHERE atom_id = ? ORDER BY id",
                (atom_id,),
            ).fetchall()
        return [ValidationDecision.model_validate_json(row[0]) for row in rows]

    def get_latest_validation_decision(self, atom_id: str) -> ValidationDecision | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM validation_decisions WHERE atom_id = ? ORDER BY id DESC LIMIT 1",
                (atom_id,),
            ).fetchone()
        if row is None:
            return None
        return ValidationDecision.model_validate_json(row[0])

    def save_probe(self, probe: VerificationProbe) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO verification_probes(probe_id, target_card_id, payload) VALUES(?, ?, ?)",
                (probe.probe_id, probe.target_card_id, probe.model_dump_json()),
            )

    def get_probe(self, probe_id: str) -> VerificationProbe:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM verification_probes WHERE probe_id = ?", (probe_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Probe not found: {probe_id}")
        return VerificationProbe.model_validate_json(row[0])

    def list_probes(self) -> list[VerificationProbe]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM verification_probes").fetchall()
        return [VerificationProbe.model_validate_json(row[0]) for row in rows]

    def save_verification_result(self, result: VerificationResult) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO verification_results(result_id, card_id, payload) VALUES(?, ?, ?)",
                (result.result_id, result.card_id, result.model_dump_json()),
            )

    def list_verification_results(self, card_id: str) -> list[VerificationResult]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM verification_results WHERE card_id = ? ORDER BY rowid",
                (card_id,),
            ).fetchall()
        return [VerificationResult.model_validate_json(row[0]) for row in rows]

    def save_action_brief_record(self, record: ActionBriefRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO action_brief_records(brief_id, influence_id, payload) VALUES(?, ?, ?)",
                (record.brief_id, record.influence_id, record.model_dump_json()),
            )

    def get_action_brief_record(self, brief_id: str) -> ActionBriefRecord:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM action_brief_records WHERE brief_id = ?", (brief_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Action brief record not found: {brief_id}")
        return ActionBriefRecord.model_validate_json(row[0])

    def save_action_influence_event(self, event: ActionInfluenceEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO action_influence_events(influence_id, payload) VALUES(?, ?)",
                (event.influence_id, event.model_dump_json()),
            )

    def list_action_influence_events(self, influence_id: str) -> list[ActionInfluenceEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM action_influence_events WHERE influence_id = ? ORDER BY id",
                (influence_id,),
            ).fetchall()
        return [ActionInfluenceEvent.model_validate_json(row[0]) for row in rows]


class InMemoryStore:
    """Local test/eval backend that exercises the same storage contract without files."""

    def __init__(self) -> None:
        self._traces: dict[str, str] = {}
        self._atoms: dict[str, str] = {}
        self._cards: dict[str, str] = {}
        self._validations: list[tuple[str, str]] = []
        self._validation_decisions: list[tuple[str, str]] = []
        self._probes: dict[str, str] = {}
        self._verification_results: list[tuple[str, str]] = []
        self._action_brief_records: dict[str, str] = {}
        self._action_influence_events: list[tuple[str, str]] = []

    def save_trace(self, trace: AgentTrace) -> None:
        self._traces[trace.trace_id] = trace.model_dump_json()

    def get_trace(self, trace_id: str) -> AgentTrace:
        payload = self._traces.get(trace_id)
        if payload is None:
            raise KeyError(f"Trace not found: {trace_id}")
        return AgentTrace.model_validate_json(payload)

    def save_atom(self, atom: ExperienceAtom) -> None:
        self._atoms[atom.atom_id] = atom.model_dump_json()

    def get_atom(self, atom_id: str) -> ExperienceAtom:
        payload = self._atoms.get(atom_id)
        if payload is None:
            raise KeyError(f"Atom not found: {atom_id}")
        return ExperienceAtom.model_validate_json(payload)

    def list_atoms(self) -> list[ExperienceAtom]:
        return [ExperienceAtom.model_validate_json(payload) for payload in self._atoms.values()]

    def save_card(self, card: ExperienceCard) -> None:
        self._cards[card.card_id] = card.model_dump_json()

    def get_card(self, card_id: str) -> ExperienceCard:
        payload = self._cards.get(card_id)
        if payload is None:
            raise KeyError(f"Card not found: {card_id}")
        return ExperienceCard.model_validate_json(payload)

    def list_cards(self) -> list[ExperienceCard]:
        return [ExperienceCard.model_validate_json(payload) for payload in self._cards.values()]

    def save_validation(self, result: ValidationResult) -> None:
        self._validations.append((result.atom_id, result.model_dump_json()))

    def list_validations(self, atom_id: str) -> list[ValidationResult]:
        return [
            ValidationResult.model_validate_json(payload)
            for stored_atom_id, payload in self._validations
            if stored_atom_id == atom_id
        ]

    def save_validation_decision(self, decision: ValidationDecision) -> None:
        self._validation_decisions.append((decision.atom_id, decision.model_dump_json()))

    def list_validation_decisions(self, atom_id: str) -> list[ValidationDecision]:
        return [
            ValidationDecision.model_validate_json(payload)
            for stored_atom_id, payload in self._validation_decisions
            if stored_atom_id == atom_id
        ]

    def get_latest_validation_decision(self, atom_id: str) -> ValidationDecision | None:
        for stored_atom_id, payload in reversed(self._validation_decisions):
            if stored_atom_id == atom_id:
                return ValidationDecision.model_validate_json(payload)
        return None

    def save_probe(self, probe: VerificationProbe) -> None:
        self._probes[probe.probe_id] = probe.model_dump_json()

    def get_probe(self, probe_id: str) -> VerificationProbe:
        payload = self._probes.get(probe_id)
        if payload is None:
            raise KeyError(f"Probe not found: {probe_id}")
        return VerificationProbe.model_validate_json(payload)

    def list_probes(self) -> list[VerificationProbe]:
        return [VerificationProbe.model_validate_json(payload) for payload in self._probes.values()]

    def save_verification_result(self, result: VerificationResult) -> None:
        self._verification_results.append((result.card_id, result.model_dump_json()))

    def list_verification_results(self, card_id: str) -> list[VerificationResult]:
        return [
            VerificationResult.model_validate_json(payload)
            for stored_card_id, payload in self._verification_results
            if stored_card_id == card_id
        ]

    def save_action_brief_record(self, record: ActionBriefRecord) -> None:
        self._action_brief_records[record.brief_id] = record.model_dump_json()

    def get_action_brief_record(self, brief_id: str) -> ActionBriefRecord:
        payload = self._action_brief_records.get(brief_id)
        if payload is None:
            raise KeyError(f"Action brief record not found: {brief_id}")
        return ActionBriefRecord.model_validate_json(payload)

    def save_action_influence_event(self, event: ActionInfluenceEvent) -> None:
        self._action_influence_events.append((event.influence_id, event.model_dump_json()))

    def list_action_influence_events(self, influence_id: str) -> list[ActionInfluenceEvent]:
        return [
            ActionInfluenceEvent.model_validate_json(payload)
            for stored_influence_id, payload in self._action_influence_events
            if stored_influence_id == influence_id
        ]
