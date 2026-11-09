"""Durable, provider-neutral job storage for the Ori Mechanic control plane."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class JobLeaseError(RuntimeError):
    """Raised when a worker attempts to finish a job without an active lease."""


@dataclass(frozen=True)
class Job:
    id: str
    payload: dict[str, Any]
    status: str
    attempts: int
    max_attempts: int
    created_at: str
    updated_at: str
    lease_owner: str | None = None
    lease_until: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


class SQLiteJobStore:
    """SQLite queue with atomic claims, expiring leases, and bounded retries.

    Hosted deployments must mount a persistent volume at the database path.
    Multi-instance deployments should use a shared transactional DB adapter.
    """

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS mechanic_jobs (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('queued', 'running', 'completed', 'failed')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_until TEXT,
                    result TEXT,
                    error TEXT
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_queue ON mechanic_jobs(status, created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_lease ON mechanic_jobs(status, lease_until)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 10000")
        if self.database != ":memory:":
            db.execute("PRAGMA journal_mode = WAL")
        return db

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> Job | None:
        if row is None:
            return None
        return Job(
            id=row["id"], payload=json.loads(row["payload"]), status=row["status"],
            attempts=row["attempts"], max_attempts=row["max_attempts"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            lease_owner=row["lease_owner"], lease_until=row["lease_until"],
            result=json.loads(row["result"]) if row["result"] is not None else None,
            error=row["error"],
        )

    def enqueue(self, payload: dict[str, Any], *, max_attempts: int = 3) -> Job:
        if not isinstance(payload, dict):
            raise TypeError("job payload must be a dictionary")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        now, job_id = _stamp(_now()), str(uuid.uuid4())
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        with self._connect() as db:
            db.execute(
                """INSERT INTO mechanic_jobs
                (id,payload,status,attempts,max_attempts,created_at,updated_at)
                VALUES (?,?,'queued',0,?,?,?)""",
                (job_id, encoded, max_attempts, now, now),
            )
            row = db.execute("SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)).fetchone()
        job = self._decode(row)
        assert job is not None
        return job

    def get(self, job_id: str) -> Job | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)).fetchone()
        return self._decode(row)

    def claim_next(self, worker_id: str, *, lease_seconds: int = 60) -> Job | None:
        if not worker_id.strip():
            raise ValueError("worker_id must not be empty")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        now = _now()
        now_text, lease_text = _stamp(now), _stamp(now + timedelta(seconds=lease_seconds))
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE mechanic_jobs
                SET status=CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END,
                    lease_owner=NULL, lease_until=NULL,
                    error=CASE WHEN attempts < max_attempts
                        THEN 'worker lease expired; queued for retry'
                        ELSE 'worker lease expired; retry limit reached' END,
                    updated_at=?
                WHERE status='running' AND lease_until <= ?""",
                (now_text, now_text),
            )
            row = db.execute(
                """SELECT id FROM mechanic_jobs
                WHERE status='queued' AND attempts < max_attempts
                ORDER BY created_at,id LIMIT 1"""
            ).fetchone()
            if row is None:
                db.commit()
                return None
            job_id = row["id"]
            db.execute(
                """UPDATE mechanic_jobs SET status='running', attempts=attempts+1,
                lease_owner=?, lease_until=?, updated_at=?, error=NULL
                WHERE id=? AND status='queued'""",
                (worker_id, lease_text, now_text, job_id),
            )
            claimed = db.execute("SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)).fetchone()
            db.commit()
        return self._decode(claimed)

    def complete(self, job_id: str, worker_id: str, result: dict[str, Any]) -> Job:
        if not isinstance(result, dict):
            raise TypeError("job result must be a dictionary")
        return self._finish(job_id, worker_id, "completed", result)

    def fail(self, job_id: str, worker_id: str, error: str, *, retryable: bool = True) -> Job:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._decode(db.execute(
                "SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)
            ).fetchone())
            self._assert_lease(job, worker_id)
            assert job is not None
            status = "queued" if retryable and job.attempts < job.max_attempts else "failed"
            now = _stamp(_now())
            db.execute(
                """UPDATE mechanic_jobs SET status=?, lease_owner=NULL, lease_until=NULL,
                error=?, updated_at=? WHERE id=?""",
                (status, error[:2000], now, job_id),
            )
            row = db.execute("SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)).fetchone()
            db.commit()
        finished = self._decode(row)
        assert finished is not None
        return finished

    def _finish(self, job_id: str, worker_id: str, status: str, result: dict[str, Any]) -> Job:
        encoded, now = json.dumps(result, separators=(",", ":"), sort_keys=True), _stamp(_now())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._decode(db.execute(
                "SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)
            ).fetchone())
            self._assert_lease(job, worker_id)
            db.execute(
                """UPDATE mechanic_jobs SET status=?, result=?, lease_owner=NULL,
                lease_until=NULL, error=NULL, updated_at=? WHERE id=?""",
                (status, encoded, now, job_id),
            )
            row = db.execute("SELECT * FROM mechanic_jobs WHERE id=?", (job_id,)).fetchone()
            db.commit()
        finished = self._decode(row)
        assert finished is not None
        return finished

    @staticmethod
    def _assert_lease(job: Job | None, worker_id: str) -> None:
        if job is None:
            raise JobLeaseError("job does not exist")
        if (job.status != "running" or job.lease_owner != worker_id
                or job.lease_until is None or job.lease_until <= _stamp(_now())):
            raise JobLeaseError("worker does not hold an active lease for this job")
