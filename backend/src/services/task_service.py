"""
Task service for tracking asynchronous background operations.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents an asynchronous task."""
    id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskService:
    """
    Service for managing asynchronous tasks.
    
    Stores task status in memory and provides thread-safe access.
    Tasks are automatically cleaned up after a configurable TTL.
    """
    
    def __init__(self, task_ttl_seconds: int = 3600):
        """
        Initialize the task service.
        
        Args:
            task_ttl_seconds: Time-to-live for completed tasks (default: 1 hour)
        """
        self._tasks: Dict[str, Task] = {}
        self._lock = Lock()
        self._task_ttl = timedelta(seconds=task_ttl_seconds)
        logger.info(f"TaskService initialized with TTL: {task_ttl_seconds}s")
    
    def create_task(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new task and return its ID.
        
        Args:
            metadata: Optional metadata to store with the task
            
        Returns:
            Task ID (UUID string)
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            id=task_id,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        logger.info(f"Created task {task_id}")
        return task_id
    
    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update task status and optionally set result or error.
        
        Args:
            task_id: Task ID to update
            status: New status
            result: Result data (for completed tasks)
            error: Error message (for failed tasks)
            
        Returns:
            True if task was updated, False if task not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for status update")
                return False
            
            task.status = status
            task.updated_at = datetime.now()
            
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
        
        logger.info(f"Task {task_id} status updated to {status}")
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status and details.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Dictionary with task details or None if not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            return {
                "id": task.id,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "result": task.result,
                "error": task.error,
                "metadata": task.metadata,
            }
    
    def mark_processing(self, task_id: str) -> bool:
        """Mark a task as processing."""
        return self.update_status(task_id, TaskStatus.PROCESSING)
    
    def mark_completed(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed with result data."""
        return self.update_status(task_id, TaskStatus.COMPLETED, result=result)
    
    def mark_failed(self, task_id: str, error: str) -> bool:
        """Mark a task as failed with error message."""
        return self.update_status(task_id, TaskStatus.FAILED, error=error)
    
    def cleanup_old_tasks(self) -> int:
        """
        Remove tasks older than TTL.
        
        Returns:
            Number of tasks cleaned up
        """
        now = datetime.now()
        tasks_to_remove = []
        
        with self._lock:
            for task_id, task in self._tasks.items():
                # Only cleanup completed or failed tasks
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if now - task.updated_at > self._task_ttl:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        
        return len(tasks_to_remove)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks (for debugging/monitoring)."""
        with self._lock:
            return {
                task_id: {
                    "id": task.id,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                for task_id, task in self._tasks.items()
            }


# Global task service instance
_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """Get or create the global task service instance."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
