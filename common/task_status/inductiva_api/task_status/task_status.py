"""Enum defining the possible task status codes."""
from enum import Enum


class TaskStatusCode(Enum):
    """Possible task status codes."""
    PENDING_INPUT = "pending-input"
    SUBMITTED = "submitted"
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    PENDING_KILL = "pending-kill"
    KILLED = "killed"
    SPOT_INSTANCE_PREEMPTED = "spot-instance-preempted"
    EXECUTER_TERMINATED = "executer-terminated"
    EXECUTER_FAILED = "executer-failed"
    ZOMBIE = "zombie"
