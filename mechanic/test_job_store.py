from datetime import datetime, timedelta, timezone

import pytest

from mechanic.job_store import JobLeaseError, SQLiteJobStore, _stamp


def test_enqueue_and_claim_survive_store_recreation(tmp_path):
    path = tmp_path / "jobs.sqlite3"
    first = SQLiteJobStore(path)
    queued = first.enqueue({"task": "inspect", "target": "repo"})
    second = SQLiteJobStore(path)
    claimed = second.claim_next("worker-a")
    assert claimed.id == queued.id
    assert claimed.payload["task"] == "inspect"
    assert claimed.status == "running"
    assert claimed.attempts == 1
    assert first.get(queued.id).status == "running"


def test_only_lease_owner_can_complete(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "test"})
    store.claim_next("worker-a")
    with pytest.raises(JobLeaseError):
        store.complete(job.id, "worker-b", {"ok": True})
    done = store.complete(job.id, "worker-a", {"ok": True})
    assert done.status == "completed"
    assert done.result == {"ok": True}
    assert done.lease_owner is None


def test_retryable_failure_obeys_attempt_limit(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "retry"}, max_attempts=2)
    store.claim_next("worker-a")
    assert store.fail(job.id, "worker-a", "temporary outage").status == "queued"
    second = store.claim_next("worker-b")
    assert second.attempts == 2
    assert store.fail(job.id, "worker-b", "still unavailable").status == "failed"
    assert store.claim_next("worker-c") is None


def test_expired_lease_is_reclaimed_and_old_worker_rejected(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "recover"}, max_attempts=2)
    first = store.claim_next("worker-a", lease_seconds=1)
    with store._connect() as db:
        expired = _stamp(datetime.now(timezone.utc) - timedelta(seconds=5))
        db.execute("UPDATE mechanic_jobs SET lease_until=? WHERE id=?", (expired, job.id))
    second = store.claim_next("worker-b")
    assert second.id == first.id
    assert second.attempts == 2
    with pytest.raises(JobLeaseError):
        store.complete(job.id, "worker-a", {"stale": True})


def test_expired_job_at_retry_limit_is_failed(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "stop"}, max_attempts=1)
    store.claim_next("worker-a", lease_seconds=1)
    with store._connect() as db:
        expired = _stamp(datetime.now(timezone.utc) - timedelta(seconds=5))
        db.execute("UPDATE mechanic_jobs SET lease_until=? WHERE id=?", (expired, job.id))
    assert store.claim_next("worker-b") is None
    assert store.get(job.id).status == "failed"


def test_lease_can_be_renewed_by_current_owner(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "long-running"})
    claimed = store.claim_next("worker-a", lease_seconds=5)
    original_expiry = claimed.lease_until

    renewed = store.renew_lease(job.id, "worker-a", lease_seconds=120)

    assert renewed.status == "running"
    assert renewed.lease_owner == "worker-a"
    assert renewed.lease_until > original_expiry
    assert store.complete(job.id, "worker-a", {"ok": True}).status == "completed"


def test_lease_cannot_be_renewed_by_another_worker(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "protected"})
    store.claim_next("worker-a")
    with pytest.raises(JobLeaseError):
        store.renew_lease(job.id, "worker-b")


def test_expired_lease_cannot_be_renewed(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue({"task": "expired"})
    store.claim_next("worker-a")
    with store._connect() as db:
        expired = _stamp(datetime.now(timezone.utc) - timedelta(seconds=5))
        db.execute("UPDATE mechanic_jobs SET lease_until=? WHERE id=?", (expired, job.id))
    with pytest.raises(JobLeaseError):
        store.renew_lease(job.id, "worker-a")


def test_invalid_inputs_are_rejected(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    with pytest.raises(ValueError):
        store.enqueue({"task": "bad"}, max_attempts=0)
    with pytest.raises(ValueError):
        store.claim_next(" ")
    with pytest.raises(ValueError):
        store.claim_next("worker-a", lease_seconds=0)
    job = store.enqueue({"task": "lease-validation"})
    store.claim_next("worker-a")
    with pytest.raises(ValueError):
        store.renew_lease(job.id, "worker-a", lease_seconds=0)
