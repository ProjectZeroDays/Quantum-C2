"""quantum.core.tasks — Task lifecycle with correlation IDs.

Real FIFO task queue with task_id, state, started, stdout, stderr, exit_code, artifacts[].
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    ok: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    artifacts: list = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "artifacts": self.artifacts,
            "data": self.data,
        }


@dataclass
class Task:
    """A task in the lifecycle."""
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    device_id: str = ""
    module: str = ""
    operation: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    state: str = "queued"  # queued | running | completed | failed | canceled
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[TaskResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "device_id": self.device_id,
            "module": self.module,
            "operation": self.operation,
            "args": self.args,
            "state": self.state,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result.to_dict() if self.result else None,
        }


class TaskQueue:
    """FIFO task queue with correlation IDs."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._queue: list = []  # FIFO of task_ids

    def create(self, task: Task) -> Task:
        """Create and enqueue a task."""
        task_id = task.task_id or uuid.uuid4().hex
        task.task_id = task_id
        task.state = "queued"
        task.created_at = datetime.now().isoformat()
        task.started_at = None
        task.completed_at = None
        task.result = None
        
        self._tasks[task_id] = task
        self._queue.append(task_id)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update(self, task_id: str, updates: Dict[str, Any]):
        """Update task fields."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task.__dict__.update({k: v for k, v in updates.items() if hasattr(task, k)})
        task.completed_at = task.completed_at or (datetime.now().isoformat() if task.state in ("completed", "failed", "canceled") else None)
        return task

    def complete(self, task_id: str, result: TaskResult) -> Task:
        """Mark task as completed with result."""
        task = self.update(task_id, {
            "state": "completed" if result.ok else "failed",
            "completed_at": datetime.now().isoformat(),
            "result": result,
        })
        return task

    def fail(self, task_id: str, error: str) -> Task:
        """Mark task as failed."""
        task = self.update(task_id, {
            "state": "failed",
            "completed_at": datetime.now().isoformat(),
            "result": TaskResult(task_id=task_id, ok=False, stderr=str(error)),
        })
        return task

    def cancel(self, task_id: str) -> Task:
        """Cancel a task."""
        task = self.update(task_id, {"state": "canceled"})
        return task

    def get_next(self) -> Optional[Task]:
        """Get next task from FIFO queue."""
        while self._queue:
            task_id = self._queue.pop(0)
            task = self._tasks.get(task_id)
            if task and task.state in ("queued",):
                task.state = "running"
                task.started_at = datetime.now().isoformat()
                return task
        return None

    def get_pending(self, device_id: str = None, limit: int = 100) -> list:
        """Get pending tasks, optionally for a device."""
        pending = [
            task for task in self._tasks.values()
            if task.state == "queued"
            and (device_id is None or task.device_id == device_id)
        ]
        return pending[-limit:]


# Global task queue instance
_task_queue = TaskQueue()


def get_task_queue() -> TaskQueue:
    """Get global task queue."""
    return _task_queue


def create_task(task: Task) -> Task:
    """Create task using global queue."""
    return _task_queue.create(task)
