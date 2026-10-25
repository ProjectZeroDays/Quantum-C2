"""FIFO task queue with correlation IDs, results, and lifecycle management."""

from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from queue import Queue, Empty, Full

from quantum.core.db import execute, execute_one, execute_write, transaction, get_conn
from quantum.core.ids import new_task_id, new_event_id, correlation_id
from quantum.core.bus import BUS, publish_task_event, publish_device_event
from quantum.core.state import DeviceState, STATE_MACHINE
from quantum.rat.registry import get_device, update_device_state


class TaskState(str, Enum):
    """Task lifecycle states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DRY_RUN = "dry_run"


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass
class Task:
    """Task record with full lifecycle tracking."""
    id: str
    device_id: str
    module: str
    args: Dict[str, Any]
    cmd: str = ""
    state: TaskState = TaskState.QUEUED
    priority: int = TaskPriority.NORMAL
    correlation_id: str = ""
    queued: float = field(default_factory=time.time)
    started: Optional[float] = None
    finished: Optional[float] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    artifacts: List[str] = field(default_factory=list)
    error: str = ""
    dry_run: bool = False
    retries: int = 0
    max_retries: int = 0
    timeout: int = 120

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, TaskState) else self.state
        d["args"] = json.dumps(self.args)
        d["artifacts"] = json.dumps(self.artifacts)
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "Task":
        args = {}
        if row.get("args"):
            try:
                args = json.loads(row["args"])
            except Exception:
                pass
        artifacts = []
        if row.get("artifacts"):
            try:
                artifacts = json.loads(row["artifacts"])
            except Exception:
                pass
        return cls(
            id=row["id"],
            device_id=row["device_id"],
            module=row["module"],
            args=args,
            cmd=row.get("cmd", "") or "",
            state=TaskState(row.get("state", "queued")),
            priority=row.get("priority", TaskPriority.NORMAL),
            correlation_id=row.get("correlation_id", "") or "",
            queued=row.get("queued", 0) or 0,
            started=row.get("started"),
            finished=row.get("finished"),
            exit_code=row.get("exit_code"),
            stdout=row.get("stdout", "") or "",
            stderr=row.get("stderr", "") or "",
            artifacts=artifacts,
            error=row.get("error", "") or "",
            dry_run=bool(row.get("dry_run", 0)),
            retries=row.get("retries", 0) or 0,
            max_retries=row.get("max_retries", 0) or 0,
            timeout=row.get("timeout", 120) or 120,
        )

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started and self.finished:
            return self.finished - self.started
        return None

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}


# In-memory queue for real-time processing
_task_queues: Dict[str, Queue] = {}  # device_id -> Queue
_queue_lock = threading.Lock()
_worker_threads: Dict[str, threading.Thread] = {}
_shutdown = False


def _get_queue(device_id: str) -> Queue:
    """Get or create queue for a device."""
    with _queue_lock:
        if device_id not in _task_queues:
            _task_queues[device_id] = Queue(maxsize=1000)
        return _task_queues[device_id]


def queue_task(
    device_id: str,
    module: str,
    args: Dict[str, Any],
    priority: int = TaskPriority.NORMAL,
    cid_param: Optional[str] = None,
    dry_run: bool = False,
    timeout: int = 120,
    max_retries: int = 0,
) -> str:
    """Queue a task for a device."""
    device = get_device(device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")

    # Check if device can accept tasks
    if device.state in {DeviceState.DEAD, DeviceState.GHOST}:
        raise ValueError(f"Device {device_id} is in {device.state.value} state")

    task_id = new_task_id(device_id)
    cid = cid_param or correlation_id()

    task = Task(
        id=task_id,
        device_id=device_id,
        module=module,
        args=args,
        priority=priority,
        correlation_id=cid,
        dry_run=dry_run,
        timeout=timeout,
        max_retries=max_retries,
    )

    # Save to database
    with transaction() as conn:
        conn.execute(
            """INSERT INTO tasks (id, device_id, module, args, cmd, state, priority,
               correlation_id, queued, started, finished, exit_code, stdout, stderr,
               artifacts, error, dry_run, retries, max_retries, timeout)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.id, task.device_id, task.module, json.dumps(task.args), task.cmd,
             task.state.value, task.priority, task.correlation_id, task.queued,
             task.started, task.finished, task.exit_code, task.stdout, task.stderr,
             json.dumps(task.artifacts), task.error, int(task.dry_run), task.retries,
             task.max_retries, task.timeout)
        )

    # Add to in-memory queue
    queue = _get_queue(device_id)
    try:
        queue.put_nowait((priority, task_id))
    except Full:
        # Queue full - task stays in DB but won't be processed immediately
        pass

    # Ensure worker is running
    _ensure_worker(device_id)

    publish_task_event(task_id, "queued", {"module": module, "args": args}, device_id)
    return task_id


