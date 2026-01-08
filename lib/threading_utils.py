"""
Thread-safe utilities for GUI updates and background processing.

This module provides a robust framework for:
- Safe GUI updates from background threads
- Task management and cancellation
- Progress tracking
- Error handling
"""

import threading
import queue
import logging
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("disconnectome")


class TaskStatus(Enum):
    """Status of a background task"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of a background task"""

    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    error_message: str = ""


class GUIThreadExecutor:
    """
    Thread-safe executor for running callbacks on the GUI thread.
    """

    def __init__(self, root_widget):
        """
        Initialize executor.

        Args:
            root_widget: Root Tkinter widget (typically CTk instance)
        """
        self.root = root_widget
        self._callback_queue = queue.Queue()
        self._running = True
        self._start_consumer()

    def _start_consumer(self):
        """Start the consumer that processes GUI callbacks"""

        def consume():
            """Consumer loop running on GUI thread"""
            while self._running:
                try:
                    # Process all pending callbacks
                    while True:
                        callback, args, kwargs = self._callback_queue.get_nowait()
                        try:
                            callback(*args, **kwargs)
                        except Exception as e:
                            logger.error(f"Error in GUI callback: {e}", exc_info=True)
                        finally:
                            self._callback_queue.task_done()
                except queue.Empty:
                    break

            # Schedule next check
            if self._running and self.root.winfo_exists():
                self.root.after(50, consume)

        # Start consumer on GUI thread
        self.root.after(50, consume)

    def submit(self, callback: Callable, *args, **kwargs):
        """
        Submit a callback to be executed on the GUI thread.

        Args:
            callback: Function to execute
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback
        """
        if not self._running:
            logger.warning("GUIThreadExecutor is stopped, ignoring callback")
            return

        try:
            self._callback_queue.put_nowait((callback, args, kwargs))
        except queue.Full:
            logger.error("GUI callback queue is full, dropping callback")

    def shutdown(self):
        """Shutdown the executor"""
        self._running = False


class BackgroundTask:
    """
    Manages a single background task with progress tracking and cancellation.
    """

    def __init__(
        self,
        worker_func: Callable,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[TaskResult], None]] = None,
        gui_executor: Optional[GUIThreadExecutor] = None,
    ):
        """
        Initialize background task.

        Args:
            worker_func: Function to run in background (should accept cancel_event)
            on_progress: Callback for progress updates (progress: float, message: str)
            on_complete: Callback when task completes
            gui_executor: GUIThreadExecutor for safe GUI updates (REQUIRED)
        """
        self.worker_func = worker_func
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.gui_executor = gui_executor

        # ✅ FIX: Require gui_executor for thread safety
        if gui_executor is None:
            raise ValueError(
                "gui_executor is required for thread safety. "
                "Pass GUIThreadExecutor instance to BackgroundTask."
            )

        self.status = TaskStatus.PENDING
        self.thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.result: Optional[TaskResult] = None

        self._progress = 0.0
        self._progress_message = ""
        self._lock = threading.Lock()

    def start(self):
        """Start the background task"""
        if self.status != TaskStatus.PENDING:
            raise RuntimeError(f"Task already started (status: {self.status})")

        self.status = TaskStatus.RUNNING
        self.thread = threading.Thread(target=self._run_worker, daemon=True)
        self.thread.start()
        logger.info("Background task started")

    def _run_worker(self):
        """Internal worker function"""
        try:
            # Run the worker function
            result = self.worker_func(
                cancel_event=self.cancel_event, progress_callback=self.update_progress
            )

            # Check if cancelled
            if self.cancel_event.is_set():
                self.result = TaskResult(
                    status=TaskStatus.CANCELLED, error_message="Task was cancelled"
                )
            else:
                self.result = TaskResult(status=TaskStatus.COMPLETED, result=result)

        except Exception as e:
            logger.error(f"Task failed with error: {e}", exc_info=True)
            self.result = TaskResult(
                status=TaskStatus.FAILED, error=e, error_message=str(e)
            )

        finally:
            self.status = self.result.status
            self._notify_completion()

    def _notify_completion(self):
        """Notify completion callback on GUI thread"""
        # ✅ FIX: Always use gui_executor - no direct callbacks
        if self.on_complete:
            self.gui_executor.submit(self.on_complete, self.result)

    def update_progress(self, progress: float, message: str = ""):
        """
        Update task progress (can be called from worker thread).

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        with self._lock:
            self._progress = progress
            self._progress_message = message

        # ✅ FIX: Always use gui_executor - no direct callbacks
        if self.on_progress:
            self.gui_executor.submit(self.on_progress, progress, message)

    def cancel(self):
        """Cancel the task"""
        logger.info("Cancelling background task")
        self.cancel_event.set()
        self.status = TaskStatus.CANCELLED

    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for task to complete.

        Args:
            timeout: Maximum time to wait (None = wait forever)

        Returns:
            True if task completed, False if timeout
        """
        if self.thread:
            self.thread.join(timeout=timeout)
            return not self.thread.is_alive()
        return True

    def get_progress(self) -> tuple[float, str]:
        """Get current progress (thread-safe)"""
        with self._lock:
            return self._progress, self._progress_message


class TaskManager:
    """
    Manages multiple background tasks.
    """

    def __init__(self, gui_executor: GUIThreadExecutor):
        """
        Initialize task manager.

        Args:
            gui_executor: GUIThreadExecutor for safe GUI updates
        """
        self.gui_executor = gui_executor
        self.tasks: Dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def create_task(
        self,
        task_id: str,
        worker_func: Callable,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[TaskResult], None]] = None,
    ) -> BackgroundTask:
        """
        Create a new background task.

        Args:
            task_id: Unique identifier for task
            worker_func: Worker function to execute
            on_progress: Progress callback
            on_complete: Completion callback

        Returns:
            Created BackgroundTask
        """
        with self._lock:
            if task_id in self.tasks:
                existing = self.tasks[task_id]
                if existing.status == TaskStatus.RUNNING:
                    raise ValueError(f"Task {task_id} is already running")

            task = BackgroundTask(
                worker_func=worker_func,
                on_progress=on_progress,
                on_complete=on_complete,
                gui_executor=self.gui_executor,
            )

            self.tasks[task_id] = task
            return task

    def start_task(self, task_id: str):
        """Start a created task"""
        with self._lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")

            task = self.tasks[task_id]
            task.start()

    def cancel_task(self, task_id: str):
        """Cancel a running task"""
        with self._lock:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return

            task = self.tasks[task_id]
            task.cancel()

    def cancel_all(self):
        """Cancel all running tasks"""
        with self._lock:
            for task in self.tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.cancel()

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get a task by ID"""
        with self._lock:
            return self.tasks.get(task_id)

    def cleanup_completed(self):
        """Remove completed tasks"""
        with self._lock:
            completed = [
                task_id
                for task_id, task in self.tasks.items()
                if task.status
                in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            for task_id in completed:
                del self.tasks[task_id]

            if completed:
                logger.info(f"Cleaned up {len(completed)} completed tasks")
