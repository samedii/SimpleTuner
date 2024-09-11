from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict
import threading

# Global executor for managing threads
executor = ThreadPoolExecutor(max_workers=1)  # Adjust max_workers based on your needs
thread_registry: Dict[str, Future] = {}  # A dictionary to store threads with their IDs
lock = threading.Lock()  # For thread-safe operations on the registry


def submit_job(job_id: str, func, *args, **kwargs):
    with lock:
        if (
            job_id in thread_registry
            and get_thread_status(job_id, with_lock=False).lower() == "running"
        ):
            raise Exception(f"Job with ID {job_id} is already running or pending.")
        # Remove the completed or cancelled future from the registry
        thread_registry.pop(job_id, None)
        # Submit the new job
        future = executor.submit(func, *args, **kwargs)
        thread_registry[job_id] = future


def get_thread_status(job_id: str, with_lock: bool = True) -> str:
    if with_lock:
        with lock:
            future = thread_registry.get(job_id)
            if not future:
                return "No such job."
            if future.running():
                return "Running"
            elif future.done():
                if future.exception():
                    return f"Failed: {future.exception()}"
                return "Completed"
            return "Pending"
    else:
        future = thread_registry.get(job_id)
        if not future:
            return "No such job."
        if future.running():
            return "Running"
        elif future.done():
            if future.exception():
                return f"Failed: {future.exception()}"
            return "Completed"
        return "Pending"


def terminate_thread(job_id: str) -> bool:
    with lock:
        future = thread_registry.get(job_id)
        if not future:
            print(f"Thread {job_id} not found")
            return False
        # Attempt to cancel the future if it hasn't started running
        cancelled = future.cancel()
        if cancelled:
            del thread_registry[job_id]
        return cancelled


def list_threads():
    return {job_id: get_thread_status(job_id) for job_id in thread_registry}