def queue_task_batch(
    device_ids: List[str],
    module: str,
    args: Dict[str, Any],
    priority: int = TaskPriority.NORMAL,
    cid_param: Optional[str] = None,
    dry_run: bool = False,
) -> List[str]:
    """Queue the same task for multiple devices."""
    cid = cid_param or correlation_id()
    task_ids = []

    for device_id in device_ids:
        try:
            tid = queue_task(
                device_id, module, args, priority, cid, dry_run
            )
            task_ids.append(tid)
        except Exception:
            pass  # Skip devices that can't accept tasks

    return task_ids


def _ensure_worker(device_id: str) -> None:
    """Ensure a worker thread is running for a device."""
    with _queue_lock:
        if device_id in _worker_threads and _worker_threads[device_id].is_alive():
            return

        thread = threading.Thread(target=_worker_loop, args=(device_id,), daemon=True)
        thread.start()
        _worker_threads[device_id] = thread


def _worker_loop(device_id: str) -> None:
    """Worker loop for processing tasks for a device."""
    queue = _get_queue(device_id)

    while not _shutdown:
        try:
            # Get next task (blocking with timeout)
            priority, task_id = queue.get(timeout=1.0)
            _process_task(task_id)
            queue.task_done()
        except Empty:
            continue
        except Exception:
            continue


def _process_task(task_id: str) -> None:
    """Process a single task."""
    task = get_task(task_id)
    if not task:
        return

    # Check if task was cancelled
    if task.state == TaskState.CANCELLED:
        return

    # Update state to running
    _update_task_state(task_id, TaskState.RUNNING, started=time.time())

    # Import module runner
    from quantum.rat.modules import run_module

    try:
        # Execute module
        result = run_module(task.device_id, task.module, task.args, task.dry_run)

        # Update task with result
        _update_task_result(
            task_id,
            exit_code=0 if result.ok else 1,
            stdout=result.raw,
            stderr=result.error,
            artifacts=[a.get("id", "") for a in result.artifacts],
        )

        # If module has next_actions, could auto-queue them
        for action in result.next_actions:
            if action.get("auto_queue", False):
                queue_task(
                    task.device_id,
                    action["module"],
                    action.get("args", {}),
                    correlation_id=task.correlation_id,
                )

    except Exception as e:
        _update_task_result(
            task_id,
            exit_code=1,
            stderr=str(e),
            error=str(e),
        )

    # Check for retries
    task = get_task(task_id)
    if task and task.state == TaskState.FAILED and task.retries < task.max_retries:
        _retry_task(task_id)


def _update_task_state(
    task_id: str,
    state: TaskState,
    started: Optional[float] = None,
    finished: Optional[float] = None,
) -> None:
    """Update task state in database."""
    updates = ["state = ?"]
    params = [state.value]

    if started:
        updates.append("started = ?")
        params.append(started)
    if finished:
        updates.append("finished = ?")
        params.append(finished)

    params.append(task_id)

    with transaction() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", tuple(params))

    publish_task_event(task_id, f"state_{state.value}", {"state": state.value})


def _update_task_result(
    task_id: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    artifacts: List[str] = None,
    error: str = "",
) -> None:
    """Update task with execution result."""
    finished = time.time()
    state = TaskState.COMPLETED if exit_code == 0 else TaskState.FAILED
    artifacts = artifacts or []

    with transaction() as conn:
        conn.execute(
            """UPDATE tasks SET state = ?, finished = ?, exit_code = ?,
               stdout = ?, stderr = ?, artifacts = ?, error = ?
               WHERE id = ?""",
            (state.value, finished, exit_code, stdout, stderr,
             json.dumps(artifacts), error, task_id)
        )

    publish_task_event(task_id, "completed" if exit_code == 0 else "failed", {
        "exit_code": exit_code,
        "artifacts": artifacts,
        "error": error,
    })


def _retry_task(task_id: str) -> None:
    """Retry a failed task."""
    task = get_task(task_id)
    if not task:
        return

    task.retries += 1
    task.state = TaskState.QUEUED
    task.started = None
    task.finished = None
    task.exit_code = None
    task.stdout = ""
    task.stderr = ""
    task.error = ""

    with transaction() as conn:
        conn.execute(
            """UPDATE tasks SET state = ?, retries = ?, started = NULL, finished = NULL,
               exit_code = NULL, stdout = '', stderr = '', error = ''
               WHERE id = ?""",
            (TaskState.QUEUED.value, task.retries, task_id)
        )

    # Re-queue
    queue = _get_queue(task.device_id)
    try:
        queue.put_nowait((task.priority, task_id))
    except Full:
        pass

    publish_task_event(task_id, "retry", {"attempt": task.retries})


def get_task(task_id: str) -> Optional[Task]:
    """Get task by ID."""
    row = execute_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not row:
        return None
    return Task.from_row(dict(row))


