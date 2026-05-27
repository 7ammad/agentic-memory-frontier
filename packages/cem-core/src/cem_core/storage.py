from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import AgentTrace, ExperienceAtom, ExperienceCard, ValidationDecision, ValidationResult


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