def get_tasks_for_device(
    device_id: str,
    state: Optional[TaskState] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Task]:
    """Get tasks for a device."""
    sql = "SELECT * FROM tasks WHERE device_id = ?"
    params: List[Any] = [device_id]

    if state:
        sql += " AND state = ?"
        params.append(state.value)

    sql += " ORDER BY queued DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = execute(sql, tuple(params))
    return [Task.from_row(dict(r)) for r in rows]


def get_pending_tasks(device_id: str) -> List[Task]:
    """Get pending (queued/running) tasks for a device."""
    return get_tasks_for_device(device_id, TaskState.QUEUED) + \
           get_tasks_for_device(device_id, TaskState.RUNNING)


def cancel_task(task_id: str) -> bool:
    """Cancel a queued or running task."""
    task = get_task(task_id)
    if not task:
        return False

    if task.state not in {TaskState.QUEUED, TaskState.RUNNING}:
        return False

    _update_task_state(task_id, TaskState.CANCELLED, finished=time.time())
    publish_task_event(task_id, "cancelled", {})
    return True


def cancel_all_tasks(device_id: str) -> int:
    """Cancel all pending tasks for a device."""
    tasks = get_pending_tasks(device_id)
    count = 0
    for task in tasks:
        if cancel_task(task.id):
            count += 1
    return count


def retry_task(task_id: str) -> bool:
    """Manually retry a failed task."""
    task = get_task(task_id)
    if not task or task.state != TaskState.FAILED:
        return False

    task.retries = 0  # Reset retries for manual retry
    return _retry_task(task_id) is not None


def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task execution result."""
    task = get_task(task_id)
    if not task:
        return None

    return {
        "task_id": task.id,
        "device_id": task.device_id,
        "module": task.module,
        "state": task.state.value,
        "exit_code": task.exit_code,
        "stdout": task.stdout,
        "stderr": task.stderr,
        "artifacts": task.artifacts,
        "error": task.error,
        "duration": task.duration,
        "started": task.started,
        "finished": task.finished,
    }


def get_tasks_by_correlation(correlation_id: str) -> List[Task]:
    """Get all tasks with a correlation ID."""
    rows = execute(
        "SELECT * FROM tasks WHERE correlation_id = ? ORDER BY queued",
        (correlation_id,)
    )
    return [Task.from_row(dict(r)) for r in rows]


def get_recent_tasks(limit: int = 50, device_id: Optional[str] = None) -> List[Task]:
    """Get recent tasks across all devices or for a specific device."""
    if device_id:
        rows = execute(
            "SELECT * FROM tasks WHERE device_id = ? ORDER BY queued DESC LIMIT ?",
            (device_id, limit)
        )
    else:
        rows = execute(
            "SELECT * FROM tasks ORDER BY queued DESC LIMIT ?",
            (limit,)
        )
    return [Task.from_row(dict(r)) for r in rows]


def get_task_stats(device_id: Optional[str] = None) -> Dict[str, Any]:
    """Get task statistics."""
    if device_id:
        where = "WHERE device_id = ?"
        params = (device_id,)
    else:
        where = ""
        params = ()

    rows = execute(
        f"SELECT state, COUNT(*) as c FROM tasks {where} GROUP BY state",
        params
    )

    stats = {s.value: 0 for s in TaskState}
    for r in rows:
        stats[r["state"]] = r["c"]

    # Add totals
    stats["total"] = sum(stats.values())
    stats["pending"] = stats.get(TaskState.QUEUED.value, 0) + stats.get(TaskState.RUNNING.value, 0)
    stats["completed"] = stats.get(TaskState.COMPLETED.value, 0)
    stats["failed"] = stats.get(TaskState.FAILED.value, 0)

    return stats


def clear_completed_tasks(device_id: str, older_than_days: int = 7) -> int:
    """Clear completed/failed/cancelled tasks older than N days."""
    cutoff = time.time() - (older_than_days * 86400)

    with transaction() as conn:
        cursor = conn.execute(
            """DELETE FROM tasks WHERE device_id = ? AND state IN (?, ?, ?)
               AND finished < ?""",
            (device_id, TaskState.COMPLETED.value, TaskState.FAILED.value,
             TaskState.CANCELLED.value, cutoff)
        )
    return cursor.rowcount


def shutdown_workers() -> None:
    """Shutdown all worker threads."""
    global _shutdown
    _shutdown = True

    # Wait for queues to drain
    for queue in _task_queues.values():
        queue.join()

    # Wait for threads
    for thread in _worker_threads.values():
        thread.join(timeout=5)

    _worker_threads.clear()


# Dry-run support

def dry_run_task(device_id: str, module: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a dry-run of a task (show what would execute)."""
    task_id = queue_task(device_id, module, args, dry_run=True)

    # Wait for completion (with timeout)
    for _ in range(50):  # 5 seconds max
        task = get_task(task_id)
        if task and task.is_terminal:
            return get_task_result(task_id)
        time.sleep(0.1)

    return {"error": "Dry-run timeout", "task_id": task_id}